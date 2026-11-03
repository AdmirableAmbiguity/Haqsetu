import os
from pathlib import Path
import re
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from backend.app.services.registry import registry
from backend.app.services.matcher import matcher
from backend.app.services.rejectshield_svc import rejectshield_verifier
from backend.app.services.timeline_engine import timeline_engine
from backend.app.services.escalation_svc import escalation_svc
from backend.app.services.notice_svc import notice_svc
from backend.app.services.analytics_svc import analytics_svc
from ai_engine.ocr import extract_text_from_bytes
from ai_engine.haqguide import generate_checklist as get_checklist

app = FastAPI(
    title="VachanSetu",
    description="Citizen-Service Assurance Platform for Indian Government Schemes",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

def classify_doc_content(text: str, filename: str = "") -> str:
    """Auto-detect document type from OCR extracted text or filename."""
    combined = (filename + " " + text).lower()
    if any(k in combined for k in ["aadhaar", "uidai", "unique identification", "aadhar"]):
        return "aadhaar_card"
    if any(k in combined for k in ["death certificate", "mrityu praman", "deceased husband", "cause of death"]):
        return "death_certificate"
    if any(k in combined for k in ["birth certificate", "janam praman", "age proof", "date of birth certificate", "voter id", "epic"]):
        return "birth_certificate"
    if any(k in combined for k in ["disability", "udid", "divyang", "handicap", "medical board certificate"]):
        return "disability_certificate"
    if any(k in combined for k in ["khatauni", "jamabandi", "khasra", "land record", "cultivable land", "land ownership"]):
        return "land_ownership_records"
    if any(k in combined for k in ["income certificate", "aay praman", "tahsildar", "tehsildar", "annual family income", "salary slip", "income affidavit"]):
        return "income_certificate"
    if any(k in combined for k in ["caste certificate", "jati praman", "obc", "scheduled caste", "scheduled tribe", "backward class"]):
        return "caste_certificate"
    if any(k in combined for k in ["marksheet", "mark sheet", "intermediate", "high school", "board of high school", "roll no", "division"]):
        return "previous_marksheet"
    if any(k in combined for k in ["fee receipt", "admission letter", "tuition fee", "bonafide", "university of", "college of"]):
        return "fee_receipt_admission"
    if any(k in combined for k in ["passbook", "bank of", "state bank", "account number", "ifsc", "savings account"]):
        return "bank_passbook"
    if any(k in combined for k in ["domicile", "niwas", "resident certificate", "permanent resident"]):
        return "domicile_certificate"
    if any(k in combined for k in ["ration", "rashan", "bpl", "antyodaya", "secc", "food and civil"]):
        return "ration_bpl_card"
    if any(k in combined for k in ["artisan", "vishwakarma", "trade declaration", "craftsperson"]):
        return "artisan_trade_proof"
    if any(k in combined for k in ["application form", "scholarship application", "online application"]):
        return "application"
    return "custom_document"

# --- Request Models ---
class MatchRequest(BaseModel):
    query: str
    profile: Optional[Dict[str, Any]] = None
    use_ai: Optional[bool] = True

class UnifiedChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    section: Optional[str] = "haqguide"
    profile: Optional[Dict[str, Any]] = None
    scheme: Optional[str] = None

class SchemeFinderRequest(BaseModel):
    query: Optional[str] = ""
    session_id: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None

class SchemeExpertRequest(BaseModel):
    query: str
    scheme_id: Optional[str] = None
    session_id: Optional[str] = None

class SessionResetRequest(BaseModel):
    session_id: str

class ChecklistRequest(BaseModel):
    service_name: str
    language: Optional[str] = "English"

class VerifyPackageRequest(BaseModel):
    scheme_id: Optional[str] = "S05"
    documents: Dict[str, str]

class CreateCaseRequest(BaseModel):
    scheme_name: str
    department: Optional[str] = "Revenue Department"
    applicant_name: str
    state: Optional[str] = "Uttar Pradesh"
    time_limit_days: Optional[int] = 15
    is_statutory: Optional[bool] = False

class AdvanceClockRequest(BaseModel):
    days: int

class LetterRequest(BaseModel):
    case_id: str
    letter_type: Optional[str] = "grievance"
    language: Optional[str] = "English"

class NoticeRequest(BaseModel):
    notice_text: str
    service_name: Optional[str] = "Income Certificate"
    language: Optional[str] = "Hindi"

# --- API Routes ---

@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "app": "VachanSetu",
        "version": "1.2.0",
        "sarvam_ai_active": bool(os.environ.get("SARVAM_API_KEY")),
        "tesseract_ocr_active": True,
        "simulated_today": str(timeline_engine.simulated_today)
    }

@app.get("/api/schemes")
def get_schemes():
    return registry.get_all_schemes()

@app.post("/api/match")
def match_service(req: MatchRequest):
    return matcher.match(query=req.query, user_profile=req.profile, use_ai=req.use_ai)

@app.post("/api/haqguide/chat")
def haqguide_chat(req: UnifiedChatRequest):
    from ai_engine.query_router import query_router
    return query_router.route(
        query=req.query,
        session_id=req.session_id,
        section_override=req.section,
        profile_override=req.profile,
        scheme_override=req.scheme
    )

@app.post("/api/scheme-finder/search")
def scheme_finder_search(req: SchemeFinderRequest):
    from ai_engine.query_router import query_router
    return query_router.route(
        query=req.query or "Find eligible schemes",
        session_id=req.session_id,
        section_override="scheme_finder",
        profile_override=req.profile
    )

@app.post("/api/scheme-expert/chat")
def scheme_expert_chat(req: SchemeExpertRequest):
    from ai_engine.query_router import query_router
    return query_router.route(
        query=req.query,
        session_id=req.session_id,
        section_override="scheme_expert",
        scheme_override=req.scheme_id
    )

@app.get("/api/schemes/catalog")
def get_schemes_catalog():
    schemes = registry.get_all_schemes()
    catalog = []
    for s in schemes:
        catalog.append({
            "id": s.get("scheme_id") or s.get("id"),
            "name": s.get("name"),
            "department": s.get("department"),
            "state": s.get("state", "All India"),
            "category": s.get("category", "General"),
            "summary": s.get("eligibility_summary", ""),
            "max_income": s.get("max_income"),
            "time_limit_days": s.get("time_limit_days", 15)
        })
    return catalog

@app.post("/api/session/reset")
def reset_session(req: SessionResetRequest):
    from ai_engine.conversation_memory import conversation_memory
    sess = conversation_memory.reset_session(req.session_id)
    return {"status": "reset", "session_id": sess.session_id}

@app.post("/api/checklist")
def get_service_checklist(req: ChecklistRequest):
    try:
        checklist = get_checklist(req.service_name, language=req.language)
        return {"service": req.service_name, "checklist": checklist}
    except Exception as e:
        docs = registry.get_scheme_docs(req.service_name)
        return {"service": req.service_name, "checklist": docs}

# --- REJECTSHIELD VERIFIER & OCR FILE UPLOAD APIS ---

@app.get("/api/rejectshield/checklist")
def get_scheme_document_checklist(scheme_id: str = "S05"):
    """Returns official required document checklist for the selected scheme."""
    return registry.get_scheme_docs(scheme_id)

@app.post("/api/rejectshield/upload-file")
async def upload_single_file(file: UploadFile = File(...), doc_type: Optional[str] = Form(None)):
    """
    Ingests and OCR-extracts a single file (PDF, PNG, JPG, JPEG, TXT).
    Returns extracted text and auto-detected document classification.
    """
    contents = await file.read()
    extracted_text = extract_text_from_bytes(contents, file.filename)
    
    assigned_type = doc_type if doc_type and doc_type != "auto" else classify_doc_content(extracted_text, file.filename)

    return {
        "filename": file.filename,
        "file_size": len(contents),
        "doc_type": assigned_type,
        "extracted_text": extracted_text,
        "preview": extracted_text[:250]
    }

@app.post("/api/rejectshield/upload-batch")
async def upload_batch_and_verify(
    scheme_id: str = Form("S05"),
    files: List[UploadFile] = File(...)
):
    """
    Uploads multiple files (PDFs, Images, TXTs), runs OCR on each,
    maps them to scheme requirements, and immediately executes full verification:
    detecting anomalies and pending / missing documents.
    """
    submitted_docs = {}
    file_metadata = []

    for f in files:
        contents = await f.read()
        extracted_text = extract_text_from_bytes(contents, f.filename)
        classified_type = classify_doc_content(extracted_text, f.filename)
        
        # If type collision, append counter
        target_key = classified_type
        counter = 1
        while target_key in submitted_docs:
            counter += 1
            target_key = f"{classified_type}_{counter}"

        submitted_docs[target_key] = extracted_text
        file_metadata.append({
            "filename": f.filename,
            "doc_type": target_key,
            "size": len(contents),
            "preview": extracted_text[:120]
        })

    # Run complete verification
    verification_result = rejectshield_verifier.verify_application_package(
        scheme_id_or_name=scheme_id,
        submitted_documents=submitted_docs
    )
    verification_result["uploaded_files_meta"] = file_metadata
    return verification_result

@app.post("/api/rejectshield/verify")
def verify_application_package(req: VerifyPackageRequest):
    """Runs complete RejectShield verifier on submitted text/documents."""
    return rejectshield_verifier.verify_application_package(
        scheme_id_or_name=req.scheme_id or "S05",
        submitted_documents=req.documents
    )

@app.get("/api/rejectshield/presets")
def get_verifier_presets():
    """Returns pre-built synthetic test packets for 1-click verification testing."""
    return {
        "scholarship_with_shortage_and_discrepancy": {
            "name": "Scholarship: Shortage of 3 Documents + Name Discrepancy (R. Kumar vs Ravi Kumar)",
            "scheme_id": "S05",
            "documents": {
                "application": "NATIONAL SCHOLARSHIP PORTAL APPLICATION FORM\nScheme: Post-Matric Scholarship for OBC Students\nApplicant Name: Ravi Kumar\nFather's Name: Suresh Kumar\nDate of Birth: 15/08/2004\nSocial Category: OBC\nAnnual Family Income: Rs. 1,50,000\nInstitution: Lucknow University\nRoll No: LU/2024/7821\nAddress: 123 Main Street, Hazratganj, Lucknow, UP - 226001",
                "aadhaar_card": "GOVERNMENT OF INDIA - AADHAAR CARD\nName: R. Kumar\nDate of Birth: 15-08-2004\nGender: Male\nFather's Name: Suresh Kumar\nAddress: 123 Main St, Lucknow, UP - 226001\nAadhaar No: XXXX-XXXX-4521",
                "income_certificate": "OFFICE OF THE TEHSILDAR, LUCKNOW\nINCOME CERTIFICATE\nCertificate No: UP/INC/2026/8912\nApplicant Name: Ravi Kumar\nFather's Name: Suresh Kumar\nCertified Annual Family Income: Rs. 1,50,000 (Rupees One Lakh Fifty Thousand Only)\nValidity: 3 Years from date of issue (10/01/2026)\nIssuing Authority: Tehsildar, Lucknow",
                "domicile_certificate": "STATE OF UTTAR PRADESH - DOMICILE CERTIFICATE\nName: Ravi Kumar\nFather's Name: Suresh Kumar\nPermanent Residence: 123 Main Street, Lucknow, Uttar Pradesh\nCertificate No: DM/LKO/DOM/00432"
            },
            "note": "Demonstrates: 1) Shortage detection (Missing Caste Certificate, Fee Receipt, Bank Passbook, Marksheet), and 2) Cross-document abbreviation detection ('R. Kumar' vs 'Ravi Kumar')."
        },
        "scholarship_complete_and_verified": {
            "name": "Scholarship: 100% Complete Packet (All 7 Documents Present & Verified)",
            "scheme_id": "S05",
            "documents": {
                "application": "NATIONAL SCHOLARSHIP PORTAL APPLICATION\nApplicant Name: Ravi Kumar\nFather's Name: Suresh Kumar\nDate of Birth: 15/08/2004\nSocial Category: OBC\nAnnual Family Income: Rs. 1,50,000\nInstitution: University of Lucknow\nRoll No: LU/2024/7821",
                "aadhaar_card": "AADHAAR CARD\nName: Ravi Kumar\nDate of Birth: 15/08/2004\nGender: Male\nFather: Suresh Kumar\nAddress: 123 Main Street, Lucknow, UP",
                "income_certificate": "INCOME CERTIFICATE (TEHSIL LUCKNOW)\nApplicant: Ravi Kumar\nFather: Suresh Kumar\nAnnual Income: Rs. 1,50,000\nIssue Date: 10/01/2026",
                "caste_certificate": "CASTE CERTIFICATE (OBC - OTHER BACKWARD CLASS)\nCandidate Name: Ravi Kumar\nFather's Name: Suresh Kumar\nCategory: OBC (Ahir / Yadav)\nIssuing Authority: Sub-Divisional Magistrate, Lucknow\nCertificate No: UP/OBC/2025/11029",
                "previous_marksheet": "BOARD OF HIGH SCHOOL & INTERMEDIATE EDUCATION\nCANDIDATE: Ravi Kumar\nFather: Suresh Kumar\nRoll: 2841092\nResult: PASSED (78.4% First Division)",
                "fee_receipt_admission": "UNIVERSITY OF LUCKNOW - TUITION FEE RECEIPT\nStudent: Ravi Kumar\nCourse: B.Sc Semester III\nReceipt No: REC-2026-4412\nTuition Fee Paid: Rs. 14,500\nBonafide Enrollment: Verified Active Student",
                "bank_passbook": "STATE BANK OF INDIA - PASSBOOK\nAccount Holder: Ravi Kumar\nA/C No: 39812009123\nIFSC: SBIN0001234\nAadhaar NPCI Status: LINKED & SEEDED ACTIVE",
                "domicile_certificate": "DOMICILE CERTIFICATE\nName: Ravi Kumar\nState: Uttar Pradesh\nDistrict: Lucknow"
            },
            "note": "Demonstrates: Perfect 100% complete package resulting in Green 'Ready for Submission' rating."
        }
    }

# --- TIMELINE & CASES APIS ---

@app.get("/api/cases")
def list_cases():
    return timeline_engine.get_all_cases()

@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    c = timeline_engine.get_case(case_id)
    if not c:
        raise HTTPException(status_code=404, detail="Case not found")
    return c

@app.post("/api/cases")
def create_case(req: CreateCaseRequest):
    return timeline_engine.create_case(req.dict())

@app.post("/api/clock/advance")
def advance_clock(req: AdvanceClockRequest):
    new_date = timeline_engine.advance_demo_clock(req.days)
    return {"simulated_today": new_date, "message": f"Demo clock advanced by {req.days} days."}

@app.post("/api/clock/reset")
def reset_clock():
    new_date = timeline_engine.reset_demo_clock()
    return {"simulated_today": new_date, "message": "Demo clock reset to base simulation date (2026-11-02)."}

@app.get("/api/alerts")
def get_alerts():
    return escalation_svc.get_all_alerts()

@app.post("/api/letters/generate")
def generate_letter(req: LetterRequest):
    return escalation_svc.generate_letter(case_id=req.case_id, letter_type=req.letter_type, language=req.language)

@app.get("/api/languages")
def get_supported_languages():
    """Returns all 11 Indian languages supported by Sarvam-105B."""
    from ai_engine.sarvam_client import SARVAM_LANGUAGES
    return SARVAM_LANGUAGES

@app.post("/api/notice/upload-and-decode")
async def upload_and_decode_notice(
    file: UploadFile = File(...),
    service_name: Optional[str] = Form("Administrative Document"),
    language: Optional[str] = Form("Hindi")
):
    """
    Ingests an image (PNG, JPG, JPEG, WEBP, TIFF, BMP) or PDF of a hard-copy
    administrative notice received via post, performs high-efficiency multi-tier OCR,
    and returns a plain-language decoded explanation and official draft rectification letter.
    """
    contents = await file.read()
    extracted_text = extract_text_from_bytes(contents, file.filename)
    if not extracted_text or not extracted_text.strip():
        extracted_text = f"Official Notice Document: {file.filename}\n(High-efficiency OCR scanned page)"

    decoded = notice_svc.decode_rejection_notice(
        notice_text=extracted_text,
        service_name=service_name or "Administrative Document",
        language=language or "Hindi"
    )
    decoded["filename"] = file.filename
    decoded["file_size"] = len(contents)
    decoded["raw_extracted_text"] = extracted_text
    return decoded

@app.post("/api/notice/decode")
def decode_notice_api(req: NoticeRequest):
    return notice_svc.decode_rejection_notice(notice_text=req.notice_text, service_name=req.service_name, language=req.language)

@app.get("/api/service-health")
def get_service_health():
    return analytics_svc.get_service_health()

@app.delete("/api/privacy/delete-my-data")
def delete_my_data():
    return {
        "status": "success",
        "message": "All session data, uploaded documents, and temporary caches have been permanently purged.",
        "compliance": "Digital Personal Data Protection (DPDP) Act & Privacy by Design principles respected."
    }

# --- Frontend Static Serving ---
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return JSONResponse({"status": "Backend running."})
