# Mars Robot Rendezvous — Beep Communication Experiment

Two Mars robots need to meet at a dig site. One has the map, one has the drill.
Their radio is damaged — they can only send beep sequences. No words.

This experiment runs in **two modes** — smart and emergent — to show
how communication strategy and protocol invention affect convergence speed.

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

### Emergent Pair (ports 9209 / 9210)

Neither robot is given an encoding scheme or confirmation signals. They only know
they can use `•` and `—`. They must invent **both** through interaction:

1. What sequence points at which landmark?
2. What signal means "yes, correct" vs "no, wrong one"?

**Emergent MapBot** — knows the dig site. Decides its own encoding on the fly.
Must be consistent enough for DrillBot to learn it. Adapts if DrillBot seems lost.
Reports the protocol it invented when done.

**Emergent DrillBot** — watches for patterns across turns. Builds hypotheses.
Uses what it observes to narrow down the answer. No rules given — pure inference.

**Result:** Converges in 5–15 exchanges. The protocol that emerges is different
every run — sometimes dot-count, sometimes position-based, sometimes repetition.
The turn count and emergent protocol are printed at the end.

---

## What Each Pair Demonstrates

| | Smart | Emergent |
|---|---|---|
| Encoding | Fixed dot-count | Invented during exchange |
| Confirmation | Single • = yes, — = no | Also invented during exchange |
| Decoding | Count dots, index lookup | Pattern inference |
| Temperature | 0.2 (precise) | 0.8 (creative) |
| Exchanges to converge | 1–2 | 5–15 |
| Protocol source | Pre-designed | Emergent |
| Reliability | Reliable | Variable |

**The lesson:**
- Smart → pre-designed protocol, snaps to answer immediately
- Emergent → neither robot told the rules, they invent them — the interesting contrast

---

## Setup

```bash
pip install a2a-sdk httpx uvicorn starlette
cp .env.sample .env
# Edit .env with your real LLM_API_KEY
```

---

## Running

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

### Emergent Pair

```bash
# Terminal 1 — Emergent DrillBot (responder)
export $(grep -v '^#' .env | xargs) && python emergent_drillbot_agent.py

# Terminal 2 — Emergent MapBot (driver, prints the secret dig site on startup)
export $(grep -v '^#' .env | xargs) && python emergent_mapbot_agent.py

# Terminal 3 — trigger
curl -s -X POST http://localhost:9209/ \
  -H "Content-Type: application/json" \
  -H "A2A-Version: 1.0" \
  -d '{"jsonrpc":"2.0","id":"1","method":"SendMessage","params":{"message":{"messageId":"e1","role":"ROLE_USER","parts":[{"text":"begin"}]}}}'
```

---

## Sample Output

### Smart Pair
```
════════════════════════════════════════════════════════════
  🤖 SMART ROBOT PAIR  |  Target: shadow-canyon
════════════════════════════════════════════════════════════

 [0] SMART MAPBOT  →  signal
────────────────────────────────────────────────────────────
  • • • • • • • • •

 [1] SMART DRILLBOT  →  guess
────────────────────────────────────────────────────────────
  ANALYSIS: 9 dots — landmark #9
  HYPOTHESIS: shadow-canyon is index 9 in the list
  GUESS: shadow-canyon
  CONFIRM: •

════════════════════════════════════════════════════════════
  ✅ RENDEZVOUS ACHIEVED after 1 exchange(s)
════════════════════════════════════════════════════════════
```

### Emergent Pair
```
════════════════════════════════════════════════════════════
  🛸 EMERGENT ROBOT PAIR  |  Target: north-basin (#4)
  No protocol agreed. They must invent one.
════════════════════════════════════════════════════════════

 [0] EMERGENT MAPBOT  →  signal
────────────────────────────────────────────────────────────
  • • — •

  ⏱  Turn 0 — protocol not yet established

 [1] EMERGENT DRILLBOT  →  response
────────────────────────────────────────────────────────────
  — — •

  ... (several more exchanges while they negotiate) ...

  ⏱  Turn 7 — converged!

════════════════════════════════════════════════════════════
  ✅ RENDEZVOUS ACHIEVED
  Turns to learn protocol : 7
  Total signals exchanged : 14
  Emergent protocol       : 2 dots then dash = landmark #4, single dot = confirm
════════════════════════════════════════════════════════════
```

---

## Architecture

```
┌──────────────────────────┐   A2A/HTTP (beeps only)   ┌──────────────────────────┐
│  SmartMapBot     :9207   │◄─────────────────────────►│  SmartDrillBot   :9208   │
│  EmergentMapBot  :9209   │   text + data (history)   │  EmergentDrillBot :9210  │
│                          │                           │                          │
│  Knows dig site          │                           │  Has the drill           │
│  Sends beep codes        │                           │  Decodes beeps           │
│  Confirms guesses        │                           │  Proposes landmarks      │
│  Drives the loop         │                           │  Just responds           │
└──────────────────────────┘                           └──────────────────────────┘
           ▲
           │ trigger (curl)
           │
      External caller
```

Dig site is chosen randomly at MapBot startup — DrillBot never sees it directly.
All agents are fully stateless; history travels in the A2A data part each turn.

The emergent pair also POST live events to the UI server (`/api/robot-event`)
so the Mars Robots tab at `http://127.0.0.1:8000` shows the exchange in real time.