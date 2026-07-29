# Free Form Environment — Dumb Baseline

Two A2A agents (Human + Alien) in a shared environment of 40 physical objects.
They are intentionally **dumb** — confused, easily distracted, inconsistent, and
unable to form hypotheses or track patterns. They communicate over HTTP using the
[A2A protocol](https://github.com/google/A2A) and fumble toward shared vocabulary
through blind repetition.

This serves as the **baseline** to prove that smarter agents (with Theory of Mind,
belief tracking, and grounding) converge significantly faster.

## How it works

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

| Run | Exchanges | Outcome |
|-----|-----------|---------|
| 1 | 20 | 10 mappings (slow, confused convergence) |
| 2 | 30 | Failed — agent had existential crisis, gave up |
| 3 | 36 | 10 mappings (reliable but very slow) |

**Average: ~30 exchanges, slow and unreliable.**

The agents wander aimlessly, get distracted by mud, lie down under trees, stare at
clouds, and use words inconsistently. When they do converge, it takes 3-4x longer
than strategic agents. Sometimes they never converge at all.

### Sample behavior

```
HUMAN: *looks around, blinking* ... *picks up stick* ... Stick?
ALIEN: *blinks* ... *stares at creature waving stick*
HUMAN: *lies down in mud* ... *stares at cloud*
ALIEN: *sits down too* ... Nuu...
HUMAN: *yawns* ... *falls asleep*
```

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

## Running

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

Terminal 3 — trigger:

```bash
curl -s -X POST http://localhost:9201/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "trigger-001",
        "role": "ROLE_USER",
        "parts": [{"text": "begin"}]
      }
    }
  }'
```

## Architecture

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
