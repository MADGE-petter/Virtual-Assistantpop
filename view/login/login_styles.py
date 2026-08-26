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
        background: rgba(6, 10, 18, 230);
        border: 1px solid rgba(0, 255, 170, 0.25);
        border-radius: 10px;
        padding: 0px 14px;
        color: #FFFFFF;
        font-size: 12px;
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        selection-background-color: rgba(0, 255, 170, 0.3);
    }
    QLineEdit:focus {
        border: 1px solid #00FFAA;
        background: rgba(10, 16, 26, 250);
        box-shadow: 0 0 10px rgba(0, 255, 170, 0.4);
    }
    QLineEdit:hover:!focus {
        border: 1px solid rgba(0, 255, 170, 0.5);
    }
    QLineEdit::placeholder {
        color: rgba(120, 140, 165, 180);
    }

    /* === PRIMARY ACTION BUTTON === */
    QPushButton#action_btn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 rgba(0, 255, 170, 0.8), stop:1 rgba(0, 204, 255, 0.8));
        border: 1px solid #00FFAA;
        border-radius: 10px;
        color: #050B14;
        font-size: 13px;
        font-weight: 700;
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        letter-spacing: 0.5px;
        padding: 6px 20px;
    }
    QPushButton#action_btn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 rgba(0, 255, 170, 1.0), stop:1 rgba(0, 204, 255, 1.0));
        border: 1px solid #FFFFFF;
        color: #000000;
    }
    QPushButton#action_btn:pressed {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                           stop:0 rgba(0, 204, 255, 0.9), stop:1 rgba(0, 255, 170, 0.9));
        color: #000000;
    }
    
    QLabel {
        color: rgba(240, 245, 250, 220);
        font-size: 12px;
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        padding: 0px;
    }
"""

TITLE_STYLE = """
    QLabel {
        color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                           stop:0 #00FFAA, stop:1 #00CCFF);
        font-size: 20px;
        font-weight: 800;
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        text-align: center;
        letter-spacing: 1.2px;
        padding: 2px;
    }
"""

REGISTER_LABEL_STYLE = """
    QLabel {
        color: rgba(0, 255, 200, 210);
        font-size: 12px;
        font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        padding: 6px;
        font-weight: 600;
    }
    QLabel:hover {
        color: #00FFAA;
        text-decoration: underline;
    }
"""