"""Interlingua Dashboard server — combines two use cases in one UI.

    python server.py            # mock mode — fast demo, no agents/LLM required

Serves a single-page dashboard on http://127.0.0.1:9500 with a top-level tab
switcher:

  1. Emergent Alignment — Free-Form A2A vs ELP-over-A2A (streams a mock run via
     SSE using the shared CONCEPTS vocabulary; only the protocol differs).
  2. Bandwidth & Grounding — token compression + grounding-an-opaque-code (ToM)
     walkthrough, replayed from demo_data.js + firstcontact_data.js.

Mock-only: every stream is generated locally (no real agents, no LLM calls), so
the demo is instant and fully self-contained.
"""
from __future__ import annotations

import asyncio
import json
import random
from pathlib import Path
from uuid import uuid4

import uvicorn
from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route
from starlette.requests import Request
from sse_starlette.sse import EventSourceResponse

# Dashboard lives at <repo>/dashboard; static assets sit alongside it.
DASHBOARD_DIR = Path(__file__).resolve().parent
STATIC_DIR = DASHBOARD_DIR / "static"

HOST, PORT = "127.0.0.1", 9500

# Ports shown on the agent cards in the UI (illustrative — no real agents run).
FF_ALPHA_PORT, FF_BETA_PORT = 9301, 9302
ELP_ALPHA_PORT, ELP_BETA_PORT = 9401, 9402

CONCEPTS = ["river", "sea", "tree", "apple", "dance", "fruit", "fire", "moon", "star", "stone"]
SYMBOLS = list("○✦≈△▽◆∿☆⬡♁∆⊚◐▣✧⋈●◇➤∞⟐⌘✺❉")
SHAREABLE = {"river", "sea", "tree", "apple", "dance", "fruit"}
UNSHAREABLE = {"fire", "moon", "star", "stone"}


# ══════════════════════════════════════════════════════════════════════════════
# MOCK MODE — simulates both scenarios with realistic output, no LLM needed
# ══════════════════════════════════════════════════════════════════════════════

async def _mock_free_form():
    """Simulate a free-form run: confused agents spiraling into failure.

    Uses the SAME concept vocabulary as the ELP run (CONCEPTS) so both panels are
    genuinely the same task/environment — only the protocol differs.
    """
    ff_objects = list(CONCEPTS)
    alien_sounds = ["vrk", "zul", "morra", "draak", "thaan", "nuu", "oosha", "qip", "plix", "felk",
                    "glisk", "tuu", "krin", "plif", "zraa", "gwom", "moof", "tweelk", "boff", "skree"]

    yield {"event": "status", "data": json.dumps({"msg": "Starting free_form agents..."})}
    await asyncio.sleep(0.3)
    yield {"event": "status", "data": json.dumps({"msg": "Agents ready. Triggering..."})}
    await asyncio.sleep(0.3)
    yield {"event": "log", "data": json.dumps({"line": "Alpha Agent (free-form) on http://localhost:9301"})}
    yield {"event": "log", "data": json.dumps({"line": "Beta Agent (free-form) on http://localhost:9302"})}
    await asyncio.sleep(0.2)

    attempted = {}
    for rnd in range(1, 31):
        obj = random.choice(ff_objects)
        alpha_msg = f"*points at the {obj}* {obj.capitalize()}!"
        yield {"event": "log", "data": json.dumps({"line": f"ALPHA: {alpha_msg}"})}
        await asyncio.sleep(0.15)

        if rnd <= 5:
            sound = random.choice(alien_sounds)
            beta_msg = f"*looks at the {obj}, tilts head* {sound.capitalize()}!"
            attempted[obj] = attempted.get(obj, set())
            attempted[obj].add(sound)
        elif rnd <= 12:
            sound1 = random.choice(alien_sounds)
            sound2 = random.choice(alien_sounds)
            if random.random() < 0.6:
                beta_msg = f"*squints, confused* ...{sound1}? ...no... {sound2}!"
                attempted.setdefault(obj, set()).update([sound1, sound2])
            else:
                beta_msg = f"*freezes, stares at other creature*"
        elif rnd <= 20:
            if random.random() < 0.7:
                beta_msg = "*freezes completely*"
            else:
                beta_msg = f"*looks confused, points at something else* {random.choice(alien_sounds).capitalize()}!"
        else:
            beta_msg = "*freezes*" if random.random() < 0.8 else "*blinks slowly*"

        yield {"event": "log", "data": json.dumps({"line": f"BETA:  {beta_msg}"})}
        await asyncio.sleep(0.15)

        if rnd <= 5:
            alpha_react = f"*nods, noting the sound*"
        elif rnd <= 10:
            inconsistent = [o for o, sounds in attempted.items() if len(sounds) > 1]
            if inconsistent:
                alpha_react = f"*frowns — creature used different sounds for {inconsistent[0]}*"
            else:
                alpha_react = "*tries again, points more deliberately*"
        elif rnd <= 20:
            alpha_react = random.choice([
                "*realizes the creature is stuck in a fear loop*",
                "*stays very still, tries to appear non-threatening*",
                "*sighs, tries a completely different approach*",
                "*waits patiently for the creature to respond*",
            ])
        else:
            alpha_react = random.choice([
                "*stops completely*", "*remains still*", "*stays calm*",
                "*gives up trying to communicate*",
            ])

        yield {"event": "log", "data": json.dumps({"line": f"ALPHA: {alpha_react}"})}
        yield {"event": "log", "data": json.dumps({"line": f"  [{rnd}/30]"})}
        await asyncio.sleep(0.1)

    yield {"event": "log", "data": json.dumps({"line": "DONE (stopped at cap 30) after 30 exchanges"})}
    yield {"event": "result", "data": json.dumps({
        "scenario": "free_form",
        "text": "stopped at cap 30 — 0 confirmed mappings",
        "run_id": uuid4().hex[:8],
    })}
    yield {"event": "done", "data": json.dumps({"scenario": "free_form"})}


async def _mock_elp():
    """Simulate an ELP run: structured negotiation with genuine convergence."""
    yield {"event": "status", "data": json.dumps({"msg": "Starting elp agents..."})}
    await asyncio.sleep(0.3)
    yield {"event": "status", "data": json.dumps({"msg": "Agents ready. Triggering..."})}
    await asyncio.sleep(0.3)
    yield {"event": "log", "data": json.dumps({"line": f"Alpha Agent (ELP + ToM) on http://localhost:9401  (ext: https://outshift.io/a2a-ext/emergence/v1)"})}
    yield {"event": "log", "data": json.dumps({"line": f"Beta Agent (ELP + ToM) on http://localhost:9402  (ext: https://outshift.io/a2a-ext/emergence/v1)"})}
    await asyncio.sleep(0.2)

    alpha_lex = {c: random.choice(SYMBOLS) for c in CONCEPTS}
    beta_lex = {c: random.choice(SYMBOLS) for c in CONCEPTS}
    history = []
    aligned = set()

    for rnd in range(1, 31):
        speaker = "alpha" if rnd % 2 == 1 else "beta"
        unresolved = [c for c in CONCEPTS if c not in aligned]
        if not unresolved:
            break
        concept = random.choice(unresolved)
        symbol = alpha_lex[concept] if speaker == "alpha" else beta_lex[concept]

        receiver = "beta" if speaker == "alpha" else "alpha"
        yield {"event": "log", "data": json.dumps({
            "line": f"[{speaker}] {speaker} proposes {symbol} for {concept} -> {receiver}"
        })}
        await asyncio.sleep(0.12)

        # Shareable concepts converge; unshareable ones don't
        if concept in SHAREABLE:
            if random.random() < 0.55:
                if speaker == "alpha":
                    beta_lex[concept] = symbol
                else:
                    alpha_lex[concept] = symbol
                aligned.add(concept)
                history.append({"referent": concept, "symbol": symbol, "accepted": True,
                                "grounded": True, "speaker": speaker})
                yield {"event": "log", "data": json.dumps({
                    "line": f"[{receiver}] accepted {symbol} for {concept} (grounded)"
                })}
            else:
                yield {"event": "log", "data": json.dumps({
                    "line": f"[{receiver}] rejected {symbol} for {concept} (low contingency)"
                })}
        else:
            history.append({"referent": concept, "symbol": symbol, "accepted": False,
                            "grounded": False, "speaker": speaker})
            yield {"event": "log", "data": json.dumps({
                "line": f"[{receiver}] rejected {symbol} for {concept} (no perceptual overlap)"
            })}
        await asyncio.sleep(0.08)

    alignment = len(aligned) / len(CONCEPTS)
    gar = 1.0
    scr = 0.0
    w = 1.0

    final_text = (f"done | round {rnd} | align {alignment:.0%} | GAR {gar} SCR {scr} W {w}")
    yield {"event": "log", "data": json.dumps({"line": f"[alpha] {final_text}"})}
    await asyncio.sleep(0.1)

    yield {"event": "log", "data": json.dumps({"line": f"  alpha : {alpha_lex}"})}
    yield {"event": "log", "data": json.dumps({"line": f"  beta  : {beta_lex}"})}

    yield {"event": "result", "data": json.dumps({
        "scenario": "elp",
        "text": final_text,
        "run_id": uuid4().hex[:8],
    })}
    yield {"event": "done", "data": json.dumps({"scenario": "elp"})}


# ══════════════════════════════════════════════════════════════════════════════
# AGENT INFO — serves agent cards + sample messages to the UI
# ══════════════════════════════════════════════════════════════════════════════

def _agent_info():
    """Return agent cards and sample messages for both scenarios."""
    return {
        "free_form": {
            "alpha": {
                "card": {
                    "name": "Alpha (free-form)",
                    "description": "English-speaking agent, plain LLM, no ToM — free-form vocabulary building.",
                    "version": "1.0.0",
                    "url": f"http://localhost:{FF_ALPHA_PORT}/",
                    "protocol_binding": "JSONRPC",
                    "skills": [{"id": "build-vocab", "name": "Build vocabulary (free-form)"}],
                    "extensions": [],
                    "streaming": False,
                },
                "sample_message": {
                    "role": "ROLE_USER",
                    "parts": [
                        {"text": "alpha proposes \u2248 for river -> beta"},
                    ],
                    "_note": "Plain text only — no participants, no episode, no grounding, no belief, no ToM",
                },
            },
            "beta": {
                "card": {
                    "name": "Beta (free-form)",
                    "description": "Agent that speaks invented language, plain LLM, no ToM.",
                    "version": "1.0.0",
                    "url": f"http://localhost:{FF_BETA_PORT}/",
                    "protocol_binding": "JSONRPC",
                    "skills": [{"id": "speak-alien", "name": "Speak alien (free-form)"}],
                    "extensions": [],
                    "streaming": False,
                },
            },
        },
        "elp": {
            "alpha": {
                "card": {
                    "name": "Alpha (ELP)",
                    "description": "Emergent-convention agent (alpha) with ToM + signaling, ELP-over-A2A.",
                    "version": "1.0.0",
                    "url": f"http://localhost:{ELP_ALPHA_PORT}/",
                    "protocol_binding": "JSONRPC",
                    "skills": [{"id": "emerge", "name": "Emergent convention (ELP)",
                                "tags": ["emergent", "l9", "tom"]}],
                    "extensions": [{
                        "uri": "https://outshift.io/a2a-ext/emergence/v1",
                        "description": "Emergent-convention convergence with belief/grounding/ToM (ELP-over-A2A).",
                        "required": False,
                        "params": {
                            "protocol": "ELP",
                            "payload_type": "emergence",
                            "carries": ["lexicons", "utterance", "grounding", "belief", "tom", "history"],
                        },
                    }],
                    "streaming": False,
                },
                "sample_message": {
                    "role": "ROLE_USER",
                    "parts": [
                        {"text": "alpha proposes \u2248 for river -> beta"},
                        {"data": {
                            "protocol": "ELP",
                            "version": "0.1",
                            "participants": {
                                "actors": [
                                    {"id": "alpha", "role": "sender"},
                                    {"id": "beta", "role": "receiver"},
                                ],
                                "groups": None,
                            },
                            "message": {
                                "id": "a3f8c901e2d4",
                                "parents": ["b7c2e4f0a19c"],
                                "episode": "urn:ioc:emerge:river:run1",
                            },
                            "context": {"topic": "concept:river"},
                            "type": "emergence",
                            "data": {
                                "round": 5,
                                "speaker": "alpha",
                                "referent": "river",
                                "proposal": "\u2248",
                                "decision": "propose",
                                "lexicons": {
                                    "alpha": {"river": "\u2248", "sea": "\u25cf", "tree": "\u229a", "apple": "\u25b3", "fire": "\u2248", "moon": "\u2606"},
                                    "beta":  {"river": "\u2248", "sea": "\u25cf", "tree": "\u229a", "apple": "\u25b3", "fire": "\u25bd", "moon": "\u25cf"},
                                },
                                "utterance": {
                                    "text": "alpha proposes \u2248 for river",
                                    "evidence": ["river"],
                                    "addresses_evidence": ["river"],
                                },
                                "grounding": {
                                    "contingency_verified": True,
                                    "contingency_score": 1.0,
                                    "repair_reason": None,
                                },
                                "belief": {"prior": 0.5, "posterior": 1.0, "revision_cause": "structured"},
                                "tom": {
                                    "beta": {"sea": "\u25cf", "tree": "\u229a", "apple": "\u25b3", "river": "?"},
                                },
                                "history": [
                                    {"referent": "sea",  "symbol": "\u25cf", "accepted": True, "grounded": True, "speaker": "beta"},
                                    {"referent": "tree", "symbol": "\u229a", "accepted": True, "grounded": True, "speaker": "alpha"},
                                    {"referent": "apple","symbol": "\u25b3", "accepted": True, "grounded": True, "speaker": "beta"},
                                ],
                            },
                        },
                         "mediaType": "application/vnd.elp+json"},
                    ],
                    "extensions": ["https://outshift.io/a2a-ext/emergence/v1"],
                },
            },
            "beta": {
                "card": {
                    "name": "Beta (ELP)",
                    "description": "Emergent-convention agent (beta) with ToM + signaling, ELP-over-A2A.",
                    "version": "1.0.0",
                    "url": f"http://localhost:{ELP_BETA_PORT}/",
                    "protocol_binding": "JSONRPC",
                    "skills": [{"id": "emerge", "name": "Emergent convention (ELP)",
                                "tags": ["emergent", "l9", "tom"]}],
                    "extensions": [{
                        "uri": "https://outshift.io/a2a-ext/emergence/v1",
                        "description": "Emergent-convention convergence with belief/grounding/ToM (ELP-over-A2A).",
                        "required": False,
                        "params": {
                            "protocol": "ELP",
                            "payload_type": "emergence",
                            "carries": ["lexicons", "utterance", "grounding", "belief", "tom", "history"],
                        },
                    }],
                    "streaming": False,
                },
            },
            "l9_model": {
                "Actor": {"fields": {"id": "str", "role": "str (sender | receiver | observer)"}},
                "ParticipantSet": {"fields": {"actors": "list[Actor]", "groups": "Optional[dict]"}},
                "Message": {"fields": {"id": "str (uuid)", "parents": "list[str]", "episode": "str (URN)"}},
                "Context": {"fields": {"topic": "str (e.g. concept:river)"}},
                "L9": {"fields": {"protocol": "str (ELP)", "version": "str (0.1)", "participants": "ParticipantSet", "message": "Message", "context": "Optional[Context]", "type": "str (emergence)", "data": "EmergenceData"}},
                "EmergenceData": {"fields": {"round": "int", "speaker": "agent_id", "referent": "concept", "proposal": "symbol", "decision": "init | propose | converged", "lexicons": "dict", "utterance": "Utterance", "grounding": "Grounding", "belief": "Belief", "tom": "dict (peer models)", "history": "list[Event]"}},
                "Utterance": {"fields": {"text": "str", "evidence": "list[feature]", "addresses_evidence": "list[feature]"}},
                "Grounding": {"fields": {"contingency_verified": "bool", "contingency_score": "float", "repair_reason": "str | None"}},
                "Belief": {"fields": {"prior": "float", "posterior": "float", "revision_cause": "str"}},
                "Event": {"fields": {"referent": "concept", "symbol": "symbol", "accepted": "bool", "grounded": "bool", "speaker": "agent_id"}},
            },
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# COMPRESSION DEMO — mock SSE streams (compression + grounding)
#   Reads the same *_data.js files the client scrubs, and replays them round by
#   round so the demo tab can "run" like the scenario tab (status dot, beam,
#   live comparison), while the manual scrub/playback still works client-side.
# ══════════════════════════════════════════════════════════════════════════════

def _load_data_js(filename: str, varname: str) -> dict:
    """Parse `window.<varname> = { ... };` from a data JS file into a dict."""
    text = (STATIC_DIR / filename).read_text()
    marker = f"window.{varname}"
    start = text.index("=", text.index(marker)) + 1
    end = text.rstrip().rstrip(";")
    return json.loads(end[start:])


async def _mock_compression():
    """Replay the compression codebook run round by round."""
    yield {"event": "status", "data": json.dumps({"msg": "Grace (Encoder) opening channel to Rocky (Decoder)..."})}
    await asyncio.sleep(0.25)
    try:
        D = _load_data_js("demo_data.js", "DEMO_DATA")
    except Exception as e:  # pragma: no cover - defensive
        yield {"event": "error", "data": json.dumps({"msg": f"could not load demo data: {e}"})}
        yield {"event": "done", "data": json.dumps({"view": "compression"})}
        return

    rounds = D["rounds"]
    total_plain = D["summary"]["totalPlaintext"]
    vocab = D["summary"]["vocabSize"]
    yield {"event": "status", "data": json.dumps({"msg": f"Relaying {len(rounds)} mission logs over ELP-over-A2A..."})}
    await asyncio.sleep(0.2)

    for i, rd in enumerate(rounds):
        saved = rd["cumPlaintext"] - rd["cumProtocol"]
        pct = round(100 * (1 - rd["cumProtocol"] / rd["cumPlaintext"])) if rd["cumPlaintext"] else 0
        yield {"event": "round", "data": json.dumps({
            "view": "compression",
            "index": i,
            "phase": rd["phase"],
            "cumPlaintext": rd["cumPlaintext"],
            "cumProtocol": rd["cumProtocol"],
            "saved": saved,
            "pct": pct,
            "codebook": len(rd["codebookAfter"]),
            "vocab": vocab,
            "roundPlain": rd["plaintext"]["tokens"],
            "roundProtocol": rd["protocol"]["tokens"],
        })}
        await asyncio.sleep(0.32)

    final = rounds[-1]
    pct = round(100 * (1 - final["cumProtocol"] / final["cumPlaintext"])) if final["cumPlaintext"] else 0
    yield {"event": "result", "data": json.dumps({
        "view": "compression",
        "cumPlaintext": final["cumPlaintext"],
        "cumProtocol": final["cumProtocol"],
        "saved": final["cumPlaintext"] - final["cumProtocol"],
        "pct": pct,
        "vocab": vocab,
        "totalPlaintext": total_plain,
    })}
    yield {"event": "done", "data": json.dumps({"view": "compression"})}


async def _mock_grounding():
    """Replay the first-contact grounding run for both arms in parallel."""
    yield {"event": "status", "data": json.dumps({"msg": "Grace (Emitter) sending opaque code to Rocky (Grounder)..."})}
    await asyncio.sleep(0.25)
    try:
        FC = _load_data_js("firstcontact_data.js", "FC_DATA")
    except Exception as e:  # pragma: no cover - defensive
        yield {"event": "error", "data": json.dumps({"msg": f"could not load grounding data: {e}"})}
        yield {"event": "done", "data": json.dumps({"view": "grounding"})}
        return

    arm_order = FC["armOrder"]
    arms = FC["arms"]
    fields = FC["meta"]["fields"]
    n_rounds = len(arms[arm_order[0]]["rounds"])
    plain_series = arms[arm_order[0]]["rounds"]

    yield {"event": "status", "data": json.dumps({"msg": f"Grounding over {n_rounds} rounds — comparing {', '.join(arm_order)}..."})}
    await asyncio.sleep(0.2)

    for i in range(n_rounds):
        payload = {"view": "grounding", "index": i, "arms": {}, "fields": len(fields)}
        for a in arm_order:
            rd = arms[a]["rounds"][i]
            payload["arms"][a] = {
                "cumEffective": rd["cumEffective"],
                "hits": rd["hits"],
                "coverage": rd.get("coverage", 0),
                "win": rd.get("win", False),
                "feedbackActive": rd.get("feedbackActive", True),
            }
        payload["cumPlaintext"] = plain_series[i]["cumPlaintext"]
        yield {"event": "round", "data": json.dumps(payload)}
        await asyncio.sleep(0.3)

    result = {"view": "grounding", "arms": {}, "plaintext": plain_series[-1]["cumPlaintext"],
              "horizon": FC["meta"].get("horizon")}
    for a in arm_order:
        arm = arms[a]
        result["arms"][a] = {
            "cumEffective": arm["rounds"][-1]["cumEffective"],
            "reliable": arm.get("reliable", False),
            "groundedAt": arm.get("groundedAt"),
            "tom": arm.get("tom", "tom" in a),
            "projTokens": arm["summary"]["projTokens"],
        }
    yield {"event": "result", "data": json.dumps(result)}
    yield {"event": "done", "data": json.dumps({"view": "grounding"})}


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════

async def index(request: Request):
    return FileResponse(STATIC_DIR / "index.html")


async def agents_info(request: Request):
    return JSONResponse(_agent_info())


async def run_scenario(request: Request):
    """Mock SSE stream for the Emergent Alignment scenarios (free_form | elp)."""
    scenario = request.path_params["scenario"]
    if scenario == "free_form":
        return EventSourceResponse(_mock_free_form())
    elif scenario == "elp":
        return EventSourceResponse(_mock_elp())
    return JSONResponse({"error": "unknown scenario"}, status_code=404)


async def run_demo(request: Request):
    """Mock SSE stream for the compression use case (view: compression|grounding)."""
    view = request.path_params["view"]
    if view == "compression":
        return EventSourceResponse(_mock_compression())
    elif view == "grounding":
        return EventSourceResponse(_mock_grounding())
    return JSONResponse({"error": "unknown view"}, status_code=404)


async def get_mode(request: Request):
    return JSONResponse({"mock": True})


def _static_file(request: Request):
    # Only serve files from within STATIC_DIR (guard against traversal).
    rel = request.path_params["path"]
    target = (STATIC_DIR / rel).resolve()
    if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.is_file():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(target)


app = Starlette(routes=[
    Route("/", index),
    Route("/api/agents", agents_info),
    Route("/run/{scenario}", run_scenario),
    Route("/demo/{view}", run_demo),
    Route("/mode", get_mode),
    Route("/static/{path:path}", _static_file),
])


if __name__ == "__main__":
    print(f"Interlingua Dashboard on http://{HOST}:{PORT}  [MOCK (fast demo)]")
    print(f"  Tab 1: Emergent Alignment   Tab 2: Bandwidth & Grounding")
    uvicorn.run(app, host=HOST, port=PORT)
