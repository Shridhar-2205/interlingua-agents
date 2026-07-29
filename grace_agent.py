"""Grace — stateless A2A ping-pong agent.

No state is stored in memory. All game state (both lexicons, round number,
current referent, proposed symbol) travels in a structured JSON `data` Part on
the A2A message (see a2a_state.py). Each call to execute() reads state from the
incoming message, does one step, and either responds (game over) or calls Rocky
with updated state. When the function returns, all local variables are gone —
the only surviving state is in the message.
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
from a2a.server.routes.agent_card_routes import create_agent_card_routes  # serves GET /.well-known/agent.json
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes        # serves POST / (JSON-RPC endpoint)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities, AgentCard, AgentExtension, AgentSkill,
    Message, Part, Role, SendMessageRequest,
)
from a2a.types.a2a_pb2 import AgentInterface

from a2a_state import pack_state, read_state
from signaling import MEANINGS, SYMBOLS, adopt, alignment, coin

# A2A extension URI — advertised on the agent card; game state rides in a data Part
EXT = "https://example.com/ext/emergent-lang/v1"

ROCKY_URL = "http://localhost:9102"  # Rocky's A2A endpoint
MAX_ROUNDS = 60  # safety net — stop even if not converged


class GraceExecutor(AgentExecutor):
    """Stateless executor — no instance variables, no stored state.

    State flow:
      1. Read game state from the incoming message's data Part
      2. Do one step (adopt incoming signal, then coin a new one)
      3. Either respond (done) or call Rocky with updated state in a data Part
      4. All local variables are discarded when this function returns
    """

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Read state from the incoming data Part — this is the ONLY source of truth
        state = read_state(context.message)

        if not state:
            # No state = trigger from Mission Control — initialize the game
            # Generate two conflicting lexicons so agents must negotiate
            pool = random.sample(SYMBOLS, len(MEANINGS) * 2)
            grace_lex = {m: pool[i] for i, m in enumerate(MEANINGS)}
            rocky_lex = {m: pool[len(MEANINGS) + i] for i, m in enumerate(MEANINGS)}
            rnd = 0
            print(f"[Grace] hop 0 | initializing lexicons")
            print(f"[Grace]   grace_lex: {grace_lex}")
            print(f"[Grace]   rocky_lex: {rocky_lex}")
        else:
            # State arrives from Rocky's last message — read it all from the data Part
            grace_lex = dict(state.get("grace_lex", {}))
            rocky_lex = dict(state.get("rocky_lex", {}))
            rnd = int(state.get("round", 0))  # int() because JSON numbers deserialize as float
            signal = state.get("message")

            print(f"[Grace] hop {rnd} | received signal '{signal}' from Rocky")

            # Adopt Rocky's signal — update Grace's lexicon to match
            if signal:
                referent = state.get("referent")
                if referent:
                    print(f"[Grace] hop {rnd} | adopting '{signal}' → meaning '{referent}'")
                    adopt(grace_lex, referent, signal)
                    print(f"[Grace] hop {rnd} | grace_lex after adopt: {grace_lex}")

        # Stop condition: all 10 meanings agree, or max rounds reached
        score = alignment(grace_lex, rocky_lex)
        print(f"[Grace] hop {rnd} | alignment: {score:.0%}")
        if score == 1.0 or rnd >= MAX_ROUNDS:
            # Game over — respond directly, do NOT call Rocky
            # Response unwinds back through the call chain to Mission Control
            summary = f"done | rounds: {rnd} | alignment: {score:.0%} | grace: {grace_lex} | rocky: {rocky_lex}"
            print(f"[Grace] hop {rnd} | convergence reached: {summary}")
            reply = Message(
                message_id=uuid4().hex,
                context_id=context.context_id or "",
                task_id=context.task_id or "",
                role=Role.ROLE_AGENT,
                parts=[
                    Part(text=summary),
                    pack_state({"grace_lex": grace_lex, "rocky_lex": rocky_lex, "round": rnd}),
                ],
                extensions=[EXT],
            )
            await event_queue.enqueue_event(reply)
            return

        # Grace speaks — pick a disagreement and coin/reuse a symbol
        unresolved = [m for m in MEANINGS if grace_lex.get(m) != rocky_lex.get(m)]
        referent = unresolved[rnd % len(unresolved)] if unresolved else MEANINGS[0]
        sym = grace_lex.get(referent) or coin(grace_lex, rocky_lex)
        grace_lex[referent] = sym

        print(f"[Grace] hop {rnd} | speaking: '{sym}' for meaning '{referent}'")
        print(f"[Grace] hop {rnd} | unresolved meanings: {unresolved}")
        print(f"[Grace] hop {rnd} | sending to Rocky →")

        # Send to Rocky via A2A — full game state in a data Part, no memory kept
        rocky = await create_client(ROCKY_URL, ClientConfig(streaming=False))
        req = SendMessageRequest(
            message=Message(
                message_id=uuid4().hex, role=Role.ROLE_USER,
                parts=[
                    Part(text="signal"),
                    pack_state({
                        "grace_lex": grace_lex, "rocky_lex": rocky_lex,
                        "round": rnd + 1, "referent": referent, "message": sym,
                    }),
                ],
                extensions=[EXT],
            ),
        )

        # Wait for Rocky's response (he may ping-pong back to us before responding)
        result_text = ""
        result_state: dict = {}
        async for ev in rocky.send_message(req):
            if hasattr(ev, "message") and ev.message.ByteSize():
                result_text = next(
                    (p.text for p in ev.message.parts if p.WhichOneof("content") == "text"), ""
                )
                result_state = read_state(ev.message)

        # Pass through Rocky's response back to whoever called us
        reply = Message(
            message_id=uuid4().hex,
            context_id=context.context_id or "",
            task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=result_text), pack_state(result_state)],
            extensions=[EXT],
        )
        await event_queue.enqueue_event(reply)

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


def build_agent_card(host: str = "localhost", port: int = 9101) -> AgentCard:
    """Agent Card — served at GET /.well-known/agent.json for A2A discovery."""
    ext = AgentExtension(uri=EXT, description="Game state via a structured data Part.", required=False)
    ext.params.update({"keys": ["grace_lex", "rocky_lex", "round", "referent", "message"], "max_rounds": MAX_ROUNDS})
    return AgentCard(
        name="Grace",
        description="Stateless ping-pong signaling game agent (the astronaut).",
        version="2.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{host}:{port}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False, extensions=[ext]),
        skills=[AgentSkill(
            id="emerge", name="Run signaling game",
            description="Stateless ping-pong with Rocky until 10 meanings align.", tags=["emergent"],
        )],
    )


def main() -> None:
    host, port = "localhost", 9101
    card = build_agent_card(host, port)
    # A2A server setup — routes for agent card discovery + JSON-RPC message handling
    handler = DefaultRequestHandler(
        agent_executor=GraceExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Grace listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
