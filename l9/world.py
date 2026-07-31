"""The shared 'known environment' — what grounds meaning.

Agents share a WORLD but not a LANGUAGE (the Project Hail Mary setup): every
agent knows the same set of concepts and the features each concept exhibits.
Symbols are NOT shared — they must emerge. Features are common knowledge and
are what grounding (CIP) scores against: a symbol is 'grounded' for a concept
when the way a listener interprets it overlaps the features the speaker used to
justify it.

Features deliberately overlap across concepts (water: river+sea; flow:
river+wind; light: fire+moon+star) so reusing a symbol is sometimes justified
and sometimes a grounding failure — which is what makes the ToM/LLM judgement
(and CIP repair) non-trivial.
"""
from __future__ import annotations

# concept -> features both agents can, in principle, perceive
CONCEPTS: dict[str, list[str]] = {
    # Groundable across the gap — each has an AMODAL feature both agents perceive.
    "river": ["shiny", "water", "flow", "nature"],
    "sea":   ["big", "water", "salt", "nature"],
    "tree":  ["tall", "green", "nature", "alive"],
    "apple": ["red", "round", "food", "alive"],
    "dance": ["motion", "energy", "joy", "alive"],
    "fruit": ["green", "round", "food", "nature"],
    # UNshareable across the gap — 2 visual + 2 physical, NO amodal anchor, so
    # what Grace perceives and what Rocky perceives never overlap. Genuine agents
    # honestly fail to align on these; a mimic adopts them anyway (→ high SCR).
    "fire":  ["light", "bright", "hot", "energy"],
    "moon":  ["round", "night", "cold", "still"],
    "star":  ["bright", "many", "hot", "cold"],
    "stone": ["dark", "shiny", "hard", "heavy"],
}

# Feature modalities — used by lens.py to give each agent a different perceptual
# slice of the SAME world (the source of the gap they must negotiate across).
VISUAL:   set[str] = {"shiny", "big", "tall", "green", "red", "round", "light", "bright", "night", "many", "dark"}
PHYSICAL: set[str] = {"water", "flow", "salt", "motion", "energy", "hot", "cold", "still", "hard", "heavy"}
# features in neither modality are AMODAL — every agent perceives them (shared floor):
# nature, alive, food, joy

# arbitrary sign inventory the agents draw novel symbols from
SYMBOLS: list[str] = list("○✦≈△▽◆∿☆⬡♁∆⊚◐▣✧⋈●◇➤∞⟐⌘✺❉")


def concepts() -> list[str]:
    return list(CONCEPTS)


def features(concept: str) -> list[str]:
    return list(CONCEPTS[concept])


def amodal() -> set[str]:
    return {f for fs in CONCEPTS.values() for f in fs} - VISUAL - PHYSICAL
