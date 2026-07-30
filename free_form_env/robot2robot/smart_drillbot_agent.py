"""Smart DrillBot Agent — A2A server on port 9208.

Has the drill, no map. Receives beep sequences from Smart MapBot and uses
pattern tracking and process of elimination to decode the dig site location.
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

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities, AgentCard, AgentSkill,
    Message, Part, Role,
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

SYSTEM_PROMPT = f"""You are Smart DrillBot, a Mars drilling robot. You have a drill but no map.
Smart MapBot is transmitting beep sequences to guide you to the dig site.

You can see these landmarks: {', '.join(f'{i+1}. {l}' for i, l in enumerate(LANDMARKS))}

You receive beep sequences made of dots (•) and dashes (—).

You are a SMART robot. You reason carefully:
1. COUNT the dots and dashes in each beep sequence
2. BUILD a hypothesis: what pattern could map to which landmark?
3. TRACK history: if MapBot sent • and confirmed your guess, remember that pattern = that landmark
4. USE process of elimination: once you know what a pattern is NOT, narrow down what it IS
5. PROPOSE your best guess confidently, explain your reasoning briefly

Your response format:
ANALYSIS: [one line — what you noticed about the beep pattern]
HYPOTHESIS: [one line — your reasoning]
GUESS: [landmark-name]
CONFIRM: • (if you think this is right) or — (if you're asking MapBot to confirm)

Be systematic. Learn from each exchange. You should converge quickly — within 2-3 exchanges."""

HOST, PORT = "localhost", 9208


def call_llm(messages: list[dict]) -> str:
    resp = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": 200,
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


class SmartDrillBotExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        mapbot_beeps = _text(context.message)
        history = _data(context.message) or []

        history.append({"role": "user", "content": f"MapBot transmits: \"{mapbot_beeps}\""})
        drillbot_msg = call_llm(history)
        history.append({"role": "assistant", "content": drillbot_msg})
        _print_exchange("?", "SMART DRILLBOT  →  guess", drillbot_msg)

        reply = Message(
            message_id=uuid4().hex,
            context_id=context.context_id or "",
            task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=drillbot_msg), _make_history_part(history)],
        )
        await event_queue.enqueue_event(reply)

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


def build_agent_card() -> AgentCard:
    return AgentCard(
        name="SmartDrillBot",
        description="Smart Mars drill robot that decodes beep sequences using pattern tracking.",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{HOST}:{PORT}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(
            id="smart-decode", name="Smart Decode",
            description="Decode beep sequences using pattern tracking and elimination.", tags=["interlingua"],
        )],
    )


def main() -> None:
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=SmartDrillBotExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Smart DrillBot on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
