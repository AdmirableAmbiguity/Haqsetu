from typing import Dict, Any
from backend.app.services.timeline_engine import timeline_engine

class AnalyticsService:
    def get_service_health(self) -> Dict[str, Any]:
        """Calculates privacy-safe aggregate statistics for staff and public audit."""
        cases = timeline_engine.get_all_cases()
        total_cases = len(cases)

        on_track = sum(1 for c in cases if c["sla_status"] == "ON_TRACK")
        approaching = sum(1 for c in cases if c["sla_status"] == "APPROACHING_DEADLINE")
        stale = sum(1 for c in cases if c["sla_status"] == "STALE_FILE")
        overdue = sum(1 for c in cases if c["sla_status"] == "OVERDUE")

        compliance_rate = round(((on_track + approaching) / max(1, total_cases)) * 100, 1)

        # Department performance
        dept_breakdown = {}
        for c in cases:
            d = c.get("department", "Other")
            if d not in dept_breakdown:
                dept_breakdown[d] = {"total": 0, "overdue": 0, "avg_days": 0}
            dept_breakdown[d]["total"] += 1
            if c["sla_status"] == "OVERDUE":
                dept_breakdown[d]["overdue"] += 1
            dept_breakdown[d]["avg_days"] += c.get("time_limit_days", 15)

        # Apply k-anonymity (k=5): mask groups smaller than 5
        dept_list = []
        for d, stats in dept_breakdown.items():
            dept_list.append({
                "department": d,
                "total_cases": stats["total"] if stats["total"] >= 5 else "< 5 (k-anonymity suppressed)",
                "overdue_cases": stats["overdue"] if stats["total"] >= 5 else "*",
                "sla_adherence_pct": round(((stats["total"] - stats["overdue"]) / stats["total"]) * 100, 1) if stats["total"] >= 5 else "N/A"
            })

        bottlenecks = [
            {"stage": "Field Enquiry & Lekhpal Verification", "avg_days_spent": 11.4, "standard_limit": 5, "status": "Critical Bottleneck (128% over SLA)"},
            {"stage": "Document Scrutiny at Inward Desk", "avg_days_spent": 1.2, "standard_limit": 2, "status": "Healthy"},
            {"stage": "Tehsildar / Competent Authority Approval", "avg_days_spent": 4.1, "standard_limit": 3, "status": "Moderate Delay"},
            {"stage": "Certificate Dispatch / Digitization", "avg_days_spent": 0.8, "standard_limit": 2, "status": "Healthy"}
        ]

        top_reasons = [
            {"reason": "Applicant name format discrepancy (Aadhaar abbreviation vs Full Name)", "percentage": 34},
            {"reason": "Missing or unverified Income Affidavit / Salary Slip", "percentage": 28},
            {"reason": "Incomplete address or domicile certificate older than validity window", "percentage": 19},
            {"reason": "Unreadable / blurry mobile phone photo scans", "percentage": 12},
            {"reason": "Other procedural objections", "percentage": 7}
        ]

        return {
            "total_cases_tracked": total_cases,
            "on_track": on_track,
            "approaching_deadline": approaching,
            "stale_silent_files": stale,
            "overdue_violations": overdue,
            "overall_sla_compliance_pct": compliance_rate,
            "departments": dept_list,
            "stage_bottlenecks": bottlenecks,
            "top_rejection_reasons": top_reasons,
            "privacy_standard": "k-anonymity (k=5) active. Synthetic demonstration data."
        }

analytics_svc = AnalyticsService()
