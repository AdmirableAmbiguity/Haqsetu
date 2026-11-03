"""
Query Router for HaqSetu / Vachan Setu.
Routes classified queries to:
1. HaqGuide (General Citizen Assistant)
2. Scheme Finder (Personalized Eligibility & Discovery)
3. Scheme Expert (Deep Dive on a Specific Scheme)
"""

import re
import logging
from typing import Dict, Any, List, Optional
from ai_engine.intent_classifier import intent_classifier, KNOWN_SCHEMES
from ai_engine.conversation_memory import conversation_memory
from backend.app.services.registry import registry
from ai_engine import sarvam_client

logger = logging.getLogger(__name__)

# Official Verified State e-District & Citizen Service Portals Registry
STATE_PORTALS_REGISTRY = {
    "Uttarakhand": {
        "portal_name": "Apuni Sarkar / e-District Uttarakhand",
        "portal_url": "https://edistrict.uk.gov.in",
        "alt_portal_url": "https://eservices.uk.gov.in",
        "act_name": "Uttarakhand Right to Service Act, 2011",
        "rtsa_days": 15,
        "department": "Revenue Department (राजस्व विभाग), Government of Uttarakhand",
        "authorities": "Patwari / Lekhpal field verification, Tehsildar / Sub-Divisional Magistrate approval"
    },
    "Uttar Pradesh": {
        "portal_name": "e-District Uttar Pradesh",
        "portal_url": "https://edistrict.up.gov.in",
        "act_name": "UP Janhit Guarantee Act, 2011",
        "rtsa_days": 15,
        "department": "Revenue Department (राजस्व विभाग), Government of Uttar Pradesh",
        "authorities": "Area Lekhpal inquiry, Tehsildar / SDM digital approval"
    },
    "Bihar": {
        "portal_name": "RTPS Bihar / ServicePlus",
        "portal_url": "https://serviceonline.bihar.gov.in",
        "act_name": "Bihar Right to Public Services Act, 2011",
        "rtsa_days": 14,
        "department": "General Administration Department, Government of Bihar",
        "authorities": "Circle Officer (CO) / Revenue Officer (RO)"
    },
    "Madhya Pradesh": {
        "portal_name": "MP e-District (Lok Seva Kendra)",
        "portal_url": "https://mpedistrict.gov.in",
        "act_name": "MP Lok Seva Guarantee Act, 2010",
        "rtsa_days": 15,
        "department": "Revenue & Public Service Management Department, MP",
        "authorities": "Patwari verification, Naib Tehsildar / Tehsildar"
    },
    "Rajasthan": {
        "portal_name": "e-Mitra / Rajasthan Single Sign-On (SSO)",
        "portal_url": "https://emitra.rajasthan.gov.in",
        "alt_portal_url": "https://sso.rajasthan.gov.in",
        "act_name": "Rajasthan Guaranteed Delivery of Public Services Act, 2011",
        "rtsa_days": 15,
        "department": "Department of Revenue & Administrative Reforms, Rajasthan",
        "authorities": "Patwari verification, Tehsildar"
    },
    "Maharashtra": {
        "portal_name": "Aaple Sarkar Portal",
        "portal_url": "https://aaplesarkar.mahaonline.gov.in",
        "act_name": "Maharashtra Right to Public Services Act, 2015",
        "rtsa_days": 15,
        "department": "Revenue and Forest Department, Government of Maharashtra",
        "authorities": "Talathi verification, Tehsildar"
    },
    "Delhi": {
        "portal_name": "e-District Delhi",
        "portal_url": "https://edistrict.delhigovt.nic.in",
        "act_name": "Delhi Right to Citizen Title Act, 2011",
        "rtsa_days": 14,
        "department": "Revenue Department, Government of NCT of Delhi",
        "authorities": "Sub-Divisional Magistrate (SDM) / Tehsildar"
    },
    "Haryana": {
        "portal_name": "Antyodaya SARAL Portal Haryana",
        "portal_url": "https://saralharyana.gov.in",
        "act_name": "Haryana Right to Service Act, 2014",
        "rtsa_days": 15,
        "department": "Revenue & Citizen Resources Information Department, Haryana",
        "authorities": "Patwari verification, Tehsildar"
    },
    "Punjab": {
        "portal_name": "mSewa Punjab / e-District Punjab",
        "portal_url": "https://connect.punjab.gov.in",
        "act_name": "Punjab Right to Services Act, 2011",
        "rtsa_days": 15,
        "department": "Department of Governance Reforms & Revenue, Punjab",
        "authorities": "Kanungo / Tehsildar"
    },
    "Gujarat": {
        "portal_name": "Digital Gujarat Portal",
        "portal_url": "https://digitalgujarat.gov.in",
        "act_name": "Gujarat Right to Public Services Act, 2013",
        "rtsa_days": 15,
        "department": "Revenue Department, Government of Gujarat",
        "authorities": "Talati-cum-Mantri / Mamlatdar"
    },
    "Karnataka": {
        "portal_name": "Seva Sindhu Karnataka",
        "portal_url": "https://sevasindhu.karnataka.gov.in",
        "act_name": "Sakala Services Act, 2011",
        "rtsa_days": 15,
        "department": "Revenue Department, Government of Karnataka",
        "authorities": "Village Accountant / Revenue Inspector / Tahsildar"
    },
    "Tamil Nadu": {
        "portal_name": "TNeGA e-Sevai Portal",
        "portal_url": "https://www.tnesevai.tn.gov.in",
        "act_name": "Tamil Nadu e-Governance Services",
        "rtsa_days": 15,
        "department": "Revenue and Disaster Management Department, Tamil Nadu",
        "authorities": "Village Administrative Officer (VAO) / Tahsildar"
    },
    "West Bengal": {
        "portal_name": "e-District West Bengal",
        "portal_url": "https://edistrict.wb.gov.in",
        "act_name": "West Bengal Right to Public Services Act, 2013",
        "rtsa_days": 15,
        "department": "Personnel and Administrative Reforms & Revenue, West Bengal",
        "authorities": "Revenue Inspector / Block Development Officer (BDO)"
    },
    "Kerala": {
        "portal_name": "e-District Kerala",
        "portal_url": "https://edistrict.kerala.gov.in",
        "act_name": "Kerala State Right to Service Act, 2012",
        "rtsa_days": 10,
        "department": "Revenue Department, Government of Kerala",
        "authorities": "Village Officer / Tahsildar"
    },
    "Odisha": {
        "portal_name": "Odisha Right to Public Services (ORTPSA) / ServicePlus",
        "portal_url": "https://serviceonline.gov.in/odisha",
        "act_name": "Odisha Right to Public Services Act, 2012",
        "rtsa_days": 15,
        "department": "Revenue and Disaster Management Department, Odisha",
        "authorities": "Revenue Inspector (RI) / Tahsildar"
    },
    "Andhra Pradesh": {
        "portal_name": "MeeSeva Andhra Pradesh",
        "portal_url": "https://ap.meeseva.gov.in",
        "act_name": "AP Right to Public Services",
        "rtsa_days": 15,
        "department": "Revenue Department, Government of Andhra Pradesh",
        "authorities": "Village Revenue Officer (VRO) / Tahsildar"
    },
    "Telangana": {
        "portal_name": "MeeSeva Telangana",
        "portal_url": "https://ts.meeseva.telangana.gov.in",
        "act_name": "Telangana Right to Public Services",
        "rtsa_days": 15,
        "department": "Revenue Department, Government of Telangana",
        "authorities": "Village Revenue Officer / Tahsildar"
    },
    "Jharkhand": {
        "portal_name": "JharSewa Jharkhand (ServicePlus)",
        "portal_url": "https://jharsewa.jharkhand.gov.in",
        "act_name": "Jharkhand Right to Service Act, 2011",
        "rtsa_days": 15,
        "department": "Department of Personnel & Revenue, Jharkhand",
        "authorities": "Circle Officer (CO)"
    },
    "Chhattisgarh": {
        "portal_name": "e-District Chhattisgarh",
        "portal_url": "https://edistrict.cgstate.gov.in",
        "act_name": "Chhattisgarh Lok Seva Guarantee Act, 2011",
        "rtsa_days": 15,
        "department": "Revenue and Disaster Management Department, Chhattisgarh",
        "authorities": "Patwari / Tehsildar"
    },
    "Himachal Pradesh": {
        "portal_name": "e-District Himachal Pradesh",
        "portal_url": "https://edistrict.hp.gov.in",
        "act_name": "HP Public Services Guarantee Act, 2011",
        "rtsa_days": 15,
        "department": "Revenue Department, Himachal Pradesh",
        "authorities": "Patwari / Tehsildar"
    },
    "Assam": {
        "portal_name": "Sewa Setu Assam (Right to Public Services)",
        "portal_url": "https://sewasetu.assam.gov.in",
        "act_name": "Assam Right to Public Services Act, 2012",
        "rtsa_days": 15,
        "department": "Administrative Reforms & Revenue, Assam",
        "authorities": "Lot Mandal / Circle Officer"
    },
    "Jammu & Kashmir": {
        "portal_name": "e-UNNAT Jammu & Kashmir (ServicePlus)",
        "portal_url": "https://serviceonline.gov.in/jammu",
        "act_name": "J&K Public Services Guarantee Act, 2011",
        "rtsa_days": 15,
        "department": "Revenue Department, J&K Administration",
        "authorities": "Patwari / Tehsildar"
    },
    "Goa": {
        "portal_name": "Goa Online Services Portal",
        "portal_url": "https://goaonline.gov.in",
        "act_name": "Goa (Right to Time-Bound Delivery of Public Services) Act, 2013",
        "rtsa_days": 15,
        "department": "Revenue Department, Government of Goa",
        "authorities": "Talathi / Mamlatdar"
    }
}


def get_state_portal_info(state_name: Optional[str]) -> Dict[str, Any]:
    """Resolves verified state portal, department, SLA, and statutory act."""
    if state_name and state_name in STATE_PORTALS_REGISTRY:
        return STATE_PORTALS_REGISTRY[state_name]
    
    # National fallback
    return {
        "portal_name": "National Services Portal / State e-District Gateway",
        "portal_url": "https://services.india.gov.in",
        "act_name": "State Right to Public Services Act",
        "rtsa_days": 15,
        "department": "Revenue Department (राजस्व विभाग) / District Administration",
        "authorities": "Local Field Inquiry Officer / Tehsildar"
    }


# Grounded Database of Common Citizen Services & Certificates
GOVERNMENT_SERVICES_KB = {
    "domicile": {
        "title": "Domicile / Residence Certificate (निवास प्रमाण पत्र)",
        "department": "Revenue Department (राजस्व विभाग) / District Administration",
        "portal_name": "State e-District Portal (e.g. edistrict.up.gov.in / State RTPS)",
        "portal_url": "https://edistrict.up.gov.in",
        "sla_days": 15,
        "is_statutory": True,
        "fee": "₹15 (Online Citizen Portal) / ₹30 (CSC / Jan Seva Kendra)",
        "summary": "Official certificate confirming permanent residence in the state, mandatory for state quotas, government jobs, and state scholarships.",
        "steps": [
            "Register or login to your State e-District Portal (or visit nearest Common Service Center / CSC).",
            "Fill Application Form for 'Domicile Certificate (निवास प्रमाण पत्र)' with applicant & father/husband details.",
            "Upload self-declaration form, photo, address proof, and age/schooling proof.",
            "Pay the nominal statutory fee (₹15 online) and save the Application Reference Number.",
            "Application moves to Area Lekhpal / Patwari for physical/record verification and is approved by Tehsildar/SDM.",
            "Download digitally signed certificate from the portal once verified within 15 days."
        ],
        "documents": [
            {"name": "Aadhaar Card / Voter ID", "mandatory": True, "purpose": "Identity and local address verification"},
            {"name": "Self-Declaration Form (स्व-प्रमाणित घोषणा पत्र)", "mandatory": True, "purpose": "Legal declaration of residence duration"},
            {"name": "Passport Size Photograph", "mandatory": True, "purpose": "Affixed on the digital certificate"},
            {"name": "Electricity Bill / Ration Card / Gas Bill", "mandatory": True, "purpose": "Proof of continuous residence at address"},
            {"name": "School Leaving Certificate / Educational Marksheet", "mandatory": False, "purpose": "Proof of education within the state"}
        ],
        "rejection_pitfalls": [
            "Incomplete address proof or discrepancy between Aadhaar and local address.",
            "Missing signed self-declaration form.",
            "Failure to appear for Lekhpal inquiry if summoned."
        ]
    },
    "income": {
        "title": "Income Certificate (आय प्रमाण पत्र)",
        "department": "Revenue Department (राजस्व विभाग)",
        "portal_name": "State e-District Portal (e.g. edistrict.up.gov.in)",
        "portal_url": "https://edistrict.up.gov.in",
        "sla_days": 15,
        "is_statutory": True,
        "fee": "₹15 (Online) / ₹30 (CSC)",
        "summary": "Statutory document certifying total annual household income from all sources (agriculture, wages, business, salary). Valid for 3 years in most states.",
        "steps": [
            "Log in to State e-District portal or visit nearest Tehsil / CSC center.",
            "Select 'Income Certificate Application (आय प्रमाण पत्र)' under Revenue Services.",
            "Enter details of family members, monthly earnings, landholding, and employer details.",
            "Upload income proof (salary slip / agricultural revenue record / self-income affidavit), Aadhaar, and photo.",
            "Pay the fee and track application with the generated Application Number.",
            "Lekhpal verifies local inquiries; Tehsildar issues digitally signed certificate within 15 working days."
        ],
        "documents": [
            {"name": "Aadhaar Card", "mandatory": True, "purpose": "Identity and family head verification"},
            {"name": "Income Affidavit / Salary Slip", "mandatory": True, "purpose": "Proof of declared family income"},
            {"name": "Ration Card / Family Register Copy", "mandatory": True, "purpose": "Verification of total family members"},
            {"name": "Passport Photo", "mandatory": True, "purpose": "Digital record"}
        ],
        "rejection_pitfalls": [
            "Under-reporting income compared to landholding or vehicle registration records.",
            "Unclear or unnotarized income affidavit for informal sector workers."
        ]
    },
    "caste": {
        "title": "Caste / Category Certificate (जाति प्रमाण पत्र - SC/ST/OBC/EWS)",
        "department": "Revenue Department / Social Welfare Department",
        "portal_name": "State e-District Portal",
        "portal_url": "https://edistrict.up.gov.in",
        "sla_days": 15,
        "is_statutory": True,
        "fee": "₹15 (Online) / ₹30 (CSC)",
        "summary": "Government certificate authenticating social category (SC, ST, OBC, or EWS) required for reservation, educational quotas, and welfare schemes.",
        "steps": [
            "Log into e-District portal or visit CSC / Tehsil e-Seva Kendra.",
            "Fill Caste Certificate application with Sub-Caste and family lineage details.",
            "Upload father's/paternal relative's caste certificate or ancient revenue land records (1359 Fasli / pre-cutoff record where required).",
            "Upload applicant Aadhaar, self-declaration, and passport photo.",
            "Submit and note application reference for tracking.",
            "Patwari/Revenue Inspector verifies lineage; SDM/Tehsildar issues certificate within 15 days."
        ],
        "documents": [
            {"name": "Father's or Blood Relative's Caste Certificate", "mandatory": True, "purpose": "Proof of hereditary caste lineage"},
            {"name": "Aadhaar Card", "mandatory": True, "purpose": "Identity and address proof"},
            {"name": "Self-Declaration Form", "mandatory": True, "purpose": "Statutory undertaking"},
            {"name": "Passport Photo", "mandatory": True, "purpose": "Affixed on certificate"}
        ],
        "rejection_pitfalls": [
            "Maternal caste certificate submitted instead of paternal lineage (Indian law requires paternal lineage for caste).",
            "Non-creamy layer (NCL) income limit exceeded for OBC candidates."
        ]
    },
    "birth": {
        "title": "Birth Certificate (जन्म प्रमाण पत्र)",
        "department": "Department of Health & Family Welfare / Municipal Corporation / Gram Panchayat",
        "portal_name": "Civil Registration System (CRS)",
        "portal_url": "https://crsorgi.gov.in",
        "sla_days": 7,
        "is_statutory": True,
        "fee": "Free within 21 days; Nominal late fee thereafter",
        "summary": "Primary legal document recording the birth of a child, fundamental for school admission, Aadhaar enrolment, passport, and citizenship verification.",
        "steps": [
            "If born in hospital/health centre, institutional record is transmitted automatically to registrar.",
            "For home birth, report within 21 days to local Registrar (Gram Panchayat Secretary or Municipal Ward Officer).",
            "Fill Form 1 on crsorgi.gov.in or at the local registrar office.",
            "Provide parents' Aadhaar cards and hospital discharge slip / birth notification slip.",
            "Certificate is issued digitally signed within 7 days."
        ],
        "documents": [
            {"name": "Hospital Discharge / Birth Slip", "mandatory": True, "purpose": "Proof of birth date, time, and location"},
            {"name": "Parents' Aadhaar Cards", "mandatory": True, "purpose": "Parental identity verification"},
            {"name": "Marriage Certificate / Address Proof", "mandatory": False, "purpose": "Parentage verification"}
        ],
        "rejection_pitfalls": [
            "Delayed registration beyond 1 year without SDM late registration order.",
            "Spelling discrepancy between parents' Aadhaar and hospital birth slip."
        ]
    },
    "aadhaar": {
        "title": "Aadhaar Demographic & Mobile Update (आधार कार्ड संशोधन)",
        "department": "Unique Identification Authority of India (UIDAI)",
        "portal_name": "myAadhaar Portal / Aadhaar Seva Kendra",
        "portal_url": "https://myaadhaarbeta.uidai.gov.in",
        "sla_days": 3,
        "is_statutory": True,
        "fee": "₹50 (Demographic / Mobile Update) / Free (Mandatory Biometric 5-15 yrs)",
        "summary": "Mandatory process to update mobile number, address, name, or biometrics on Aadhaar. Note: Mobile update strictly requires in-person biometric verification.",
        "steps": [
            "Locate nearest Aadhaar Seva Kendra (ASK) or Post Office Aadhaar counter via appointments.uidai.gov.in.",
            "Book an online appointment (or walk in) for 'Mobile Number Update / Biometric Update'.",
            "Visit the center with original Aadhaar card (no documents needed specifically for mobile update).",
            "Operator collects live biometrics (fingerprint/iris) and updates your 10-digit mobile number.",
            "Pay the standard ₹50 UIDAI fee and collect the 14-digit URN (Update Request Number) slip.",
            "Update reflects in UIDAI database within 24 to 72 hours; verify status on myAadhaar."
        ],
        "documents": [
            {"name": "Original Aadhaar Card", "mandatory": True, "purpose": "Biometric match (no other doc required for mobile update)"},
            {"name": "Address Proof (if updating address)", "mandatory": False, "purpose": "Electricity bill / bank passbook / rent agreement"}
        ],
        "rejection_pitfalls": [
            "Attempting to update mobile number online without existing linked mobile (UIDAI requires in-person biometric authentication).",
            "Fingerprint biometric mismatch (use iris scan if fingerprints are faint)."
        ]
    },
    "ration_card": {
        "title": "Ration Card (राशन कार्ड - NFSA / Antyodaya)",
        "department": "Department of Food & Civil Supplies (खाद्य एवं रसद विभाग)",
        "portal_name": "State Food & Civil Supplies Portal (e.g. fcs.up.gov.in)",
        "portal_url": "https://fcs.up.gov.in",
        "sla_days": 30,
        "is_statutory": True,
        "fee": "₹20 - ₹50 (CSC Application Fee)",
        "summary": "Household entitlement document for subsidized or free foodgrains under National Food Security Act (NFSA) and primary proof of family composition.",
        "steps": [
            "Visit CSC or log into state food & civil supplies portal.",
            "Fill New NFSA Ration Card application (Rural or Urban).",
            "Add details of woman head of household (Section 13 NFSA mandates female head) and all family members.",
            "Upload Aadhaar of all members, income certificate, electricity bill, and woman head's bank passbook.",
            "Area Supply Inspector (Purti Nirikshak) conducts physical verification.",
            "Ration card number generated within 30 days and linked to Fair Price Shop (Kotedaar)."
        ],
        "documents": [
            {"name": "Aadhaar Card of all family members", "mandatory": True, "purpose": "Aadhaar seeding to prevent ghost cards"},
            {"name": "Bank Passbook of Woman Head of Household", "mandatory": True, "purpose": "Mandatory female head under NFSA 2013"},
            {"name": "Income Certificate", "mandatory": True, "purpose": "Priority Household (PHH) or BPL qualification"},
            {"name": "Electricity Bill / Residence Proof", "mandatory": True, "purpose": "Local jurisdiction assignment"}
        ],
        "rejection_pitfalls": [
            "Family member already active in another ration card.",
            "Household owns four-wheeler or exceeds urban area income ceiling."
        ]
    }
}


class QueryRouter:
    """Intelligently routes citizen requests to the proper section handler."""

    def route(
        self,
        query: str,
        session_id: Optional[str] = None,
        section_override: Optional[str] = None,
        profile_override: Optional[Dict[str, Any]] = None,
        scheme_override: Optional[str] = None
    ) -> Dict[str, Any]:
        session = conversation_memory.get_session(session_id)
        if profile_override:
            session.update_profile(profile_override)

        # 1. Classify intent
        classification = intent_classifier.classify(query)
        intent = classification.get("intent", "GENERAL_GOVERNMENT_QUERY")
        entities = classification.get("entities", {})

        # Priority routing logic:
        # If citizen explicitly clicked Scheme Finder tab or query is SCHEME_DISCOVERY
        if section_override == "scheme_finder" or intent == "SCHEME_DISCOVERY":
            session.set_scheme(None)
            res = self._handle_scheme_finder(query, session, classification)
            # If no schemes were found and query asks procedural or legal questions, fall through to HaqGuide
            if len(res.get("matches", [])) == 0 and any(w in query.lower() for w in ["how to", "process", "procedure", "grievance", "complaint", "rights"]):
                return self._handle_haqguide(query, session, classification)
            return res

        # If query is clearly a general service, certificate, status, or greeting,
        # route to HaqGuide (even if a scheme was viewed earlier), unless citizen is explicitly pinned to scheme_expert
        if intent in ["CERTIFICATE_APPLICATION", "GOVERNMENT_SERVICE_QUERY", "APPLICATION_STATUS", "CONVERSATIONAL", "GENERAL_GOVERNMENT_QUERY"] and section_override != "scheme_expert":
            session.set_scheme(None)
            return self._handle_haqguide(query, session, classification)

        # If citizen explicitly selected Scheme Expert tab, specified a scheme, or query is SCHEME_SPECIFIC_QUERY
        if section_override == "scheme_expert" or intent == "SCHEME_SPECIFIC_QUERY" or scheme_override or (session.active_scheme and section_override != "haqguide"):
            return self._handle_scheme_expert(query, session, classification, scheme_override)

        # Otherwise, route to HaqGuide (General Assistant)
        return self._handle_haqguide(query, session, classification)

    # -------------------------------------------------------------
    # SECTION 1: HAQGUIDE (General Government Assistant)
    # -------------------------------------------------------------
    def _handle_haqguide(self, query: str, session, classification: Dict[str, Any]) -> Dict[str, Any]:
        intent = classification.get("intent", "GENERAL_GOVERNMENT_QUERY")
        entities = classification.get("entities", {})
        session.active_section = "haqguide"

        # Check for conversational / greeting
        if intent == "CONVERSATIONAL":
            reply = (
                "Namaste! I am **HaqGuide**, your digital citizen rights and government service assistant.\n\n"
                "I can guide you step-by-step through:\n"
                "• **Certificates**: Domicile (निवास), Income (आय), Caste (जाति), Birth/Death\n"
                "• **Citizen Services**: Aadhaar update, Ration Card, Voter ID, Driving License\n"
                "• **Timelines & Grievances**: Right to Public Services Act (RTSA) deadlines and pending status\n"
                "• **Schemes & Scholarships**: Eligibility matching in the **Scheme Finder** section\n\n"
                "How can I help you today? Please tell me which service or certificate you need assistance with."
            )
            session.add_message("user", query, intent)
            session.add_message("assistant", reply, intent)
            return {
                "session_id": session.session_id,
                "section": "haqguide",
                "intent": intent,
                "response": reply,
                "structured_guide": None,
                "matches": [],
                "follow_ups": [
                    "How to apply for a Domicile Certificate?",
                    "How to obtain an Income Certificate?",
                    "How to update Aadhaar mobile number?"
                ]
            }

        # Check if clarification is needed (e.g. "I want to apply for a certificate")
        if classification.get("requires_clarification"):
            clarify_msg = (
                "To assist you properly, please specify:\n"
                "1. **Which certificate** do you want to apply for? (e.g., Domicile/Residence, Income, Caste, Birth)\n"
                "2. **Which State / UT** do you reside in? (e.g., Uttar Pradesh, Bihar, Delhi, etc.)\n\n"
                "Once you share this, I will give you the complete step-by-step application procedure, required documents checklist, and official portal link."
            )
            session.add_message("user", query, intent)
            session.add_message("assistant", clarify_msg, intent)
            return {
                "session_id": session.session_id,
                "section": "haqguide",
                "intent": intent,
                "response": clarify_msg,
                "structured_guide": None,
                "matches": [],
                "follow_ups": [
                    "Domicile Certificate in Uttar Pradesh",
                    "Income Certificate in Uttar Pradesh",
                    "Caste Certificate in Bihar"
                ]
            }

        # Check for Comparison questions (e.g. difference between income certificate and domicile certificate)
        if entities.get("sub_type") == "comparison" or "difference between" in query.lower() or "antar" in query.lower():
            reply = (
                "### Difference Between Income Certificate and Domicile Certificate\n\n"
                "| Feature | Income Certificate (आय प्रमाण पत्र) | Domicile Certificate (निवास प्रमाण पत्र) |\n"
                "| :--- | :--- | :--- |\n"
                "| **Purpose** | Certifies total annual household income from all sources | Confirms legal and permanent residence in a specific State/UT |\n"
                "| **Issued By** | Tehsildar / Competent Revenue Authority | Sub-Divisional Magistrate (SDM) / Tehsildar |\n"
                "| **Primary Use** | Scholarships, fee waivers, EWS quota, BPL subsidies | State quota admissions, government jobs, state scholarships |\n"
                "| **Validity** | Generally **3 years** (or 1 financial year depending on state) | Generally **lifetime** (unless permanent address changes) |\n"
                "| **Key Documents** | Salary slip, income affidavit, ration card, land record | Aadhaar card, electricity bill, ration card, self-declaration |\n"
                "| **Official SLA** | 15 working days under Right to Public Services Act | 15 to 20 working days under Right to Public Services Act |\n\n"
                "> **Key Note**: Both certificates are processed via your State e-District portal (e.g., `edistrict.up.gov.in`). If applying for scholarships, you often need **both** certificates."
            )
            session.add_message("user", query, intent)
            session.add_message("assistant", reply, intent)
            return {
                "session_id": session.session_id,
                "section": "haqguide",
                "intent": intent,
                "response": reply,
                "structured_guide": None,
                "matches": [],
                "follow_ups": [
                    "How to apply for an Income Certificate?",
                    "How to apply for a Domicile Certificate?",
                    "What documents are needed for Scholarship?"
                ]
            }

        # Check for Application Status / Pending / Grievance query
        if intent == "APPLICATION_STATUS":
            reply = (
                "### Statutory Action for Delayed or Pending Application\n\n"
                "Under the **Right to Public Services Act (RTSA)**, state authorities are legally mandated to deliver public services (like certificates and scholarships) within prescribed statutory deadlines (typically **15 to 30 days**).\n\n"
                "If your application has exceeded the statutory deadline, here are your official next steps:\n\n"
                "1. **Check Status Online First**:\n"
                "   • Visit your application portal (e.g., `scholarship.up.gov.in` or `edistrict.up.gov.in`).\n"
                "   • Click **Application Status (आवेदन की स्थिति)** and enter your Application Number / Ref Number to verify where the file is currently halted.\n\n"
                "2. **Lodge an Official RTSA / CM Helpline Grievance**:\n"
                "   • In Uttar Pradesh: Call **1076 (CM Helpline)** or register an issue on **Jansunwai Portal (jansunwai.up.gov.in)**.\n"
                "   • For Central / Multi-state schemes: File a grievance on **CPGRAMS (pgportal.gov.in)**.\n\n"
                "3. **First Appeal to Appellate Authority**:\n"
                "   • The Act provides for a First Appeal to the Sub-Divisional Magistrate (SDM) or District Welfare Officer against unnotified administrative delay.\n\n"
                "4. **Statutory Notice & RTI Option**:\n"
                "   • You can use HaqSetu's **Silent-File RTI Generator** tab to automatically draft a formal Section 6(1) RTI inquiry asking for day-to-day progress on your file."
            )
            session.add_message("user", query, intent)
            session.add_message("assistant", reply, intent)
            return {
                "session_id": session.session_id,
                "section": "haqguide",
                "intent": intent,
                "response": reply,
                "structured_guide": {
                    "title": "Application Delay Resolution & RTSA Rights",
                    "department": "Administrative Reforms / Public Grievance Directorate",
                    "portal_name": "Jansunwai / CPGRAMS / State RTI Portal",
                    "portal_url": "https://pgportal.gov.in",
                    "sla_days": "Statutory limit breached",
                    "steps": [
                        "Track status on official portal with Application Ref ID",
                        "Call State CM Helpline (e.g. UP 1076)",
                        "File first appeal under Right to Public Services Act",
                        "Submit formal RTI inquiry via Silent-File module"
                    ]
                },
                "matches": [],
                "follow_ups": [
                    "How to file an RTI for delayed certificate?",
                    "Open Silent-File RTI generator",
                    "Check Service Health of UP Scholarship Portal"
                ]
            }

        # Check for matched government service in KB
        service_key = None
        for k in GOVERNMENT_SERVICES_KB.keys():
            # Use word boundary check so that words like "registration" don't falsely match "ration"
            if re.search(r'\b' + re.escape(k) + r'\b', query.lower()) or entities.get("certificate") == k or entities.get("service") == k:
                # Grievances against dealers, faulty bills, or refusals should go to OmniGovernanceEngine
                if any(w in query.lower() for w in ["complaint", "shikayat", "refuse", "not giving", "nahi de raha", "dispute", "cut", "problem", "faulty"]):
                    continue
                service_key = k
                break

        if service_key and service_key in GOVERNMENT_SERVICES_KB:
            kb = GOVERNMENT_SERVICES_KB[service_key]
            detected_state = entities.get("state")
            if not detected_state:
                detected_state = intent_classifier._extract_state(query)
            
            portal_info = get_state_portal_info(detected_state)
            state_label = detected_state if detected_state else "your State"
            portal_name = portal_info["portal_name"]
            portal_url = portal_info["portal_url"]
            dept_name = portal_info["department"] if detected_state else kb["department"]
            sla_days = portal_info.get("rtsa_days", kb["sla_days"])
            act_name = portal_info.get("act_name", "Right to Public Services Act")
            authorities = portal_info.get("authorities", "Lekhpal / Patwari inquiry and Tehsildar approval")

            # Dynamic state-tailored steps
            tailored_steps = [
                f"Register or login to the official {portal_name} ({portal_url}) or visit your nearest Common Service Center (CSC) / e-Seva Kendra in {state_label}.",
                f"Under Revenue / Citizen Services, select 'Application for {kb['title']}'.",
                f"Fill in the applicant details (Name, Father/Husband Name, Address, and Duration of Residence).",
                f"Upload the required documents (Aadhaar/Identity proof, self-declaration, and local address proof).",
                f"Pay the statutory application fee ({kb['fee']}) and retain the Application Reference Number for tracking.",
                f"Verification is conducted by {authorities} within {sla_days} working days as mandated under the {act_name}.",
                f"Download the digitally signed certificate directly from {portal_name} or collect from your local Tehsil."
            ]
            steps_text = "\n".join([f"{idx+1}. {step}" for idx, step in enumerate(tailored_steps)])
            docs_text = "\n".join([f"• **{doc['name']}** ({'Mandatory' if doc['mandatory'] else 'Optional'}): {doc['purpose']}" for doc in kb["documents"]])
            pitfalls_text = "\n".join([f"• {p}" for p in kb.get("rejection_pitfalls", [])])

            reply = (
                f"### How to Apply for {kb['title']} in {state_label}\n\n"
                f"{kb['summary']}\n\n"
                f"**Responsible Department**: {dept_name}\n"
                f"**Official State Portal**: [{portal_name}]({portal_url})\n"
                f"**Statutory SLA Timeline**: **{sla_days} Working Days** (Guaranteed under {act_name})\n"
                f"**Statutory Application Fee**: {kb['fee']}\n\n"
                f"#### Step-by-Step Procedure ({state_label}):\n{steps_text}\n\n"
                f"#### Mandatory Documents Checklist:\n{docs_text}\n\n"
                f"#### Common Rejection Pitfalls to Avoid:\n{pitfalls_text}"
            )

            structured_guide = {
                "title": f"{kb['title']} ({state_label})",
                "department": dept_name,
                "portal_name": portal_name,
                "portal_url": portal_url,
                "sla_days": f"{sla_days} Days",
                "fee": kb["fee"],
                "steps": tailored_steps,
                "documents": kb["documents"],
                "rejection_pitfalls": kb.get("rejection_pitfalls", [])
            }

            session.add_message("user", query, intent)
            session.add_message("assistant", reply, intent)

            return {
                "session_id": session.session_id,
                "section": "haqguide",
                "intent": intent,
                "response": reply,
                "structured_guide": structured_guide,
                "matches": [],  # NO scheme recommendations!
                "follow_ups": [
                    f"Check document requirements on RejectShield",
                    f"What is the statutory deadline for {kb['title']}?",
                    f"What happens if my application is delayed?"
                ]
            }

        # OmniGovernanceEngine: Resolves EVERY possible civic, administrative, and legal query
        from ai_engine.omni_ai import answer_domain_query
        detected_state = entities.get("state") or intent_classifier._extract_state(query)
        omni_result = answer_domain_query(query=query, state=detected_state, language="English")
        ai_response = omni_result["response"]
        structured_guide = omni_result.get("structured_guide")
        ai_provider = omni_result.get("provider", "unknown")

        session.add_message("user", query, intent)
        session.add_message("assistant", ai_response, intent)

        return {
            "session_id": session.session_id,
            "section": "haqguide",
            "intent": intent,
            "response": ai_response,
            "structured_guide": structured_guide,
            "provider": ai_provider,
            "matches": [],  # Clean: no scheme cards!
            "follow_ups": [
                "Check document requirements on RejectShield",
                "What is the statutory deadline under Right to Service Act?",
                "Find government schemes I am eligible for"
            ]
        }

    # -------------------------------------------------------------
    # SECTION 2: SCHEME FINDER (Personalized Discovery)
    # -------------------------------------------------------------
    def _handle_scheme_finder(self, query: str, session, classification: Dict[str, Any]) -> Dict[str, Any]:
        session.active_section = "scheme_finder"
        entities = classification.get("entities", {})

        # Extract profile from query & session
        from backend.app.services.matcher import matcher
        extracted_profile = matcher.extract_profile_rules(query)
        session.update_profile(extracted_profile)
        user_profile = session.user_profile

        # Special case: PM-KISAN or specific scheme alternatives
        if entities.get("mode") == "alternatives":
            disqualified = entities.get("disqualified_scheme", "the requested scheme")
            reply = (
                f"### Alternative Government Benefits & Farmer Support (Alternatives to {disqualified})\n\n"
                f"If you do not meet the criteria for **{disqualified}** (e.g., due to landholding restrictions, institutional land ownership, or income tax payee status), here are verified active alternatives you can explore:\n\n"
                f"1. **Kisan Credit Card (KCC) Scheme**:\n"
                f"   • Provides low-interest institutional agricultural credit (effective rate of 4% after interest subvention).\n"
                f"   • Also available to tenant farmers, oral lessees, and allied animal husbandry / dairy workers.\n\n"
                f"2. **PM Kisan Maandhan Yojana (PM-KMY)**:\n"
                f"   • An assured monthly old-age pension of ₹3,000 for small and marginal farmers aged 18 to 40 years.\n\n"
                f"3. **Pradhan Mantri Fasal Bima Yojana (PMFBY)**:\n"
                f"   • Comprehensive crop insurance cover against non-preventable natural risks from pre-sowing to post-harvest.\n\n"
                f"4. **PM Vishwakarma Scheme (For Artisans & Rural Craftsmen)**:\n"
                f"   • If your household engages in traditional trades (carpentry, blacksmithing, tailoring, pottery), receive ₹15,000 toolkits grant and collateral-free enterprise loans at 5%."
            )
            # Find matching alternative schemes from catalog
            alt_schemes = []
            for s in registry.get_all_schemes():
                sid = s.get("scheme_id") or s.get("id")
                if sid in ["S10", "S08", "S11"]:
                    alt_schemes.append({
                        "scheme_id": sid,
                        "name": s.get("name"),
                        "department": s.get("department"),
                        "state": s.get("state", "All India"),
                        "score": 85,
                        "signal": "likely_eligible",
                        "criteria_met": ["Alternative welfare program for rural / artisan households"],
                        "criteria_unmet": [],
                        "criteria_unknown": ["Landholding / trade registration status"],
                        "verification_state": "verified",
                        "summary": s.get("eligibility_summary", ""),
                        "time_limit_days": s.get("time_limit_days", 15)
                    })

            session.add_message("user", query, "SCHEME_DISCOVERY")
            session.add_message("assistant", reply, "SCHEME_DISCOVERY")

            return {
                "session_id": session.session_id,
                "section": "scheme_finder",
                "intent": "SCHEME_DISCOVERY",
                "response": reply,
                "parsed_profile": user_profile,
                "matches": alt_schemes,
                "follow_ups": [
                    "Check PM Vishwakarma eligibility",
                    "Kisan Credit Card requirements",
                    "Upload documents to RejectShield"
                ]
            }

        # Normal scheme matching
        schemes = registry.get_all_schemes()
        tokens = set(re.findall(r'\w+', query.lower()))
        results = []

        for s in schemes:
            name = s.get("name", "").lower()
            desc = s.get("eligibility_summary", "").lower()
            dept = s.get("department", "").lower()
            tags = [t.lower() for t in s.get("tags", [])]
            content_str = f"{name} {desc} {dept} {' '.join(tags)}"

            score = 0
            # Token match
            matched_words = tokens.intersection(set(re.findall(r'\w+', content_str)))
            score += len(matched_words) * 10

            # Domain bonuses
            is_relevant = False
            if "scholarship" in tokens and "scholar" in name:
                score += 50
                is_relevant = True
            if any(k in tokens for k in ["farmer", "farmers", "kisan", "agriculture"]) and any(k in content_str for k in ["kisan", "farmer", "agriculture"]):
                score += 50
                is_relevant = True
            if any(k in tokens for k in ["health", "hospital", "ayushman", "medical"]) and "ayushman" in content_str:
                score += 50
                is_relevant = True
            if any(k in tokens for k in ["old age", "vridha", "senior citizen", "elderly"]) and "old age" in name:
                score += 50
                is_relevant = True
            elif "pension" in tokens and "pension" in content_str and not any(k in tokens for k in ["widow", "vidhwa", "disability", "divyang"]):
                score += 40
                is_relevant = True

            # Negative penalties for mismatched specific categories
            if any(k in tokens for k in ["widow", "vidhwa", "destitute"]) and "old age" in name:
                score -= 60
            if any(k in tokens for k in ["disability", "divyang", "handicap"]) and "old age" in name:
                score -= 60
            if any(k in tokens for k in ["artisan", "vishwakarma", "craftsman"]) and "vishwakarma" in content_str:
                score += 50
                is_relevant = True

            criteria_met = []
            criteria_unmet = []
            criteria_unknown = []

            # Income check
            if "annual_income" in user_profile:
                max_income = s.get("max_income")
                if max_income:
                    if user_profile["annual_income"] <= max_income:
                        criteria_met.append(f"Income ₹{user_profile['annual_income']:,} is within limit of ₹{max_income:,}")
                        score += 25
                    else:
                        criteria_unmet.append(f"Income ₹{user_profile['annual_income']:,} exceeds ceiling of ₹{max_income:,}")
                        score -= 40
            elif s.get("max_income"):
                criteria_unknown.append(f"Annual household income (limit: ₹{s['max_income']:,})")

            # Category check
            if "category" in user_profile:
                allowed_cats = s.get("allowed_categories", [])
                if allowed_cats:
                    if user_profile["category"] in allowed_cats:
                        criteria_met.append(f"Social category {user_profile['category']} qualifies")
                        score += 20
                    else:
                        criteria_unmet.append(f"Category {user_profile['category']} not in allowed quotas ({', '.join(allowed_cats)})")
                        score -= 30
            elif s.get("allowed_categories"):
                criteria_unknown.append(f"Social category ({', '.join(s['allowed_categories'])})")

            # Occupation check
            if "occupation" in user_profile:
                req_occ = s.get("target_occupation")
                if req_occ:
                    if user_profile["occupation"].lower() == req_occ.lower():
                        criteria_met.append(f"Occupation '{user_profile['occupation']}' directly aligns")
                        score += 30
                        is_relevant = True
                    else:
                        criteria_unmet.append(f"Requires occupation: {req_occ}")
                        score -= 20

            # State check
            if "state" in user_profile:
                s_state = s.get("state")
                if s_state and s_state != "All India" and s_state != "Central":
                    if user_profile["state"].lower() == s_state.lower():
                        criteria_met.append(f"State residency aligns with {s_state}")
                        score += 20
                    else:
                        criteria_unmet.append(f"Restricted to {s_state}")
                        score -= 30

            # Signal
            if criteria_unmet:
                signal = "likely_not_eligible"
            elif len(criteria_met) >= 2 and len(criteria_unknown) == 0:
                signal = "likely_eligible"
            elif criteria_unknown:
                signal = "needs_clarification"
            else:
                signal = "possibly_eligible"

            # Only include schemes with positive scores and relevance
            if score >= 35 or (is_relevant and score > 20):
                results.append({
                    "scheme_id": s.get("scheme_id", s.get("id")),
                    "name": s.get("name"),
                    "department": s.get("department", "State / Central Government"),
                    "state": s.get("state", "All India"),
                    "score": max(0, score),
                    "signal": signal,
                    "criteria_met": criteria_met,
                    "criteria_unmet": criteria_unmet,
                    "criteria_unknown": criteria_unknown,
                    "verification_state": s.get("verification_state", "verified"),
                    "source_basis": s.get("source_basis", "State citizen service charter"),
                    "time_limit_days": s.get("time_limit_days", 15),
                    "is_statutory": s.get("is_statutory", False),
                    "fee": s.get("fee", 0),
                    "summary": s.get("eligibility_summary", "")
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        top_matches = results[:4]

        # Intelligent AI Live Scheme Discovery Fallback
        # Only triggered if existing catalog matching yields 0 or insufficient results
        if len(top_matches) == 0:
            try:
                from ai_engine.ai_scheme_discovery import ai_scheme_discovery
                discovered = ai_scheme_discovery.discover_schemes(query=query, user_profile=user_profile)
                if discovered:
                    existing_names = {m["name"].lower() for m in top_matches}
                    for d in discovered:
                        if d["name"].lower() not in existing_names:
                            top_matches.append(d)
                            existing_names.add(d["name"].lower())
                    top_matches = top_matches[:4]
            except Exception as e:
                logger.warning(f"Live scheme discovery fallback error: {e}")

        # Generate follow-up questions for missing profile
        follow_ups = []
        if "annual_income" not in user_profile:
            follow_ups.append("What is your approximate total annual family income?")
        if "category" not in user_profile:
            follow_ups.append("Which social category do you belong to (General, OBC, SC, ST, EWS)?")
        if "state" not in user_profile:
            follow_ups.append("Which Indian State or Union Territory do you reside in?")

        # Construct explanation
        if top_matches:
            reply = (
                f"### Matched Government Schemes & Welfare Programs\n\n"
                f"Based on your profile ({', '.join([f'{k}: {v}' for k, v in user_profile.items()]) or 'General Inquiry'}), "
                f"we identified **{len(top_matches)} verified programs** matching your criteria.\n\n"
                f"Review the eligibility criteria below and click **Audit Documents on RejectShield** to verify your papers prior to submission."
            )
        else:
            reply = (
                "### No Schemes Found Matching Your Exact Profile\n\n"
                "We could not find any active schemes matching your exact search parameters in our catalog.\n\n"
                "**Suggestions**:\n"
                "• Try updating your social category or annual income range.\n"
                "• Search for broader terms such as 'scholarship', 'farmer support', or 'pension'.\n"
                "• Inquire in the **HaqGuide** section about required certificates like Income or Domicile."
            )

        session.add_message("user", query, "SCHEME_DISCOVERY")
        session.add_message("assistant", reply, "SCHEME_DISCOVERY")

        return {
            "session_id": session.session_id,
            "section": "scheme_finder",
            "intent": "SCHEME_DISCOVERY",
            "response": reply,
            "parsed_profile": user_profile,
            "matches": top_matches,
            "follow_ups": follow_ups[:3]
        }

    # -------------------------------------------------------------
    # SECTION 3: SCHEME EXPERT (Deep Dive Q&A)
    # -------------------------------------------------------------
    def _handle_scheme_expert(
        self,
        query: str,
        session,
        classification: Dict[str, Any],
        scheme_override: Optional[str] = None
    ) -> Dict[str, Any]:
        session.active_section = "scheme_expert"
        entities = classification.get("entities", {})

        # Resolve target scheme
        target_scheme_name = scheme_override or entities.get("scheme_name")
        target_scheme_obj = None

        if target_scheme_name:
            # Match against catalog
            for s in registry.get_all_schemes():
                sname = s.get("name", "").lower()
                sid = (s.get("scheme_id") or s.get("id") or "").lower()
                if (target_scheme_name.lower() in sname or
                    sname in target_scheme_name.lower() or
                    target_scheme_name.lower() == sid):
                    target_scheme_obj = s
                    break

        # Fallback to session active scheme
        if not target_scheme_obj and session.active_scheme:
            target_scheme_obj = session.active_scheme

        # Default fallback if still unknown
        if not target_scheme_obj:
            # Check scheme keywords using word boundaries
            if re.search(r'\b(pm-?kisan|kisan|farmer)\b', query.lower()):
                target_scheme_obj = registry.get_scheme_by_id("S01")
            elif re.search(r'\b(ayushman|pm-?jay|golden card)\b', query.lower()):
                target_scheme_obj = registry.get_scheme_by_id("S02")
            else:
                target_scheme_obj = registry.get_scheme_by_id("S05")

        session.set_scheme(target_scheme_obj)
        scheme_name = target_scheme_obj.get("name", "Selected Government Scheme")
        scheme_id = target_scheme_obj.get("scheme_id") or target_scheme_obj.get("id")

        # Get official document checklist
        doc_registry = registry.get_scheme_docs(scheme_id)
        docs = doc_registry.get("required_documents", [])
        docs_bullet = "\n".join([f"• **{d['name']}** ({'Mandatory' if d.get('mandatory') else 'Optional'}): {d.get('purpose', '')}" for d in docs])

        # Generate deep-dive response via Sarvam-105B with scheme context
        ai_reply = ""
        try:
            recent_turns = session.get_recent_history(limit=4)
            history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in recent_turns[:-1]])

            prompt = (
                f"You are the Scheme Expert AI for Indian Government Schemes.\n"
                f"CURRENT SCHEME UNDER REVIEW: {scheme_name}\n"
                f"DEPARTMENT: {target_scheme_obj.get('department')}\n"
                f"SUMMARY & RULES: {target_scheme_obj.get('eligibility_summary')}\n"
                f"MAX INCOME: ₹{target_scheme_obj.get('max_income', 'N/A')}\n"
                f"OFFICIAL SLA: {target_scheme_obj.get('time_limit_days', 15)} days\n"
                f"MANDATORY DOCUMENTS:\n{docs_bullet}\n\n"
                f"CONVERSATION HISTORY:\n{history_text or 'No prior history'}\n\n"
                f"CITIZEN QUESTION: \"{query}\"\n\n"
                "Provide an authoritative, detailed, reassuring answer directly addressing the question.\n"
                "Cite official criteria, landholding/income limits, document requirements, or common rejection pitfalls where relevant.\n"
                "Mention that they can verify their documents using RejectShield."
            )

            ai_reply = sarvam_client.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are Scheme Expert, an authoritative and helpful guide on Indian government schemes.",
                temperature=0.3,
                max_tokens=650
            )
        except Exception as e:
            logger.warning(f"Sarvam Scheme Expert call error: {e}")
            ai_reply = (
                f"### {scheme_name}\n\n"
                f"{target_scheme_obj.get('eligibility_summary', '')}\n\n"
                f"**Department**: {target_scheme_obj.get('department')}\n"
                f"**Mandatory Documents Required**:\n{docs_bullet}\n\n"
                f"You can verify your uploaded documents for this scheme using the RejectShield module."
            )

        session.add_message("user", query, "SCHEME_SPECIFIC_QUERY", {"scheme_id": scheme_id})
        session.add_message("assistant", ai_reply, "SCHEME_SPECIFIC_QUERY", {"scheme_id": scheme_id})

        return {
            "session_id": session.session_id,
            "section": "scheme_expert",
            "intent": "SCHEME_SPECIFIC_QUERY",
            "active_scheme": {
                "id": scheme_id,
                "name": scheme_name,
                "department": target_scheme_obj.get("department"),
                "summary": target_scheme_obj.get("eligibility_summary"),
                "time_limit_days": target_scheme_obj.get("time_limit_days", 15)
            },
            "response": ai_reply,
            "required_documents": docs,
            "matches": [],  # Deep dive mode - conversational, no match list dumping
            "follow_ups": [
                f"What are common rejection reasons for {scheme_name}?",
                f"What documents do I need to upload?",
                f"Audit documents on RejectShield"
            ]
        }


query_router = QueryRouter()
