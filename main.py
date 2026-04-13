# main.py
from PyQt6.QtWidgets import QApplication
from gui.main_app import WarrantyManagerApp, LoginWindow
from actions.db_actions import init_db
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    handler = RotatingFileHandler(logs_dir / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    # quieter noisy libs if needed:
    logging.getLogger("PyPDF2").setLevel(logging.WARNING)

if __name__ == '__main__':
    setup_logging()
    logging.info("Starting Warranty Manager")
    # Initialize database (creates tables, migrations, admin user)
    init_db()
    logging.info("Database initialized")

    app = QApplication(sys.argv)

    # Show login window first
    login_window = LoginWindow()
    if login_window.exec() == login_window.DialogCode.Accepted:
        window = WarrantyManagerApp(login_window.user)
        window.show()
        logging.info("Main window shown for user=%s role=%s", login_window.user["username"], login_window.user["role"])
        sys.exit(app.exec())
    else:
        logging.info("Login canceled/closed")
