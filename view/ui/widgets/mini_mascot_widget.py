"""
Mini Mascot Widget - Backward Compatibility Proxy.
The mascot has been fully modularized into a dedicated MVC package at `view/ui/mascot/`:
- Model: view.ui.mascot.mascot_model.MascotModel
- View: view.ui.mascot.mascot_painter.MascotPainter
- Controller: view.ui.mascot.mascot_controller.MascotController
- Widget: view.ui.mascot.mascot_widget.MiniMascotWidget
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
