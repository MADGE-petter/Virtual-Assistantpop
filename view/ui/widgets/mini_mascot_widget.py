"""
Backward compatibility proxy for MiniMascotWidget.
The mascot has been refactored into a dedicated MVC package at `view.ui.mascot`.
"""

from view.ui.mascot import (
    MiniMascotWidget,
    MascotModel,
    MascotPainter,
    MascotController,
)

__all__ = [
    "MiniMascotWidget",
    "MascotModel",
    "MascotPainter",
    "MascotController",
]
