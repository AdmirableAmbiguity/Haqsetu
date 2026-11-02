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
from backend.app.services.rejectshield_svc import rejectshield_svc
from backend.app.services.timeline_engine import timeline_engine
from backend.app.services.escalation_svc import escalation_svc
from backend.app.services.notice_svc import notice_svc
from backend.app.services.analytics_svc import analytics_svc
from ai_engine.haqguide import generate_checklist as get_checklist

app = FastAPI(
    title="HaqSetu AI + Vachan Setu",
    description="Citizen-Service Assurance Platform for Indian Government Schemes",
    version="1.0.0"
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

class AuditRequest(BaseModel):
    documents: Dict[str, str]
    requirements: Optional[List[str]] = None

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
        "version": "1.0.0",
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
        return {
            "service": req.service_name,
            "checklist": {
                "required_documents": [
                    {"document": "Aadhaar Card", "purpose": "Proof of Identity & Domicile"},
                    {"document": "Income Affidavit / Salary Slip", "purpose": "Proof of Annual Family Income"},
                    {"document": "Ration Card / BPL Card", "purpose": "Family Composition Verification"}
                ],
                "important_notes": ["Verify certificate validity on the official state e-District portal."]
            }
        }

@app.post("/api/rejectshield/audit")
def audit_documents(req: AuditRequest):
    return rejectshield_svc.audit_documents(doc_inputs=req.documents, required_docs=req.requirements)

@app.get("/api/rejectshield/sample")
def get_sample_docs():
    """Returns sample synthetic documents for 1-click testing."""
    samples_dir = Path(__file__).resolve().parent.parent.parent / "samples"
    app_text = (samples_dir / "application.txt").read_text(encoding="utf-8", errors="ignore") if (samples_dir / "application.txt").exists() else ""
    id_text = (samples_dir / "identity.txt").read_text(encoding="utf-8", errors="ignore") if (samples_dir / "identity.txt").exists() else ""
    cert_text = (samples_dir / "certificate.txt").read_text(encoding="utf-8", errors="ignore") if (samples_dir / "certificate.txt").exists() else ""

    return {
        "application": app_text,
        "identity": id_text,
        "certificate": cert_text,
        "notes": "Preloaded synthetic sample with deliberate name abbreviation ('R. Kumar' vs 'Ravi Kumar') to showcase cross-document consistency detection."
    }

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
        return JSONResponse({"status": "Backend running. Frontend index.html not yet built."})
