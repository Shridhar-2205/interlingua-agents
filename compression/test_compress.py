"""Tests for the stateless Mission Log Relay compression agents (a2a-sdk 1.1.2)."""
import multiprocessing
import time

import httpx
import pytest

from a2a.types import Message, Part, Role

from compress_state import ALLOWED_KEYS, CompressionState, encode, decode
from compress import (
    FIELDS, VOCAB, decode_record, encode_codebook, encode_verbose, make_record,
    next_code, simulate, tokens, verbose_tokens,
)
from grace_compress_agent import (
    GraceCompressExecutor, build_agent_card as grace_card, parse_trigger,
)
from rocky_compress_agent import RockyCompressExecutor, build_agent_card as rocky_card


def _incoming(state: dict | None = None, text: str = "input") -> Message:
    parts = [Part(text=text)]
    if state is not None:
        parts.append(encode(state))
    return Message(message_id="in", role=Role.ROLE_USER, parts=parts)


def _peer_reply(text: str, state: dict | None = None) -> Message:
    parts = [Part(text=text)]
    if state is not None:
        parts.append(encode(state))
    return Message(message_id="reply", role=Role.ROLE_AGENT, parts=parts)


# --- Pure logic ---


class TestRecords:
    def test_make_record_is_deterministic(self):
        assert make_record(1, 3) == make_record(1, 3)

    def test_make_record_uses_vocab(self):
        rec = make_record(7, 5)
        assert set(rec) == set(FIELDS)
        for f in FIELDS:
            assert rec[f] in VOCAB[f]


class TestCoding:
    def test_next_code_increments(self):
        assert next_code({}) == "$1"
        assert next_code({"a": "$1"}) == "$2"

    def test_define_then_refer(self):
        record = {"loc": "docking bay seven", "act": "seal the hull breach",
                  "stat": "status critical", "crew": "three crew aboard"}
        wire1, cb1 = encode_codebook(record, {})
        # First time: everything is spelled out (DEFINE), codebook now full.
        assert wire1 == record
        assert len(cb1) == len(FIELDS)
        # Second time: same record => all REFER => 1 token per field.
        wire2, cb2 = encode_codebook(record, cb1)
        assert tokens(wire2) == len(FIELDS)
        assert cb2 == cb1

    def test_decode_roundtrips_codebook(self):
        record = make_record(2, 4)
        wire, cb = encode_codebook(record, {})
        assert decode_record(wire, cb) == record
        wire2, cb2 = encode_codebook(record, cb)      # REFER round
        assert decode_record(wire2, cb2) == record

    def test_decode_roundtrips_verbose(self):
        record = make_record(3, 1)
        assert decode_record(encode_verbose(record), {}) == record

    def test_verbose_tokens_counts_words(self):
        assert verbose_tokens({"loc": "a b", "act": "c", "stat": "d e", "crew": "f"}) == 6


class TestSimulate:
    def test_both_arms_lossless(self):
        for arm in ("verbose", "codebook"):
            res = simulate(seed=1, total=24, arm=arm)
            assert res["wins"] == res["total"]        # 100% accuracy, both arms

    def test_codebook_compresses(self):
        v = simulate(seed=1, total=24, arm="verbose")
        c = simulate(seed=1, total=24, arm="codebook")
        assert sum(c["tokens_log"]) < sum(v["tokens_log"])
        # Late rounds should be cheaper than early rounds (curve decays).
        tl = c["tokens_log"]
        assert sum(tl[-6:]) < sum(tl[:6])


# --- Fixed data-Part schema ---


class TestCompressionStateSchema:
    def test_encode_rejects_unknown_key(self):
        with pytest.raises(ValueError):
            encode({"arm": "codebook", "bogus": 1})

    def test_decode_rejects_unknown_key(self):
        from google.protobuf import struct_pb2
        value = struct_pb2.Value()
        value.struct_value.update({"arm": "codebook", "bogus": 1})
        msg = Message(message_id="x", role=Role.ROLE_USER, parts=[Part(data=value)])
        with pytest.raises(ValueError):
            decode(msg)

    def test_numeric_fields_round_trip_as_int(self):
        msg = _incoming({"round": 7, "seed": 2, "total": 24, "wins": 3,
                         "tokens_log": [12, 6, 4], "verbose_log": [12, 12, 12]})
        st = decode(msg)
        assert st.round == 7 and isinstance(st.round, int)
        assert st.tokens_log == [12, 6, 4]
        assert all(isinstance(x, int) for x in st.tokens_log)

    def test_optionals_omitted_when_none(self):
        from google.protobuf.json_format import MessageToDict
        msg = _peer_reply("done", {"arm": "codebook", "total": 1, "round": 1})
        data = next(MessageToDict(p)["data"] for p in msg.parts
                    if p.WhichOneof("content") == "data")
        assert "wire" not in data and "reconstruction" not in data

    def test_wire_and_reconstruction_round_trip(self):
        rec = make_record(1, 0)
        st = decode(_incoming({"arm": "codebook", "total": 5, "round": 0,
                               "wire": rec, "reconstruction": rec}))
        assert st.wire == rec and st.reconstruction == rec

    def test_allowed_keys_are_exactly_the_schema(self):
        assert ALLOWED_KEYS == {"codebook", "round", "seed", "total", "arm",
                                "tokens_log", "verbose_log", "wins", "wire",
                                "reconstruction"}


# --- Trigger parsing ---


class TestParseTrigger:
    def test_defaults(self):
        assert parse_trigger("start") == ("codebook", 1, 24)

    def test_arm_seed_total(self):
        assert parse_trigger("verbose seed=5 total=30") == ("verbose", 5, 30)


# --- Agent cards ---


class TestAgentCards:
    def test_grace_card(self):
        card = grace_card()
        assert card.name == "Grace-Compress"
        assert card.capabilities.streaming is False
        assert card.skills[0].id == "relay"
        assert card.capabilities.extensions[0].required is False

    def test_rocky_card(self):
        card = rocky_card()
        assert card.name == "Rocky-Compress"
        assert card.skills[0].id == "reconstruct"
        ext = card.capabilities.extensions[0]
        assert ext.required is True
        assert ext.uri == "https://example.com/ext/emergent-compress/v1"


# --- Executor units ---


class TestGraceExecutor:
    @pytest.mark.asyncio
    async def test_grace_scores_and_terminates(self):
        from unittest.mock import MagicMock
        from a2a.server.events.event_queue import EventQueueLegacy

        executor = GraceCompressExecutor()
        ctx = MagicMock()
        # Round 0 of a 1-round session; Rocky's reconstruction matches truth.
        truth = make_record(1, 0)
        ctx.message = _incoming({
            "arm": "codebook", "seed": 1, "total": 1, "round": 0,
            "tokens_log": [12], "verbose_log": [12], "wins": 0,
            "wire": truth, "reconstruction": truth,
        })
        ctx.context_id, ctx.task_id = "c", "t"

        queue = EventQueueLegacy()
        await executor.execute(ctx, queue)
        event = await queue.dequeue_event()
        assert "done" in event.parts[0].text
        assert "accuracy: 1/1" in event.parts[0].text
        assert decode(event).round == 1

    @pytest.mark.asyncio
    async def test_grace_trigger_transmits_and_calls_rocky(self):
        from unittest.mock import MagicMock, AsyncMock, patch
        from a2a.server.events.event_queue import EventQueueLegacy

        executor = GraceCompressExecutor()
        ctx = MagicMock()
        ctx.message = _incoming(text="codebook total=3")  # no data Part = trigger
        ctx.context_id, ctx.task_id = "c", "t"

        peer = MagicMock()
        peer.message = _peer_reply("done | ...")

        async def stream(*a, **kw):
            yield peer

        client = AsyncMock()
        client.send_message = stream
        with patch("grace_compress_agent.create_client", return_value=client):
            queue = EventQueueLegacy()
            await executor.execute(ctx, queue)
            event = await queue.dequeue_event()
            assert "done" in event.parts[0].text


class TestRockyExecutor:
    @pytest.mark.asyncio
    async def test_rocky_decodes_and_calls_grace(self):
        from unittest.mock import MagicMock, AsyncMock, patch
        from a2a.server.events.event_queue import EventQueueLegacy

        executor = RockyCompressExecutor()
        record = make_record(1, 0)
        wire, cb = encode_codebook(record, {})
        ctx = MagicMock()
        ctx.message = _incoming({
            "arm": "codebook", "seed": 1, "total": 3, "round": 0,
            "codebook": cb, "wire": wire,
        })
        ctx.context_id, ctx.task_id = "c", "t"

        captured = {}

        async def stream(req, *a, **kw):
            captured["state"] = decode(req.message)
            peer = MagicMock()
            peer.message = _peer_reply("passthrough")
            yield peer

        client = AsyncMock()
        client.send_message = stream
        with patch("rocky_compress_agent.create_client", return_value=client):
            queue = EventQueueLegacy()
            await executor.execute(ctx, queue)
            # Rocky must have reconstructed the record and sent it to Grace.
            assert captured["state"].reconstruction == record
            event = await queue.dequeue_event()
            assert event.parts[0].text == "passthrough"


# --- Integration (both servers) ---


def _run_rocky():
    from rocky_compress_agent import main
    main()


def _run_grace():
    from grace_compress_agent import main
    main()


def _trigger(text: str) -> str:
    payload = {
        "jsonrpc": "2.0", "id": "1", "method": "SendMessage",
        "params": {"message": {"messageId": "go", "role": "ROLE_USER",
                               "parts": [{"text": text}]}},
    }
    headers = {"A2A-Version": "1.0", "Content-Type": "application/json"}
    resp = httpx.post("http://localhost:9201/", json=payload, headers=headers, timeout=120)
    assert resp.status_code == 200
    data = resp.json()
    return data.get("result", {}).get("message", {}).get("parts", [{}])[0].get("text", "")


@pytest.mark.integration
class TestIntegration:
    """Run with: pytest -m integration (needs ports 9201/9202 free)."""

    @pytest.fixture(autouse=True)
    def _servers(self):
        rocky = multiprocessing.Process(target=_run_rocky, daemon=True)
        grace = multiprocessing.Process(target=_run_grace, daemon=True)
        rocky.start(); grace.start()
        time.sleep(2)
        yield
        grace.terminate(); rocky.terminate()
        grace.join(timeout=3); rocky.join(timeout=3)

    def test_codebook_session_is_lossless_and_compresses(self):
        text = _trigger("codebook seed=1 total=24")
        assert "accuracy: 24/24" in text        # lossless
        assert "ratio:" in text and "1.00x" not in text  # actually compressed

    def test_verbose_session_is_lossless_flat(self):
        text = _trigger("verbose seed=1 total=24")
        assert "accuracy: 24/24" in text
        assert "ratio: 1.00x" in text            # no compression, by construction
