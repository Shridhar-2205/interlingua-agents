"""Run both arms and write the whole thing out for the UI to replay.

Real output, not mock data.

A design note, because it is a real choice. If you simply run the session twice,
the two arms drift apart within ten rounds — the Office adapts to whichever
picker it is talking to, so a yes-man partner produces different word choices.
That is honest behaviour, but it means the two runs are no longer answering the
same question, and a side-by-side becomes meaningless.

So we hold the speaker fixed: run the honest session, record every message it
sent, and replay that exact stream to a yes-man picker. Both then see the
identical orders and the identical marks, and the only variable left is what the
picker does when it isn't sure. That is the comparison worth showing.

    python export_trace.py                 # -> ui/trace.js
    python export_trace.py --orders 80 --seed 3
"""
from __future__ import annotations

import json
import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.append(os.path.join(_HERE, "..", "l9"))

import catalogue                     # noqa: E402
import signaling                     # noqa: E402
from floor import Floor              # noqa: E402
from office import Office            # noqa: E402


def arm(honest: bool, orders: int, seed: int,
        script: list[dict] | None = None) -> list[dict]:
    """One full session, recorded round by round.

    With `script`, the Office is not run at all — we replay the exact orders and
    marks it produced in another session, so this picker faces identical input.
    """
    rng = random.Random(seed)
    office = Office(rng=random.Random(seed + 1))
    floor = Floor(rng=random.Random(seed + 2), honest=honest)
    history: list[dict] = []
    out: list[dict] = []

    for n in range(1, orders + 1):
        if script:
            ordered = script[n - 1]["ordered"]
            msg = {"symbols": script[n - 1]["marks"], "basis": script[n - 1]["basis"]}
        else:
            ordered = rng.choice(catalogue.products())
            msg = office.describe(ordered)
        act = floor.pick(msg["symbols"])
        # the listener's side of the exchange, as it stood at the moment it decided
        understood, unresolved = floor.resolve(msg["symbols"])
        cands, fit = floor.candidates(understood)

        if act["choice"] is not None:
            history = signaling.record_outcome(
                history, ordered, "".join(msg["symbols"]), True, "floor",
                grounded=act["grounded"])

        # Snapshot what the Floor knew AT THE MOMENT IT DECIDED — this is what
        # explains the decision, and it must not include what the open box is
        # about to teach it.
        knew = {s: " + ".join(sorted(m)) for s, m in floor.meaning.items()}
        conf = {s: floor.confidence(s) for s in floor.meaning}

        # Decide first, then open the box, then learn — so the belief changes
        # belong to this round but happen after its decision.
        fr, orv = len(floor.revisions), len(office.revisions)
        floor.learn(msg["symbols"], ordered, round_no=n)
        if not script:
            office.learn(msg["basis"], act["unresolved"], act["choice"] == ordered, round_no=n)

        out.append({
            "n": n,
            "ordered": ordered,
            "marks": msg["symbols"],
            "basis": msg["basis"],
            "understood": sorted(understood),
            "unresolved": list(unresolved),      # what it could NOT check
            "candidates": list(cands),           # boxes still consistent with it
            "fit": fit,
            "choice": act["choice"],
            "grounded": act["grounded"],
            "reason": act["reason"],
            "correct": act["choice"] == ordered,
            "refused": act["choice"] is None,
            # the shared vocabulary as it stood when this decision was made
            "glossary": knew,
            "meant": {s: f for f, s in office.symbol_of.items()},
            "gar": signaling.gar(history),
            "scr": signaling.scr(history),
            "w": signaling.provenance_weight(history),

            # --- Theory of Mind: each agent's model of the other ---
            # the Office's model of what the Floor can PERCEIVE (not what it says)
            "office_model": dict(office.score),
            # how sure the Floor was of each mark it had a reading for
            "floor_conf": conf,
            # the moments either mind changed, once this box was opened
            "revisions": floor.revisions[fr:] + office.revisions[orv:],
        })

    return out


def main() -> None:
    argv = sys.argv[1:]
    orders = int(argv[argv.index("--orders") + 1]) if "--orders" in argv else 60
    seed = int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 3

    honest = arm(True, orders, seed)
    yesman = arm(False, orders, seed, script=honest)   # same messages, different picker

    # The two arms must be answering the same question.
    for a, b in zip(honest, yesman):
        assert a["ordered"] == b["ordered"], f"order stream diverged at round {a['n']}"
        assert a["marks"] == b["marks"], f"marks diverged at round {a['n']}"

    trace = {
        "orders": orders,
        "seed": seed,
        "aisle": [{"name": p,
                   "visible": sorted(catalogue.visible(p)),
                   "hidden": sorted(catalogue.features(p) - catalogue.visible(p))}
                  for p in catalogue.products()],
        "twins": catalogue.twins(),
        "honest": honest,
        "yesman": yesman,
    }

    ui = os.path.join(_HERE, "ui")
    os.makedirs(ui, exist_ok=True)
    path = os.path.join(ui, "trace.js")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("window.TRACE = ")
        json.dump(trace, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write(";\n")

    def tally(rows):
        return (sum(r["correct"] for r in rows),
                sum(1 for r in rows if not r["refused"] and not r["correct"]),
                sum(r["refused"] for r in rows))

    hr, hw, hh = tally(honest)
    yr, yw, yh = tally(yesman)
    print(f"wrote {path}  ({os.path.getsize(path)/1024:.0f} KB)")
    print(f"  honest : {hr} right, {hw} WRONG, {hh} asked for help   W={honest[-1]['w']}")
    print(f"  yes-man: {yr} right, {yw} WRONG, {yh} asked for help   W={yesman[-1]['w']}")


if __name__ == "__main__":
    main()
