"""Mascot collection system (eggs, gacha, shop, inventory)."""

from service.collection.character_registry import (
    DEFAULT_CHARACTER_ID,
    RARITY_INFO,
    RARITY_ORDER,
    CharacterDef,
    CharacterRegistry,
)
from service.collection.collection_service import CollectionService, get_collection_service
from service.collection.gacha_engine import PITY_THRESHOLD, GachaEngine

__all__ = [
    "DEFAULT_CHARACTER_ID",
    "RARITY_INFO",
    "RARITY_ORDER",
    "CharacterDef",
    "CharacterRegistry",
    "CollectionService",
    "get_collection_service",
    "GachaEngine",
    "PITY_THRESHOLD",
]
