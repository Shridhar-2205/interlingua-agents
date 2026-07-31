"""A2A transport for the emergence extension.

Wraps the pure reasoning core (agent.step) in a real A2A server+client, mirroring
the base repo's grace_agent.py / rocky_agent.py — but every message is our L9
envelope in a self-describing DataPart, and the Agent Card advertises the
`emergence` extension.

Each agent is server AND client. On each incoming message it runs one step() and
either responds (converged) or forwards the new state to the peer and awaits —
the terminal result unwinds back to Mission Control, exactly like the base game.
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

import agent
import signaling
import l9_envelope
from l9_envelope import EXT_URI, build_l9, to_data_part, from_a2a, agent_card_extension

PORTS = {"grace": 9101, "rocky": 9102}


def _label(nxt: dict) -> str:
    if nxt.get("decision") == "converged":
        h = nxt.get("history", [])
        return (f"done | round {nxt['round']} | align {signaling.alignment(nxt['lexicons']):.0%} "
                f"| GAR {signaling.gar(h)} SCR {signaling.scr(h)} W {signaling.provenance_weight(h)}")
    return f"{nxt.get('speaker')} proposes {nxt.get('proposal')} for {nxt.get('referent')}"


def _message(l9, role, ctx: RequestContext | None = None) -> Message:
    return Message(
        message_id=uuid4().hex,
        context_id=(ctx.context_id or "") if ctx else "",
        task_id=(ctx.task_id or "") if ctx else "",
        role=role,
        parts=[Part(text=_label(l9.data)), to_data_part(l9)],
        extensions=[EXT_URI],
    )


class EmergenceExecutor(AgentExecutor):
    def __init__(self, me: str, peer_id: str, peer_url: str) -> None:
        self.me, self.peer_id, self.peer_url = me, peer_id, peer_url

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        incoming = from_a2a(context.message)
        if incoming is None:
            # Mission Control trigger — open the episode, seed independent priors.
            state = agent.initial_state([self.me, self.peer_id])
            episode = l9_envelope.episode_urn("session", uuid4().hex)
            parents: list[str] = []
        else:
            state = incoming.data
            episode = incoming.message.episode
            parents = [incoming.message.id]

        nxt = agent.step(state, self.me)

        if nxt.get("decision") == "converged":
            out = build_l9(sender=self.me, recipients=[self.peer_id],
                           episode=episode, data=nxt, parents=parents)
            print(f"[{self.me}] {_label(nxt)}")
            await event_queue.enqueue_event(_message(out, Role.ROLE_AGENT, context))
            return

        # Propose to the peer and await the (terminal) response, then pass it up.
        out = build_l9(sender=self.me, recipients=[self.peer_id],
                       episode=episode, data=nxt, topic=f"concept:{nxt['referent']}",
                       parents=parents)
        print(f"[{self.me}] {_label(nxt)} → {self.peer_id}")

        peer = await create_client(self.peer_url, ClientConfig(streaming=False))
        req = SendMessageRequest(message=_message(out, Role.ROLE_USER))
        reply: Message | None = None
        async for ev in peer.send_message(req):
            if hasattr(ev, "message") and ev.message.ByteSize():
                reply = ev.message
        await event_queue.enqueue_event(reply or _message(out, Role.ROLE_AGENT, context))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


def build_card(me: str, host: str = "localhost") -> AgentCard:
    port = PORTS[me]
    ext_spec = agent_card_extension()
    ext = AgentExtension(uri=ext_spec["uri"], description=ext_spec["description"],
                         required=ext_spec["required"])
    ext.params.update(ext_spec["params"])
    return AgentCard(
        name=me.capitalize(),
        description=f"Emergent-convention agent ({me}) speaking the L9 emergence A2A extension.",
        version="1.0.0",
        supported_interfaces=[AgentInterface(url=f"http://{host}:{port}/", protocol_binding="JSONRPC")],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False, extensions=[ext]),
        skills=[AgentSkill(id="emerge", name="Emergent convention",
                           description="Converge on a shared symbol convention, grounded + measured.",
                           tags=["emergent", "l9"])],
    )


def serve(me: str, peer_id: str, host: str = "localhost") -> None:
    port = PORTS[me]
    card = build_card(me, host)
    handler = DefaultRequestHandler(
        agent_executor=EmergenceExecutor(me, peer_id, f"http://{host}:{PORTS[peer_id]}"),
        task_store=InMemoryTaskStore(), agent_card=card,
    )
    app = Starlette(routes=create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/"))
    print(f"{me.capitalize()} listening on http://{host}:{port}  (ext: {EXT_URI})")
    uvicorn.run(app, host=host, port=port)
