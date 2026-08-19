"""
Login Styles - Pop Assistant
Quản lý toàn bộ giao diện (CSS) cho màn hình đăng nhập
Deep dark theme with starfield effect
"""

MAIN_WINDOW_STYLE = """
    QDialog {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                           stop:0 #030508, stop:0.3 #080c14, stop:0.7 #0a0f1a, stop:1 #050810);
    }
    /* === INPUT FIELDS === */
    QLineEdit {
        background: rgba(5, 8, 14, 220);
        border: 1px solid rgba(0, 255, 170, 50);
        border-radius: 12px;
        padding: 0px 18px;
        color: #FFFFFF;
        font-size: 14px;
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        selection-background-color: rgba(0, 255, 170, 0.3);
    }
    QLineEdit:focus {
        border: 1px solid #00FFAA;
        background: rgba(8, 12, 20, 240);
    }
    QLineEdit:hover:!focus {
        border: 1px solid rgba(0, 255, 170, 90);
    }
    QLineEdit::placeholder {
        color: rgba(100, 115, 135, 180);
    }
    /* === PRIMARY BUTTON === */
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 rgba(0, 255, 170, 40), stop:1 rgba(0, 204, 255, 30));
        border: 1px solid rgba(0, 255, 170, 100);
        border-radius: 12px;
        color: #00FFAA;
        font-size: 14px;
        font-weight: 600;
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        letter-spacing: 0.5px;
        padding: 8px 24px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 rgba(0, 255, 170, 70), stop:1 rgba(0, 204, 255, 60));
        border: 1px solid #00FFAA;
        color: #FFFFFF;
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 rgba(0, 204, 255, 80), stop:1 rgba(0, 255, 170, 90));
        border: 1px solid #00CCFF;
        color: #FFFFFF;
        padding-top: 10px;
        padding-bottom: 6px;
    }
    QPushButton:disabled {
        background: rgba(20, 28, 40, 150);
        border: 1px solid rgba(40, 52, 70, 100);
        color: rgba(100, 115, 135, 180);
    }
    QLabel {
        color: rgba(240, 245, 250, 220);
        font-size: 13px;
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        padding: 0px;
    }
    /* Starfield container */
    QWidget#starfield {
        background: transparent;
    }
"""

TITLE_STYLE = """
    QLabel {
        color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #00ffaa, stop:1 #00ccff);
        font-size: 32px;
        font-weight: 300;
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        text-align: center;
        padding: 20px;
    }
"""

REGISTER_LABEL_STYLE = """
    QLabel {
        color: rgba(0, 255, 136, 200);
        font-size: 13px;
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        padding: 10px;
        font-weight: 500;
    }
"""