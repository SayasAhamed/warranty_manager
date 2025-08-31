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
from PyQt6.QtGui import QPixmap, QIcon, QCursor
from PyQt6.QtCore import Qt, QDate

from actions.db_actions import (
    get_all_invoices, get_invoice_pdf_path, delete_invoice_by_id,
    check_user_credentials, get_all_users, create_user, delete_user,
    verify_security_answers, update_user_password
)
from actions.invoice_actions import add_invoice
from actions.warranty_actions import (
    mark_as_paid, mark_warranty_ended, calculate_warranty_period
)

BUSINESS_LOGO_PATH = 'assets/business_logo.png'
PDF_ICON_PATH = 'assets/pdf_icon.png'
BACKGROUND_IMAGE_PATH = "assets/main_bg.jpg"  # main app background


# ---------------- PDF OPEN ----------------
def open_pdf_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found: {path}")
    if platform.system() == "Windows":
        os.startfile(os.path.abspath(path))
    elif platform.system() == "Darwin":  # macOS
        subprocess.Popen(["open", os.path.abspath(path)])
    else:  # Linux
        subprocess.Popen(["xdg-open", os.path.abspath(path)])


# ---------------- Login Window ----------------
class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PC-Fix Warranty Manager Login")
        self.setFixedSize(400, 350)

        # Background
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 400, 350)
        if os.path.exists(BACKGROUND_IMAGE_PATH):
            bg_pix = QPixmap(BACKGROUND_IMAGE_PATH).scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.bg_label.setPixmap(bg_pix)
        self.bg_label.lower()

        # Container
        container = QWidget(self)
        container.setGeometry(20, 20, 360, 310)
        container.setStyleSheet("background-color: rgba(0,0,0,120); border-radius: 15px;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)

        # Logo
        if os.path.exists(BUSINESS_LOGO_PATH):
            logo = QLabel()
            logo_pix = QPixmap(BUSINESS_LOGO_PATH).scaledToWidth(120, Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(logo_pix)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo)

        # Title
        title = QLabel("Welcome to PC-Fix Warranty Manager")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-bottom: 10px;")
        layout.addWidget(title)

        # Username & Password
        self.username_entry = QLineEdit()
        self.username_entry.setPlaceholderText("Username")
        self.username_entry.setStyleSheet("padding:6px; border-radius:8px; background-color: rgba(255,255,255,180);")
        layout.addWidget(self.username_entry)

        self.password_entry = QLineEdit()
        self.password_entry.setPlaceholderText("Password")
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_entry.setStyleSheet("padding:6px; border-radius:8px; background-color: rgba(255,255,255,180);")
        layout.addWidget(self.password_entry)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_login = QPushButton("Login")
        self.btn_login.clicked.connect(self.attempt_login)
        self.btn_login.setStyleSheet("background-color:#4CAF50;color:white;font-weight:bold;border-radius:10px;")
        btn_layout.addWidget(self.btn_login)

        self.btn_forgot = QPushButton("Forgot Password?")
        self.btn_forgot.clicked.connect(self.open_forgot_password)
        self.btn_forgot.setStyleSheet("background-color:#f44336;color:white;font-weight:bold;border-radius:10px;")
        btn_layout.addWidget(self.btn_forgot)

        layout.addLayout(btn_layout)

        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Footer
        footer = QLabel("Developed By Sayas Mansoor © 2025")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("font-size:12px;color:white;")
        layout.addWidget(footer)

        self.user = None
        self.username_entry.returnPressed.connect(self.attempt_login)
        self.password_entry.returnPressed.connect(self.attempt_login)
        self.username_entry.setFocus()

    def attempt_login(self):
        username = self.username_entry.text().strip()
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
        self.setFixedSize(400, 250)
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
        username = self.username_entry.text().strip()
        ans1 = self.answer1.text().strip()
        ans2 = self.answer2.text().strip()
        user_id = verify_security_answers(username, ans1, ans2)
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
        self.resize(1000, 720)
        self.imported_pdf_path = None
        self.init_ui()
        self.load_data()

    # --- UI Initialization ---
    def init_ui(self):
        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Add Invoice Tab
        self.tab_add_invoice = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        scroll_layout.setContentsMargins(20, 20, 20, 20)

        if os.path.exists(BUSINESS_LOGO_PATH):
            pixmap = QPixmap(BUSINESS_LOGO_PATH).scaledToWidth(180)
            logo_label = QLabel()
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            scroll_layout.addWidget(logo_label)

        title_label = QLabel("PC-Fix - Warranty Manager")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 20px;")
        scroll_layout.addWidget(title_label)

        def add_form_row(label_text, widget):
            container = QHBoxLayout()
            label = QLabel(label_text)
            label.setMinimumWidth(180)
            container.addWidget(label)
            container.addWidget(widget)
            container.setSpacing(10)
            return container

        self.entry_invoice_id = QLineEdit()
        scroll_layout.addLayout(add_form_row("Invoice ID (Required):", self.entry_invoice_id))
        self.entry_customer = QLineEdit()
        scroll_layout.addLayout(add_form_row("Customer Name:", self.entry_customer))
        self.entry_invoice_date = QDateEdit()
        self.entry_invoice_date.setCalendarPopup(True)
        self.entry_invoice_date.setDate(QDate.currentDate())
        scroll_layout.addLayout(add_form_row("Invoice Date:", self.entry_invoice_date))
        self.entry_warranty_start = QDateEdit()
        self.entry_warranty_start.setCalendarPopup(True)
        self.entry_warranty_start.setDate(QDate.currentDate())
        scroll_layout.addLayout(add_form_row("Warranty Start:", self.entry_warranty_start))
        self.entry_warranty_duration = QLineEdit()
        self.entry_warranty_duration.setPlaceholderText("Duration in Days")
        scroll_layout.addLayout(add_form_row("Warranty Duration:", self.entry_warranty_duration))

        # PDF Import
        pdf_container = QHBoxLayout()
        self.btn_import_pdf = QPushButton("Import Invoice PDF(s)")
        self.btn_import_pdf.clicked.connect(self.import_invoice_pdf)
        pdf_container.addWidget(self.btn_import_pdf)
        self.pdf_preview_label = QLabel("")
        self.pdf_preview_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pdf_preview_label.setMinimumHeight(32)
        self.pdf_preview_label.mousePressEvent = self.preview_pdf_clicked
        pdf_container.addWidget(self.pdf_preview_label)
        self.btn_remove_pdf = QPushButton("Remove PDF")
        self.btn_remove_pdf.setEnabled(False)
        self.btn_remove_pdf.clicked.connect(self.remove_imported_pdf)
        pdf_container.addWidget(self.btn_remove_pdf)
        scroll_layout.addLayout(pdf_container)

        self.btn_add_invoice = QPushButton("Add Invoice")
        self.btn_add_invoice.setStyleSheet("background-color: #4CAF50; font-weight: bold;")
        self.btn_add_invoice.clicked.connect(self.add_invoice)
        scroll_layout.addWidget(self.btn_add_invoice)
        scroll_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        scroll_area.setWidget(scroll_content)
        add_layout = QVBoxLayout()
        add_layout.addWidget(scroll_area)
        self.tab_add_invoice.setLayout(add_layout)
        self.tabs.addTab(self.tab_add_invoice, "Add Invoice")

        # --- Other Tabs ---
        self.tab_overall = QWidget()
        overall_layout = QVBoxLayout()
        self.sub_tabs = QTabWidget()
        overall_layout.addWidget(self.sub_tabs)
        self.tab_overall.setLayout(overall_layout)
        self.tabs.addTab(self.tab_overall, "All Invoices & Warranty")

        # Paid invoices
        self.tab_paid = QWidget()
        self.paid_list = QListWidget()
        self.paid_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
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

        self.tab_warranty_ended = QWidget()
        self.warranty_ended_list = QListWidget()
        self.warranty_ended_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.tab_warranty_ended.setStyleSheet("QWidget { background-color: #800000; color: white; }")
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

        self.tab_warranty_under = QWidget()
        self.warranty_under_list = QListWidget()
        self.warranty_under_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.tab_warranty_under.setStyleSheet("QWidget { background-color: #006400; color: white; }")
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
            self.user_list = QListWidget()
            self.user_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
            admin_layout.addWidget(QLabel("Registered Users:"))
            admin_layout.addWidget(self.user_list)

            btn_layout = QHBoxLayout()
            self.btn_add_user = QPushButton("Add User")
            self.btn_add_user.clicked.connect(self.add_user)
            self.btn_delete_user = QPushButton("Delete User")
            self.btn_delete_user.clicked.connect(self.delete_selected_user)
            btn_layout.addWidget(self.btn_add_user)
            btn_layout.addWidget(self.btn_delete_user)
            admin_layout.addLayout(btn_layout)

            self.tab_admin.setLayout(admin_layout)
            self.tabs.addTab(self.tab_admin, "Admin")
            self.load_users()

        main_layout.addWidget(self.tabs)


        # Footer
        footer = QLabel("Developed By Sayas Mansoor © 2025")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("font-size: 12px; color: white; margin-top: 10px;")
        main_layout.addWidget(footer)

        self.setLayout(main_layout)




    # -------------------- Methods --------------------
    def open_calculator_window(self):
        self.calc_window = WarrantyCalculatorWindow()
        self.calc_window.show()

    def import_invoice_pdf(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Invoice PDF(s)", "", "PDF Files (*.pdf)")
        if paths:
            self.imported_pdf_path = paths
            self.pdf_preview_label.setText(", ".join([os.path.basename(p) for p in paths]))
            icon = QPixmap(PDF_ICON_PATH).scaled(32, 32) if os.path.exists(PDF_ICON_PATH) else QPixmap()
            self.pdf_preview_label.setPixmap(icon)
            self.btn_remove_pdf.setEnabled(True)

    def remove_imported_pdf(self):
        self.imported_pdf_path = None
        self.pdf_preview_label.clear()
        self.btn_remove_pdf.setEnabled(False)

    def preview_pdf_clicked(self, event):
        if self.imported_pdf_path:
            for path in self.imported_pdf_path:
                if os.path.exists(path):
                    open_pdf_file(path)

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
            pdf_name = f"{invoice_id}_Invoice_{cust_name}.pdf"
            new_pdf_path = os.path.join(NONPAID_FOLDER, pdf_name)
            counter = 1
            while os.path.exists(new_pdf_path):
                new_pdf_path = os.path.join(NONPAID_FOLDER, f"{invoice_id}_Invoice_{cust_name}_{counter}.pdf")
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
        invoices = get_all_invoices()
        self.paid_list.clear()
        self.non_paid_list.clear()
        self.warranty_ended_list.clear()
        self.warranty_under_list.clear()
        icon = QIcon(PDF_ICON_PATH if os.path.exists(PDF_ICON_PATH) else BUSINESS_LOGO_PATH)
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
            display_text = f"Invoice #{inv_id} - {cust_name} (Ends {end_date_fmt} · {days_str})"
            item = QListWidgetItem(icon, display_text)
            item.setData(Qt.ItemDataRole.UserRole, inv_id)
            if paid:
                self.paid_list.addItem(item)
            else:
                self.non_paid_list.addItem(item.clone())
            if active:
                self.warranty_under_list.addItem(item.clone())
            else:
                self.warranty_ended_list.addItem(item.clone())

    def get_selected_invoice_ids(self, list_widget):
        items = list_widget.selectedItems()
        if not items:
            QMessageBox.warning(self, "Select Invoice", "Please select at least one invoice.")
            return []
        return [item.data(Qt.ItemDataRole.UserRole) for item in items]

    def view_pdf_from_list(self, list_widget):
        inv_ids = self.get_selected_invoice_ids(list_widget)
        if not inv_ids:
            return
        for inv_id in inv_ids:
            pdf_path = get_invoice_pdf_path(inv_id)
            if pdf_path and os.path.exists(pdf_path):
                open_pdf_file(pdf_path)
            else:
                QMessageBox.warning(self, "Missing PDF", f"PDF not found for Invoice #{inv_id}")

    def delete_selected_invoice(self, list_widget):
        inv_ids = self.get_selected_invoice_ids(list_widget)
        if not inv_ids:
            return
        confirm = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete {len(inv_ids)} invoice(s)?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
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

    def delete_selected_user(self):
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


# -------------------- Run App --------------------
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    login = LoginWindow()
    if login.exec() == QDialog.DialogCode.Accepted:
        window = WarrantyManagerApp(login.user)
        window.show()
        sys.exit(app.exec())