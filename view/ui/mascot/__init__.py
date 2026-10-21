"""
Mascot Module - Package containing MVC components for Desktop Mini Mascot.
"""

from view.ui.mascot.mascot_model import MascotModel
from view.ui.mascot.mascot_painter import MascotPainter
from view.ui.mascot.mascot_controller import MascotController
from view.ui.mascot.mascot_widget import MiniMascotWidget

__all__ = [
    "MiniMascotWidget",
    "MascotModel",
    "MascotPainter",
    "MascotController",
]
