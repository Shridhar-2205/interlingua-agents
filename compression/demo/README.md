# Interlingua — Emergent Language Demo (UI)

A self-contained, no-build browser demo with two views:

- **Compression (codebook)** — Grace relays mission logs to Rocky. A thin protocol
  (DEFINE a code once → REFER to it forever) shrinks each message. Deterministic and
  lossless: watch the *emerged language* (codebook) fill in and the token cost curve
  bend flat. Data from the rule-based simulator (`../compress.py`).
- **Grounding (Theory of Mind)** — the sender speaks an **opaque** code (meaning never
  transmitted); Rocky must **ground** it from feedback. Compares a plain receiver vs
  one with an **l9-style Theory-of-Mind** advisor that carries an explicit model of the
  sender's code. Real GPT-4o run: `perfield` never grounds (480 tok, unreliable);
  `perfield+tom` grounds by round 9, drops the feedback channel, rides the bare wire
  (280 tok, reliable). Data from `../llm_firstcontact.py` traces.

## Run

Just open `index.html` in a browser — no server, no build:

```bash
open index.html          # macOS
```

Controls: play/pause, step, scrub the round slider. In the Grounding view, toggle
`perfield` vs `perfield+tom` to show the contrast. Deep-link for slides/screenshots:

```
index.html?view=compression&round=6
index.html?view=grounding&arm=perfield+tom&round=12
```

## Regenerate the data

The UI reads two generated files (`window.DEMO_DATA`, `window.FC_DATA`):

```bash
# Compression data (deterministic; tweak seed/rounds freely)
python export_demo.py --seed 1 --total 20

# Grounding data — first run a trace, then export from it:
cd ..
python llm_firstcontact.py --arm perfield --tom compare --total 30 --trace   # writes firstcontact_trace_llm_*.jsonl
cd demo
python export_firstcontact.py            # picks the newest trace, writes firstcontact_data.js
# or: python export_firstcontact.py --trace ../firstcontact_trace_llm_<stamp>.jsonl
```

## Files

| File | Role |
|---|---|
| `index.html` | the demo UI (vanilla JS + inline SVG charts; no dependencies) |
| `export_demo.py` | compression scenario → `demo_data.js` |
| `export_firstcontact.py` | first-contact trace → `firstcontact_data.js` |
| `demo_data.js` / `firstcontact_data.js` | generated data (`window.DEMO_DATA` / `window.FC_DATA`) |

## Talking points

- **Same terse emerged language, two routes.** Compression pays a one-time DEFINE cost;
  first-contact uses opaque codes from round 0 (no DEFINE) but must *ground* them.
- **Token = message payload on the wire** (word count, a model-independent proxy for LLM
  tokens), not message count.
- **ToM's payoff is on the token axis too:** by grounding fast it lets you switch off the
  feedback side-channel and stop paying for it — cheaper *and* reliable.
- Honest caveat for a slide: the "feedback OFF after grounding" is a cost model; ToM also
  adds prompt tokens to the receiver's own call (counted separately from wire+feedback).
