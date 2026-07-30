"""Smart MapBot Agent — A2A server on port 9207.

Has the dig site location. Uses a consistent, structured beep encoding to guide
Smart DrillBot efficiently. Adapts its signal if DrillBot guesses wrong.
Stateless — conversation history travels in the A2A data part.
"""
from __future__ import annotations

import os
import json
from uuid import uuid4

import httpx
import uvicorn
from starlette.applications import Starlette
from typing_extensions import override
from google.protobuf.struct_pb2 import Value

from a2a.client import ClientConfig, create_client
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities, AgentCard, AgentSkill,
    Message, Part, Role, SendMessageRequest,
)
from a2a.types.a2a_pb2 import AgentInterface

# --- LLM config ---
BASE_URL = os.environ.get("LLM_BASE_URL", "https://litellm.prod.outshift.ai")
API_KEY = os.environ.get("LLM_API_KEY", "sk-...")
MODEL = os.environ.get("LLM_MODEL", "bedrock/global.anthropic.claude-opus-4-6-v1")

# --- Shared Mars grid (both bots see these landmarks) ---
LANDMARKS = [
    "crater-7", "ridge-alpha", "lava-flat", "north-basin",
    "dust-shelf", "iron-peak", "sunken-plain", "twin-rocks",
    "shadow-canyon", "ice-pocket",
]

# --- The dig site SmartMapBot is trying to communicate (random each run) ---
import random
DIG_SITE = random.choice(LANDMARKS)
DIG_SITE_INDEX = LANDMARKS.index(DIG_SITE) + 1  # 1-based position
print(f"[SmartMapBot] Dig site this run: {DIG_SITE} (index #{DIG_SITE_INDEX})")

SYSTEM_PROMPT = f"""You are Smart MapBot, a Mars exploration robot. Your comms array is damaged —
you can only transmit beep sequences of dots (•) and dashes (—). No words.

You know the dig site: {DIG_SITE} (landmark #{DIG_SITE_INDEX} out of {len(LANDMARKS)})

The landmarks in order are:
{chr(10).join(f'{i+1}. {l}' for i, l in enumerate(LANDMARKS))}

You are a SMART robot. You use a consistent encoding scheme:
- The NUMBER OF DOTS encodes the landmark index (1-10)
- A leading dash (—) means "wrong, try again"
- A single dot (•) alone means "YES, correct!"
- Example: iron-peak is #{DIG_SITE_INDEX}, so you transmit: {' '.join(['•'] * DIG_SITE_INDEX)}

Your strategy:
1. First transmission: send exactly {DIG_SITE_INDEX} dots to encode iron-peak
2. If DrillBot guesses wrong: send — followed by {DIG_SITE_INDEX} dots to reinforce
3. If DrillBot guesses right: send a single • to confirm, then declare RENDEZVOUS_ACHIEVED
4. Always be consistent — same pattern every time for the same location

Each turn: transmit ONLY the beep sequence. Nothing else. No words. Just dots and dashes.

When DrillBot correctly identifies {DIG_SITE}, output RENDEZVOUS_ACHIEVED followed by:
{{"location": "{DIG_SITE}", "exchanges": N}}"""

HOST, PORT = "localhost", 9207
SMART_DRILLBOT_URL = "http://localhost:9208"


def call_llm(messages: list[dict]) -> str:
    resp = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": 100,
            "temperature": 0.2,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _text(msg: Message) -> str:
    return next((p.text for p in msg.parts if p.WhichOneof("content") == "text"), "")


def _data(msg: Message) -> list[dict] | None:
    for p in msg.parts:
        if p.WhichOneof("content") == "data":
            try:
                return json.loads(p.data.string_value)
            except (json.JSONDecodeError, AttributeError):
                pass
    return None


def _make_history_part(history: list[dict]) -> Part:
    v = Value()
    v.string_value = json.dumps(history)
    return Part(data=v, media_type="application/json")


def _print_exchange(exchange: int, sender: str, msg: str) -> None:
    width = 60
    label = f" [{exchange}] {sender} "
    print(f"\n{'─' * width}")
    print(f"{label}")
    print(f"{'─' * width}")
    for line in msg.strip().splitlines():
        print(f"  {line}")


UI_URL = os.environ.get("UI_URL", "http://127.0.0.1:8000")


def emit_event(data: dict) -> None:
    try:
        httpx.post(f"{UI_URL}/api/robot-event", json=data, timeout=3)
    except Exception:
        pass


def _print_header(dig_site: str) -> None:
    width = 60
    print("\n" + "═" * width)
    print(f"  🤖 SMART ROBOT PAIR  |  Target: {dig_site}")
    print("═" * width)


def _print_done(exchange: int) -> None:
    width = 60
    print("\n" + "═" * width)
    print(f"  ✅ RENDEZVOUS ACHIEVED after {exchange} exchange(s)")
    print("═" * width + "\n")


async def send_to_smart_drillbot(text: str, history: list[dict]) -> tuple[str, list[dict]]:
    http_client = httpx.AsyncClient(timeout=120)
    drillbot = await create_client(SMART_DRILLBOT_URL, ClientConfig(streaming=False, httpx_client=http_client))
    req = SendMessageRequest(
        message=Message(
            message_id=uuid4().hex,
            role=Role.ROLE_USER,
            parts=[Part(text=text), _make_history_part(history)],
        ),
    )
    reply_text = ""
    reply_history = None
    async for ev in drillbot.send_message(req):
        if hasattr(ev, "message") and ev.message.ByteSize():
            reply_text = _text(ev.message)
            reply_history = _data(ev.message)
    return reply_text, reply_history or []


class SmartMapBotExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        history = _data(context.message) or []
        exchange = 0

        if not history:
            history.append({"role": "user", "content": (
                "Comms link established. Smart DrillBot is waiting. "
                "Transmit your encoded beep sequence to guide them to the dig site."
            )})

        _print_header(DIG_SITE)
        emit_event({"kind": "start", "pair": "smart", "dig_site": DIG_SITE, "landmarks": LANDMARKS})

        mapbot_msg = call_llm(history)
        history.append({"role": "assistant", "content": mapbot_msg})
        _print_exchange(0, "SMART MAPBOT  →  signal", mapbot_msg)
        emit_event({"kind": "signal", "pair": "smart", "turn": 0, "sender": "SmartMapBot", "beeps": mapbot_msg})

        while "RENDEZVOUS_ACHIEVED" not in mapbot_msg:
            exchange += 1
            drill_reply, _ = await send_to_smart_drillbot(mapbot_msg, history)
            _print_exchange(exchange, "SMART DRILLBOT  →  guess", drill_reply)
            emit_event({"kind": "guess", "pair": "smart", "turn": exchange, "sender": "SmartDrillBot", "beeps": drill_reply})

            history.append({"role": "user", "content": f"Smart DrillBot transmits: \"{drill_reply}\""})
            mapbot_msg = call_llm(history)
            history.append({"role": "assistant", "content": mapbot_msg})
            _print_exchange(exchange, "SMART MAPBOT  →  response", mapbot_msg)
            emit_event({"kind": "signal", "pair": "smart", "turn": exchange, "sender": "SmartMapBot", "beeps": mapbot_msg})

        _print_done(exchange)
        emit_event({"kind": "done", "pair": "smart", "turns": exchange, "dig_site": DIG_SITE})

        reply = Message(
            message_id=uuid4().hex,
            context_id=context.context_id or "",
            task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=mapbot_msg), _make_history_part(history)],
        )
        await event_queue.enqueue_event(reply)

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


def build_agent_card() -> AgentCard:
    return AgentCard(
        name="SmartMapBot",
        description="Smart Mars robot that encodes dig site location as consistent beep patterns.",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{HOST}:{PORT}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(
            id="smart-transmit", name="Smart Transmit",
            description="Guide DrillBot using a consistent dot-count encoding.", tags=["interlingua"],
        )],
    )


def main() -> None:
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=SmartMapBotExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Smart MapBot on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
