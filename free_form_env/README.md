# Free Form Environment — Dumb Baseline, Theory of Mind, and the Structured Fix

Two A2A agents (Human + Alien) in a shared environment of 40 physical objects,
building a shared vocabulary. Three variants, same environment, same starting
point — each one a fix for a failure in the last:

| Variant | Files | Intelligence | Wire format | Result |
|---|---|---|---|---|
| **Dumb baseline** | `human_agent.py` + `alien_agent.py` | none — reactive, confused, inconsistent | free text | ~30 exchanges, unreliable (sometimes never converges) |
| **Depth A** | `human_agent_smart.py` + `alien_agent.py` | `l9.Mind` (Theory-of-Mind advisor) on the human only | free text | **FAILED** — 0/10 confirmed in 39 exchanges: the two LLMs derailed into a mirror loop |
| **Depth B** | `human_agent_structured.py` + `alien_agent_structured.py` | none needed | structured EIP `{object→word}` | **100% in 12 rounds**, seconds, GAR 1.0 SCR 0.0, deterministic |

Depth A shows that giving *one* agent a Theory-of-Mind advisor over free text
isn't enough — two chatty LLMs can still spiral into copying each other's
meta-commentary instead of naming objects (the "conversational loop" failure
mode). Depth B removes the failure mode by construction: proposals are
structured `{object, word}` pairs riding in an EIP DataPart, so there's no
prose channel left to derail in.

## How the dumb baseline works

- **Human Agent** (port 9201): A confused English-speaking creature. Gets distracted,
  forgets previous exchanges, points at random things, sometimes lies down and stares
  at the sky. No strategy — just reacts.
- **Alien Agent** (port 9202): A confused creature making invented sounds. Inconsistent
  with its own words (vrk vs vrrk vs vruk). Gets distracted, ignores what the human
  does, sometimes points at the wrong thing entirely.

The human is triggered externally, then drives a ping-pong loop with the alien via
A2A. The loop ends when the human stumbles into declaring 10 mappings — or gives up.

## The shared environment

40 fixed objects both agents can see:

```
fire, water, rock, tree, sun, moon, sky, cloud, rain, wind,
flower, fruit, seed, leaf, root, fish, bird, snake, insect, egg,
hand, eye, mouth, foot, head, cave, river, mountain, sand, mud,
bone, stick, shell, feather, fur, smoke, ice, lightning, shadow, star
```

The human knows them by English names. The alien perceives them by description
(e.g. "the hot bright dancing thing" for fire) and invents its own words.

## Results

### Dumb baseline

| Run | Exchanges | Outcome |
|-----|-----------|---------|
| 1 | 20 | 10 mappings (slow, confused convergence) |
| 2 | 30 | Failed — agent had existential crisis, gave up |
| 3 | 36 | 10 mappings (reliable but very slow) |

**Average: ~30 exchanges, slow and unreliable.**

The agents wander aimlessly, get distracted by mud, lie down under trees, stare at
clouds, and use words inconsistently. When they do converge, it takes 3-4x longer
than strategic agents. Sometimes they never converge at all.

Sample behavior:

```
HUMAN: *looks around, blinking* ... *picks up stick* ... Stick?
ALIEN: *blinks* ... *stares at creature waving stick*
HUMAN: *lies down in mud* ... *stares at cloud*
ALIEN: *sits down too* ... Nuu...
HUMAN: *yawns* ... *falls asleep*
```

### Depth A — Mind advisor, still free text: derailed

39 exchanges, 0/10 confirmed. The human (with `l9.Mind` tracking the alien's
vocabulary) and the unchanged dumb alien fell into a mirror loop instead of
naming objects:

```
ALIEN: *STOPS COMPLETELY*
HUMAN: *STOPS and realizes we're in an impossible loop*
ALIEN: *REALIZES WE JUST WROTE IDENTICAL RESPONSES AGAIN*
HUMAN: *Sees them sit in silence*
```

A one-sided advisor can't rescue a conversation once both sides start copying
each other's stage directions instead of pointing at objects — Theory of Mind
over free text doesn't remove the derailment attractor, it just gives one
participant a better (but still ignored) strategy.

### Depth B — structured EIP: fixed

12 rounds, 100% alignment, GAR 1.0, SCR 0.0, in seconds, zero LLM calls. Every
message is `{"referent": object, "proposal": word}` — there's no prose to
spiral in, so the failure mode from depth A cannot occur. The shared vocabulary
that emerges is a genuine mix of both agents' words (e.g. `fire→fire`,
`water→ripi`, `moon→rupo`), not one side dictating to the other.

## How state travels (A2A data part)

Conversation history is passed as a **JSON data part** in every A2A message.
Both agents are fully stateless — they reconstruct conversation history from the
data part on each incoming request.

```python
Message.parts = [
    Part(text="*blinks* ... vrk?"),                             # the utterance
    Part(data=Value(string_value=json.dumps(history)),          # full LLM history
         media_type="application/json"),
]
```

## Setup

```bash
pip install a2a-sdk httpx uvicorn starlette
```

```bash
cp .env.sample .env
# Edit .env with your real LLM_API_KEY
```

## Running — dumb baseline

Terminal 1 — Alien agent:

```bash
cd free_form_env
export $(grep -v '^#' .env | xargs)
python alien_agent.py
```

Terminal 2 — Human agent:

```bash
cd free_form_env
export $(grep -v '^#' .env | xargs)
python human_agent.py
```

Terminal 3 — trigger. `message_id` is snake_case and the `A2A-Version` header
is required — without it you get `Method not found` / `VERSION_NOT_SUPPORTED`:

```bash
curl -s -X POST http://localhost:9201/ \
  -H "Content-Type: application/json" -H "A2A-Version: 1.0" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "SendMessage",
    "params": {
      "message": {
        "message_id": "trigger-001",
        "role": "ROLE_USER",
        "parts": [{"text": "begin"}]
      }
    }
  }'
```

## Running — Depth A (Mind advisor)

Run `human_agent_smart.py` **instead of** `human_agent.py` (same port 9201),
against the unchanged `alien_agent.py`. Same trigger as above. Expect it to
derail (see Results) — kept as the honest baseline that motivates Depth B.

```bash
python alien_agent.py &        # unchanged
python human_agent_smart.py    # l9.Mind advisor wired in
```

## Running — Depth B (structured EIP)

Deterministic — no LLM, no `.env` needed:

```bash
python alien_agent_structured.py &   # :9202
python human_agent_structured.py &   # :9201
python trigger_structured.py         # prints the converged result
```

## Architecture — dumb baseline

```
┌─────────────────┐         A2A/HTTP          ┌─────────────────┐
│  Human Agent    │◄────────────────────────►  │  Alien Agent    │
│  :9201          │  text + data (history)     │  :9202          │
│                 │                            │                 │
│  Dumb creature  │                            │  Dumb creature  │
│  English sounds │                            │  Alien sounds   │
│  No strategy    │                            │  Inconsistent   │
│  Easily confused│                            │  Easily confused│
│  Stateless      │                            │  Stateless      │
└─────────────────┘                            └─────────────────┘
        ▲
        │ trigger (curl / A2A client)
        │
   External caller
```

No theory of mind. No belief tracking. No grounding. Just two confused creatures
bumbling around in a shared environment, occasionally making sounds at each other.

Depth A swaps in `l9.Mind` on the human side only (same architecture, human
is no longer purely reactive — see `../l9/README.md` for how `Mind` works).
Depth B replaces the free-text `Message.parts` data with the EIP envelope from
`../l9/l9_envelope.py` — see that README for the wire format.
