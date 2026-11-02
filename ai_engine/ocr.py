
import fitz
import pytesseract
from PIL import Image
import io
import os


def extract_text(file_path):
    """
    Extract text from PDF or image documents.
    Supports text-based PDFs, scanned PDFs and images.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    text = ""

    # PDF processing
    if file_path.lower().endswith(".pdf"):
        pdf = fitz.open(file_path)

        for page_number, page in enumerate(pdf):
            page_text = page.get_text()

            # OCR fallback for scanned PDF pages
            if not page_text.strip():
                pix = page.get_pixmap(dpi=200)
                image = Image.open(
                    io.BytesIO(pix.tobytes("png"))
                )
                page_text = pytesseract.image_to_string(image)

            text += f"\n--- Page {page_number + 1} ---\n"
            text += page_text

        pdf.close()

    # Image processing
    else:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)

    return text.strip()
