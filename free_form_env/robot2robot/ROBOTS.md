# Mars Robot Rendezvous — Beep Communication Experiment

Two Mars robots need to meet at a dig site. One has the map, one has the drill.
Their radio is damaged — they can only send beep sequences. No words.

This experiment runs in two modes: **dumb** and **smart**, to show how much
communication strategy matters when the signal channel is severely constrained.

---

## The Scenario

```
        [crater-7]     [ridge-alpha]    [lava-flat]
        [north-basin]  [dust-shelf]     [iron-peak]
        [sunken-plain] [twin-rocks]     [shadow-canyon]
                       [ice-pocket]
```

- **MapBot** knows which of these 10 landmarks is the dig site (picked randomly at startup)
- **DrillBot** can see all 10 landmarks but has no idea which one to go to
- They can only exchange beep sequences: dots (•) and dashes (—)
- Goal: DrillBot reaches the correct landmark

---

## Two Pairs

### Dumb Pair (ports 9205 / 9206)

**MapBot** — improvises a different beep encoding every turn. No fixed scheme.
Sometimes repeats the same pattern, sometimes varies it. Occasionally confirms
the wrong answer by accident.

**DrillBot** — guesses randomly. No memory of previous beeps. Gets excited and
rushes to the wrong place. Forgets what patterns meant last turn.

**Result:** Stumbles to the answer in 4–25+ exchanges. Sometimes fails entirely.

---

### Smart Pair (ports 9207 / 9208)

**Smart MapBot** — uses a consistent encoding: number of dots = landmark index.
- `crater-7` is #1 → transmits `•`
- `iron-peak` is #6 → transmits `• • • • • •`
- Wrong guess → `— • • • • • •` (dash = no, then repeat the count)
- Correct guess → `•` (single dot = yes)

**Smart DrillBot** — counts dots, builds a hypothesis, uses process of elimination.
Tracks which patterns got a yes/no and narrows down the answer systematically.

**Result:** Converges in 1–2 exchanges, reliably.

---

## What This Demonstrates

| | Dumb | Smart |
|---|---|---|
| Encoding | Random, inconsistent | Fixed dot-count scheme |
| Decoding | Random guessing | Pattern tracking + elimination |
| Temperature | 1.0 (chaotic) | 0.2 (precise) |
| Exchanges to converge | 4–25+ | 1–2 |
| Reliability | Sometimes fails | Reliable |

**The lesson:** same broken radio channel, same 10 landmarks — but a consistent
encoding strategy and systematic decoding collapses the problem from dozens of
exchanges to one or two.

---

## Setup

```bash
pip install a2a-sdk httpx uvicorn starlette
cp .env.sample .env
# Edit .env with your real LLM_API_KEY
```

---

## Running

### Dumb Pair

```bash
# Terminal 1 — DrillBot (responder)
export $(grep -v '^#' .env | xargs) && python drillbot_agent.py

# Terminal 2 — MapBot (driver, prints the secret dig site on startup)
export $(grep -v '^#' .env | xargs) && python mapbot_agent.py

# Terminal 3 — trigger
curl -s -X POST http://localhost:9205/ \
  -H "Content-Type: application/json" \
  -H "A2A-Version: 1.0" \
  -d '{"jsonrpc":"2.0","id":"1","method":"SendMessage","params":{"message":{"messageId":"m1","role":"ROLE_USER","parts":[{"text":"begin"}]}}}'
```

### Smart Pair

```bash
# Terminal 1 — Smart DrillBot (responder)
export $(grep -v '^#' .env | xargs) && python smart_drillbot_agent.py

# Terminal 2 — Smart MapBot (driver, prints the secret dig site on startup)
export $(grep -v '^#' .env | xargs) && python smart_mapbot_agent.py

# Terminal 3 — trigger
curl -s -X POST http://localhost:9207/ \
  -H "Content-Type: application/json" \
  -H "A2A-Version: 1.0" \
  -d '{"jsonrpc":"2.0","id":"1","method":"SendMessage","params":{"message":{"messageId":"s1","role":"ROLE_USER","parts":[{"text":"begin"}]}}}'
```

---

## Sample Output

### Dumb Pair
```
════════════════════════════════════════════════════════════
  🤖 DUMB ROBOT PAIR  |  Target: shadow-canyon
════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────
 [0] MAPBOT  →  signal
────────────────────────────────────────────────────────────
  • — • •

────────────────────────────────────────────────────────────
 [1] DRILLBOT  →  guess
────────────────────────────────────────────────────────────
  ?? — crater-7

────────────────────────────────────────────────────────────
 [1] MAPBOT  →  response
────────────────────────────────────────────────────────────
  — •• —

  ... (many more exchanges) ...

════════════════════════════════════════════════════════════
  ✅ RENDEZVOUS ACHIEVED after 11 exchange(s)
════════════════════════════════════════════════════════════
```

### Smart Pair
```
════════════════════════════════════════════════════════════
  🤖 SMART ROBOT PAIR  |  Target: shadow-canyon
════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────
 [0] SMART MAPBOT  →  signal
────────────────────────────────────────────────────────────
  • • • • • • • • •

────────────────────────────────────────────────────────────
 [1] SMART DRILLBOT  →  guess
────────────────────────────────────────────────────────────
  ANALYSIS: 9 dots — landmark #9
  HYPOTHESIS: shadow-canyon is index 9 in the list
  GUESS: shadow-canyon
  CONFIRM: •

────────────────────────────────────────────────────────────
 [1] SMART MAPBOT  →  response
────────────────────────────────────────────────────────────
  •

════════════════════════════════════════════════════════════
  ✅ RENDEZVOUS ACHIEVED after 1 exchange(s)
════════════════════════════════════════════════════════════
```

---

## Architecture

```
┌─────────────────────┐      A2A/HTTP (beeps only)     ┌──────────────────────┐
│  MapBot / SmartMapBot│◄─────────────────────────────►│ DrillBot/SmartDrillBot│
│  :9205 / :9207       │   text + data (history)        │  :9206 / :9208        │
│                      │                                │                       │
│  Knows dig site      │                                │  Has the drill        │
│  Sends beep codes    │                                │  Decodes beeps        │
│  Confirms guesses    │                                │  Proposes landmarks   │
│  Drives the loop     │                                │  Just responds        │
└─────────────────────┘                                └──────────────────────┘
         ▲
         │ trigger (curl)
         │
    External caller
```

Dig site is chosen randomly at MapBot startup — DrillBot never sees it directly.
Both agents are fully stateless; history travels in the A2A data part each turn.
