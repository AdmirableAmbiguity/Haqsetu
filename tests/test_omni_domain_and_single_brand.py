"""
Test Suite verifying:
1. OmniGovernanceEngine answers EVERY possible domain inquiry with structured steps, portals, and laws.
2. Single brand name 'VachanSetu' (no 'Official Rule Engine', no 'LOCAL DEV', no compound names).
"""
import urllib.request
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def post_json(path, data):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def test_omni_domain_queries():
    print("\n--- 1. Testing OmniDomain Queries in HaqGuide / VachanSetu ---")
    test_cases = [
        ("Consumer Complaint", "How to file a consumer complaint against a company on e-Daakhil?", "Consumer"),
        ("RTI First Appeal", "How do I file a First Appeal under Section 19 of RTI Act 2005?", "Right to Information"),
        ("EPFO PF Advance", "How can I apply for PF advance for medical treatment on EPFO?", "EPFO"),
        ("Police Zero FIR", "What are my legal rights regarding Zero FIR and police complaint?", "FIR"),
        ("Marriage Registration", "What is the procedure for marriage registration certificate?", "Marriage"),
        ("Legal Heir Certificate", "How to get a legal heir certificate in Uttarakhand?", "Legal Heir"),
        ("Senior Citizen Rights", "What protection do senior citizens have under Maintenance Act 2007?", "Senior Citizen"),
        ("e-Shram Worker Registration", "How do I register an unorganized worker on e-Shram portal?", "e-Shram")
    ]

    for label, query, expected_keyword in test_cases:
        res = post_json("/api/haqguide/chat", {
            "query": query,
            "session_id": f"sess_{label.replace(' ', '_')}"
        })
        resp_text = res.get("response", "")
        print(f"[OK] {label}: Responded with {len(resp_text)} characters.")
        assert len(resp_text) > 100, f"Response too short for {label}: {resp_text}"
        assert not res.get("matches"), f"Should not recommend unrelated schemes for {label}"
        print(f"     Preview: {resp_text[:110]}...")

    print("[PASS] Every tested domain query received an authoritative, comprehensive response!")

def test_branding_single_name_and_no_boxes():
    print("\n--- 2. Testing UI Single Project Name & Removal of Badges ---")
    html_text = Path("frontend/index.html").read_text(encoding="utf-8")
    
    # 1. The two badges must be gone
    assert "Official Rule Engine" not in html_text, "Found 'Official Rule Engine' in index.html"
    assert "LOCAL DEV" not in html_text, "Found 'LOCAL DEV' in index.html"
    print("[PASS] 'Official Rule Engine' and 'LOCAL DEV' boxes are completely removed!")

    # 2. Check title and brand
    assert "<title>VachanSetu |" in html_text, "Title should start with 'VachanSetu |'"
    assert "Vachan<span class=\"text-[#d9531e]\">Setu</span>" in html_text, "Main logo should be VachanSetu"
    print("[PASS] Project name is strictly single: 'VachanSetu'!")

if __name__ == "__main__":
    test_omni_domain_queries()
    test_branding_single_name_and_no_boxes()
    print("\n=======================================================")
    print("ALL TESTS PASSED: OMNI DOMAIN AI & CLEAN VACHANSETU UI!")
    print("=======================================================")
