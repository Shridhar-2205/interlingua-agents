"""Depth B — two STRUCTURED emergence agents over the L9 A2A extension.

The depth-A run derailed: two free-text LLM creatures fell into a mirror loop and
confirmed 0/10 (the classic MAS "conversational loop / joint derailment"). Depth B
removes the failure mode by construction: the agents exchange **structured
{object → word} proposals** in the L9 DataPart — there is no prose channel to
spiral in, and the referent is named explicitly so grounding is unambiguous.

Reuses the l9 core (signaling primitives + the L9 envelope/extension). This is the
Grace/Rocky naming game applied to the free_form_env world: Human starts with
English names, Alien with invented sounds; they converge on one shared word per
object. Fully deterministic — no LLM, no gateway calls — so it's fast and reliable.
"""
from __future__ import annotations

import os
import sys
import uuid
import random

import uvicorn
from starlette.applications import Starlette
from typing_extensions import override

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "l9"))

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

import signaling
import l9_envelope
from l9_envelope import EXT_URI, build_l9, to_data_part, from_a2a, agent_card_extension
from l9_models import Kind

# A modest slice of the shared environment for a snappy demo (extend to all 40 freely).
OBJECTS = ["fire", "water", "rock", "tree", "sun", "moon", "sky", "cloud", "rain", "wind", "flower", "fruit"]
PORTS = {"human": 9201, "alien": 9202}
MAX_ROUNDS = 100


def _alien_words(n: int) -> list[str]:
    """Invented alien sounds (vrk, zul, mok…) — distinct pseudo-words."""
    cons, vowels = "vkzrmntsgpl", "aeiou"
    out: list[str] = []
    while len(out) < n:
        w = random.choice(cons) + random.choice(vowels) + random.choice(cons)
        if random.random() < 0.4:
            w += random.choice(vowels)
        if w not in out:
            out.append(w)
    return out


def initial_state() -> dict:
    aw = _alien_words(len(OBJECTS))
    lexicons = {
        "human": {o: o for o in OBJECTS},                     # English names
        "alien": {o: aw[i] for i, o in enumerate(OBJECTS)},   # invented sounds
    }
    return {"lexicons": lexicons, "round": 0, "speaker": None,
            "referent": None, "proposal": None, "history": [], "decision": "init"}


def step(state: dict, me: str) -> dict:
    """One structured hop: adopt the peer's explicit {object: word}, then propose
    the next unresolved object with my word. Grounding is trivial (the object is
    named), so every adoption is genuine — GAR 1.0, no derailment possible."""
    lex = state["lexicons"]
    peer = "alien" if me == "human" else "human"
    hist = state.get("history", [])
    rnd = int(state.get("round", 0))

    if state.get("speaker") and state["speaker"] != me and state.get("proposal"):
        obj, word = state["referent"], state["proposal"]
        signaling.adopt(lex[me], obj, word)
        hist = signaling.record_outcome(hist, obj, word, True, state["speaker"], grounded=True)

    if signaling.alignment(lex, OBJECTS) == 1.0 or rnd >= MAX_ROUNDS:
        return {**state, "round": rnd, "history": hist, "decision": "converged",
                "referent": None, "proposal": None}

    prop = signaling.propose_with_tom(lex[me], lex[peer], hist, meanings=OBJECTS)
    if prop is None:
        return {**state, "round": rnd, "history": hist, "decision": "converged",
                "referent": None, "proposal": None}
    obj = prop["referent"]
    word = lex[me][obj]
    return {
        "lexicons": lex, "round": rnd + 1, "speaker": me,
        "referent": obj, "proposal": word,
        "utterance": {"text": f"{me}: '{word}' means {obj}", "evidence": [obj], "addresses_evidence": [obj]},
        "grounding": {"contingency_verified": True, "contingency_score": 1.0, "repair_reason": None},
        "belief": {"prior": 0.5, "posterior": 1.0, "revision_cause": "structured"},
        "history": hist, "decision": "propose",
    }


def _label(nxt: dict) -> str:
    if nxt.get("decision") == "converged":
        h = nxt.get("history", [])
        return (f"done | round {nxt['round']} | align {signaling.alignment(nxt['lexicons'], OBJECTS):.0%} "
                f"| GAR {signaling.gar(h)} SCR {signaling.scr(h)}")
    return f"{nxt['speaker']}: '{nxt['proposal']}' = {nxt['referent']}"


def _message(l9, role, ctx: RequestContext | None = None) -> Message:
    return Message(
        message_id=uuid.uuid4().hex,
        context_id=(ctx.context_id or "") if ctx else "",
        task_id=(ctx.task_id or "") if ctx else "",
        role=role,
        parts=[Part(text=_label(l9.payload.data)), to_data_part(l9)],
        extensions=[EXT_URI],
    )


class EmergenceBExecutor(AgentExecutor):
    def __init__(self, me: str, peer: str) -> None:
        self.me, self.peer = me, peer

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        incoming = from_a2a(context.message)
        if incoming is None:
            state = initial_state()
            episode = l9_envelope.episode_urn("ff", uuid.uuid4().hex)
            parents: list[str] = []
        else:
            state = incoming.payload.data
            episode = incoming.header.message.episode
            parents = [incoming.header.message.id]

        nxt = step(state, self.me)

        if nxt.get("decision") == "converged":
            out = build_l9(kind=Kind.commit, subkind="converged", sender=self.me,
                           recipients=[self.peer], episode=episode, data=nxt,
                           subprotocol="CIP", parents=parents)
            print(f"[{self.me}] {_label(nxt)}")
            await event_queue.enqueue_event(_message(out, Role.ROLE_AGENT, context))
            return

        out = build_l9(kind=Kind.exchange, sender=self.me, recipients=[self.peer],
                       episode=episode, data=nxt, topic=f"object:{nxt['referent']}",
                       subprotocol="CIP", parents=parents)
        print(f"[{self.me}] {_label(nxt)} -> {self.peer}")

        peer = await create_client(f"http://localhost:{PORTS[self.peer]}", ClientConfig(streaming=False))
        req = SendMessageRequest(message=_message(out, Role.ROLE_USER))
        reply: Message | None = None
        async for ev in peer.send_message(req):
            if hasattr(ev, "message") and ev.message.ByteSize():
                reply = ev.message
        await event_queue.enqueue_event(reply or _message(out, Role.ROLE_AGENT, context))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


def build_card(me: str) -> AgentCard:
    spec = agent_card_extension()
    ext = AgentExtension(uri=spec["uri"], description=spec["description"], required=spec["required"])
    ext.params.update(spec["params"])
    return AgentCard(
        name=f"{me.capitalize()} (structured)",
        description=f"Depth-B {me} agent: structured {{object→word}} convergence over the L9 emergence extension.",
        version="1.0.0",
        supported_interfaces=[AgentInterface(url=f"http://localhost:{PORTS[me]}/", protocol_binding="JSONRPC")],
        default_input_modes=["text/plain"], default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False, extensions=[ext]),
        skills=[AgentSkill(id="emerge", name="Structured convention",
                           description="Converge on shared object names via structured proposals.",
                           tags=["emergent", "l9", "structured"])],
    )


def serve(me: str, peer: str) -> None:
    card = build_card(me)
    handler = DefaultRequestHandler(
        agent_executor=EmergenceBExecutor(me, peer),
        task_store=InMemoryTaskStore(), agent_card=card,
    )
    app = Starlette(routes=create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/"))
    print(f"{me.capitalize()} (structured) on http://localhost:{PORTS[me]}  (ext: {EXT_URI})")
    uvicorn.run(app, host="localhost", port=PORTS[me])
