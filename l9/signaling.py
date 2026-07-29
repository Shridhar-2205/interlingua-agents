"""Lewis Signaling + Theory of Mind + grounding + convergence metrics.

Builds directly on the colleague's feature/theory-of-mind branch of
interlingua-agents (coin_smart / predict_acceptance / propose_with_tom /
decide_accept / record_outcome are reused near-verbatim as the DETERMINISTIC
backbone). Added here:

  * feature-grounding (CIP contingency check) so acceptance depends on whether a
    symbol's evidence overlaps how the listener perceives the concept, not just
    on symbol availability;
  * GAR / SCR / MPC / provenance-weight, computed from the history event log.

Reference: David Lewis, "Convention" (1969).
"""
from __future__ import annotations

import random
from typing import Optional

import world

SYMBOLS = world.SYMBOLS
MEANINGS = world.concepts()
THETA_C = 0.40  # default CIP contingency threshold


# ── Lewis primitives (from base repo) ──────────────────────────────────────────

def coin(mine: dict, theirs: dict) -> str:
    used = set(mine.values()) | set(theirs.values())
    free = [s for s in SYMBOLS if s not in used]
    return random.choice(free or [s for s in SYMBOLS if s not in set(mine.values())])


def adopt(lex: dict, meaning: str, symbol: str) -> None:
    for m in [m for m, s in lex.items() if s == symbol and m != meaning]:
        del lex[m]
    lex[meaning] = symbol


def alignment(lexicons: dict[str, dict]) -> float:
    """Fraction of concepts where ALL agents agree (generalizes to N agents)."""
    lexes = list(lexicons.values())
    if len(lexes) < 2:
        return 0.0
    agree = 0
    for m in MEANINGS:
        syms = {lx.get(m) for lx in lexes}
        if len(syms) == 1 and None not in syms:
            agree += 1
    return agree / len(MEANINGS)


# ── ToM primitives (reused from feature/theory-of-mind) ────────────────────────

def coin_smart(mine: dict, theirs: dict, history: list[dict]) -> str:
    rejected = {h["symbol"] for h in history if not h.get("accepted", True)}
    avoid = set(mine.values()) | set(theirs.values()) | rejected
    free = [s for s in SYMBOLS if s not in avoid]
    return random.choice(free or [s for s in SYMBOLS if s not in set(mine.values())])


def predict_acceptance(meaning: str, symbol: str, peer_lex: dict, history: list[dict]) -> float:
    """Speaker ToM (availability-only baseline). intelligence.py upgrades this
    with feature grounding when an LLM is available."""
    for h in history:
        if h["referent"] == meaning and h["symbol"] == symbol and not h.get("accepted", True):
            return 0.0
    peer_sym = peer_lex.get(meaning)
    if peer_sym is None or peer_sym == symbol:
        return 1.0
    if symbol in peer_lex.values():
        return 0.3
    return 0.5


def propose_with_tom(mine: dict, theirs: dict, history: list[dict]) -> Optional[dict]:
    unresolved = [m for m in MEANINGS if mine.get(m) != theirs.get(m)]
    if not unresolved:
        return None
    best, best_score = None, -1.0
    for meaning in unresolved:
        sym = mine.get(meaning)
        if sym:
            score = predict_acceptance(meaning, sym, theirs, history)
            if score > best_score:
                best, best_score = {"referent": meaning, "symbol": sym, "predicted_acceptance": score}, score
        if best_score < 0.5:
            new_sym = coin_smart(mine, theirs, history)
            score = predict_acceptance(meaning, new_sym, theirs, history)
            if score > best_score:
                best, best_score = {"referent": meaning, "symbol": new_sym, "predicted_acceptance": score}, score
                mine[meaning] = new_sym
    return best


def record_outcome(history: list[dict], referent: str, symbol: str, accepted: bool,
                   speaker: str, grounded: bool = False) -> list[dict]:
    """Append a round outcome (no mutation). `grounded` feeds GAR/SCR."""
    return history + [{"referent": referent, "symbol": symbol, "accepted": accepted,
                       "speaker": speaker, "grounded": grounded}]


# ── Grounding (CIP contingency check) — the feature dimension we add ────────────

def contingency_score(addresses_evidence: list[str], evidence: list[str]) -> float:
    """|addresses ∩ evidence| / |evidence|  — did the listener engage the speaker's grounding?"""
    if not evidence:
        return 0.0
    inter = len(set(addresses_evidence) & set(evidence))
    return round(inter / len(set(evidence)), 4)


# ── Convergence quality metrics (adapted from L9's SIEP defs) ──────────────────

def scr(history: list[dict]) -> float:
    """Social Compliance Ratio: adoptions that happened WITHOUT grounding."""
    adopts = [h for h in history if h.get("accepted")]
    if not adopts:
        return 0.0
    compliance = [h for h in adopts if not h.get("grounded")]
    return round(len(compliance) / len(adopts), 4)


def gar(history: list[dict]) -> float:
    """Genuine Agreement Ratio: adoptions that passed the grounding check."""
    adopts = [h for h in history if h.get("accepted")]
    if not adopts:
        return 0.0
    grounded = [h for h in adopts if h.get("grounded")]
    return round(len(grounded) / len(adopts), 4)


def mpc(posteriors: list[float]) -> float:
    """Mean Posterior Confidence across agents' final beliefs."""
    return round(sum(posteriors) / len(posteriors), 4) if posteriors else 0.0


def provenance_weight(history: list[dict]) -> float:
    """W = (1 - SCR) * GAR. ~1 = genuine emergence; ~0 = mimicry."""
    return round((1 - scr(history)) * gar(history), 4)
