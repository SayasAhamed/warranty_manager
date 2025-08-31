from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QSpacerItem, QSizePolicy, QMessageBox, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from actions.db_actions import check_user_credentials
import os

BUSINESS_LOGO_PATH = "assets/business_logo.png"
LOGIN_BG_PATH = "assets/login_bg.png"

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PC-Fix Warranty Manager Login")
        self.setFixedSize(800, 700)

        # ---------------- Background ----------------
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, 400, 350)
        if os.path.exists(LOGIN_BG_PATH):
            bg_pixmap = QPixmap(LOGIN_BG_PATH).scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.background_label.setPixmap(bg_pixmap)
        self.background_label.lower()

        # ---------------- Glassy Container ----------------
        container = QWidget(self)
        container.setGeometry(20, 20, 360, 310)
        container.setStyleSheet("""
            background-color: rgba(0, 0, 0, 120);  /* semi-transparent black */
            border-radius: 15px;
        """)
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(30, 20, 30, 20)

        # ---------------- Logo ----------------
        if os.path.exists(BUSINESS_LOGO_PATH):
            logo_pixmap = QPixmap(BUSINESS_LOGO_PATH).scaledToWidth(100, Qt.TransformationMode.SmoothTransformation)
            logo_label = QLabel()
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(logo_label)

        # ---------------- Title ----------------
        title_label = QLabel("Welcome to PC-Fix Warranty Manager")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #ffffff;
            margin-bottom: 15px;
        """)
        main_layout.addWidget(title_label)

        # ---------------- Username ----------------
        self.username_entry = QLineEdit()
        self.username_entry.setPlaceholderText("Username")
        self.username_entry.setStyleSheet("""
            padding: 6px 10px;
            border-radius: 10px;
            border: 1px solid #ccc;
            background-color: rgba(255, 255, 255, 180);
        """)
        main_layout.addWidget(self.username_entry)

        # ---------------- Password ----------------
        self.password_entry = QLineEdit()
        self.password_entry.setPlaceholderText("Password")
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_entry.setStyleSheet("""
            padding: 6px 10px;
            border-radius: 10px;
            border: 1px solid #ccc;
            background-color: rgba(255, 255, 255, 180);
        """)
        main_layout.addWidget(self.password_entry)

        # ---------------- Login Button ----------------
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.handle_login)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold;
                border-radius: 12px;
                padding: 8px 0;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        main_layout.addWidget(self.login_btn)

        # ---------------- Spacer ----------------
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # ---------------- Footer ----------------
        footer = QLabel("Developed By Sayas Mansoor © 2025")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("font-size: 12px; color: #ffffff;")
        main_layout.addWidget(footer)

        # ---------------- Variables & Shortcuts ----------------
        self.user = None
        self.username_entry.returnPressed.connect(self.handle_login)
        self.password_entry.returnPressed.connect(self.handle_login)
        self.username_entry.setFocus()

    # ---------------- Login Logic ----------------
    def handle_login(self):
        username = self.username_entry.text().strip().lower()
        password = self.password_entry.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password!")
            return

        user = check_user_credentials(username, password)
        if user:
            self.user = user
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", "Incorrect username or password.")
            self.password_entry.clear()
            self.password_entry.setFocus()
