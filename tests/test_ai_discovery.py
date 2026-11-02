import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding='utf-8')

from ai_engine.ai_scheme_discovery import ai_scheme_discovery

print("=== TESTING AI SCHEME DISCOVERY FALLBACK SERVICE ===")

test_queries = [
    ("English Non-Catalog Query", "PM Surya Ghar Muft Bijli Yojana rooftop solar panel subsidy", {"state": "Uttar Pradesh"}),
    ("Hinglish Query", "Mahilaon ke liye self employment loan yojana in Bihar", {"state": "Bihar", "gender": "Female"}),
    ("Hindi Query", "छात्राओं के लिए उच्च शिक्षा स्कॉलरशिप योजना", {"state": "Rajasthan", "occupation": "Student"})
]

for label, q, prof in test_queries:
    print(f"\n--- Testing: {label} ---")
    print(f"Query: '{q}' | Profile: {prof}")
    results = ai_scheme_discovery.discover_schemes(q, prof)
    print(f"Discovered Schemes: {len(results)}")
    for s in results:
        print(f"  * Name: {s.get('name')}")
        print(f"    Dept: {s.get('department')}")
        print(f"    Source: {s.get('source_basis')}")
        print(f"    Verification State: {s.get('verification_state')}")
        print(f"    Summary: {s.get('summary')}")
        # Assert schema fields
        for key in ["scheme_id", "name", "department", "state", "score", "signal", "criteria_met", "criteria_unmet", "criteria_unknown", "summary"]:
            assert key in s, f"Missing key {key} in discovered scheme"

print("\nAI SCHEME DISCOVERY TESTS PASSED!")
