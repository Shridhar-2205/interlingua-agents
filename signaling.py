"""Lewis Signaling Game primitives.

Pure functions — no state stored in memory. These are called by stateless
agents that read/write all state via an A2A message data Part (see a2a_state.py).

Reference: David Lewis, "Convention: A Philosophical Study" (1969)
https://plato.stanford.edu/entries/convention/
https://arxiv.org/abs/1705.11192
"""
import random

SYMBOLS = list("○✦≈△▽◆∿☆⬡♁∆⊚◐▣✧⋈●◇➤∞")
MEANINGS = ["apple", "dance", "river", "sea", "moon", "fire", "star", "wind", "stone", "tree"]


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