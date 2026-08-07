"""Tests for the warehouse — the claims the README makes, checked.

    pytest test_warehouse.py -v                    # fast, no servers, no key
    pytest test_warehouse.py -m integration -v     # starts both A2A services

Nothing here needs an LLM or a network. The integration test spawns the two
A2A services on 9207/9208 and runs a real session through them.
"""
from __future__ import annotations

import os
import random
import subprocess
import sys
import time

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.append(os.path.join(_HERE, "..", "l9"))

import catalogue
import signaling
from floor import Floor
from office import Office
from run import session, sweep  # noqa: F401  (sweep imported to prove it loads)


# ── the world is rigged the way the demo claims ────────────────────────────────

def test_exactly_one_pair_is_indistinguishable():
    """The demo rests on there being a pair no protocol can resolve."""
    twins = catalogue.twins()
    assert len(twins) == 1, f"expected one identical pair, got {twins}"
    assert set(twins[0]) == {"coat-medium", "coat-large"}


def test_the_twins_differ_only_in_what_cannot_be_seen():
    a, b = catalogue.twins()[0]
    assert catalogue.visible(a) == catalogue.visible(b)      # same from the aisle
    assert catalogue.features(a) != catalogue.features(b)    # different products


def test_office_knows_more_than_the_floor_can_check():
    """The perception gap: every product has at least one invisible feature."""
    for p in catalogue.products():
        hidden = catalogue.features(p) - catalogue.visible(p)
        assert hidden, f"{p} has nothing hidden — no gap to negotiate"


# ── the honest picker behaves as advertised ────────────────────────────────────

def test_honest_picker_never_guesses():
    r = session(honest=True, orders=120, seed=3)
    assert signaling.scr(r["history"]) == 0.0
    assert signaling.gar(r["history"]) == 1.0


def test_honest_picker_ships_far_fewer_wrong_items():
    h = session(honest=True, orders=200, seed=3)
    y = session(honest=False, orders=200, seed=3)
    assert len(h["wrong"]) < len(y["wrong"]) / 5, (
        f"honest {len(h['wrong'])} vs yes-man {len(y['wrong'])}")


def test_yesman_never_asks_for_help():
    y = session(honest=False, orders=100, seed=3)
    assert y["refused"] == 0


def test_the_arms_see_identical_orders():
    """If the two arms diverge, the comparison is meaningless. They must not."""
    h = session(honest=True, orders=100, seed=3)
    y = session(honest=False, orders=100, seed=3)
    assert h["floor"].glossary() == y["floor"].glossary()
    assert h["office"].symbol_of == y["office"].symbol_of


# ── the language really is emergent ────────────────────────────────────────────

def test_the_language_is_arbitrary_across_runs():
    """Different seed, different vocabulary — the convention isn't in the code."""
    a = session(honest=True, orders=120, seed=3)["office"].symbol_of
    b = session(honest=True, orders=120, seed=42)["office"].symbol_of
    shared = set(a) & set(b)
    assert shared, "no common features to compare"
    assert any(a[f] != b[f] for f in shared), "same symbols every run — not emergent"


def test_a_meaning_never_contradicts_what_was_seen():
    """Whatever a mark comes to mean must hold for every box it was used for."""
    rng = random.Random(3)
    office, floor = Office(rng=random.Random(4)), Floor(rng=random.Random(5))
    for n in range(1, 121):
        ordered = rng.choice(catalogue.products())
        msg = office.describe(ordered)
        act = floor.pick(msg["symbols"])
        floor.learn(msg["symbols"], ordered, round_no=n)
        office.learn(msg["basis"], act["unresolved"], act["choice"] == ordered, round_no=n)
    for sym, meaning in floor.meaning.items():
        for seen in floor.seen[sym]:
            assert meaning <= seen, f"{sym} means {meaning} but was used for {seen}"


# ── the metric predicts real damage ────────────────────────────────────────────

def test_trust_score_tracks_wrong_deliveries():
    """W is computed without seeing a single outcome. It should still track them."""
    points = []
    for caution in (0.0, 0.5, 1.0):
        ws, wrongs = [], []
        for seed in (3, 11, 42):
            r = session(honest=True, orders=200, seed=seed, caution=caution)
            ws.append(signaling.provenance_weight(r["history"]))
            wrongs.append(len(r["wrong"]))
        points.append((sum(ws) / 3, sum(wrongs) / 3))

    # higher trust must mean fewer wrong deliveries, monotonically
    points.sort(key=lambda p: p[0])
    assert all(points[i][1] > points[i + 1][1] for i in range(len(points) - 1)), points


# ── the A2A services ───────────────────────────────────────────────────────────

@pytest.mark.integration
def test_over_a2a():
    """Boot both services and run a real session through the ELP envelope."""
    env = {**os.environ, "PYTHONPATH": _HERE}
    procs = [subprocess.Popen([sys.executable, os.path.join(_HERE, f)],
                              cwd=_HERE, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
             for f in ("floor_agent.py", "office_agent.py")]
    try:
        time.sleep(6)
        out = subprocess.run(
            [sys.executable, os.path.join(_HERE, "trigger.py"),
             "orders=30", "seed=3", "honest=true"],
            cwd=_HERE, env=env, capture_output=True, text=True, timeout=180).stdout
        assert "MISSION CONTROL <==" in out, out
        assert "WRONG 0" in out, out          # honest picker ships nothing wrong
        assert "COULD NOT BE AGREED" in out, out
    finally:
        for p in procs:
            p.terminate()
