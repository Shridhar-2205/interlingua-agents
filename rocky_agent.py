"""Rocky — stateless A2A ping-pong agent.

No state is stored in memory. All game state (both lexicons, round number,
current referent) travels in A2A message metadata. Each call to execute()
reads state from the incoming message, does one step, and either responds
(game over) or calls Grace with updated state. When the function returns,
all local variables are gone — the only surviving state is in the message.
"""
from __future__ import annotations

from uuid import uuid4

import uvicorn
from starlette.applications import Starlette
from typing_extensions import override

# A2A SDK — client (sends messages to Grace) and server (receives messages)
from a2a.client import ClientConfig, create_client
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes  # serves GET /.well-known/agent.json
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes        # serves POST / (JSON-RPC endpoint)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities, AgentCard, AgentExtension, AgentSkill,
    Message, Part, Role, SendMessageRequest,
)
from a2a.types.a2a_pb2 import AgentInterface
from google.protobuf.json_format import MessageToDict

from signaling import MEANINGS, adopt, alignment, coin

# A2A extension URI — metadata keys are namespaced under this
EXT = "https://example.com/ext/emergent-lang/v1"
CONTEXT = f"{EXT}/context"  # carries: grace_lex, rocky_lex, round, referent
MESSAGE = f"{EXT}/message"  # carries: the symbol being proposed

GRACE_URL = "http://localhost:9101"  # Grace's A2A endpoint
MAX_ROUNDS = 60  # safety net — stop even if not converged


class RockyExecutor(AgentExecutor):
    """Stateless executor — no instance variables, no stored state.

    State flow:
      1. Read game state from incoming A2A metadata
      2. Do one step (adopt incoming signal, then coin a new one)
      3. Either respond (done) or call Grace with updated state in metadata
      4. All local variables are discarded when this function returns
    """

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Read state from incoming A2A metadata — this is the ONLY source of truth
        md = context.metadata or {}
        ctx = md.get(CONTEXT) or {}
        grace_lex = dict(ctx.get("grace_lex", {}))
        rocky_lex = dict(ctx.get("rocky_lex", {}))
        rnd = int(ctx.get("round", 0))  # int() because JSON numbers deserialize as float
        referent = ctx.get("referent")
        signal = md.get(MESSAGE)

        print(f"[Rocky] hop {rnd} | received signal '{signal}' from Grace for meaning '{referent}'")

        # Adopt Grace's signal — update Rocky's lexicon to match
        if signal:
            print(f"[Rocky] hop {rnd} | adopting '{signal}' → meaning '{referent}'")
            adopt(rocky_lex, referent, signal)
            print(f"[Rocky] hop {rnd} | rocky_lex after adopt: {rocky_lex}")

        # Stop condition: all 10 meanings agree, or max rounds reached
        score = alignment(grace_lex, rocky_lex)
        print(f"[Rocky] hop {rnd} | alignment: {score:.0%}")
        if score == 1.0 or rnd >= MAX_ROUNDS:
            # Game over — respond directly, do NOT call Grace
            # Response unwinds back through the call chain to Mission Control
            summary = f"done | rounds: {rnd} | alignment: {score:.0%} | grace: {grace_lex} | rocky: {rocky_lex}"
            print(f"[Rocky] hop {rnd} | convergence reached: {summary}")
            reply = Message(
                message_id=uuid4().hex,
                context_id=context.context_id or "",
                task_id=context.task_id or "",
                role=Role.ROLE_AGENT,
                parts=[Part(text=summary)],
                extensions=[EXT],
            )
            reply.metadata.update({CONTEXT: {"grace_lex": grace_lex, "rocky_lex": rocky_lex, "round": rnd}})
            await event_queue.enqueue_event(reply)
            return

        # Rocky speaks — pick a disagreement and coin/reuse a symbol
        unresolved = [m for m in MEANINGS if grace_lex.get(m) != rocky_lex.get(m)]
        referent = unresolved[rnd % len(unresolved)] if unresolved else MEANINGS[0]
        sym = rocky_lex.get(referent) or coin(rocky_lex, grace_lex)
        rocky_lex[referent] = sym

        print(f"[Rocky] hop {rnd} | speaking: '{sym}' for meaning '{referent}'")
        print(f"[Rocky] hop {rnd} | unresolved meanings: {unresolved}")
        print(f"[Rocky] hop {rnd} | sending to Grace →")

        # Send to Grace via A2A — full game state in metadata, no memory kept
        grace = await create_client(GRACE_URL, ClientConfig(streaming=False))
        req = SendMessageRequest(
            message=Message(
                message_id=uuid4().hex, role=Role.ROLE_USER,
                parts=[Part(text="signal")], extensions=[EXT],
            ),
        )
        # All state goes into metadata — nothing stored in memory
        req.metadata.update({
            CONTEXT: {"grace_lex": grace_lex, "rocky_lex": rocky_lex, "round": rnd + 1, "referent": referent},
            MESSAGE: sym,
        })

        # Wait for Grace's response (she may ping-pong back to us before responding)
        result_text = ""
        result_metadata = {}
        async for ev in grace.send_message(req):
            if hasattr(ev, "message") and ev.message.ByteSize():
                result_text = ev.message.parts[0].text if ev.message.parts else ""
                result_metadata = MessageToDict(ev.message.metadata) if ev.message.metadata.ByteSize() else {}

        # Pass through Grace's response back to whoever called us
        reply = Message(
            message_id=uuid4().hex,
            context_id=context.context_id or "",
            task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=result_text)],
            extensions=[EXT],
        )
        reply.metadata.update(result_metadata)
        await event_queue.enqueue_event(reply)

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


def build_agent_card(host: str = "localhost", port: int = 9102) -> AgentCard:
    """Agent Card — served at GET /.well-known/agent.json for A2A discovery."""
    ext = AgentExtension(uri=EXT, description="Game state via extension.", required=True)
    ext.params.update({"keys": ["context", "message"]})
    return AgentCard(
        name="Rocky",
        description="Stateless ping-pong signaling game peer (the Eridian).",
        version="2.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{host}:{port}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False, extensions=[ext]),
        skills=[AgentSkill(
            id="signal", name="Signaling game",
            description="Stateless ping-pong: one step per call.", tags=["emergent"],
        )],
    )


def main() -> None:
    host, port = "localhost", 9102
    card = build_agent_card(host, port)
    # A2A server setup — routes for agent card discovery + JSON-RPC message handling
    handler = DefaultRequestHandler(
        agent_executor=RockyExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Rocky listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
