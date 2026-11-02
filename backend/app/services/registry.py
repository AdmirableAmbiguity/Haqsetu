import json
import os
from pathlib import Path
from typing import Dict, List, Any

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

# Comprehensive official document checklists per scheme for all registered schemes
SCHEME_DOC_REGISTRY = {
    "S01": {
        "scheme_name": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
        "department": "Ministry of Agriculture & Farmers Welfare",
        "category": "Agriculture",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Aadhaar Card",
                "mandatory": True,
                "purpose": "Mandatory Aadhaar authentication for DBT transfer under Section 7 of Aadhaar Act.",
                "authority": "UIDAI"
            },
            {
                "id": "land_ownership_records",
                "name": "Land Ownership Record (Khatauni / Jamabandi)",
                "mandatory": True,
                "purpose": "Proof of cultivable landholding in applicant's name verified by revenue authorities.",
                "authority": "Revenue Department / Patwari"
            },
            {
                "id": "bank_passbook",
                "name": "Aadhaar-Linked Bank Account Passbook",
                "mandatory": True,
                "purpose": "Direct Benefit Transfer (DBT) bank routing and NPCI active mapping.",
                "authority": "Scheduled Bank / Post Office"
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
                "purpose": "Biometric e-KYC authentication and patient identity verification.",
                "authority": "UIDAI"
            },
            {
                "id": "ration_bpl_card",
                "name": "Ration Card or SECC-2011 Household Reference Letter",
                "mandatory": True,
                "purpose": "Proof of inclusion in SECC deprivation criteria or NFSA active beneficiary list.",
                "authority": "Civil Supplies / State Health Agency"
            }
        ]
    },
    "S03": {
        "scheme_name": "PMAY-Gramin (Pradhan Mantri Awas Yojana - Gramin)",
        "department": "Ministry of Rural Development",
        "category": "Housing",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Aadhaar Card",
                "mandatory": True,
                "purpose": "Identity and family head biometric authentication.",
                "authority": "UIDAI"
            },
            {
                "id": "bank_passbook",
                "name": "Bank Account Passbook (Aadhaar Seeded)",
                "mandatory": True,
                "purpose": "Direct installment disbursement for house construction.",
                "authority": "Scheduled Bank / Regional Rural Bank"
            },
            {
                "id": "ration_bpl_card",
                "name": "MGNREGA Job Card / SECC Household Registration",
                "mandatory": True,
                "purpose": "Proof of rural deprivation status and 90-day construction labor credit.",
                "authority": "Gram Panchayat / Rural Development Dept"
            },
            {
                "id": "land_record",
                "name": "Homestead Land Title / Allotment Certificate",
                "mandatory": True,
                "purpose": "Proof of undisputed land possession for residential unit construction.",
                "authority": "Tehsildar / Gram Sabha"
            }
        ]
    },
    "S04": {
        "scheme_name": "NSAP - Indira Gandhi National Old Age Pension",
        "department": "Department of Social Welfare",
        "category": "Social Security",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Aadhaar Card",
                "mandatory": True,
                "purpose": "Biometric identity verification and demographic age matching.",
                "authority": "UIDAI"
            },
            {
                "id": "age_proof",
                "name": "Age Proof Certificate (Voter ID / Birth Certificate / Medical Certificate)",
                "mandatory": True,
                "purpose": "Verification of attaining statutory age threshold (60+ years).",
                "authority": "Election Commission / Chief Medical Officer"
            },
            {
                "id": "income_certificate",
                "name": "BPL Household Card / Certified Family Income Certificate",
                "mandatory": True,
                "purpose": "Proof of living below statutory poverty threshold.",
                "authority": "Tehsildar / Block Development Officer"
            },
            {
                "id": "bank_passbook",
                "name": "Single Bank Account Passbook",
                "mandatory": True,
                "purpose": "Monthly direct social security pension deposit.",
                "authority": "Public Sector Bank / Post Office"
            }
        ]
    },
    "S05": {
        "scheme_name": "National Scholarship Portal (Pre/Post-Matric Scholarship)",
        "department": "Ministry of Social Justice & Ministry of Tribal Affairs / State Welfare Dept",
        "category": "Scholarship",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Aadhaar Card (Identity Proof)",
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
    "S06": {
        "scheme_name": "PM Matru Vandana Yojana (PMMVY)",
        "department": "Ministry of Women and Child Development",
        "category": "Women & Child",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Beneficiary Mother's Aadhaar Card",
                "mandatory": True,
                "purpose": "Primary biometric identity verification.",
                "authority": "UIDAI"
            },
            {
                "id": "mcp_card",
                "name": "Mother and Child Protection (MCP) Card",
                "mandatory": True,
                "purpose": "Proof of institutional ante-natal check-up and infant vaccination.",
                "authority": "Anganwadi Worker / Primary Health Centre (PHC)"
            },
            {
                "id": "bank_passbook",
                "name": "Mother's Individual Bank Account Passbook",
                "mandatory": True,
                "purpose": "Direct Benefit Transfer installment credit.",
                "authority": "Scheduled Bank / Post Office"
            },
            {
                "id": "husband_aadhaar",
                "name": "Husband's Identity Proof",
                "mandatory": False,
                "purpose": "Family record compilation.",
                "authority": "UIDAI / Election Commission"
            }
        ]
    },
    "S07": {
        "scheme_name": "PM Ujjwala Yojana (PMUY)",
        "department": "Ministry of Petroleum & Natural Gas",
        "category": "Welfare",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Adult Female Family Head Aadhaar Card",
                "mandatory": True,
                "purpose": "Mandatory biometric e-KYC for subsidized LPG connection.",
                "authority": "UIDAI"
            },
            {
                "id": "ration_bpl_card",
                "name": "BPL Ration Card / Deprivation Certificate",
                "mandatory": True,
                "purpose": "Proof of poor household identification as per SECC / State Ration database.",
                "authority": "Food & Civil Supplies Department"
            },
            {
                "id": "bank_passbook",
                "name": "Aadhaar-Linked Bank Account Passbook",
                "mandatory": True,
                "purpose": "LPG subsidy direct debit transfer routing.",
                "authority": "Scheduled Bank"
            },
            {
                "id": "domicile_certificate",
                "name": "Proof of Residence / Utility Bill",
                "mandatory": False,
                "purpose": "Installation address verification.",
                "authority": "Tehsil / Electricity Board"
            }
        ]
    },
    "S08": {
        "scheme_name": "MGNREGA (Mahatma Gandhi NREGA Job Card)",
        "department": "Ministry of Rural Development",
        "category": "Employment",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Aadhaar Card",
                "mandatory": True,
                "purpose": "Identity and ABPS (Aadhaar Based Payment System) mandatory seeding.",
                "authority": "UIDAI"
            },
            {
                "id": "domicile_certificate",
                "name": "Proof of Local Residence in Gram Panchayat",
                "mandatory": True,
                "purpose": "Verification of local jurisdiction for 100 days guaranteed wage labor.",
                "authority": "Gram Panchayat / Block Administration"
            },
            {
                "id": "bank_passbook",
                "name": "Bank or Post Office Passbook",
                "mandatory": True,
                "purpose": "Weekly wage payment direct account routing.",
                "authority": "Commercial Bank / India Post"
            }
        ]
    },
    "S09": {
        "scheme_name": "Sukanya Samriddhi Yojana",
        "department": "Department of Financial Services / Ministry of Finance",
        "category": "Financial Security",
        "required_documents": [
            {
                "id": "birth_certificate",
                "name": "Girl Child Birth Certificate",
                "mandatory": True,
                "purpose": "Proof of age (must be opened before attaining 10 years of age).",
                "authority": "Municipal Corporation / Registrar of Births"
            },
            {
                "id": "aadhaar_card",
                "name": "Parent / Legal Guardian Aadhaar Card",
                "mandatory": True,
                "purpose": "Guardian identity and KYC verification.",
                "authority": "UIDAI"
            },
            {
                "id": "domicile_certificate",
                "name": "Proof of Address of Guardian",
                "mandatory": True,
                "purpose": "Account opening KYC documentation.",
                "authority": "Competent Authority"
            }
        ]
    },
    "S10": {
        "scheme_name": "PM Vishwakarma Scheme",
        "department": "Ministry of Micro, Small and Medium Enterprises (MSME)",
        "category": "Artisans & Crafts",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Aadhaar Card (Biometric Verified)",
                "mandatory": True,
                "purpose": "Mandatory biometric e-KYC and mobile linkage verification.",
                "authority": "UIDAI"
            },
            {
                "id": "bank_passbook",
                "name": "Active Bank Account Passbook",
                "mandatory": True,
                "purpose": "Disbursement of ₹15,000 toolkit incentive and collateral-free enterprise loan.",
                "authority": "Commercial / Grameen Bank"
            },
            {
                "id": "artisan_trade_proof",
                "name": "Artisan Self-Declaration / Gram Panchayat Recommendation",
                "mandatory": True,
                "purpose": "Proof of engagement in one of the 18 recognized traditional family trades.",
                "authority": "Gram Panchayat Head / ULB Nodal Officer"
            },
            {
                "id": "ration_bpl_card",
                "name": "Ration Card / Family Member ID",
                "mandatory": False,
                "purpose": "One-benefit-per-family statutory compliance check.",
                "authority": "Civil Supplies"
            }
        ]
    },
    "S11": {
        "scheme_name": "Stand-Up India Scheme",
        "department": "Department of Financial Services",
        "category": "Enterprise & Loans",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Aadhaar Identity Card & PAN Card",
                "mandatory": True,
                "purpose": "Enterprise founder KYC and credit bureau score authentication.",
                "authority": "UIDAI / Income Tax Dept"
            },
            {
                "id": "caste_certificate",
                "name": "Caste Certificate (SC/ST) or Women Entrepreneur Affidavit",
                "mandatory": True,
                "purpose": "Proof of affirmative eligibility for greenfield enterprise financing (₹10 Lakh - ₹1 Crore).",
                "authority": "Competent Revenue Authority / Notary"
            },
            {
                "id": "project_report",
                "name": "Detailed Project Report (DPR) / Greenfield Business Plan",
                "mandatory": True,
                "purpose": "Assessment of commercial viability and projected cash flows.",
                "authority": "Applicant / Certified Chartered Accountant"
            },
            {
                "id": "bank_passbook",
                "name": "Bank Statement (Last 6 Months)",
                "mandatory": True,
                "purpose": "Financial credibility assessment.",
                "authority": "Commercial Bank"
            }
        ]
    },
    "S12": {
        "scheme_name": "Atal Pension Yojana (APY)",
        "department": "Pension Fund Regulatory and Development Authority (PFRDA)",
        "category": "Pension & Retirement",
        "required_documents": [
            {
                "id": "aadhaar_card",
                "name": "Aadhaar Card",
                "mandatory": True,
                "purpose": "Biometric identity verification and KYC compliance (entry age 18-40 years).",
                "authority": "UIDAI"
            },
            {
                "id": "bank_passbook",
                "name": "Savings Bank Account Passbook",
                "mandatory": True,
                "purpose": "Monthly auto-debit contribution deduction and maturity pension routing.",
                "authority": "Bank / Post Office"
            },
            {
                "id": "nominee_id",
                "name": "Nominee Identity Proof & Relationship Details",
                "mandatory": True,
                "purpose": "Statutory spouse / nominee pension survivorship guarantee.",
                "authority": "Government Recognized ID"
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
    }
}


def generate_dynamic_checklist(scheme_name: str) -> Dict[str, Any]:
    """Generates an intelligent official document checklist for any custom or citizen-entered scheme."""
    norm = scheme_name.lower()
    docs = [
        {
            "id": "aadhaar_card",
            "name": "Aadhaar Identity Card",
            "mandatory": True,
            "purpose": "Mandatory identity authentication & Section 7 Aadhaar verification.",
            "authority": "UIDAI"
        }
    ]

    if any(k in norm for k in ["pension", "widow", "vidhwa", "old age", "vridha", "divyang", "disability", "destitute", "nirashrit", "destitute women"]):
        if any(k in norm for k in ["widow", "vidhwa", "destitute", "nirashrit", "destitute women"]):
            docs.append({
                "id": "death_certificate",
                "name": "Deceased Husband Death Certificate",
                "mandatory": True,
                "purpose": "Official statutory proof of widowhood.",
                "authority": "Registrar of Births & Deaths / Municipal Corporation"
            })
        if any(k in norm for k in ["disability", "divyang"]):
            docs.append({
                "id": "disability_certificate",
                "name": "UDID Card / Disability Medical Certificate (Min 40%)",
                "mandatory": True,
                "purpose": "Official medical proof of benchmark disability.",
                "authority": "Chief Medical Officer (CMO) / UDID Portal"
            })
        if any(k in norm for k in ["old age", "vridha", "senior"]):
            docs.append({
                "id": "age_proof",
                "name": "Age Proof Certificate (Voter ID / Birth Certificate)",
                "mandatory": True,
                "purpose": "Proof of attaining statutory minimum age requirement.",
                "authority": "Election Commission / Competent Medical Board"
            })
        docs.extend([
            {
                "id": "income_certificate",
                "name": "Certified Family Income Certificate",
                "mandatory": True,
                "purpose": "Proof that annual household income satisfies poverty / income cap criteria.",
                "authority": "Tehsildar / Sub-Divisional Magistrate"
            },
            {
                "id": "bank_passbook",
                "name": "Aadhaar-Linked Bank Account Passbook",
                "mandatory": True,
                "purpose": "Direct Benefit Transfer (DBT) monthly pension routing.",
                "authority": "Public Sector / Scheduled Bank"
            },
            {
                "id": "domicile_certificate",
                "name": "Domicile / Resident Certificate",
                "mandatory": False,
                "purpose": "Proof of continuous territorial residency in the state.",
                "authority": "Tehsil / e-District"
            }
        ])
    elif any(k in norm for k in ["scholar", "student", "education", "matric", "post-matric", "fellowship"]):
        docs.extend([
            {
                "id": "income_certificate",
                "name": "Family Income Certificate",
                "mandatory": True,
                "purpose": "Household income verification for scholarship fee waiver eligibility.",
                "authority": "Revenue Authority / Tehsildar"
            },
            {
                "id": "caste_certificate",
                "name": "Caste / Category Certificate (SC/ST/OBC/EWS)",
                "mandatory": True,
                "purpose": "Social category quota validation.",
                "authority": "District Magistrate / Tehsildar"
            },
            {
                "id": "previous_marksheet",
                "name": "Previous Qualifying Exam Marksheet",
                "mandatory": True,
                "purpose": "Academic merit and regular academic progression verification.",
                "authority": "Recognized Examination Board / University"
            },
            {
                "id": "fee_receipt_admission",
                "name": "Current Academic Year Fee Receipt & Bonafide Certificate",
                "mandatory": True,
                "purpose": "Active regular enrollment and exact non-refundable fee claim proof.",
                "authority": "Head of Recognized Institution / College Registrar"
            },
            {
                "id": "bank_passbook",
                "name": "Aadhaar-Seeded Bank Passbook",
                "mandatory": True,
                "purpose": "Direct scholarship disbursement via PFMS/DBT.",
                "authority": "Scheduled Bank"
            },
            {
                "id": "domicile_certificate",
                "name": "Domicile / Resident Certificate",
                "mandatory": False,
                "purpose": "Proof of continuous residence within the respective state.",
                "authority": "Tehsil / e-District Portal"
            }
        ])
    elif any(k in norm for k in ["kisan", "farmer", "krishi", "agriculture", "crop"]):
        docs.extend([
            {
                "id": "land_ownership_records",
                "name": "Land Record (Khatauni / Khasra / Jamabandi)",
                "mandatory": True,
                "purpose": "Proof of cultivable agricultural land title in applicant's name.",
                "authority": "Revenue Department / Patwari"
            },
            {
                "id": "bank_passbook",
                "name": "Aadhaar-Linked Bank Account Passbook",
                "mandatory": True,
                "purpose": "Direct benefit credit transfer via DBT.",
                "authority": "Commercial / Regional Rural Bank"
            }
        ])
    elif any(k in norm for k in ["caste", "jati"]):
        docs.extend([
            {
                "id": "caste_certificate",
                "name": "Ancestral Caste / Community Proof or Previous Family Certificate",
                "mandatory": True,
                "purpose": "Verification of community lineage and recognized social category.",
                "authority": "Competent Revenue Authority"
            },
            {
                "id": "domicile_certificate",
                "name": "Domicile / Native Resident Certificate",
                "mandatory": True,
                "purpose": "Proof of permanent residency in the state.",
                "authority": "Tehsil"
            }
        ])
    elif any(k in norm for k in ["domicile", "niwas", "resident"]):
        docs.extend([
            {
                "id": "electricity_utility_bill",
                "name": "Electricity Bill / Land Title / House Tax Receipt",
                "mandatory": True,
                "purpose": "Proof of continuous residence for minimum statutory years.",
                "authority": "DISCOM / Municipal Corporation"
            },
            {
                "id": "education_proof",
                "name": "Continuous Education Marksheets / School Certificates",
                "mandatory": False,
                "purpose": "Proof of minimum years of schooling in state.",
                "authority": "Educational Board"
            }
        ])
    elif any(k in norm for k in ["ration", "bpl", "food", "khadya"]):
        docs.extend([
            {
                "id": "income_certificate",
                "name": "Income Certificate / Income Affidavit",
                "mandatory": True,
                "purpose": "Verification of deprivation criteria and economic eligibility.",
                "authority": "Tehsildar"
            },
            {
                "id": "domicile_certificate",
                "name": "Proof of Residence / Electricity Bill",
                "mandatory": True,
                "purpose": "Jurisdiction mapping to Fair Price Shop (FPS).",
                "authority": "Local Civic Body"
            },
            {
                "id": "bank_passbook",
                "name": "Family Head Bank Passbook",
                "mandatory": False,
                "purpose": "DBT subsidy transfer if applicable.",
                "authority": "Bank / Post Office"
            }
        ])
    else:
        # Standard administrative citizen packet
        docs.extend([
            {
                "id": "income_certificate",
                "name": "Income Proof / Income Certificate",
                "mandatory": True,
                "purpose": "Proof of household financial eligibility criteria.",
                "authority": "Revenue Department / Employer / Notary"
            },
            {
                "id": "domicile_certificate",
                "name": "Domicile / Residence Certificate",
                "mandatory": False,
                "purpose": "Proof of territorial jurisdiction and permanent residence.",
                "authority": "Tehsil / Local Municipal Body"
            },
            {
                "id": "bank_passbook",
                "name": "Bank Account Passbook / Statement",
                "mandatory": True,
                "purpose": "Direct Benefit Transfer (DBT) verification and NPCI linkage.",
                "authority": "Scheduled Bank / Post Office"
            }
        ])

    return {
        "scheme_name": scheme_name,
        "department": "Public Service Department",
        "category": "Citizen Services",
        "required_documents": docs
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

        # Enrich catalog schemes with document registries
        for s in self.schemes:
            sid = s.get("scheme_id") or s.get("id")
            if sid in SCHEME_DOC_REGISTRY:
                s["doc_registry"] = SCHEME_DOC_REGISTRY[sid]
            else:
                s["doc_registry"] = generate_dynamic_checklist(s.get("name", "Government Scheme"))

    def get_all_schemes(self):
        return self.schemes

    def get_scheme_by_id(self, scheme_id):
        for s in self.schemes:
            if s.get("scheme_id") == scheme_id or s.get("id") == scheme_id:
                return s
        return None

    def get_scheme_docs(self, scheme_id_or_name: str) -> Dict[str, Any]:
        """Lookup required document checklist by scheme id or fuzzy name, or generate dynamic checklist."""
        if not scheme_id_or_name:
            return SCHEME_DOC_REGISTRY["S05"]

        clean_id = scheme_id_or_name.strip()
        # 1. Exact match in SCHEME_DOC_REGISTRY
        if clean_id in SCHEME_DOC_REGISTRY:
            return SCHEME_DOC_REGISTRY[clean_id]

        # 2. Match in self.schemes
        for s in self.schemes:
            sid = s.get("scheme_id") or s.get("id")
            sname = s.get("name", "").lower()
            if sid == clean_id or clean_id.lower() == sname:
                return s.get("doc_registry") or SCHEME_DOC_REGISTRY.get(sid, generate_dynamic_checklist(s.get("name", clean_id)))
            if clean_id.lower() in sname:
                return s.get("doc_registry") or SCHEME_DOC_REGISTRY.get(sid, generate_dynamic_checklist(s.get("name", clean_id)))

        # 3. Known keywords in custom scheme names
        norm = clean_id.lower()
        if "scholar" in norm:
            res = dict(SCHEME_DOC_REGISTRY["S05"])
            res["scheme_name"] = clean_id
            return res
        if "income" in norm:
            res = dict(SCHEME_DOC_REGISTRY["S13"])
            res["scheme_name"] = clean_id
            return res
        if "kisan" in norm:
            res = dict(SCHEME_DOC_REGISTRY["S01"])
            res["scheme_name"] = clean_id
            return res
        if "ayushman" in norm or "golden card" in norm:
            res = dict(SCHEME_DOC_REGISTRY["S02"])
            res["scheme_name"] = clean_id
            return res
        if "vishwakarma" in norm:
            res = dict(SCHEME_DOC_REGISTRY["S10"])
            res["scheme_name"] = clean_id
            return res

        # 4. Generate dynamic checklist for any custom citizen service/scheme
        return generate_dynamic_checklist(clean_id)

    def get_timeline_scenarios(self):
        return self.timeline_scenarios

registry = PromiseRegistry()
