"""Gacha Engine - Weighted rarity roll with pity guarantee."""

import random
from typing import List, Optional, Tuple

from service.collection.character_registry import (
    RARITY_INFO,
    RARITY_ORDER,
    CharacterDef,
    rarity_rank,
)

PITY_THRESHOLD = 50          # Guaranteed legendary+ on the 50th open without one
PITY_MIN_RARITY = "legendary"


class GachaEngine:
    """Pure logic: no I/O. Easy to unit-test and to move server-side later."""

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()

    def roll_rarity(self, pity_counter: int, available: List[str]) -> str:
        forced = pity_counter + 1 >= PITY_THRESHOLD
        candidates = [r for r in RARITY_ORDER if r in available]
        if forced:
            high = [r for r in candidates if rarity_rank(r) >= rarity_rank(PITY_MIN_RARITY)]
            if high:
                candidates = high

        weights = [RARITY_INFO[r]["rate"] for r in candidates]
        return self.rng.choices(candidates, weights=weights, k=1)[0]

    def roll(self, pool: List[CharacterDef], pity_counter: int) -> Tuple[CharacterDef, int]:
        """Return (character, new_pity_counter)."""
        if not pool:
            raise ValueError("Gacha pool rỗng")

        available = sorted({c.rarity for c in pool}, key=rarity_rank)
        rarity = self.roll_rarity(pity_counter, available)
        char = self.rng.choice([c for c in pool if c.rarity == rarity])

        if rarity_rank(rarity) >= rarity_rank(PITY_MIN_RARITY):
            return char, 0
        return char, pity_counter + 1
