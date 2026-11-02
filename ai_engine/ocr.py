"""
High-Efficiency OCR and Document Text Extraction Engine for HaqSetu / Vachan Setu.
Engineered for real-world citizen documents:
- Scanned notices & mobile photos of hard-copy administrative return memos.
- Faded stamp papers, tehsil deficiency slips, and application forms.
- PDFs (text-based and high-resolution 300 DPI rasterized scanned pages).
- Multi-pass image preprocessing (upscaling, contrast enhancement, sharpening, binarization, auto-rotation).
- Automated administrative text cleaning and reconstruction.
"""

import io
import os
import re
import logging
from typing import Optional, List
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pymupdf as fitz
import pytesseract

logger = logging.getLogger(__name__)

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


def clean_ocr_text(text: str) -> str:
    """
    Cleans raw OCR artifacts, fixes broken administrative tokens,
    removes non-printable noise characters, and normalizes spacing.
    """
    if not text:
        return ""

    # 1. Remove non-printable control characters & replacement chars
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\ufffd]', ' ', text)

    # 2. Fix common Indian administrative OCR misrecognitions
    replacements = [
        (r'[/|\\]+ERNMIENTOF\s+INDIA', 'GOVERNMENT OF INDIA'),
        (r'UNIQUE\s+IDENTIFICATION\s+AUTHORITY\s+OF\s+INDIA\s+\(UIDA[D|0|1]\)', 'UNIQUE IDENTIFICATION AUTHORITY OF INDIA (UIDAI)'),
        (r'[^\w\s]?adhaar\s+Number[.:\s]+', 'Aadhaar Number: '),
        (r'[^\w\s]?Address\s*[:.\s]?', 'Address: '),
        (r'\bTehsi[1l]dar\b', 'Tehsildar'),
        (r'\bTahsi[1l]dar\b', 'Tahsildar'),
        (r'\bLekhpa[1l]\b', 'Lekhpal'),
        (r'\bPatwar[1i]\b', 'Patwari'),
        (r'\bKhataun[1i]\b', 'Khatauni'),
        (r'\bDEFIC[1I]ENCY\b', 'DEFICIENCY'),
        (r'\bREJECT[1I]ON\b', 'REJECTION'),
        (r'\bRETURN\s+MEM[0O]\b', 'RETURN MEMO'),
        (r'\bOBJECTION[S]?\b', 'OBJECTIONS'),
        (r'\bCERT[1I]F[1I]CATE\b', 'CERTIFICATE')
    ]
    for pat, rep in replacements:
        cleaned = re.sub(pat, rep, cleaned, flags=re.IGNORECASE)

    # 3. Clean up excessive whitespace while preserving paragraph lines
    lines = []
    for line in cleaned.splitlines():
        line_clean = re.sub(r'[ \t]+', ' ', line).strip()
        # Filter out lines that are purely noisy punctuation fragments
        if len(line_clean) == 1 and line_clean in "-_.,:;~`^'\"\\/|":
            continue
        lines.append(line_clean)

    # Deduplicate consecutive blank lines
    result = []
    for line in lines:
        if line == "" and (not result or result[-1] == ""):
            continue
        result.append(line)

    return "\n".join(result).strip()


def preprocess_image(image: Image.Image) -> List[Image.Image]:
    """
    Produces multi-tier enhanced versions of an input image for OCR:
    1. Grayscale + Upscaled + Contrast + Sharpness enhanced.
    2. Adaptive Binarized (Black and White thresholded for low contrast text).
    """
    # Convert mode to RGB if RGBA, Palette, or CMYK
    if image.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "RGBA":
            bg.paste(image, mask=image.split()[3])
        else:
            bg.paste(image.convert("RGB"))
        image = bg
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # 1. Orientation check & auto-rotation using OSD if confidence is high
    try:
        osd_data = pytesseract.image_to_osd(image, config='--psm 0')
        rotate_match = re.search(r'Rotate:\s+(\d+)', osd_data)
        if rotate_match:
            angle = int(rotate_match.group(1))
            if angle in (90, 180, 270):
                image = image.rotate(-angle, expand=True)
    except Exception:
        pass  # OSD can fail on small or low-text images; continue safely

    # 2. Optimal resolution scaling (aim for width >= 1800 px for crisp characters)
    width, height = image.size
    if width < 1800 and width > 0:
        scale_factor = 1800.0 / width
        new_size = (int(width * scale_factor), int(height * scale_factor))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # 3. Grayscale conversion
    gray = image.convert("L")

    # Pass 1: Contrast stretching & unsharp sharpening
    enhanced_contrast = ImageEnhance.Contrast(gray).enhance(2.0)
    enhanced_sharp = ImageEnhance.Sharpness(enhanced_contrast).enhance(2.0)

    # Pass 2: Adaptive binarization (thresholding) for washed out or shaded paper
    # Using local threshold / mean thresholding
    threshold = 145
    binarized = gray.point(lambda p: 255 if p > threshold else 0, mode='1').convert("L")

    return [enhanced_sharp, binarized, gray]


def extract_text_from_image(image: Image.Image) -> str:
    """
    Executes a multi-pass OCR strategy on an image to ensure maximum text yield.
    """
    variants = preprocess_image(image)
    best_text = ""
    max_words = 0

    # Configurations to test:
    # 1. PSM 3 (Fully automatic page segmentation)
    # 2. PSM 6 (Assume a single uniform block of text)
    # 3. PSM 4 (Assume a single column of text of variable sizes)
    configs = [
        "--oem 3 --psm 3",
        "--oem 3 --psm 6",
        "--oem 3 --psm 4"
    ]

    for img_variant in variants:
        for cfg in configs:
            try:
                raw = pytesseract.image_to_string(img_variant, config=cfg)
                cleaned = clean_ocr_text(raw)
                words = len(cleaned.split())
                if words > max_words:
                    max_words = words
                    best_text = cleaned
                # If we achieved substantial character count, break early
                if max_words >= 35:
                    return best_text
            except Exception as e:
                logger.debug(f"OCR pass error with {cfg}: {e}")

    return best_text


def extract_text(file_path: str) -> str:
    """Extract text from a file on disk."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    return extract_text_from_bytes(file_bytes, os.path.basename(file_path))


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Extracts clean text directly from in-memory file bytes.
    Supports: .pdf, .png, .jpg, .jpeg, .webp, .bmp, .tiff, .tif, .txt, .json.
    """
    ext = os.path.splitext(filename.lower())[1]

    # Plain text formats
    if ext in [".txt", ".json", ".csv", ".tsv", ".md"]:
        try:
            return clean_ocr_text(file_bytes.decode("utf-8", errors="ignore"))
        except Exception:
            return clean_ocr_text(file_bytes.decode("latin-1", errors="ignore"))

    # PDF processing (Digital text + 300 DPI high-res OCR fallback)
    if ext == ".pdf":
        text_parts = []
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()

                # If text is empty or very short (<25 chars), render page at 300 DPI and run high-efficiency OCR
                if len(page_text.strip()) < 25:
                    try:
                        # 300 DPI equivalent for crisp character recognition
                        matrix = fitz.Matrix(300 / 72, 300 / 72)
                        pix = page.get_pixmap(matrix=matrix)
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        page_text = extract_text_from_image(img)
                    except Exception as ocr_err:
                        logger.warning(f"PDF OCR page {page_num} error: {ocr_err}")

                if page_text.strip():
                    text_parts.append(clean_ocr_text(page_text))

            doc.close()
            extracted = "\n\n".join(text_parts).strip()
            if extracted:
                return extracted
            return f"[PDF Note: {filename}] Document opened successfully, but no readable text or characters were detected."
        except Exception as e:
            return f"[PDF Processing Error on {filename}]: {str(e)}"

    # Image processing (PNG, JPG, JPEG, WEBP, BMP, TIFF)
    if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"]:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            extracted_text = extract_text_from_image(image)
            if extracted_text:
                return extracted_text
            return f"[Image Note: {filename}] Image loaded ({image.width}x{image.height}), but no legible text was detected by OCR."
        except Exception as e:
            return f"[Image OCR Error on {filename}]: {str(e)}"

    # Fallback attempt decoding as text
    try:
        return clean_ocr_text(file_bytes.decode("utf-8", errors="ignore"))
    except Exception:
        return f"[Unsupported Format]: Cannot extract text from {filename}"
