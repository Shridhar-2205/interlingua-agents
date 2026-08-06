# Scenario Examples — Free-Form vs ELP Comparison

Two implementations of the same task (two agents building a shared vocabulary in
a shared environment), demonstrating why structured ELP protocol with Theory of
Mind converges reliably while unstructured LLM-to-LLM communication fails.

## Results (30-round cap)

| Metric | Free-Form (LLM only) | ELP (ToM + Signaling + LLM) |
|--------|---------------------|----------------------------|
| **Rounds** | 30 (hit cap) | 30 (hit cap) |
| **Alignment** | 0% — never converged | **60%** (6/10 concepts) |
| **Confirmed mappings** | 0 | 6 genuinely grounded |
| **GAR (Genuine Agreement)** | N/A (no measurement) | **1.0** (100% genuine) |
| **SCR (Social Compliance)** | N/A | **0.0** (zero mimicry) |
| **W (Provenance Weight)** | N/A | **1.0** |
| **Failure mode** | Spiral into freeze/mirror loop | Only fails on deliberately unshareable concepts |

The 4 concepts that didn't align in ELP (fire, moon, star, stone) are
deliberately designed in `world.py` with zero perceptual overlap between visual
and physical agents — the protocol correctly refuses to fake agreement on those.

## The Scenarios

| Scenario | Directory | Intelligence | Wire Format |
|----------|-----------|--------------|-------------|
| **Free-form** | `free_form/` | None — two plain LLM agents | Free text A2A |
| **ELP** | `elp/` | ToM + signaling from `l9/` | Structured ELP envelope |

## Free-Form Scenario

Two agents communicate via plain text A2A messages with no structure, no Theory
of Mind, no grounding protocol. Alpha speaks English and drives the loop; Beta
invents sounds on the fly with no fixed vocabulary (no cheat sheet).

**What happens**: Beta is inconsistent (uses different sounds for the same object
each turn). Alpha notices but can't establish any stable mappings. Both agents
eventually spiral into a "freeze loop" — each waiting for the other to act,
producing no vocabulary at all. After 30 exchanges: zero confirmed mappings.

Sample run:
```
ALPHA: *points at the sun*
BETA:  *squints at bright circle above, looks confused*
ALPHA: *nods enthusiastically, points at the sun again*
BETA:  *stops*  Plif!
ALPHA: *frowns — first "Zraa" now "Plif" for the same object*
...
BETA:  *freezes*
ALPHA: *realizes this creature is stuck in a fear loop*
BETA:  *freezes*
ALPHA: *stops completely*
  [30/30] DONE (stopped at cap 30) — 0 confirmed mappings
```

### Running

```bash
cd scenario_examples/free_form
cp .env.sample .env   # set your LLM_API_KEY
export $(grep -v '^#' .env | xargs)

python agent_beta.py &    # port 9302
python agent_alpha.py &   # port 9301

# trigger via curl:
curl -s -X POST http://localhost:9301/ \
  -H "Content-Type: application/json" -H "A2A-Version: 1.0" \
  -d '{
    "jsonrpc": "2.0", "id": "1", "method": "SendMessage",
    "params": {"message": {"message_id": "trigger-001", "role": "ROLE_USER", "parts": [{"text": "begin"}]}}
  }'
```

## ELP Scenario

Two agents import `signaling`, `intelligence`, `world`, and `lens` from the
`l9/` package. They communicate via A2A messages carrying a structured ELP
envelope (`application/vnd.elp+json`) with:

- **Lexicons**: full state of each agent's vocabulary
- **Proposals**: `{referent, symbol}` — no prose to derail in
- **Grounding**: CIP contingency scoring (feature overlap)
- **Theory of Mind**: predict what the peer will accept
- **History**: GAR/SCR event log for measuring genuine agreement vs mimicry

Each agent uses `intelligence.coin()` (LLM-enhanced symbol justification) and
`intelligence.ground()` (LLM-enhanced grounding) before sending an ELP message.
When no LLM credentials are set, both fall back to deterministic ToM from
`signaling.py`.

Sample run:
```
[alpha] alpha proposes ∆ for river -> beta
[beta]  beta proposes ⊚ for sea -> alpha
[alpha] alpha proposes ◆ for dance -> beta
...
[alpha] done | round 30 | align 60% | GAR 1.0 SCR 0.0 W 1.0
  alpha : {river: ∆, sea: ⊚, tree: ○, apple: ⟐, dance: ◆, fruit: ◐, ...}
  beta  : {river: ∆, sea: ⊚, tree: ○, apple: ⟐, dance: ◆, fruit: ◐, ...}
```

### Running

```bash
cd scenario_examples/elp
cp .env.sample .env   # optional — works without LLM creds (deterministic fallback)
export $(grep -v '^#' .env | xargs)

python agent_beta.py &     # port 9402
python agent_alpha.py &    # port 9401
python trigger.py          # prints converged result with metrics
```

## Why ELP Wins

| Problem | Free-Form | ELP Solution |
|---------|-----------|--------------|
| Inconsistent naming | Beta invents new sound each turn | Lexicons travel in every message — state is explicit |
| No grounding | Alpha guesses if mapping is correct | CIP contingency check: feature overlap must exceed threshold |
| Spiral/freeze loops | LLMs copy each other's stage directions | Proposals are structured `{referent, symbol}` — no prose channel to derail |
| No measurement | "Did it work?" — unclear | GAR/SCR/W quantify exactly how genuine the agreement is |
| Fake convergence | Agent can self-declare success without verification | Only counts agreements that pass grounding |
| Unshareable concepts | Would claim false mapping | Correctly refuses — SCR stays at 0.0 |

## Architecture

```
Free-Form:
┌──────────────────┐       A2A/HTTP (free text)      ┌──────────────────┐
│  Alpha :9301     │◄──────────────────────────────►  │  Beta :9302      │
│  LLM → English   │   Part(text) + Part(data/json)   │  LLM → Alien     │
│  No intelligence │                                  │  No intelligence │
│  No grounding    │                                  │  Inconsistent    │
└──────────────────┘                                  └──────────────────┘

ELP:
┌──────────────────┐     A2A/HTTP (ELP envelope)     ┌──────────────────┐
│  Alpha :9401     │◄──────────────────────────────►  │  Beta :9402      │
│  ToM + signaling │   Part(data/vnd.elp+json)        │  ToM + signaling │
│  intelligence.py │                                  │  intelligence.py │
│  lens: VISUAL    │                                  │  lens: PHYSICAL  │
└──────────────────┘                                  └──────────────────┘
        │                                                      │
        └───────── both import from ../../l9/ ─────────────────┘
                   (signaling, intelligence, world, lens, l9_envelope)
```

## Dependencies

```bash
pip install a2a-sdk httpx uvicorn starlette litellm
```

The ELP scenario also needs `pydantic` (transitive via `a2a-sdk`).
