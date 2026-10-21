"""
POP UI Styles & Design System Tokens matching image po (DESIGN TOKENS & STYLESHEETS).
Transparent glassmorphic panels with top-to-bottom white gradient borders and Blue-Green accents.
"""


class DesignTokens:
    """Color palette, gradients, typography scales, and geometric tokens."""

    # Colors - Deep cosmic slate dark theme
    BG_BASE = "#070B14"
    SURFACE_1 = "transparent"
    SURFACE_2 = "rgba(19, 28, 48, 0.70)"
    SURFACE_3 = "rgba(26, 38, 64, 0.85)"
    BORDER = "rgba(255, 255, 255, 0.08)"
    BORDER_SUBTLE = "rgba(255, 255, 255, 0.05)"

    # White gradient top specular border (Gờ sáng trắng phối từ trên xuống dưới)
    BORDER_GRADIENT = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.30), stop:0.35 rgba(255, 255, 255, 0.12), stop:0.8 rgba(255, 255, 255, 0.04), stop:1 rgba(255, 255, 255, 0.01))"
    BORDER_GRADIENT_HOVER = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.55), stop:0.4 rgba(255, 255, 255, 0.22), stop:1 rgba(0, 255, 170, 0.10))"

    # Blue & Green Brand Gradient (Xanh dương & Xanh lá)
    COLOR_BLUE = "#008EFF"
    COLOR_GREEN = "#00FFAA"
    GRADIENT_BLUE_GREEN = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #008EFF, stop:1 #00FFAA)"
    GRADIENT_BLUE_GREEN_DIAG = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA)"

    # Text hierarchy - modern slate & crisp whites
    TEXT_MAIN = "#FFFFFF"
    TEXT_PRIMARY = "#00FFAA"
    TEXT_SECONDARY = "#94A3B8"
    TEXT_MUTED = "#64748B"

    # Accents & Gradients
    CYAN = "#00FFAA"
    CYAN_ACCENT = "#00FFAA"
    BLUE_ACCENT = "#008EFF"
    PURPLE_ACCENT = "#7C3AED"
    PINK_ACCENT = "#A855F7"
    CORAL_ACCENT = "#F43F5E"

    # Glow & Transparency
    GLOW_CYAN = "rgba(0, 255, 170, 0.18)"
    GLOW_PURPLE = "rgba(124, 58, 237, 0.18)"
    BORDER_GLOW = "rgba(0, 255, 170, 0.28)"

    # Fonts
    FONT_FAMILY = "Arial, Helvetica, sans-serif"


STYLE_SHEET = f"""
/* Global Reset & Base */
QWidget {{
    background: transparent;
    color: {DesignTokens.TEXT_MAIN};
    font-family: {DesignTokens.FONT_FAMILY};
    font-size: 13px;
}}

QMainWindow {{
    background-color: {DesignTokens.BG_BASE};
}}

/* ScrollBars */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: rgba(148, 163, 184, 0.22);
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: rgba(0, 255, 170, 0.45);
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    height: 6px;
}}
QScrollBar::handle:horizontal {{
    background: rgba(148, 163, 184, 0.22);
    border-radius: 3px;
}}

/* Tooltips */
QToolTip {{
    background-color: #000000;
    color: #FFFFFF;
    border: 1px solid;
    border-color: {DesignTokens.BORDER_GRADIENT};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* Buttons */
QPushButton {{
    background: transparent;
    color: #FFFFFF;
    border: 1px solid;
    border-color: {DesignTokens.BORDER_GRADIENT};
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 500;
}}
QPushButton:hover {{
    background: rgba(255, 255, 255, 0.05);
    border-color: {DesignTokens.BORDER_GRADIENT_HOVER};
    color: #FFFFFF;
}}
QPushButton:pressed {{
    background: rgba(255, 255, 255, 0.02);
}}

/* Primary Glow Button (Blue & Green Gradient) */
QPushButton#primaryButton {{
    background: {DesignTokens.GRADIENT_BLUE_GREEN};
    color: #040812;
    border: none;
    font-weight: 700;
    border-radius: 8px;
}}
QPushButton#primaryButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077D6, stop:1 #00E699);
}}

/* Line Edit / Text Input */
QLineEdit, QTextEdit {{
    background: transparent;
    color: #FFFFFF;
    border: 1px solid;
    border-color: {DesignTokens.BORDER_GRADIENT};
    border-radius: 10px;
    padding: 8px 12px;
    selection-background-color: rgba(0, 142, 255, 0.4);
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid rgba(0, 255, 170, 0.5);
    background: rgba(255, 255, 255, 0.02);
}}

/* Combo Box */
QComboBox {{
    background: transparent;
    color: #FFFFFF;
    border: 1px solid;
    border-color: {DesignTokens.BORDER_GRADIENT};
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 500;
}}
QComboBox:hover {{
    border-color: {DesignTokens.BORDER_GRADIENT_HOVER};
    background: rgba(255, 255, 255, 0.04);
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: none;
}}
QComboBox QAbstractItemView {{
    background-color: #000000;
    color: #FFFFFF;
    border: 1px solid;
    border-color: {DesignTokens.BORDER_GRADIENT};
    selection-background-color: rgba(0, 255, 170, 0.15);
    selection-color: #00FFAA;
    border-radius: 8px;
    padding: 4px;
}}
"""


def init_fonts():
    """Apply global font (Arial) to QApplication."""
    try:
        from PyQt6.QtGui import QFont
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app:
            app.setFont(QFont("Arial", 10))
            return True
        return False
    except Exception as e:
        print(f"[Styles] Failed to set font: {e}")
        return False

