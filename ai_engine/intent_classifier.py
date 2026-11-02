"""
Intent Classifier for HaqSetu / Vachan Setu.
Accurately categorizes citizen inquiries into distinct intents:
- GENERAL_GOVERNMENT_QUERY
- CERTIFICATE_APPLICATION
- GOVERNMENT_SERVICE_QUERY
- SCHEME_DISCOVERY
- SCHEME_SPECIFIC_QUERY
- APPLICATION_STATUS
- GRIEVANCE_QUERY
- CONVERSATIONAL
- OUT_OF_DOMAIN
"""

import re
import json
import logging
from typing import Dict, Any, Optional
from ai_engine import sarvam_client

logger = logging.getLogger(__name__)

# Known Schemes for fast resolution
KNOWN_SCHEMES = {
    "pm-kisan": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
    "pm kisan": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
    "kisan samman": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
    "ayushman": "Ayushman Bharat PM-JAY (Golden Card)",
    "pm-jay": "Ayushman Bharat PM-JAY (Golden Card)",
    "pmjay": "Ayushman Bharat PM-JAY (Golden Card)",
    "golden card": "Ayushman Bharat PM-JAY (Golden Card)",
    "pmay": "PMAY-Gramin (Pradhan Mantri Awas Yojana)",
    "awas yojana": "PMAY-Gramin (Pradhan Mantri Awas Yojana)",
    "old age pension": "NSAP - Indira Gandhi National Old Age Pension",
    "vridha pension": "NSAP - Indira Gandhi National Old Age Pension",
    "post-matric": "National Scholarship Portal (Pre/Post-Matric Scholarship)",
    "post matric": "National Scholarship Portal (Pre/Post-Matric Scholarship)",
    "pre-matric": "National Scholarship Portal (Pre/Post-Matric Scholarship)",
    "nsp": "National Scholarship Portal (Pre/Post-Matric Scholarship)",
    "up scholarship": "National Scholarship Portal (Pre/Post-Matric Scholarship)",
    "pmmvy": "PM Matru Vandana Yojana (PMMVY)",
    "matru vandana": "PM Matru Vandana Yojana (PMMVY)",
    "ujjwala": "PM Ujjwala Yojana (PMUY)",
    "pmuy": "PM Ujjwala Yojana (PMUY)",
    "gas cylinder": "PM Ujjwala Yojana (PMUY)",
    "mgnrega": "MGNREGA (Mahatma Gandhi National Rural Employment Guarantee)",
    "nrega": "MGNREGA (Mahatma Gandhi National Rural Employment Guarantee)",
    "sukanya": "Sukanya Samriddhi Yojana",
    "ssy": "Sukanya Samriddhi Yojana",
    "vishwakarma": "PM Vishwakarma Scheme",
    "pm vishwakarma": "PM Vishwakarma Scheme",
    "stand-up india": "Stand-Up India Scheme",
    "stand up india": "Stand-Up India Scheme",
    "atal pension": "Atal Pension Yojana (APY)",
    "apy": "Atal Pension Yojana (APY)"
}

# Known Certificate Types
CERTIFICATE_TYPES = [
    "domicile", "niwas", "residence", "resident",
    "income", "aay", "income certificate",
    "caste", "jati", "obc certificate", "sc certificate", "st certificate", "ews certificate",
    "birth", "janam", "death", "mrityu",
    "character", "charitra", "disability", "divyang",
    "succession", "varisana", "khatauni"
]

class IntentClassifier:
    """Classifies user queries semantically using rule-heuristics + Sarvam-105B."""

    def classify_deterministic(self, query: str) -> Optional[Dict[str, Any]]:
        """Fast pattern-based intent identification to guarantee 100% precision on common cases."""
        q = query.strip().lower()

        # 1. Greetings & Conversational
        greeting_patterns = [
            r'^(hi|hello|hey|namaste|pranam|good\s*(morning|afternoon|evening|day)|kaise\s*ho|how\s*are\s*you)[\s!.,?]*$',
            r'^(hello|hi|hey)[\s,]+(how\s*are\s*you|kaise\s*ho)[\s!.,?]*$',
            r'^(who\s*are\s*you|what\s*can\s*you\s*do|what\s*is\s*haqsetu|tell\s*me\s*about\s*yourself)[\s!.,?]*$',
            r'^(thanks|thank\s*you|dhanyawad|shukriya)[\s!.,?]*$'
        ]
        for pat in greeting_patterns:
            if re.match(pat, q, re.IGNORECASE):
                return {
                    "intent": "CONVERSATIONAL",
                    "confidence": 0.99,
                    "entities": {"type": "greeting"},
                    "requires_scheme_discovery": False
                }

        # 2. General broad certificate intent (needs clarification)
        if re.match(r'^(i\s*want\s*to\s*apply\s*for\s*(a\s*)?certificate|certificate\s*apply\s*karna\s*hai|apply\s*certificate)[\s!.,?]*$', q):
            return {
                "intent": "CERTIFICATE_APPLICATION",
                "confidence": 0.95,
                "entities": {"certificate": None, "state": None},
                "requires_scheme_discovery": False,
                "requires_clarification": True,
                "clarification_prompt": "Which specific certificate would you like to apply for (e.g., Domicile, Income, Caste, Birth) and in which State?"
            }

        # 3. Certificate Difference / Comparison Questions
        if ("difference between" in q or "kya antar hai" in q or "vs" in q) and any(c in q for c in CERTIFICATE_TYPES):
            return {
                "intent": "GENERAL_GOVERNMENT_QUERY",
                "confidence": 0.98,
                "entities": {"sub_type": "comparison"},
                "requires_scheme_discovery": False
            }

        # 4. Specific Certificate Inquiries
        for cert in CERTIFICATE_TYPES:
            if cert in q:
                # If query is explicitly asking to find scholarships/schemes with an income cert, route to scheme discovery
                if ("scholarship" in q or "yojana" in q or "scheme" in q or "find" in q) and any(kw in q for kw in ["find", "search", "eligible", "which scholarship", "what scholarship"]):
                    break  # Let it fall to Scheme Discovery

                state = self._extract_state(q)
                return {
                    "intent": "CERTIFICATE_APPLICATION",
                    "confidence": 0.95,
                    "entities": {
                        "certificate": cert,
                        "state": state
                    },
                    "requires_scheme_discovery": False
                }

        # 5. Aadhaar, Voter, Passport, Driving License, Ration Card Procedures
        govt_services = {
            "aadhaar": ["aadhaar", "aadhar", "uidai", "aadhaar card", "update mobile"],
            "ration_card": ["ration card", "rashan card", "ration", "fcs"],
            "voter_id": ["voter id", "epic", "voter card", "nvsp", "eci"],
            "driving_license": ["driving license", "dl", "driving licence", "sarathi", "parivahan", "learning license"],
            "passport": ["passport", "passport seva", "tatkaal passport"]
        }
        for s_type, keywords in govt_services.items():
            if any(k in q for k in keywords):
                if not any(sw in q for sw in ["scheme", "yojana", "find scholarship", "subsidy"]):
                    return {
                        "intent": "GOVERNMENT_SERVICE_QUERY",
                        "confidence": 0.95,
                        "entities": {"service": s_type, "state": self._extract_state(q)},
                        "requires_scheme_discovery": False
                    }

        # 6. Application Status / Delay / Grievance / RTI
        status_keywords = [
            "pending for", "pending since", "not received yet", "rejected without reason",
            "statutory limit", "rtsa", "right to service", "file rti", "rti application",
            "complaint against", "delay in application", "status check", "application track",
            "din ho gaye", "kab tak aayega", "reject ho gaya"
        ]
        if any(sk in q for sk in status_keywords):
            return {
                "intent": "APPLICATION_STATUS",
                "confidence": 0.95,
                "entities": {"status_query": True},
                "requires_scheme_discovery": False
            }

        # 7. Alternatives for a specific scheme
        if "alternative" in q or "alternatives" in q or "not eligible for" in q or "ineligible for" in q:
            matched_scheme = None
            for key, fullname in KNOWN_SCHEMES.items():
                if key in q:
                    matched_scheme = fullname
                    break
            return {
                "intent": "SCHEME_DISCOVERY",
                "confidence": 0.92,
                "entities": {"mode": "alternatives", "disqualified_scheme": matched_scheme or "specified scheme"},
                "requires_scheme_discovery": True
            }

        # 8. Specific Scheme Deep Dive (Scheme Expert)
        for key, fullname in KNOWN_SCHEMES.items():
            if key in q:
                # If citizen is explicitly asking to explain or query a known scheme:
                if any(kw in q for kw in [
                    "explain", "what is", "about", "details", "documents for", "documents required",
                    "landholding", "land limit", "eligibility for", "who can apply for", "validity",
                    "rules", "benefits of", "kya hai", "kaise milega", "patrata"
                ]) or len(q.split()) <= 4:
                    return {
                        "intent": "SCHEME_SPECIFIC_QUERY",
                        "confidence": 0.95,
                        "entities": {"scheme_name": fullname, "scheme_key": key},
                        "requires_scheme_discovery": False
                    }

        # 9. Scheme Discovery & Search
        discovery_keywords = [
            "find scholarship", "what scholarship", "which scholarship", "scholarships can i apply",
            "find schemes", "which scheme", "what scheme", "government benefits", "subsidies",
            "subsidy", "schemes for", "benefits for farmers", "scholarship for", "schemes available"
        ]
        if any(dk in q for dk in discovery_keywords) or ("scholarship" in q and ("student" in q or "income" in q)):
            return {
                "intent": "SCHEME_DISCOVERY",
                "confidence": 0.95,
                "entities": {"query": query},
                "requires_scheme_discovery": True
            }

        return None

    def _extract_state(self, q: str) -> Optional[str]:
        states = [
            ("uttar pradesh", "Uttar Pradesh"), ("up", "Uttar Pradesh"),
            ("bihar", "Bihar"), ("madhya pradesh", "Madhya Pradesh"), ("mp", "Madhya Pradesh"),
            ("rajasthan", "Rajasthan"), ("maharashtra", "Maharashtra"), ("delhi", "Delhi"),
            ("haryana", "Haryana"), ("punjab", "Punjab"), ("gujarat", "Gujarat"),
            ("karnataka", "Karnataka"), ("tamil nadu", "Tamil Nadu"), ("west bengal", "West Bengal")
        ]
        for key, state_name in states:
            # Word boundary check
            if re.search(r'\b' + re.escape(key) + r'\b', q):
                return state_name
        return None

    def classify(self, query: str) -> Dict[str, Any]:
        """Classifies intent using deterministic engine first; falls back to Sarvam-105B."""
        det_res = self.classify_deterministic(query)
        if det_res:
            return det_res

        # LLM-based classification via Sarvam-105B
        try:
            prompt = (
                f"You are the Intent Classification Engine for HaqSetu (Indian Citizen Service Platform).\n"
                f"Classify the following citizen query:\n"
                f"Query: \"{query}\"\n\n"
                f"Categories:\n"
                f"- GENERAL_GOVERNMENT_QUERY (general civic guidance, difference between certificates, governance laws)\n"
                f"- CERTIFICATE_APPLICATION (domicile, caste, income, birth, death certificate procedures)\n"
                f"- GOVERNMENT_SERVICE_QUERY (Aadhaar update, Ration Card, Voter ID, Driving License)\n"
                f"- SCHEME_DISCOVERY (citizen seeking scholarships, subsidies, loans or welfare schemes to apply for)\n"
                f"- SCHEME_SPECIFIC_QUERY (in-depth questions about ONE specific named scheme like PM-KISAN, NSP, etc.)\n"
                f"- APPLICATION_STATUS (checking status, SLA breach, delay complaint, RTI)\n"
                f"- CONVERSATIONAL (greetings, pleasantries, who are you)\n"
                f"- OUT_OF_DOMAIN (unrelated non-governance questions)\n\n"
                f"Return ONLY valid JSON in this exact structure:\n"
                f"{{\n"
                f'  "intent": "ONE_CATEGORY_ABOVE",\n'
                f'  "confidence": 0.9,\n'
                f'  "entities": {{"service": null, "state": null, "scheme_name": null}},\n'
                f'  "requires_scheme_discovery": false,\n'
                f'  "requires_clarification": false\n'
                f"}}"
            )

            raw = sarvam_client.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a strict, precise JSON classifier. Return only valid JSON.",
                temperature=0.1,
                max_tokens=256
            )

            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                intent = parsed.get("intent", "GENERAL_GOVERNMENT_QUERY")
                # Safety check: do not trigger scheme discovery unless intent is SCHEME_DISCOVERY
                requires_discovery = (intent == "SCHEME_DISCOVERY")
                parsed["requires_scheme_discovery"] = requires_discovery
                return parsed

        except Exception as e:
            logger.warning(f"Sarvam intent classification error: {e}")

        # Safe fallback: treat as GENERAL_GOVERNMENT_QUERY without schemes
        return {
            "intent": "GENERAL_GOVERNMENT_QUERY",
            "confidence": 0.70,
            "entities": {"query": query},
            "requires_scheme_discovery": False
        }


intent_classifier = IntentClassifier()
