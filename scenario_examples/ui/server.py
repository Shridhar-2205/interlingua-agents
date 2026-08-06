"""Comparison UI server — runs both scenarios and streams events via SSE.

    python server.py            # mock mode (default) — fast, no LLM
    python server.py --live     # live mode — starts real agents, calls LLM

Opens on http://localhost:9500. The browser UI triggers scenario runs and
receives real-time events as agents communicate over A2A.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route
from starlette.requests import Request
from sse_starlette.sse import EventSourceResponse

ROOT = Path(__file__).resolve().parent.parent
FREE_FORM_DIR = ROOT / "free_form"
ELP_DIR = ROOT / "elp"
STATIC_DIR = Path(__file__).resolve().parent / "static"

HOST, PORT = "localhost", 9500
MOCK_MODE = "--live" not in sys.argv

FF_ALPHA_PORT, FF_BETA_PORT = 9301, 9302
ELP_ALPHA_PORT, ELP_BETA_PORT = 9401, 9402

_procs: dict[str, subprocess.Popen] = {}

CONCEPTS = ["river", "sea", "tree", "apple", "dance", "fruit", "fire", "moon", "star", "stone"]
SYMBOLS = list("○✦≈△▽◆∿☆⬡♁∆⊚◐▣✧⋈●◇➤∞⟐⌘✺❉")
SHAREABLE = {"river", "sea", "tree", "apple", "dance", "fruit"}
UNSHAREABLE = {"fire", "moon", "star", "stone"}


# ══════════════════════════════════════════════════════════════════════════════
# MOCK MODE — simulates both scenarios with realistic output, no LLM needed
# ══════════════════════════════════════════════════════════════════════════════

async def _mock_free_form():
    """Simulate a free-form run: confused LLM agents spiraling into failure."""
    ff_objects = ["sun", "water", "fire", "rock", "tree", "moon", "sky", "cloud", "bird", "fish"]
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
# LIVE MODE — starts real agents as subprocess, triggers via A2A
# ══════════════════════════════════════════════════════════════════════════════

def _env():
    env = os.environ.copy()
    for env_file in [FREE_FORM_DIR / ".env", ELP_DIR / ".env"]:
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k.strip(), v.strip())
    l9_dir = str(ROOT.parent / "l9")
    project_root = str(ROOT.parent)
    env["PYTHONPATH"] = os.pathsep.join([l9_dir, project_root, env.get("PYTHONPATH", "")])
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _kill_all():
    for name, p in list(_procs.items()):
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass
        _procs.pop(name, None)


PYTHON = sys.executable


def _start_agent(name: str, script: Path, env: dict) -> subprocess.Popen:
    if name in _procs:
        try:
            os.killpg(os.getpgid(_procs[name].pid), signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass
    p = subprocess.Popen(
        [PYTHON, str(script)],
        cwd=str(script.parent),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )
    _procs[name] = p
    return p


async def _wait_for_port(port: int, timeout: float = 10.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"http://localhost:{port}/.well-known/agent.json", timeout=1)
                if r.status_code in (200, 404, 405):
                    return True
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout):
            pass
        await asyncio.sleep(0.3)
    return False


async def _live_scenario(scenario: str, run_id: str):
    env = _env()

    if scenario == "free_form":
        alpha_port, beta_port = FF_ALPHA_PORT, FF_BETA_PORT
        alpha_script = FREE_FORM_DIR / "agent_alpha.py"
        beta_script = FREE_FORM_DIR / "agent_beta.py"
    else:
        alpha_port, beta_port = ELP_ALPHA_PORT, ELP_BETA_PORT
        alpha_script = ELP_DIR / "agent_alpha.py"
        beta_script = ELP_DIR / "agent_beta.py"

    yield {"event": "status", "data": json.dumps({"msg": f"Starting {scenario} agents..."})}

    # Kill leftover processes
    import subprocess as _sp
    for port in [alpha_port, beta_port]:
        try:
            pids = _sp.check_output(["lsof", "-ti", f":{port}"], text=True).strip()
            if pids:
                for pid in pids.split("\n"):
                    os.kill(int(pid), signal.SIGTERM)
        except (_sp.CalledProcessError, ValueError, ProcessLookupError):
            pass
    await asyncio.sleep(0.5)

    _start_agent(f"{scenario}_beta", beta_script, env)
    await asyncio.sleep(2)
    _start_agent(f"{scenario}_alpha", alpha_script, env)

    if not await _wait_for_port(alpha_port):
        yield {"event": "error", "data": json.dumps({"msg": "Alpha agent failed to start"})}
        return
    if not await _wait_for_port(beta_port):
        yield {"event": "error", "data": json.dumps({"msg": "Beta agent failed to start"})}
        return

    yield {"event": "status", "data": json.dumps({"msg": "Agents ready. Triggering..."})}

    # Fire trigger in background, stream subprocess logs while waiting
    result_holder: dict = {}

    async def _trigger():
        async with httpx.AsyncClient(timeout=600) as client:
            payload = {
                "jsonrpc": "2.0", "id": "1", "method": "SendMessage",
                "params": {"message": {"message_id": f"trigger-{run_id}", "role": "ROLE_USER",
                                       "parts": [{"text": "begin"}]}}
            }
            try:
                resp = await client.post(
                    f"http://localhost:{alpha_port}/",
                    json=payload,
                    headers={"Content-Type": "application/json", "A2A-Version": "1.0"},
                )
                result_holder["data"] = resp.json()
            except Exception as e:
                result_holder["error"] = str(e)

    trigger_task = asyncio.create_task(_trigger())

    # Stream stdout from both agents while the trigger runs
    procs = [_procs.get(f"{scenario}_alpha"), _procs.get(f"{scenario}_beta")]
    import select
    while not trigger_task.done():
        for proc in procs:
            if proc and proc.stdout:
                while select.select([proc.stdout], [], [], 0)[0]:
                    line = proc.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode(errors="replace").rstrip()
                    if decoded.strip() and "INFO:" not in decoded:
                        yield {"event": "log", "data": json.dumps({"line": decoded})}
        await asyncio.sleep(0.3)

    # Drain any remaining output
    for proc in procs:
        if proc and proc.stdout:
            while select.select([proc.stdout], [], [], 0.1)[0]:
                line = proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode(errors="replace").rstrip()
                if decoded.strip() and "INFO:" not in decoded:
                    yield {"event": "log", "data": json.dumps({"line": decoded})}

    if "error" in result_holder:
        yield {"event": "error", "data": json.dumps({"msg": result_holder["error"]})}
    elif "data" in result_holder:
        result = result_holder["data"]
        if "error" in result:
            yield {"event": "error", "data": json.dumps({"msg": result["error"].get("message", "Unknown error")})}
        else:
            msg = result.get("result", {}).get("message", {})
            parts = msg.get("parts", [])
            text_part = next((p.get("text", "") for p in parts if "text" in p), "")
            yield {"event": "result", "data": json.dumps({
                "scenario": scenario, "text": text_part, "run_id": run_id,
            })}

    yield {"event": "done", "data": json.dumps({"scenario": scenario})}

    for name in [f"{scenario}_alpha", f"{scenario}_beta"]:
        if name in _procs:
            try:
                os.killpg(os.getpgid(_procs[name].pid), signal.SIGTERM)
            except (ProcessLookupError, OSError):
                pass
            _procs.pop(name, None)


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
                        {"text": "*points at fire* Fire!"},
                        {"data": "{...}", "mediaType": "application/json"},
                    ],
                    "_note": "No participants, no episode, no grounding, no belief state",
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
                        {"text": "alpha proposes ○ for river -> beta"},
                        {"data": {"protocol": "ELP", "version": "0.1",
                                  "participants": {"actors": [{"id": "alpha", "role": "sender"}, {"id": "beta", "role": "receiver"}]},
                                  "message": {"id": "a3f8c901...", "parents": ["b7c2e4f0..."], "episode": "urn:ioc:emerge:session:run1"},
                                  "context": {"topic": "concept:river"},
                                  "type": "emergence",
                                  "data": {"round": 5, "referent": "river", "proposal": "○", "decision": "propose"}},
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
                "L9": {"fields": {"protocol": "str (ELP)", "version": "str (0.1)", "participants": "ParticipantSet", "message": "Message", "context": "Optional[Context]", "type": "str (emergence)", "data": "dict"}},
            },
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════

async def index(request: Request):
    return FileResponse(STATIC_DIR / "index.html")


async def agents_info(request: Request):
    return JSONResponse(_agent_info())


_running: set[str] = set()

async def run_scenario(request: Request):
    scenario = request.path_params["scenario"]
    run_id = uuid4().hex[:8]

    def _wrap(gen):
        async def _inner():
            try:
                async for item in gen:
                    yield item
            finally:
                _running.discard(scenario)
        return _inner()

    if MOCK_MODE:
        if scenario == "free_form":
            return EventSourceResponse(_mock_free_form())
        else:
            return EventSourceResponse(_mock_elp())
    else:
        if scenario in _running:
            return JSONResponse({"error": "already running"}, status_code=409)
        _running.add(scenario)
        return EventSourceResponse(_wrap(_live_scenario(scenario, run_id)))


async def get_mode(request: Request):
    return JSONResponse({"mock": MOCK_MODE})


async def stop_all(request: Request):
    _kill_all()
    return JSONResponse({"ok": True})


app = Starlette(routes=[
    Route("/", index),
    Route("/api/agents", agents_info),
    Route("/run/{scenario}", run_scenario),
    Route("/mode", get_mode),
    Route("/stop", stop_all, methods=["POST"]),
    Route("/static/{path:path}", lambda r: FileResponse(STATIC_DIR / r.path_params["path"])),
])


if __name__ == "__main__":
    mode_label = "MOCK (fast demo)" if MOCK_MODE else "LIVE (real agents + LLM)"
    print(f"Comparison UI on http://{HOST}:{PORT}  [{mode_label}]")
    print(f"  Use --live flag to run real agents")
    uvicorn.run(app, host=HOST, port=PORT)
