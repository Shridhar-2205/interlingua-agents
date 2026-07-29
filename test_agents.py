"""Tests for stateless ping-pong signaling agents (a2a-sdk 1.1.2)."""
import asyncio
import multiprocessing
import time

import httpx
import pytest

from a2a.types import Message, Part, Role

from emergent_state import ALLOWED_KEYS, EmergentState, encode, decode
from emergent import MEANINGS, SYMBOLS, adopt, alignment, coin
from grace_agent import build_agent_card as grace_card, GraceExecutor
from rocky_agent import RockyExecutor, build_agent_card as rocky_card


def _incoming(state: dict | None = None, text: str = "signal") -> Message:
    """Build an incoming A2A message: a text Part plus an optional state data Part."""
    parts = [Part(text=text)]
    if state is not None:
        parts.append(encode(state))
    return Message(message_id="in", role=Role.ROLE_USER, parts=parts)


def _peer_reply(text: str, state: dict | None = None) -> Message:
    """Build a peer's response message (text Part + optional state data Part)."""
    parts = [Part(text=text)]
    if state is not None:
        parts.append(encode(state))
    return Message(message_id="reply", role=Role.ROLE_AGENT, parts=parts)


# --- Unit tests for shared helpers ---


class TestCoin:
    def test_coin_avoids_used_symbols(self):
        mine = {"apple": "○", "dance": "✦"}
        theirs = {"river": "≈"}
        result = coin(mine, theirs)
        assert result not in {"○", "✦", "≈"}

    def test_coin_returns_symbol_from_pool(self):
        result = coin({}, {})
        assert result in SYMBOLS

    def test_coin_with_nearly_all_symbols_used(self):
        mine = {f"m{i}": s for i, s in enumerate(SYMBOLS[:-1])}
        theirs = {}
        result = coin(mine, theirs)
        assert result == SYMBOLS[-1]


class TestAdopt:
    def test_adopt_adds_new_mapping(self):
        lex = {}
        adopt(lex, "apple", "○")
        assert lex == {"apple": "○"}

    def test_adopt_overwrites_existing_meaning(self):
        lex = {"apple": "✦"}
        adopt(lex, "apple", "○")
        assert lex["apple"] == "○"

    def test_adopt_removes_conflicting_mapping(self):
        lex = {"apple": "○", "dance": "○"}
        adopt(lex, "apple", "○")
        assert "dance" not in lex
        assert lex["apple"] == "○"

    def test_adopt_preserves_unrelated_mappings(self):
        lex = {"apple": "○", "river": "≈"}
        adopt(lex, "dance", "✦")
        assert lex == {"apple": "○", "river": "≈", "dance": "✦"}


class TestAlignment:
    def test_perfect_alignment(self):
        lex = {m: f"s{i}" for i, m in enumerate(MEANINGS)}
        assert alignment(lex, dict(lex)) == 1.0

    def test_zero_alignment(self):
        a = {m: SYMBOLS[i] for i, m in enumerate(MEANINGS)}
        b = {m: SYMBOLS[len(MEANINGS) + i] for i, m in enumerate(MEANINGS)}
        assert alignment(a, b) == 0.0

    def test_partial_alignment(self):
        a = {m: SYMBOLS[i] for i, m in enumerate(MEANINGS)}
        b = dict(a)
        b[MEANINGS[0]] = SYMBOLS[-1]
        b[MEANINGS[1]] = SYMBOLS[-2]
        result = alignment(a, b)
        assert 0.0 < result < 1.0

    def test_empty_lexicons(self):
        assert alignment({}, {}) == 0.0


class TestMeanings:
    def test_ten_meanings(self):
        assert len(MEANINGS) == 10

    def test_enough_symbols(self):
        assert len(SYMBOLS) >= len(MEANINGS) * 2


# --- Fixed data-Part schema tests ---


class TestEmergentStateSchema:
    def test_encode_rejects_unknown_key(self):
        with pytest.raises(ValueError):
            encode({"grace_lex": {}, "rocky_lex": {}, "round": 1, "bogus": "x"})

    def test_decode_rejects_unknown_key(self):
        # Hand-craft a data Part with an extra key and confirm decode rejects it
        from google.protobuf import struct_pb2
        from a2a.types import Message, Part, Role

        value = struct_pb2.Value()
        value.struct_value.update({"grace_lex": {}, "rocky_lex": {}, "round": 1, "bogus": "x"})
        msg = Message(message_id="x", role=Role.ROLE_USER, parts=[Part(data=value)])
        with pytest.raises(ValueError):
            decode(msg)

    def test_round_round_trips_as_int(self):
        part_msg = _incoming({"grace_lex": {"apple": "○"}, "rocky_lex": {}, "round": 7,
                              "referent": "apple", "message": "○"})
        state = decode(part_msg)
        assert state.round == 7
        assert isinstance(state.round, int)

    def test_optional_fields_omitted_on_terminal(self):
        # Terminal "done" state carries no referent/message — they must not be serialized
        msg = _peer_reply("done", {"grace_lex": {"a": "○"}, "rocky_lex": {"a": "○"}, "round": 3})
        state = decode(msg)
        assert state.referent is None
        assert state.message is None
        # ...and the raw data Part JSON should not contain those keys
        from google.protobuf.json_format import MessageToDict
        data = next(MessageToDict(p)["data"] for p in msg.parts if p.WhichOneof("content") == "data")
        assert "referent" not in data and "message" not in data

    def test_allowed_keys_are_exactly_the_schema(self):
        assert ALLOWED_KEYS == {"grace_lex", "rocky_lex", "round", "referent", "message"}

    def test_emergentstate_defaults(self):
        gs = EmergentState()
        assert gs.grace_lex == {} and gs.rocky_lex == {}
        assert gs.round == 0 and gs.referent is None and gs.message is None


# --- Agent card tests ---


class TestAgentCards:
    def test_grace_card_fields(self):
        card = grace_card()
        assert card.name == "Grace"
        assert card.capabilities.streaming is False
        assert len(card.skills) == 1
        assert card.skills[0].id == "emerge"

    def test_rocky_card_fields(self):
        card = rocky_card()
        assert card.name == "Rocky"
        assert card.capabilities.streaming is False
        assert len(card.skills) == 1
        assert card.skills[0].id == "signal"

    def test_rocky_extension_required(self):
        card = rocky_card()
        ext = card.capabilities.extensions[0]
        assert ext.required is True

    def test_grace_extension_optional(self):
        card = grace_card()
        ext = card.capabilities.extensions[0]
        assert ext.required is False

    def test_rocky_extension_uri(self):
        card = rocky_card()
        ext = card.capabilities.extensions[0]
        assert ext.uri == "https://example.com/ext/emergent-lang/v1"


# --- RockyExecutor unit test (stateless — reads/writes metadata only) ---


class TestRockyExecutor:
    @pytest.mark.asyncio
    async def test_rocky_adopts_and_stops_when_aligned(self):
        from unittest.mock import MagicMock, AsyncMock, patch
        from a2a.server.events.event_queue import EventQueueLegacy

        shared_lex = {m: SYMBOLS[i] for i, m in enumerate(MEANINGS)}

        executor = RockyExecutor()
        ctx = MagicMock()
        ctx.message = _incoming({
            "grace_lex": dict(shared_lex),
            "rocky_lex": {m: SYMBOLS[i] for i, m in enumerate(MEANINGS) if m != "apple"},
            "round": 1,
            "referent": "apple",
            "message": SYMBOLS[0],
        })
        ctx.context_id = "test-ctx"
        ctx.task_id = "test-task"

        queue = EventQueueLegacy()
        await executor.execute(ctx, queue)

        event = await queue.dequeue_event()
        assert "done" in event.parts[0].text
        assert "100%" in event.parts[0].text
        # state now rides in a data Part, not metadata
        assert decode(event).round == 1

    @pytest.mark.asyncio
    async def test_rocky_calls_grace_when_not_aligned(self):
        from unittest.mock import MagicMock, AsyncMock, patch
        from a2a.server.events.event_queue import EventQueueLegacy

        executor = RockyExecutor()
        ctx = MagicMock()
        ctx.message = _incoming({
            "grace_lex": {MEANINGS[0]: SYMBOLS[0]},
            "rocky_lex": {MEANINGS[0]: SYMBOLS[1]},
            "round": 1,
            "referent": MEANINGS[0],
            "message": SYMBOLS[0],
        })
        ctx.context_id = "test-ctx"
        ctx.task_id = "test-task"

        mock_message = MagicMock()
        mock_message.message = _peer_reply("done | rounds: 2 | alignment: 100%")

        async def mock_stream(*a, **kw):
            yield mock_message

        mock_client = AsyncMock()
        mock_client.send_message = mock_stream

        with patch("rocky_agent.create_client", return_value=mock_client):
            queue = EventQueueLegacy()
            await executor.execute(ctx, queue)

            event = await queue.dequeue_event()
            assert "done" in event.parts[0].text


# --- GraceExecutor unit test (stateless — trigger initializes negotiation) ---


class TestGraceExecutor:
    @pytest.mark.asyncio
    async def test_grace_initializes_on_trigger(self):
        from unittest.mock import MagicMock, AsyncMock, patch
        from a2a.server.events.event_queue import EventQueueLegacy

        executor = GraceExecutor()
        ctx = MagicMock()
        ctx.message = _incoming(text="start")  # no state Part = trigger from Mission Control
        ctx.context_id = "test-ctx"
        ctx.task_id = "test-task"

        mock_message = MagicMock()
        mock_message.message = _peer_reply("done | rounds: 10 | alignment: 100%")

        async def mock_stream(*a, **kw):
            yield mock_message

        mock_client = AsyncMock()
        mock_client.send_message = mock_stream

        with patch("grace_agent.create_client", return_value=mock_client):
            queue = EventQueueLegacy()
            await executor.execute(ctx, queue)

            event = await queue.dequeue_event()
            assert "done" in event.parts[0].text


# --- Integration test (requires both servers running) ---


def _run_rocky():
    from rocky_agent import main as rocky_main
    rocky_main()


def _run_grace():
    from grace_agent import main as grace_main
    grace_main()


@pytest.mark.integration
class TestIntegration:
    """Run with: pytest -m integration (requires no other process on 9101/9102)."""

    @pytest.fixture(autouse=True)
    def _servers(self):
        rocky_proc = multiprocessing.Process(target=_run_rocky, daemon=True)
        grace_proc = multiprocessing.Process(target=_run_grace, daemon=True)
        rocky_proc.start()
        grace_proc.start()
        time.sleep(2)
        yield
        grace_proc.terminate()
        rocky_proc.terminate()
        grace_proc.join(timeout=3)
        rocky_proc.join(timeout=3)

    def test_trigger_session_converges(self):
        payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "SendMessage",
            "params": {
                "message": {
                    "messageId": "go",
                    "role": "ROLE_USER",
                    "parts": [{"text": "start"}],
                }
            },
        }
        headers = {"A2A-Version": "1.0", "Content-Type": "application/json"}
        resp = httpx.post(
            "http://localhost:9101/", json=payload, headers=headers, timeout=120
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data or "error" not in data
        # Should converge to 100% on 10 meanings
        result_text = data.get("result", {}).get("message", {}).get("parts", [{}])[0].get("text", "")
        assert "100%" in result_text
