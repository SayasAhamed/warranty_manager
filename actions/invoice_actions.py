# actions/invoice_actions.py
import os
import shutil
import sys
from actions.db_actions import insert_invoice

# ----------------- Helper for exe path -----------------
def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and PyInstaller exe
    """
    try:
        base_path = getattr(__import__('sys'), "_MEIPASS")  # type: ignore[attr-defined]
    except Exception:
        base_path = os.getcwd()
    return os.path.join(base_path, relative_path)

# Folder for non-paid invoices
NONPAID_FOLDER = resource_path(os.path.join("invoices", "NonPaid"))
os.makedirs(NONPAID_FOLDER, exist_ok=True)

# ----------------- PDF Handling -----------------
def copy_imported_pdf(imported_pdf_path, invoice_id, customer_name):
    if not os.path.exists(imported_pdf_path):
        raise FileNotFoundError("Imported PDF not found")

    # Safe file name
    safe_name = "".join(c if c.isalnum() else "_" for c in customer_name)
    new_pdf_name = f"{invoice_id}_Invoice_{safe_name}.pdf"
    new_pdf_path = os.path.join(NONPAID_FOLDER, new_pdf_name)

    # Avoid overwriting
    counter = 1
    while os.path.exists(new_pdf_path):
        new_pdf_path = os.path.join(NONPAID_FOLDER, f"{invoice_id}_Invoice_{safe_name}_{counter}.pdf")
        counter += 1

    shutil.copy(imported_pdf_path, new_pdf_path)
    return new_pdf_path

# ----------------- Add Invoice -----------------
def add_invoice(invoice_id, customer_name, invoice_date, warranty_start, warranty_duration, pdf_path):
    """
    Adds invoice to DB and moves PDF to NonPaid folder
    """
    final_pdf_path = copy_imported_pdf(pdf_path, invoice_id, customer_name)
    insert_invoice(customer_name, invoice_date, warranty_start, warranty_duration, final_pdf_path, invoice_id)
