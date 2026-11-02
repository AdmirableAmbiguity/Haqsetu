import json
import os
from pathlib import Path
from typing import Dict, List, Any

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

# Comprehensive official document checklists per scheme
SCHEME_DOC_REGISTRY = {
    "S05": {
        "scheme_name": "National Scholarship Portal (Pre/Post-Matric Scholarship)",
        "department": "Ministry of Social Justice & Ministry of Tribal Affairs / State Welfare Dept",
        "category": "Scholarship",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Aadhaar Card (Identity & Domicile Proof)",
                "mandatory": True,
                "purpose": "Aadhaar authentication and DBT bank account seeding (mandatory under Section 7 of Aadhaar Act).",
                "authority": "UIDAI"
            },
            {
                "id": "income_certificate",
                "name": "Family Income Certificate",
                "mandatory": True,
                "purpose": "Proof of annual household income not exceeding ₹2,50,000 (must be issued within the last 12 months).",
                "authority": "Tehsildar / Sub-Divisional Magistrate (Revenue Dept)"
            },
            {
                "id": "caste_certificate",
                "name": "Caste / Category Certificate (OBC/SC/ST/EWS)",
                "mandatory": True,
                "purpose": "Verification of social category eligibility for category-specific scholarship quotas.",
                "authority": "District Magistrate / Competent Revenue Authority"
            },
            {
                "id": "previous_marksheet",
                "name": "Previous Year Academic Marksheet",
                "mandatory": True,
                "purpose": "Proof of academic progression with minimum required pass percentage (min 50% for post-matric).",
                "authority": "Recognized School / University Board"
            },
            {
                "id": "fee_receipt_admission",
                "name": "College / Institute Current Year Fee Receipt & Bonafide Certificate",
                "mandatory": True,
                "purpose": "Proof of active regular enrollment and exact non-refundable tuition fee claim.",
                "authority": "Head of Recognized Institution / College Registrar"
            },
            {
                "id": "bank_passbook",
                "name": "Bank Account Passbook / Statement (Aadhaar Seeded)",
                "mandatory": True,
                "purpose": "Proof of active individual savings account in applicant's name with NPCI Aadhaar bridge mapping.",
                "authority": "Scheduled Commercial Bank / Post Office"
            },
            {
                "id": "domicile_certificate",
                "name": "Domicile / Resident Certificate",
                "mandatory": False,
                "purpose": "Proof of continuous residence within the respective state.",
                "authority": "Tehsil / e-District Portal"
            }
        ]
    },
    "S13": {
        "scheme_name": "Income Certificate (State e-District Service)",
        "department": "Revenue Department (Tehsil / District Administration)",
        "category": "Revenue & Certificates",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Aadhaar Card / Photo Identity Proof",
                "mandatory": True,
                "purpose": "Identity and primary residential address proof.",
                "authority": "UIDAI"
            },
            {
                "id": "salary_slip_affidavit",
                "name": "Income Affidavit / Salary Slip / ITR",
                "mandatory": True,
                "purpose": "Self-declaration of family income on non-judicial stamp paper or employer salary certificate.",
                "authority": "Notary Public / Employer / IT Dept"
            },
            {
                "id": "ration_bpl_card",
                "name": "Ration Card or BPL / Antyodaya Card",
                "mandatory": True,
                "purpose": "Proof of family composition and dependency.",
                "authority": "Food & Civil Supplies Department"
            },
            {
                "id": "property_tax_land_record",
                "name": "Land Record (Khatauni) or Electricity / Municipal Tax Bill",
                "mandatory": False,
                "purpose": "Proof of immovable agricultural land or property holding in district.",
                "authority": "Revenue / Municipal Authority"
            }
        ]
    },
    "S01": {
        "scheme_name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "department": "Ministry of Agriculture & Farmers Welfare",
        "category": "Agriculture",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Aadhaar Card",
                "mandatory": True,
                "purpose": "Mandatory Aadhaar authentication for DBT transfer.",
                "authority": "UIDAI"
            },
            {
                "id": "land_ownership_records",
                "name": "Land Ownership Record (Khatauni / Jamabandi)",
                "mandatory": True,
                "purpose": "Proof of cultivable landholding in applicant's name.",
                "authority": "Revenue Department / Patwari"
            },
            {
                "id": "bank_passbook",
                "name": "Aadhaar-Linked Bank Account Passbook",
                "mandatory": True,
                "purpose": "Direct Benefit Transfer bank routing.",
                "authority": "Bank / Post Office"
            }
        ]
    },
    "S02": {
        "scheme_name": "Ayushman Bharat PM-JAY (Golden Card)",
        "department": "National Health Authority",
        "category": "Healthcare",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Aadhaar Card",
                "mandatory": True,
                "purpose": "Biometric e-KYC authentication.",
                "authority": "UIDAI"
            },
            {
                "id": "ration_bpl_card",
                "name": "Ration Card or SECC-2011 Household Reference Letter",
                "mandatory": True,
                "purpose": "Proof of inclusion in SECC deprivation criteria.",
                "authority": "Civil Supplies / State Health Agency"
            }
        ]
    }
}

class PromiseRegistry:
    def __init__(self):
        self.schemes = []
        self.timeline_scenarios = []
        self.load_data()

    def load_data(self):
        matcher_path = DATA_DIR / "eligibility_matcher_dataset.json"
        timeline_path = DATA_DIR / "timeline_tracker_dataset.json"

        if matcher_path.exists():
            with open(matcher_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.schemes = data.get("scheme_catalog", [])

        if timeline_path.exists():
            with open(timeline_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.timeline_scenarios = data.get("records", [])

        # Enrich schemes with document registries
        for s in self.schemes:
            sid = s.get("scheme_id") or s.get("id")
            if sid in SCHEME_DOC_REGISTRY:
                s["doc_registry"] = SCHEME_DOC_REGISTRY[sid]
            else:
                # Default document requirements
                s["doc_registry"] = {
                    "scheme_name": s.get("name"),
                    "department": s.get("department", "State / Central Ministry"),
                    "required_documents": [
                        {"id": "aadhaar_card", "name": "Aadhaar Identity Card", "mandatory": True, "purpose": "Identity Verification", "authority": "UIDAI"},
                        {"id": "income_certificate", "name": "Income Certificate", "mandatory": True, "purpose": "Income Proof", "authority": "Revenue Dept"},
                        {"id": "domicile_certificate", "name": "Domicile / Residence Certificate", "mandatory": False, "purpose": "State Residence Proof", "authority": "Tehsil"}
                    ]
                }

    def get_all_schemes(self):
        return self.schemes

    def get_scheme_by_id(self, scheme_id):
        for s in self.schemes:
            if s.get("scheme_id") == scheme_id or s.get("id") == scheme_id:
                return s
        return None

    def get_scheme_docs(self, scheme_id_or_name: str) -> Dict[str, Any]:
        """Lookup required document checklist by scheme id or fuzzy name."""
        for s in self.schemes:
            sid = s.get("scheme_id") or s.get("id")
            sname = s.get("name", "").lower()
            if sid == scheme_id_or_name or scheme_id_or_name.lower() in sname:
                return s.get("doc_registry", SCHEME_DOC_REGISTRY.get("S05"))
        # Fallback to Scholarship if 'scholarship' in query
        if "scholar" in scheme_id_or_name.lower():
            return SCHEME_DOC_REGISTRY["S05"]
        if "income" in scheme_id_or_name.lower():
            return SCHEME_DOC_REGISTRY["S13"]
        return SCHEME_DOC_REGISTRY["S05"]

    def get_timeline_scenarios(self):
        return self.timeline_scenarios

registry = PromiseRegistry()
