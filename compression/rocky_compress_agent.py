"""Rocky — stateless A2A listener for the Mission Log Relay.

No state is stored in memory. Rocky reconstructs each record from ONLY the wire
segments + the shared codebook carried in the incoming `data` Part (he never
sees the source record), then calls Grace back with his reconstruction. Same
stateless ping-pong / unwind pattern as the Lewis demo's rocky_agent.py.
"""
from __future__ import annotations

from uuid import uuid4

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
    AgentCapabilities, AgentCard, AgentExtension, AgentSkill,
    Message, Part, Role, SendMessageRequest,
)
from a2a.types.a2a_pb2 import AgentInterface

from compress_state import CompressionState, decode, encode
from compress import decode_record

EXT = "https://example.com/ext/emergent-compress/v1"
GRACE_URL = "http://localhost:9201"   # Grace's A2A endpoint


class RockyCompressExecutor(AgentExecutor):
    """Stateless executor — no instance variables, no stored state."""

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        state = decode(context.message)

        # Reconstruct from the wire + shared codebook ONLY — no access to truth.
        reconstruction = decode_record(state.wire or {}, state.codebook)
        state.reconstruction = reconstruction
        print(f"[Rocky] round {state.round} | wire={state.wire} "
              f"| decoded={reconstruction}")

        # Call Grace back so she can score this round.
        grace = await create_client(GRACE_URL, ClientConfig(streaming=False))
        req = SendMessageRequest(
            message=Message(
                message_id=uuid4().hex, role=Role.ROLE_USER,
                parts=[Part(text="input"), encode(state)],
                extensions=[EXT],
            ),
        )
        result_text = ""
        result_state: CompressionState = CompressionState()
        async for ev in grace.send_message(req):
            if hasattr(ev, "message") and ev.message.ByteSize():
                result_text = next(
                    (p.text for p in ev.message.parts if p.WhichOneof("content") == "text"), ""
                )
                result_state = decode(ev.message)

        reply = Message(
            message_id=uuid4().hex,
            context_id=context.context_id or "",
            task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=result_text), encode(result_state)],
            extensions=[EXT],
        )
        await event_queue.enqueue_event(reply)

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


def build_agent_card(host: str = "localhost", port: int = 9202) -> AgentCard:
    """Agent Card — served at GET /.well-known/agent.json for A2A discovery."""
    ext = AgentExtension(uri=EXT, description="Session state via a structured data Part.",
                         required=True)
    ext.params.update({"role": "listener"})
    return AgentCard(
        name="Rocky-Compress",
        description="Stateless listener for the Mission Log Relay (the Eridian).",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{host}:{port}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False, extensions=[ext]),
        skills=[AgentSkill(
            id="reconstruct", name="Reconstruct mission-log record",
            description="Decode a wire + shared codebook back into a full record.",
            tags=["emergent", "compression"],
        )],
    )


def main() -> None:
    host, port = "localhost", 9202
    card = build_agent_card(host, port)
    handler = DefaultRequestHandler(
        agent_executor=RockyCompressExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Rocky-Compress listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
