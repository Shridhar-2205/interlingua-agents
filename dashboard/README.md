# Interlingua Dashboard

A single UI that combines two use cases behind a top-level tab switcher, each
named after the job it demonstrates:

1. **Emergent Alignment** (_Can two agents agree on a shared code?_) — Free-Form
   A2A vs ELP-over-A2A. Two agents try to build a shared vocabulary over
   HTTP/JSONRPC; the UI streams the run live via SSE and shows a final alignment
   comparison. (Scenario logic unchanged from `scenario_examples/ui`.)
2. **Bandwidth & Grounding** — the emergent-language walkthrough with two
   sub-views, each with a **Run (stream)** button plus manual scrub/playback:
   - **Token Compression** (_codebook · DEFINE → REFER_) — DEFINE once → REFER
     forever; watch the token-cost curve bend flat, lossless.
   - **Grounding an Opaque Code** (_Theory of Mind_) — the sender speaks an opaque
     code; the receiver must ground it from feedback (`perfield` vs
     `perfield+tom`). Restyled to match the dark-glass look.

Both tabs share the same A2A architecture / agent-card / SendMessage framing and a
live comparison panel.

## Run

```bash
python server.py   # mock mode — fast demo, no agents/LLM required
```

Then open http://127.0.0.1:9500. Switch use cases with the tabs at the top.

Runs in **mock mode**: both tabs stream pre-generated traces over SSE, so the demo
is instant and fully self-contained (no live agents or LLM calls).

Deep-links for the compression demo (screenshots/slides):

```
http://127.0.0.1:9500/?view=compression&round=6
http://127.0.0.1:9500/?view=grounding&arm=perfield+tom&round=12
```

## A2A message anatomy (ELP) — Demo 1

An ELP message is **an A2A `SendMessage` that carries an ELP/L9 envelope inside one
of its parts**. There are two nested skeletons: the outer **A2A transport** and the
inner **ELP payload**. This is what makes the right-hand panel in Demo 1 different
from Free-Form (left), which sends only the plain-text part.

### Outer layer — A2A `SendMessage`

```json
{
  "role": "ROLE_USER",
  "parts": [
    { "text": "alpha proposes ≈ for river" },
    { "data": { /* ELP envelope ↓ */ },
      "mediaType": "application/vnd.elp+json" }
  ],
  "extensions": ["https://outshift.io/a2a-ext/emergence/v1"]
}
```

- A2A messages are a list of **parts**; a part is either `text` or structured `data`.
- Part 1 is a human-readable summary (any A2A agent can read *something*).
- Part 2 is the `data` part, self-described via `mediaType: application/vnd.elp+json`.
- `extensions` advertises the governing A2A extension (also declared on each Agent
  Card), so the receiver knows how to interpret the data part.

### Inner layer — the ELP / L9 envelope (`l9/l9_models.py`)

```json
{
  "protocol": "ELP",
  "version": "0.1",
  "participants": {                          // WHO
    "actors": [
      { "id": "alpha", "role": "sender" },
      { "id": "beta",  "role": "receiver" }
    ],
    "groups": null
  },
  "message": {                               // episode linkage (a DAG)
    "id": "a3f8c901e2d4",
    "parents": ["b7c2e4f0a19c"],             // the message this replies to
    "episode": "urn:ioc:emerge:river:run1"   // groups the whole conversation
  },
  "context": { "topic": "concept:river" },   // WHAT it's about
  "type": "emergence",                       // which schema `data` follows
  "data": { /* emergence payload ↓ */ }
}
```

### Innermost — the `emergence` payload (`l9/l9_envelope.py`)

```json
{
  "round": 5,
  "speaker": "alpha",
  "referent": "river",              // concept being proposed
  "proposal": "≈",                  // symbol offered for it
  "decision": "propose",           // init | propose | converged
  "lexicons": {                     // full {agent: {concept: symbol}} state
    "alpha": { "river": "≈", "sea": "●", "tree": "⊚" },
    "beta":  { "river": "≈", "sea": "●", "tree": "⊚" }
  },
  "utterance": {                    // the signaling act
    "text": "alpha proposes ≈ for river",
    "evidence": ["river"],
    "addresses_evidence": ["river"]
  },
  "grounding": {                    // was it mutually confirmed?
    "contingency_verified": true, "contingency_score": 1.0, "repair_reason": null
  },
  "belief": {                       // confidence on the mapping
    "prior": 0.5, "posterior": 1.0, "revision_cause": "structured"
  },
  "tom": {                          // Theory of Mind — sender's MODEL of the peer
    "beta": { "sea": "●", "tree": "⊚", "apple": "△", "river": "?" }
  },
  "history": [                      // GAR/SCR event log
    { "referent": "sea",  "symbol": "●", "accepted": true, "grounded": true, "speaker": "beta" },
    { "referent": "tree", "symbol": "⊚", "accepted": true, "grounded": true, "speaker": "alpha" }
  ]
}
```

### Why each field matters (the ELP value-add)

| Field | What it buys you |
|---|---|
| `participants`, `message.episode`, `parents` | Every message is **addressable and linkable** — reconstruct the whole conversation DAG, not just the last turn. |
| `context.topic` | The referent is **named explicitly**, so grounding is unambiguous. |
| `lexicons` | Agents stay **stateless** — full shared state rides on the wire. |
| `grounding` | Alignment is **verified, not assumed** — and measurable. |
| `belief` | Each mapping carries a **confidence**, updated per turn. |
| `tom` | Sender models **what the peer knows** (`river: "?"` = not yet grounded) → proposes the most useful next symbol. |
| `history` | Audit log yielding metrics like **GAR** (grounded-acceptance rate) and **SCR**. |

Nesting summary: **A2A part → ELP wrapper → emergence payload**. Free-Form sends
just the top text line; ELP sends the entire structured, measurable envelope beside
it — which is why it converges and Free-Form doesn't.

## Files

| File | Role |
|---|---|
| `server.py` | Starlette server — SSE scenario runs + serves the static UI |
| `static/index.html` | combined dashboard (scenario UI + restyled compression demo) |
| `static/demo_data.js` | compression scenario data (`window.DEMO_DATA`) |
| `static/firstcontact_data.js` | grounding trace data (`window.FC_DATA`) |

## Regenerate the compression data

The compression/grounding data is generated in `../compression/demo`. Regenerate
there, then copy the two `*_data.js` files into `dashboard/static/`:

```bash
cd ../compression/demo
python export_demo.py --seed 1 --total 20
python export_firstcontact.py
cp demo_data.js firstcontact_data.js ../../dashboard/static/
```
