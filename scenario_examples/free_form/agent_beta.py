"""Agent Beta — free-form A2A agent on port 9302.

Plain LLM-driven agent that speaks an invented language. Receives messages from
Agent Alpha and responds. No Theory of Mind, no signaling, no ELP — just raw LLM.
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

BASE_URL = os.environ.get("LLM_BASE_URL", "https://litellm.prod.outshift.ai")
API_KEY = os.environ.get("LLM_API_KEY", "sk-...")
MODEL = os.environ.get("LLM_MODEL", "bedrock/global.anthropic.claude-opus-4-6-v1")

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
You do NOT have a fixed vocabulary — you invent new sounds spontaneously each time.

Environment (things you can perceive): {', '.join(ENVIRONMENT)}

You have no pre-existing language. Each time you want to refer to something, you make up
a sound on the spot. You are NOT consistent — sometimes you use a different sound for the
same thing. You are easily confused about what the other creature is pointing at.

EVERY response must contain an invented sound. Format:
*[gesture/action]* [INVENTED SOUND]

You are reactive and confused. You often:
- Misunderstand what the other creature is pointing at
- Point at the wrong thing entirely
- Invent a new sound even for things you've named before
- Get distracted by something else in the environment

RULES:
- NEVER write English words (fire, water, rock, etc.)
- ALWAYS end with an invented sound spoken aloud
- Sounds should be 1-2 syllables (like: vrk, tuu, mab, glisk, pho, zeel, krin)
- One object per turn, keep it short
- Be inconsistent — you are a confused creature with no fixed language"""

HOST, PORT = "localhost", 9302


def call_llm(messages: list[dict]) -> str:
    import time
    for attempt in range(5):
        resp = httpx.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"model": MODEL,
                  "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                  "max_tokens": 100, "temperature": 1.0},
            timeout=90,
        )
        if resp.status_code == 503 or resp.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    resp.raise_for_status()
    return ""


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


class BetaExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        alpha_msg = _text(context.message)
        history = _data(context.message) or []

        history.append({"role": "user", "content": f'Other agent says: "{alpha_msg}"'})
        try:
            beta_msg = call_llm(history)
        except Exception as e:
            print(f"BETA: [LLM error: {e}]", flush=True)
            beta_msg = "*confused silence*"
        history.append({"role": "assistant", "content": beta_msg})
        print(f"BETA: {beta_msg}", flush=True)

        reply = Message(
            message_id=uuid4().hex,
            context_id=context.context_id or "",
            task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=beta_msg), _make_history_part(history)],
        )
        await event_queue.enqueue_event(reply)

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


def build_agent_card() -> AgentCard:
    return AgentCard(
        name="Beta (free-form)",
        description="Agent that speaks an invented language, plain LLM, no ToM.",
        version="1.0.0",
        supported_interfaces=[AgentInterface(url=f"http://{HOST}:{PORT}/", protocol_binding="JSONRPC")],
        default_input_modes=["text/plain"], default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(id="speak-alien", name="Speak alien (free-form)",
                           description="Respond in invented language.", tags=["interlingua"])],
    )


def main() -> None:
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=BetaExecutor(), task_store=InMemoryTaskStore(), agent_card=card)
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Beta Agent (free-form) on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
