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
