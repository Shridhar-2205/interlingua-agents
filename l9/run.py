"""In-process smoke test / demo driver — no a2a-sdk, no LLM required.

Simulates the A2A ping-pong in one process by alternately calling agent.step()
for each agent, then reports convergence + the L9 quality metrics (GAR/SCR/W).

    python run.py            # genuine run (both agents ground before adopting)
    python run.py --mimic    # contrast run: one agent adopts without grounding
"""
from __future__ import annotations

import sys

import agent
import signaling
import lens as lens_mod


def drive(agents: list[str], max_hops: int = 200) -> dict:
    state = agent.initial_state(agents)
    turn = 0
    while state.get("decision") != "converged" and turn < max_hops:
        me = agents[turn % len(agents)]
        state = agent.step(state, me)
        turn += 1
    return state


def main() -> None:
    mimic = "--mimic" in sys.argv
    if mimic:
        lens_mod.BY_ID["rocky"] = lens_mod.ROCKY_COMPLIANT  # adopts without grounding

    state = drive(["grace", "rocky"])
    lexicons = state["lexicons"]
    history = state["history"]

    print(f"run: {'MIMIC (grounding off for rocky)' if mimic else 'GENUINE'}")
    print(f"rounds        : {state['round']}")
    print(f"alignment     : {signaling.alignment(lexicons):.0%}")
    print(f"adoptions     : {sum(1 for h in history if h['accepted'])}  "
          f"(grounded={sum(1 for h in history if h.get('grounded'))})")
    print(f"GAR (genuine) : {signaling.gar(history)}")
    print(f"SCR (mimicry) : {signaling.scr(history)}")
    print(f"W  (provenance): {signaling.provenance_weight(history)}")
    print(f"grace lex     : {lexicons['grace']}")
    print(f"rocky lex     : {lexicons['rocky']}")


if __name__ == "__main__":
    main()
