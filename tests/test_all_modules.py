import urllib.request
import urllib.parse
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
BASE_URL = "http://localhost:8000"

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

print("=== VERIFYING ALL HAQSETU + VACHAN SETU MODULES ===")

# 1. Health
h = get_json("/api/health")
print(f"[OK] Module Health: {h['status']} | Sarvam AI Active: {h['sarvam_ai_active']}")
assert h["status"] == "healthy"

# 2. Scheme Catalog
cat = get_json("/api/schemes/catalog")
print(f"[OK] Scheme Catalog: Loaded {len(cat)} schemes")
assert len(cat) >= 13

# 3. RejectShield Checklist
rs = get_json("/api/rejectshield/checklist?scheme_id=S05")
print(f"[OK] RejectShield Checklist S05: {rs.get('scheme_name')} ({len(rs.get('required_documents', []))} docs)")
assert len(rs.get("required_documents", [])) > 0

# 4. Vachan Setu Cases & Clock
cases = get_json("/api/cases")
print(f"[OK] Vachan Setu Cases: {len(cases)} cases tracked")
assert len(cases) > 0

# Clock advance & reset
adv = post_json("/api/clock/advance", {"days": 3})
print(f"[OK] Clock Advanced: {adv['simulated_today']}")
rst = post_json("/api/clock/reset", {})
print(f"[OK] Clock Reset: {rst['simulated_today']}")

# 5. Silent-File Alerts
alerts = get_json("/api/alerts")
print(f"[OK] Silent-File Alerts: {len(alerts)} alerts generated")

# 6. Service Health
sh = get_json("/api/service-health")
print(f"[OK] Service Health: {len(sh.get('departments', []))} departments monitored, {len(sh.get('stage_bottlenecks', []))} bottlenecks analyzed")
assert len(sh.get("departments", [])) > 0

# 7. Notice Decoder
sample_notice = (
    "OFFICE OF THE TEHSILDAR, LUCKNOW (UTTAR PRADESH)\n"
    "RETURN MEMO / DEFICIENCY MEMO\n"
    "Ref: LKO/IC/2026/4521 | Date: 28/10/2026\n"
    "To: Shri Ravi Kumar, Lucknow.\n\n"
    "Your application for Income Certificate is hereby returned with the following objections:\n"
    "1. Discrepancy in declared income vs electricity bill tariff.\n"
    "2. Missing notarized affidavit on stamp paper.\n"
)
nd = post_json("/api/notice/decode", {"notice_text": sample_notice, "service_name": "Income Certificate", "language": "Hindi"})
print(f"[OK] Notice Decoder: Successfully decoded notice ({nd.get('data_origin')})")
assert "plain_language_explanation" in nd
assert "draft_response_letter" in nd

# 8. All 10 Refactored Queries Verification
queries_test = [
    ("TEST 1", "How can I apply for a domicile certificate in Uttar Pradesh?", "haqguide", 0),
    ("TEST 2", "What is the difference between an income certificate and a domicile certificate?", "haqguide", 0),
    ("TEST 3", "I am a B.Tech student from UP with family income of ₹1.5 lakh. Find scholarships for me.", "scheme_finder", 3),
    ("TEST 4", "Explain the PM-KISAN scheme.", "scheme_expert", 0),
    ("TEST 5", "My scholarship application has been pending for 45 days.", "haqguide", 0),
    ("TEST 6", "How do I update my Aadhaar mobile number?", "haqguide", 0),
    ("TEST 7", "Tell me about the latest government benefits available for farmers.", "scheme_finder", 1),
    ("TEST 8", "Hello, how are you?", "haqguide", 0),
    ("TEST 9", "I want to apply for a certificate.", "haqguide", 0),
    ("TEST 10", "I am not eligible for PM-KISAN. Are there any alternatives?", "scheme_finder", 3),
]

for label, q, exp_sec, exp_min_matches in queries_test:
    res = post_json("/api/haqguide/chat", {"query": q, "session_id": f"sess_{label}"})
    sec = res.get("section")
    matches = res.get("matches", [])
    print(f"[OK] {label}: section={sec}, matches={len(matches)}")
    assert sec == exp_sec, f"{label} expected {exp_sec} got {sec}"
    if exp_min_matches == 0:
        assert len(matches) == 0, f"{label} expected 0 matches got {len(matches)}"
    else:
        assert len(matches) >= exp_min_matches, f"{label} expected >={exp_min_matches} matches got {len(matches)}"

print("\n=======================================================")
print("ALL MODULES AND INTENT ROUTING ENDPOINTS 100% OPERATIONAL")
print("=======================================================")
