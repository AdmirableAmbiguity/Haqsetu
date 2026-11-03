"""
OmniGovernanceEngine: Resilient, Multi-Provider Intelligence Engine for VachanSetu.
Answers EVERY possible related query originating in the Indian governance, citizen rights,
administrative procedures, legal safeguards, and public entitlements domain.

Multi-Tier Model Cascade:
  Tier 1: OpenAI ChatGPT (gpt-4o-mini / gpt-4o) when OPENAI_API_KEY is configured.
  Tier 2: Sarvam-105B (sarvam-105b-conversations) bilingual Indian reasoning model.
  Tier 3: Structured High-Authority Grounded Civic Domain Synthesizer (Zero-Failure Fallback).
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional, List

from ai_engine import sarvam_client

logger = logging.getLogger(__name__)

# Try loading dotenv if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

_openai_client = None

def get_openai_client():
    global _openai_client
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        return None
    if _openai_client is None:
        try:
            import openai
            _openai_client = openai.OpenAI(api_key=api_key.strip())
        except Exception as e:
            logger.warning(f"Could not initialize OpenAI client: {e}")
            return None
    return _openai_client


# Comprehensive Domain Knowledge Repository for Common Citizen Legal & Administrative Inquiries
EXTENDED_CIVIC_KB = {
    "e_shram": {
        "patterns": ["e-shram", "eshram", "unorganized worker", "shramik card", "e shram"],
        "title": "e-Shram Portal Registration for Unorganized Workers",
        "department": "Ministry of Labour & Employment, Government of India",
        "portal_name": "e-Shram National Database of Unorganised Workers",
        "portal_url": "https://eshram.gov.in",
        "act_name": "Unorganised Workers' Social Security Act, 2008",
        "sla_days": 1,
        "fee": "Nil (Completely Free at eshram.gov.in / Nominal CSC charge)",
        "summary": "National database issuance of a 12-digit Universal Account Number (UAN) e-Shram card providing ₹2 Lakh accidental insurance (PMSBY) and priority social security benefits to unorganized workers aged 16-59.",
        "steps": [
            "Visit the official e-Shram portal at eshram.gov.in or visit the nearest CSC / Jan Seva Kendra.",
            "Click on 'Register on e-Shram' and enter your Aadhaar-linked active mobile number and captcha.",
            "Enter the OTP received on your mobile phone to authenticate.",
            "Verify personal details auto-fetched from Aadhaar database (Name, DOB, Gender, Photo).",
            "Fill in address details, educational qualification, occupation/skill, and bank account details for DBT transfer.",
            "Preview self-declaration and submit. The 12-digit UAN e-Shram Card is generated instantly for free download and printing."
        ],
        "documents": [
            {"name": "Aadhaar Card", "mandatory": True, "purpose": "Aadhaar e-KYC authentication"},
            {"name": "Aadhaar-Linked Active Mobile Number", "mandatory": True, "purpose": "OTP validation"},
            {"name": "Savings Bank Account Details (Account Number & IFSC)", "mandatory": True, "purpose": "Direct benefit routing"}
        ]
    },
    "consumer": {
        "patterns": ["consumer complaint", "consumer court", "consumer rights", "defective product", "e-daakhil", "consumer forum", "उपभोक्ता", "ग्राहक फोरम", "उपभोक्ता अदालत"],
        "title": "Consumer Grievance & Dispute Redressal (e-Daakhil)",
        "department": "Department of Consumer Affairs, Ministry of Consumer Affairs, Food & Public Distribution",
        "portal_name": "National Consumer Helpline / e-Daakhil Portal",
        "portal_url": "https://edaakhil.nic.in",
        "act_name": "Consumer Protection Act, 2019",
        "sla_days": 21,
        "fee": "Nil for claims up to ₹5 Lakh; nominal court fee above ₹5 Lakh",
        "summary": "Statutory legal remedy for consumers against defective goods, deficiency in service, unfair trade practices, and misleading advertisements.",
        "steps": [
            "Lodge an informal dispute via National Consumer Helpline (NCH) app or toll-free number 1915 / consumerhelpline.gov.in.",
            "If unresolved after 15 days, send a formal Legal Notice to the company giving 15-30 days to rectify or refund.",
            "Register on e-Daakhil portal (edaakhil.nic.in) with Aadhaar e-KYC and email verification.",
            "File a Consumer Complaint before the District Consumer Disputes Redressal Commission (DCDRC) for claims up to ₹50 Lakh (State Commission for ₹50L - ₹2 Cr).",
            "Upload proof of purchase (invoice/bill), warranty card, written communications, and legal notice copy.",
            "Track case listing and attend hearing physically or through virtual video-conferencing."
        ],
        "documents": [
            {"name": "Tax Invoice / Purchase Receipt", "mandatory": True, "purpose": "Proof of transaction and consumer standing"},
            {"name": "Written Communications / Rejection Emails", "mandatory": True, "purpose": "Evidence of deficiency in service"},
            {"name": "Copy of Legal Notice sent to Merchant", "mandatory": False, "purpose": "Demonstrates pre-litigation attempt to resolve"}
        ]
    },
    "rti": {
        "patterns": ["rti", "right to information", "file rti", "section 6", "first appeal", "information commission", "सूचना का अधिकार", "आरटीआई"],
        "title": "Right to Information (RTI) Application & Statutory First Appeal",
        "department": "Department of Personnel and Training (DoPT) / State Information Commission",
        "portal_name": "RTI Online Portal (Central & State)",
        "portal_url": "https://rtionline.gov.in",
        "act_name": "Right to Information Act, 2005 (Sec 6(1) & Sec 19(1))",
        "sla_days": 30,
        "fee": "₹10 per application (Free for BPL cardholders)",
        "summary": "Fundamental transparency entitlement enabling every Indian citizen to inspect government files, extract certified copies of official records, and question delays.",
        "steps": [
            "Identify the Public Authority and its Public Information Officer (CPIO / SPIO).",
            "Visit rtionline.gov.in (for Central Ministries) or respective State RTI portal.",
            "Draft clear, numbered questions asking for factual recorded information (not subjective opinions).",
            "Pay statutory fee of ₹10 online or via Indian Postal Order (IPO).",
            "If information is not provided within 30 days (or within 48 hours for life & liberty matters), file a First Appeal under Section 19(1) to the designated First Appellate Authority (FAA).",
            "If dissatisfied with First Appeal order, file a Second Appeal to the Central/State Information Commission."
        ],
        "documents": [
            {"name": "Application Query Draft", "mandatory": True, "purpose": "Specific list of records sought"},
            {"name": "Proof of Identity / Citizenship", "mandatory": True, "purpose": "Indian citizenship compliance (Aadhaar/Voter ID)"},
            {"name": "BPL Certificate (if claiming fee exemption)", "mandatory": False, "purpose": "Exemption from ₹10 fee"}
        ]
    },
    "labor_pf": {
        "patterns": ["epfo", "provident fund", "pf advance", "uan", "gratuity", "e-shram", "maternity benefit", "unorganized worker"],
        "title": "Employees' Provident Fund (EPFO) & Labor Rights Redressal",
        "department": "Ministry of Labour and Employment, Government of India",
        "portal_name": "EPFO Unified Member Portal / e-Shram Portal",
        "portal_url": "https://unifiedportal-mem.epfindia.gov.in",
        "act_name": "EPF & MP Act 1952 / Code on Social Security 2020",
        "sla_days": 7,
        "fee": "Nil (Free statutory service)",
        "summary": "Social security rights covering monthly PF balance withdrawal, medical/housing advance, pension (EPS-95), and maternity benefits.",
        "steps": [
            "Ensure Universal Account Number (UAN) is active with Aadhaar and Bank KYC seeded.",
            "Log in to the EPFO Unified Member Portal or UMANG App.",
            "Navigate to 'Online Services' -> Select Claim (Form 31, 19, 10C, or 10D).",
            "For medical illness or unemployment advance, select Form 31 (Para 68J / 68B) which requires no employer attestation.",
            "Upload cancelled cheque or scanned bank passbook showing Name and IFSC clearly.",
            "Authenticate via Aadhaar OTP. Statutory settlement occurs within 3 to 7 working days directly into your bank account.",
            "For grievances against non-crediting or delayed settlement, lodge a ticket on EPFiGMS (epfigms.gov.in)."
        ],
        "documents": [
            {"name": "UAN Linked with Aadhaar", "mandatory": True, "purpose": "Universal Member verification"},
            {"name": "Cancelled Cheque / Passbook Copy", "mandatory": True, "purpose": "Bank IFSC and account number verification"}
        ]
    },
    "arrest_rights": {
        "patterns": ["arrest rights", "rights if arrested", "arrested by police", "right after arrest",
                     "giraftari ke adhikar", "giraftari", "rights when arrested", "police ne pakad",
                     "illegal detention", "giraftar", "section 41", "habeas corpus",
                     "\u0917\u093f\u0930\u092b\u094d\u0924\u093e\u0930\u0940", "\u0939\u093f\u0930\u093e\u0938\u0924", "\u0917\u093f\u0930\u092e\u095e\u094d\u0924\u093e\u0930"],
        "title": "Fundamental Rights of a Person Arrested by Police (India)",
        "department": "Ministry of Home Affairs / State Police / Judiciary / DLSA",
        "portal_name": "National Human Rights Commission",
        "portal_url": "https://nhrc.nic.in",
        "act_name": "Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023 / Article 20, 21, 22 Constitution / D.K. Basu Guidelines",
        "sla_days": 24,
        "fee": "Nil",
        "summary": "Every person arrested in India has constitutionally guaranteed rights. Police CANNOT detain without immediately stating the reason, informing family, providing legal aid, and producing before a Magistrate within 24 hours.",
        "steps": [
            "RIGHT TO BE INFORMED: Police MUST immediately inform the arrested person of the GROUNDS of arrest in a language they understand (Article 22(1) Constitution / Sec 47 BNSS).",
            "RIGHT TO INFORM RELATIVE: You have the absolute right to have ONE person of your choice (family, friend, or advocate) informed immediately of your arrest and detention location (D.K. Basu Guidelines / Sec 49 BNSS).",
            "RIGHT TO FREE LEGAL AID: You are entitled to consult a lawyer at any stage. If you cannot afford one, DEMAND a free government lawyer from the District Legal Services Authority (DLSA) — this is a statutory right under Section 12 of the Legal Services Authorities Act.",
            "RIGHT AGAINST SELF-INCRIMINATION: No person can be forced to testify against themselves (Article 20(3) Constitution). You may remain silent except when identifying yourself.",
            "RIGHT TO MEDICAL EXAMINATION: You are entitled to a medical examination by a doctor on request (Sec 53 BNSS) — critical if you allege physical mistreatment or torture.",
            "24-HOUR MAGISTRATE RULE: Police CANNOT hold you for more than 24 hours without producing you before a Judicial Magistrate (Article 22(2) / Sec 57 BNSS). Only the Magistrate can authorize further custody (judicial remand).",
            "Section 41A NOTICE (for bailable / non-cognizable): Police must first issue a notice before arresting for bailable offenses. If arrested without notice, apply for bail immediately before the Magistrate.",
            "IF RIGHTS ARE VIOLATED: File with State Human Rights Commission or National Human Rights Commission (nhrc.nic.in). File Habeas Corpus petition in Sessions Court / High Court if detained unlawfully."
        ],
        "documents": [
            {"name": "Identity Proof (Aadhaar / Voter ID)", "mandatory": False, "purpose": "Verification upon police demand"},
            {"name": "Legal Aid Application Form (DLSA)", "mandatory": False, "purpose": "For free legal representation"},
            {"name": "Medical Examination Report (MLC)", "mandatory": False, "purpose": "Evidence if police brutality alleged"}
        ]
    },
    "police_fir": {
        "patterns": ["police complaint", "zero fir", "fir rights", "police harassment", "police fir", "police", "fir", "thana", "darj", "पुलिस", "एफआईआर", "थाना", "रपट"],
        "title": "Police Complaint, FIR Registration & Citizen Safeguards",
        "department": "State Police Department / Ministry of Home Affairs",
        "portal_name": "State Citizen Police Portal / National Cyber Crime Portal",
        "portal_url": "https://cybercrime.gov.in",
        "act_name": "Bharatiya Nagarik Suraksha Sanhita (BNSS) / CrPC & Lalita Kumari Supreme Court Judgment",
        "sla_days": 1,
        "fee": "Nil (Free public duty)",
        "summary": "Citizen safeguards and statutory procedure for reporting cognizable and non-cognizable offenses without unlawful refusal.",
        "steps": [
            "Write a factual complaint describing date, time, location, suspect details, and sequence of events.",
            "Visit the jurisdictional Police Station. In emergency situations, you have the right to register a 'Zero FIR' at ANY police station irrespective of territorial jurisdiction.",
            "By Supreme Court mandate (Lalita Kumari vs Govt of UP), police MUST register an FIR immediately for cognizable offenses.",
            "You are entitled to a FREE certified copy of the registered FIR on the spot (Section 154 CrPC / Sec 173 BNSS).",
            "If police refuse to register an FIR: send the written complaint by Registered Post to the Superintendent of Police (SP / DCP) under Section 154(3) CrPC / Sec 173(4) BNSS.",
            "If still unaddressed: file an application before the Judicial Magistrate under Section 156(3) CrPC / Sec 175 BNSS directing police to investigate."
        ],
        "documents": [
            {"name": "Signed Written Complaint", "mandatory": True, "purpose": "Written statement of facts"},
            {"name": "Supporting Evidence (Photos / CCTV / Medical MLC)", "mandatory": False, "purpose": "Corroboration"}
        ]
    },
    "marriage": {
        "patterns": ["marriage registration", "marriage certificate", "court marriage", "special marriage act"],
        "title": "Compulsory Marriage Registration Certificate",
        "department": "Revenue Department (Inspector General of Registration) / District Administration",
        "portal_name": "State e-District / IGRS Portal",
        "portal_url": "https://services.india.gov.in",
        "act_name": "Special Marriage Act, 1954 / Hindu Marriage Act, 1955 / Compulsory Registration Rules",
        "sla_days": 15,
        "fee": "₹100 - ₹250 (depending on state statutory rules)",
        "summary": "Legal registration of solemnized marriage providing conclusive proof of spousal status for passport, visa, joint property, and inheritance.",
        "steps": [
            "Access your State Registration / IGRS portal or e-District portal.",
            "Select 'Marriage Registration' and enter groom and bride demographic details.",
            "Upload wedding photograph, wedding card / religious institution certificate, age proof, and address proof for both partners.",
            "Provide witness details (minimum 3 adult witnesses with valid Aadhaar/Voter IDs).",
            "Book an appointment slot at the Sub-Registrar Office (SRO).",
            "Attend the SRO on the scheduled date with original documents and witnesses for biometric recording and certificate issuance."
        ],
        "documents": [
            {"name": "Aadhaar Card of Groom & Bride", "mandatory": True, "purpose": "Identity and age verification (Min 21M / 18F)"},
            {"name": "Wedding Photograph & Wedding Invitation Card", "mandatory": True, "purpose": "Evidence of solemnization"},
            {"name": "Aadhaar of 3 Witnesses", "mandatory": True, "purpose": "Statutory attestation"}
        ]
    },
    "legal_heir": {
        "patterns": ["legal heir", "varisan", "succession certificate", "survivor certificate", "death of parent"],
        "title": "Legal Heir / Succession Certificate (वारिसाना प्रमाण पत्र)",
        "department": "Revenue Department (Tehsildar / District Court)",
        "portal_name": "State e-District Portal / Revenue Court Portal",
        "portal_url": "https://services.india.gov.in",
        "act_name": "Indian Succession Act, 1925 / State Revenue Code",
        "sla_days": 30,
        "fee": "₹15 - ₹50 (Revenue Portal) / Stamp Duty for Court Succession",
        "summary": "Mandatory administrative certificate identifying legitimate heirs of a deceased person for transferring bank accounts, property mutation, and pensions.",
        "steps": [
            "Obtain original Death Certificate of the deceased family member from the local civic body / municipal registrar.",
            "Log in to State e-District portal or submit physical application to the Area Tehsildar / Talathi.",
            "Fill in family pedigree (Vansh-Vriksha) detailing all surviving Class-I legal heirs (spouse, sons, daughters, mother).",
            "Upload notarized family affidavit declaring that no other heirs exist.",
            "Lekhpal / Revenue Inspector conducts field inquiry and Gram Panchayat verification.",
            "A 15-day public objection notice is published; if undisputed, the Tehsildar issues the digitally signed Legal Heir Certificate."
        ],
        "documents": [
            {"name": "Death Certificate of Deceased", "mandatory": True, "purpose": "Proof of demise"},
            {"name": "Aadhaar Cards of all Surviving Heirs", "mandatory": True, "purpose": "Heir identity proof"},
            {"name": "Notarized Family Pedigree Affidavit", "mandatory": True, "purpose": "Legal undertaking of surviving lineage"}
        ]
    },
    "senior_citizen": {
        "patterns": ["senior citizen", "maintenance tribunal", "parents harassment", "evict son", "maintenance act 2007", "vridha", "mata pita", "वरिष्ठ नागरिक", "बुजुर्ग", "माता पिता", "माता-पिता"],
        "title": "Senior Citizens Maintenance & Welfare Tribunal Protection",
        "department": "Department of Social Justice and Empowerment / Sub-Divisional Magistrate (SDM)",
        "portal_name": "District Magistrate / SDM Maintenance Tribunal",
        "portal_url": "https://socialjustice.gov.in",
        "act_name": "Maintenance and Welfare of Parents and Senior Citizens Act, 2007",
        "sla_days": 90,
        "fee": "Nil (Completely free for senior citizens)",
        "summary": "Speedy summary legal remedy enabling parents and senior citizens (60+) to claim monthly maintenance from children/relatives and revoke gift deeds if neglected.",
        "steps": [
            "Any parent or senior citizen unable to maintain themselves can file a simple written application before the SDM (Maintenance Tribunal).",
            "No advocate is necessary; the Tribunal conducts informal, conciliation-oriented summary proceedings.",
            "The Tribunal can order children/legal heirs to pay monthly maintenance up to statutory limits within 90 days.",
            "Under Section 23 of the Act: If property was transferred/gifted to children with a condition of care, and children fail to provide basic physical needs, the Tribunal can declare the transfer VOID as made by fraud or coercion.",
            "Senior citizens can seek an eviction order against abusive children from their self-acquired or ancestral home."
        ],
        "documents": [
            {"name": "Age Proof (Aadhaar / Voter ID / Birth Record)", "mandatory": True, "purpose": "Verification of age 60+"},
            {"name": "Property Ownership Record (if claiming protection/eviction)", "mandatory": False, "purpose": "Proof of self-acquired property"}
        ]
    },
    "tenant_rights": {
        "patterns": ["tenant", "tenants", "eviction", "evict", "kirayedaar", "makaan malik", "rent agreement", "rent control", "unlawful eviction", "model tenancy", "किराएदार", "किराया", "मकान मालिक", "मकान"],
        "title": "Tenant Rights & Protection Against Unlawful Eviction",
        "department": "Rent Authority / Rent Court / Rent Tribunal (District Administration)",
        "portal_name": "State Urban Development & Revenue Portal",
        "portal_url": "https://services.india.gov.in",
        "act_name": "Model Tenancy Act / State Rent Control Act & Transfer of Property Act (Sec 106)",
        "sla_days": 30,
        "fee": "Nominal fee for Rent Tribunal filing",
        "summary": "Under Indian law, a landlord CANNOT forcibly evict a tenant or cut electricity/water connections without a formal statutory notice and order from a competent Rent Court.",
        "steps": [
            "Landlord must serve a formal written eviction notice (minimum 15 to 30 days notice period under Section 106 of Transfer of Property Act).",
            "Forcible lockout, throwing belongings, or disconnecting electricity/water is illegal and punishable as criminal trespass and intimidation (BNS / IPC).",
            "If landlord harasses or disconnects utilities: file an immediate police complaint and petition the Rent Authority for restoration of essential supplies.",
            "Eviction can only occur on statutory grounds (non-payment of rent, substantial damage, or bonafide personal requirement) proved before the Rent Tribunal.",
            "Security deposit must be refunded upon handover of peaceful possession minus actual verified damage."
        ],
        "documents": [
            {"name": "Registered / Notarized Rent Agreement", "mandatory": True, "purpose": "Proof of tenancy and terms"},
            {"name": "Rent Receipts / Bank Transfer Proofs", "mandatory": True, "purpose": "Evidence of regular rent compliance"},
            {"name": "Copy of Eviction Notice (if served)", "mandatory": False, "purpose": "Verification of notice validity"}
        ]
    },
    "electricity_dispute": {
        "patterns": ["electricity bill", "bijli bill", "meter fast", "power disconnection", "power theft", "electricity grievance", "cgrf", "electricity ombudsman", "bijli", "electricity", "बिजली", "मीटर", "विद्युत"],
        "title": "Electricity Bill Dispute & Disconnection Protection (CGRF)",
        "department": "Consumer Grievance Redressal Forum (CGRF) & State Electricity Regulatory Commission (SERC)",
        "portal_name": "State DISCOM Portal / State Electricity Ombudsman",
        "portal_url": "https://services.india.gov.in",
        "act_name": "Electricity Act, 2003 (Section 42(5) & Section 56)",
        "sla_days": 15,
        "fee": "Nil (Free statutory grievance process)",
        "summary": "Statutory rights against arbitrary high power bills, faulty meters, and illegal disconnection without mandatory 15-day written notice.",
        "steps": [
            "Submit a formal written disputed bill complaint to your Sub-Divisional Officer (SDO) or Executive Engineer (EE).",
            "Request meter testing by paying standard test fee. If meter is found defective, DISCOM must revise bills for preceding 6 months.",
            "Under Section 56 of Electricity Act 2003: DISCOM CANNOT disconnect power without giving at least 15 CLEAR DAYS prior written notice.",
            "If SDO does not resolve within 15 days: file a complaint before the Consumer Grievance Redressal Forum (CGRF) of your DISCOM.",
            "You can pay 50% of undisputed average bill under protest to ensure supply is never disconnected while dispute is pending.",
            "If dissatisfied with CGRF order, appeal to the State Electricity Ombudsman within 30 days."
        ],
        "documents": [
            {"name": "Disputed Electricity Bill Copy", "mandatory": True, "purpose": "Record of disputed charges"},
            {"name": "Past 6-12 Months Paid Bills", "mandatory": True, "purpose": "Baseline consumption proof"},
            {"name": "Written Representation to SDO / DISCOM", "mandatory": True, "purpose": "Proof of prior representation"}
        ]
    },
    "water_municipal": {
        "patterns": ["water bill", "water supply", "sewer complaint", "drainage issue", "municipal corporation", "nagar nigam", "municipality", "jal board", "jal sansthan"],
        "title": "Municipal Corporation & Jal Sansthan Grievance Redressal",
        "department": "Urban Local Body (Nagar Nigam / Municipality) & Jal Sansthan",
        "portal_name": "State Urban Civic Services / e-NagarSewa Portal",
        "portal_url": "https://services.india.gov.in",
        "act_name": "State Municipal Corporation Act & Right to Public Services Act",
        "sla_days": 7,
        "fee": "Nil (Public utility duty)",
        "summary": "Mandatory civic delivery of clean drinking water, sewer clearance, drainage maintenance, and street maintenance within statutory SLA limits.",
        "steps": [
            "Register complaint on your City Municipal Portal or State CM Helpline (e.g. UP 1076, Delhi Jal Board 1916).",
            "Quote your Consumer Water Connection Number and ward/zone location.",
            "Under Right to Service Act, sewer overflow must be cleared within 24-48 hours; dirty water complaints within 3 days.",
            "If unaddressed within SLA: file a written complaint to the Municipal Commissioner / Executive Officer (EO).",
            "Persistent failure enables filing an appeal before the RTSA Appellate Officer and claiming statutory compensation."
        ],
        "documents": [
            {"name": "Water Connection Bill / ID", "mandatory": True, "purpose": "Consumer account verification"},
            {"name": "Photographs of Sewer Overflow / Pipe Leak", "mandatory": False, "purpose": "Evidence of grievance"}
        ]
    },
    "domestic_violence_women": {
        "patterns": ["domestic violence", "mahila helpline", "women harassment", "dowry harassment", "patni", "maintenance for wife", "protection order", "pwdva", "181 helpline", "1090", "घरेलू हिंसा", "दहेज", "महिला हेल्पलाइन"],
        "title": "Domestic Violence Protection, Women Rights & Emergency Relief",
        "department": "Protection Officer / Judicial Magistrate / National Commission for Women (NCW)",
        "portal_name": "National Commission for Women / State Women Helpline",
        "portal_url": "https://ncw.nic.in",
        "act_name": "Protection of Women from Domestic Violence Act, 2005 (PWDVA) / Bharatiya Nyaya Sanhita (Sec 85/86)",
        "sla_days": 3,
        "fee": "Nil (Free legal assistance via DLSA)",
        "summary": "Comprehensive legal safeguard providing emergency protection orders, right to reside in shared household, monetary maintenance, and custody rights for women facing physical, emotional, or economic abuse.",
        "steps": [
            "In emergency: Call 112 (National Emergency), 181 (Women Helpline), or 1090 (Women Power Line).",
            "Contact the District Protection Officer (located in District Magistrate / Collectorate office) or nearest One Stop Centre (Sakhi).",
            "The Protection Officer prepares a Domestic Incident Report (DIR) and files it before the Judicial Magistrate.",
            "Court is legally bound to hold the first hearing within 3 days of receiving application under PWDVA Section 12.",
            "Magistrate can grant ex-parte Protection Orders (preventing abuser from contacting or entering victim's residence), Residence Orders, and interim maintenance.",
            "Free legal counsel is provided automatically through the District Legal Services Authority (DLSA)."
        ],
        "documents": [
            {"name": "Written Incident Complaint", "mandatory": True, "purpose": "Factual description of abuse"},
            {"name": "Medical Examination / MLC Report (if physical injury)", "mandatory": False, "purpose": "Forensic evidence of violence"},
            {"name": "Proof of Shared Residence / Marriage", "mandatory": False, "purpose": "Jurisdiction proof"}
        ]
    },
    "traffic_challan": {
        "patterns": ["traffic challan", "echallan", "challan payment", "wrong challan", "contest challan", "virtual court", "traffic police"],
        "title": "Traffic E-Challan Verification, Contest & Virtual Court Settlement",
        "department": "Traffic Police / Department of Justice Virtual Courts",
        "portal_name": "Parivahan e-Challan / Virtual Courts India",
        "portal_url": "https://vcourts.gov.in",
        "act_name": "Motor Vehicles (Amendment) Act, 2019 / Section 208 CrPC / Sec 231 BNSS",
        "sla_days": 1,
        "fee": "Fine amount or Nil if contested/dismissed",
        "summary": "Official procedure for reviewing photo evidence of traffic violations, paying online, or contesting wrongful challans through Virtual Courts or National Lok Adalat.",
        "steps": [
            "Visit echallan.parivahan.gov.in and check challan details by entering Vehicle Number or Challan Number.",
            "Review camera photo/video evidence. If wrong vehicle number or cloned plate is detected, submit grievance on portal with RC copy.",
            "If challan is sent to court: visit vcourts.gov.in -> Select your State and Virtual Court.",
            "You have two options: 'Plead Guilty & Pay Fine' (reduced fine) or 'I wish to contest' (transfers matter to regular court for hearing).",
            "For significant compounding or waiver of pending compoundable challans, attend the quarterly National Lok Adalat."
        ],
        "documents": [
            {"name": "Vehicle Registration Certificate (RC)", "mandatory": True, "purpose": "Vehicle ownership verification"},
            {"name": "Driving License (DL)", "mandatory": True, "purpose": "Driver identity proof"},
            {"name": "Challan Notice / Transaction Number", "mandatory": True, "purpose": "Case reference"}
        ]
    },
    "rte_quota": {
        "patterns": ["rte", "right to education", "25 percent quota", "25% quota", "free school admission", "rte 12", "poor children admission"],
        "title": "Right to Education (RTE) 25% Free Admission in Private Schools",
        "department": "Department of School Education & Literacy / State Basic Education Directorate",
        "portal_name": "State RTE Portal (e.g., rte25.upsdc.gov.in)",
        "portal_url": "https://services.india.gov.in",
        "act_name": "Right of Children to Free and Compulsory Education (RTE) Act, 2009 (Section 12(1)(c))",
        "sla_days": 30,
        "fee": "Nil (Completely free; school tuition reimbursed by Government)",
        "summary": "Statutory entitlement reserving 25% of entry-level seats (Nursery / Class 1) in private unaided schools for children from Economically Weaker Sections (EWS) and disadvantaged groups.",
        "steps": [
            "Check annual admission notification on your State RTE portal (typically Jan - March each year).",
            "Register online by filling child demographic details, Aadhaar, and residential address.",
            "Select neighborhood private schools within 1 to 3 km radius from residence.",
            "Upload birth certificate, income certificate (EWS limit ₹1 Lakh / ₹2 Lakh per state rules), and domicile proof.",
            "Seats are allocated through a computerized transparent lottery conducted by District Education Officer (BSA / DEO).",
            "Upon selection, report to allotted private school; no admission fees or tuition can be charged from parents."
        ],
        "documents": [
            {"name": "Child Birth Certificate / Hospital Card", "mandatory": True, "purpose": "Age verification (3 to 6 years)"},
            {"name": "Income Certificate from Tehsildar (EWS proof)", "mandatory": True, "purpose": "Economic criteria compliance"},
            {"name": "Parent Aadhaar Card & Local Address Proof", "mandatory": True, "purpose": "Neighborhood residency within school zone"}
        ]
    },
    "land_mutation": {
        "patterns": ["land mutation", "dakhil kharij", "mutation of land", "property mutation", "khatauni name change", "inheritance land", "tehsil mutation", "dakhil-kharij"],
        "title": "Land Mutation / Dakhil-Kharij (दाखिल-खारिज) Procedure",
        "department": "Revenue Department (राजस्व विभाग) / Naib Tehsildar Court",
        "portal_name": "State Revenue Court Computerized System (RCCMS / Bhulekh)",
        "portal_url": "https://services.india.gov.in",
        "act_name": "State Land Revenue Code & Right to Public Services Act",
        "sla_days": 35,
        "fee": "₹15 to ₹50 statutory fee",
        "summary": "Statutory process of recording transfer of land title in revenue records (Khatauni / Jamabandi) following sale deed execution, inheritance, or gift.",
        "steps": [
            "Following registered sale deed or inheritance, apply online on State Revenue Court portal (e.g., vaad.up.nic.in) or submit at Tehsil.",
            "Attach registered deed copy or death certificate + family pedigree (Varisan) for inheritance.",
            "Tehsildar issues a 35-day public notice (Ishtehaar) inviting objections.",
            "Area Lekhpal / Patwari submits field verification report confirming possession.",
            "If no valid legal objection is raised, Naib Tehsildar passes mutation order (Dakhil-Kharij Aadesh).",
            "Revenue record keeper updates Khatauni and buyer/heir name is entered on official Bhulekh portal."
        ],
        "documents": [
            {"name": "Registered Sale Deed / Gift Deed / Will Copy", "mandatory": True, "purpose": "Title transfer basis"},
            {"name": "Latest Khatauni / Land Record Extract", "mandatory": True, "purpose": "Khasra number identification"},
            {"name": "Death Certificate & Heir Affidavit (for inheritance)", "mandatory": False, "purpose": "Lineage proof"}
        ]
    },
    "disability_udid": {
        "patterns": ["disability certificate", "divyang", "udid card", "disability rights", "handicap certificate", "rpwd act"],
        "title": "Unique Disability ID (UDID) & Rights of Persons with Disabilities",
        "department": "Department of Empowerment of Persons with Disabilities / Chief Medical Officer (CMO)",
        "portal_name": "UDID Portal (Swavlamban)",
        "portal_url": "https://swavlambancard.gov.in",
        "act_name": "Rights of Persons with Disabilities (RPwD) Act, 2016",
        "sla_days": 30,
        "fee": "Nil (Free statutory certificate)",
        "summary": "Nationally recognized single digital identity card for persons with 40%+ benchmark disabilities, providing nationwide access to travel concessions, pensions, and quotas.",
        "steps": [
            "Register online on Swavlamban Card portal (swavlambancard.gov.in).",
            "Fill in personal details, Aadhaar, address, and disability category (21 recognized disabilities under RPwD Act).",
            "Upload photo, signature/thumb impression, and identity proof.",
            "Portal assigns an appointment at the District Hospital / Chief Medical Officer (CMO) Medical Board.",
            "Attend medical examination; Medical Board evaluates disability percentage.",
            "UDID Card and digital certificate are issued online and physical card is delivered via speed post."
        ],
        "documents": [
            {"name": "Aadhaar Card", "mandatory": True, "purpose": "Identity and address proof"},
            {"name": "Passport Size Photograph", "mandatory": True, "purpose": "UDID card printing"},
            {"name": "Previous Medical Records / Hospital Slips", "mandatory": False, "purpose": "Clinical evaluation history"}
        ]
    },
    "cyber_fraud_banking": {
        "patterns": ["cyber crime", "online fraud", "atm fraud", "upi fraud", "unauthorized transaction", "bank fraud", "banking ombudsman", "1930 helpline", "1930"],
        "title": "Cyber Crime Reporting, Financial Fraud & RBI Banking Ombudsman",
        "department": "National Cyber Crime Reporting Portal / Reserve Bank of India (RBI)",
        "portal_name": "National Cyber Crime Portal / RBI CMS Portal",
        "portal_url": "https://cybercrime.gov.in",
        "act_name": "Information Technology Act, 2000 & RBI Customer Protection Circular on Limited Liability",
        "sla_days": 30,
        "fee": "Nil (Free grievance resolution)",
        "summary": "Statutory recovery mechanism for online financial frauds, unauthorized UPI/card transactions, and banking service deficiencies.",
        "steps": [
            "Within 24 hours of fraud: Call toll-free National Cyber Helpline 1930 immediately to freeze fraudulent transaction trail.",
            "Register formal complaint on cybercrime.gov.in and download copy of financial fraud acknowledgement.",
            "Notify your bank immediately in writing within 3 working days. Under RBI guidelines: Citizen has ZERO liability for third-party digital fraud if reported within 3 days.",
            "Bank is mandated to reverse disputed amount (shadow credit) within 10 working days pending inquiry.",
            "If bank rejects or delays resolution beyond 30 days: lodge complaint with the RBI Banking Ombudsman at cms.rbi.org.in."
        ],
        "documents": [
            {"name": "Bank Statement showing Fraudulent Debit", "mandatory": True, "purpose": "Transaction ID and timestamp proof"},
            {"name": "Cybercrime Acknowledgement Slip (1930 / portal)", "mandatory": True, "purpose": "Proof of immediate reporting"},
            {"name": "Copy of Written Dispute Letter to Bank", "mandatory": True, "purpose": "Proof of notification within 3 days"}
        ]
    },
    "msme_payment": {
        "patterns": ["msme delayed payment", "samadhaan", "vendor payment delay", "msmed act", "buyer not paying", "delayed payment"],
        "title": "MSME Samadhaan — Statutory Recovery of Delayed Payments",
        "department": "Ministry of Micro, Small & Medium Enterprises / MSEFC",
        "portal_name": "MSME Samadhaan Portal",
        "portal_url": "https://samadhaan.msme.gov.in",
        "act_name": "Micro, Small and Medium Enterprises Development (MSMED) Act, 2006 (Section 15-18)",
        "sla_days": 90,
        "fee": "Nil",
        "summary": "Mandatory legal entitlement forcing buyers to clear MSME invoices within 45 days. Delayed payments carry compound interest at three times the RBI bank rate.",
        "steps": [
            "Ensure enterprise possesses active Udyam Registration certificate dated prior to invoice date.",
            "Under Section 15 MSMED Act, buyer must make payment within agreed period (maximum 45 days from delivery).",
            "Log in to samadhaan.msme.gov.in with Udyam Number and OTP.",
            "Upload unpaid tax invoices, purchase orders (PO), and proof of goods/services delivery.",
            "Portal automatically issues statutory notice to buyer demanding immediate payment with 3x RBI interest.",
            "If unresolved, case is heard by State Micro & Small Enterprise Facilitation Council (MSEFC) with powers of Civil Court."
        ],
        "documents": [
            {"name": "Udyam Registration Certificate", "mandatory": True, "purpose": "MSME legal standing"},
            {"name": "Tax Invoices & Purchase Orders", "mandatory": True, "purpose": "Proof of supply and agreed terms"},
            {"name": "Goods Delivery Challan / Work Completion Signoff", "mandatory": True, "purpose": "Proof of undisputed delivery"}
        ]
    },
    "ration_dealer_pds": {
        "patterns": ["ration dealer", "rashan dealer", "quota not given", "less ration", "ration complaint", "pds complaint", "kotedar", "rashan nahi de raha", "कोटेदार", "राशन डीलर", "राशन"],
        "title": "PDS Fair Price Shop (Ration Dealer) Grievance Redressal",
        "department": "Food and Civil Supplies Department (खाद्य एवं रसद विभाग) / State Food Commission",
        "portal_name": "State Food & Civil Supplies Portal",
        "portal_url": "https://nfsa.gov.in",
        "act_name": "National Food Security Act (NFSA), 2013 (Section 14-20)",
        "sla_days": 15,
        "fee": "Nil",
        "summary": "Legal guarantee under NFSA 2013 ensuring every NFSA cardholder receives prescribed monthly foodgrains (5kg/person for Priority, 35kg for Antyodaya) without underweighing or overcharging.",
        "steps": [
            "Call National PDS Toll-Free Helpline 1967 or your State FCS Helpline (e.g. UP 1800-1800-150).",
            "Lodge written complaint with the Area Supply Inspector (Purti Nirikshak) or Sub-Divisional Magistrate (SDM).",
            "Under Section 15 NFSA: District Grievance Redressal Officer (DGRO / ADM) must investigate and redress issue within 30 days.",
            "Dealers found indulging in diversion, biometric denial, or weight manipulation face license suspension and FIR under Essential Commodities Act (ECA Sec 3/7).",
            "If local officer shields dealer: appeal directly to the State Food Commission."
        ],
        "documents": [
            {"name": "Ration Card (Ration Card Number)", "mandatory": True, "purpose": "Active NFSA quota verification"},
            {"name": "e-PoS Machine Slip (if issued with less weight)", "mandatory": False, "purpose": "Evidence of under-distribution"}
        ]
    },
    "maternity_benefit": {
        "patterns": ["maternity benefit", "maternity leave", "maternity duration", "pregnancy leave", "creche facility", "maternity benefit act"],
        "title": "Maternity Benefit Rights, 26 Weeks Paid Leave & Employment Security",
        "department": "Ministry of Labour & Employment / Chief Labour Commissioner",
        "portal_name": "Ministry of Labour & Employment / State Labour Portal",
        "portal_url": "https://labour.gov.in",
        "act_name": "Maternity Benefit (Amendment) Act, 2017 / Code on Social Security 2020",
        "sla_days": 1,
        "fee": "Nil (Statutory employee entitlement)",
        "summary": "Statutory mandate providing 26 weeks (182 days) fully paid maternity leave to women employees who worked for at least 80 days in the preceding 12 months.",
        "steps": [
            "Give written notice to employer specifying expected delivery date and start date of maternity leave (up to 8 weeks before delivery).",
            "Employer MUST pay full average daily wages during the 26-week absence.",
            "For women with 2 or more surviving children, paid leave entitlement is 12 weeks.",
            "Section 12 strictly PROHIBITS dismissing, terminating, or reducing wages of a woman during maternity leave.",
            "Establishments with 50+ employees MUST provide mandatory creche facility within 500 meters with 4 visits allowed daily.",
            "If employer denies benefit: file written complaint before the jurisdictional Labour Inspector under Section 17 of the Act."
        ],
        "documents": [
            {"name": "Doctor Certificate / Pregnancy Ultrasound Report", "mandatory": True, "purpose": "Proof of pregnancy and expected delivery"},
            {"name": "Written Maternity Leave Application", "mandatory": True, "purpose": "Formal notice to employer"},
            {"name": "Attendance / Pay Slips proving 80 days work", "mandatory": True, "purpose": "Statutory eligibility compliance"}
        ]
    },
    "ngo_society": {
        "patterns": ["ngo registration", "society registration", "trust registration", "section 8", "darpan portal", "samiti registration"],
        "title": "NGO, Society & Trust Registration Procedure",
        "department": "Registrar of Societies & Chits / Ministry of Corporate Affairs / NITI Aayog",
        "portal_name": "NITI Aayog NGO DARPAN / State IGRS Portal",
        "portal_url": "https://ngodarpan.gov.in",
        "act_name": "Societies Registration Act, 1860 / Indian Trusts Act, 1882 / Companies Act 2013",
        "sla_days": 30,
        "fee": "₹100 to ₹1000 depending on state statutory rules",
        "summary": "Official registration pathways for non-profit entities: Society (min 7 members), Trust (min 2 trustees), or Section 8 Company.",
        "steps": [
            "Choose structure: Society (Social/educational welfare), Trust (Charitable endowments), or Section 8 (Nationwide corporate non-profit).",
            "Draft Memorandum of Association (MoA) and Rules & Regulations outlining charitable objectives.",
            "Obtain NOC from property owner for registered office and gather ID/address proofs of all governing body members.",
            "Submit online on State Registrar of Societies portal (e.g. `prerna.up.gov.in` / IGRS) or Sub-Registrar office.",
            "Upon inspection and fee payment, Certificate of Registration is issued.",
            "Register on NITI Aayog NGO DARPAN (ngodarpan.gov.in) to qualify for government grants and CSR funding."
        ],
        "documents": [
            {"name": "Memorandum of Association (MoA) & By-Laws", "mandatory": True, "purpose": "Governing rules and aims"},
            {"name": "Aadhaar & PAN of all Governing Members", "mandatory": True, "purpose": "Trustee / member identity"},
            {"name": "Electricity Bill / Rent Agreement of Office", "mandatory": True, "purpose": "Registered office address proof"}
        ]
    },
    "will_testament": {
        "patterns": ["will", "testament", "will banane", "how to make a will", "wills act",
                     "vasiyat", "vasiat", "succession planning", "nominee vs legal heir",
                     "वसीयत", "उत्तराधिकार"],
        "title": "How to Make a Valid Will (Vasiyat) in India",
        "department": "Sub-Registrar Office / District Registrar (for registration) / No authority required for an unregistered Will",
        "portal_name": "State Registration & Stamps Department / IGRS Portal",
        "portal_url": "https://igrs.gov.in",
        "act_name": "Indian Succession Act, 1925 / Hindu Succession Act, 1956 / Indian Registration Act, 1908",
        "sla_days": 1,
        "fee": "Nil (Unregistered Will) / Nominal stamp duty for registered Will",
        "summary": "A Will (Vasiyat) is a legal document expressing a person\'s wishes for distributing property after death. While registration is optional (but strongly recommended), a Will must be signed by the testator and witnessed by 2 adults to be legally valid.",
        "steps": [
            "ELIGIBILITY: Any person of sound mind, aged 18+ years, owning property can make a Will (called the Testator). There is no mandatory government permission or format.",
            "DRAFT THE WILL: Clearly state: (1) Your full name, address, Aadhaar; (2) Description of each asset (property, bank accounts, shares, FDs, jewelry); (3) Name and relationship of each beneficiary; (4) Appointment of an Executor (trusted person to implement the will).",
            "SIGNATURE: Sign the Will in the presence of 2 adult witnesses who must also sign. Witnesses CANNOT be beneficiaries in the same Will.",
            "OPTIONAL REGISTRATION (Highly Recommended): Visit the Sub-Registrar Office with the original Will, 2 witnesses, and Aadhaar. Pay nominal stamp duty. Registered Wills are harder to challenge and have strong evidentiary value.",
            "SAFE CUSTODY: Store the original Will in a safe place. Inform the Executor of its location. You may also deposit it in court for safe custody under Section 42 of Indian Registration Act.",
            "AFTER DEATH (Probate): For property in certain cities (Mumbai, Chennai, Kolkata) and Christians/Parsis nationwide, the executor must obtain Probate from the High Court. For most Hindus in other states, no probate is needed — the Will is directly acted upon."
        ],
        "documents": [
            {"name": "Identity Proof of Testator (Aadhaar / PAN)", "mandatory": True, "purpose": "Testator identity for registered Will"},
            {"name": "Property Documents (title deeds, bank passbooks)", "mandatory": False, "purpose": "Schedule of assets described in Will"},
            {"name": "Identity of 2 Witnesses (Aadhaar)", "mandatory": True, "purpose": "Attestation requirement for registration"}
        ]
    },
    "wrongful_termination": {
        "patterns": ["wrongful termination", "wrongly terminated", "illegal dismissal", "government job termination",
                     "naukri se nikala", "job terminated", "sacked wrongly", "industrial dispute",
                     "reinstatement", "service matter", "central administrative tribunal",
                     "नौकरी से निकाला", "सेवा विवाद"],
        "title": "Wrongful Termination / Illegal Dismissal from Government or Private Job",
        "department": "Central Administrative Tribunal (CAT) / State Administrative Tribunal / Labour Court / Industrial Tribunal",
        "portal_name": "Central Administrative Tribunal / National Industrial Tribunal",
        "portal_url": "https://www.cat.nic.in",
        "act_name": "Industrial Disputes Act, 1947 / Central Civil Services (Classification, Control & Appeal) Rules, 1965 / Constitution Article 311",
        "sla_days": 90,
        "fee": "₹50 - ₹500 filing fee depending on the forum",
        "summary": "No government or private sector employee can be dismissed without following due process. Government employees have Constitutional protection under Article 311. Private sector employees are protected under Industrial Disputes Act (ID Act) 1947.",
        "steps": [
            "GOVERNMENT JOB: Under Article 311 of the Constitution, no government employee can be dismissed without: (1) a Charge Sheet with specific allegations, (2) opportunity to show cause, (3) an inquiry by a competent officer. Dismissal without this process is unconstitutional.",
            "File a Representation/Appeal to the next higher authority within the service rules timeline (typically 30-90 days from dismissal order).",
            "GOVERNMENT EMPLOYEE: If internal appeals fail, approach the Central Administrative Tribunal (CAT) for central govt employees or State Administrative Tribunal (SAT) within 1 year of dismissal.",
            "PRIVATE SECTOR EMPLOYEE (workman): Under Industrial Disputes Act, a 'workman' (non-managerial, salary below ₹10,000 basic) can raise an industrial dispute with the Labour Commissioner within 3 years. The Labour Court can order reinstatement with back wages.",
            "PRIVATE SECTOR SENIOR/MANAGERIAL: Approach a Civil Court for damages, or file a complaint under Payment of Gratuity Act / EPF Act if those statutory dues were withheld.",
            "EVIDENCE to PRESERVE: Appointment letter, pay slips, charge sheet (if any), show cause notice, dismissal order, service records, performance appraisals, any correspondence with management.",
            "LEGAL AID: Approach the District Legal Services Authority (DLSA) for free legal representation if your income is below the threshold."
        ],
        "documents": [
            {"name": "Appointment Letter & Service Records", "mandatory": True, "purpose": "Proof of employment and terms of service"},
            {"name": "Dismissal / Termination Order Copy", "mandatory": True, "purpose": "Subject matter of the legal challenge"},
            {"name": "Charge Sheet / Show Cause Notice (if any)", "mandatory": False, "purpose": "Evidence of procedure followed or violated"},
            {"name": "Salary Slips (last 6 months)", "mandatory": True, "purpose": "Establishing nature of employment and salary"}
        ]
    },
    "caste_ews": {
        "patterns": ["ews certificate", "obc certificate", "non creamy layer", "sc st certificate", "caste certificate rules", "jati praman", "obc ncl"],
        "title": "Caste (SC/ST/OBC Non-Creamy Layer) & EWS Certificate Standards",
        "department": "Revenue Department (राजस्व विभाग) / Sub-Divisional Magistrate (SDM) / Tehsildar",
        "portal_name": "State e-District Portal / ServicePlus",
        "portal_url": "https://services.india.gov.in",
        "act_name": "State Caste Certificate Rules & 103rd Constitutional Amendment (EWS)",
        "sla_days": 15,
        "fee": "₹15 to ₹30 statutory fee",
        "summary": "Statutory certificates required to claim constitutional reservation in central/state government employment and admissions.",
        "steps": [
            "Log in to your State e-District portal (e.g. edistrict.up.gov.in, RTPS Bihar, Aaple Sarkar).",
            "Select 'Application for Caste Certificate' (specify SC, ST, or OBC) or 'Economically Weaker Section (EWS) Certificate'.",
            "For OBC Non-Creamy Layer: Family gross annual income from non-agricultural sources must be below ₹8 Lakh for past 3 consecutive years.",
            "For EWS: Family annual income below ₹8 Lakh; agricultural land under 5 acres; residential flat under 1000 sq ft.",
            "Attach self-declaration, legacy caste proof (father's or grandfather's certificate), and income certificate.",
            "Area Lekhpal / Patwari conducts inquiry; Tehsildar/SDM issues digitally verifiable certificate within 15 working days."
        ],
        "documents": [
            {"name": "Applicant & Father Aadhaar Card", "mandatory": True, "purpose": "Identity and family linkage"},
            {"name": "Father / Paternal Relative Caste Certificate", "mandatory": True, "purpose": "Ancestral lineage evidence"},
            {"name": "Income Certificate from Tehsildar", "mandatory": True, "purpose": "Creamy layer / EWS ceiling compliance"}
        ]
    }
}


def answer_domain_query(query: str, state: Optional[str] = None, language: str = "English") -> Dict[str, Any]:
    """
    Primary Unified Domain Intelligence Service.
    Resolves ANY query originating in the citizen service / public welfare domain.
    """
    clean_q = query.strip()
    norm = clean_q.lower()

    # Step 1: Detect matching topic in EXTENDED_CIVIC_KB for immediate grounded accuracy
    for topic, kb in EXTENDED_CIVIC_KB.items():
        matched = False
        for pat in kb["patterns"]:
            if re.search(r'\b' + re.escape(pat) + r'\b', norm):
                matched = True
                break
        if matched:
            state_label = state if state else "All India / State Jurisdiction"
            steps_text = "\n".join([f"{idx+1}. {step}" for idx, step in enumerate(kb["steps"])])
            docs_text = "\n".join([f"• **{doc['name']}** ({'Mandatory' if doc['mandatory'] else 'Optional'}): {doc['purpose']}" for doc in kb["documents"]])

            reply = (
                f"### {kb['title']}\n\n"
                f"{kb['summary']}\n\n"
                f"**Governing Law / Act**: {kb['act_name']}\n"
                f"**Competent Authority**: {kb['department']}\n"
                f"**Official Portal**: [{kb['portal_name']}]({kb['portal_url']})\n"
                f"**Statutory Resolution Timeline**: **{kb['sla_days']} Days**\n"
                f"**Statutory Fee**: {kb['fee']}\n\n"
                f"#### Step-by-Step Procedure ({state_label}):\n{steps_text}\n\n"
                f"#### Key Documents & Evidence Checklist:\n{docs_text}\n\n"
                f"> **Citizen Advisory**: Under Indian administrative law, you are legally entitled to receive official written reasons if any public authority delays or rejects your application."
            )

            structured_guide = {
                "title": kb["title"],
                "department": kb["department"],
                "portal_name": kb["portal_name"],
                "portal_url": kb["portal_url"],
                "sla_days": f"{kb['sla_days']} Days",
                "fee": kb["fee"],
                "steps": kb["steps"],
                "documents": kb["documents"]
            }

            return {
                "response": reply,
                "structured_guide": structured_guide,
                "provider": "grounded_civic_kb"
            }

    # Step 2: Attempt OpenAI ChatGPT (Tier 1) if OPENAI_API_KEY is present
    openai_client = get_openai_client()
    if openai_client is not None:
        try:
            state_ctx = f"The citizen resides in or asks specifically about {state}." if state else "Provide the applicable state/central rules."
            sys_prompt = (
                "You are the Lead Citizen Rights & Government Procedure Specialist for VachanSetu, an official Indian public service platform.\n"
                "Your objective is to provide an authoritative, accurate, step-by-step procedural guide for ANY civic, administrative, or legal service query.\n"
                "Structure your response with:\n"
                "1. Clear Summary & Statutory Basis (Name of relevant Act / Scheme / Regulation)\n"
                "2. Responsible Government Department & Official Portal (Provide direct valid government URLs like .gov.in or .nic.in)\n"
                "3. Step-by-Step Application or Remedy Procedure (Numbered, chronological steps)\n"
                "4. Required Documents Checklist (Categorized by mandatory and optional)\n"
                "5. Statutory Timelines (SLA), Fees & Citizen Appeals / Grievance Rights (RTSA / RTI / Appellate Authority)\n"
                "Tone: Authoritative, dignified, supportive, and completely free of irrelevant promotional schemes."
            )
            completion = openai_client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": f"Citizen Query: {clean_q}\n{state_ctx}\nLanguage: {language}"}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            ans = completion.choices[0].message.content
            if ans and len(ans.strip()) > 50:
                return {
                    "response": ans.strip(),
                    "structured_guide": None,
                    "provider": "openai_chatgpt"
                }
        except Exception as e:
            logger.warning(f"OpenAI ChatGPT call encountered error, falling back to Sarvam: {e}")

    # Step 3: Attempt Sarvam-105B (Tier 2)
    try:
        state_ctx = f"The citizen specifically inquired about {state}." if state else "Provide general Indian and state-specific statutory guidance."
        prompt = (
            f"Citizen Query: '{clean_q}'\n"
            f"{state_ctx}\n"
            f"Language: {language}\n\n"
            "You are the official VachanSetu Citizen Rights Specialist. Explain the exact government process in clear, well-formatted Markdown:\n"
            "1. Procedural Overview & Relevant Act/Law\n"
            "2. Government Department & Official Portal (e.g. state e-District, ServicePlus, or Central Portal)\n"
            "3. Step-by-Step Practical Procedure\n"
            "4. Required Documents Checklist\n"
            "5. Statutory Deadlines (SLA) & Appeals if delayed or rejected\n\n"
            "Do NOT recommend unrelated welfare schemes unless directly asked."
        )
        ai_resp = sarvam_client.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are VachanSetu, a trusted, factual Indian citizen rights assistant. Be source-grounded and structured.",
            temperature=0.3,
            max_tokens=1200
        )
        if ai_resp and len(ai_resp.strip()) > 50:
            return {
                "response": ai_resp.strip(),
                "structured_guide": None,
                "provider": "sarvam_ai"
            }
    except Exception as e:
        logger.warning(f"Sarvam call failed: {e}")

    # Step 4: Robust Universal Synthesizer (Tier 3 Zero-Failure Fallback)
    state_str = state if state else "your State / Central Department"
    fallback_resp = (
        f"### Citizen Guidance: {clean_q.capitalize()}\n\n"
        f"To process your request regarding **'{clean_q}'** in {state_str}, follow the standard Indian statutory procedure:\n\n"
        f"1. **Official Jurisdiction & Portal**:\n"
        f"   • Visit your official State e-District portal or the National Citizen Services Gateway ([services.india.gov.in](https://services.india.gov.in)).\n"
        f"   • For Central Government matters, visit [pgportal.gov.in](https://pgportal.gov.in) (CPGRAMS).\n\n"
        f"2. **Step-by-Step Procedure**:\n"
        f"   • **Step 1**: Register on the designated citizen portal or visit your nearest Common Service Center (CSC) / Jan Seva Kendra.\n"
        f"   • **Step 2**: Fill in the prescribed application or grievance form with your personal and Aadhaar details.\n"
        f"   • **Step 3**: Upload verified supporting documentation (identity proof, address proof, and relevant affidavits).\n"
        f"   • **Step 4**: Pay statutory application fees (if applicable) and note the generated Application Reference Number.\n"
        f"   • **Step 5**: Track file movement online; competent authorities must dispose of the application within statutory Right to Public Services Act (RTSA) limits.\n\n"
        f"3. **Statutory Documents Checklist**:\n"
        f"   • **Aadhaar Card / Photo Identity Proof** (Mandatory)\n"
        f"   • **Proof of Address / Domicile Certificate** (Mandatory for territorial jurisdiction)\n"
        f"   • **Specific Transaction Record / Affidavit / Bill** related to your query.\n\n"
        f"4. **Citizen Legal Remedy for Delay**:\n"
        f"   • If public authorities fail to respond within the published SLA, you can file a First Appeal under the **Right to Public Services Act** or submit a formal Section 6(1) query under the **RTI Act 2005**."
    )

    return {
        "response": fallback_resp,
        "structured_guide": None,
        "provider": "universal_synthesizer"
    }
