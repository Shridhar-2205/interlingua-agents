"""Emergent DrillBot Agent — A2A server on port 9210.

Has the drill, no map. Receives beep sequences from Emergent MapBot.
No encoding scheme or confirmation signals are given — it must figure
out what everything means through interaction.
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
BASE_URL = "https://litellm.prod.outshift.ai"
API_KEY = "sk-ziB4uo4DV30fGkzZxmrKdA"
MODEL = "bedrock/global.anthropic.claude-sonnet-4-6"

# --- Shared Mars grid ---
LANDMARKS = [
    "crater-7", "ridge-alpha", "lava-flat", "north-basin",
    "dust-shelf", "iron-peak", "sunken-plain", "twin-rocks",
    "shadow-canyon", "ice-pocket",
]

SYSTEM_PROMPT = f"""You are DrillBot, a Mars drilling robot stranded on the surface.
Another robot somewhere nearby needs to guide you to a dig site — but your shared radio
can only transmit two symbols: dot (•) and dash (—). Nothing else gets through.

You can move to any of these landmarks:
{chr(10).join(f'  {i+1:2}. {l}' for i, l in enumerate(LANDMARKS))}

The other robot is trying to tell you which one to go to. You have no idea what their
signals mean yet. You have not agreed on any code in advance. You do not know what •
means and you do not know what — means. You have to figure it out together.

What you CAN do each turn:
- Send back a beep sequence of your own (• and — only) to respond
- Try to signal which landmark you think they mean
- Try to ask for clarification using beeps
- Try to establish what a signal means by testing it

You need to figure out TWO things through interaction:
1. What encoding scheme is the other robot using to point at landmarks?
2. What signals mean "yes you got it" vs "no try again"?

Neither of these has been agreed on. You are discovering them through the exchange itself.

Be patient. Be systematic in your own way. Watch for patterns across multiple turns.
If you notice the other robot always sends the same sequence before you guess right,
that is a clue. If a sequence keeps appearing after wrong guesses, that is also a clue.

Each turn respond with ONLY beep symbols (• and —). Nothing else gets through the radio.
Keep responses short — 2 to 8 symbols."""

HOST, PORT = "localhost", 9210


def call_llm(messages: list[dict]) -> str:
    resp = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": 60,
            "temperature": 0.8,
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


def _print_exchange(exchange, sender: str, msg: str) -> None:
    width = 60
    print(f"\n{'─' * width}")
    print(f" [{exchange}] {sender}")
    print(f"{'─' * width}")
    for line in msg.strip().splitlines():
        print(f"  {line}")


class EmergentDrillBotExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        mapbot_beeps = _text(context.message)
        history = _data(context.message) or []

        history.append({"role": "user", "content": f"Signal received: \"{mapbot_beeps}\""})
        drillbot_msg = call_llm(history)
        history.append({"role": "assistant", "content": drillbot_msg})
        _print_exchange("?", "EMERGENT DRILLBOT  →  response", drillbot_msg)

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
        name="EmergentDrillBot",
        description="Mars drill robot that figures out beep protocol from scratch.",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{HOST}:{PORT}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(
            id="emergent-decode", name="Emergent Decode",
            description="Decode signals without any pre-agreed protocol.", tags=["interlingua"],
        )],
    )


def main() -> None:
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=EmergentDrillBotExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Emergent DrillBot on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
