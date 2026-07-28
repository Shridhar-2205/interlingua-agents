"""Lewis Signaling Game primitives.

Pure functions — no state stored in memory. These are called by stateless
agents that read/write all state via A2A message metadata.

Reference: David Lewis, "Convention: A Philosophical Study" (1969)
https://plato.stanford.edu/entries/convention/
https://arxiv.org/abs/1705.11192
"""
import random

SYMBOLS = list("○✦≈△▽◆∿☆⬡♁∆⊚◐▣✧⋈●◇➤∞")
MEANINGS = ["apple", "dance", "river", "sea", "moon", "fire", "star", "wind", "stone", "tree"]

# Confidence levels
CONFIDENCE_COINED = 0.5    # freshly invented — arbitrary choice
CONFIDENCE_ADOPTED = 0.7   # accepted from peer — socially validated
CONFIDENCE_AGREED = 1.0    # both agents have the same mapping — settled

# --- Legacy primitives (still work, used by old tests) ---


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
    """Fraction of meanings where both agents agree.

    Works with both old format ({"river": "≈"}) and new format
    ({"river": {"symbol": "≈", "confidence": 0.7}}).
    """
    def get_sym(lex, m):
        v = lex.get(m)
        if isinstance(v, dict):
            return v.get("symbol")
        return v

    agree = sum(1 for m in MEANINGS if get_sym(a, m) and get_sym(a, m) == get_sym(b, m))
    return agree / len(MEANINGS)


# --- Smart primitives (mutual exclusivity + batch + confidence) ---


def coin_exclusive(mine: dict, theirs: dict) -> str:
    """Pick a symbol not mapped to ANY meaning in either lexicon.

    Guarantees one-to-one: the returned symbol is completely free.
    Prevents collisions that waste rounds to resolve.
    """
    mine_syms = {v["symbol"] if isinstance(v, dict) else v for v in mine.values()}
    theirs_syms = {v["symbol"] if isinstance(v, dict) else v for v in theirs.values()}
    used = mine_syms | theirs_syms
    free = [s for s in SYMBOLS if s not in used]
    return random.choice(free or [s for s in SYMBOLS if s not in mine_syms])


def get_symbol(lex: dict, meaning: str) -> str | None:
    """Extract symbol from a lexicon entry (handles both formats)."""
    v = lex.get(meaning)
    if v is None:
        return None
    if isinstance(v, dict):
        return v.get("symbol")
    return v


def get_confidence(lex: dict, meaning: str) -> float:
    """Extract confidence from a lexicon entry."""
    v = lex.get(meaning)
    if isinstance(v, dict):
        return v.get("confidence", CONFIDENCE_COINED)
    return CONFIDENCE_COINED if v else 0.0


def propose_batch(mine: dict, theirs: dict) -> list[dict]:
    """Generate proposals for ALL unresolved meanings at once.

    Each proposal includes the referent, a conflict-free symbol, and confidence.
    Only proposes for meanings where the two lexicons disagree.
    """
    proposals = []
    for m in MEANINGS:
        my_sym = get_symbol(mine, m)
        their_sym = get_symbol(theirs, m)
        if my_sym == their_sym and my_sym is not None:
            continue  # already agreed
        # Use existing symbol if we have one, otherwise coin a new exclusive one
        sym = my_sym or coin_exclusive(mine, theirs)
        conf = get_confidence(mine, m) if my_sym else CONFIDENCE_COINED
        proposals.append({"referent": m, "symbol": sym, "confidence": conf})
    return proposals


def resolve_batch(my_lex: dict, proposals: list[dict]) -> dict:
    """Process incoming proposals — accept if their confidence >= mine, reject otherwise.

    Returns the updated lexicon (new format with confidence).
    Does NOT mutate the input — returns a new dict.
    """
    result = dict(my_lex)
    for p in proposals:
        referent = p["referent"]
        their_sym = p["symbol"]
        their_conf = p.get("confidence", CONFIDENCE_COINED)
        my_conf = get_confidence(result, referent)
        my_sym = get_symbol(result, referent)

        if my_sym == their_sym:
            # Already agree — boost to agreed confidence
            result[referent] = {"symbol": my_sym, "confidence": CONFIDENCE_AGREED}
        elif their_conf >= my_conf:
            # Their confidence is higher or equal — adopt their symbol
            # Remove any other meaning that had this symbol (mutual exclusivity)
            for m in list(result.keys()):
                if m != referent and get_symbol(result, m) == their_sym:
                    del result[m]
            result[referent] = {"symbol": their_sym, "confidence": CONFIDENCE_ADOPTED}
        # else: reject — keep mine (higher confidence wins)

    return result
