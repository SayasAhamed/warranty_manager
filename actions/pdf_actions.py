# actions/pdf_actions.py
from __future__ import annotations

import os
import platform
import subprocess
from io import BytesIO
from typing import Tuple

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color

# ---------------- Utilities ----------------

def _page_size_of(pdf_path: str) -> Tuple[float, float]:
    reader = PdfReader(pdf_path)
    box = reader.pages[0].mediabox
    return float(box.width), float(box.height)

def _merge_overlay(base_pdf_path: str, overlay_pdf_bytes: bytes, output_path: str) -> None:
    base_reader = PdfReader(base_pdf_path)
    overlay_reader = PdfReader(BytesIO(overlay_pdf_bytes))
    writer = PdfWriter()

    # Merge overlay onto page 1; copy remaining pages unchanged
    first = base_reader.pages[0]
    first.merge_page(overlay_reader.pages[0])
    writer.add_page(first)

    for i in range(1, len(base_reader.pages)):
        writer.add_page(base_reader.pages[i])

    with open(output_path, "wb") as f:
        writer.write(f)

# ---------------- Public: PAID stamping ----------------

def add_paid_stamps(base_pdf_path: str, seal_path: str, paid_date_text: str, output_path: str) -> None:
    """
    Draws on page 1:
      - a large, semi-transparent diagonal 'PAID' watermark centered
      - the round 'PAID' seal image near the top, slightly right of center
      - 'Paid: <date>' on the top-right corner
    Then writes full PDF to output_path.
    """
    if not (os.path.exists(base_pdf_path) and os.path.exists(seal_path)):
        raise FileNotFoundError("Base PDF or seal image missing")

    page_w, page_h = _page_size_of(base_pdf_path)

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))

    # --- Big diagonal "PAID" watermark ---
    c.saveState()
    try:
        c.setFillAlpha(0.12)
    except Exception:
        pass
    c.setFillColor(Color(0, 0, 0, alpha=0.12))
    c.setStrokeColor(Color(0, 0, 0, alpha=0.12))
    font_size = max(72, int(page_w * 0.12))
    c.setFont("Helvetica-Bold", font_size)
    c.translate(page_w / 2.0, page_h / 2.0)
    c.rotate(35)
    text = "PAID"
    tw = c.stringWidth(text, "Helvetica-Bold", font_size)
    c.drawString(-tw / 2.0, -font_size / 2.0, text)
    c.restoreState()

    # --- Round "PAID" seal (near top, slightly right of center) ---
    c.saveState()
    seal_img = ImageReader(seal_path)
    seal_w = page_w * 0.18  # ~18% of page width
    iw, ih = seal_img.getSize()
    seal_h = seal_w * (ih / iw)
    x = page_w * 0.60
    y = page_h * 0.70
    c.drawImage(seal_img, x, y, width=seal_w, height=seal_h, mask='auto')
    c.restoreState()

    # --- Paid date at top-right ---
    c.saveState()
    margin = page_w * 0.035
    c.setFont("Helvetica-Bold", 12)
    label = f"Paid: {paid_date_text}"
    tw = c.stringWidth(label, "Helvetica-Bold", 12)
    c.setFillColor(Color(0.15, 0.15, 0.15))
    c.drawString(page_w - margin - tw, page_h - margin - 12, label)
    c.restoreState()

    c.showPage()
    c.save()

    buf.seek(0)
    _merge_overlay(base_pdf_path, buf.getvalue(), output_path)

# ---------------- Public: WARRANTY ENDED stamping ----------------

def add_warranty_end_stamp(base_pdf_path: str, end_seal_path: str, output_path: str) -> None:
    """
    Draws on page 1 ONLY:
      - the 'WARRANTY ENDED' round seal, positioned slightly to the RIGHT of the Paid seal.
    (No watermark/date text by design, per request.)
    """
    if not (os.path.exists(base_pdf_path) and os.path.exists(end_seal_path)):
        raise FileNotFoundError("Base PDF or end seal image missing")

    page_w, page_h = _page_size_of(base_pdf_path)

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))

    # blank overlay base
    # Position: Paid seal sits at ~0.60W; place End seal a bit further right (e.g. 0.76W), same Y
    c.saveState()
    end_img = ImageReader(end_seal_path)
    seal_w = page_w * 0.18  # keep similar visual size
    iw, ih = end_img.getSize()
    seal_h = seal_w * (ih / iw)

    x = page_w * 0.76   # slightly right of Paid seal
    y = page_h * 0.70   # same vertical alignment as Paid seal
    c.drawImage(end_img, x, y, width=seal_w, height=seal_h, mask='auto')
    c.restoreState()

    c.showPage()
    c.save()

    buf.seek(0)
    _merge_overlay(base_pdf_path, buf.getvalue(), output_path)

# ---------------- Optional: open with default viewer ----------------

def open_pdf_file(pdf_path: str):
    """Open PDF file with the default system viewer"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        if platform.system() == 'Windows':
            os.startfile(pdf_path)  # type: ignore[attr-defined]
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', pdf_path])
        else:  # Linux
            subprocess.run(['xdg-open', pdf_path])
    except Exception as e:
        raise Exception(f"Failed to open PDF: {e}")
