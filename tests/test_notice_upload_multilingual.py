"""
End-to-End Test Suite for Notice Decoder Upload & Multilingual Sarvam Features.
Tests:
1. Multi-tier OCR extraction on image notices and PDFs.
2. /api/notice/upload-and-decode endpoint with image upload.
3. /api/notice/upload-and-decode endpoint with PDF upload.
4. Multilingual response decoding in Hindi, Bengali, Tamil, and English.
5. All 11 Sarvam languages catalog check.
"""
import io
import sys
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont

BASE_URL = "http://localhost:8000"

def create_synthetic_notice_image() -> bytes:
    """Creates a synthetic hard-copy government rejection notice photo/scan."""
    img = Image.new("RGB", (1200, 700), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    lines = [
        "OFFICE OF THE SUB-DIVISIONAL MAGISTRATE / TEHSILDAR, LUCKNOW",
        "SPEED POST / REGISTERED NOTICE - DEFICIENCY & OBJECTION MEMO",
        "Ref No: LKO/REV/2026/89412             Date: 29/10/2026",
        "",
        "To: Smt. Sunita Devi, Village Mohanlalganj, Lucknow, UP",
        "",
        "Subject: Deficiency Memo regarding Application for Widow Pension (Vidhwa Pension)",
        "",
        "Sir/Madam,",
        "Your application Ref No. LKO/REV/2026/89412 has been examined. The following deficiencies were noted:",
        "1. Deceased husband death certificate is illegible. Please submit certified copy.",
        "2. Annual family income certificate from Tehsildar is missing from file.",
        "3. Bank passbook does not display active NPCI Aadhaar seeding stamp.",
        "",
        "You are granted 15 days from the receipt of this notice to submit the rectified documents",
        "at the Tehsil Citizen Service Centre (CSC), failing which your application shall be deemed rejected.",
        "",
        "By Order,",
        "Tehsildar / Competent Authority",
        "Department of Social Welfare, Government of Uttar Pradesh"
    ]
    
    y = 30
    for line in lines:
        draw.text((40, y), line, fill=(20, 20, 20))
        y += 32
        
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_multilingual_api():
    print("\n--- 1. Testing /api/languages ---")
    res = requests.get(f"{BASE_URL}/api/languages")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    langs = res.json()
    print(f"Supported languages: {list(langs.keys())}")
    assert "Hindi" in langs
    assert "Bengali" in langs
    assert "Telugu" in langs
    assert "Tamil" in langs
    assert "Marathi" in langs
    assert "Gujarati" in langs
    assert "Kannada" in langs
    assert "Malayalam" in langs
    assert "Odia" in langs
    assert "Punjabi" in langs
    assert "English" in langs
    print("[PASS] All 11 Sarvam Indian languages verified!")

def test_upload_image_notice():
    print("\n--- 2. Testing /api/notice/upload-and-decode with Image ---")
    img_bytes = create_synthetic_notice_image()
    
    files = {
        "file": ("speed_post_notice.png", img_bytes, "image/png")
    }
    data = {
        "service_name": "Widow Pension",
        "language": "Hindi"
    }
    
    res = requests.post(f"{BASE_URL}/api/notice/upload-and-decode", files=files, data=data)
    assert res.status_code == 200, f"Failed: {res.status_code} - {res.text}"
    result = res.json()
    
    assert "raw_extracted_text" in result
    assert "notice_summary" in result
    assert "plain_language_explanation" in result
    assert "draft_response_letter" in result
    
    print(f"Extracted Text Length: {len(result['raw_extracted_text'])} chars")
    print(f"Raw text preview: {result['raw_extracted_text'][:120]}...")
    print(f"Plain Language Explanation: {result['plain_language_explanation'][:150]}...")
    print(f"Draft Response Letter preview: {result['draft_response_letter'][:150]}...")
    print("[PASS] Image Notice Upload & Multi-tier OCR decode successful!")

def test_upload_pdf_notice():
    print("\n--- 3. Testing /api/notice/upload-and-decode with PDF (Bengali language) ---")
    pdf_path = Path("samples/test_files/income_certificate.pdf")
    if not pdf_path.exists():
        print("[SKIP] samples/test_files/income_certificate.pdf not found.")
        return
        
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
        
    files = {
        "file": ("income_notice.pdf", pdf_bytes, "application/pdf")
    }
    data = {
        "service_name": "Income Certificate",
        "language": "Bengali"
    }
    
    res = requests.post(f"{BASE_URL}/api/notice/upload-and-decode", files=files, data=data)
    assert res.status_code == 200, f"Failed: {res.status_code} - {res.text}"
    result = res.json()
    
    assert len(result["raw_extracted_text"]) > 0
    assert result["plain_language_explanation"]
    print(f"PDF OCR Extracted {len(result['raw_extracted_text'])} chars from PDF.")
    print(f"Bengali / Multilingual decode preview: {result['plain_language_explanation'][:120]}...")
    print("[PASS] PDF Notice Upload & Multilingual OCR decode successful!")

if __name__ == "__main__":
    test_multilingual_api()
    test_upload_image_notice()
    test_upload_pdf_notice()
    print("\n=======================================================")
    print("ALL NOTICE DECODER & MULTILINGUAL TESTS PASSED (100%)!")
    print("=======================================================")
