from gui.main_app import WarrantyManagerApp, LoginWindow
from actions.db_actions import init_db
from PyQt6.QtWidgets import QApplication
import sys

if __name__ == '__main__':
    # Initialize database (creates tables if not exists)
    init_db()

    app = QApplication(sys.argv)

    # Show login window first
    login_window = LoginWindow()
    if login_window.exec() == login_window.DialogCode.Accepted:
        # If login successful, launch main app with logged-in user info
        window = WarrantyManagerApp(login_window.user)
        window.show()
        sys.exit(app.exec())
