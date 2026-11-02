import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"

class PromiseRegistry:
    def __init__(self):
        self.schemes = []
        self.timeline_scenarios = []
        self.load_data()

    def load_data(self):
        matcher_path = DATA_DIR / "eligibility_matcher_dataset.json"
        timeline_path = DATA_DIR / "timeline_tracker_dataset.json"

        if matcher_path.exists():
            with open(matcher_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.schemes = data.get("scheme_catalog", [])

        if timeline_path.exists():
            with open(timeline_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.timeline_scenarios = data.get("records", [])

    def get_all_schemes(self):
        return self.schemes

    def get_scheme_by_id(self, scheme_id):
        for s in self.schemes:
            if s.get("scheme_id") == scheme_id or s.get("id") == scheme_id:
                return s
        return None

    def get_timeline_scenarios(self):
        return self.timeline_scenarios

registry = PromiseRegistry()
