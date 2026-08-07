"""Putting the warehouse on the wire — ELP envelope over A2A.

The in-process demo (`run.py`) calls `office.describe()` and `floor.pick()` as
plain functions. This module is what those calls become when the two agents are
separate services: a structured payload inside the L9 emergence envelope that
`../l9/l9_envelope.py` defines, in a self-describing A2A DataPart.

Both agents are STATELESS, following the rest of the repo. Everything either one
has learned travels on the wire and comes back — kill either service mid-session,
restart it, and the next message still works, because the message *is* the memory.

The payload (inside the envelope's `data`):

    round        int             which order we're on
    orders       int             how many in this session
    honest       bool            may the Floor answer "I can't tell"?
    marks        [str]           what the Office is saying this round
    basis        [str]           WHAT IT IS GOING ON — the features behind those
                                 marks. l9's `evidence`, by another name.
    reveal       {marks, truth}  last round's answer, so the Floor can learn
    floor_state  {...}           the Floor's memory, carried by the Office
    office_state {...}           the Office's memory

    -- and coming back --
    choice       str | null      the box it took, or null for "I can't tell"
    grounded     bool            did it work it out, or guess?
    unresolved   [str]           WHAT IT COULD NOT CHECK. l9's grounding report.
    why          str             human-readable reason

`basis` and `unresolved` are the two halves of the thing l9 exists to carry:
what the speaker was going on, and what the listener could actually verify.
"""
from __future__ import annotations

import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.append(os.path.join(_HERE, "..", "l9"))

from floor import Floor          # noqa: E402
from office import Office        # noqa: E402

PORTS = {"office": 9207, "floor": 9208}


# ── the agents' memories, as JSON ──────────────────────────────────────────────

def floor_state(f: Floor) -> dict:
    """Everything the Floor has learned, JSON-able (sets become sorted lists)."""
    return {
        "seen": {s: [sorted(v) for v in uses] for s, uses in f.seen.items()},
        "meaning": {s: sorted(m) for s, m in f.meaning.items()},
        "revisions": f.revisions,
    }


def floor_from(state: dict, rng: random.Random, honest: bool) -> Floor:
    f = Floor(rng=rng, honest=honest)
    f.seen = {s: [set(v) for v in uses] for s, uses in (state or {}).get("seen", {}).items()}
    f.meaning = {s: frozenset(m) for s, m in (state or {}).get("meaning", {}).items()}
    f.revisions = list((state or {}).get("revisions", []))
    return f


def office_state(o: Office) -> dict:
    return {"symbol_of": o.symbol_of, "score": o.score,
            "sent": o.sent, "revisions": o.revisions}


def office_from(state: dict, rng: random.Random) -> Office:
    o = Office(rng=rng)
    o.symbol_of = dict((state or {}).get("symbol_of", {}))
    o.score = dict((state or {}).get("score", {}))
    o.sent = dict((state or {}).get("sent", {}))
    o.revisions = list((state or {}).get("revisions", []))
    return o
