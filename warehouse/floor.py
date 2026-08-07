"""The Floor — has the hands, cannot see the order.

Hears a handful of symbols, looks down the aisle, and either picks a box or
says "I can't tell which one". It has never been given a dictionary; it works
out what the symbols mean by seeing which box turned out to be right.

Two versions, and the difference is one line:

  honest  — if the symbols do not single out exactly one box, it says so.
  yes-man — always picks something. Never gets stuck, never asks for help,
            and quietly sends the wrong thing to a customer.

The honest one looks worse on a dashboard and is the one you want.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

import catalogue

BIND_AFTER = 2   # times a symbol must be seen before we dare give it a meaning
SETTLED = 4      # ...and this many before we'll act on that meaning alone


@dataclass
class Floor:
    rng: random.Random
    honest: bool = True
    # How often it admits uncertainty instead of guessing, 0.0–1.0. The honest
    # and yes-man arms are just the two ends of this dial; the middle exists so
    # we can sweep it and see whether l9's trust score tracks real damage.
    caution: float | None = None
    # every set of aisle-visible features we have seen a symbol used for
    seen: dict[str, list[set[str]]] = field(default_factory=dict)
    # symbol -> every property that has held every time we heard it. Often more
    # than one: if every small box we ever saw was also heavy, then as far as we
    # can tell the sign means "small and heavy". Keeping both is honest, and it
    # un-confuses itself the first time a small light box turns up.
    meaning: dict[str, frozenset[str]] = field(default_factory=dict)
    # every moment one of those meanings changed — formed, narrowed, or collapsed
    revisions: list[dict] = field(default_factory=list)

    # ── theory of mind: our model of what the Office means ─────────────────────
    def confidence(self, symbol: str) -> float:
        """How sure are we of this meaning? Purely a question of how much we've
        seen it — a sign heard twice is a hunch, heard six times it's a word."""
        return round(min(1.0, len(self.seen.get(symbol, [])) / SETTLED), 2)

    def beliefs(self) -> list[dict]:
        """Our model of the Office's language, most-believed first. This is the
        Theory of Mind: not what the signs mean, but what we *think* they mean."""
        return sorted(
            ({"symbol": s, "means": " + ".join(sorted(m)),
              "confidence": self.confidence(s), "seen": len(self.seen.get(s, []))}
             for s, m in self.meaning.items()),
            key=lambda b: (-b["confidence"], b["means"]),
        )

    # ── understanding ──────────────────────────────────────────────────────────
    def resolve(self, symbols: list[str]) -> tuple[set[str], list[str]]:
        """Split what we heard into what we understood and what we didn't.

        The unresolved list is not an error — it is the honest report the
        Office needs in order to stop describing things we cannot check.
        """
        got: set[str] = set()
        for s in symbols:
            got |= self.meaning.get(s, frozenset())
        missed = [s for s in symbols if s not in self.meaning]
        return got, missed

    def candidates(self, understood: set[str]) -> tuple[list[str], float]:
        """Boxes in the aisle that fit everything we understood, and how well.

        A box only qualifies if it has all of those features. Among those, the
        best fit is the one they account for most completely — a description
        that covers a box entirely beats one that merely overlaps a bigger box.
        (If they'd meant the cutlery set, they would have mentioned "small".)
        """
        best, top = [], -1.0
        for p in catalogue.products():
            vis = catalogue.visible(p)
            if not understood <= vis:
                continue
            fit = len(understood & vis) / len(vis) if vis else 0.0
            if fit > top:
                best, top = [p], fit
            elif fit == top:
                best.append(p)
        return best, max(top, 0.0)

    # ── acting ─────────────────────────────────────────────────────────────────
    def pick(self, symbols: list[str]) -> dict:
        """Take a box, or refuse. This is the only thing that ends a round —
        neither agent gets to declare success."""
        understood, missed = self.resolve(symbols)
        options, fit = self.candidates(understood)

        # Only claim to have identified a box when three things hold: one box
        # stands alone, the description accounts for everything that box shows
        # (a partial match is a description that happens to fit, not one that
        # picks something out), and we aren't leaning on a meaning we've only
        # just formed. A meaning seen twice is a hunch, not an understanding.
        young = [s for s in symbols if s in self.meaning and len(self.seen.get(s, [])) < SETTLED]
        sure = len(options) == 1 and fit == 1.0 and not young

        caution = self.caution if self.caution is not None else (1.0 if self.honest else 0.0)

        if sure:
            choice, why = options[0], "identified"
        elif self.rng.random() < caution:
            choice, why = None, "cannot tell them apart"
        else:
            choice, why = (self.rng.choice(options) if options else
                           self.rng.choice(catalogue.products())), "guessed"

        return {
            "choice": choice,
            "grounded": why == "identified",   # did we actually work it out?
            "reason": why,
            "narrowed_to": len(options),
            "unresolved": missed,              # what we could not check
        }

    # ── learning ───────────────────────────────────────────────────────────────
    def learn(self, symbols: list[str], truth: str, round_no: int = 0) -> None:
        """The box is open. Whatever it turned out to be, every symbol we just
        heard was used for *that*. Keep only what has held every single time.

        A meaning is always consistent with every box we have seen so far — but
        "so far" is doing real work. A symbol the Office uses for "gift" looks
        exactly like a symbol for "rattles" until the first gift arrives that
        doesn't rattle. Then the meaning we had was too broad, and we drop it.
        Guessing too broadly costs us a wrong box; it is caught the next round.
        """
        vis = catalogue.visible(truth)
        for s in symbols:
            self.seen.setdefault(s, []).append(vis)
            uses = self.seen[s]
            if len(uses) < BIND_AFTER:
                continue

            before = self.meaning.get(s)
            always = set.intersection(*uses)
            if always:
                # everything that has held every single time — no arbitrary
                # choice between equally-good readings, which is where a sign
                # for "small" quietly turns into a sign for "heavy"
                self.meaning[s] = frozenset(always)
            else:
                # it has now been used for two boxes with nothing in common, so
                # whatever we thought it meant was wrong. Drop it and go back to
                # not understanding it — better than acting on a stale guess.
                self.meaning.pop(s, None)

            self._note_revision(s, before, self.meaning.get(s), truth, round_no)

    def _note_revision(self, symbol: str, before, after, truth: str, round_no: int) -> None:
        """Record the moment a belief changed, and why. This log is the honest
        history of a mind changing — the thing that is normally invisible."""
        if before == after:
            return
        if before is None:
            kind, note = "formed", f"after {len(self.seen[symbol])} sightings"
        elif after is None:
            kind, note = "COLLAPSED", f"'{truth}' contradicted it"
        else:
            kind, note = "narrowed", f"'{truth}' ruled out the rest"
        self.revisions.append({
            "round": round_no, "who": "Floor", "kind": kind, "symbol": symbol,
            "before": " + ".join(sorted(before)) if before else "unknown",
            "after": " + ".join(sorted(after)) if after else "unknown",
            "note": note,
        })

    def glossary(self) -> dict[str, str]:
        """symbol -> what we take it to mean, in readable form."""
        return {s: " + ".join(sorted(m)) for s, m in self.meaning.items()}
