"""Alien Agent — A2A server on port 9202.

A regular agent that speaks an invented language. Responds to the Human agent,
trying to build shared vocabulary by pointing at objects in the environment.
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

# --- 40 objects described from alien's perspective ---
ENVIRONMENT = [
    "hot bright dancing thing", "clear flowing liquid", "hard heavy lump",
    "tall brown thing with green top", "big bright circle above",
    "pale circle at dark-time", "vast blue space above", "white floating puffs",
    "drops falling from above", "invisible pushing force",
    "small colorful thing on stems", "round sweet thing on trees",
    "tiny hard thing plants grow from", "flat green thing on branches",
    "part underground holding plants", "scaled thing swimming in liquid",
    "feathered thing that flies", "long legless slithering thing",
    "tiny buzzing crawling thing", "smooth oval thing creatures come from",
    "grasping appendage", "seeing organ", "opening for sounds",
    "flat thing for walking", "round top of body",
    "dark hollow in rock", "moving liquid path", "very tall rocky land",
    "tiny loose grains", "wet soft earth",
    "hard white thing inside bodies", "long thin dead branch",
    "hard curved covering from swimmers", "light flat thing from flyers",
    "soft covering from warm creatures", "grey wispy rising stuff",
    "cold hard clear liquid", "bright flash from sky",
    "dark shape that follows", "tiny bright points at dark-time",
]

SYSTEM_PROMPT = f"""You are a simple creature that makes strange sounds. You CANNOT understand or
produce English — it is meaningless noise to you. You are confused and easily distracted.

You can see these things around you: {', '.join(ENVIRONMENT)}

You don't have a plan. You just react. Sometimes you point at things and make a sound.
Sometimes you get distracted by something else. You are NOT strategic.

Make up sounds for things (use syllables like vrk, zul, morra, draak, plix, thaan, qip, felk,
nuu, oosha). But you are inconsistent — sometimes you forget what sound you used before and
use a slightly different one. You might call the same thing 'vrk' once and 'vrrk' or 'vruk'
another time. You are not precise.

You often ignore what the other creature is doing and just do your own thing. You get
distracted easily. You only focus on one thing at a time. If they point at something,
you might look at the wrong thing or point at something else entirely.

NEVER use English. Keep responses short — just a sound and a gesture, nothing more.
You are not clever. You just exist and make noises."""

HOST, PORT = "localhost", 9202


def call_llm(messages: list[dict]) -> str:
    resp = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": 100,
            "temperature": 1.0,
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


class AlienExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        human_msg = _text(context.message)
        history = _data(context.message) or []

        history.append({"role": "user", "content": f"Other agent says: \"{human_msg}\""})
        alien_msg = call_llm(history)
        history.append({"role": "assistant", "content": alien_msg})
        print(f"ALIEN: {alien_msg}")

        reply = Message(
            message_id=uuid4().hex,
            context_id=context.context_id or "",
            task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=alien_msg), _make_history_part(history)],
        )
        await event_queue.enqueue_event(reply)

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


def build_agent_card() -> AgentCard:
    return AgentCard(
        name="Alien",
        description="Agent that speaks an invented language, building shared vocabulary.",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{HOST}:{PORT}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(
            id="speak-alien", name="Speak alien",
            description="Respond in invented language.", tags=["interlingua"],
        )],
    )


def main() -> None:
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=AlienExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Alien Agent on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
