"""
Login Styles - Pop Assistant
Quản lý toàn bộ giao diện (CSS) cho màn hình đăng nhập
Deep dark theme with starfield effect
"""

MAIN_WINDOW_STYLE = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                           stop:0 #020408, stop:0.3 #070b14, stop:0.7 #090e1a, stop:1 #040710);
    }

    /* === INPUT FIELDS === */
    QLineEdit {
        background: transparent;
        border: 1px solid;
        border-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.30), stop:0.35 rgba(255, 255, 255, 0.12), stop:0.8 rgba(255, 255, 255, 0.04), stop:1 rgba(255, 255, 255, 0.01));
        border-radius: 10px;
        padding: 0px 14px;
        color: #FFFFFF;
        font-size: 12px;
        font-family: Arial, sans-serif;
        selection-background-color: rgba(0, 142, 255, 0.35);
    }
    QLineEdit:focus {
        border: 1px solid rgba(0, 255, 170, 0.6);
        background: rgba(255, 255, 255, 0.02);
    }
    QLineEdit:hover:!focus {
        border-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255, 255, 255, 0.55), stop:0.4 rgba(255, 255, 255, 0.22), stop:1 rgba(0, 255, 170, 0.10));
        background: rgba(255, 255, 255, 0.03);
    }
    QLineEdit::placeholder {
        color: rgba(120, 140, 165, 180);
    }

    /* === PRIMARY ACTION BUTTON === */
    QPushButton#action_btn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #008EFF, stop:1 #00FFAA);
        border: none;
        border-radius: 10px;
        color: #040812;
        font-size: 13px;
        font-weight: 700;
        font-family: Arial, sans-serif;
        letter-spacing: 0.5px;
        padding: 6px 20px;
    }
    QPushButton#action_btn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077D6, stop:1 #00E699);
        color: #000000;
    }
    QPushButton#action_btn:pressed {
        background: #00CC88;
        color: #000000;
    }
    
    QLabel {
        color: rgba(240, 245, 250, 220);
        font-size: 12px;
        font-family: Arial, sans-serif;
        padding: 0px;
    }
"""

TITLE_STYLE = """
    QLabel {
        color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #008EFF, stop:1 #00FFAA);
        font-size: 20px;
        font-weight: 800;
        font-family: Arial, sans-serif;
        text-align: center;
        letter-spacing: 1.2px;
        padding: 2px;
    }
"""

REGISTER_LABEL_STYLE = """
    QLabel {
        color: #00FFAA;
        font-size: 12px;
        font-family: Arial, sans-serif;
        padding: 6px;
        font-weight: 600;
    }
    QLabel:hover {
        color: #FFFFFF;
        text-decoration: underline;
    }
"""