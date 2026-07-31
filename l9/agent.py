"""The reasoning core, transport-free — see a2a_agent.py for the A2A server/client.

All state travels in the emergence DataPart defined by l9_envelope; the agent
keeps nothing between calls.

Episode, see README:
    trigger → prior formation (per agent) → exchange loop
    (propose → ground → adopt | reject) → converged
"""
from __future__ import annotations

import uuid

import signaling
import intelligence
import world
from lens import Lens, BY_ID
from l9_envelope import build_l9, episode_urn

MAX_ROUNDS = 60


def form_prior(lens: Lens) -> dict:
    """exchange:prior — each agent independently coins its own starting lexicon.
    This declared baseline is what GAR/SCR measure from.

    Local (no LLM) on purpose: a prior is just a distinct starting symbol per
    concept — no proposal is being grounded yet, so there's nothing for the LLM
    to reason about. Symbols are still randomised (independent per agent); we just
    skip the LLM call. Reserving the LLM for the negotiation loop drops ~20 calls
    (10 concepts x 2 agents) with zero behaviour change (form_prior only ever kept
    the symbol; the LLM's rationale/evidence were discarded)."""
    lex: dict = {}
    for concept in world.concepts():
        lex[concept] = signaling.coin_smart(lex, {}, [])
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
