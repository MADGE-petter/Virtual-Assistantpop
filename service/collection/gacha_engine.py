"""Gacha Engine - Weighted rarity roll with 120-pull guaranteed Rate-Up pity."""

import random
from typing import List, Optional, Tuple

from service.collection.character_registry import (
    RARITY_INFO,
    RARITY_ORDER,
    CharacterDef,
    rarity_rank,
)

PITY_THRESHOLD = 120         # Guaranteed Rate-Up Mythic on the 120th pull
PITY_MIN_RARITY = "mythic"


class GachaEngine:
    """Pure logic: no I/O. Easy to unit-test and to move server-side later."""

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()

    def roll_rarity(
        self,
        pity_counter: int,
        available: List[str],
        min_rarity: Optional[str] = None,
    ) -> str:
        forced = (pity_counter + 1) >= PITY_THRESHOLD
        candidates = [r for r in RARITY_ORDER if r in available]

        if forced:
            high = [r for r in candidates if rarity_rank(r) >= rarity_rank(PITY_MIN_RARITY)]
            if high:
                candidates = high
        elif min_rarity:
            filtered = [r for r in candidates if rarity_rank(r) >= rarity_rank(min_rarity)]
            if filtered:
                candidates = filtered

        weights = [RARITY_INFO[r]["rate"] for r in candidates]
        return self.rng.choices(candidates, weights=weights, k=1)[0]

    def roll(
        self,
        pool: List[CharacterDef],
        pity_counter: int,
        featured_id: Optional[str] = None,
        min_rarity: Optional[str] = None,
    ) -> Tuple[CharacterDef, int]:
        """Return (character, new_pity_counter)."""
        if not pool:
            raise ValueError("Gacha pool rỗng")

        forced_rate_up = (pity_counter + 1) >= PITY_THRESHOLD
        available = sorted({c.rarity for c in pool}, key=rarity_rank)
        rarity = self.roll_rarity(pity_counter, available, min_rarity=min_rarity)

        tier_chars = [c for c in pool if c.rarity == rarity]
        featured_char = next((c for c in tier_chars if c.id == featured_id), None) if featured_id else None

        if forced_rate_up and featured_char is not None:
            # Lượt thứ 120 chắc chắn trúng nhân vật Rate-Up của Banner đang chọn
            char = featured_char
        elif featured_char is not None and len(tier_chars) > 1:
            # Khi nổ Thần Thoại tự nhiên: 75% trúng nhân vật Rate-Up của Banner
            if self.rng.random() < 0.75:
                char = featured_char
            else:
                others = [c for c in tier_chars if c.id != featured_id]
                char = self.rng.choice(others)
        else:
            char = self.rng.choice(tier_chars)

        if rarity_rank(rarity) >= rarity_rank(PITY_MIN_RARITY):
            return char, 0
        return char, pity_counter + 1
