#!/usr/bin/env python3
"""Export the Grounding (Theory-of-Mind) demo data from a first-contact trace.

Reads a JSONL trace produced by ``llm_firstcontact.py --tom compare --trace`` and
emits ``firstcontact_data.js`` (``window.FC_DATA = {...}``) for the demo UI. This
is REAL LLM behaviour (not scripted): the sender speaks an opaque code, the
receiver grounds it from feedback, and with ToM it converges fast enough to drop
the feedback channel and ride the bare wire.

    python export_firstcontact.py --trace ../firstcontact_trace_llm_...jsonl
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from compress import FIELDS, verbose_tokens  # noqa: E402

FIELD_LABELS = {"loc": "location", "act": "action", "stat": "status", "crew": "crew"}
WIRE_TOKENS = len(FIELDS)
STREAK_K = 3


def _feedback_tokens(base_arm: str, correct: dict, truth: dict) -> int:
    if base_arm == "scalar":
        return 1
    if base_arm == "perfield":
        return len(FIELDS)
    if base_arm == "repair":
        return sum(1 if correct[f] else len(truth[f].split()) for f in FIELDS)
    return len(FIELDS)


def _grounded_at(wins: list) -> int | None:
    for i in range(len(wins) - STREAK_K + 1):
        if all(wins[i:i + STREAK_K]):
            return i + STREAK_K - 1
    return None


def _reverse_code_map(code_map: dict) -> dict:
    """{'loc:cargo hold nine': '⋈', ...} -> {'⋈': {'field','phrase'}}."""
    rev = {}
    for key, glyph in code_map.items():
        field, phrase = key.split(":", 1)
        rev[glyph] = {"field": field, "phrase": phrase}
    return rev


def parse_trace(path: str) -> dict:
    session = None
    arms: dict = {}
    order: list = []
    cur = None  # current arm label

    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            ev = json.loads(line)
            kind = ev.get("event")
            if kind == "session":
                session = ev
            elif kind == "arm_start":
                cur = ev["arm"]
                order.append(cur)
                arms[cur] = {
                    "label": cur, "tom": ev.get("tom", False),
                    "base_arm": cur.replace("+tom", ""),
                    "symbolTruth": _reverse_code_map(dict(ev["code_map"])),
                    "rounds_raw": [],
                }
            elif kind == "round":
                arms[ev["arm"]]["rounds_raw"].append(ev)
            elif kind == "arm_summary":
                arms[ev["arm"]]["summary_raw"] = ev

    if session is None:
        raise SystemExit("Trace has no session header; is this a firstcontact trace?")

    fields = session.get("fields", FIELDS)
    vocab = session.get("vocab", {})
    total = session.get("total", 0)

    out_arms = {}
    for label in order:
        a = arms[label]
        wins = [r["win"] for r in a["rounds_raw"]]
        g_at = _grounded_at(wins)
        sym_truth = a["symbolTruth"]

        cum_wire = cum_fb = cum_eff = cum_plain = 0
        rounds = []
        for r in a["rounds_raw"]:
            idx = r["round"]
            truth = r["truth"]
            correct = r["correct"]
            fb = _feedback_tokens(a["base_arm"], correct, truth)
            feedback_active = (g_at is None) or (idx <= g_at)
            eff_fb = fb if feedback_active else 0
            plain = verbose_tokens(truth)

            cum_wire += WIRE_TOKENS
            cum_fb += eff_fb
            cum_eff += WIRE_TOKENS + eff_fb
            cum_plain += plain

            # ToM peer model grounded so far (symbol -> phrase), from tom_grounded
            peer = []
            for gk in r.get("tom_grounded", []) or []:
                fld, sym = gk.split(":", 1)
                phrase = sym_truth.get(sym, {}).get("phrase", "?")
                peer.append({"field": fld, "label": FIELD_LABELS.get(fld, fld),
                             "symbol": sym, "phrase": phrase})

            rounds.append({
                "r": idx,
                "symbols": {f: r["symbols"][f] for f in fields},
                "wireTokens": WIRE_TOKENS,
                "guess": r["guess"],
                "correct": correct,
                "hits": r["hits"],
                "win": r["win"],
                "coverage": r.get("tom_coverage"),
                "peerModel": peer,
                "feedbackTokens": fb,
                "feedbackActive": feedback_active,
                "cumWire": cum_wire,
                "cumFeedback": cum_fb,
                "cumEffective": cum_eff,
                "cumPlaintext": cum_plain,
            })

        # Projection over a horizon (matches llm_firstcontact.report_tokens).
        horizon = 60
        fb_all = [rr["feedbackTokens"] for rr in rounds]
        if g_at is not None:
            overhead = sum(fb_all[:g_at + 1])
            proj = WIRE_TOKENS * horizon + overhead
            reliable = True
        else:
            overhead = sum(fb_all)
            avg_fb = overhead / max(1, len(fb_all))
            proj = (WIRE_TOKENS + avg_fb) * horizon
            reliable = False

        sr = a.get("summary_raw", {})
        out_arms[label] = {
            "label": label, "tom": a["tom"], "baseArm": a["base_arm"],
            "groundedAt": g_at, "reliable": reliable,
            "rounds": rounds,
            "summary": {
                "perFieldAcc": sr.get("per_field_acc"),
                "wholeRecordAcc": sr.get("whole_record_acc"),
                "coverageFinal": sr.get("tom_coverage_final"),
                "feedbackOverhead": overhead,
                "projHorizon": horizon,
                "projTokens": round(proj),
                "steadyPerRound": WIRE_TOKENS if g_at is not None
                else round(WIRE_TOKENS + overhead / max(1, len(fb_all)), 1),
            },
        }

    plain_round = round(sum(verbose_tokens(r["truth"]) for r in arms[order[0]]["rounds_raw"])
                        / max(1, total), 1)

    return {
        "meta": {
            "title": "First Contact — Grounding an Opaque Code (Theory of Mind)",
            "receiver": session.get("receiver", "?"),
            "seed": session.get("seed"), "total": total,
            "fields": fields, "fieldLabels": FIELD_LABELS, "vocab": vocab,
            "wireTokensPerRound": WIRE_TOKENS,
            "plaintextPerRound": plain_round,
            "horizon": 60,
            "plaintextProjection": round(plain_round * 60),
            "generatedFrom": os.path.basename(path),
        },
        "armOrder": order,
        "arms": out_arms,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trace", default=None,
                    help="Path to a firstcontact trace JSONL. Defaults to the newest "
                         "firstcontact_trace_llm_*.jsonl in the parent folder.")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "firstcontact_data.js"))
    args = ap.parse_args()

    trace = args.trace
    if trace is None:
        parent = Path(__file__).resolve().parent.parent
        cands = sorted(glob.glob(str(parent / "firstcontact_trace_llm_*.jsonl")))
        if not cands:
            raise SystemExit("No firstcontact_trace_llm_*.jsonl found; pass --trace.")
        trace = cands[-1]

    data = parse_trace(trace)
    payload = "window.FC_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    Path(args.out).write_text(payload, encoding="utf-8")

    print(f"Wrote {args.out}  (from {os.path.basename(trace)})")
    for label in data["armOrder"]:
        a = data["arms"][label]
        s = a["summary"]
        g = a["groundedAt"]
        print(f"  {label:<14} grounded@{g if g is not None else 'never':<6} "
              f"proj {s['projTokens']:>4} tok  reliable={a['reliable']}")


if __name__ == "__main__":
    main()
