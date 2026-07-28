"""Lewis Signaling Game primitives — with Theory of Mind + History.

Pure functions — no state stored in memory. These are called by stateless
agents that read/write all state via A2A message metadata.

Theory of Mind: each agent models what the other agent believes and predicts
whether a proposal will be accepted before sending it.

History: past proposals and outcomes travel in metadata so agents never
repeat failed attempts.

Reference: David Lewis, "Convention: A Philosophical Study" (1969)
https://plato.stanford.edu/entries/convention/
https://arxiv.org/abs/1705.11192
"""
import random

SYMBOLS = list("○✦≈△▽◆∿☆⬡♁∆⊚◐▣✧⋈●◇➤∞")
MEANINGS = ["apple", "dance", "river", "sea", "moon", "fire", "star", "wind", "stone", "tree"]


# --- Legacy primitives (backward compat) ---


def coin(mine: dict, theirs: dict) -> str:
    """Pick a symbol not used by either agent."""
    used = set(mine.values()) | set(theirs.values())
    free = [s for s in SYMBOLS if s not in used]
    return random.choice(free or [s for s in SYMBOLS if s not in set(mine.values())])


def adopt(lex: dict, meaning: str, symbol: str) -> None:
    """Listener accepts speaker's symbol, removing conflicts."""
    for m in [m for m, s in lex.items() if s == symbol and m != meaning]:
        del lex[m]
    lex[meaning] = symbol


def alignment(a: dict, b: dict) -> float:
    """Fraction of meanings where both agents agree."""
    agree = sum(1 for m in MEANINGS if a.get(m) and a.get(m) == b.get(m))
    return agree / len(MEANINGS)


# --- Theory of Mind + History primitives ---


def coin_smart(mine: dict, theirs: dict, history: list[dict]) -> str:
    """Pick a symbol avoiding conflicts AND past rejected symbols.

    Theory of mind: don't pick a symbol that's already mapped in the peer's
    lexicon (it would cause a conflict they'd likely reject).

    History: don't pick a symbol that was rejected in a previous round.
    """
    mine_syms = set(mine.values())
    theirs_syms = set(theirs.values())
    rejected_syms = {h["symbol"] for h in history if not h.get("accepted", True)}
    avoid = mine_syms | theirs_syms | rejected_syms
    free = [s for s in SYMBOLS if s not in avoid]
    return random.choice(free or [s for s in SYMBOLS if s not in mine_syms])


def predict_acceptance(meaning: str, symbol: str, peer_lex: dict, history: list[dict]) -> float:
    """Theory of mind: predict likelihood the peer will accept this proposal.

    Returns a score 0.0–1.0:
      - 1.0: peer has no mapping for this meaning (will definitely accept)
      - 0.8: peer has a mapping but it conflicts (likely to yield)
      - 0.0: we tried this exact proposal before and it was rejected
      - 0.5: peer has a different symbol for this meaning (uncertain)
    """
    # Check history — was this exact proposal rejected before?
    for h in history:
        if h["referent"] == meaning and h["symbol"] == symbol and not h.get("accepted", True):
            return 0.0

    peer_sym = peer_lex.get(meaning)
    if peer_sym is None:
        return 1.0  # peer has no opinion — will accept
    if peer_sym == symbol:
        return 1.0  # already agrees
    # Peer has a different symbol — check if our symbol conflicts with another of their meanings
    if symbol in peer_lex.values():
        return 0.3  # our symbol is taken in their lexicon — likely reject
    return 0.5  # different but no direct conflict — uncertain


def propose_with_tom(mine: dict, theirs: dict, history: list[dict]) -> dict | None:
    """Theory of mind: pick the proposal most likely to be accepted.

    Evaluates all unresolved meanings, predicts acceptance for each,
    and returns the one with the highest predicted acceptance.
    Returns None if no unresolved meanings remain.
    """
    unresolved = [m for m in MEANINGS if mine.get(m) != theirs.get(m)]
    if not unresolved:
        return None

    best = None
    best_score = -1.0

    for meaning in unresolved:
        # Try our existing symbol first
        sym = mine.get(meaning)
        if sym:
            score = predict_acceptance(meaning, sym, theirs, history)
            if score > best_score:
                best_score = score
                best = {"referent": meaning, "symbol": sym, "predicted_acceptance": score}

        # If our symbol is bad, try coining a new one
        if best_score < 0.5:
            new_sym = coin_smart(mine, theirs, history)
            score = predict_acceptance(meaning, new_sym, theirs, history)
            if score > best_score:
                best_score = score
                best = {"referent": meaning, "symbol": new_sym, "predicted_acceptance": score}
                mine[meaning] = new_sym  # update our lexicon with the new coin

    return best


def decide_accept(my_lex: dict, meaning: str, symbol: str, peer_lex: dict, history: list[dict]) -> bool:
    """Theory of mind: decide whether to accept or reject a proposal.

    Accept if:
      - We have no mapping for this meaning
      - We have the same mapping already
      - The symbol doesn't conflict with any of our other mappings
      - We rejected fewer times than the peer proposed (be cooperative)

    Reject if:
      - The symbol conflicts with a meaning we've already established
        AND that established mapping has never been challenged
    """
    my_sym = my_lex.get(meaning)

    # No opinion yet — always accept
    if my_sym is None:
        return True

    # Already agree — trivial accept
    if my_sym == symbol:
        return True

    # Check conflict: does this symbol map to a DIFFERENT meaning in our lexicon?
    conflict_meanings = [m for m, s in my_lex.items() if s == symbol and m != meaning]
    if conflict_meanings:
        # Check history — have we successfully used our current mapping before?
        my_established = any(
            h["referent"] == meaning and h["symbol"] == my_sym and h.get("accepted", False)
            for h in history
        )
        if my_established:
            return False  # our mapping is established — reject

    # Default: be cooperative, accept
    return True


def record_outcome(history: list[dict], referent: str, symbol: str, accepted: bool, speaker: str) -> list[dict]:
    """Append a round outcome to the history. Returns new list (no mutation)."""
    return history + [{"referent": referent, "symbol": symbol, "accepted": accepted, "speaker": speaker}]
