# actions/warranty_actions.py
from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime, timedelta

from actions.db_actions import (
    update_invoice_paid,
    get_invoice_pdf_path,
    update_invoice_pdf,
)
from actions.pdf_actions import add_paid_stamps, add_warranty_end_stamp

# ----------------- Helper for exe path -----------------
def resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and PyInstaller exe
    """
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except Exception:
        base_path = os.getcwd()
    return os.path.join(base_path, relative_path)

# ----------------- Folders -----------------
NON_PAID_FOLDER = resource_path(os.path.join("invoices", "NonPaid"))
PAID_FOLDER = resource_path(os.path.join("invoices", "Paid"))
WARRANTY_ENDED_FOLDER = resource_path(os.path.join("invoices", "Warranty Ended"))
SEALS_FOLDER = resource_path("assets")  # contains paid_logo.png, warranty_end_seal.png

# Make sure folders exist
for folder in [NON_PAID_FOLDER, PAID_FOLDER, WARRANTY_ENDED_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# ----------------- Calculate Warranty -----------------
def calculate_warranty_period(start_date_str, duration_days):
    """
    start_date_str: str (either 'DD-MM-YYYY' or 'YYYY-MM-DD')
    duration_days: int
    Returns (end_date_iso, days_remaining_str, is_active)
    """
    try:
        duration = int(duration_days)
        if duration <= 0:
            return start_date_str, "Unknown duration", False
    except Exception:
        return start_date_str, "Unknown duration", False

    # Parse start date
    start_date = None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            start_date = datetime.strptime(start_date_str, fmt)
            break
        except Exception:
            continue
    if not start_date:
        return start_date_str, "Unknown duration", False

    end_date = start_date + timedelta(days=duration)
    today = datetime.now()
    remaining_days = (end_date - today).days
    active = remaining_days >= 0
    days_str = f"{remaining_days} days remaining" if active else f"{abs(remaining_days)} days expired"
    return end_date.strftime("%Y-%m-%d"), days_str, active


# ----------------- Mark Invoice Paid -----------------
def mark_as_paid(invoice_id: int):
    """
    Copy original to Paid folder and stamp page 1 with:
      - PAID seal image (assets/paid_logo.png) near the top, slightly right of center
      - Large diagonal 'PAID' watermark
      - Paid date at top-right
    """
    pdf_path = get_invoice_pdf_path(invoice_id)
    if not pdf_path or not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Invoice PDF not found for ID {invoice_id}")

    base_name = os.path.basename(pdf_path)
    new_name = f"id_{invoice_id}_{base_name}"
    dest_path = os.path.join(PAID_FOLDER, new_name)
    shutil.copy(pdf_path, dest_path)

    paid_seal_path = os.path.join(SEALS_FOLDER, "paid_logo.png")
    paid_date_text = datetime.now().strftime("%Y-%m-%d")

    if os.path.exists(paid_seal_path):
        try:
            stamped_tmp = dest_path + ".tmp.pdf"
            add_paid_stamps(dest_path, paid_seal_path, paid_date_text, stamped_tmp)
            os.replace(stamped_tmp, dest_path)
        except Exception as e:
            print(f"[WARN] Could not add paid stamps: {e}")

    update_invoice_paid(invoice_id, dest_path)


# ----------------- Mark Warranty Ended (manual) -----------------
def mark_warranty_ended(invoice_id: int):
    """
    Copy current PDF to Warranty Ended folder and stamp page 1 with 'warranty_end_seal.png'
    positioned slightly to the right of the PAID seal.
    """
    pdf_path = get_invoice_pdf_path(invoice_id)
    if not pdf_path or not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Invoice PDF not found for ID {invoice_id}")

    base_name = os.path.basename(pdf_path)
    new_name = f"id_{invoice_id}_{base_name}"
    dest_path = os.path.join(WARRANTY_ENDED_FOLDER, new_name)
    shutil.copy(pdf_path, dest_path)

    end_seal_path = os.path.join(SEALS_FOLDER, "warranty_end_seal.png")
    if os.path.exists(end_seal_path):
        try:
            stamped_tmp = dest_path + ".tmp.pdf"
            add_warranty_end_stamp(dest_path, end_seal_path, stamped_tmp)
            os.replace(stamped_tmp, dest_path)
        except Exception as e:
            print(f"[WARN] Could not add warranty end seal: {e}")

    update_invoice_pdf(invoice_id, dest_path)


# ----------------- Auto Maintenance -----------------
def _is_in_ended_folder(path: str) -> bool:
    try:
        return os.path.abspath(WARRANTY_ENDED_FOLDER) in os.path.abspath(path)
    except Exception:
        return False

def _auto_apply_end_if_expired(invoice_id: int, start_date_str: str, duration_days: int):
    """
    If warranty has expired AND the file isn't already in 'Warranty Ended',
    move+stamp it automatically.
    """
    end_iso, _days, active = calculate_warranty_period(start_date_str, duration_days)
    if active:
        return  # still under warranty

    current_pdf = get_invoice_pdf_path(invoice_id)
    if not current_pdf or not os.path.exists(current_pdf):
        return
    if _is_in_ended_folder(current_pdf):
        return  # already filed as ended

    # Move & stamp
    try:
        base_name = os.path.basename(current_pdf)
        new_name = f"id_{invoice_id}_{base_name}"
        dest_path = os.path.join(WARRANTY_ENDED_FOLDER, new_name)
        shutil.copy(current_pdf, dest_path)

        seal_path = os.path.join(SEALS_FOLDER, "warranty_end_seal.png")
        if os.path.exists(seal_path):
            stamped_tmp = dest_path + ".tmp.pdf"
            add_warranty_end_stamp(dest_path, seal_path, stamped_tmp)
            os.replace(stamped_tmp, dest_path)

        update_invoice_pdf(invoice_id, dest_path)
    except Exception as e:
        print(f"[WARN] Auto end-stamp failed for invoice {invoice_id}: {e}")


def run_warranty_maintenance():
    """
    Scan all invoices; for any expired warranties not yet in 'Warranty Ended',
    automatically file them there and apply the End seal.
    Call this on app start and whenever you refresh the lists.
    """
    try:
        from actions.db_actions import get_all_invoices  # local import to avoid circular
        for inv_id, _cust, _paid, w_start, w_duration in get_all_invoices():
            _auto_apply_end_if_expired(inv_id, w_start, w_duration)
    except Exception as e:
        print(f"[WARN] Maintenance scan failed: {e}")
