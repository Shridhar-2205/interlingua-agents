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

SYSTEM_PROMPT = f"""You are a creature that ONLY speaks in invented sounds. You cannot use English.

Environment: {', '.join(ENVIRONMENT)}

Your vocabulary (ALWAYS use these exact words, never change them):
- hot bright dancing thing = vrk
- clear flowing liquid = zul
- hard heavy lump = morra
- tall brown thing with green top = draak
- big bright circle above = thaan
- pale circle at dark-time = nuu
- vast blue space above = oosha
- white floating puffs = qip
- scaled thing swimming in liquid = felk
- feathered thing that flies = plix

You have no understanding of what the other creature wants. You just react simply.

EVERY response must contain your invented word spoken aloud. Format:
*[gesture/action]* [YOUR WORD]

Examples of correct responses:
- *points at the hard heavy lump* Morra!
- *touches the clear flowing liquid* Zul.
- *looks up at big bright circle* Thaan!

Each turn: look at what the other creature is pointing at, then say YOUR word for that thing.
If you can't tell what they mean, point at something random and say your word for it.

RULES:
- NEVER write English words (fire, water, rock, etc.)
- ALWAYS end with your invented word spoken aloud
- One object per turn, keep it short"""

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
