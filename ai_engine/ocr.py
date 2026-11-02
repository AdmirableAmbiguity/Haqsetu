import io
import os
from PIL import Image
import pymupdf as fitz
import pytesseract

# Configure Tesseract OCR binary path for Windows if available
TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
]
for p in TESSERACT_PATHS:
    if os.path.exists(p):
        pytesseract.pytesseract.tesseract_cmd = p
        break


def extract_text(file_path: str) -> str:
    """
    Extract text from PDF, images, or text files on disk.
    Supports text-based PDFs, scanned PDFs, images (PNG, JPG), and plain text.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    return extract_text_from_bytes(file_bytes, os.path.basename(file_path))


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Extract text directly from in-memory file bytes.
    Supports: .pdf, .png, .jpg, .jpeg, .webp, .tiff, .txt, .json.
    """
    ext = os.path.splitext(filename.lower())[1]

    # Plain text
    if ext in [".txt", ".json", ".csv", ".tsv"]:
        try:
            return file_bytes.decode("utf-8", errors="ignore").strip()
        except Exception:
            return file_bytes.decode("latin-1", errors="ignore").strip()

    # PDF processing
    if ext == ".pdf":
        text_parts = []
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()

                # If text is empty or very short, run OCR on scanned page image
                if len(page_text.strip()) < 20:
                    try:
                        pix = page.get_pixmap(dpi=200)
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        page_text = pytesseract.image_to_string(img)
                    except Exception:
                        pass

                text_parts.append(page_text)
            doc.close()
            extracted = "\n".join(text_parts).strip()
            if extracted:
                return extracted
            return "[PDF Note] Document opened successfully, but no readable text was detected."
        except Exception as e:
            return f"[PDF Processing Error]: {str(e)}"

    # Image processing (PNG, JPG, JPEG, WEBP, TIFF)
    if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"]:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Convert RGBA to RGB if needed
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            text = pytesseract.image_to_string(image)
            clean_text = text.strip()
            if clean_text:
                return clean_text
            return f"[Image Note: {filename}] Image loaded successfully ({image.width}x{image.height}), but no legible text was detected by OCR."
        except Exception as e:
            return f"[Image OCR Error on {filename}]: {str(e)}"

    # Fallback attempt decoding as text
    try:
        return file_bytes.decode("utf-8", errors="ignore").strip()
    except Exception:
        return f"[Unsupported Format]: Cannot extract text from {filename}"
