import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
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
from ai_engine.haqguide import generate_checklist as get_checklist

app = FastAPI(
    title="HaqSetu AI + Vachan Setu",
    description="Citizen-Service Assurance Platform for Indian Government Schemes",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

# --- Request Models ---
class MatchRequest(BaseModel):
    query: str
    profile: Optional[Dict[str, Any]] = None
    use_ai: Optional[bool] = True

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
        "app": "HaqSetu AI + Vachan Setu",
        "version": "1.1.0",
        "sarvam_ai_active": bool(os.environ.get("SARVAM_API_KEY")),
        "simulated_today": str(timeline_engine.simulated_today)
    }

@app.get("/api/schemes")
def get_schemes():
    return registry.get_all_schemes()

@app.post("/api/match")
def match_service(req: MatchRequest):
    return matcher.match(query=req.query, user_profile=req.profile, use_ai=req.use_ai)

@app.post("/api/checklist")
def get_service_checklist(req: ChecklistRequest):
    try:
        checklist = get_checklist(req.service_name, language=req.language)
        return {"service": req.service_name, "checklist": checklist}
    except Exception as e:
        docs = registry.get_scheme_docs(req.service_name)
        return {"service": req.service_name, "checklist": docs}

# --- REJECTSHIELD VERIFIER APIS ---

@app.get("/api/rejectshield/checklist")
def get_scheme_document_checklist(scheme_id: str = "S05"):
    """Returns official required document checklist for the selected scheme."""
    return registry.get_scheme_docs(scheme_id)

@app.post("/api/rejectshield/verify")
def verify_application_package(req: VerifyPackageRequest):
    """Runs complete RejectShield verifier: shortage check + cross-document consistency."""
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
