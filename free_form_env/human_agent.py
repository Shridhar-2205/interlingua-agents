"""Human Agent — A2A server on port 9201.

Triggered externally (e.g. curl / A2A client). On trigger, ping-pongs with the
Alien agent via A2A until the human believes it has established agreement on
10 out of 40 objects in the shared environment. Then it stops and returns the
mapping it thinks they've agreed on.
"""
from __future__ import annotations

import os
import json
from uuid import uuid4

import httpx
import uvicorn
from starlette.applications import Starlette
from typing_extensions import override

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

# --- 40 fixed objects in the shared environment ---
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

# --- Persona ---
SYSTEM_PROMPT = f"""You are a human linguist stranded on an alien planet. You speak only English.
You are trying to establish communication with an alien being.
You cannot understand anything the alien says — it sounds like gibberish to you.

You are both in an environment that contains these 40 objects:
{', '.join(ENVIRONMENT)}

You can point at objects, pick them up, gesture, mime actions, repeat words.
Try to teach the alien English words by pointing at things and naming them.
Also try to learn what the alien calls things by watching what they point at.

Just talk naturally. Keep responses to 2-3 sentences max.
Describe your physical actions in [brackets] like [points at the fire].
Focus on one or two objects at a time. Be patient and repetitive.

IMPORTANT: As you converse, mentally track which alien words you believe correspond
to which English words. When you are confident you have identified 10 word mappings
(alien word = English object), end your message with exactly:
MAPPINGS_COMPLETE
followed by a JSON list like: [{{"english":"fire","alien":"vrk"}}, ...]
Only do this when you are truly confident about 10 mappings from repeated confirmation."""

HOST, PORT = "localhost", 9201
ALIEN_URL = "http://localhost:9202"


def call_llm(messages: list[dict]) -> str:
    resp = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": 400,
            "temperature": 0.7,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _text(msg: Message) -> str:
    return next((p.text for p in msg.parts if p.WhichOneof("content") == "text"), "")


async def send_to_alien(text: str) -> str:
    http_client = httpx.AsyncClient(timeout=120)
    alien = await create_client(ALIEN_URL, ClientConfig(streaming=False, httpx_client=http_client))
    req = SendMessageRequest(
        message=Message(message_id=uuid4().hex, role=Role.ROLE_USER, parts=[Part(text=text)]),
    )
    reply = ""
    async for ev in alien.send_message(req):
        if hasattr(ev, "message") and ev.message.ByteSize():
            reply = _text(ev.message)
    return reply


class HumanExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        history: list[dict] = []
        exchange = 0

        print("\n" + "=" * 60)
        print("  FIRST CONTACT — Human meets Alien (A2A over HTTP)")
        print("  Environment: 40 shared objects")
        print("  Goal: agree on 10 word mappings, then stop")
        print("=" * 60 + "\n")

        # First utterance
        history.append({"role": "user", "content": "You just noticed the alien being. Start trying to communicate by pointing at something nearby."})
        human_msg = call_llm(history)
        history.append({"role": "assistant", "content": human_msg})
        print(f"HUMAN: {human_msg}\n")

        while "MAPPINGS_COMPLETE" not in human_msg:
            exchange += 1

            # Send to alien via A2A
            alien_reply = await send_to_alien(human_msg)
            print(f"ALIEN: {alien_reply}")

            # Generate human response
            history.append({"role": "user", "content": f"The alien responds: \"{alien_reply}\""})
            human_msg = call_llm(history)
            history.append({"role": "assistant", "content": human_msg})
            print(f"HUMAN: {human_msg}")
            print(f"  [exchange {exchange}]\n")

        # Extract the mappings JSON from the final message
        print("\n" + "=" * 60)
        print(f"  DONE after {exchange} exchanges!")
        print("=" * 60)
        if "MAPPINGS_COMPLETE" in human_msg:
            json_part = human_msg.split("MAPPINGS_COMPLETE")[-1].strip()
            print(f"  Mappings: {json_part}")
        print()

        reply = Message(
            message_id=uuid4().hex,
            context_id=context.context_id or "",
            task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=human_msg)],
        )
        await event_queue.enqueue_event(reply)

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


def build_agent_card() -> AgentCard:
    return AgentCard(
        name="Human",
        description="An English-speaking linguist building a shared language with an alien.",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{HOST}:{PORT}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(
            id="first-contact", name="First contact",
            description="Talk with the Alien until 10 word mappings are established.", tags=["firstcontact"],
        )],
    )


def main() -> None:
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=HumanExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Human Agent listening on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
