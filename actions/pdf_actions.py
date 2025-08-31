import os
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image
import subprocess
import platform

def overlay_image_on_pdf(pdf_path, image_path, output_path, position=(400, 700), scale=0.3):
    if not os.path.exists(pdf_path) or not os.path.exists(image_path):
        return False
    
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    # Get the first page
    page = reader.pages[0]
    
    # Create a buffer for the overlay
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Draw the image on the canvas
    img = Image.open(image_path)
    width, height = img.size
    scaled_width = width * scale
    scaled_height = height * scale
    can.drawImage(image_path, position[0], position[1], width=scaled_width, height=scaled_height, mask='auto')
    can.save()
    
    # Move to the beginning of the buffer
    packet.seek(0)
    overlay_pdf = PdfReader(packet)
    
    # Merge the overlay with the original page
    overlay_page = overlay_pdf.pages[0]
    page.merge_page(overlay_page)
    
    # Add the modified page to the writer
    writer.add_page(page)
    
    # Add remaining pages if any
    for i in range(1, len(reader.pages)):
        writer.add_page(reader.pages[i])
    
    # Write the output file
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    
    return True

def open_pdf_file(pdf_path):
    """Open PDF file with the default system viewer"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        if platform.system() == 'Windows':
            os.startfile(pdf_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', pdf_path])
        else:  # Linux
            subprocess.run(['xdg-open', pdf_path])
    except Exception as e:
        raise Exception(f"Failed to open PDF: {e}")