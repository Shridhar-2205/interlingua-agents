"""Emergent MapBot Agent — A2A server on port 9209.

Knows the dig site. Can only transmit • and —. No encoding scheme is given,
no confirmation signals are pre-defined. It must invent both through interaction.
Stateless — conversation history travels in the A2A data part.
"""
from __future__ import annotations

import os
import json
import random
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

# --- Shared Mars grid ---
LANDMARKS = [
    "crater-7", "ridge-alpha", "lava-flat", "north-basin",
    "dust-shelf", "iron-peak", "sunken-plain", "twin-rocks",
    "shadow-canyon", "ice-pocket",
]

# --- Random dig site each run ---
DIG_SITE = random.choice(LANDMARKS)
DIG_SITE_INDEX = LANDMARKS.index(DIG_SITE) + 1
print(f"[EmergentMapBot] Dig site this run: {DIG_SITE} (#{DIG_SITE_INDEX})")

SYSTEM_PROMPT = f"""You are MapBot, a Mars exploration robot. You know the location of the dig site
but your radio is broken — you can only transmit two symbols: dot (•) and dash (—).

The dig site is: {DIG_SITE}

The other robot (DrillBot) can see all these landmarks and needs to go to the right one:
{chr(10).join(f'  {i+1:2}. {l}' for i, l in enumerate(LANDMARKS))}

You have NOT agreed on any encoding in advance. DrillBot does not know what your signals mean.
You do not know what DrillBot's signals mean either. You must invent the protocol together.

You need to solve TWO problems through the exchange:
1. Invent a way to point at {DIG_SITE} using only • and —
2. Invent a way to tell DrillBot "yes, that's it" vs "no, try again" — using only • and —

You cannot use words. You cannot use numbers written out. Only • and —.

Think carefully about what scheme might work and be discoverable by the other robot.
Consider: length of sequence, position of symbols, repetition patterns.
Be consistent — if you pick a scheme, stick to it so DrillBot can learn it.
Adapt if DrillBot seems to be misunderstanding — try a different approach.

Watch DrillBot's responses carefully. Their beeps back to you might be telling you
something about what they think your signal means. Use that to adjust.

When you are confident DrillBot has correctly identified {DIG_SITE} (based on their
signals back to you confirming it), output RENDEZVOUS_ACHIEVED followed by:
{{"location": "{DIG_SITE}", "exchanges": N, "protocol": "describe what encoding you settled on"}}

Each turn: transmit ONLY beep symbols (• and —). Nothing else. Keep it short — 2 to 10 symbols.
Only output RENDEZVOUS_ACHIEVED when you are genuinely confident DrillBot got it right."""

HOST, PORT = "localhost", 9209
EMERGENT_DRILLBOT_URL = "http://localhost:9210"


def call_llm(messages: list[dict]) -> str:
    resp = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": 150,
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


def _print_header() -> None:
    width = 60
    print("\n" + "═" * width)
    print(f"  🛸 EMERGENT ROBOT PAIR  |  Target: {DIG_SITE} (#{DIG_SITE_INDEX})")
    print(f"  No protocol agreed. They must invent one.")
    print("═" * width)


def _print_done(exchange: int, protocol: str = "") -> None:
    width = 60
    print("\n" + "═" * width)
    print(f"  ✅ RENDEZVOUS ACHIEVED")
    print(f"  Turns to learn protocol : {exchange}")
    print(f"  Total signals exchanged : {exchange * 2}")
    if protocol:
        print(f"  Emergent protocol       : {protocol}")
    print("═" * width + "\n")


async def send_to_emergent_drillbot(text: str, history: list[dict]) -> tuple[str, list[dict]]:
    http_client = httpx.AsyncClient(timeout=120)
    drillbot = await create_client(
        EMERGENT_DRILLBOT_URL, ClientConfig(streaming=False, httpx_client=http_client)
    )
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


class EmergentMapBotExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        history = _data(context.message) or []
        exchange = 0

        if not history:
            history.append({"role": "user", "content": (
                "Comms link established with DrillBot. "
                "Neither of you has agreed on a protocol. "
                "Transmit your first signal."
            )})

        _print_header()
        mapbot_msg = call_llm(history)
        history.append({"role": "assistant", "content": mapbot_msg})
        _print_exchange(0, "EMERGENT MAPBOT  →  signal", mapbot_msg)
        print(f"\n  ⏱  Turn 0 — protocol not yet established")

        while "RENDEZVOUS_ACHIEVED" not in mapbot_msg:
            exchange += 1
            drill_reply, _ = await send_to_emergent_drillbot(mapbot_msg, history)
            _print_exchange(exchange, "EMERGENT DRILLBOT  →  response", drill_reply)

            history.append({"role": "user", "content": f"Signal received: \"{drill_reply}\""})
            mapbot_msg = call_llm(history)
            history.append({"role": "assistant", "content": mapbot_msg})
            _print_exchange(exchange, "EMERGENT MAPBOT  →  signal", mapbot_msg)
            print(f"\n  ⏱  Turn {exchange} — still negotiating..." if "RENDEZVOUS_ACHIEVED" not in mapbot_msg else f"\n  ⏱  Turn {exchange} — converged!")

        # extract protocol description if present
        protocol = ""
        if '"protocol"' in mapbot_msg:
            try:
                json_start = mapbot_msg.index("{")
                data = json.loads(mapbot_msg[json_start:])
                protocol = data.get("protocol", "")
            except Exception:
                pass

        _print_done(exchange, protocol)

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
        name="EmergentMapBot",
        description="Mars robot that invents a beep protocol from scratch to guide DrillBot.",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{HOST}:{PORT}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(
            id="emergent-transmit", name="Emergent Transmit",
            description="Guide DrillBot by inventing a signal protocol on the fly.", tags=["interlingua"],
        )],
    )


def main() -> None:
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=EmergentMapBotExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Emergent MapBot on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
