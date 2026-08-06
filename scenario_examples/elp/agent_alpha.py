"""Agent Alpha (ELP) — A2A server on port 9401 with ToM + signaling.

Imports intelligence (LLM-enhanced ToM) and signaling from the l9 package.
Communicates with Agent Beta using the ELP A2A message structure — every message
carries a structured L9 envelope with lexicons, grounding, belief, and history.

Run this agent, then agent_beta.py, then trigger.py.
"""
from __future__ import annotations

import sys
import os
from uuid import uuid4

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

# import smarts/ToM from the l9 package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "l9"))
import signaling
import intelligence
import world
from lens import Lens
from l9_models import L9, Actor, ParticipantSet, Message as L9Message, Context
from l9_envelope import (
    EXT_URI, MEDIA_L9, build_l9, pack_l9, unpack_l9,
    to_data_part, from_a2a, episode_urn, agent_card_extension,
)

HOST, PORT = "localhost", 9401
PEER_ID = "beta"
PEER_URL = "http://localhost:9402"
MAX_ROUNDS = 30

ALPHA_LENS = Lens(
    agent_id="alpha", modality=world.VISUAL,
    grounding_strictness=0.40, compliance=0.10, innovation=0.5,
)

BETA_LENS = Lens(
    agent_id="beta", modality=world.PHYSICAL,
    grounding_strictness=0.40, compliance=0.10, innovation=0.5,
)

LENSES = {"alpha": ALPHA_LENS, "beta": BETA_LENS}


def form_prior(lens: Lens) -> dict:
    lex: dict = {}
    for concept in world.concepts():
        lex[concept] = signaling.coin_smart(lex, {}, [])
    return lex


def step(state: dict, me: str) -> dict:
    lens = LENSES[me]
    lexicons: dict = state["lexicons"]
    history: list = state.get("history", [])
    rnd = int(state.get("round", 0))

    if state.get("speaker") and state["speaker"] != me and state.get("proposal"):
        concept, symbol = state["referent"], state["proposal"]
        speaker_ev = (state.get("utterance") or {}).get("evidence", [])
        peer_model = state.get("tom", {}).get(me, lexicons[state["speaker"]])
        addresses, posterior, score = intelligence.ground(
            concept, symbol, speaker_ev, lens, lexicons[me], history)
        grounded = score >= signaling.THETA_C
        if score >= lens.grounding_strictness or lens.compliance >= 0.5:
            signaling.adopt(lexicons[me], concept, symbol)
            history = signaling.record_outcome(history, concept, symbol, True, state["speaker"],
                                               grounded=grounded)
        else:
            history = signaling.record_outcome(history, concept, symbol, False, state["speaker"],
                                               grounded=False)

    if signaling.alignment(lexicons) == 1.0 or rnd >= MAX_ROUNDS:
        return {**state, "round": rnd, "history": history, "decision": "converged",
                "referent": None, "proposal": None}

    peer = next(a for a in lexicons if a != me)
    peer_model = state.get("tom", {}).get(me, dict(lexicons[peer]))
    prop = signaling.propose_with_tom(lexicons[me], peer_model, history)
    if prop is None:
        return {**state, "round": rnd, "history": history, "decision": "converged",
                "referent": None, "proposal": None}
    concept = prop["referent"]
    symbol, rationale, evidence = intelligence.coin(concept, lens, lexicons[me], peer_model, history)
    lexicons[me][concept] = symbol
    return {
        "lexicons": lexicons, "round": rnd + 1, "speaker": me,
        "referent": concept, "proposal": symbol,
        "utterance": {"text": rationale, "evidence": evidence, "addresses_evidence": []},
        "grounding": {"contingency_verified": None, "contingency_score": None, "repair_reason": None},
        "belief": {"prior": 0.5, "posterior": 0.5, "revision_cause": "innovation"},
        "tom": {me: dict(peer_model)},
        "history": history, "decision": "propose",
    }


def initial_state() -> dict:
    lexicons = {"alpha": form_prior(ALPHA_LENS), "beta": form_prior(BETA_LENS)}
    return {"lexicons": lexicons, "round": 0, "speaker": None, "referent": None,
            "proposal": None, "history": [], "decision": "init"}


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


class AlphaExecutor(AgentExecutor):
    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        incoming = from_a2a(context.message)
        if incoming is None:
            state = initial_state()
            episode = episode_urn("session", uuid4().hex)
            parents: list[str] = []
        else:
            state = incoming.data
            episode = incoming.message.episode
            parents = [incoming.message.id]

        nxt = step(state, "alpha")

        if nxt.get("decision") == "converged":
            out = build_l9(sender="alpha", recipients=["beta"],
                           episode=episode, data=nxt, parents=parents)
            print(f"[alpha] {_label(nxt)}")
            await event_queue.enqueue_event(_message(out, Role.ROLE_AGENT, context))
            return

        out = build_l9(sender="alpha", recipients=["beta"],
                       episode=episode, data=nxt, topic=f"concept:{nxt['referent']}",
                       parents=parents)
        print(f"[alpha] {_label(nxt)} -> beta")

        http_client = httpx.AsyncClient(timeout=300)
        peer = await create_client(PEER_URL, ClientConfig(streaming=False, httpx_client=http_client))
        req = SendMessageRequest(message=_message(out, Role.ROLE_USER))
        reply: Message | None = None
        async for ev in peer.send_message(req):
            if hasattr(ev, "message") and ev.message.ByteSize():
                reply = ev.message
        await event_queue.enqueue_event(reply or _message(out, Role.ROLE_AGENT, context))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        pass


def build_agent_card() -> AgentCard:
    ext_spec = agent_card_extension()
    ext = AgentExtension(uri=ext_spec["uri"], description=ext_spec["description"],
                         required=ext_spec["required"])
    ext.params.update(ext_spec["params"])
    return AgentCard(
        name="Alpha (ELP)",
        description="Emergent-convention agent (alpha) with ToM + signaling, ELP-over-A2A.",
        version="1.0.0",
        supported_interfaces=[AgentInterface(url=f"http://{HOST}:{PORT}/", protocol_binding="JSONRPC")],
        default_input_modes=["text/plain"], default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False, extensions=[ext]),
        skills=[AgentSkill(id="emerge", name="Emergent convention (ELP)",
                           description="Converge on shared symbols via ToM + grounding + ELP.",
                           tags=["emergent", "l9", "tom"])],
    )


def main() -> None:
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=AlphaExecutor(),
        task_store=InMemoryTaskStore(), agent_card=card)
    app = Starlette(routes=create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/"))
    print(f"Alpha Agent (ELP + ToM) on http://{HOST}:{PORT}  (ext: {EXT_URI})")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
