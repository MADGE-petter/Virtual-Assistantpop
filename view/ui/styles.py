"""
POP UI Styles & Design System Tokens matching image po (DESIGN TOKENS & STYLESHEETS).
"""


class DesignTokens:
    """Color palette, gradients, typography scales, and geometric tokens."""

    # Colors
    BG_BASE = "#03050B"
    SURFACE_1 = "#080F16"
    SURFACE_2 = "#10161F"
    SURFACE_3 = "#151C27"
    BORDER = "#1E2634"

    TEXT_PRIMARY = "#6BEEFF"
    TEXT_MAIN = "#E6F4FF"
    TEXT_SECONDARY = "#96D7E9"
    TEXT_MUTED = "#557088"

    # Accents & Gradients
    CYAN = "#00FFFF"
    CYAN_ACCENT = "#00FFAA"
    BLUE_ACCENT = "#008EFF"
    PURPLE_ACCENT = "#7C3CFF"
    PINK_ACCENT = "#B14DFF"
    CORAL_ACCENT = "#FF4B6E"

    # Glow & Transparency
    GLOW_CYAN = "rgba(0, 255, 255, 0.25)"
    GLOW_PURPLE = "rgba(124, 60, 255, 0.25)"
    BORDER_GLOW = "rgba(0, 255, 255, 0.4)"

    # Fonts
    FONT_FAMILY = "Segoe UI, Inter, -apple-system, BlinkMacSystemFont, sans-serif"


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
    background: rgba(30, 38, 52, 0.8);
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: rgba(0, 255, 255, 0.4);
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
    background: rgba(30, 38, 52, 0.8);
    border-radius: 3px;
}}

/* Tooltips */
QToolTip {{
    background-color: {DesignTokens.SURFACE_2};
    color: {DesignTokens.TEXT_MAIN};
    border: 1px solid {DesignTokens.BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* Buttons */
QPushButton {{
    background-color: {DesignTokens.SURFACE_2};
    color: {DesignTokens.TEXT_MAIN};
    border: 1px solid {DesignTokens.BORDER};
    border-radius: 8px;
    padding: 6px 12px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {DesignTokens.SURFACE_3};
    border-color: rgba(0, 255, 255, 0.4);
    color: #FFFFFF;
}}
QPushButton:pressed {{
    background-color: {DesignTokens.SURFACE_1};
}}

/* Primary Glow Button */
QPushButton#primaryButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA);
    color: #03050B;
    border: none;
    font-weight: 600;
    border-radius: 8px;
}}
QPushButton#primaryButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00A6FF, stop:1 #33FFBC);
}}

/* Line Edit / Text Input */
QLineEdit, QTextEdit {{
    background-color: {DesignTokens.SURFACE_2};
    color: {DesignTokens.TEXT_MAIN};
    border: 1px solid {DesignTokens.BORDER};
    border-radius: 10px;
    padding: 8px 12px;
    selection-background-color: {DesignTokens.PURPLE_ACCENT};
}}
QLineEdit:focus, QTextEdit:focus {{
    border: 1px solid {DesignTokens.CYAN};
    background-color: {DesignTokens.SURFACE_3};
}}

/* Combo Box */
QComboBox {{
    background-color: rgba(8, 15, 22, 0.85);
    color: {DesignTokens.TEXT_MAIN};
    border: 1px solid {DesignTokens.BORDER};
    border-radius: 18px;
    padding: 5px 14px;
    font-size: 13px;
    font-weight: 500;
}}
QComboBox:hover {{
    border-color: {DesignTokens.CYAN};
    background-color: {DesignTokens.SURFACE_2};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: none;
}}
QComboBox QAbstractItemView {{
    background-color: {DesignTokens.SURFACE_2};
    color: {DesignTokens.TEXT_MAIN};
    border: 1px solid {DesignTokens.BORDER};
    selection-background-color: {DesignTokens.SURFACE_3};
    selection-color: {DesignTokens.CYAN};
    border-radius: 8px;
    padding: 4px;
}}
"""
