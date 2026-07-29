# Interlingua UI

A space-themed web dashboard that animates two agents — an astronaut
(**Grace**) and an alien (**Rocky**) — starting with *no words in common* and
inventing a shared language from scratch, symbol by symbol, live in the browser.

The visual theme (dark nebula backdrop, cyan **Grace** / amber **Rocky**
accents, glass cards, the beam between the two ships) and the character art
(`astro.jpeg`, `alien.jpeg`, `bcg.jpg`) are from the *Project Hail Mary* concept.

## Design

The server is **minimal** — it only serves the page and its images. The whole
negotiation (language generation + chat feed) streams **client-side from mock
data**: a faithful replay of the negotiation the agents run
(`coin` / `adopt` / `alignment`), paced with timers so it reads like a live
conversation. No backend calls, no external services.

Enter a `seed` to reproduce a specific run, or hit **↺ Replay** to re-run the
last one.

## What it shows

- **Two agent cards** — Grace (`:9101`) and Rocky (`:9102`) with their live lexicons.
- **The negotiation feed** — each hop as a chat bubble: who proposed which symbol
  for which meaning, and who adopted it.
- **Alignment bar + round counter** — climbs to 100% as the lexicons converge.
- **Shared codebook** — the final language both agents agree on.

## Run

```bash
pip install -r ../requirements.txt      # starlette + uvicorn (already required)
python -m ui.server                     # http://127.0.0.1:8000
```

Open <http://127.0.0.1:8000> and hit **✦ Generate language**.

## Files

```
ui/
  server.py        — minimal Starlette static server (page + assets)
  static/
    index.html     — the dashboard + client-side mock negotiation stream
    astro.jpeg     — Grace (the astronaut)
    alien.jpeg     — Rocky (the Eridian)
    bcg.jpg        — nebula backdrop
```
