"""Base Character Renderer - Common interface and utilities for all mascot skins."""

from abc import ABC, abstractmethod
from PyQt6.QtGui import QPainter
from view.ui.mascot.mascot_model import MascotModel


class BaseCharacterRenderer(ABC):
    """Abstract renderer interface for desktop mascot characters."""

    @abstractmethod
    def paint(self, painter: QPainter, width: int, height: int, model: MascotModel) -> None:
        """Render character on QPainter according to current model state."""
        pass
