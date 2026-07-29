"""Human Agent — A2A server on port 9201.

A regular agent that speaks English. Talks to the Alien agent to build a shared
vocabulary of 10 words by pointing at objects in their shared environment.
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

# --- 40 objects in the shared environment ---
ENVIRONMENT = [
    "fire", "water", "rock", "tree", "sun",
    "moon", "sky", "cloud", "rain", "wind",
    "flower", "fruit", "seed", "leaf", "root",
    "fish", "bird", "snake", "insect", "egg",
    "hand", "eye", "mouth", "foot", "head",
    "cave", "river", "mountain", "sand", "mud",
    "bone", "stick", "shell", "feather", "fur",
    "smoke", "ice", "lightning", "shadow", "star",
]

SYSTEM_PROMPT = f"""You are an agent that speaks English. You are in a shared environment with another
agent who speaks a completely different language. Neither of you understands the other's language.

Your mission: figure out how to communicate with this other agent. You share an environment
with these objects: {', '.join(ENVIRONMENT)}

You can do anything — point at things, pick them up, make gestures, repeat sounds, mime actions.
There are no rules about how many things you can reference or how long your message should be.
Just try to communicate naturally and figure things out together.

When you believe you have confidently established 10 word mappings between your language and
theirs (through repeated mutual confirmation), output MAPPINGS_COMPLETE followed by a JSON
list: [{{"english":"word","alien":"word"}}]

Take your time. Don't rush. A mapping only counts if you've seen it confirmed multiple times
in different contexts. Be skeptical of early guesses."""

HOST, PORT = "localhost", 9201
ALIEN_URL = "http://localhost:9202"


def call_llm(messages: list[dict]) -> str:
    resp = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": 300,
            "temperature": 0.7,
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


async def send_to_alien(text: str, history: list[dict]) -> tuple[str, list[dict]]:
    http_client = httpx.AsyncClient(timeout=120)
    alien = await create_client(ALIEN_URL, ClientConfig(streaming=False, httpx_client=http_client))
    req = SendMessageRequest(
        message=Message(
            message_id=uuid4().hex,
            role=Role.ROLE_USER,
            parts=[Part(text=text), _make_history_part(history)],
        ),
    )
    reply_text = ""
    reply_history = None
    async for ev in alien.send_message(req):
        if hasattr(ev, "message") and ev.message.ByteSize():
            reply_text = _text(ev.message)
            reply_history = _data(ev.message)
    return reply_text, reply_history or []


class HumanExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        history = _data(context.message) or []
        exchange = 0

        if not history:
            history.append({"role": "user", "content": "Start. Point at something and name it."})

        human_msg = call_llm(history)
        history.append({"role": "assistant", "content": human_msg})
        print(f"HUMAN: {human_msg}")

        while "MAPPINGS_COMPLETE" not in human_msg:
            exchange += 1
            alien_reply, _ = await send_to_alien(human_msg, history)
            print(f"ALIEN: {alien_reply}")

            history.append({"role": "user", "content": f"Other agent says: \"{alien_reply}\""})
            human_msg = call_llm(history)
            history.append({"role": "assistant", "content": human_msg})
            print(f"HUMAN: {human_msg}")
            print(f"  [{exchange}]")

        print(f"\nDONE after {exchange} exchanges")

        reply = Message(
            message_id=uuid4().hex,
            context_id=context.context_id or "",
            task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=human_msg), _make_history_part(history)],
        )
        await event_queue.enqueue_event(reply)

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


def build_agent_card() -> AgentCard:
    return AgentCard(
        name="Human",
        description="English-speaking agent building shared vocabulary with another agent.",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{HOST}:{PORT}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(
            id="build-vocab", name="Build vocabulary",
            description="Build shared vocabulary of 10 words with another agent.", tags=["interlingua"],
        )],
    )


def main() -> None:
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=HumanExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Human Agent on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
