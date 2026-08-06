"""Agent Alpha — free-form A2A agent on port 9301.

Plain LLM-driven agent that speaks English. Sends free-text messages to Agent
Beta via A2A. No Theory of Mind, no signaling, no ELP — just two LLMs talking.

Drives the conversation loop: takes a turn, sends to Beta, receives reply, repeats.
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

BASE_URL = os.environ.get("LLM_BASE_URL", "https://litellm.prod.outshift.ai")
API_KEY = os.environ.get("LLM_API_KEY", "sk-...")
MODEL = os.environ.get("LLM_MODEL", "bedrock/global.anthropic.claude-opus-4-6-v1")

ENVIRONMENT = [
    "fire", "water", "rock", "tree", "sun", "moon", "sky", "cloud", "rain", "wind",
    "flower", "fruit", "seed", "leaf", "root", "fish", "bird", "snake", "insect", "egg",
    "hand", "eye", "mouth", "foot", "head", "cave", "river", "mountain", "sand", "mud",
    "bone", "stick", "shell", "feather", "fur", "smoke", "ice", "lightning", "shadow", "star",
]

SYSTEM_PROMPT = f"""You are a creature that speaks English, trying to build a shared vocabulary
with another creature that speaks an invented language you cannot understand.

You share a physical environment containing these objects: {', '.join(ENVIRONMENT)}

The other creature is confused and inconsistent — it may use different sounds for the
same object across turns. You must work hard to establish agreement:
- Point at ONE object, say its English name clearly
- Observe what sound the other creature makes back
- Repeat the SAME object multiple times to confirm the mapping is stable
- Only count a mapping as confirmed if the creature used the SAME sound for an object
  at least 3 times consistently

Do not trust a single response. The creature is unreliable. You must verify through
repetition. Do not get philosophical — just point and name things.

When you have 10 objects each confirmed with a consistent sound (seen at least 3 times),
output MAPPINGS_COMPLETE followed by a JSON list:
[{{"english":"word","alien":"word"}}]"""

HOST, PORT = "localhost", 9301
BETA_URL = "http://localhost:9302"
MAX_EXCHANGES = 30


def call_llm(messages: list[dict]) -> str:
    import time
    for attempt in range(5):
        resp = httpx.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"model": MODEL,
                  "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                  "max_tokens": 300, "temperature": 1.0},
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


async def send_to_beta(text: str, history: list[dict]) -> tuple[str, list[dict]]:
    http_client = httpx.AsyncClient(timeout=120)
    beta = await create_client(BETA_URL, ClientConfig(streaming=False, httpx_client=http_client))
    req = SendMessageRequest(message=Message(
        message_id=uuid4().hex, role=Role.ROLE_USER,
        parts=[Part(text=text), _make_history_part(history)]))
    reply_text, reply_history = "", None
    async for ev in beta.send_message(req):
        if hasattr(ev, "message") and ev.message.ByteSize():
            reply_text = _text(ev.message)
            reply_history = _data(ev.message)
    return reply_text, reply_history or []


class AlphaExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        history = _data(context.message) or []
        exchange = 0

        if not history:
            history.append({"role": "user", "content": "Start. Point at something and name it."})

        try:
            alpha_msg = call_llm(history)
        except Exception as e:
            print(f"ALPHA: [LLM error: {e}]", flush=True)
            alpha_msg = "*looks around confused*"
        history.append({"role": "assistant", "content": alpha_msg})
        print(f"ALPHA: {alpha_msg}", flush=True)

        while "MAPPINGS_COMPLETE" not in alpha_msg and exchange < MAX_EXCHANGES:
            exchange += 1
            try:
                beta_reply, _ = await send_to_beta(alpha_msg, history)
            except Exception as e:
                print(f"BETA:  [error: {e}]", flush=True)
                beta_reply = "*silence*"
            print(f"BETA:  {beta_reply}", flush=True)
            history.append({"role": "user", "content": f'Other agent says: "{beta_reply}"'})
            try:
                alpha_msg = call_llm(history)
            except Exception as e:
                print(f"ALPHA: [LLM error: {e}]", flush=True)
                alpha_msg = "*pauses*"
            history.append({"role": "assistant", "content": alpha_msg})
            print(f"ALPHA: {alpha_msg}", flush=True)
            print(f"  [{exchange}/{MAX_EXCHANGES}]", flush=True)

        status = "converged" if "MAPPINGS_COMPLETE" in alpha_msg else f"stopped at cap {MAX_EXCHANGES}"
        print(f"\nDONE ({status}) after {exchange} exchanges", flush=True)
        await event_queue.enqueue_event(Message(
            message_id=uuid4().hex, context_id=context.context_id or "", task_id=context.task_id or "",
            role=Role.ROLE_AGENT, parts=[Part(text=alpha_msg), _make_history_part(history)]))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


def build_agent_card() -> AgentCard:
    return AgentCard(
        name="Alpha (free-form)",
        description="English-speaking agent, plain LLM, no ToM — free-form vocabulary building.",
        version="1.0.0",
        supported_interfaces=[AgentInterface(url=f"http://{HOST}:{PORT}/", protocol_binding="JSONRPC")],
        default_input_modes=["text/plain"], default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(id="build-vocab", name="Build vocabulary (free-form)",
                           description="Build shared vocabulary via unstructured text.", tags=["interlingua"])],
    )


def main() -> None:
    card = build_agent_card()
    handler = DefaultRequestHandler(agent_executor=AlphaExecutor(),
                                    task_store=InMemoryTaskStore(), agent_card=card)
    app = Starlette(routes=create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/"))
    print(f"Alpha Agent (free-form) on http://{HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
