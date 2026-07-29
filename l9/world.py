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
    "river": ["water", "flow", "nature", "cold"],
    "sea":   ["water", "big", "salt", "nature"],
    "fire":  ["hot", "light", "danger", "energy"],
    "moon":  ["night", "light", "round", "sky"],
    "star":  ["night", "light", "many", "sky"],
    "wind":  ["air", "flow", "cold", "sky"],
    "stone": ["hard", "heavy", "ground", "still"],
    "tree":  ["nature", "tall", "green", "alive"],
    "apple": ["food", "round", "red", "alive"],
    "dance": ["motion", "joy", "rhythm", "alive"],
}

# Feature modalities — used by lens.py to give each agent a different perceptual
# slice of the SAME world (the source of the gap they must negotiate across).
VISUAL:   set[str] = {"light", "round", "red", "green", "tall", "big", "distant", "many", "night"}
PHYSICAL: set[str] = {"hot", "cold", "hard", "heavy", "water", "flow", "air", "energy", "motion", "still", "salt", "invisible"}
# features in neither modality are AMODAL — every agent perceives them (shared floor)

# arbitrary sign inventory the agents draw novel symbols from
SYMBOLS: list[str] = list("○✦≈△▽◆∿☆⬡♁∆⊚◐▣✧⋈●◇➤∞⟐⌘✺❉")


def concepts() -> list[str]:
    return list(CONCEPTS)


def features(concept: str) -> list[str]:
    return list(CONCEPTS[concept])


def amodal() -> set[str]:
    return {f for fs in CONCEPTS.values() for f in fs} - VISUAL - PHYSICAL
