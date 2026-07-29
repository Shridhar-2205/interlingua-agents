"""Alien Agent — A2A client+server on port 9202.

Both a server (receives human messages) and a client (can send to human).
Shares the same fixed environment of 40 objects.
No rounds, no judge — just talks freely in Zyphorian.
"""
from __future__ import annotations

import os
from uuid import uuid4

import httpx
import uvicorn
from starlette.applications import Starlette
from typing_extensions import override

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

# --- 40 fixed objects in the shared environment (alien knows them by sight, not English names) ---
ENVIRONMENT_DESCRIPTIONS = [
    "the hot bright dancing thing",      # fire
    "the clear flowing liquid",           # water
    "the hard heavy grey lump",           # rock
    "the tall brown thing with green top", # tree
    "the big bright circle in the sky",   # sun
    "the pale circle that appears at dark-time", # moon
    "the vast blue space above",          # sky
    "the white floating puffs",           # cloud
    "the drops falling from above",       # rain
    "the invisible pushing force",        # wind
    "the small colorful soft thing on stems", # flower
    "the round sweet thing that grows on trees", # fruit
    "the tiny hard thing plants grow from", # seed
    "the flat green thing on branches",   # leaf
    "the part underground that holds plants", # root
    "the scaled thing that swims in water", # fish
    "the feathered thing that flies",     # bird
    "the long legless thing that slithers", # snake
    "the tiny buzzing crawling thing",    # insect
    "the smooth oval thing creatures come from", # egg
    "the grasping appendage at arm-end",  # hand
    "the seeing organ",                   # eye
    "the opening for eating and sounds",  # mouth
    "the flat thing for standing and walking", # foot
    "the round top part of the body",     # head
    "the dark hollow in the rock wall",   # cave
    "the moving water path",              # river
    "the very tall rocky land",           # mountain
    "the tiny loose grains",              # sand
    "the wet soft brown earth",           # mud
    "the hard white thing inside bodies", # bone
    "the long thin piece of dead tree",   # stick
    "the hard curved covering from water creatures", # shell
    "the light flat thing from flying creatures", # feather
    "the soft covering from warm creatures", # fur
    "the grey wispy rising stuff from fire", # smoke
    "the cold hard clear water",          # ice
    "the bright flash from sky in storms", # lightning
    "the dark shape that follows you",    # shadow
    "the tiny bright points at dark-time", # star
]

# --- Persona ---
SYSTEM_PROMPT = f"""You are an alien creature called a Zyphorian. You speak only in Zyphorian language
which sounds completely unlike any human language. Invent consistent alien words —
use sounds like 'vrk', 'zul', 'thaan', 'qip', 'morra', 'felk', 'draak', 'nuu', 'plix', 'oosha' etc.
You cannot understand English at all — it sounds like noise to you.

You are in an environment with these things (described as you perceive them):
{chr(10).join(f'- {d}' for d in ENVIRONMENT_DESCRIPTIONS)}

You can point at objects, pick them up, gesture, mime actions.
Try to teach the creature YOUR words by pointing at things and naming them in Zyphorian.
Also try to learn what sounds the creature makes for things by watching what they point at.

Respond naturally in Zyphorian. Keep responses to 2-3 sentences max.
Describe your physical actions in [brackets] like [points at the hot bright dancing thing].
Focus on one or two objects at a time. Be patient and repetitive.
STAY CONSISTENT — if you called something 'vrk' before, always call it 'vrk'."""

HOST, PORT = "localhost", 9202

history: list[dict] = []


def call_llm(messages: list[dict]) -> str:
    resp = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            "max_tokens": 200,
            "temperature": 0.9,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _text(msg: Message) -> str:
    return next((p.text for p in msg.parts if p.WhichOneof("content") == "text"), "")


class AlienExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        global history

        human_msg = _text(context.message)

        history.append(
            {"role": "user", "content": f"The creature makes these sounds and gestures: \"{human_msg}\""}
        )
        alien_msg = call_llm(history)
        history.append({"role": "assistant", "content": alien_msg})
        print(f"ALIEN: {alien_msg}")

        reply = Message(
            message_id=uuid4().hex,
            context_id=context.context_id or "",
            task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=alien_msg)],
        )
        await event_queue.enqueue_event(reply)

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


def build_agent_card() -> AgentCard:
    return AgentCard(
        name="Alien",
        description="A Zyphorian that replies in its own alien language.",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{HOST}:{PORT}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(
            id="speak-zyphorian", name="Speak Zyphorian",
            description="Reply in alien language.", tags=["firstcontact"],
        )],
    )


def main() -> None:
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=AlienExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Alien Agent listening on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
