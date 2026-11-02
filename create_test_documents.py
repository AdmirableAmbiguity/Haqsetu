import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import fitz

OUTPUT_DIR = Path(__file__).resolve().parent / "samples" / "test_files"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def create_image(filename, lines, title):
    img = Image.new("RGB", (700, 320), color=(250, 250, 252))
    d = ImageDraw.Draw(img)
    # Header bar
    d.rectangle([(0, 0), (700, 50)], fill=(37, 99, 235))
    d.text((20, 15), title, fill=(255, 255, 255))
    
    y = 70
    for line in lines:
        d.text((30, y), line, fill=(15, 23, 42))
        y += 35
        
    img.save(OUTPUT_DIR / filename)
    print(f"Created image: {OUTPUT_DIR / filename}")

def create_pdf(filename, title, lines):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842) # A4
    page.insert_text((50, 60), title, fontsize=18, fontname="helv", color=(0.1, 0.2, 0.6))
    y = 120
    for line in lines:
        page.insert_text((50, y), line, fontsize=12, fontname="helv", color=(0.1, 0.1, 0.1))
        y += 30
    doc.save(OUTPUT_DIR / filename)
    doc.close()
    print(f"Created PDF: {OUTPUT_DIR / filename}")

if __name__ == "__main__":
    # 1. Aadhaar PNG (contains R. Kumar)
    create_image("aadhaar_card.png", [
        "UNIQUE IDENTIFICATION AUTHORITY OF INDIA (UIDAI)",
        "Name: R. Kumar",
        "Father's Name: Suresh Kumar",
        "Date of Birth: 15/08/2004",
        "Gender: Male",
        "Address: 123 Main Street, Lucknow, UP - 226001",
        "Aadhaar Number: 9812 4410 4521"
    ], "GOVERNMENT OF INDIA - AADHAAR CARD")

    # 2. Income Certificate PDF (contains Ravi Kumar, 1.5 Lakh)
    create_pdf("income_certificate.pdf", "OFFICE OF THE TEHSILDAR, LUCKNOW (REVENUE DEPT)", [
        "CERTIFICATE OF ANNUAL FAMILY INCOME",
        "Certificate Reference No: UP/INC/2026/8912",
        "Date of Issue: 10/01/2026",
        "Applicant Name: Ravi Kumar",
        "Father's Name: Suresh Kumar",
        "Certified Annual Income: Rs. 1,50,000 (Rupees One Lakh Fifty Thousand Only)",
        "Income Source: Agriculture & Small Business",
        "Validity: 3 Years from date of issuance",
        "Issuing Officer: Tehsildar, Tehsil Sadar, Lucknow"
    ])

    # 3. Caste Certificate PNG
    create_image("caste_certificate.png", [
        "REVENUE & SOCIAL WELFARE DEPARTMENT, UTTAR PRADESH",
        "Certificate No: UP/OBC/2025/11029",
        "Candidate Name: Ravi Kumar",
        "Father's Name: Suresh Kumar",
        "Social Category: Other Backward Class (OBC)",
        "Caste Community: Ahir / Yadav",
        "Competent Authority: Sub-Divisional Magistrate, Lucknow"
    ], "STATE OF UTTAR PRADESH - CASTE CERTIFICATE (OBC)")

    # 4. Marksheet PDF
    create_pdf("marksheet_class12.pdf", "BOARD OF HIGH SCHOOL AND INTERMEDIATE EDUCATION", [
        "SENIOR SECONDARY SCHOOL EXAMINATION MARKSHEET",
        "Candidate Name: Ravi Kumar",
        "Father's Name: Suresh Kumar",
        "Roll Number: 2841092",
        "Year of Passing: 2024",
        "Total Marks: 392 / 500 (78.4% - First Division)",
        "Result: PASSED",
        "Institution: Lucknow Public Inter College"
    ])

    print("All sample test files successfully generated!")
