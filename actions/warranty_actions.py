import os
import shutil
from datetime import datetime, timedelta
from actions.db_actions import update_invoice_paid, get_invoice_pdf_path, update_invoice_pdf

# ---------------- Folders ----------------
NON_PAID_FOLDER = os.path.join(os.getcwd(), "invoices", "NonPaid")
PAID_FOLDER = os.path.join(os.getcwd(), "invoices", "Paid")
WARRANTY_ENDED_FOLDER = os.path.join(os.getcwd(), "invoices", "Warranty Ended")
SEALS_FOLDER = os.path.join(os.getcwd(), "assets")  # contains paid_logo.png, warranty_end_seal.png

# Make sure folders exist
for folder in [NON_PAID_FOLDER, PAID_FOLDER, WARRANTY_ENDED_FOLDER]:
    os.makedirs(folder, exist_ok=True)


# ---------------- Calculate Warranty ----------------
def calculate_warranty_period(start_date_str, duration_days):
    """
    start_date_str: str (either 'DD-MM-YYYY' or 'YYYY-MM-DD')
    duration_days: int
    Returns (end_date_iso, days_remaining_str, is_active)
    """
    # Validate duration
    try:
        duration = int(duration_days)
        if duration <= 0:
            return start_date_str, "Unknown duration", False
    except:
        return start_date_str, "Unknown duration", False

    # Parse start date with both formats
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            start_date = datetime.strptime(start_date_str, fmt)
            break
        except:
            start_date = None

    if not start_date:
        return start_date_str, "Unknown duration", False

    end_date = start_date + timedelta(days=duration)
    today = datetime.now()
    remaining_days = (end_date - today).days
    active = remaining_days >= 0
    days_str = f"{remaining_days} days remaining" if active else f"{abs(remaining_days)} days expired"
    return end_date.strftime("%Y-%m-%d"), days_str, active


# ---------------- Mark Invoice Paid ----------------
def mark_as_paid(invoice_id):
    pdf_path = get_invoice_pdf_path(invoice_id)
    if not pdf_path or not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Invoice PDF not found for ID {invoice_id}")

    # Copy to Paid folder
    base_name = os.path.basename(pdf_path)
    new_name = f"id_{invoice_id}_{base_name}"
    dest_path = os.path.join(PAID_FOLDER, new_name)
    shutil.copy(pdf_path, dest_path)

    # Add Paid Seal (placeholder)
    paid_seal_path = os.path.join(SEALS_FOLDER, "paid_logo.png")
    if os.path.exists(paid_seal_path):
        try:
            from PyPDF2 import PdfReader, PdfWriter
            reader = PdfReader(dest_path)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            # TODO: Add actual seal image using reportlab or other lib
            with open(dest_path, "wb") as f_out:
                writer.write(f_out)
        except Exception as e:
            print(f"Could not add paid seal: {e}")

    # Update DB
    update_invoice_paid(invoice_id, dest_path)


# ---------------- Mark Warranty Ended ----------------
def mark_warranty_ended(invoice_id):
    pdf_path = get_invoice_pdf_path(invoice_id)
    if not pdf_path or not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Invoice PDF not found for ID {invoice_id}")

    # Copy to Warranty Ended folder
    base_name = os.path.basename(pdf_path)
    new_name = f"id_{invoice_id}_{base_name}"
    dest_path = os.path.join(WARRANTY_ENDED_FOLDER, new_name)
    shutil.copy(pdf_path, dest_path)

    # Add Warranty End Seal (placeholder)
    seal_path = os.path.join(SEALS_FOLDER, "warranty_end_seal.png")
    if os.path.exists(seal_path):
        try:
            from PyPDF2 import PdfReader, PdfWriter
            reader = PdfReader(dest_path)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            # TODO: Add actual seal image using reportlab or other lib
            with open(dest_path, "wb") as f_out:
                writer.write(f_out)
        except Exception as e:
            print(f"Could not add warranty end seal: {e}")

    # Update DB PDF path
    update_invoice_pdf(invoice_id, dest_path)
