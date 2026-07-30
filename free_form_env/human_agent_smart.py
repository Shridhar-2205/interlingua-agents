"""Human Agent (SMART) — A2A server on port 9201.

Same free-form A2A agent as human_agent.py, but it imports `l9.Mind` and calls it
before each turn: Mind tracks the alien's emerging vocabulary and injects a memory
+ strategy block into the prompt. Drop-in depth-A integration — the alien on 9202
can stay dumb; only this side gets smart.

Run this INSTEAD of human_agent.py (same port) against the unchanged alien_agent.py
to show a smart↔dumb pairing converges faster than the dumb↔dumb baseline.
"""
from __future__ import annotations

import os
import sys
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

# --- import the reusable Mind advisor from l9/ (sibling dir) ---
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from l9 import Mind

# --- LLM config ---
BASE_URL = os.environ.get("LLM_BASE_URL", "https://litellm.prod.outshift.ai")
API_KEY = os.environ.get("LLM_API_KEY", "sk-...")
MODEL = os.environ.get("LLM_MODEL", "bedrock/global.anthropic.claude-opus-4-6-v1")

ENVIRONMENT = [
    "fire", "water", "rock", "tree", "sun", "moon", "sky", "cloud", "rain", "wind",
    "flower", "fruit", "seed", "leaf", "root", "fish", "bird", "snake", "insect", "egg",
    "hand", "eye", "mouth", "foot", "head", "cave", "river", "mountain", "sand", "mud",
    "bone", "stick", "shell", "feather", "fur", "smoke", "ice", "lightning", "shadow", "star",
]

# Strategic persona (unlike the dumb baseline). The per-turn MEMORY & STRATEGY block
# supplied by Mind gives it the tracking/focus the baseline prompt lacks.
SYSTEM_PROMPT = f"""You are a methodical creature that speaks English, building a shared vocabulary
with another creature that speaks an invented language you cannot understand.

You share these objects: {', '.join(ENVIRONMENT)}

You are strategic and have a strong memory. Each turn you are given a MEMORY & STRATEGY note
summarising what you have learned about the other creature's sounds and the best next move.
Follow it: focus on ONE object at a time, say its English name clearly, and watch which sound
the other creature makes. Do not get distracted; do not forget what you have confirmed.

When you have 10 objects each confirmed with a consistent sound, output MAPPINGS_COMPLETE
followed by a JSON list of exactly 10 pairs: [{{"english":"word","alien":"word"}}]."""

HOST, PORT = "localhost", 9201
ALIEN_URL = "http://localhost:9202"


def call_llm(messages: list[dict]) -> str:
    resp = httpx.post(
        f"{BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"model": MODEL,
              "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
              "max_tokens": 300, "temperature": 0.7},
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
    req = SendMessageRequest(message=Message(
        message_id=uuid4().hex, role=Role.ROLE_USER,
        parts=[Part(text=text), _make_history_part(history)]))
    reply_text, reply_history = "", None
    async for ev in alien.send_message(req):
        if hasattr(ev, "message") and ev.message.ByteSize():
            reply_text = _text(ev.message)
            reply_history = _data(ev.message)
    return reply_text, reply_history or []


class SmartHumanExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        history = _data(context.message) or []
        mind = Mind("human", ENVIRONMENT, call_llm, ground_threshold=3, target=10)  # <-- the wiring
        exchange = 0

        if not history:
            history.append({"role": "user", "content": "Start. Point at something and name it."})

        def think() -> str:
            mind.observe(history)                                   # track the alien's vocabulary
            msgs = history + [{"role": "system", "content": mind.advise().prompt}]  # inject strategy
            out = call_llm(msgs)
            history.append({"role": "assistant", "content": out})
            mind.record(out)
            return out

        human_msg = think()
        print(f"HUMAN: {human_msg}")

        while "MAPPINGS_COMPLETE" not in human_msg:
            exchange += 1
            alien_reply, _ = await send_to_alien(human_msg, history)
            print(f"ALIEN: {alien_reply}")
            history.append({"role": "user", "content": f'Other agent says: "{alien_reply}"'})
            human_msg = think()
            m = mind.metrics()
            print(f"HUMAN: {human_msg}")
            print(f"  [{exchange}] confirmed {m['confirmed']}/{m['target']}")

        print(f"\nDONE after {exchange} exchanges | {mind.metrics()}")
        await event_queue.enqueue_event(Message(
            message_id=uuid4().hex, context_id=context.context_id or "", task_id=context.task_id or "",
            role=Role.ROLE_AGENT, parts=[Part(text=human_msg), _make_history_part(history)]))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


def build_agent_card() -> AgentCard:
    return AgentCard(
        name="Human (smart)",
        description="English agent with an l9.Mind Theory-of-Mind advisor; builds shared vocabulary.",
        version="1.0.0",
        supported_interfaces=[AgentInterface(url=f"http://{HOST}:{PORT}/", protocol_binding="JSONRPC")],
        default_input_modes=["text/plain"], default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(id="build-vocab", name="Build vocabulary (ToM)",
                           description="Build shared vocabulary using a Theory-of-Mind advisor.",
                           tags=["interlingua", "tom"])],
    )


def main() -> None:
    card = build_agent_card()
    handler = DefaultRequestHandler(agent_executor=SmartHumanExecutor(),
                                    task_store=InMemoryTaskStore(), agent_card=card)
    app = Starlette(routes=create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/"))
    print(f"Human Agent (SMART, l9.Mind) on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
