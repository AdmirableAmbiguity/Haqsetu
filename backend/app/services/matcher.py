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
        """Matches citizen need to schemes with scoring, criteria checks, and rationale."""
        extracted = self.extract_profile_rules(query)
        profile = {**extracted, **(user_profile or {})}

        schemes = registry.get_all_schemes()
        results = []
        tokens = set(re.findall(r'\w+', query.lower()))

        for s in schemes:
            name = s.get("name", "").lower()
            desc = s.get("eligibility_summary", "").lower()
            dept = s.get("department", "").lower()
            tags = [t.lower() for t in s.get("tags", [])]

            score = 0
            # Token match
            matched_words = tokens.intersection(set(re.findall(r'\w+', f"{name} {desc} {dept} {' '.join(tags)}")))
            score += len(matched_words) * 12

            # Domain bonuses
            if "scholarship" in tokens and "scholarship" in name:
                score += 50
            if "income" in tokens and "income" in name:
                score += 50
            if "ration" in tokens and "ration" in name:
                score += 50
            if "pension" in tokens and "pension" in name:
                score += 50
            if "kisan" in tokens and ("kisan" in name or "farmer" in desc):
                score += 50

            criteria_met = []
            criteria_unmet = []
            criteria_unknown = []

            # Check criteria
            if "annual_income" in profile:
                max_income = s.get("max_income")
                if max_income:
                    if profile["annual_income"] <= max_income:
                        criteria_met.append(f"Income ₹{profile['annual_income']:,} is within limit of ₹{max_income:,}")
                        score += 20
                    else:
                        criteria_unmet.append(f"Income ₹{profile['annual_income']:,} exceeds limit of ₹{max_income:,}")
                        score -= 30
            else:
                if s.get("max_income"):
                    criteria_unknown.append(f"Annual household income (limit: ₹{s['max_income']:,})")

            if "category" in profile:
                allowed_cats = s.get("allowed_categories", [])
                if allowed_cats:
                    if profile["category"] in allowed_cats:
                        criteria_met.append(f"Social category {profile['category']} qualifies")
                        score += 15
                    else:
                        criteria_unmet.append(f"Social category {profile['category']} not covered")
                        score -= 20
            else:
                if s.get("allowed_categories"):
                    criteria_unknown.append(f"Social category (Target: {', '.join(s['allowed_categories'])})")

            if "occupation" in profile:
                req_occ = s.get("target_occupation")
                if req_occ:
                    if profile["occupation"].lower() == req_occ.lower():
                        criteria_met.append(f"Occupation '{profile['occupation']}' directly aligns")
                        score += 25
                    else:
                        criteria_unmet.append(f"Requires occupation: {req_occ}")

            if "state" in profile:
                s_state = s.get("state")
                if s_state and s_state != "All India" and s_state != "Central":
                    if profile["state"].lower() == s_state.lower():
                        criteria_met.append(f"Domicile matches {s_state}")
                        score += 20
                    else:
                        criteria_unmet.append(f"Specific to {s_state}; citizen state is {profile['state']}")
                        score -= 40

            # Signal determination
            if criteria_unmet:
                signal = "likely_not_eligible"
            elif len(criteria_met) >= 2 and len(criteria_unknown) == 0:
                signal = "likely_eligible"
            elif criteria_unknown:
                signal = "needs_clarification"
            else:
                signal = "possibly_eligible"

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
                "verification_state": s.get("verification_state", "needs_review"),
                "source_basis": s.get("source_basis", "State citizen service charter"),
                "time_limit_days": s.get("time_limit_days", 15),
                "is_statutory": s.get("is_statutory", False),
                "fee": s.get("fee", 0),
                "summary": s.get("eligibility_summary", "")
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        top_matches = results[:4]

        # Generate follow-up questions
        follow_ups = []
        if "annual_income" not in profile:
            follow_ups.append("What is your approximate total annual family income?")
        if "category" not in profile:
            follow_ups.append("Which social category do you belong to (General, OBC, SC, ST, EWS)?")
        if "state" not in profile:
            follow_ups.append("Which Indian State / UT do you reside in?")

        # AI enhancement via Sarvam-105B (if requested & key available)
        ai_rationale = ""
        if use_ai and top_matches:
            try:
                top = top_matches[0]
                prompt = (
                    f"Citizen asked: '{query}'\n"
                    f"Top matched scheme: {top['name']} ({top['department']}).\n"
                    f"Criteria met: {top['criteria_met']}\n"
                    f"Criteria unknown: {top['criteria_unknown']}\n"
                    f"Signal: {top['signal']}\n"
                    "Provide a warm, reassuring 2-sentence explanation in simple English and Hindi "
                    "clarifying why this scheme fits and what they should verify first."
                )
                ai_rationale = sarvam_client.chat(
                    messages=[{"role": "user", "content": prompt}],
                    system_prompt="You are HaqGuide, an empathetic citizen assistance AI. Always be concise and honest.",
                    temperature=0.3,
                    max_tokens=256
                )
            except Exception as e:
                ai_rationale = f"Based on your query, {top_matches[0]['name']} is the primary matching public service."

        # Detect scheme combinations (e.g. Income Certificate + UP Scholarship)
        combinations = []
        top_ids = [m["name"].lower() for m in top_matches]
        if any("scholarship" in n for n in top_ids) and any("income" in n for n in top_ids):
            combinations.append({
                "combination_name": "Scholarship + Income Certificate Prerequisite Bundle",
                "reason": "An Income Certificate is mandatory before your scholarship application can be processed.",
                "step_order": ["Apply for Income Certificate (7-15 days)", "Apply for Post-Matric Scholarship with Income Ref"]
            })

        return {
            "query": query,
            "parsed_profile": profile,
            "matches": top_matches,
            "follow_up_questions": follow_ups[:3],
            "ai_rationale": ai_rationale,
            "combinations": combinations,
            "data_origin": "ai_inferred"
        }

matcher = EligibilityMatcher()
