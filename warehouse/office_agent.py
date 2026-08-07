"""The Office, as an A2A service on :9207 — and the driver of the session.

Mission Control triggers it once; it then works through the orders, calling the
Floor over A2A for each one, and finally answers Mission Control with the tally
and the glossary.

Asymmetric on purpose. In Grace/Rocky both sides propose and the calls ping-pong.
Here only the Office speaks and only the Floor acts, which is how most real
systems are shaped — and it means a flat loop rather than N-deep recursion.

Stateless: the Office carries both its own memory and the Floor's in the
envelope, and neither service holds anything between calls.

    python floor_agent.py &
    python office_agent.py &
    python trigger.py
"""
from __future__ import annotations

import random
import uuid

import httpx
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

import catalogue
import wire
from wire import PORTS, floor_state, office_from, office_state

import signaling
import l9_envelope
from l9_envelope import EXT_URI, build_l9, to_data_part, from_a2a, agent_card_extension

DEFAULT_ORDERS = 60


def _config(text: str) -> dict:
    """Read 'orders=60 seed=3 honest=true' off the trigger's text part."""
    cfg = {"orders": DEFAULT_ORDERS, "seed": 3, "honest": True}
    for tok in (text or "").split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            if k == "honest":
                cfg[k] = v.lower() not in ("false", "0", "no")
            elif k in cfg:
                cfg[k] = int(v)
    return cfg


class OfficeExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        text = next((p.text for p in context.message.parts
                     if p.WhichOneof("content") == "text"), "")
        cfg = _config(text)
        orders, seed, honest = cfg["orders"], cfg["seed"], cfg["honest"]
        episode = l9_envelope.episode_urn("warehouse", uuid.uuid4().hex)

        rng = random.Random(seed)
        office = office_from({}, random.Random(seed + 1))
        fstate: dict = {}
        history: list[dict] = []
        right = wrong = refused = 0
        wrong_list: list[tuple[str, str]] = []
        reveal: dict = {}

        hc = httpx.AsyncClient(timeout=60)
        floor = await create_client(f"http://localhost:{PORTS['floor']}",
                                    ClientConfig(streaming=False, httpx_client=hc))
        print(f"[office] session: {orders} orders, seed {seed}, "
              f"{'honest' if honest else 'yes-man'} floor")

        for n in range(1, orders + 1):
            ordered = rng.choice(catalogue.products())      # only we see this
            msg = office.describe(ordered)

            out = build_l9(
                sender="office", recipients=["floor"], episode=episode,
                topic=f"round:{n}",
                data={
                    "round": n, "orders": orders, "honest": honest,
                    "marks": msg["symbols"],
                    "basis": msg["basis"],          # what we are going on
                    "reveal": reveal,               # last round's answer
                    "floor_state": fstate,
                    "office_state": office_state(office),
                },
            )
            reply = await self._ask(floor, out, n)
            if reply is None:
                break
            fstate = reply.get("floor_state", fstate)
            choice, unresolved = reply.get("choice"), list(reply.get("unresolved", []))

            if choice is None:
                refused += 1
            else:
                if choice == ordered:
                    right += 1
                else:
                    wrong += 1
                    wrong_list.append((ordered, choice))
                history = signaling.record_outcome(history, ordered, "".join(msg["symbols"]),
                                                   True, "floor",
                                                   grounded=bool(reply.get("grounded")))

            office.learn(msg["basis"], unresolved, choice == ordered, round_no=n)
            reveal = {"marks": msg["symbols"], "truth": ordered}

        # one last hop so the Floor learns the final box too
        final = build_l9(sender="office", recipients=["floor"], episode=episode,
                         topic="round:final",
                         data={"round": orders + 1, "honest": honest, "marks": [],
                               "reveal": reveal, "floor_state": fstate})
        last = await self._ask(floor, final, orders + 1)
        if last:
            fstate = last.get("floor_state", fstate)
        await hc.aclose()

        summary = {
            "orders": orders, "right": right, "wrong": wrong, "refused": refused,
            "wrong_deliveries": [{"ordered": o, "sent": s} for o, s in wrong_list],
            "gar": signaling.gar(history), "scr": signaling.scr(history),
            "provenance_weight": signaling.provenance_weight(history),
            "glossary": {s: " + ".join(m) for s, m in fstate.get("meaning", {}).items()},
            "office_meant": {s: f for f, s in office.symbol_of.items()},
            "unresolvable": catalogue.twins(),
            "office_state": office_state(office), "floor_state": fstate,
        }
        label = (f"done | {orders} orders | right {right} | WRONG {wrong} | "
                 f"asked for help {refused} | W {summary['provenance_weight']}")
        print(f"[office] {label}")

        done = build_l9(sender="office", recipients=["mission-control"],
                        episode=episode, topic="summary", data=summary)
        await event_queue.enqueue_event(Message(
            message_id=uuid.uuid4().hex,
            context_id=context.context_id or "", task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=label), to_data_part(done)],
            extensions=[EXT_URI],
        ))

    async def _ask(self, floor, envelope, n: int) -> dict | None:
        """One A2A round trip to the Floor; returns its payload."""
        req = SendMessageRequest(message=Message(
            message_id=uuid.uuid4().hex, role=Role.ROLE_USER,
            parts=[Part(text=f"round {n}"), to_data_part(envelope)],
            extensions=[EXT_URI],
        ))
        async for ev in floor.send_message(req):
            if hasattr(ev, "message") and ev.message.ByteSize():
                got = from_a2a(ev.message)
                if got is not None:
                    return got.data
        return None

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


def build_card() -> AgentCard:
    spec = agent_card_extension()
    ext = AgentExtension(uri=spec["uri"], description=spec["description"],
                         required=spec["required"])
    ext.params.update(spec["params"])
    return AgentCard(
        name="Office",
        description=("Warehouse order desk. Sees every order, reaches no shelf. "
                     "Invents its own marks and learns which ones the Floor can check."),
        version="1.0.0",
        supported_interfaces=[AgentInterface(url=f"http://localhost:{PORTS['office']}/",
                                             protocol_binding="JSONRPC")],
        default_input_modes=["text/plain"], default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False, extensions=[ext]),
        skills=[AgentSkill(id="relay", name="Relay orders",
                           description="Describe ordered products in an emergent shorthand.",
                           tags=["emergent", "l9", "warehouse"])],
    )


def main() -> None:
    card = build_card()
    handler = DefaultRequestHandler(agent_executor=OfficeExecutor(),
                                    task_store=InMemoryTaskStore(), agent_card=card)
    app = Starlette(routes=create_agent_card_routes(card)
                    + create_jsonrpc_routes(handler, rpc_url="/"))
    print(f"Office on http://localhost:{PORTS['office']}   (ext: {EXT_URI})")
    uvicorn.run(app, host="localhost", port=PORTS["office"])


if __name__ == "__main__":
    main()
