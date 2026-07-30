"""Hybrid intelligence — LLM at the two ToM decision points, deterministic fallback.

Two decisions get the LLM (via litellm, using your creds); if no creds / on any
error, they fall back to signaling.py's deterministic ToM so the demo always runs:

  coin(...)   SPEAKER ToM  — choose a symbol for a concept and JUSTIFY it with
                            evidence (features), reasoning about what the peer,
                            given its perception, will understand.
  ground(...) LISTENER ToM — infer which features the incoming symbol addresses,
                            then score grounding (CIP) against the speaker's evidence.

Belief lives in the payload; this module only produces the numbers/text that go there.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import signaling
from lens import Lens


def _load_env(path: Path) -> None:
    """Minimal .env loader (no dep). Values already in the environment win."""
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env(Path(__file__).with_name(".env"))   # l9/.env (gitignored)

_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")


def available() -> bool:
    return bool(os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
                or os.environ.get("AZURE_OPENAI_API_KEY"))


def _extract_json(text: str) -> dict:
    """Parse a JSON object, tolerating ```json ... ``` fences and surrounding prose."""
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
        return json.loads(t[i:j + 1]) if i != -1 and j > i else {}


def _llm(system: str, user: str) -> Optional[dict]:
    """Call the LLM, expect a JSON object back. None on any failure → caller falls back."""
    try:
        import litellm
        base_url = (os.environ.get("LLM_API_BASE") or os.environ.get("LLM_BASE_URL")
                    or os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE"))
        kw: dict = {
            "model": _MODEL,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": 0.4,
        }
        api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if api_key:
            kw["api_key"] = api_key
        if base_url:
            kw["base_url"] = base_url
        resp = litellm.completion(**kw)
        return _extract_json(resp.choices[0].message.content or "{}")
    except Exception as exc:  # noqa: BLE001
        print(f"  [LLM] fallback ({exc})")
        return None


# ── SPEAKER ToM: coin + justify ────────────────────────────────────────────────

def coin(concept: str, lens: Lens, my_lex: dict, peer_model: dict,
         history: list[dict]) -> tuple[str, str, list[str]]:
    """Return (symbol, rationale, evidence). Symbol via deterministic ToM;
    rationale + evidence enriched by the LLM when available."""
    # Symbol FOR this concept: reuse our own mapping if we have one, else coin a
    # fresh symbol avoiding those already used by us and (ToM) the peer. (Do NOT
    # use propose_with_tom here — that picks *which* concept to discuss, not a
    # symbol for a given one; using it made prior formation reuse one symbol.)
    symbol = my_lex.get(concept) or signaling.coin_smart(my_lex, peer_model, history)
    evidence = lens.perceived_evidence(concept)

    if available():
        out = _llm(
            system=("You choose a symbol's justification in an emergent-language game. "
                    "You perceive the world through these features only. Output JSON "
                    '{"rationale": str, "evidence": [feature,...]} using ONLY given features.'),
            user=json.dumps({
                "concept": concept, "symbol": symbol,
                "my_perceived_features": evidence,
                "my_model_of_peer_lexicon": peer_model,
            }),
        )
        if out:
            evidence = [f for f in out.get("evidence", evidence) if f in evidence] or evidence
            return symbol, out.get("rationale", ""), evidence
    return symbol, f"{symbol} for {concept} (features: {', '.join(evidence)})", evidence


# ── LISTENER ToM: interpret + ground ───────────────────────────────────────────

def ground(concept: str, symbol: str, speaker_evidence: list[str], lens: Lens,
           my_lex: dict, history: list[dict]) -> tuple[list[str], float, float]:
    """Return (addresses_evidence, posterior, score). Listener infers which
    features the symbol addresses, then CIP-scores against the speaker's evidence.
    `score` is objective; the caller decides adopt/reject from its own policy."""
    my_view = lens.perceived_evidence(concept)
    addresses = [f for f in speaker_evidence if f in my_view]  # deterministic default

    if available():
        out = _llm(
            system=("You are the listener in an emergent-language game. Given a symbol a peer "
                    "proposed for a concept and the features THEY justified it with, decide which "
                    "of YOUR perceived features it addresses. Output JSON "
                    '{"addresses_evidence": [feature,...]} using only features you perceive.'),
            user=json.dumps({
                "concept": concept, "symbol": symbol,
                "speaker_evidence": speaker_evidence,
                "my_perceived_features": my_view,
            }),
        )
        if out:
            addresses = [f for f in out.get("addresses_evidence", addresses) if f in my_view] or addresses

    score = signaling.contingency_score(addresses, speaker_evidence)
    posterior = round(min(1.0, 0.3 + 0.7 * score), 4)
    return addresses, posterior, score
