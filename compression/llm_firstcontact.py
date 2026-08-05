#!/usr/bin/env python3
"""First Contact — grounding an OPAQUE code with no plaintext, only feedback.

The harder sibling of llm_compress.py. There, a DEFINE shipped the plaintext
phrase alongside its code, so meaning was grounded instantly (lossless from round
0). Here we withhold the plaintext entirely: the SENDER labels each field with an
opaque symbol whose meaning is never transmitted, and the RECEIVER (an LLM) must
INFER what each symbol means from feedback alone. That turns the task from
compression into genuine emergent *grounding* — accuracy has to CONVERGE.

The sender speaks a fixed but unknown "language": a consistent symbol per
field-value (same value -> same symbol, chosen opaquely). The receiver guesses
each field's phrase from the known vocabulary and learns the symbol<->phrase
mapping across rounds.

The A/B is the FEEDBACK — this is where a thin protocol earns its keep:

  scalar    - no protocol: only whole-record win/lose. A loss doesn't say WHICH
              field was wrong, so the receiver faces brutal credit assignment and
              can only learn from the (rare) all-correct rounds.
  perfield  - protocol CONFIRM: the sender reports which fields were right/wrong
              (not the answer). The receiver grounds each symbol by elimination.
  repair    - protocol CONFIRM + REPAIR: for a wrong field the sender also reveals
              the correct phrase (a teaching correction), so a symbol is grounded
              the first time it is seen.

A spectrum of grounding acts: scalar < perfield < repair. Metric: CONVERGENCE
(per-field AND whole-record accuracy over rounds, first->second half).

    python llm_firstcontact.py --mock --arm all              # offline heuristic
    python llm_firstcontact.py --arm all --total 30 --verbose  # live (needs .env)
"""
from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional

from compress import FIELDS, VOCAB, make_record
from llm_compress import LLMBackend, _extract_json

Record = Dict[str, str]

# Opaque symbols — zero linguistic hint (true first contact).
GLYPHS = list("\u25b2\u25c6\u25cf\u25a0\u2605\u2726\u25bd\u29d7\u224b\u2298\u25a1"
              "\u223f\u2b21\u2699\u25d0\u25c8\u27a0\u22c8")


# --------------------------------------------------------------------------- #
# Sender — a fixed, consistent, OPAQUE code (could be an LLM; kept deterministic  #
# so the A/B isolates the receiver's grounding under different feedback).        #
# --------------------------------------------------------------------------- #
def build_code_map(seed: int) -> Dict[str, str]:
    """Assign each field-value a distinct opaque glyph, consistently."""
    pool = list(GLYPHS)
    random.Random(seed).shuffle(pool)
    code_map: Dict[str, str] = {}
    i = 0
    for f in FIELDS:
        for v in VOCAB[f]:
            code_map[f"{f}:{v}"] = pool[i]
            i += 1
    return code_map


def encode(record: Record, code_map: Dict[str, str]) -> Dict[str, str]:
    return {f: code_map[f"{f}:{record[f]}"] for f in FIELDS}


# --------------------------------------------------------------------------- #
# Receiver prompts.                                                             #
# --------------------------------------------------------------------------- #
SYSTEM = (
    "You are the RECEIVER making FIRST CONTACT. A sender labels each field of a "
    "mission-log record (loc, act, stat, crew) with an OPAQUE symbol whose meaning "
    "you do NOT know in advance. Symbols are CONSISTENT: the same underlying value "
    "always gets the same symbol. Your job: guess each field's phrase from the "
    "known set. You get feedback after each guess — use it to learn what each "
    "symbol means. Reply with COMPACT JSON only."
)


def _vocab_block() -> str:
    return "\n".join(f"  {f}: {VOCAB[f]}" for f in FIELDS)


def _perfield_memo(history: List[Dict]) -> str:
    """What the receiver has learned per field: symbol -> tried phrases + result."""
    memo: Dict[str, Dict[str, List]] = {f: {} for f in FIELDS}
    for h in history:
        for f in FIELDS:
            sym = h["wire"][f]
            entry = (h["guess"][f], h["correct"][f])
            seen = memo[f].setdefault(sym, [])
            if entry not in seen:
                seen.append(entry)
    lines = []
    for f in FIELDS:
        if not memo[f]:
            continue
        lines.append(f"  {f}:")
        for sym, tries in memo[f].items():
            parts = ", ".join(f"'{ph}'={'RIGHT' if ok else 'wrong'}" for ph, ok in tries)
            lines.append(f"    {sym}: {parts}")
    return "\n".join(lines) if lines else "  (nothing learned yet)"


def _repair_memo(history: List[Dict]) -> str:
    """Grounded dictionary: each seen symbol -> its revealed true phrase.
    In the repair arm, a right field is confirmed and a wrong field is corrected,
    so any symbol seen even once has its meaning known."""
    known: Dict[str, Dict[str, str]] = {f: {} for f in FIELDS}
    for h in history:
        for f in FIELDS:
            known[f][h["wire"][f]] = h["record"][f]   # truth revealed via confirm/repair
    lines = []
    for f in FIELDS:
        if not known[f]:
            continue
        lines.append(f"  {f}:")
        for sym, phrase in known[f].items():
            lines.append(f"    {sym} = '{phrase}'")
    return "\n".join(lines) if lines else "  (nothing learned yet)"


def _scalar_history(history: List[Dict], window: int = 12) -> str:
    if not history:
        return "  (no rounds yet)"
    rows = []
    for h in history[-window:]:
        syms = " ".join(f"{f}={h['wire'][f]}" for f in FIELDS)
        guess = " ".join(f"{f}={h['guess'][f]}" for f in FIELDS)
        rows.append(f"  [{syms}] guessed[{guess}] -> {'WIN' if h['win'] else 'lose'}")
    return "\n".join(rows)


def render(arm: str, wire: Dict[str, str], history: List[Dict]) -> List[Dict]:
    syms = "\n".join(f"  {f}: {wire[f]}" for f in FIELDS)
    if arm == "repair":
        learned = _repair_memo(history)
        user = (f"This round's symbols:\n{syms}\n\nGrounded dictionary so far "
                f"(symbol = its confirmed phrase):\n{learned}\n\n"
                f"Allowed phrases per field:\n{_vocab_block()}\n\n"
                "If a symbol is in the dictionary, use its phrase. Otherwise make "
                "your best guess (you'll be told the correct phrase after).\n"
                "JSON: {\"loc\": \"..\", \"act\": \"..\", \"stat\": \"..\", \"crew\": \"..\"}")
    elif arm == "perfield":
        learned = _perfield_memo(history)
        user = (f"This round's symbols:\n{syms}\n\nWhat you've learned "
                f"(symbol -> phrases you tried and whether each was RIGHT):\n{learned}\n\n"
                f"Allowed phrases per field:\n{_vocab_block()}\n\n"
                "For each field: if a symbol has a phrase marked RIGHT, reuse it. "
                "Otherwise pick a phrase you have NOT already had marked wrong for "
                "that symbol.\nJSON: {\"loc\": \"..\", \"act\": \"..\", "
                "\"stat\": \"..\", \"crew\": \"..\"}")
    else:  # scalar
        hist = _scalar_history(history)
        user = (f"This round's symbols:\n{syms}\n\nRecent rounds (symbols seen, what "
                f"you guessed, whether the WHOLE record was right):\n{hist}\n\n"
                f"Allowed phrases per field:\n{_vocab_block()}\n\n"
                "A WIN means every field was right (so those symbol->phrase pairs are "
                "confirmed); a loss means at least one field was wrong but you are NOT "
                "told which. Use the wins to lock mappings and reason about the rest.\n"
                "JSON: {\"loc\": \"..\", \"act\": \"..\", \"stat\": \"..\", \"crew\": \"..\"}")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


# --------------------------------------------------------------------------- #
# Backends.                                                                     #
# --------------------------------------------------------------------------- #
class ReceiverLLM:
    def __init__(self, model: Optional[str] = None, temperature: float = 0.2):
        self.http = LLMBackend(model=model, temperature=temperature)
        self.kind, self.model = self.http.kind, self.http.model

    def guess(self, arm: str, wire: Dict[str, str], history: List[Dict]) -> Dict:
        return _extract_json(self.http.chat(render(arm, wire, history)))


class ReceiverMock:
    """Not an LLM. Grounds symbols by elimination from history (per-field feedback)
    or only from whole-record wins (scalar) — showing the credit-assignment gap."""

    kind = "mock"
    model = "mock"

    def guess(self, arm: str, wire: Dict[str, str], history: List[Dict]) -> Dict:
        rng = random.Random(len(history))
        out: Dict[str, str] = {}
        if arm == "repair":
            known: Dict[str, str] = {}
            for h in history:
                for f in FIELDS:
                    known[h["wire"][f]] = h["record"][f]   # revealed truth
            return {f: known.get(wire[f], rng.choice(VOCAB[f])) for f in FIELDS}
        if arm == "perfield":
            locked: Dict[str, str] = {}
            wrong: Dict[str, set] = {}
            for h in history:
                for f in FIELDS:
                    sym = h["wire"][f]
                    if h["correct"][f]:
                        locked[sym] = h["guess"][f]
                    else:
                        wrong.setdefault(sym, set()).add(h["guess"][f])
            for f in FIELDS:
                sym = wire[f]
                if sym in locked:
                    out[f] = locked[sym]
                else:
                    untried = [v for v in VOCAB[f] if v not in wrong.get(sym, set())]
                    out[f] = rng.choice(untried or VOCAB[f])
        else:  # scalar — only whole-record wins teach anything
            locked = {}
            for h in history:
                if h["win"]:
                    for f in FIELDS:
                        locked[h["wire"][f]] = h["guess"][f]
            for f in FIELDS:
                sym = wire[f]
                out[f] = locked.get(sym, rng.choice(VOCAB[f]))
        return out


# --------------------------------------------------------------------------- #
# Game loop.                                                                    #
# --------------------------------------------------------------------------- #
def _canon(field: str, val) -> str:
    v = str(val).strip()
    for phrase in VOCAB[field]:
        if v.lower() == phrase.lower():
            return phrase
    return v


def run(receiver, arm: str, seed: int, total: int, verbose: bool,
        trace=None) -> Dict:
    code_map = build_code_map(seed)
    history: List[Dict] = []
    wins: List[bool] = []
    field_hits: List[int] = []          # 0..len(FIELDS) correct per round

    if trace is not None:
        trace.write(json.dumps({"event": "arm_start", "arm": arm, "seed": seed,
                                "total": total,
                                "code_map": {k: v for k, v in code_map.items()}}) + "\n")

    for r in range(total):
        record = make_record(seed, r)
        wire = encode(record, code_map)

        raw = receiver.guess(arm, wire, history)
        guess = {f: _canon(f, raw.get(f, "")) for f in FIELDS}
        correct = {f: guess[f] == record[f] for f in FIELDS}
        win = all(correct.values())
        wins.append(win)
        field_hits.append(sum(correct.values()))

        if verbose:
            marks = "".join("+" if correct[f] else "." for f in FIELDS)
            print(f"  [{arm[:4]} r{r:02d}] {[wire[f] for f in FIELDS]} "
                  f"{marks} {'WIN' if win else ''}")

        if trace is not None:
            trace.write(json.dumps({
                "event": "round", "arm": arm, "round": r,
                "symbols": {f: wire[f] for f in FIELDS},
                "truth": record,
                "guess": guess,
                "raw": raw,
                "correct": correct,
                "hits": sum(correct.values()),
                "win": win,
            }, ensure_ascii=False) + "\n")

        # Feedback the receiver will see next round (this IS the A/B). The record
        # is stored so the repair arm can reveal truth; other arms don't expose it.
        history.append({"wire": wire, "guess": guess, "correct": correct,
                        "win": win, "record": record})

    result = {"arm": arm, "wins": wins, "field_hits": field_hits, "total": total}
    if trace is not None:
        nf = len(FIELDS)
        half = total // 2
        trace.write(json.dumps({
            "event": "arm_summary", "arm": arm,
            "per_field_acc": sum(field_hits) / (total * nf),
            "per_field_1st_half": sum(field_hits[:half]) / max(1, half * nf),
            "per_field_2nd_half": sum(field_hits[half:]) / max(1, (total - half) * nf),
            "whole_record_acc": sum(wins) / total,
            "first_3win_streak": _first_streak(wins),
        }) + "\n")
    return result


def _first_streak(wins: List[bool], k: int = 3) -> Optional[int]:
    for i in range(len(wins) - k + 1):
        if all(wins[i:i + k]):
            return i
    return None


def report(results: List[Dict], name: str) -> None:
    nf = len(FIELDS)
    print("\n" + "=" * 82)
    print(f"FIRST CONTACT — grounding an opaque code  |  receiver={name}")
    print("=" * 82)
    print(f"  {'arm':<10} | {'per-field acc':>22} | {'whole-record acc':>22} | "
          f"{'streak':>8}")
    print(f"  {'':<10} | {'overall  1st->2nd half':>22} | "
          f"{'overall  1st->2nd half':>22} | {'@round':>8}")
    print("  " + "-" * 78)
    for r in results:
        w, fh, total = r["wins"], r["field_hits"], r["total"]
        half = total // 2
        # per-field accuracy
        fa = sum(fh) / (total * nf)
        fa1 = sum(fh[:half]) / max(1, half * nf)
        fa2 = sum(fh[half:]) / max(1, (total - half) * nf)
        # whole-record accuracy
        wa = sum(w) / total
        wa1 = sum(w[:half]) / max(1, half)
        wa2 = sum(w[half:]) / max(1, total - half)
        streak = _first_streak(w)
        streak_s = str(streak) if streak is not None else "never"
        print(f"  {r['arm']:<10} | {fa:>6.0%} {fa1:>6.0%}->{fa2:<8.0%} | "
              f"{wa:>6.0%} {wa1:>6.0%}->{wa2:<8.0%} | {streak_s:>8}")
    print("=" * 82)
    print("  Convergence, not compression. Richer grounding acts help monotonically:")
    print("  scalar (win/lose) < perfield (confirm) < repair (confirm+correct).")
    print("  Per-field accuracy shows the climb even when all-4-at-once is still rare.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", choices=["scalar", "perfield", "repair", "all"], default="all")
    ap.add_argument("--total", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--model", default=None)
    ap.add_argument("--mock", action="store_true", help="Offline heuristic (no API key).")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--trace", nargs="?", const="", default=None,
                    help="Write a JSONL trace. Optional path; default auto-names a file.")
    args = ap.parse_args()

    arms = ["scalar", "perfield", "repair"] if args.arm == "all" else [args.arm]
    if args.mock:
        receiver, name = ReceiverMock(), "MOCK heuristic (not an LLM)"
    else:
        try:
            receiver = ReceiverLLM(model=args.model)
        except RuntimeError as e:
            raise SystemExit(f"\n{e}\n")
        name = f"{receiver.kind}:{receiver.model}"

    trace = trace_path = None
    if args.trace is not None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        tag = "mock" if args.mock else "llm"
        trace_path = args.trace or f"firstcontact_trace_{tag}_seed{args.seed}_{stamp}.jsonl"
        trace = open(trace_path, "w", encoding="utf-8")
        trace.write(json.dumps({
            "event": "session", "receiver": name, "seed": args.seed,
            "total": args.total, "arms": arms, "fields": FIELDS, "vocab": VOCAB,
            "started_utc": stamp,
        }) + "\n")

    print(f"First Contact  |  seed={args.seed}  rounds={args.total}  arms={arms}")
    try:
        results = [run(receiver, arm, args.seed, args.total, args.verbose, trace)
                   for arm in arms]
    finally:
        if trace is not None:
            trace.close()
    report(results, name)
    if trace_path:
        print(f"\n  trace saved -> {trace_path}")


if __name__ == "__main__":
    main()
