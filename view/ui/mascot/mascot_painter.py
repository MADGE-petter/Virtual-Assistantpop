"""
Mascot Painter - Multi-Skin & Vector Rendering Engine for Desktop Mini Mascot.
Follows MVC architecture: delegates drawing to specific character renderers
(PopRenderer, VectorCharacterRenderer, PngSkinRenderer) based on equipped character.
"""

from typing import Optional
from PyQt6.QtGui import QPainter
from service.collection.character_registry import CharacterDef
from view.ui.mascot.characters import create_renderer_for_character
from view.ui.mascot.characters.base_character_renderer import BaseCharacterRenderer
from view.ui.mascot.characters.pop_renderer import PopRenderer
from view.ui.mascot.mascot_model import MascotModel


class MascotPainter:
    """Delegating painter engine supporting multiple collectible mascot skins."""

    def __init__(self, character: Optional[CharacterDef] = None):
        self._character: Optional[CharacterDef] = character
        self._renderer: BaseCharacterRenderer = create_renderer_for_character(character) if character else PopRenderer()

    @property
    def current_character(self) -> Optional[CharacterDef]:
        return self._character

    def set_character(self, character: Optional[CharacterDef]) -> None:
        """Switch active character skin renderer."""
        self._character = character
        self._renderer = create_renderer_for_character(character)

    def paint(self, painter: QPainter, width: int, height: int, model: MascotModel) -> None:
        """Delegate rendering to current character renderer."""
        if self._renderer:
            self._renderer.paint(painter, width, height, model)
