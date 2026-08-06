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

from compress import FIELDS, VOCAB, make_record, verbose_tokens
from llm_compress import LLMBackend, _extract_json

# --- Token cost model (see report_tokens) --------------------------------- #
# The wire is opaque, one token per field, every round and every arm.
WIRE_TOKENS = len(FIELDS)
# How many tokens the feedback (the "protocol" side-channel) costs per round.
FEEDBACK_COST = {
    "scalar": lambda correct, record: 1,                       # one win/lose bit
    "perfield": lambda correct, record: len(FIELDS),           # one bit per field
    "repair": lambda correct, record:                          # ack right, teach wrong
        sum(1 if correct[f] else len(record[f].split()) for f in FIELDS),
}
STREAK_K = 3   # a K-win streak = "grounded"; after it, drop the feedback channel

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


def render(arm: str, wire: Dict[str, str], history: List[Dict],
           tom_prompt: Optional[str] = None) -> List[Dict]:
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
    msgs = [{"role": "system", "content": SYSTEM}]
    if tom_prompt:
        msgs.append({"role": "system", "content": tom_prompt})
    msgs.append({"role": "user", "content": user})
    return msgs


# --------------------------------------------------------------------------- #
# Backends.                                                                     #
# --------------------------------------------------------------------------- #
class ReceiverLLM:
    def __init__(self, model: Optional[str] = None, temperature: float = 0.2):
        self.http = LLMBackend(model=model, temperature=temperature)
        self.kind, self.model = self.http.kind, self.http.model

    def guess(self, arm: str, wire: Dict[str, str], history: List[Dict],
              tom_prompt: Optional[str] = None) -> Dict:
        return _extract_json(self.http.chat(render(arm, wire, history, tom_prompt)))


class ReceiverMock:
    """Not an LLM. Grounds symbols by elimination from history (per-field feedback)
    or only from whole-record wins (scalar) — showing the credit-assignment gap."""

    kind = "mock"
    model = "mock"

    def guess(self, arm: str, wire: Dict[str, str], history: List[Dict],
              tom_prompt: Optional[str] = None) -> Dict:
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
# Theory of Mind — the first-contact analog of l9/mind.py.                       #
# --------------------------------------------------------------------------- #
class SymbolMind:
    """The RECEIVER's Theory of Mind about the SENDER's private code.

    Mirrors l9/mind.py's epistemic surface (peer_model, grounded/unresolved,
    advise(), metrics()/coverage, ground_threshold/target) but adapted to this
    task: instead of inferring a peer's free-text vocabulary via an LLM, the
    "evidence" is the structured feedback the protocol exposes, so belief is
    computed deterministically. Each observe() rebuilds belief from the whole
    history (stateless-friendly), then advise() emits a memory+strategy prompt to
    inject before the receiver's LLM call — turning a reactive guesser into one
    that carries an explicit model of the other agent's language.

    peer_model:  (field, symbol) -> {"best": phrase|None, "count": int,
                                      "ruled_out": set[str]}
    """

    def __init__(self, fields: List[str], vocab: Dict[str, List[str]], *,
                 ground_threshold: int = 1) -> None:
        self.fields = list(fields)
        self.vocab = vocab
        self.ground_threshold = ground_threshold
        self.target = sum(len(vocab[f]) for f in fields)   # total symbols to ground
        self.peer_model: Dict[tuple, Dict] = {}

    def _touch(self, f: str, sym: str) -> Dict:
        return self.peer_model.setdefault((f, sym),
                                          {"best": None, "count": 0, "ruled_out": set()})

    def observe(self, history: List[Dict], arm: str) -> "SymbolMind":
        """Rebuild the peer model from whatever signal this arm's feedback exposes."""
        self.peer_model = {}
        for h in history:
            for f in self.fields:
                sym = h["wire"][f]
                e = self._touch(f, sym)
                if arm == "repair":
                    e["best"], e["count"] = h["record"][f], e["count"] + 1
                elif arm == "perfield":
                    if h["correct"][f]:
                        e["best"], e["count"] = h["guess"][f], e["count"] + 1
                    else:
                        e["ruled_out"].add(h["guess"][f])
                elif arm == "scalar" and h["win"]:      # a win confirms all four
                    e["best"], e["count"] = h["guess"][f], e["count"] + 1
        return self

    def grounded(self) -> List[tuple]:
        return [k for k, v in self.peer_model.items()
                if v["best"] and v["count"] >= self.ground_threshold]

    def advise(self, wire: Dict[str, str]) -> Dict:
        grounded = set(self.grounded())
        by_field: Dict[str, List] = {}
        for (f, sym), v in self.peer_model.items():
            by_field.setdefault(f, []).append((sym, v))

        lines = ["THEORY OF MIND — your model of the SENDER's private code "
                 "(carry it forward; do not forget):"]
        for f in self.fields:
            parts = []
            for sym, v in by_field.get(f, []):
                if (f, sym) in grounded:
                    parts.append(f"{sym}='{v['best']}' (confirmed)")
                elif v["ruled_out"]:
                    parts.append(f"{sym}=? (ruled out: {', '.join(sorted(v['ruled_out']))})")
            if parts:
                lines.append(f"  {f}: " + " | ".join(parts))
        lines.append(f"Grounded {len(grounded)}/{self.target} of the sender's symbols.")

        todo = [f for f in self.fields if (f, wire[f]) not in grounded]
        if todo:
            focus = ", ".join(f"{f}:{wire[f]}" for f in todo)
            lines.append(f"NEXT MOVE: for this round's still-unconfirmed symbols ({focus}), "
                         "reuse a confirmed phrase if the symbol already matches one, "
                         "otherwise pick a phrase you have NOT already ruled out.")
        else:
            lines.append("NEXT MOVE: every symbol this round is already confirmed — reuse them.")

        seen = set(self.peer_model)
        return {"prompt": "\n".join(lines),
                "grounded": sorted(f"{f}:{s}" for f, s in grounded),
                "unresolved": sorted(f"{f}:{s}" for f, s in seen - grounded)}

    def metrics(self) -> Dict:
        g = self.grounded()
        return {"grounded": len(g), "target": self.target,
                "coverage": round(len(g) / self.target, 3) if self.target else 0.0}


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
        trace=None, tom: bool = False) -> Dict:
    code_map = build_code_map(seed)
    history: List[Dict] = []
    wins: List[bool] = []
    field_hits: List[int] = []          # 0..len(FIELDS) correct per round
    cov_log: List[float] = []           # ToM lexicon coverage going into each round
    fb_log: List[int] = []              # feedback (protocol side-channel) tokens/round
    plain_log: List[int] = []           # plaintext baseline tokens/round
    mind = SymbolMind(FIELDS, VOCAB) if tom else None
    label = f"{arm}+tom" if tom else arm

    if trace is not None:
        trace.write(json.dumps({"event": "arm_start", "arm": label, "tom": tom,
                                "seed": seed, "total": total,
                                "code_map": {k: v for k, v in code_map.items()}}) + "\n")

    for r in range(total):
        record = make_record(seed, r)
        wire = encode(record, code_map)

        tom_prompt = tom_grounded = None
        if mind is not None:
            mind.observe(history, arm)
            adv = mind.advise(wire)
            tom_prompt, tom_grounded = adv["prompt"], adv["grounded"]
            cov_log.append(mind.metrics()["coverage"])

        raw = receiver.guess(arm, wire, history, tom_prompt)
        guess = {f: _canon(f, raw.get(f, "")) for f in FIELDS}
        correct = {f: guess[f] == record[f] for f in FIELDS}
        win = all(correct.values())
        wins.append(win)
        field_hits.append(sum(correct.values()))
        fb_log.append(FEEDBACK_COST[arm](correct, record))
        plain_log.append(verbose_tokens(record))

        if verbose:
            marks = "".join("+" if correct[f] else "." for f in FIELDS)
            cov = f" cov={cov_log[-1]:.0%}" if mind is not None else ""
            print(f"  [{label[:12]:<12} r{r:02d}] {[wire[f] for f in FIELDS]} "
                  f"{marks} {'WIN' if win else ''}{cov}")

        if trace is not None:
            row = {
                "event": "round", "arm": label, "round": r,
                "symbols": {f: wire[f] for f in FIELDS},
                "truth": record, "guess": guess, "raw": raw,
                "correct": correct, "hits": sum(correct.values()), "win": win,
            }
            if mind is not None:
                row["tom_coverage"] = cov_log[-1]
                row["tom_grounded"] = tom_grounded
            trace.write(json.dumps(row, ensure_ascii=False) + "\n")

        # Feedback the receiver will see next round (this IS the A/B). The record
        # is stored so the repair arm can reveal truth; other arms don't expose it.
        history.append({"wire": wire, "guess": guess, "correct": correct,
                        "win": win, "record": record})

    # Final ToM coverage after all feedback is in.
    cov_final = None
    if mind is not None:
        cov_final = mind.observe(history, arm).metrics()["coverage"]

    result = {"arm": label, "tom": tom, "wins": wins, "field_hits": field_hits,
              "total": total, "coverage_final": cov_final,
              "fb_log": fb_log, "plain_log": plain_log, "src_arm": arm}
    if trace is not None:
        nf = len(FIELDS)
        half = total // 2
        trace.write(json.dumps({
            "event": "arm_summary", "arm": label, "tom": tom,
            "per_field_acc": sum(field_hits) / (total * nf),
            "per_field_1st_half": sum(field_hits[:half]) / max(1, half * nf),
            "per_field_2nd_half": sum(field_hits[half:]) / max(1, (total - half) * nf),
            "whole_record_acc": sum(wins) / total,
            "first_3win_streak": _first_streak(wins),
            "tom_coverage_final": cov_final,
            "grounded_at": _grounded_at(wins),
            "feedback_tokens_total": sum(fb_log),
            "wire_tokens_per_round": WIRE_TOKENS,
            "plaintext_tokens_total": sum(plain_log),
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
    print(f"  {'arm':<14} | {'per-field acc':>22} | {'whole-record acc':>22} | "
          f"{'streak':>7} | {'ToM':>5}")
    print(f"  {'':<14} | {'overall  1st->2nd half':>22} | "
          f"{'overall  1st->2nd half':>22} | {'@round':>7} | {'cov':>5}")
    print("  " + "-" * 84)
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
        cov = r.get("coverage_final")
        cov_s = f"{cov:.0%}" if cov is not None else "  -"
        print(f"  {r['arm']:<14} | {fa:>6.0%} {fa1:>6.0%}->{fa2:<8.0%} | "
              f"{wa:>6.0%} {wa1:>6.0%}->{wa2:<8.0%} | {streak_s:>7} | {cov_s:>5}")
    print("=" * 82)
    print("  Convergence, not compression. Richer grounding acts help monotonically:")
    print("  scalar (win/lose) < perfield (confirm) < repair (confirm+correct).")
    print("  +tom = an l9-style Theory-of-Mind advisor that carries an explicit model")
    print("  of the sender's code (peer_model) into each guess; 'ToM cov' = fraction of")
    print("  the sender's symbols the receiver has grounded.")


def _grounded_at(wins: List[bool]) -> Optional[int]:
    """Round at which the receiver is deemed grounded: the end of the first K-win
    streak (the point you'd be confident enough to switch off the feedback)."""
    s = _first_streak(wins, STREAK_K)
    return None if s is None else s + STREAK_K - 1


def report_tokens(results: List[Dict], horizon: int = 60) -> None:
    """Cost to reach reliable, feedback-free communication.

    Model: every round costs WIRE_TOKENS on the wire (opaque codes) plus the arm's
    feedback tokens. Once grounded (a K-win streak) you switch OFF the feedback
    channel and ride the bare wire, reliably. Arms that never ground keep paying
    feedback forever AND stay unreliable. Plaintext is the always-reliable, never-
    cheap baseline (spell everything out, every round)."""
    print("\n" + "=" * 82)
    print("TOKEN COST — reaching reliable, feedback-free communication")
    print("=" * 82)
    print("  wire = 4 opaque tokens/round (all arms). feedback/round: scalar~1, "
          "perfield~4, repair~phrases.")
    plain_round = sum(results[0]["plain_log"]) / max(1, len(results[0]["plain_log"]))
    print(f"  plaintext baseline: ~{plain_round:.0f} tokens/round, always reliable, "
          f"never cheaper -> {plain_round * horizon:.0f} over {horizon} rounds.\n")
    print(f"  {'arm':<14} | {'grounded':>9} | {'feedback to':>12} | {'steady':>7} | "
          f"{'proj. ' + str(horizon) + 'r':>9} | reliable?")
    print(f"  {'':<14} | {'@round':>9} | {'ground (tok)':>12} | {'tok/rnd':>7} | "
          f"{'tokens':>9} |")
    print("  " + "-" * 78)
    for r in results:
        g = _grounded_at(r["wins"])
        fb = r["fb_log"]
        if g is not None:
            overhead = sum(fb[:g + 1])                       # feedback paid while learning
            proj = WIRE_TOKENS * horizon + overhead          # then wire-only, forever
            g_s, steady_s, rel = str(g), str(WIRE_TOKENS), "yes"
        else:
            overhead = sum(fb)
            avg_fb = overhead / max(1, len(fb))
            proj = (WIRE_TOKENS + avg_fb) * horizon           # keeps paying feedback
            g_s, steady_s, rel = "never", f"{WIRE_TOKENS + avg_fb:.0f}", "NO (still erroring)"
        print(f"  {r['arm']:<14} | {g_s:>9} | {overhead:>12} | {steady_s:>7} | "
              f"{proj:>9.0f} | {rel}")
    print("=" * 82)
    print("  ToM's payoff is here: it collapses the learning phase, so you reach the")
    print("  bare 4-token/round channel fast and stop paying feedback; without it you")
    print("  keep paying the side-channel (and never become reliable).")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", choices=["scalar", "perfield", "repair", "all"], default="all")
    ap.add_argument("--total", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--model", default=None)
    ap.add_argument("--mock", action="store_true", help="Offline heuristic (no API key).")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--tom", choices=["off", "on", "compare"], default="off",
                    help="l9-style Theory-of-Mind advisor: off, on, or compare "
                         "(run each arm both with and without ToM).")
    ap.add_argument("--trace", nargs="?", const="", default=None,
                    help="Write a JSONL trace. Optional path; default auto-names a file.")
    args = ap.parse_args()

    arms = ["scalar", "perfield", "repair"] if args.arm == "all" else [args.arm]
    # Build (arm, tom) plan.
    if args.tom == "compare":
        plan = [(a, t) for a in arms for t in (False, True)]
    else:
        plan = [(a, args.tom == "on") for a in arms]
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
            "total": args.total, "arms": arms, "tom": args.tom,
            "fields": FIELDS, "vocab": VOCAB, "started_utc": stamp,
        }) + "\n")

    plan_labels = [a + ("+tom" if t else "") for a, t in plan]
    print(f"First Contact  |  seed={args.seed}  rounds={args.total}  plan={plan_labels}")
    try:
        results = [run(receiver, arm, args.seed, args.total, args.verbose, trace, tom)
                   for arm, tom in plan]
    finally:
        if trace is not None:
            trace.close()
    report(results, name)
    report_tokens(results)
    if trace_path:
        print(f"\n  trace saved -> {trace_path}")


if __name__ == "__main__":
    main()
