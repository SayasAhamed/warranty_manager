# gui/main_app.py
from __future__ import annotations

import os
import shutil
import platform
import subprocess
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QFileDialog, QTabWidget, QVBoxLayout,
    QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox, QScrollArea, QSpacerItem,
    QSizePolicy, QGridLayout, QApplication, QDialog, QDateEdit, QInputDialog
)
from PyQt6.QtGui import QPixmap, QIcon, QCursor, QAction, QKeySequence
from PyQt6.QtCore import Qt, QDate

from actions.db_actions import (
    get_all_invoices, get_invoice_pdf_path, delete_invoice_by_id,
    get_all_users, create_user, delete_user,
    verify_security_answers, update_user_password, update_username,
    check_user_credentials
)
from actions.invoice_actions import add_invoice
from actions.warranty_actions import (
    mark_as_paid, mark_warranty_ended, calculate_warranty_period, run_warranty_maintenance
)

#----------------- Helper for exe path -----------------
def resource_path(relative_path: str) -> str:
    try:
        base_path = getattr(__import__('sys'), "_MEIPASS")  # type: ignore[attr-defined]
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ---------------- Assets ----------------
BUSINESS_LOGO_PATH = resource_path('assets/business_logo.png')
PDF_ICON_PATH = resource_path('assets/pdf_icon.png')
BACKGROUND_IMAGE_PATH = resource_path("assets/main_bg.png")
DEFAULT_ICON = PDF_ICON_PATH if os.path.exists(PDF_ICON_PATH) else BUSINESS_LOGO_PATH


# ---------------- PDF OPEN ----------------
def open_pdf_file(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found: {path}")
    if platform.system() == "Windows":
        os.startfile(os.path.abspath(path))  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":  # macOS
        subprocess.Popen(["open", os.path.abspath(path)])
    else:  # Linux
        subprocess.Popen(["xdg-open", os.path.abspath(path)])


# ---------------- Login Window ----------------
class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PC-Fix Warranty Manager Login")
        self.setFixedSize(820, 700)

        # Background
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 820, 700)
        if os.path.exists(BACKGROUND_IMAGE_PATH):
            bg_pix = QPixmap(BACKGROUND_IMAGE_PATH).scaled(
                self.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.bg_label.setPixmap(bg_pix)
        self.bg_label.lower()

        # Glassy container
        container = QWidget(self)
        container.setGeometry(80, 80, 660, 520)
        container.setStyleSheet("""
            QWidget { background-color: rgba(0,0,0,140); border-radius: 18px; }
            QLabel { color: #E9EEF5; }
            QLineEdit {
                padding:10px; border-radius:12px;
                background-color: rgba(255,255,255,210);
                color:#0f172a;
            }
            QLineEdit::placeholder { color:#6b7280; }
            QPushButton {
                font-weight: 600; border-radius:12px; padding:10px 16px;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(14)

        # Logo
        if os.path.exists(BUSINESS_LOGO_PATH):
            logo = QLabel()
            logo_pix = QPixmap(BUSINESS_LOGO_PATH).scaledToWidth(
                150, Qt.TransformationMode.SmoothTransformation
            )
            logo.setPixmap(logo_pix)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo)

        # Title
        title = QLabel("Welcome to PC-Fix Warranty Manager")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #FFD54A; margin-bottom: 6px;")
        layout.addWidget(title)

        # Username & Password
        self.username_entry = QLineEdit()
        self.username_entry.setPlaceholderText("Username")
        layout.addWidget(self.username_entry)

        self.password_entry = QLineEdit()
        self.password_entry.setPlaceholderText("Password")
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_entry)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_login = QPushButton("Login")
        self.btn_login.clicked.connect(self.attempt_login)
        self.btn_login.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_login.setStyleSheet("""
            QPushButton { background-color:#4CAF50; color:white; }
            QPushButton:hover { background-color:#45a049; }
        """)
        btn_layout.addWidget(self.btn_login)

        self.btn_forgot = QPushButton("Forgot Password?")
        self.btn_forgot.clicked.connect(self.open_forgot_password)
        self.btn_forgot.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_forgot.setStyleSheet("""
            QPushButton { background-color:#f44336; color:white; }
            QPushButton:hover { background-color:#e53935; }
        """)
        btn_layout.addWidget(self.btn_forgot)

        layout.addLayout(btn_layout)

        # Spacer + footer
        layout.addStretch(1)
        footer = QLabel("Developed By Sayas Mansoor © 2026")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("font-size: 12px; color: #E9EEF5;")
        layout.addWidget(footer)

        self.user = None
        self.username_entry.returnPressed.connect(self.attempt_login)
        self.password_entry.returnPressed.connect(self.attempt_login)
        self.username_entry.setFocus()

    def attempt_login(self):
        username = self.username_entry.text().strip().lower()
        password = self.password_entry.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.")
            return
        user = check_user_credentials(username, password)
        if user:
            self.user = user
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

    def open_forgot_password(self):
        dialog = ForgotPasswordDialog()
        dialog.exec()


# ---------------- Forgot Password Dialog ----------------
class ForgotPasswordDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forgot Password")
        self.setFixedSize(420, 260)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Enter your username:"))
        self.username_entry = QLineEdit()
        layout.addWidget(self.username_entry)
        layout.addWidget(QLabel("Answer to Security Question 1:"))
        self.answer1 = QLineEdit()
        layout.addWidget(self.answer1)
        layout.addWidget(QLabel("Answer to Security Question 2:"))
        self.answer2 = QLineEdit()
        layout.addWidget(self.answer2)
        self.btn_verify = QPushButton("Verify & Reset Password")
        self.btn_verify.clicked.connect(self.verify_answers)
        layout.addWidget(self.btn_verify)
        self.setLayout(layout)

    def verify_answers(self):
        user_id = verify_security_answers(
            self.username_entry.text().strip(),
            self.answer1.text().strip(),
            self.answer2.text().strip()
        )
        if user_id:
            new_pass, ok = QInputDialog.getText(self, "Reset Password", "Enter new password:")
            if ok and new_pass.strip():
                update_user_password(user_id, new_pass.strip())
                QMessageBox.information(self, "Success", "Password reset successfully!")
                self.accept()
        else:
            QMessageBox.warning(self, "Error", "Incorrect username or security answers.")


# ---------------- Warranty Calculator ----------------
class WarrantyCalculatorWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warranty Calculator")
        self.setMinimumSize(420, 220)
        layout = QGridLayout()
        layout.addWidget(QLabel("Warranty Start (DD-MM-YYYY):"), 0, 0)
        self.calc_start_entry = QDateEdit()
        self.calc_start_entry.setCalendarPopup(True)
        self.calc_start_entry.setDisplayFormat("dd-MM-yyyy")
        self.calc_start_entry.setDate(QDate.currentDate())
        layout.addWidget(self.calc_start_entry, 0, 1)
        layout.addWidget(QLabel("Duration (Days):"), 1, 0)
        self.calc_duration_entry = QLineEdit()
        self.calc_duration_entry.setPlaceholderText("e.g. 365")
        layout.addWidget(self.calc_duration_entry, 1, 1)
        self.calc_btn = QPushButton("Calculate Warranty")
        layout.addWidget(self.calc_btn, 2, 0, 1, 2)
        self.calc_output = QLabel("")
        self.calc_output.setStyleSheet("font-weight:bold;color:#0D47A1;")
        self.calc_output.setWordWrap(True)
        layout.addWidget(self.calc_output, 3, 0, 1, 2)
        self.setLayout(layout)
        self.calc_btn.clicked.connect(self.calculate_warranty)

    def calculate_warranty(self):
        start_qdate = self.calc_start_entry.date()
        start_date = start_qdate.toPyDate()
        duration_text = self.calc_duration_entry.text().strip()
        if not duration_text:
            QMessageBox.warning(self, "Input Error", "Please enter warranty duration in days.")
            return
        try:
            duration = int(duration_text)
            if duration < 0:
                raise ValueError("Duration cannot be negative.")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Duration must be a non-negative integer (days).")
            return
        end_date_obj = start_date + timedelta(days=duration)
        today = datetime.today().date()
        if end_date_obj >= today:
            days_remaining = (end_date_obj - today).days
            days_str = f"{days_remaining} day(s) remaining"
            active = True
        else:
            days_over = (today - end_date_obj).days
            days_str = f"Expired {days_over} day(s) ago"
            active = False
        end_date_fmt = end_date_obj.strftime("%d-%m-%Y")
        status = "Active" if active else "Expired"
        self.calc_output.setText(f"Warranty End: {end_date_fmt}  |  {days_str}  |  {status}")


# ---------------- Main App ----------------
class WarrantyManagerApp(QWidget):
    def __init__(self, logged_in_user):
        super().__init__()
        self.logged_in_user = logged_in_user
        self.setWindowTitle(f"Warranty Manager - {logged_in_user['username']} ({logged_in_user['role']})")
        self.resize(1120, 760)
        self.imported_pdf_path = None
        self._updating_check = False  # prevents recursive selection<->check loops
        self.init_ui()
        self.load_data()
        self._setup_shortcuts()

    # --- UI Initialization ---
    def init_ui(self):
        # Background
        self.bg = QLabel(self)
        self.bg.setGeometry(0, 0, self.width(), self.height())
        if os.path.exists(BACKGROUND_IMAGE_PATH):
            self.bg.setPixmap(QPixmap(BACKGROUND_IMAGE_PATH).scaled(
                self.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        self.bg.lower()

        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab { padding: 8px 16px; font-weight: 700; color:#E9EEF5; }
            QTabBar::tab:selected { background: #1f2937; }
            QTabWidget::pane { border: 1px solid #94a3b8; border-radius: 10px; }
        """)

        # Add Invoice Tab
        self.tab_add_invoice = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setStyleSheet("""
            QWidget { background-color: rgba(255,255,255,225); border-radius: 14px; }
            QLabel { color:#111827; }
            QLineEdit { color:#111827; }
            QLineEdit::placeholder { color:#6b7280; }
            QPushButton { font-weight: 700; }
        """)
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(14)
        scroll_layout.setContentsMargins(20, 20, 20, 20)

        if os.path.exists(BUSINESS_LOGO_PATH):
            pixmap = QPixmap(BUSINESS_LOGO_PATH).scaledToWidth(200)
            logo_label = QLabel()
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_layout.addWidget(logo_label)

        title_label = QLabel("PC-Fix - Warranty Manager")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 22px; font-weight: 900; margin-bottom: 10px; color:#1f2937;")
        scroll_layout.addWidget(title_label)

        def add_form_row(label_text, widget):
            container = QHBoxLayout()
            label = QLabel(label_text)
            label.setMinimumWidth(200)
            container.addWidget(label)
            container.addWidget(widget)
            container.setSpacing(10)
            return container

        # Shared input style (padding + DARK calendar/nav text)
        common_input_style = """
            QLineEdit, QDateEdit {
                color: black;
                background-color: white;
                padding: 6px 10px;
                border: 1px solid #ccc;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit::placeholder { color: #666; }
            /* Calendar popup */
            QCalendarWidget QWidget { background-color: white; }
            QCalendarWidget QAbstractItemView {
                color: black;                    /* day numbers */
                selection-background-color: #4CAF50;
                selection-color: white;
                font-size: 12px;
            }
            QCalendarWidget QToolButton {        /* month & nav arrows */
                color: #111111;                  /* <-- dark month text */
                background: #E5E7EB;
                border-radius: 6px;
                padding: 4px 8px;
                font-weight: 700;
            }
            QCalendarWidget QSpinBox {           /* year spinbox text */
                color: #111111;
                background: white;
                border: none;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar { background: #E5E7EB; }
        """

        self.entry_invoice_id = QLineEdit()
        self.entry_invoice_id.setStyleSheet(common_input_style)
        scroll_layout.addLayout(add_form_row("Invoice ID (Required):", self.entry_invoice_id))

        self.entry_customer = QLineEdit()
        self.entry_customer.setPlaceholderText("Customer Name")
        self.entry_customer.setStyleSheet(common_input_style)
        scroll_layout.addLayout(add_form_row("Customer Name:", self.entry_customer))

        self.entry_invoice_date = QDateEdit()
        self.entry_invoice_date.setCalendarPopup(True)
        self.entry_invoice_date.setDate(QDate.currentDate())
        self.entry_invoice_date.setDisplayFormat("yyyy-MM-dd")
        self.entry_invoice_date.setStyleSheet(common_input_style)
        scroll_layout.addLayout(add_form_row("Invoice Date:", self.entry_invoice_date))

        self.entry_warranty_start = QDateEdit()
        self.entry_warranty_start.setCalendarPopup(True)
        self.entry_warranty_start.setDate(QDate.currentDate())
        self.entry_warranty_start.setDisplayFormat("yyyy-MM-dd")
        self.entry_warranty_start.setStyleSheet(common_input_style)
        scroll_layout.addLayout(add_form_row("Warranty Start:", self.entry_warranty_start))

        self.entry_warranty_duration = QLineEdit()
        self.entry_warranty_duration.setPlaceholderText("Duration in Days")
        self.entry_warranty_duration.setStyleSheet(common_input_style)
        scroll_layout.addLayout(add_form_row("Warranty Duration:", self.entry_warranty_duration))

        # PDF Import controls
        pdf_container = QHBoxLayout()

        self.btn_import_pdf = QPushButton("Import Invoice PDF(s)")
        self.btn_import_pdf.clicked.connect(self.import_invoice_pdf)
        self.btn_import_pdf.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_import_pdf.setStyleSheet("""
            QPushButton { background-color:#2563EB; color:#F8FAFC; border-radius:10px; padding:10px 14px; }
            QPushButton:hover { background-color:#1D4ED8; }
        """)
        pdf_container.addWidget(self.btn_import_pdf)

        self.pdf_name_label = QLabel("No files selected")
        self.pdf_name_label.setStyleSheet("color:#111827;")
        self.pdf_name_label.setMinimumWidth(300)
        pdf_container.addWidget(self.pdf_name_label)

        self.btn_remove_pdf = QPushButton("Remove PDF")
        self.btn_remove_pdf.setEnabled(False)
        self.btn_remove_pdf.clicked.connect(self.remove_imported_pdf)
        self.btn_remove_pdf.setStyleSheet("""
            QPushButton { background-color:#DC2626; color:#F8FAFC; border-radius:10px; padding:10px 14px; }
            QPushButton:hover { background-color:#B91C1C; }
        """)
        pdf_container.addWidget(self.btn_remove_pdf)
        scroll_layout.addLayout(pdf_container)

        self.btn_add_invoice = QPushButton("Add Invoice")
        self.btn_add_invoice.setStyleSheet("""
            QPushButton { background-color: #22C55E; color: white; font-weight: bold; border-radius: 10px; padding: 12px 16px; }
            QPushButton:hover { background-color: #16A34A; }
        """)
        self.btn_add_invoice.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_add_invoice.clicked.connect(self.add_invoice)
        scroll_layout.addWidget(self.btn_add_invoice)

        scroll_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        scroll_area.setWidget(scroll_content)
        add_layout = QVBoxLayout()
        add_layout.addWidget(scroll_area)
        self.tab_add_invoice.setLayout(add_layout)
        self.tabs.addTab(self.tab_add_invoice, "Add Invoice")

        # --- All Invoices & Warranty ---
        self.tab_overall = QWidget()
        overall_layout = QVBoxLayout()
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet("""
            QListWidget { background-color: rgba(31,41,55,0.85); color:#F8FAFC; border-radius:10px; }
        """)
        overall_layout.addWidget(self.sub_tabs)
        self.tab_overall.setLayout(overall_layout)
        self.tabs.addTab(self.tab_overall, "All Invoices & Warranty")

        # Paid invoices
        self.tab_paid = QWidget()
        self.paid_list = QListWidget()
        self.paid_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.paid_list.setStyleSheet("QListWidget { font-size: 15px; }")
        self.paid_list.itemChanged.connect(self._sync_selection_from_check)
        btn_view_paid = QPushButton("View PDF")
        btn_view_paid.clicked.connect(lambda: self.view_pdf_from_list(self.paid_list))
        btn_delete_paid = QPushButton("Delete")
        btn_delete_paid.clicked.connect(lambda: self.delete_selected_invoice(self.paid_list))
        paid_btn_layout = QVBoxLayout()
        paid_btn_layout.addWidget(btn_view_paid)
        paid_btn_layout.addWidget(btn_delete_paid)
        paid_btn_layout.addStretch()
        paid_layout = QHBoxLayout()
        paid_layout.addWidget(self.paid_list)
        paid_layout.addLayout(paid_btn_layout)
        self.tab_paid.setLayout(paid_layout)
        self.sub_tabs.addTab(self.tab_paid, "Invoice Paid")

        # Non-Paid invoices
        self.tab_non_paid = QWidget()
        self.non_paid_list = QListWidget()
        self.non_paid_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.non_paid_list.setStyleSheet("QListWidget { font-size: 15px; }")
        self.non_paid_list.itemChanged.connect(self._sync_selection_from_check)
        btn_mark_paid = QPushButton("Mark as Paid")
        btn_mark_paid.clicked.connect(self.mark_selected_paid)
        btn_view_non_paid = QPushButton("View PDF")
        btn_view_non_paid.clicked.connect(lambda: self.view_pdf_from_list(self.non_paid_list))
        btn_delete_non_paid = QPushButton("Delete")
        btn_delete_non_paid.clicked.connect(lambda: self.delete_selected_invoice(self.non_paid_list))
        non_paid_btn_layout = QVBoxLayout()
        non_paid_btn_layout.addWidget(btn_mark_paid)
        non_paid_btn_layout.addWidget(btn_view_non_paid)
        non_paid_btn_layout.addWidget(btn_delete_non_paid)
        non_paid_btn_layout.addStretch()
        non_paid_layout = QHBoxLayout()
        non_paid_layout.addWidget(self.non_paid_list)
        non_paid_layout.addLayout(non_paid_btn_layout)
        self.tab_non_paid.setLayout(non_paid_layout)
        self.sub_tabs.addTab(self.tab_non_paid, "Invoice Non-Paid")

        # Warranty sub-tabs
        self.tab_warranty = QWidget()
        warranty_layout = QVBoxLayout()
        self.warranty_tabs = QTabWidget()
        self.warranty_tabs.setStyleSheet("""
            QListWidget { background-color: rgba(31,41,55,0.85); color:#F8FAFC; border-radius:10px; font-size:15px; }
        """)

        # Warranty Ended
        self.tab_warranty_ended = QWidget()
        self.warranty_ended_list = QListWidget()
        self.warranty_ended_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.warranty_ended_list.itemChanged.connect(self._sync_selection_from_check)
        self.tab_warranty_ended.setStyleSheet("QWidget { background-color: rgba(128,0,0,0.25); }")
        ended_layout = QHBoxLayout()
        ended_btn_layout = QVBoxLayout()
        btn_add_seal = QPushButton("Add End Seal")
        btn_add_seal.clicked.connect(self.add_warranty_ended_seal)
        btn_view_ended = QPushButton("View PDF")
        btn_view_ended.clicked.connect(lambda: self.view_pdf_from_list(self.warranty_ended_list))
        btn_delete_ended = QPushButton("Delete")
        btn_delete_ended.clicked.connect(lambda: self.delete_selected_invoice(self.warranty_ended_list))
        ended_btn_layout.addWidget(btn_add_seal)
        ended_btn_layout.addWidget(btn_view_ended)
        ended_btn_layout.addWidget(btn_delete_ended)
        ended_btn_layout.addStretch()
        ended_layout.addWidget(self.warranty_ended_list)
        ended_layout.addLayout(ended_btn_layout)
        self.tab_warranty_ended.setLayout(ended_layout)

        # Under Warranty
        self.tab_warranty_under = QWidget()
        self.warranty_under_list = QListWidget()
        self.warranty_under_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.warranty_under_list.itemChanged.connect(self._sync_selection_from_check)
        self.tab_warranty_under.setStyleSheet("QWidget { background-color: rgba(0,100,0,0.25); }")
        under_layout = QHBoxLayout()
        under_btn_layout = QVBoxLayout()
        btn_view_under = QPushButton("View PDF")
        btn_view_under.clicked.connect(lambda: self.view_pdf_from_list(self.warranty_under_list))
        btn_delete_under = QPushButton("Delete")
        btn_delete_under.clicked.connect(lambda: self.delete_selected_invoice(self.warranty_under_list))
        under_btn_layout.addWidget(btn_view_under)
        under_btn_layout.addWidget(btn_delete_under)
        under_btn_layout.addStretch()
        under_layout.addWidget(self.warranty_under_list)
        under_layout.addLayout(under_btn_layout)
        self.tab_warranty_under.setLayout(under_layout)

        self.warranty_tabs.addTab(self.tab_warranty_ended, "Warranty Ended")
        self.warranty_tabs.addTab(self.tab_warranty_under, "Under Warranty")
        warranty_layout.addWidget(self.warranty_tabs)
        self.tab_warranty.setLayout(warranty_layout)
        self.sub_tabs.addTab(self.tab_warranty, "Warranty Period")

        # Calculator tab
        self.tab_calculator = QWidget()
        calc_layout = QVBoxLayout()
        btn_open_float = QPushButton("Open Warranty Calculator")
        btn_open_float.clicked.connect(self.open_calculator_window)
        calc_layout.addWidget(btn_open_float)
        calc_layout.addStretch()
        self.tab_calculator.setLayout(calc_layout)
        self.tabs.addTab(self.tab_calculator, "Warranty Calculator")

        # Admin tab
        if self.logged_in_user['role'] == 'admin':
            self.tab_admin = QWidget()
            admin_layout = QVBoxLayout()

            header = QLabel("Registered Users:")
            header.setStyleSheet("color:#E9EEF5; font-weight:700;")
            admin_layout.addWidget(header)

            self.user_list = QListWidget()
            self.user_list.setStyleSheet("QListWidget { background-color: rgba(31,41,55,0.90); color:#F8FAFC; border-radius:10px; font-size:15px; }")
            self.user_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
            admin_layout.addWidget(self.user_list)

            btn_row = QHBoxLayout()
            self.btn_add_user = QPushButton("Add User")
            self.btn_add_user.clicked.connect(self.add_user)

            self.btn_edit_username = QPushButton("Edit Username")
            self.btn_edit_username.clicked.connect(self.edit_selected_username)

            self.btn_reset_password = QPushButton("Reset Password")
            self.btn_reset_password.clicked.connect(self.reset_selected_password)

            self.btn_delete_user = QPushButton("Delete User")
            self.btn_delete_user.clicked.connect(self.delete_selected_user)

            for b in (self.btn_add_user, self.btn_edit_username, self.btn_reset_password, self.btn_delete_user):
                b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

            btn_row.addWidget(self.btn_add_user)
            btn_row.addWidget(self.btn_edit_username)
            btn_row.addWidget(self.btn_reset_password)
            btn_row.addWidget(self.btn_delete_user)
            admin_layout.addLayout(btn_row)

            self.tab_admin.setLayout(admin_layout)
            self.tabs.addTab(self.tab_admin, "Admin")
            self.load_users()

        # Assemble main
        main_layout.addWidget(self.tabs)

        # Footer
        footer = QLabel("Developed By Sayas Mansoor © 2026")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("font-size: 12px; color: #E9EEF5; margin-top: 10px;")
        main_layout.addWidget(footer)
        self.setLayout(main_layout)

    def _setup_shortcuts(self):
        act_new = QAction(self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(self.add_invoice)
        self.addAction(act_new)

        act_paid = QAction(self)
        act_paid.setShortcut(QKeySequence("Ctrl+P"))
        act_paid.triggered.connect(self.mark_selected_paid)
        self.addAction(act_paid)

        act_delete = QAction(self)
        act_delete.setShortcut(QKeySequence("Delete"))
        act_delete.triggered.connect(lambda: self.delete_selected_invoice(self.current_active_list()))
        self.addAction(act_delete)

    def current_active_list(self) -> QListWidget:
        if self.sub_tabs.currentWidget() == self.tab_paid:
            return self.paid_list
        if self.sub_tabs.currentWidget() == self.tab_non_paid:
            return self.non_paid_list
        if self.sub_tabs.currentWidget() == self.tab_warranty:
            if self.warranty_tabs.currentWidget() == self.tab_warranty_ended:
                return self.warranty_ended_list
            return self.warranty_under_list
        return self.non_paid_list

    # -------------------- Methods --------------------
    def open_calculator_window(self):
        self.calc_window = WarrantyCalculatorWindow()
        self.calc_window.show()

    def import_invoice_pdf(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Invoice PDF(s)", "", "PDF Files (*.pdf)")
        if paths:
            self.imported_pdf_path = paths
            names = ", ".join([os.path.basename(p) for p in paths])
            self.pdf_name_label.setText(names if len(names) < 80 else names[:77] + "…")
            self.btn_remove_pdf.setEnabled(True)

    def remove_imported_pdf(self):
        self.imported_pdf_path = None
        self.pdf_name_label.setText("No files selected")
        self.btn_remove_pdf.setEnabled(False)

    def add_invoice(self):
        if not self.entry_invoice_id.text().strip():
            QMessageBox.warning(self, "Input Error", "Invoice ID is required!")
            return
        if not self.imported_pdf_path:
            QMessageBox.warning(self, "PDF Missing", "Please import at least one invoice PDF.")
            return

        NONPAID_FOLDER = os.path.join(os.getcwd(), "invoices", "NonPaid")
        os.makedirs(NONPAID_FOLDER, exist_ok=True)

        for pdf_path in self.imported_pdf_path:
            invoice_id = self.entry_invoice_id.text().strip()
            cust_name = self.entry_customer.text().strip()
            safe_name = "".join(c if c.isalnum() else "_" for c in cust_name)
            pdf_name = f"{invoice_id}_Invoice_{safe_name}.pdf"
            new_pdf_path = os.path.join(NONPAID_FOLDER, pdf_name)
            counter = 1
            while os.path.exists(new_pdf_path):
                new_pdf_path = os.path.join(NONPAID_FOLDER, f"{invoice_id}_Invoice_{safe_name}_{counter}.pdf")
                counter += 1
            shutil.copy(pdf_path, new_pdf_path)

            invoice_date_str = self.entry_invoice_date.date().toString("yyyy-MM-dd")
            warranty_start_str = self.entry_warranty_start.date().toString("yyyy-MM-dd")
            try:
                duration_val = int(self.entry_warranty_duration.text().strip())
            except Exception:
                duration_val = 0

            add_invoice(invoice_id, cust_name, invoice_date_str, warranty_start_str, duration_val, new_pdf_path)

        QMessageBox.information(self, "Success", "Invoice(s) added successfully.")
        self.entry_invoice_id.clear()
        self.entry_customer.clear()
        self.entry_warranty_duration.clear()
        self.remove_imported_pdf()
        self.load_data()

    def load_data(self):
        # Auto-move and seal expired warranties first
        run_warranty_maintenance()

        invoices = get_all_invoices()
        self.paid_list.clear()
        self.non_paid_list.clear()
        self.warranty_ended_list.clear()
        self.warranty_under_list.clear()
        icon = QIcon(DEFAULT_ICON) if os.path.exists(DEFAULT_ICON) else QIcon()

        for inv in invoices:
            inv_id, cust_name, paid, w_start, w_duration = inv
            try:
                end_date, days_str, active = calculate_warranty_period(w_start, w_duration)
            except Exception:
                try:
                    start_date = datetime.strptime(w_start, "%Y-%m-%d").date()
                    end_date_obj = start_date + timedelta(days=int(w_duration))
                    end_date = end_date_obj.strftime("%Y-%m-%d")
                    today = datetime.today().date()
                    active = today <= end_date_obj
                    days_str = f"{(end_date_obj - today).days} day(s) remaining" if active else f"Expired {(today - end_date_obj).days} day(s) ago"
                except Exception:
                    end_date = w_start
                    days_str = "Unknown duration"
                    active = False
            try:
                end_date_fmt = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
            except Exception:
                end_date_fmt = end_date

            badge = "🟢 Under" if active else "🔴 Ended"
            display_text = f"{badge} | Invoice #{inv_id} - {cust_name} (Ends {end_date_fmt} · {days_str})"

            # Build a user-checkable item with checkbox (tick icon) support
            def make_item(text: str) -> QListWidgetItem:
                it = QListWidgetItem(icon, text)
                it.setData(Qt.ItemDataRole.UserRole, inv_id)
                it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                it.setCheckState(Qt.CheckState.Unchecked)  # start unchecked (no ✓)
                return it

            if paid:
                self.paid_list.addItem(make_item(display_text))
            else:
                self.non_paid_list.addItem(make_item(display_text))
            if active:
                self.warranty_under_list.addItem(make_item(display_text))
            else:
                self.warranty_ended_list.addItem(make_item(display_text))

    # Keep selection in sync with the checkbox (✓)
    def _sync_selection_from_check(self, item: QListWidgetItem):
        if self._updating_check:
            return
        self._updating_check = True
        try:
            list_widget: QListWidget = item.listWidget()
            row = list_widget.row(item)
            if item.checkState() == Qt.CheckState.Checked:
                list_widget.item(row).setSelected(True)
            else:
                list_widget.item(row).setSelected(False)
        finally:
            self._updating_check = False

    def get_selected_invoice_ids(self, list_widget: QListWidget):
        # Accept either: items selected OR items that are checked (✓)
        ids = set()
        for i in range(list_widget.count()):
            it = list_widget.item(i)
            if it.isSelected() or it.checkState() == Qt.CheckState.Checked:
                ids.add(it.data(Qt.ItemDataRole.UserRole))
        if not ids:
            QMessageBox.warning(self, "Select Invoice", "Please select (or tick ✓) at least one invoice.")
        return list(ids)

    def view_pdf_from_list(self, list_widget: QListWidget):
        inv_ids = self.get_selected_invoice_ids(list_widget)
        if not inv_ids:
            return
        for inv_id in inv_ids:
            pdf_path = get_invoice_pdf_path(inv_id)
            if pdf_path and os.path.exists(pdf_path):
                open_pdf_file(pdf_path)
            else:
                QMessageBox.warning(self, "Missing PDF", f"PDF not found for Invoice #{inv_id}")

    def delete_selected_invoice(self, list_widget: QListWidget):
        inv_ids = self.get_selected_invoice_ids(list_widget)
        if not inv_ids:
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {len(inv_ids)} invoice(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            for inv_id in inv_ids:
                pdf_path = get_invoice_pdf_path(inv_id)
                if pdf_path and os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                    except Exception:
                        pass
                delete_invoice_by_id(inv_id)
            self.load_data()

    def mark_selected_paid(self):
        inv_ids = self.get_selected_invoice_ids(self.non_paid_list)
        if not inv_ids:
            return
        for inv_id in inv_ids:
            mark_as_paid(inv_id)
        self.load_data()

    def add_warranty_ended_seal(self):
        inv_ids = self.get_selected_invoice_ids(self.warranty_ended_list)
        if not inv_ids:
            return
        for inv_id in inv_ids:
            mark_warranty_ended(inv_id)
        self.load_data()

    # ---------------- Admin ----------------
    def load_users(self):
        if not hasattr(self, "user_list"):
            return
        self.user_list.clear()
        users = get_all_users()
        for user_id, username, role in users:
            item = QListWidgetItem(f"{username} ({role})")
            item.setData(Qt.ItemDataRole.UserRole, user_id)
            self.user_list.addItem(item)

    def add_user(self):
        username, ok1 = QInputDialog.getText(self, "New User", "Enter username:")
        if not ok1 or not username.strip():
            return
        password, ok2 = QInputDialog.getText(self, "New User", "Enter password:")
        if not ok2 or not password.strip():
            return
        role, ok3 = QInputDialog.getItem(self, "New User", "Select role:", ["user", "admin"], 0, False)
        if not ok3:
            return
        if create_user(username.strip(), password.strip(), role):
            QMessageBox.information(self, "Success", f"User '{username}' added successfully.")
            self.load_users()
        else:
            QMessageBox.warning(self, "Error", "User already exists or could not be created.")

    def edit_selected_username(self):
        if not hasattr(self, "user_list"):
            return
        selected = self.user_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Select User", "Please select a user to rename.")
            return
        item = selected[0]
        user_id = item.data(Qt.ItemDataRole.UserRole)
        old_label = item.text()
        old_username = old_label.split(" (")[0]
        new_username, ok = QInputDialog.getText(self, "Edit Username", "Enter new username:", text=old_username)
        if not ok or not new_username.strip():
            return
        if update_username(user_id, new_username.strip()):
            if self.logged_in_user["user_id"] == user_id:
                self.logged_in_user["username"] = new_username.strip().lower()
                self.setWindowTitle(f"Warranty Manager - {self.logged_in_user['username']} ({self.logged_in_user['role']})")
            self.load_users()
            QMessageBox.information(self, "Success", "Username updated.")
        else:
            QMessageBox.warning(self, "Error", "That username is already taken or invalid.")

    def reset_selected_password(self):
        if not hasattr(self, "user_list"):
            return
        selected = self.user_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Select User", "Please select a user to reset password.")
            return
        item = selected[0]
        user_id = item.data(Qt.ItemDataRole.UserRole)
        new_pass, ok = QInputDialog.getText(self, "Reset Password", "Enter new password:")
        if not ok or not new_pass.strip():
            return
        update_user_password(user_id, new_pass.strip())
        QMessageBox.information(self, "Success", "Password updated.")

    def delete_selected_user(self):
        if not hasattr(self, "user_list"):
            return
        selected_items = self.user_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Select User", "Please select a user to delete.")
            return
        user_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if user_id == 1:
            QMessageBox.warning(self, "Error", "Cannot delete default admin user.")
            return
        confirm = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this user?")
        if confirm == QMessageBox.StandardButton.Yes:
            delete_user(user_id)
            self.load_users()


# -------------------- Run App (for direct launch) --------------------
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    dummy_user = {"user_id": 1, "username": "admin", "role": "admin123"}
    window = WarrantyManagerApp(dummy_user)
    window.show()
    sys.exit(app.exec())
