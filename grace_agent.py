"""Grace — stateless A2A ping-pong agent.

No state is stored in memory. All game state (both lexicons, round number,
proposals) travels in A2A message metadata. Each call to execute() reads
state from the incoming message, does one step, and either responds (game
over) or calls Rocky with updated state. When the function returns, all
local variables are gone — the only surviving state is in the message.

Smart convergence features:
  - Mutual exclusivity: coin_exclusive() never picks a conflicting symbol
  - Batch proposals: all disagreements proposed in one round
  - Confidence scores: lower-confidence agent yields, prevents flip-flopping
"""
from __future__ import annotations

import random
from uuid import uuid4

import uvicorn
from starlette.applications import Starlette
from typing_extensions import override

# A2A SDK — client (sends messages to Rocky) and server (receives messages)
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
from google.protobuf.json_format import MessageToDict

from signaling import (
    MEANINGS, SYMBOLS, CONFIDENCE_COINED,
    alignment, coin_exclusive, propose_batch, resolve_batch, get_symbol,
)

# A2A extension URI — metadata keys are namespaced under this
EXT = "https://example.com/ext/emergent-lang/v1"
CONTEXT = f"{EXT}/context"      # carries: grace_lex, rocky_lex, round
PROPOSALS = f"{EXT}/proposals"  # carries: list of {referent, symbol, confidence}

ROCKY_URL = "http://localhost:9102"
MAX_ROUNDS = 60


def init_lexicon() -> dict:
    """Generate a random initial lexicon with confidence scores."""
    pool = random.sample(SYMBOLS, len(MEANINGS))
    return {m: {"symbol": pool[i], "confidence": CONFIDENCE_COINED} for i, m in enumerate(MEANINGS)}


class GraceExecutor(AgentExecutor):
    """Stateless executor — no instance variables, no stored state.

    State flow:
      1. Read game state from incoming A2A metadata
      2. Resolve incoming proposals (if any) using confidence-based yielding
      3. Check alignment — stop if converged
      4. Generate batch proposals for all remaining disagreements
      5. Send to Rocky via A2A — all state in metadata, nothing in memory
    """

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Read state from incoming A2A metadata — the ONLY source of truth
        md = context.metadata or {}
        ctx = md.get(CONTEXT)

        if ctx is None:
            # No metadata = trigger from Mission Control — initialize the game
            grace_lex = init_lexicon()
            rocky_lex = init_lexicon()
            rnd = 0
        else:
            grace_lex = dict(ctx.get("grace_lex", {}))
            rocky_lex = dict(ctx.get("rocky_lex", {}))
            rnd = int(ctx.get("round", 0))

            # Process Rocky's proposals — confidence determines who yields
            proposals = md.get(PROPOSALS, [])
            if proposals:
                grace_lex = resolve_batch(grace_lex, proposals)

        # Stop condition: all 10 meanings agree, or max rounds reached
        score = alignment(grace_lex, rocky_lex)
        if score == 1.0 or rnd >= MAX_ROUNDS:
            summary = f"done | rounds: {rnd} | alignment: {score:.0%} | grace: {grace_lex} | rocky: {rocky_lex}"
            print(summary)
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

        # Batch propose — all disagreements at once, with confidence
        proposals = propose_batch(grace_lex, rocky_lex)

        # Send to Rocky via A2A — full state in metadata, nothing stored in memory
        rocky = await create_client(ROCKY_URL, ClientConfig(streaming=False))
        req = SendMessageRequest(
            message=Message(
                message_id=uuid4().hex, role=Role.ROLE_USER,
                parts=[Part(text="signal")], extensions=[EXT],
            ),
        )
        req.metadata.update({
            CONTEXT: {"grace_lex": grace_lex, "rocky_lex": rocky_lex, "round": rnd + 1},
            PROPOSALS: proposals,
        })

        # Wait for Rocky's response (he may ping-pong back before responding)
        result_text = ""
        result_metadata = {}
        async for ev in rocky.send_message(req):
            if hasattr(ev, "message") and ev.message.ByteSize():
                result_text = ev.message.parts[0].text if ev.message.parts else ""
                result_metadata = MessageToDict(ev.message.metadata) if ev.message.metadata.ByteSize() else {}

        # Pass through Rocky's response back to caller
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


def build_agent_card(host: str = "localhost", port: int = 9101) -> AgentCard:
    """Agent Card — served at GET /.well-known/agent.json for A2A discovery."""
    ext = AgentExtension(uri=EXT, description="Game state via extension.", required=False)
    ext.params.update({"keys": ["context", "proposals"], "max_rounds": MAX_ROUNDS})
    return AgentCard(
        name="Grace",
        description="Stateless ping-pong signaling game agent (the astronaut).",
        version="3.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{host}:{port}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False, extensions=[ext]),
        skills=[AgentSkill(
            id="emerge", name="Run signaling game",
            description="Stateless ping-pong with Rocky — batch proposals + confidence.", tags=["emergent"],
        )],
    )


def main() -> None:
    host, port = "localhost", 9101
    card = build_agent_card(host, port)
    handler = DefaultRequestHandler(
        agent_executor=GraceExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Grace listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
