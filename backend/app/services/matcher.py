import re
from typing import Dict, List, Any
from backend.app.services.registry import registry
from ai_engine import sarvam_client

class EligibilityMatcher:
    def __init__(self):
        pass

    def extract_profile_rules(self, query: str) -> Dict[str, Any]:
        """Deterministic profile extraction from text using regex/keywords."""
        profile = {}
        query_lower = query.lower()

        # Age detection
        age_match = re.search(r'\b(?:age|years old|saal|umar|varsh)\s*[:=]?\s*(\d{1,2})\b', query_lower)
        if not age_match:
            age_match = re.search(r'\b(\d{1,2})\s*(?:years old|saal|varsh|yr)\b', query_lower)
        if age_match:
            profile["age"] = int(age_match.group(1))

        # Income detection
        income_match = re.search(r'(?:income|aay|salary|earning|kamata)\s*[:=]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|k|thousand|hazar)?', query_lower)
        if not income_match:
            income_match = re.search(r'([\d,]+(?:\.\d+)?)\s*(lakh|k|thousand|hazar)\s*(?:income|aay|salary)', query_lower)
        
        if income_match:
            num = float(income_match.group(1).replace(",", ""))
            unit = income_match.group(2)
            if unit in ["lakh", "lac"]:
                annual_income = int(num * 100000)
            elif unit in ["k", "thousand", "hazar"]:
                annual_income = int(num * 1000)
            else:
                annual_income = int(num)
            profile["annual_income"] = annual_income

        # Category
        if re.search(r'\b(sc|scheduled caste|dalit)\b', query_lower):
            profile["category"] = "SC"
        elif re.search(r'\b(st|scheduled tribe|adivasi)\b', query_lower):
            profile["category"] = "ST"
        elif re.search(r'\b(obc|other backward class|pichhda)\b', query_lower):
            profile["category"] = "OBC"
        elif re.search(r'\b(ews|economically weaker section)\b', query_lower):
            profile["category"] = "EWS"
        elif re.search(r'\b(general|samanya)\b', query_lower):
            profile["category"] = "General"

        # Gender
        if re.search(r'\b(female|woman|girl|mahila|aurat|beti)\b', query_lower):
            profile["gender"] = "Female"
        elif re.search(r'\b(male|man|boy|purush|ladka|beta)\b', query_lower):
            profile["gender"] = "Male"

        # Occupation / Role
        if re.search(r'\b(student|chhatra|padhai|college|school|vidyarthi|scholarship)\b', query_lower):
            profile["occupation"] = "Student"
        elif re.search(r'\b(farmer|kisan|kheti|krishi)\b', query_lower):
            profile["occupation"] = "Farmer"
        elif re.search(r'\b(artisan|weaver|karigar|bunkaar|vishwakarma)\b', query_lower):
            profile["occupation"] = "Artisan"
        elif re.search(r'\b(laborer|mazdoor|daily wage|shramik)\b', query_lower):
            profile["occupation"] = "Laborer"

        # State detection
        states = [
            "uttar pradesh", "bihar", "maharashtra", "rajasthan", "madhya pradesh", 
            "delhi", "haryana", "punjab", "karnataka", "tamil nadu", "west bengal", 
            "gujarat", "odisha", "jharkhand", "assam", "telangana", "kerala"
        ]
        for st in states:
            if st in query_lower:
                profile["state"] = st.title()
                break
        if "up" in query_lower.split():
            profile["state"] = "Uttar Pradesh"
        elif "mp" in query_lower.split():
            profile["state"] = "Madhya Pradesh"

        return profile

    def match(self, query: str, user_profile: Dict[str, Any] = None, use_ai: bool = True) -> Dict[str, Any]:
        """Matches citizen need to schemes using intelligent routing and intent classification."""
        from ai_engine.query_router import query_router

        route_res = query_router.route(query=query, profile_override=user_profile)

        # Detect scheme combinations (e.g. Income Certificate + UP Scholarship) if matches present
        combinations = []
        top_matches = route_res.get("matches", [])
        top_ids = [m["name"].lower() for m in top_matches]
        if any("scholarship" in n for n in top_ids) and any("income" in n for n in top_ids):
            combinations.append({
                "combination_name": "Scholarship + Income Certificate Prerequisite Bundle",
                "reason": "An Income Certificate is mandatory before your scholarship application can be processed.",
                "step_order": ["Apply for Income Certificate (7-15 days)", "Apply for Post-Matric Scholarship with Income Ref"]
            })

        return {
            "query": query,
            "section": route_res.get("section", "haqguide"),
            "intent": route_res.get("intent", "GENERAL_GOVERNMENT_QUERY"),
            "response": route_res.get("response", ""),
            "ai_rationale": route_res.get("response", ""),
            "parsed_profile": route_res.get("parsed_profile", user_profile or {}),
            "matches": top_matches,
            "structured_guide": route_res.get("structured_guide"),
            "active_scheme": route_res.get("active_scheme"),
            "required_documents": route_res.get("required_documents"),
            "follow_up_questions": route_res.get("follow_ups", []),
            "combinations": combinations,
            "data_origin": "ai_inferred"
        }

matcher = EligibilityMatcher()
