import fitz
import pytesseract
from PIL import Image
import io
import os


def extract_text(file_path):
    """
    Extract text from PDF, images, or text files.
    Supports text-based PDFs, scanned PDFs, images, and plain text files.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Plain text processing (.txt, .json, .csv)
    if file_path.lower().endswith((".txt", ".json", ".csv", ".tsv")):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()

    # PDF processing
    if file_path.lower().endswith(".pdf"):
        text = ""
        pdf = fitz.open(file_path)

        for page_number, page in enumerate(pdf):
            page_text = page.get_text()

            # OCR fallback for scanned PDF pages
            if not page_text.strip():
                try:
                    pix = page.get_pixmap(dpi=200)
                    image = Image.open(
                        io.BytesIO(pix.tobytes("png"))
                    )
                    page_text = pytesseract.image_to_string(image)
                except Exception:
                    pass

            text += f"\n--- Page {page_number + 1} ---\n"
            text += page_text

        pdf.close()
        return text.strip()

    # Image processing
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        return f"[OCR fallback] Unable to process image: {e}"
