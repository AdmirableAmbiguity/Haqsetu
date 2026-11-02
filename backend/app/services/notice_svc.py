from typing import Dict, Any, Optional
import re
from ai_engine.notice_decoder import decode_notice, draft_response_letter
from ai_engine import sarvam_client

class NoticeService:
    def decode_rejection_notice(self, notice_text: str, service_name: str = "Income Certificate", language: str = "Hindi") -> Dict[str, Any]:
        """Decodes an official rejection or deficiency memo using Sarvam-105B."""
        try:
            decoded = decode_notice(notice_text=notice_text, service_name=service_name)
        except Exception:
            decoded = {
                "notice_type": "return",
                "explanation_english": "Administrative return memo regarding submitted application.",
                "stated_reasons": ["Incomplete or mismatching documentation noted by examining officer."],
                "confidence": "low"
            }

        # Extract reasons and details safely
        stated_reasons = decoded.get("stated_reasons") or decoded.get("reasons") or []
        if isinstance(stated_reasons, str):
            stated_reasons = [stated_reasons]
        
        # Try extracting applicant and reference number from text or decoded
        applicant_name = decoded.get("applicant_name")
        if not applicant_name:
            match_name = re.search(r"To:\s*(?:Shri|Smt|Ms|Mr)?\.?\s*([A-Za-z\s]+?)(?:,|$|\n)", notice_text)
            applicant_name = match_name.group(1).strip() if match_name else "Applicant"

        app_ref = decoded.get("reference_number") or decoded.get("application_ref")
        if not app_ref:
            match_ref = re.search(r"(?:Ref|Application No|Ref No)[:\s]+([A-Za-z0-9\/\-_]+)", notice_text, re.IGNORECASE)
            app_ref = match_ref.group(1).strip() if match_ref else "APP/REF/2026/01"

        # Plain language explanation in chosen language
        explanation = decoded.get("explanation_hindi") if language.lower() == "hindi" and decoded.get("explanation_hindi") else decoded.get("explanation_english", "")
        if not explanation:
            try:
                explanation = sarvam_client.explain_in_simple_language(
                    text=f"Official Notice states: {notice_text}\nReasons: {stated_reasons}",
                    language=language
                )
            except Exception:
                explanation = f"आपकी {service_name} की अर्जी को निम्नलिखित कारणों से वापस/आपत्ति दर्ज की गई है: {', '.join(stated_reasons)}।" if language.lower() == "hindi" else f"Your application for {service_name} was returned due to: {', '.join(stated_reasons)}."

        # Draft response letter
        try:
            response_letter = draft_response_letter(
                notice_text=notice_text,
                applicant_name=applicant_name,
                application_ref=app_ref,
                service_name=service_name
            )
        except Exception:
            response_letter = (
                f"DRAFT RECTIFICATION LETTER - PLEASE REVIEW BEFORE SUBMITTING\n\n"
                f"To,\nThe Competent Authority / Tehsildar,\nDepartment of Public Services\n\n"
                f"Subject: Resubmission & Rectification for Application Ref: {app_ref} ({service_name})\n\n"
                f"Respected Sir/Madam,\n\n"
                f"I, {applicant_name}, submit this response regarding the objection memo dated for application {app_ref}.\n"
                f"I have addressed the concerns raised and attached the necessary supporting documents for review.\n\n"
                f"Kindly process and approve the certificate.\n\n"
                f"Sincerely,\n{applicant_name}\nContact: +91-XXXXXXXXXX"
            )

        return {
            "notice_summary": decoded,
            "plain_language_explanation": explanation,
            "draft_response_letter": response_letter,
            "remedial_steps": [
                "1. Gather the specific missing or deficient documents highlighted in the objection memo.",
                "2. Review your personal details (Name spelling, DOB, Address) across all attached files.",
                "3. Submit the rectification letter and verified documents to your local Tehsil / CSC or upload to the e-District portal before the 15-day deadline expires."
            ],
            "data_origin": "ai_inferred"
        }

notice_svc = NoticeService()
