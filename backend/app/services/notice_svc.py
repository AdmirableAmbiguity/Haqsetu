from typing import Dict, Any
from ai_engine.notice_decoder import decode_notice, draft_response_letter
from ai_engine import sarvam_client

class NoticeService:
    def decode_rejection_notice(self, notice_text: str, service_name: str = "Income Certificate", language: str = "Hindi") -> Dict[str, Any]:
        """Decodes an official rejection or deficiency memo using Sarvam-105B."""
        decoded = decode_notice(notice_text=notice_text, scheme_rules=None)
        
        # Plain language explanation in chosen language
        explanation = ""
        try:
            explanation = sarvam_client.explain_in_simple_language(
                text=f"Official Notice states: {notice_text}\nReasons: {decoded.get('reasons')}",
                language=language
            )
        except Exception:
            explanation = f"Your application for {service_name} was returned due to: {', '.join(decoded.get('reasons', []))}."

        # Draft response letter
        try:
            response_letter = draft_response_letter(
                notice_text=notice_text,
                applicant_name=decoded.get("applicant_name") or "Applicant",
                service_name=service_name
            )
        except Exception:
            response_letter = "To The Competent Authority,\nIn reference to your deficiency memo, please find attached the requested documents..."

        return {
            "notice_summary": decoded,
            "plain_language_explanation": explanation,
            "draft_response_letter": response_letter,
            "remedial_steps": [
                "1. Gather the specific missing or deficient documents highlighted above.",
                "2. Review your personal details (Name, DOB, Address) across all attached files.",
                "3. Submit the rectification letter and documents to your local Tehsil / CSC or upload to the e-District portal before the deadline expires."
            ],
            "data_origin": "ai_inferred"
        }

notice_svc = NoticeService()
