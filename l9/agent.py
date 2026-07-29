"""Stateless A2A agent — the emergence extension over A2A ping-pong.

Generalizes the base repo's grace_agent.py / rocky_agent.py into one executor
parametrized by (agent_id, peer). All state travels in the L9 DataPart defined by
l9_envelope (the extension); the agent keeps nothing between calls.

Episode (L9 grammar), see README:
    trigger → intent → exchange:prior (per agent) → exchange loop
    (propose → ground → adopt | contingency-repair) → commit:converged → knowledge

NOTE: transport wiring (a2a-sdk create_client / server routes) is marked TODO —
the reasoning core (signaling, intelligence, l9_envelope) is fully implemented and
unit-testable without a2a. Install a2a-sdk to run the servers.
"""
from __future__ import annotations

import uuid

import signaling
import intelligence
import world
from lens import Lens, BY_ID
from l9_envelope import build_l9, episode_urn
from l9_models import Kind

MAX_ROUNDS = 60


def _subprotocol(n_agents: int) -> str:
    return "SIEP" if n_agents > 2 else "CIP"   # pair=CIP, population=SIEP


def form_prior(lens: Lens) -> dict:
    """exchange:prior — each agent independently coins its own starting lexicon
    from its own perception. This declared baseline is what GAR/SCR measure from."""
    lex: dict = {}
    for concept in world.concepts():
        sym, _r, _e = intelligence.coin(concept, lens, lex, {}, [])
        lex[concept] = sym
    return lex


def step(state: dict, me: str) -> dict:
    """One hop of the game, given the emergence payload `state`. Pure w.r.t. `me`;
    returns the next state to put on the wire (or a terminal state)."""
    lens = BY_ID[me]
    lexicons: dict = state["lexicons"]
    history: list = state.get("history", [])
    rnd = int(state.get("round", 0))

    # 1. If a proposal is addressed to me, ground it and adopt-or-repair.
    if state.get("speaker") and state["speaker"] != me and state.get("proposal"):
        concept, symbol = state["referent"], state["proposal"]
        speaker_ev = (state.get("utterance") or {}).get("evidence", [])
        peer_model = state.get("tom", {}).get(me, lexicons[state["speaker"]])
        addresses, posterior, score = intelligence.ground(
            concept, symbol, speaker_ev, lens, lexicons[me], history)
        grounded = score >= signaling.THETA_C          # objective grounding truth
        if score >= lens.grounding_strictness or lens.compliance >= 0.5:  # this agent's adopt policy
            signaling.adopt(lexicons[me], concept, symbol)
            history = signaling.record_outcome(history, concept, symbol, True, state["speaker"],
                                               grounded=grounded)
        else:
            # grounding failure → contingency (repair): the better-positioned
            # speaker will re-propose this concept in a groundable direction.
            history = signaling.record_outcome(history, concept, symbol, False, state["speaker"],
                                               grounded=False)

    # 2. Convergence check.
    if signaling.alignment(lexicons) == 1.0 or rnd >= MAX_ROUNDS:
        return {**state, "round": rnd, "history": history, "decision": "converged",
                "referent": None, "proposal": None}

    # 3. My turn to speak — pick + justify a proposal via ToM.
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


def initial_state(agents: list[str]) -> dict:
    """intent + prior-formation for all agents (single-process bootstrap)."""
    lexicons = {a: form_prior(BY_ID[a]) for a in agents}
    return {"lexicons": lexicons, "round": 0, "speaker": None, "referent": None,
            "proposal": None, "history": [], "decision": "init"}


# ── A2A transport (TODO: wire to a2a-sdk, mirroring base grace_agent.py) ────────
#
# def build_card(agent_id, port): AgentCard(..., capabilities=AgentCapabilities(
#     extensions=[AgentExtension(**l9_envelope.agent_card_extension())]))
#
# class Executor(AgentExecutor):
#     async def execute(self, ctx, event_queue):
#         l9 = l9_envelope.from_a2a(ctx.message)
#         state = l9.payload.data if l9 else initial_state([self.me, self.peer])
#         nxt = step(state, self.me)
#         if nxt["decision"] == "converged":
#             out = build_l9(kind=Kind.commit, subkind="converged", ...)   # + knowledge
#         else:
#             out = build_l9(kind=Kind.exchange, ...); send to peer via create_client
#         await event_queue.enqueue_event(...l9_envelope.to_data_part(out)...)
