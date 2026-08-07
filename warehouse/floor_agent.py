"""The Floor, as an A2A service on :9208.

Stateless. Everything it has learned arrives in the message and goes back out in
the reply — it keeps nothing between calls. Kill it mid-session and restart it;
the next message still works.

Each request carries two things: last round's answer (so it can learn) and this
round's marks (so it can act). It replies with the box it took — or null, and
the list of marks it could not place. That list is the point: it is the Floor
telling the Office, on the record, what it was unable to check.

    python floor_agent.py
"""
from __future__ import annotations

import random
import uuid

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
    AgentCapabilities, AgentCard, AgentExtension, AgentSkill,
    Message, Part, Role,
)
from a2a.types.a2a_pb2 import AgentInterface

import wire
from wire import PORTS, floor_from, floor_state

import l9_envelope
from l9_envelope import EXT_URI, build_l9, to_data_part, from_a2a, agent_card_extension


class FloorExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        incoming = from_a2a(context.message)
        if incoming is None:
            await event_queue.enqueue_event(Message(
                message_id=uuid.uuid4().hex, role=Role.ROLE_AGENT,
                parts=[Part(text="floor: expected an emergence envelope")]))
            return

        d = incoming.data
        rnd = int(d.get("round", 0))
        honest = bool(d.get("honest", True))
        floor = floor_from(d.get("floor_state"), random.Random(rnd), honest)

        # 1. Last round's box was opened. Learn from it before doing anything else.
        reveal = d.get("reveal") or {}
        if reveal.get("truth"):
            floor.learn(list(reveal.get("marks", [])), reveal["truth"], round_no=rnd - 1)

        # 2. Act on this round's marks — take a box, or say we cannot tell.
        marks = list(d.get("marks", []))
        act = ({"choice": None, "grounded": False, "reason": "nothing asked", "unresolved": []}
               if not marks else floor.pick(marks))

        out = build_l9(
            sender="floor", recipients=["office"],
            episode=incoming.message.episode,
            parents=[incoming.message.id],
            topic=f"round:{rnd}",
            data={
                "round": rnd,
                "choice": act["choice"],
                "grounded": act["grounded"],
                "why": act["reason"],
                # the grounding report: what we could NOT check
                "unresolved": act["unresolved"],
                "floor_state": floor_state(floor),
            },
        )
        label = act["choice"] or "— can't tell"
        print(f"[floor] r{rnd} heard {' '.join(marks) or '(none)'} -> {label}")
        await event_queue.enqueue_event(Message(
            message_id=uuid.uuid4().hex,
            context_id=context.context_id or "", task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=f"r{rnd}: {label}"), to_data_part(out)],
            extensions=[EXT_URI],
        ))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


def build_card() -> AgentCard:
    spec = agent_card_extension()
    ext = AgentExtension(uri=spec["uri"], description=spec["description"],
                         required=spec["required"])
    ext.params.update(spec["params"])
    return AgentCard(
        name="Floor",
        description=("Warehouse picker. Reaches every shelf, never sees the order. "
                     "Reports what it could not check instead of guessing."),
        version="1.0.0",
        supported_interfaces=[AgentInterface(url=f"http://localhost:{PORTS['floor']}/",
                                             protocol_binding="JSONRPC")],
        default_input_modes=["text/plain"], default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False, extensions=[ext]),
        skills=[AgentSkill(id="pick", name="Pick a box",
                           description="Decode invented marks to a box, or report it cannot tell.",
                           tags=["emergent", "l9", "warehouse"])],
    )


def main() -> None:
    card = build_card()
    handler = DefaultRequestHandler(agent_executor=FloorExecutor(),
                                    task_store=InMemoryTaskStore(), agent_card=card)
    app = Starlette(routes=create_agent_card_routes(card)
                    + create_jsonrpc_routes(handler, rpc_url="/"))
    print(f"Floor on http://localhost:{PORTS['floor']}   (ext: {EXT_URI})")
    uvicorn.run(app, host="localhost", port=PORTS["floor"])


if __name__ == "__main__":
    main()
