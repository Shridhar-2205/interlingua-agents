"""The Office — knows the order, cannot reach a shelf.

Each round it gets a customer order that only it can see, and has to describe
the product using signals. Nothing is pre-agreed: the first time the Office
wants to talk about "heavy" it coins an arbitrary symbol for it, and that
symbol means nothing to anyone until the Floor works it out.

The Office starts out describing products the way a customer would — "blue",
"medium", "winter". Those describe something genuinely true about the product
and are completely useless to someone looking at a sealed box.

It learns this the honest way. The Floor reports back which symbols it could
not resolve, and the Office lowers its opinion of those features. Over ~50
orders it stops mentioning colour and starts mentioning weight. Nobody
programmed that; it falls out of being told "I couldn't check that".
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

import catalogue

# Arbitrary marks. They have no built-in meaning — that is the point.
SYMBOLS = list("○✦≈△▽◆∿☆⬡♁∆⊚◐▣✧⋈●◇➤∞⟐⌘✺❉")

WORTH_SAYING = 0.35   # stop mentioning a feature once we think this little of it
MOST = 5              # never send more than this many symbols in one description
LEAST = 2             # always say at least this much, even early on
PATIENCE = 3          # give the Floor this many uses of a symbol before judging it
START_SCORE = 0.5     # no opinion yet about whether a feature is worth using


@dataclass
class Office:
    rng: random.Random
    symbol_of: dict[str, str] = field(default_factory=dict)   # feature -> coined symbol
    score: dict[str, float] = field(default_factory=dict)     # feature -> how useful it has proven
    sent: dict[str, int] = field(default_factory=dict)        # feature -> times mentioned
    revisions: list[dict] = field(default_factory=list)       # moments we changed our mind

    # ── coining ────────────────────────────────────────────────────────────────
    def _symbol(self, feature: str) -> str:
        """Our mark for this feature, invented on first use and kept forever."""
        if feature not in self.symbol_of:
            used = set(self.symbol_of.values())
            free = [s for s in SYMBOLS if s not in used]
            self.symbol_of[feature] = self.rng.choice(free or SYMBOLS)
        return self.symbol_of[feature]

    # ── speaking ───────────────────────────────────────────────────────────────
    def describe(self, product: str) -> dict:
        """Say everything about this product we still think is worth saying.

        Describing it fully matters more than being brief. If we hold back a
        detail, the Floor can end up with a description that fits a smaller box
        perfectly and picks that instead — the wrong box, confidently. So we
        mention every feature we haven't given up on, and let the Floor ignore
        the ones it can't check.
        """
        ranked = sorted(
            catalogue.features(product),
            key=lambda f: (-self.score.get(f, START_SCORE), catalogue.rarity(f), f),
        )
        chosen = [f for f in ranked if self.score.get(f, START_SCORE) >= WORTH_SAYING]
        chosen = (chosen or ranked[:LEAST])[:MOST]
        for f in chosen:
            self.sent[f] = self.sent.get(f, 0) + 1
        return {
            "symbols": [self._symbol(f) for f in chosen],
            # what we are going on — carried openly so the round is auditable
            "basis": chosen,
        }

    # ── learning ───────────────────────────────────────────────────────────────
    def learn(self, basis: list[str], unresolved: list[str], correct: bool,
              round_no: int = 0) -> None:
        """Update our opinion of each feature we used.

        Two signals, and they deserve very different amounts of trust.

        "I could not check that symbol" is the Floor telling us something it
        knows for certain about itself. Believe it, and act on it hard.

        A wrong box is far weaker evidence. We mentioned several features and
        have no idea which one misled the Floor — the fault is often a sign the
        Floor is still misreading, not the feature we chose. Blaming everything
        we just said would make us abandon perfectly good words like "small".
        So a failure barely moves the needle.
        """
        unresolved_feats = {f for f in basis if self._symbol(f) in unresolved}
        for f in basis:
            cur = self.score.get(f, START_SCORE)
            if f in unresolved_feats and self.sent.get(f, 0) > PATIENCE:
                target, weight = 0.0, 0.20         # trusted: you can't check it
            elif correct:
                target, weight = 1.0, 0.10
            else:
                target, weight = 0.6, 0.05         # something went wrong; unclear what
            self.score[f] = round((1 - weight) * cur + weight * target, 4)

            # the moment we stop believing the Floor can check this at all
            if cur >= WORTH_SAYING > self.score[f]:
                self.revisions.append({
                    "round": round_no, "who": "Office", "kind": "gave up",
                    "symbol": self._symbol(f), "before": f, "after": "unsayable",
                    "note": f"the Floor kept reporting it couldn't check '{f}'",
                })

    # ── theory of mind: our model of what the Floor can perceive ───────────────
    def peer_model(self) -> dict[str, list[str]]:
        """What we now believe about the Floor's senses.

        Note what is being modelled here: not the Floor's *words*, but the
        Floor's *limits*. We started out assuming it could check everything we
        know about a product, and it can't. Learning that is the whole job.
        """
        can = [f for f, s in self.score.items() if s >= 0.6]
        cannot = [f for f, s in self.score.items() if s < WORTH_SAYING]
        unsure = [f for f in self.score if f not in can and f not in cannot]
        return {
            "can check": sorted(can, key=lambda f: -self.score[f]),
            "cannot check": sorted(cannot, key=lambda f: self.score[f]),
            "still unsure": sorted(unsure, key=lambda f: -self.score[f]),
        }

    # ── what it ended up believing ─────────────────────────────────────────────
    def ranking(self) -> list[tuple[str, float]]:
        """Every feature we've used, best first. The top of this list is what
        the Floor can check; the bottom is what we learned to stop saying."""
        return sorted(self.score.items(), key=lambda kv: -kv[1])

    def abandoned(self) -> list[str]:
        """Features we no longer bother mentioning — same cutoff `describe`
        uses, so this is genuinely what fell out of our speech."""
        return sorted((f for f, s in self.score.items() if s < WORTH_SAYING),
                      key=lambda f: self.score[f])
