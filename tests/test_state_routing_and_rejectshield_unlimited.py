"""
Comprehensive verification test for:
1. Multi-State Dynamic Prompt Routing (Uttarakhand vs Uttar Pradesh vs Bihar).
2. Unlimited Scope RejectShield Target Scheme & Custom Scheme Entry.
3. RejectShield Verification on Custom Schemes (e.g. Widow Pension).
4. Official UI Branding verification (No Sarvam AI / MeitY / myGov in public text).
"""
import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def get_json(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def post_json(path, data):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def test_state_prompt_routing():
    print("\n--- 1. Testing State Prompt Routing (Uttarakhand vs UP vs Bihar) ---")
    
    # Test A: User spelling 'uttrakhand'
    res_uk = post_json("/api/haqguide/chat", {
        "query": "how to make domicile in uttrakhand",
        "session_id": "test_uk_prompt"
    })
    guide_uk = res_uk.get("structured_guide", {})
    portal_uk = guide_uk.get("portal_url", "")
    title_uk = guide_uk.get("title", "")
    print(f"[UK] Title: {title_uk} | Portal: {portal_uk}")
    assert "edistrict.uk.gov.in" in portal_uk, f"Expected Uttarakhand portal, got: {portal_uk}"
    assert "Uttarakhand" in title_uk
    print("[PASS] Uttarakhand prompt routing verified!")

    # Test B: UP prompt
    res_up = post_json("/api/haqguide/chat", {
        "query": "how can I apply for a domicile certificate in Uttar Pradesh?",
        "session_id": "test_up_prompt"
    })
    guide_up = res_up.get("structured_guide", {})
    portal_up = guide_up.get("portal_url", "")
    print(f"[UP] Title: {guide_up.get('title')} | Portal: {portal_up}")
    assert "edistrict.up.gov.in" in portal_up, f"Expected UP portal, got: {portal_up}"
    print("[PASS] Uttar Pradesh prompt routing verified!")

    # Test C: Bihar prompt
    res_bihar = post_json("/api/haqguide/chat", {
        "query": "How to apply for an income certificate in bihar?",
        "session_id": "test_bihar_prompt"
    })
    guide_bihar = res_bihar.get("structured_guide", {})
    portal_bihar = guide_bihar.get("portal_url", "")
    print(f"[Bihar] Title: {guide_bihar.get('title')} | Portal: {portal_bihar}")
    assert "serviceonline.bihar.gov.in" in portal_bihar, f"Expected Bihar portal, got: {portal_bihar}"
    print("[PASS] Bihar prompt routing verified!")

def test_rejectshield_unlimited_schemes():
    print("\n--- 2. Testing RejectShield Dynamic & Custom Scheme Checklists ---")
    
    # Test catalog schemes beyond the previous 4:
    schemes_to_test = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11", "S12", "S13"]
    for sid in schemes_to_test:
        chk = get_json(f"/api/rejectshield/checklist?scheme_id={sid}")
        assert len(chk.get("required_documents", [])) > 0, f"Checklist empty for {sid}"
        print(f"  [OK] {sid} ({chk.get('scheme_name')}): {len(chk['required_documents'])} required documents")
    print("[PASS] All 13 Catalog Schemes have official checklists!")

    # Test custom citizen-entered schemes
    custom_schemes = [
        ("Widow Pension Scheme", "death_certificate"),
        ("UP Destitute Women Pension", "death_certificate"),
        ("Uttarakhand Domicile Certificate", "electricity_utility_bill"),
        ("Ration Card Application", "income_certificate"),
        ("Disability Pension Support", "disability_certificate"),
        ("Kisan Samman Subsidy", "land_ownership_records")
    ]
    for sname, expected_doc_key in custom_schemes:
        encoded = urllib.parse.quote(sname)
        chk = get_json(f"/api/rejectshield/checklist?scheme_id={encoded}")
        docs = chk.get("required_documents", [])
        doc_ids = [d["id"] for d in docs]
        print(f"  [Custom] '{sname}': {len(docs)} documents generated. IDs: {doc_ids}")
        assert expected_doc_key in doc_ids, f"Expected {expected_doc_key} in {doc_ids} for '{sname}'"
    print("[PASS] Custom scheme entry system successfully produces tailored checklists!")

def test_rejectshield_verification_on_custom_scheme():
    print("\n--- 3. Testing Verification Execution on Custom Scheme ---")
    req = {
        "scheme_id": "Widow Pension Scheme",
        "documents": {
            "aadhaar_card": "GOVERNMENT OF INDIA - AADHAAR CARD\nName: Sunita Devi\nDOB: 12/04/1978\nAddress: Village Mohanlalganj, Lucknow, UP",
            "death_certificate": "REGISTRAR OF BIRTHS AND DEATHS\nDeceased: Late Ramesh Kumar\nSpouse: Sunita Devi\nDate of Death: 14/02/2025"
        }
    }
    ver_res = post_json("/api/rejectshield/verify", req)
    assert "readiness_label" in ver_res
    assert "shortage_list" in ver_res
    print(f"Verification Result for '{req['scheme_id']}':")
    print(f"  Status: {ver_res['overall_status']} | Label: {ver_res['readiness_label']}")
    print(f"  Identified Shortages: {[s['name'] for s in ver_res['shortage_list']]}")
    # Income certificate is missing from the submitted docs
    assert any("Income" in s["name"] for s in ver_res["shortage_list"]), "Should flag missing Income Certificate"
    print("[PASS] Custom scheme verification successfully identifies shortages!")

def test_ui_branding_cleanliness():
    print("\n--- 4. Testing Frontend UI Cleanliness ---")
    from pathlib import Path
    html_text = Path("frontend/index.html").read_text(encoding="utf-8").lower()
    
    assert "sarvam" not in html_text, "Found 'sarvam' in frontend/index.html"
    assert "meity" not in html_text, "Found 'meity' in frontend/index.html"
    assert "mygov" not in html_text, "Found 'mygov' in frontend/index.html"
    assert "myhaqsetu" not in html_text, "Found 'myhaqsetu' in frontend/index.html"
    print("[PASS] Zero forbidden branding terms found in frontend/index.html!")

if __name__ == "__main__":
    test_state_prompt_routing()
    test_rejectshield_unlimited_schemes()
    test_rejectshield_verification_on_custom_scheme()
    test_ui_branding_cleanliness()
    print("\n==================================================================")
    print("ALL TESTS PASSED 100%: STATE ROUTING, REJECTSHIELD, & CLEAN UI!")
    print("==================================================================")
