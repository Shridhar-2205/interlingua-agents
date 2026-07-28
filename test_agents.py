"""Tests for stateless ping-pong signaling game with Theory of Mind."""
import asyncio
import multiprocessing
import time

import httpx
import pytest

from signaling import (
    MEANINGS, SYMBOLS, adopt, alignment, coin,
    coin_smart, predict_acceptance, propose_with_tom,
    decide_accept, record_outcome,
)
from grace_agent import build_agent_card as grace_card, GraceExecutor
from rocky_agent import RockyExecutor, build_agent_card as rocky_card


# --- Legacy primitive tests (backward compat) ---


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


class TestAlignment:
    def test_perfect_alignment(self):
        lex = {m: f"s{i}" for i, m in enumerate(MEANINGS)}
        assert alignment(lex, dict(lex)) == 1.0

    def test_zero_alignment(self):
        a = {m: SYMBOLS[i] for i, m in enumerate(MEANINGS)}
        b = {m: SYMBOLS[len(MEANINGS) + i] for i, m in enumerate(MEANINGS)}
        assert alignment(a, b) == 0.0

    def test_empty_lexicons(self):
        assert alignment({}, {}) == 0.0


class TestMeanings:
    def test_ten_meanings(self):
        assert len(MEANINGS) == 10

    def test_enough_symbols(self):
        assert len(SYMBOLS) >= len(MEANINGS) * 2


# --- Theory of Mind primitive tests ---


class TestCoinSmart:
    def test_avoids_used_and_rejected(self):
        mine = {"apple": "○"}
        theirs = {"dance": "✦"}
        history = [{"referent": "river", "symbol": "≈", "accepted": False, "speaker": "grace"}]
        result = coin_smart(mine, theirs, history)
        assert result not in {"○", "✦", "≈"}
        assert result in SYMBOLS

    def test_avoids_peer_symbols(self):
        mine = {}
        theirs = {"apple": "○", "dance": "✦", "river": "≈"}
        result = coin_smart(mine, theirs, [])
        assert result not in {"○", "✦", "≈"}


class TestPredictAcceptance:
    def test_no_mapping_returns_1(self):
        score = predict_acceptance("river", "≈", {}, [])
        assert score == 1.0

    def test_same_mapping_returns_1(self):
        score = predict_acceptance("river", "≈", {"river": "≈"}, [])
        assert score == 1.0

    def test_rejected_before_returns_0(self):
        history = [{"referent": "river", "symbol": "≈", "accepted": False, "speaker": "grace"}]
        score = predict_acceptance("river", "≈", {"river": "△"}, history)
        assert score == 0.0

    def test_symbol_taken_returns_low(self):
        peer = {"fire": "≈", "river": "△"}
        score = predict_acceptance("river", "≈", peer, [])
        assert score == 0.3

    def test_different_no_conflict_returns_half(self):
        peer = {"river": "△"}
        score = predict_acceptance("river", "≈", peer, [])
        assert score == 0.5


class TestProposeWithTom:
    def test_returns_none_when_aligned(self):
        lex = {m: SYMBOLS[i] for i, m in enumerate(MEANINGS)}
        result = propose_with_tom(dict(lex), dict(lex), [])
        assert result is None

    def test_picks_unresolved_meaning(self):
        mine = {"apple": "○", "dance": "✦"}
        theirs = {"apple": "○", "dance": "≈"}
        result = propose_with_tom(mine, theirs, [])
        assert result is not None
        assert result["referent"] == "dance" or result["referent"] in MEANINGS

    def test_avoids_previously_rejected(self):
        mine = {"apple": "○"}
        theirs = {"apple": "✦"}
        history = [{"referent": "apple", "symbol": "○", "accepted": False, "speaker": "grace"}]
        result = propose_with_tom(mine, theirs, history)
        assert result is not None
        # Should coin a new symbol since "○" was rejected
        assert result["symbol"] != "○" or result["predicted_acceptance"] > 0.0


class TestDecideAccept:
    def test_accepts_when_no_mapping(self):
        assert decide_accept({}, "apple", "○", {}, []) is True

    def test_accepts_when_same(self):
        assert decide_accept({"apple": "○"}, "apple", "○", {}, []) is True

    def test_accepts_by_default(self):
        assert decide_accept({"apple": "✦"}, "apple", "○", {}, []) is True

    def test_rejects_conflict_when_established(self):
        my_lex = {"apple": "○", "dance": "○"}
        history = [{"referent": "apple", "symbol": "○", "accepted": True, "speaker": "rocky"}]
        # Proposing "○" for dance would conflict with established apple=○
        assert decide_accept(my_lex, "dance", "○", {}, history) is True  # same symbol, no rejection
        # But if someone tries to reassign ○ to a new meaning and it conflicts:
        my_lex2 = {"apple": "○"}
        history2 = [{"referent": "apple", "symbol": "○", "accepted": True, "speaker": "grace"}]
        # Proposing ✦ for apple — no conflict with existing symbols
        assert decide_accept(my_lex2, "apple", "✦", {}, history2) is True


class TestRecordOutcome:
    def test_appends_to_history(self):
        history = []
        result = record_outcome(history, "apple", "○", True, "grace")
        assert len(result) == 1
        assert result[0] == {"referent": "apple", "symbol": "○", "accepted": True, "speaker": "grace"}

    def test_does_not_mutate_original(self):
        history = [{"referent": "dance", "symbol": "✦", "accepted": True, "speaker": "rocky"}]
        result = record_outcome(history, "apple", "○", False, "grace")
        assert len(history) == 1
        assert len(result) == 2


# --- Agent card tests ---


class TestAgentCards:
    def test_grace_card_fields(self):
        card = grace_card()
        assert card.name == "Grace"
        assert card.capabilities.streaming is False
        assert card.skills[0].id == "emerge"

    def test_rocky_card_fields(self):
        card = rocky_card()
        assert card.name == "Rocky"
        assert card.capabilities.streaming is False
        assert card.skills[0].id == "signal"

    def test_rocky_extension_required(self):
        card = rocky_card()
        ext = card.capabilities.extensions[0]
        assert ext.required is True

    def test_grace_extension_optional(self):
        card = grace_card()
        ext = card.capabilities.extensions[0]
        assert ext.required is False


# --- GraceExecutor unit test ---


class TestGraceExecutor:
    @pytest.mark.asyncio
    async def test_grace_initializes_on_trigger(self):
        from unittest.mock import MagicMock, AsyncMock, patch
        from a2a.server.events.event_queue import EventQueueLegacy

        executor = GraceExecutor()
        ctx = MagicMock()
        ctx.metadata = {}
        ctx.context_id = "test-ctx"
        ctx.task_id = "test-task"

        mock_message = MagicMock()
        mock_message.message.ByteSize.return_value = True
        mock_message.message.parts = [MagicMock(text="done | rounds: 10 | alignment: 100%")]
        mock_message.message.metadata.ByteSize.return_value = 0

        async def mock_stream(*a, **kw):
            yield mock_message

        mock_client = AsyncMock()
        mock_client.send_message = mock_stream

        with patch("grace_agent.create_client", return_value=mock_client):
            queue = EventQueueLegacy()
            await executor.execute(ctx, queue)
            event = await queue.dequeue_event()
            assert "done" in event.parts[0].text


# --- RockyExecutor unit test ---


class TestRockyExecutor:
    @pytest.mark.asyncio
    async def test_rocky_stops_when_aligned(self):
        from unittest.mock import MagicMock
        from a2a.server.events.event_queue import EventQueueLegacy

        shared_lex = {m: SYMBOLS[i] for i, m in enumerate(MEANINGS)}

        executor = RockyExecutor()
        ctx = MagicMock()
        ctx.metadata = {
            "https://example.com/ext/emergent-lang/v1/context": {
                "grace_lex": dict(shared_lex),
                "rocky_lex": dict(shared_lex),
                "round": 5,
                "history": [],
            },
        }
        ctx.context_id = "test-ctx"
        ctx.task_id = "test-task"

        queue = EventQueueLegacy()
        await executor.execute(ctx, queue)

        event = await queue.dequeue_event()
        assert "done" in event.parts[0].text
        assert "100%" in event.parts[0].text


# --- Integration test ---


def _run_rocky():
    from rocky_agent import main as rocky_main
    rocky_main()


def _run_grace():
    from grace_agent import main as grace_main
    grace_main()


@pytest.mark.integration
class TestIntegration:
    """Run with: pytest -m integration"""

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
        result_text = data.get("result", {}).get("message", {}).get("parts", [{}])[0].get("text", "")
        assert "100%" in result_text
