import datetime
import hashlib
import json
from typing import Dict, List, Any, Optional
from backend.app.services.registry import registry

class TimelineEngine:
    def __init__(self):
        # Base simulated date
        self.simulated_today = datetime.date(2026, 11, 2)
        self.cases: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []
        self._seed_default_cases()

    def _seed_default_cases(self):
        """Seed initial tracked cases from timeline_tracker_dataset.json."""
        records = registry.get_timeline_scenarios()
        for idx, rec in enumerate(records[:8]):
            ack = rec.get("application_id", f"ACK-2026-{1000 + idx}")
            sub_date_str = rec.get("submission_date", "2026-10-15")
            try:
                sub_date = datetime.datetime.strptime(sub_date_str, "%Y-%m-%d").date()
            except Exception:
                sub_date = self.simulated_today - datetime.timedelta(days=14)

            offset = rec.get("expected_offset_days", 15)
            due_date = sub_date + datetime.timedelta(days=offset)
            is_statutory = rec.get("deadline_basis") == "statutory_candidate"

            # Milestones
            milestones = []
            for m in rec.get("milestones", []):
                milestones.append({
                    "name": m.get("name"),
                    "status": m.get("status", "pending"),
                    "target_date": m.get("target_date"),
                    "completed_date": m.get("completed_date"),
                    "notes": m.get("notes", "")
                })
            if not milestones:
                milestones = [
                    {"name": "Application Inward & Scrutiny", "status": "completed", "completed_date": str(sub_date + datetime.timedelta(days=1))},
                    {"name": "Field Enquiry / Lekhpal Verification", "status": "in_progress", "completed_date": None},
                    {"name": "Tehsildar Final Approval", "status": "pending", "completed_date": None},
                    {"name": "Certificate Generation & Dispatch", "status": "pending", "completed_date": None}
                ]

            case = {
                "case_id": ack,
                "scheme_name": rec.get("scheme_name", "Public Service Application"),
                "department": rec.get("department", "State Revenue / Welfare Dept"),
                "state": rec.get("state", "Uttar Pradesh"),
                "applicant_name": rec.get("applicant_name", "Sunil Sharma"),
                "submission_date": str(sub_date),
                "due_date": str(due_date),
                "time_limit_days": offset,
                "is_statutory": is_statutory,
                "verification_state": "verified" if is_statutory else "needs_review",
                "deadline_basis": "Statutory Service Guarantee" if is_statutory else "Illustrative Service Charter",
                "current_status": rec.get("current_status", "Under Scrutiny"),
                "last_update_date": rec.get("last_update_date", str(sub_date + datetime.timedelta(days=2))),
                "status_origin": "synthetic_demo",
                "milestones": milestones,
                "grievance_pathway": rec.get("grievance_pathway", [
                    {"level": 1, "authority": "Sub-Divisional Magistrate (SDM) / Tehsildar", "turnaround_days": 15},
                    {"level": 2, "authority": "District Magistrate / CPGRAMS Portal", "turnaround_days": 30}
                ]),
                "notes": rec.get("notes", "Simulated demo case from government service tracker."),
                "events": [
                    {
                        "date": str(sub_date),
                        "description": "Application submitted via citizen service portal.",
                        "origin": "citizen_entered",
                        "hash": hashlib.sha256(f"{ack}-sub".encode()).hexdigest()[:12]
                    }
                ]
            }
            self.cases[ack] = case

    def advance_demo_clock(self, days: int) -> str:
        """Advance simulated 'today' forward for interactive SLA testing."""
        self.simulated_today += datetime.timedelta(days=days)
        return str(self.simulated_today)

    def reset_demo_clock(self) -> str:
        self.simulated_today = datetime.date(2026, 11, 2)
        return str(self.simulated_today)

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        case = self.cases.get(case_id)
        if not case:
            return None
        return self._enrich_case_status(case)

    def get_all_cases(self) -> List[Dict[str, Any]]:
        return [self._enrich_case_status(c) for c in self.cases.values()]

    def create_case(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a newly submitted citizen case (SIMULATED official submission)."""
        ack = f"VS-{datetime.date.today().strftime('%Y%m')}-{len(self.cases) + 1042}"
        sub_date = self.simulated_today
        offset_days = data.get("time_limit_days", 15)
        due_date = sub_date + datetime.timedelta(days=offset_days)
        is_statutory = data.get("is_statutory", False)

        milestones = [
            {"name": "Application Inwarded", "status": "completed", "completed_date": str(sub_date)},
            {"name": "Document Verification", "status": "in_progress", "completed_date": None},
            {"name": "Field Inspection (if applicable)", "status": "pending", "completed_date": None},
            {"name": "Competent Authority Decision", "status": "pending", "completed_date": None},
            {"name": "Service Delivery / Dispatch", "status": "pending", "completed_date": None}
        ]

        event_hash = hashlib.sha256(f"{ack}-created-{sub_date}".encode()).hexdigest()[:12]

        new_case = {
            "case_id": ack,
            "scheme_name": data.get("scheme_name", "Public Service Request"),
            "department": data.get("department", "Public Services Dept"),
            "state": data.get("state", "Uttar Pradesh"),
            "applicant_name": data.get("applicant_name", "Citizen Applicant"),
            "submission_date": str(sub_date),
            "due_date": str(due_date),
            "time_limit_days": offset_days,
            "is_statutory": is_statutory,
            "verification_state": "verified" if is_statutory else "needs_review",
            "deadline_basis": "Statutory Service Guarantee" if is_statutory else "Illustrative Service Charter",
            "current_status": "Application Received",
            "last_update_date": str(sub_date),
            "status_origin": "citizen_entered",
            "milestones": milestones,
            "grievance_pathway": [
                {"level": 1, "authority": "Nodal Officer / Grievance Cell", "turnaround_days": 15},
                {"level": 2, "authority": "First Appellate Officer", "turnaround_days": 30},
                {"level": 3, "authority": "CPGRAMS / CM Helpline", "turnaround_days": 45}
            ],
            "notes": "Simulated official portal submission. Tracked under Vachan Setu guarantee.",
            "events": [
                {
                    "date": str(sub_date),
                    "description": "Application recorded in Vachan Setu with simulated portal receipt.",
                    "origin": "citizen_entered",
                    "hash": event_hash
                }
            ]
        }
        self.cases[ack] = new_case
        return self._enrich_case_status(new_case)

    def _enrich_case_status(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates live SLA countdown, freshness, and silent-file alerts relative to simulated_today."""
        due_date = datetime.datetime.strptime(case["due_date"], "%Y-%m-%d").date()
        last_update = datetime.datetime.strptime(case["last_update_date"], "%Y-%m-%d").date()
        
        days_remaining = (due_date - self.simulated_today).days
        days_since_update = (self.simulated_today - last_update).days

        # Risk & SLA State
        is_overdue = days_remaining < 0
        is_approaching = 0 <= days_remaining <= 5
        is_stale = days_since_update >= 14

        if is_overdue:
            sla_status = "OVERDUE"
            badge_color = "#ef4444"
            headline = f"Official SLA Violated by {abs(days_remaining)} days"
        elif is_approaching:
            sla_status = "APPROACHING_DEADLINE"
            badge_color = "#f59e0b"
            headline = f"Approaching Service Deadline ({days_remaining} days left)"
        elif is_stale:
            sla_status = "STALE_FILE"
            badge_color = "#ea580c"
            headline = f"Silent File: No department update for {days_since_update} days"
        else:
            sla_status = "ON_TRACK"
            badge_color = "#10b981"
            headline = f"On Track ({days_remaining} days remaining)"

        enriched = dict(case)
        enriched["simulated_today"] = str(self.simulated_today)
        enriched["days_remaining"] = days_remaining
        enriched["days_since_update"] = days_since_update
        enriched["sla_status"] = sla_status
        enriched["badge_color"] = badge_color
        enriched["headline"] = headline
        return enriched

timeline_engine = TimelineEngine()
