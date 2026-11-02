import io
import os

import pymupdf as fitz
import pytesseract

from PIL import (
    Image,
    ImageEnhance,
    ImageFilter,
    ImageOps
)


# --------------------------------------------------
# TESSERACT CONFIGURATION
# --------------------------------------------------

TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(
        r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    )
]

for path in TESSERACT_PATHS:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        break


OCR_LANGUAGE = "eng"
OCR_CONFIG = "--oem 3 --psm 6"

SUPPORTED_IMAGE_FORMATS = {
    ".png", ".jpg", ".jpeg", ".webp",
    ".bmp", ".tiff", ".tif"
}

SUPPORTED_TEXT_FORMATS = {
    ".txt", ".json", ".csv", ".tsv"
}


# --------------------------------------------------
# IMAGE PREPROCESSING
# --------------------------------------------------

def preprocess_image(image):
    """
    Improve image readability before OCR.

    Operations:
    - Convert to grayscale
    - Improve contrast
    - Apply sharpening
    - Correct image orientation where possible
    """

    image = ImageOps.exif_transpose(image)

    image = image.convert("L")

    image = ImageOps.autocontrast(image)

    image = ImageEnhance.Contrast(image).enhance(1.5)

    image = image.filter(ImageFilter.SHARPEN)

    return image


# --------------------------------------------------
# OCR EXECUTION WITH QUALITY METADATA
# --------------------------------------------------

def perform_ocr_with_metadata(image):
    """
    Run OCR using multiple page segmentation modes.

    Returns:
        text
        mean_token_confidence
        word_count
        low_confidence_words
        needs_review
        method

    Tesseract confidence is a quality indicator,
    not a probability that the extracted text is correct.
    """

    try:
        processed_image = preprocess_image(image)

        configs = [
            ("PSM 6", OCR_CONFIG),
            ("PSM 11", "--oem 3 --psm 11")
        ]

        best_result = None
        best_score = -1
        errors = []

        for method, config in configs:
            try:
                data = pytesseract.image_to_data(
                    processed_image,
                    lang=OCR_LANGUAGE,
                    config=config,
                    output_type=pytesseract.Output.DICT
                )

                words = []
                confidences = []

                for index, word in enumerate(data["text"]):
                    word = word.strip()

                    if not word:
                        continue

                    try:
                        confidence = float(data["conf"][index])
                    except (ValueError, TypeError):
                        continue

                    if confidence >= 0:
                        words.append(word)
                        confidences.append(confidence)

                text = " ".join(words).strip()

                if not text:
                    continue

                mean_confidence = (
                    sum(confidences) / len(confidences)
                    if confidences else 0.0
                )

                # Identify words with low OCR confidence.
                low_confidence_words = [
                    {
                        "word": word,
                        "confidence": round(confidence, 2)
                    }
                    for word, confidence in zip(words, confidences)
                    if confidence < 50
                ]

                word_count = len(words)

                # Balance average confidence with word coverage.
                coverage_factor = min(word_count / 8, 1.0)

                score = mean_confidence * coverage_factor

                result = {
                    "text": text,

                    "mean_token_confidence": round(
                        mean_confidence, 2
                    ),

                    "word_count": word_count,

                    "low_confidence_words": low_confidence_words,

                    "needs_review": (
                        mean_confidence < 60
                        or word_count < 5
                        or bool(low_confidence_words)
                    ),

                    "method": method
                }

                if score > best_score:
                    best_score = score
                    best_result = result

            except pytesseract.TesseractError as error:
                errors.append(str(error))

        if best_result is None:

            if errors:
                raise RuntimeError(
                    "All OCR attempts failed: "
                    + "; ".join(errors)
                )

            raise RuntimeError(
                "No readable text detected in the image."
            )

        return best_result

    except pytesseract.TesseractNotFoundError as error:
        raise RuntimeError(
            "Tesseract OCR executable was not found. "
            "Check the Tesseract installation."
        ) from error

    except pytesseract.TesseractError as error:
        raise RuntimeError(
            f"Tesseract OCR failed: {error}"
        ) from error


# --------------------------------------------------
# BACKWARD-COMPATIBLE OCR FUNCTION
# --------------------------------------------------

def perform_ocr(image):
    """
    Existing code continues receiving a plain string.
    """

    result = perform_ocr_with_metadata(image)

    return result["text"]


# --------------------------------------------------
# PDF TEXT QUALITY CHECK
# --------------------------------------------------

def is_text_poor_quality(text):
    """
    Decide whether a PDF page needs OCR.

    Short or mostly non-alphanumeric native text is
    treated as potentially incomplete.
    """

    text = text.strip()

    if len(text) < 30:
        return True

    alphanumeric_count = sum(
        character.isalnum()
        for character in text
    )

    ratio = alphanumeric_count / max(len(text), 1)

    return ratio < 0.45


# --------------------------------------------------
# FILE PATH INTERFACE
# --------------------------------------------------

def extract_text(file_path: str) -> str:
    """
    Extract text from a file stored on disk.
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    with open(file_path, "rb") as file:
        file_bytes = file.read()

    filename = os.path.basename(file_path)

    return extract_text_from_bytes(
        file_bytes,
        filename
    )


# --------------------------------------------------
# IN-MEMORY FILE INTERFACE
# --------------------------------------------------

def extract_text_from_bytes(
    file_bytes: bytes,
    filename: str
) -> str:
    """
    Extract text from uploaded document bytes.

    Supported:
    PDF, PNG, JPG, JPEG, WEBP, BMP, TIFF,
    TXT, JSON, CSV and TSV.

    Returns extracted text as a string.
    """

    if not file_bytes:
        raise ValueError(
            f"The uploaded file is empty: {filename}"
        )

    ext = os.path.splitext(filename.lower())[1]

    # ----------------------------------------------
    # PLAIN TEXT FILES
    # ----------------------------------------------

    if ext in SUPPORTED_TEXT_FORMATS:

        try:
            return file_bytes.decode(
                "utf-8-sig"
            ).strip()

        except UnicodeDecodeError:
            return file_bytes.decode(
                "latin-1"
            ).strip()

    # ----------------------------------------------
    # IMAGE FILES
    # ----------------------------------------------

    if ext in SUPPORTED_IMAGE_FORMATS:

        try:
            image = Image.open(
                io.BytesIO(file_bytes)
            )

            image.load()

            extracted_text = perform_ocr(image)

            if not extracted_text:
                raise RuntimeError(
                    f"No readable text detected in {filename}. "
                    "Please verify the image or upload a clearer copy."
                )

            return extracted_text

        except RuntimeError:
            raise

        except Exception as error:
            raise RuntimeError(
                f"Unable to process image {filename}: {error}"
            ) from error

    # ----------------------------------------------
    # PDF FILES
    # ----------------------------------------------

    if ext == ".pdf":

        text_parts = []

        try:
            with fitz.open(
                stream=file_bytes,
                filetype="pdf"
            ) as document:

                if document.needs_pass:
                    raise RuntimeError(
                        "This PDF is password-protected. "
                        "Please provide an accessible document."
                    )

                if len(document) == 0:
                    raise RuntimeError(
                        "The PDF contains no pages."
                    )

                for page_number, page in enumerate(
                    document,
                    start=1
                ):

                    native_text = page.get_text().strip()

                    # Use OCR if native PDF text looks incomplete.
                    if is_text_poor_quality(native_text):

                        try:
                            pixmap = page.get_pixmap(
                                dpi=250,
                                alpha=False
                            )

                            image = Image.open(
                                io.BytesIO(
                                    pixmap.tobytes("png")
                                )
                            )

                            ocr_text = perform_ocr(image)

                            if ocr_text:
                                page_text = ocr_text

                            elif native_text:
                                page_text = native_text

                            else:
                                raise RuntimeError(
                                    f"No readable text detected "
                                    f"on PDF page {page_number}."
                                )

                        except Exception as error:

                            if native_text:
                                raise RuntimeError(
                                    f"OCR failed on PDF page "
                                    f"{page_number}: {error}"
                                ) from error

                            raise RuntimeError(
                                f"Could not extract text from "
                                f"PDF page {page_number}: {error}"
                            ) from error

                    else:
                        page_text = native_text

                    text_parts.append(page_text)

            extracted_text = "\n".join(
                text_parts
            ).strip()

            if not extracted_text:
                raise RuntimeError(
                    "PDF opened successfully, but no readable "
                    "text could be extracted."
                )

            return extracted_text

        except RuntimeError:
            raise

        except Exception as error:
            raise RuntimeError(
                f"PDF processing failed for {filename}: {error}"
            ) from error

    # ----------------------------------------------
    # UNSUPPORTED FILE FORMAT
    # ----------------------------------------------

    raise ValueError(
        f"Unsupported file format: {ext or 'unknown'}. "
        "Supported formats: PDF, PNG, JPG, JPEG, WEBP, "
        "BMP, TIFF, TXT, JSON, CSV and TSV."
    )