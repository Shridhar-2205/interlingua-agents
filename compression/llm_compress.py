#!/usr/bin/env python3
"""LLM version of the Mission Log Relay — agents INVENT their own shorthand.

This is to compress.py what l9/ is to the root Lewis demo: the same task, but
driven by LLM agents instead of a deterministic rule. Now the shorthand is not
handed to the agents ($1, $2, ...); the SENDER invents codes and the RECEIVER
must reconstruct records from them. The interesting question stops being "can we
compress" (the rule-based version already does) and becomes "can two LLMs evolve
a shared shorthand that stays LOSSLESS while it gets shorter?"

The A/B isolates the protocol (the ONLY difference between arms):

  freeform  - the sender compresses however it likes; both agents share a running
              transcript of (what was sent -> what it really was). No explicit
              codebook, so shorthand can be ambiguous or drift -> accuracy slips.
  codebook  - a thin PROTOCOL: an explicit shared codebook plus DEFINE / REFER.
              The LLM still invents the codes; the structure just keeps reuse
              disciplined and unambiguous -> compression WITHOUT losing accuracy.

Metrics per arm: convergence of tokens-per-round (compression) AND accuracy
(exact reconstruction). The headline is accuracy-under-compression.

    # offline heuristic (no key) — verifies the harness + shows the failure mode:
    python llm_compress.py --mock --arm both

    # live (reads compression/.env, or inherits Azure/OpenAI vars from the env):
    python llm_compress.py --arm both --total 10
"""
from __future__ import annotations

import argparse
import json
import os
import random
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from compress import FIELDS, VOCAB, make_record, tokens, verbose_tokens

Record = Dict[str, str]
HISTORY = 8   # rounds of shared transcript / codebook shown in prompts


# --------------------------------------------------------------------------- #
# Credentials + LLM backend (self-contained; Azure or OpenAI; stdlib only).    #
# --------------------------------------------------------------------------- #
def _load_env(path: Path) -> None:
    """Minimal .env loader (no dep). Values already in the environment win."""
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env(Path(__file__).with_name(".env"))   # compression/.env (gitignored)


def _extract_json(text: str) -> dict:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    t = t.strip()
    try:
        return json.loads(t)
    except Exception:  # noqa: BLE001
        i, j = t.find("{"), t.rfind("}")
        try:
            return json.loads(t[i:j + 1]) if i != -1 and j > i else {}
        except Exception:  # noqa: BLE001
            return {}


class LLMBackend:
    """Talks to Azure OpenAI or OpenAI over HTTPS with the stdlib only."""

    def __init__(self, model: Optional[str] = None, temperature: float = 0.3,
                 timeout: float = 60.0):
        self.temperature = temperature
        self.timeout = timeout
        az_key = os.environ.get("AZURE_OPENAI_API_KEY")
        az_ep = os.environ.get("AZURE_OPENAI_ENDPOINT")
        az_dep = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        if az_key and az_ep and az_dep:
            self.kind = "azure"
            self.model = model or f"azure/{az_dep}"
            ver = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-06-01")
            self.url = f"{az_ep.rstrip('/')}/openai/deployments/{az_dep}/chat/completions?api-version={ver}"
            self.headers = {"Content-Type": "application/json", "api-key": az_key}
        elif os.environ.get("OPENAI_API_KEY"):
            self.kind = "openai"
            self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
            self.url = "https://api.openai.com/v1/chat/completions"
            self.headers = {"Content-Type": "application/json",
                            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
        else:
            raise RuntimeError(
                "No LLM credentials found. Set AZURE_OPENAI_* or OPENAI_API_KEY in "
                "compression/.env (see .env.example), or run with --mock.")

    def chat(self, messages: List[Dict], max_tokens: int = 400) -> str:
        body = {"messages": messages, "temperature": self.temperature,
                "max_tokens": max_tokens}
        if self.kind == "openai":
            body["model"] = self.model
        data = json.dumps(body).encode()
        for attempt in range(3):
            try:
                req = urllib.request.Request(self.url, data=data, headers=self.headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    out = json.loads(resp.read().decode())
                return out["choices"][0]["message"]["content"] or "{}"
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                if attempt == 2:
                    raise RuntimeError(f"LLM call failed: {e}") from e
        return "{}"

    def decide(self, arm: str, role: str, p: Dict) -> Dict:
        return _extract_json(self.chat(render(arm, role, p)))


# --------------------------------------------------------------------------- #
# Prompts.                                                                      #
# --------------------------------------------------------------------------- #
SYSTEM = (
    "Two agents relay MISSION-LOG records efficiently. A record has four fields "
    "(loc, act, stat, crew), each a short phrase. The SENDER transmits; the "
    "RECEIVER must reconstruct the EXACT phrases. You want to send as FEW tokens "
    "as possible while staying perfectly accurate. You share no memory beyond "
    "what each prompt shows. Reply with COMPACT JSON only."
)


def _vocab_block() -> str:
    return "\n".join(f"  {f}: {VOCAB[f]}" for f in FIELDS)


def _transcript_block(transcript: List[Dict]) -> str:
    if not transcript:
        return "  (nothing sent yet)"
    rows = []
    for e in transcript[-HISTORY:]:
        sent = " ".join(f"{f}={e['wire'].get(f, '?')}" for f in FIELDS)
        was = " ".join(f"{f}={e['record'][f]}" for f in FIELDS)
        rows.append(f"  sent[{sent}] -> was[{was}]")
    return "\n".join(rows)


def _codebook_block(codebook: Dict[str, str]) -> str:
    if not codebook:
        return "  (empty)"
    return "\n".join(f"  {code} = {phrase}" for phrase, code in codebook.items())


def render(arm: str, role: str, p: Dict) -> List[Dict]:
    if arm == "freeform" and role == "speak":
        user = (f"You are the SENDER. Target record:\n"
                + "\n".join(f"  {f}: {p['record'][f]}" for f in FIELDS)
                + f"\n\nShared history (what you sent -> what it really was):\n"
                f"{_transcript_block(p['transcript'])}\n\n"
                "Transmit each field in as FEW tokens as possible so the RECEIVER "
                "(who sees this same history) can recover the exact phrase. You may "
                "abbreviate or reuse shorthand you established earlier.\n"
                'JSON: {"wire": {"loc": "..", "act": "..", "stat": "..", "crew": ".."}}')
    elif arm == "freeform":  # listen
        user = (f"You are the RECEIVER. You received:\n"
                + "\n".join(f"  {f}: {p['wire'].get(f, '?')}" for f in FIELDS)
                + f"\n\nShared history (what was sent -> what it really was):\n"
                f"{_transcript_block(p['transcript'])}\n\n"
                f"Reconstruct the EXACT record. Each field MUST be one of:\n{_vocab_block()}\n"
                'JSON: {"loc": "..", "act": "..", "stat": "..", "crew": ".."}')
    elif arm == "codebook" and role == "speak":
        user = (f"You are the SENDER. Target record:\n"
                + "\n".join(f"  {f}: {p['record'][f]}" for f in FIELDS)
                + f"\n\nShared CODEBOOK (code = phrase) established so far:\n"
                f"{_codebook_block(p['codebook'])}\n\n"
                "For each field: if its phrase already has a code, put that CODE in "
                "the wire (cheap REFER). Otherwise invent a SHORT new code (e.g. a1, "
                "x7) and add it to 'defs' (a DEFINE, which costs the full phrase this "
                "once). Reuse codes consistently.\n"
                'JSON: {"wire": {"loc": "<code>", "act": "<code>", "stat": "<code>", '
                '"crew": "<code>"}, "defs": {"<code>": "<phrase>"}}')
    else:  # codebook listen
        user = (f"You are the RECEIVER. You received codes:\n"
                + "\n".join(f"  {f}: {p['wire'].get(f, '?')}" for f in FIELDS)
                + f"\n\nShared CODEBOOK (code = phrase):\n{_codebook_block(p['codebook'])}\n\n"
                f"Reconstruct the EXACT record. Each field MUST be one of:\n{_vocab_block()}\n"
                'JSON: {"loc": "..", "act": "..", "stat": "..", "crew": ".."}')
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


# --------------------------------------------------------------------------- #
# Offline heuristic backend (verifies the harness + shows the failure mode).    #
# --------------------------------------------------------------------------- #
class MockBackend:
    """Not an LLM. Sender abbreviates to word-initials (freeform) or invents
    sequential codes (codebook); receiver resolves from shared history/codebook.
    Freeform mis-fires on a phrase's FIRST appearance (never seen -> can't
    resolve); codebook is always resolvable -> lossless. Same shape as an LLM
    that compresses well but, without structure, occasionally can't disambiguate."""

    kind = "mock"
    model = "mock"

    def decide(self, arm: str, role: str, p: Dict) -> Dict:
        if arm == "freeform" and role == "speak":
            return {"wire": {f: _initials(p["record"][f]) for f in FIELDS}}
        if arm == "freeform":  # listen
            seen: Dict[str, Dict[str, str]] = {f: {} for f in FIELDS}
            for e in p["transcript"]:
                for f in FIELDS:
                    seen[f][e["wire"].get(f, "")] = e["record"][f]
            return {f: seen[f].get(p["wire"].get(f, ""), "UNKNOWN") for f in FIELDS}
        if arm == "codebook" and role == "speak":
            cb = dict(p["codebook"])           # phrase -> code
            wire, defs = {}, {}
            for f in FIELDS:
                val = p["record"][f]
                if val in cb:
                    wire[f] = cb[val]
                else:
                    code = f"c{len(cb) + len(defs) + 1}"
                    defs[code] = val
                    wire[f] = code
            return {"wire": wire, "defs": defs}
        # codebook listen
        rev = {code: phrase for phrase, code in p["codebook"].items()}
        return {f: rev.get(p["wire"].get(f, ""), "UNKNOWN") for f in FIELDS}


def _initials(phrase: str) -> str:
    return "".join(w[0] for w in phrase.split())


# --------------------------------------------------------------------------- #
# Game loop.                                                                    #
# --------------------------------------------------------------------------- #
def _clean_wire(raw) -> Dict[str, str]:
    raw = raw if isinstance(raw, dict) else {}
    return {f: str(raw.get(f, "?")).strip() for f in FIELDS}


def _canon(field: str, val) -> str:
    v = str(val).strip()
    for phrase in VOCAB[field]:
        if v.lower() == phrase.lower():
            return phrase
    return v   # unmatched -> stays as-is, will count as wrong


def run(backend, arm: str, seed: int, total: int, verbose: bool) -> Dict:
    codebook: Dict[str, str] = {}          # phrase -> code (codebook arm)
    transcript: List[Dict] = []            # revealed (record, wire) pairs (shared)
    tokens_log: List[int] = []
    verbose_log: List[int] = []
    wins = 0

    for r in range(total):
        record = make_record(seed, r)

        sp = backend.decide(arm, "speak", {"record": record, "codebook": codebook,
                                           "transcript": transcript})
        wire = _clean_wire(sp.get("wire"))
        defs = sp.get("defs", {}) if arm == "codebook" else {}
        if not isinstance(defs, dict):
            defs = {}
        for code, phrase in defs.items():
            codebook[str(phrase)] = str(code)   # register new definitions (shared)

        cost = tokens(wire)
        if arm == "codebook":
            cost += sum(len(str(ph).split()) + 1 for ph in defs.values())  # DEFINE cost
        tokens_log.append(cost)
        verbose_log.append(verbose_tokens(record))

        ls = backend.decide(arm, "listen", {"wire": wire, "codebook": codebook,
                                            "transcript": transcript})
        recon = {f: _canon(f, ls.get(f, "")) for f in FIELDS}
        win = recon == record
        wins += int(win)

        if verbose:
            print(f"  [{arm[:4]} r{r:02d}] wire={wire} defs={defs} -> "
                  f"{'OK ' if win else 'ERR'} {cost} tok")

        transcript.append({"record": record, "wire": wire})   # feedback (shared)

    return {"arm": arm, "tokens_log": tokens_log, "verbose_log": verbose_log,
            "wins": wins, "total": total}


def report(results: List[Dict], name: str) -> None:
    print("\n" + "=" * 78)
    print(f"LLM MISSION LOG RELAY  |  backend={name}")
    print("=" * 78)
    print(f"  {'arm':<10} {'accuracy':>10} {'tokens':>10} {'vs verbose':>12} "
          f"{'ratio':>7}  per-round")
    for r in results:
        tl, vl, total = r["tokens_log"], r["verbose_log"], r["total"]
        k = max(1, total // 4)
        first = sum(tl[:k]) / k if tl else 0.0
        last = sum(tl[-k:]) / k if tl else 0.0
        ratio = (sum(vl) / sum(tl)) if sum(tl) else 1.0
        print(f"  {r['arm']:<10} {r['wins']}/{total:<8} {sum(tl):>10} {sum(vl):>12} "
              f"{ratio:>6.2f}x  first{k}avg {first:.1f} -> last{k}avg {last:.1f}")
    print("=" * 78)
    print("  Headline: accuracy under compression. The protocol (codebook) should")
    print("  compress AND stay lossless; freeform tends to compress but slip on")
    print("  accuracy when shorthand gets ambiguous.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", choices=["freeform", "codebook", "both"], default="both")
    ap.add_argument("--total", type=int, default=12)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--model", default=None)
    ap.add_argument("--mock", action="store_true", help="Offline heuristic (no API key).")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    arms = ["freeform", "codebook"] if args.arm == "both" else [args.arm]
    if args.mock:
        backend, name = MockBackend(), "MOCK heuristic (not an LLM)"
    else:
        try:
            backend = LLMBackend(model=args.model)
        except RuntimeError as e:
            raise SystemExit(f"\n{e}\n")
        name = f"{backend.kind}:{backend.model}"

    print(f"LLM Mission Log Relay  |  seed={args.seed}  rounds={args.total}  arms={arms}")
    results = [run(backend, arm, args.seed, args.total, args.verbose) for arm in arms]
    report(results, name)


if __name__ == "__main__":
    main()
