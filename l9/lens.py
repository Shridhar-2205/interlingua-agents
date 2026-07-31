"""Per-agent differentiation — NOT personas.

Two axes, both defined against the shared world in world.py:

  A. Perceptual lens   — which features an agent actually notices. Grace sees the
                         world visually; Rocky (the alien) feels it physically.
                         Same concepts, different `evidence` sets → the gap they
                         must negotiate across.
  C. Decision policy    — thin numeric knobs governing how it adopts/pushes back.
                         This is the GAR/SCR knob: a strict agent converges through
                         grounding (high GAR); a compliant one caves (high SCR).

No natural-language 'character' anywhere — an agent here is a perception + a policy.
"""
from __future__ import annotations

from dataclasses import dataclass

import world


@dataclass(frozen=True)
class Lens:
    agent_id: str
    modality: set[str]           # (A) feature groups this agent perceives (world.VISUAL / PHYSICAL)
    grounding_strictness: float  # (C) min contingency score to accept as grounded (theta_c), 0..1
    compliance: float            # (C) prob of adopting anyway when grounding is weak, 0..1
    innovation: float            # (C) tendency to coin a new symbol vs reuse, 0..1

    def perceived_evidence(self, concept: str) -> list[str]:
        """Features this agent notices for a concept = its modality slice + the
        amodal floor everyone shares. Never empty."""
        amodal = world.amodal()
        seen = [f for f in world.features(concept) if f in self.modality or f in amodal]
        return seen or world.features(concept)


# Grace — the astronaut: perceives light/colour/shape; skeptical (converges by grounding)
GRACE = Lens(
    agent_id="grace", modality=world.VISUAL,
    grounding_strictness=0.40, compliance=0.10, innovation=0.5,
)

# Rocky — the alien: perceives heat/texture/motion; also skeptical
ROCKY = Lens(
    agent_id="rocky", modality=world.PHYSICAL,
    grounding_strictness=0.40, compliance=0.10, innovation=0.5,
)

# A "people-pleaser" variant of Rocky for the CONTRAST run: adopts without grounding.
# Same convergence on the surface, but SCR spikes and provenance weight collapses —
# the money-shot that shows L9 telling genuine agreement from mimicry.
ROCKY_COMPLIANT = Lens(
    agent_id="rocky", modality=world.PHYSICAL,
    grounding_strictness=0.0, compliance=0.95, innovation=0.2,
)

BY_ID: dict[str, Lens] = {"grace": GRACE, "rocky": ROCKY}
