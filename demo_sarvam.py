"""
VachanSetu — Sarvam-105B Integration Demo
==========================================
Demonstrates the Sarvam-powered AI modules:
  1. HaqGuide: Service finder + eligibility + checklist
  2. RejectShield: AI-powered document audit
  3. NoticeDecoder: Rejection notice explanation

Set SARVAM_API_KEY environment variable before running.
Usage: python demo_sarvam.py
"""

import os
import json

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def demo_haqguide():
    print("\n" + "=" * 60)
    print("MODULE 1: HaqGuide — Know Your Rights")
    print("=" * 60)

    from ai_engine.haqguide import find_service, generate_checklist, explain_eligibility

    # 1. Service finder
    query = "My family needs an income certificate for a scholarship. What should I do first?"
    print(f"\nCitizen Query: {query}")
    print("\nFinding relevant service...")
    service = find_service(query)
    print(f"Service Identified: {json.dumps(service, ensure_ascii=False, indent=2)}")

    # 2. Document checklist
    if isinstance(service, dict) and service.get("service_name"):
        service_name = service["service_name"]
        print(f"\nGenerating checklist for: {service_name}")
        checklist = generate_checklist(
            service_name,
            citizen_profile={"state": "Uttar Pradesh", "purpose": "scholarship"}
        )
        print(json.dumps(checklist, ensure_ascii=False, indent=2))

        # 3. Eligibility
        print(f"\nEligibility explanation (Hindi):")
        eligibility = explain_eligibility(service_name, language="Hindi")
        print(eligibility)


def demo_document_audit():
    print("\n" + "=" * 60)
    print("MODULE 2: RejectShield — AI Document Audit")
    print("=" * 60)

    # Create synthetic sample documents for demo
    os.makedirs("samples", exist_ok=True)

    with open("samples/application.txt", "w", encoding="utf-8") as f:
        f.write("""
INCOME CERTIFICATE APPLICATION FORM
Name: Ravi Kumar
Date of Birth: 15/08/1990
Father's Name: Suresh Kumar
Address: 123 Main Street, Lucknow, Uttar Pradesh - 226001
Annual Income: Rs. 1,50,000
Purpose: Scholarship
Application Date: 01/11/2026
""")

    with open("samples/identity.txt", "w", encoding="utf-8") as f:
        f.write("""
AADHAAR CARD
Name: R. Kumar
Date of Birth: 15-08-1990
Gender: Male
Address: 123 Main St, Lucknow, UP - 226001
Aadhaar: XXXX XXXX 4521
""")

    with open("samples/certificate.txt", "w", encoding="utf-8") as f:
        f.write("""
DOMICILE CERTIFICATE
Name: Ravi Kumar
Father's Name: Suresh Kumar
Date of Birth: 15/08/1990
Permanent Address: 123 Main Street, Lucknow, Uttar Pradesh
Issue Date: 10/01/2025
Issuing Authority: District Magistrate, Lucknow
Certificate No: DM/LKO/2025/00123
""")

    from ai_engine.sarvam_auditor import audit_application

    document_paths = {
        "application": "samples/application.txt",
        "identity": "samples/identity.txt",
        "certificate": "samples/certificate.txt",
    }
    requirements = ["application", "identity", "certificate", "income_proof"]

    print("\nRunning AI-powered document audit...")
    report = audit_application(document_paths, requirements)

    print(f"\nOverall Status: {report['overall_status']}")
    print(f"Documents Processed: {report['documents_processed']}")

    print("\nFindings:")
    for finding in report["findings"]:
        print(f"  [{finding.get('severity', '?').upper()}] {finding.get('type')}: {finding.get('explanation', '')}")

    if report.get("ai_summary"):
        summary = report["ai_summary"]
        print(f"\nAI Readiness Report:")
        print(f"  Verdict: {summary.get('verdict')} ({summary.get('verdict_hindi', '')})")
        print(f"  Summary: {summary.get('summary_english', '')}")
        print(f"  Hindi: {summary.get('summary_hindi', '')}")
        print(f"  Can Submit: {summary.get('can_submit')}")


def demo_notice_decoder():
    print("\n" + "=" * 60)
    print("MODULE 3: NoticeDecoder — Understand Your Rejection")
    print("=" * 60)

    from ai_engine.notice_decoder import decode_notice, suggest_next_steps, draft_response_letter

    notice = """
OFFICE OF THE DISTRICT MAGISTRATE, LUCKNOW
Date: 28/10/2026
Application No: LKO/IC/2026/4521
Subject: Return of Income Certificate Application

Your application for Income Certificate has been returned for the following reasons:
1. Income proof document (salary slip/bank statement) not attached
2. Name on application form does not match identity proof

Please re-submit with the required corrections within 15 days.
District Magistrate
Lucknow
"""

    print("\nDecoding rejection notice...")
    decoded = decode_notice(notice, service_name="Income Certificate")
    print(json.dumps(decoded, ensure_ascii=False, indent=2))

    print("\nSuggesting next steps (Hindi)...")
    steps = suggest_next_steps(notice, service_name="Income Certificate", language="Hindi")
    print(steps)

    print("\nDrafting response letter...")
    letter = draft_response_letter(
        notice_text=notice,
        applicant_name="Ravi Kumar",
        application_ref="LKO/IC/2026/4521",
        service_name="Income Certificate",
    )
    print(letter)


if __name__ == "__main__":
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        print("ERROR: Please set SARVAM_API_KEY environment variable")
        print("Get your key at: https://dashboard.sarvam.ai")
        print("Then run: set SARVAM_API_KEY=your_key_here")
        exit(1)

    print("VachanSetu — Sarvam-105B Integration Demo")
    print(f"Using model: sarvam-105b")

    try:
        demo_haqguide()
    except Exception as e:
        print(f"HaqGuide demo error: {e}")

    try:
        demo_document_audit()
    except Exception as e:
        print(f"Document audit demo error: {e}")

    try:
        demo_notice_decoder()
    except Exception as e:
        print(f"NoticeDecoder demo error: {e}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)
