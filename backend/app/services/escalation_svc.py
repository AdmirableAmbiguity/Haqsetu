from typing import Dict, Any, List
from ai_engine import sarvam_client
from backend.app.services.timeline_engine import timeline_engine

class EscalationService:
    def get_all_alerts(self) -> List[Dict[str, Any]]:
        """Collects all critical and warning alerts across all active cases."""
        cases = timeline_engine.get_all_cases()
        alerts = []
        for c in cases:
            if c["sla_status"] in ["OVERDUE", "APPROACHING_DEADLINE", "STALE_FILE"]:
                alerts.append({
                    "case_id": c["case_id"],
                    "scheme_name": c["scheme_name"],
                    "department": c["department"],
                    "applicant_name": c["applicant_name"],
                    "sla_status": c["sla_status"],
                    "headline": c["headline"],
                    "badge_color": c["badge_color"],
                    "days_remaining": c["days_remaining"],
                    "days_since_update": c["days_since_update"],
                    "recommended_action": (
                        "File CPGRAMS / Statutory Grievance Petition" if c["sla_status"] == "OVERDUE"
                        else "Send Polite Status Inquiry / SMS Reminder" if c["sla_status"] == "APPROACHING_DEADLINE"
                        else "File RTI Application under Section 6(1) for File Movement Inspection"
                    )
                })
        return alerts

    def generate_letter(self, case_id: str, letter_type: str = "grievance", language: str = "English") -> Dict[str, Any]:
        """
        Generates a legally grounded, human-reviewable letter using Sarvam-105B.
        letter_type: 'grievance', 'rti', or 'status_inquiry'
        """
        case = timeline_engine.get_case(case_id)
        if not case:
            raise ValueError(f"Case '{case_id}' not found.")

        prompt = (
            f"Generate a formal, polite, and legally grounded {letter_type.upper()} letter for an Indian citizen.\n"
            f"Details:\n"
            f"- Applicant Name: {case['applicant_name']}\n"
            f"- Application ACK Number: {case['case_id']}\n"
            f"- Service Requested: {case['scheme_name']}\n"
            f"- Department: {case['department']}\n"
            f"- State: {case['state']}\n"
            f"- Date of Application: {case['submission_date']}\n"
            f"- Official Service Guarantee (Days): {case['time_limit_days']} days\n"
            f"- Target Due Date: {case['due_date']}\n"
            f"- Current Status: {case['current_status']}\n"
            f"- Days Overdue / Stale: {abs(case['days_remaining'])} days overdue\n"
            f"Language: {language}\n\n"
            f"Requirements:\n"
            f"1. Tone: Respectful, factual, assertive, not aggressive.\n"
            f"2. Reference the relevant Right to Public Services Act (RTS Act) or RTI Act 2005 (Sec 6(1)) if applicable.\n"
            f"3. State that the applicant seeks an update on the file status and reasons for the delay beyond the published SLA.\n"
            f"4. Clearly mention that this draft is for human review before final dispatch.\n"
        )

        try:
            letter_body = sarvam_client.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a legal aid and citizen rights drafting specialist. Produce well-formatted letters ready for official submission.",
                temperature=0.2,
                max_tokens=800
            )
        except Exception as e:
            # Fallback template
            letter_body = (
                f"To,\n"
                f"The Public Information Officer / Grievance Officer,\n"
                f"{case['department']},\n"
                f"{case['state']}.\n\n"
                f"Subject: Status Inquiry / Grievance regarding delay in Application Ref: {case['case_id']}\n\n"
                f"Respected Sir/Madam,\n\n"
                f"I, {case['applicant_name']}, submitted an application for '{case['scheme_name']}' on {case['submission_date']} under reference number {case['case_id']}.\n\n"
                f"As per the official Citizen Charter / Service Guarantee, the stipulated turnaround time for this service is {case['time_limit_days']} days, with the due date being {case['due_date']}.\n\n"
                f"As of today ({case['simulated_today']}), the application remains pending without conclusive action. I kindly request you to look into the matter and provide the current status and reasons for delay.\n\n"
                f"Thank you.\n\n"
                f"Yours sincerely,\n"
                f"{case['applicant_name']}\n"
                f"Applicant"
            )

        return {
            "case_id": case_id,
            "letter_type": letter_type,
            "language": language,
            "generated_letter": letter_body,
            "data_origin": "ai_inferred",
            "verification_state": "needs_review",
            "review_warning": "This letter was drafted by AI for human review. Please verify all details and dates before sending to the official department."
        }

escalation_svc = EscalationService()
