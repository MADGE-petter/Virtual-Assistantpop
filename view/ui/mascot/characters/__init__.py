"""Character renderers package."""

from typing import Optional
from service.collection.character_registry import CharacterDef
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.characters.png_skin_renderer import PngSkinRenderer
from view.ui.mascot.characters.vector_character_renderer import VectorCharacterRenderer


def create_renderer_for_character(char_def: Optional[CharacterDef]) -> BaseCharacterRenderer:
    """Factory creating appropriate renderer based on character definition."""
    if char_def is None or char_def.kind == "pop":
        from view.ui.mascot.characters.pop_renderer import PopRenderer
        return PopRenderer()
    if char_def.kind == "phoebe_chuby":
        from view.ui.mascot.characters.chubby_meme_renderer import ChubbyMemeRenderer
        return ChubbyMemeRenderer("phoebe")
    if char_def.kind == "nono_chubby":
        from view.ui.mascot.characters.chubby_meme_renderer import ChubbyMemeRenderer
        return ChubbyMemeRenderer("nono")
    if char_def.kind == "aemeath_idol":
        from view.ui.mascot.characters.pink_idol_renderer import PinkIdolRenderer
        return PinkIdolRenderer(char_def.skin_dir)
    if char_def.kind == "png" and char_def.skin_dir:
        return PngSkinRenderer(char_def.skin_dir)
    return VectorCharacterRenderer(char_def.spec)
