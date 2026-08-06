#!/usr/bin/env python3
"""Export a message-by-message dataset for the Interlingua compression demo UI.

Runs the SAME deterministic, lossless compression logic the A2A agents use
(compress.py), but records every wire segment so the UI can show:

  1. the PLAINTEXT message Grace would have to send with no shared code,
  2. the PROTOCOL message she actually sends (DEFINE a code once, then REFER),
  3. the EMERGED LANGUAGE (the codebook) filling in over rounds,
  4. Rocky's lossless reconstruction, and
  5. the token-cost reduction (per-round and cumulative).

Writes ``demo_data.js`` (``window.DEMO_DATA = {...}``) so ``index.html`` can load
it straight from the filesystem — no server, no build step.

    python export_demo.py --seed 1 --total 20
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Import the real compression primitives from the parent module.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from compress import FIELDS, VOCAB, make_record, next_code  # noqa: E402

FIELD_LABELS = {"loc": "location", "act": "action", "stat": "status", "crew": "crew"}


def _phase(refers: int, defines: int) -> str:
    if refers == 0:
        return "plaintext"          # nothing coded yet — must spell everything out
    if defines == 0:
        return "emerged"            # fully in the emerged code
    return "establishing"           # protocol still coining codes


def build(seed: int, total: int) -> dict:
    codebook: dict = {}             # phrase -> code (the emerged language)
    rounds = []
    cum_plain = cum_proto = 0

    for r in range(total):
        record = make_record(seed, r)

        # (1) Plaintext: every field spelled out, every round.
        plain_segs = [{"field": f, "label": FIELD_LABELS[f],
                       "phrase": record[f], "tokens": len(record[f].split())}
                      for f in FIELDS]
        plain_tok = sum(s["tokens"] for s in plain_segs)

        # (2) Protocol wire: DEFINE a new value (costs the phrase, registers a code),
        #     REFER to a known value (costs one code token).
        proto_segs, new_codes = [], []
        defines = refers = 0
        for f in FIELDS:
            val = record[f]
            if val in codebook:
                code = codebook[val]
                proto_segs.append({"field": f, "label": FIELD_LABELS[f], "kind": "refer",
                                   "phrase": val, "code": code, "tokens": 1})
                refers += 1
            else:
                code = next_code(codebook)
                codebook[val] = code
                new_codes.append({"code": code, "phrase": val,
                                  "field": f, "label": FIELD_LABELS[f]})
                proto_segs.append({"field": f, "label": FIELD_LABELS[f], "kind": "define",
                                   "phrase": val, "code": code,
                                   "tokens": len(val.split())})
                defines += 1
        proto_tok = sum(s["tokens"] for s in proto_segs)

        cum_plain += plain_tok
        cum_proto += proto_tok

        codebook_after = [{"code": c, "phrase": p}
                          for p, c in sorted(codebook.items(),
                                             key=lambda kv: int(kv[1][1:]))]

        rounds.append({
            "r": r,
            "record": record,
            "phase": _phase(refers, defines),
            "plaintext": {"segments": plain_segs, "tokens": plain_tok},
            "protocol": {"segments": proto_segs, "tokens": proto_tok,
                         "newCodes": new_codes, "defines": defines, "refers": refers},
            "codebookAfter": codebook_after,
            "reconstruction": record,      # lossless by construction
            "correct": True,
            "cumPlaintext": cum_plain,
            "cumProtocol": cum_proto,
            "savedPct": round(100 * (1 - proto_tok / plain_tok)) if plain_tok else 0,
        })

    # Steady-state (last quarter) per-round averages, for the headline.
    k = max(1, total // 4)
    steady_plain = sum(x["plaintext"]["tokens"] for x in rounds[-k:]) / k
    steady_proto = sum(x["protocol"]["tokens"] for x in rounds[-k:]) / k

    summary = {
        "totalPlaintext": cum_plain,
        "totalProtocol": cum_proto,
        "saved": cum_plain - cum_proto,
        "reductionPct": round(100 * (1 - cum_proto / cum_plain)) if cum_plain else 0,
        "ratio": round(cum_plain / cum_proto, 2) if cum_proto else 1.0,
        "steadyPlaintext": round(steady_plain, 1),
        "steadyProtocol": round(steady_proto, 1),
        "steadyReductionPct": round(100 * (1 - steady_proto / steady_plain))
        if steady_plain else 0,
        "vocabSize": sum(len(v) for v in VOCAB.values()),
    }

    return {
        "meta": {
            "title": "Interlingua — Emergent Compression Protocol",
            "seed": seed, "total": total, "fields": FIELDS,
            "fieldLabels": FIELD_LABELS, "vocab": VOCAB,
            "generatedUtc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        "rounds": rounds,
        "summary": summary,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--total", type=int, default=20)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "demo_data.js"))
    args = ap.parse_args()

    data = build(args.seed, args.total)
    payload = "window.DEMO_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    Path(args.out).write_text(payload, encoding="utf-8")

    s = data["summary"]
    print(f"Wrote {args.out}")
    print(f"  rounds={args.total} seed={args.seed}")
    print(f"  plaintext total tokens : {s['totalPlaintext']}")
    print(f"  protocol  total tokens : {s['totalProtocol']}")
    print(f"  saved                  : {s['saved']} tokens "
          f"({s['reductionPct']}% overall, {s['ratio']}x)")
    print(f"  steady-state per round : {s['steadyPlaintext']} -> {s['steadyProtocol']} "
          f"tokens ({s['steadyReductionPct']}% reduction)")


if __name__ == "__main__":
    main()
