"""The warehouse — the shared world, and the gap between the two agents.

The Office takes customer orders. The Floor walks the aisles and picks boxes.
Both know the full catalogue: every product and every property it has.

What the Office does NOT know is which of those properties the Floor can
actually *check from the aisle*. A sealed brown box shows its weight, its size,
whether it rattles, whether it came off the cold shelf. It does not show the
colour of the coat inside, or what size that coat is.

That is the whole gap, and it is not staged — it is what warehouses are like.

Two products are deliberately IDENTICAL to the Floor: coat-medium and
coat-large are both `soft, bulky` sealed boxes on the same shelf. The features
that separate them (`medium` / `large`) are invisible from the aisle. No amount
of clever communication resolves that pair — "I can't tell" is the only honest
answer, and finding that out is the point of the exercise.
"""
from __future__ import annotations

# Properties the Floor can perceive from the aisle — a sealed box shows these.
PERCEIVABLE: set[str] = {
    "heavy", "light", "rattles", "soft", "cold", "long", "small", "bulky",
}

# Everything else is customer language: real, true, and invisible to the Floor.
#   blue, red, medium, large, winter, gift, kitchen, book, art, sport, food

CATALOGUE: dict[str, set[str]] = {
    "mug-set":       {"heavy", "rattles", "gift", "kitchen"},
    "wine-glasses":  {"light", "rattles", "bulky", "gift", "kitchen"},
    "coat-medium":   {"soft", "bulky", "blue", "winter", "medium"},   # ← twin
    "coat-large":    {"soft", "bulky", "blue", "winter", "large"},    # ← twin
    "wool-scarf":    {"soft", "light", "bulky", "red", "winter"},
    "hardback-book": {"heavy", "small", "gift", "book"},
    "poster-tube":   {"long", "light", "blue", "art"},
    "yoga-mat":      {"long", "bulky", "soft", "sport"},
    "ice-cream":     {"cold", "small", "heavy", "food"},
    "frozen-peas":   {"cold", "light", "soft", "food"},
    "cutlery-set":   {"heavy", "rattles", "small", "gift", "kitchen"},
    "tshirt":        {"soft", "light", "small", "red", "medium"},
}


def products() -> list[str]:
    return list(CATALOGUE)


def features(product: str) -> set[str]:
    """Everything that is true about this product (Office's view)."""
    return set(CATALOGUE[product])


def visible(product: str) -> set[str]:
    """What the Floor can actually check from the aisle."""
    return CATALOGUE[product] & PERCEIVABLE


def twins() -> list[list[str]]:
    """Products the Floor genuinely cannot tell apart — identical from the aisle.

    This is the list the warehouse manager needs: every group here is a place
    that needs a printed label, because no protocol can fix it.
    """
    groups: dict[frozenset[str], list[str]] = {}
    for p in CATALOGUE:
        groups.setdefault(frozenset(visible(p)), []).append(p)
    return [g for g in groups.values() if len(g) > 1]


def rarity(feature: str) -> int:
    """How many products share this feature — fewer means more informative."""
    return sum(1 for p in CATALOGUE if feature in CATALOGUE[p])
