"""Rocky — stateless A2A ping-pong agent with Theory of Mind.

No state is stored in memory. All game state (lexicons, round, history,
beliefs about Grace) travels in A2A message metadata.

Theory of Mind: Rocky models what Grace believes and predicts whether
she'll accept a proposal before sending it. He picks the proposal most
likely to succeed on the first try.

History: past proposals and outcomes travel in metadata so Rocky never
repeats a failed attempt.
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
from google.protobuf.json_format import MessageToDict

from signaling import (
    MEANINGS, alignment, adopt,
    propose_with_tom, decide_accept, record_outcome,
)

EXT = "https://example.com/ext/emergent-lang/v1"
CONTEXT = f"{EXT}/context"    # carries: grace_lex, rocky_lex, round, history
MESSAGE = f"{EXT}/message"    # carries: the symbol being proposed
REFERENT = f"{EXT}/referent"  # carries: what meaning is being proposed
RESPONSE = f"{EXT}/response"  # carries: accepted (true/false)

GRACE_URL = "http://localhost:9101"
MAX_ROUNDS = 60


class RockyExecutor(AgentExecutor):
    """Stateless executor with Theory of Mind — no instance variables.

    Each call:
      1. Read full state from A2A metadata (lexicons + history + round)
      2. If Grace just proposed: decide accept/reject using ToM
      3. If it's Rocky's turn to propose: pick best proposal using ToM
      4. Send to Grace or stop if converged
      5. All locals discarded on return — metadata is the only memory
    """

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        md = context.metadata or {}
        ctx = md.get(CONTEXT) or {}
        grace_lex = dict(ctx.get("grace_lex", {}))
        rocky_lex = dict(ctx.get("rocky_lex", {}))
        history = list(ctx.get("history", []))
        rnd = int(ctx.get("round", 0))

        # Grace just proposed — decide whether to accept
        signal = md.get(MESSAGE)
        referent = md.get(REFERENT)
        if signal and referent:
            accepted = decide_accept(rocky_lex, referent, signal, grace_lex, history)
            if accepted:
                adopt(rocky_lex, referent, signal)
            history = record_outcome(history, referent, signal, accepted, "grace")

        # Check stop condition
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
            reply.metadata.update({CONTEXT: {"grace_lex": grace_lex, "rocky_lex": rocky_lex, "round": rnd, "history": history}})
            await event_queue.enqueue_event(reply)
            return

        # Rocky's turn — use Theory of Mind to pick the best proposal
        proposal = propose_with_tom(rocky_lex, grace_lex, history)
        if proposal is None:
            score = alignment(grace_lex, rocky_lex)
            summary = f"done | rounds: {rnd} | alignment: {score:.0%} | grace: {grace_lex} | rocky: {rocky_lex}"
            reply = Message(
                message_id=uuid4().hex, context_id=context.context_id or "",
                task_id=context.task_id or "", role=Role.ROLE_AGENT,
                parts=[Part(text=summary)], extensions=[EXT],
            )
            reply.metadata.update({CONTEXT: {"grace_lex": grace_lex, "rocky_lex": rocky_lex, "round": rnd, "history": history}})
            await event_queue.enqueue_event(reply)
            return

        referent = proposal["referent"]
        sym = proposal["symbol"]
        rocky_lex[referent] = sym

        # Send to Grace via A2A — full state in metadata
        grace = await create_client(GRACE_URL, ClientConfig(streaming=False))
        req = SendMessageRequest(
            message=Message(
                message_id=uuid4().hex, role=Role.ROLE_USER,
                parts=[Part(text="signal")], extensions=[EXT],
            ),
        )
        req.metadata.update({
            CONTEXT: {"grace_lex": grace_lex, "rocky_lex": rocky_lex, "round": rnd + 1, "history": history},
            MESSAGE: sym,
            REFERENT: referent,
        })

        result_text = ""
        result_metadata = {}
        async for ev in grace.send_message(req):
            if hasattr(ev, "message") and ev.message.ByteSize():
                result_text = ev.message.parts[0].text if ev.message.parts else ""
                result_metadata = MessageToDict(ev.message.metadata) if ev.message.metadata.ByteSize() else {}

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
    ext = AgentExtension(uri=EXT, description="Game state + ToM via extension.", required=True)
    ext.params.update({"keys": ["context", "message", "referent", "response"]})
    return AgentCard(
        name="Rocky",
        description="Stateless ping-pong agent with Theory of Mind (the Eridian).",
        version="4.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{host}:{port}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False, extensions=[ext]),
        skills=[AgentSkill(
            id="signal", name="Signaling game",
            description="Stateless ping-pong with ToM: one step per call.", tags=["emergent"],
        )],
    )


def main() -> None:
    host, port = "localhost", 9102
    card = build_agent_card(host, port)
    handler = DefaultRequestHandler(
        agent_executor=RockyExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Rocky listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
