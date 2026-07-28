"""Tests for stateless ping-pong signaling game agents (a2a-sdk 1.1.2)."""
import asyncio
import multiprocessing
import time

import httpx
import pytest

from signaling import MEANINGS, SYMBOLS, adopt, alignment, coin
from grace_agent import build_agent_card as grace_card, GraceExecutor
from rocky_agent import RockyExecutor, build_agent_card as rocky_card


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
        ctx.metadata = {
            "https://example.com/ext/emergent-lang/v1/context": {
                "grace_lex": dict(shared_lex),
                "rocky_lex": {m: SYMBOLS[i] for i, m in enumerate(MEANINGS) if m != "apple"},
                "round": 1,
                "referent": "apple",
            },
            "https://example.com/ext/emergent-lang/v1/message": SYMBOLS[0],
        }
        ctx.context_id = "test-ctx"
        ctx.task_id = "test-task"

        queue = EventQueueLegacy()
        await executor.execute(ctx, queue)

        event = await queue.dequeue_event()
        assert "done" in event.parts[0].text
        assert "100%" in event.parts[0].text

    @pytest.mark.asyncio
    async def test_rocky_calls_grace_when_not_aligned(self):
        from unittest.mock import MagicMock, AsyncMock, patch
        from a2a.server.events.event_queue import EventQueueLegacy

        executor = RockyExecutor()
        ctx = MagicMock()
        ctx.metadata = {
            "https://example.com/ext/emergent-lang/v1/context": {
                "grace_lex": {MEANINGS[0]: SYMBOLS[0]},
                "rocky_lex": {MEANINGS[0]: SYMBOLS[1]},
                "round": 1,
                "referent": MEANINGS[0],
            },
            "https://example.com/ext/emergent-lang/v1/message": SYMBOLS[0],
        }
        ctx.context_id = "test-ctx"
        ctx.task_id = "test-task"

        mock_message = MagicMock()
        mock_message.message.ByteSize.return_value = True
        mock_message.message.parts = [MagicMock(text="done | rounds: 2 | alignment: 100%")]
        mock_message.message.metadata.ByteSize.return_value = 0

        async def mock_stream(*a, **kw):
            yield mock_message

        mock_client = AsyncMock()
        mock_client.send_message = mock_stream

        with patch("rocky_agent.create_client", return_value=mock_client):
            queue = EventQueueLegacy()
            await executor.execute(ctx, queue)

            event = await queue.dequeue_event()
            assert "done" in event.parts[0].text


# --- GraceExecutor unit test (stateless — trigger initializes game) ---


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
