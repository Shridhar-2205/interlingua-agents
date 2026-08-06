"""Emergent shorthand — token-compression primitives.

Pure functions, no stored state. Called by stateless agents that read/write all
state via an A2A message data Part (see compress_state.py), exactly like the
Lewis demo's emergent.py / emergent_state.py split.

The idea: two agents relay a stream of structured MISSION LOG records. The
speaker (Grace) must convey each record so the listener (Rocky) reconstructs it
exactly. Records reuse a small vocabulary, so most content recurs. A thin
PROTOCOL lets the pair build a shared CODEBOOK: define a short code for a value
ONCE (costs the full phrase that round), then REFER to it cheaply forever after.

Two arms, identical task, one flag apart:

    verbose   - spell every value, every round            (flat token cost)
    codebook  - DEFINE a code once, then REFER (protocol)  (token cost decays)

Both are LOSSLESS (exact reconstruction), so accuracy stays 100% in both arms;
the only thing that changes is tokens-on-the-wire. That is the whole point: the
protocol buys cost, not correctness.

Run the offline simulator (no a2a-sdk needed) to see the curve:

    python compress.py
"""
from __future__ import annotations

import random
from typing import Dict, List, Tuple

# A mission-log record has these fields; each draws from a small recurring vocab
# of multi-word phrases (so spelling one out costs several tokens, a code costs 1).
FIELDS = ["loc", "act", "stat", "crew"]
VOCAB: Dict[str, List[str]] = {
    "loc": ["docking bay seven", "engine room four", "medical bay two", "cargo hold nine"],
    "act": ["seal the hull breach", "vent the plasma coolant",
            "reroute the main power", "purge the outer airlock"],
    "stat": ["status critical", "status nominal", "status degraded"],
    "crew": ["three crew aboard", "two crew aboard", "one crew aboard"],
}

Record = Dict[str, str]
Wire = Dict[str, str]
Codebook = Dict[str, str]   # value phrase -> short code (e.g. "docking bay seven" -> "$1")


def make_record(seed: int, r: int) -> Record:
    """Deterministic record for round r. Small vocab => values recur across rounds."""
    rng = random.Random(f"{seed}|{r}")
    return {f: rng.choice(VOCAB[f]) for f in FIELDS}


def next_code(codebook: Codebook) -> str:
    return f"${len(codebook) + 1}"


def encode_verbose(record: Record) -> Wire:
    """No protocol: every field carries its full phrase, every round."""
    return {f: record[f] for f in FIELDS}


def encode_codebook(record: Record, codebook: Codebook) -> Tuple[Wire, Codebook]:
    """Protocol: REFER by code if the value is already coded; else DEFINE it
    (spell it out this round) and register a code for future REFERs.

    Returns (wire, updated_codebook). The codebook travels in shared state, so
    the listener can resolve any code and future rounds get the cheap REFER."""
    cb = dict(codebook)
    wire: Wire = {}
    for f in FIELDS:
        val = record[f]
        if val in cb:
            wire[f] = cb[val]          # REFER  -> 1 token
        else:
            cb[val] = next_code(cb)    # register for next time
            wire[f] = val              # DEFINE -> full phrase this round
    return wire, cb


def decode_record(wire: Wire, codebook: Codebook) -> Record:
    """Reconstruct a record from a wire + shared codebook. Unified across arms:
    a segment that is a known code resolves to its phrase; anything else is a
    literal phrase (verbose, or a DEFINE round's spelled-out value)."""
    rev = {code: val for val, code in codebook.items()}
    return {f: rev.get(wire[f], wire[f]) for f in FIELDS}


def tokens(wire: Wire) -> int:
    """Wire-tokens = whitespace words across the transmitted segments. Field
    labels are part of the fixed schema (not re-sent), so they don't count."""
    return sum(len(str(seg).split()) for seg in wire.values())


def verbose_tokens(record: Record) -> int:
    """What this record WOULD cost spelled out — the counterfactual baseline."""
    return sum(len(v.split()) for v in record.values())


# --------------------------------------------------------------------------- #
# Offline simulator — the exact same logic the A2A agents run, but as a plain  #
# loop so you can see the compression curve without a2a-sdk.                    #
# --------------------------------------------------------------------------- #
def simulate(seed: int, total: int, arm: str) -> Dict[str, object]:
    codebook: Codebook = {}
    tokens_log: List[int] = []
    verbose_log: List[int] = []
    wins = 0
    for r in range(total):
        record = make_record(seed, r)
        if arm == "codebook":
            wire, codebook = encode_codebook(record, codebook)
        else:
            wire = encode_verbose(record)
        tokens_log.append(tokens(wire))
        verbose_log.append(verbose_tokens(record))
        # Listener reconstructs from wire + shared codebook only
        reconstruction = decode_record(wire, codebook)
        wins += int(reconstruction == record)
    return {"arm": arm, "tokens_log": tokens_log, "verbose_log": verbose_log,
            "wins": wins, "total": total, "codebook": codebook}


def summarize(res: Dict[str, object]) -> str:
    tl: List[int] = res["tokens_log"]        # type: ignore[assignment]
    vl: List[int] = res["verbose_log"]       # type: ignore[assignment]
    total: int = res["total"]                # type: ignore[assignment]
    k = max(1, total // 4)
    first = sum(tl[:k]) / k
    last = sum(tl[-k:]) / k
    ratio = (sum(vl) / sum(tl)) if sum(tl) else 1.0
    return (f"arm={res['arm']:<9} accuracy={res['wins']}/{total} "
            f"tokens={sum(tl)} (vs verbose {sum(vl)}) ratio={ratio:.2f}x  "
            f"per-round: first{k}avg={first:.1f} -> last{k}avg={last:.1f}")


def _main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Offline token-compression simulator.")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--total", type=int, default=24)
    ap.add_argument("--curve", action="store_true", help="Print per-round token curve.")
    args = ap.parse_args()

    print(f"Mission Log Relay  |  seed={args.seed}  rounds={args.total}  "
          f"fields={FIELDS}\n" + "=" * 72)
    results = {arm: simulate(args.seed, args.total, arm) for arm in ("verbose", "codebook")}
    for arm in ("verbose", "codebook"):
        print("  " + summarize(results[arm]))
    if args.curve:
        vb: List[int] = results["verbose"]["tokens_log"]   # type: ignore[index]
        cb: List[int] = results["codebook"]["tokens_log"]  # type: ignore[index]
        print("\n  round  verbose  codebook")
        for r, (v, c) in enumerate(zip(vb, cb)):
            bar = "#" * c
            print(f"  {r:>4}   {v:>6}   {c:>7}  {bar}")
    print("=" * 72)


if __name__ == "__main__":
    _main()
