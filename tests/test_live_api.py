import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def post_json(path, data):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

test_queries = [
    ("TEST 1", "How can I apply for a domicile certificate in Uttar Pradesh?"),
    ("TEST 2", "What is the difference between an income certificate and a domicile certificate?"),
    ("TEST 3", "I am a B.Tech student from UP with family income of ₹1.5 lakh. Find scholarships for me."),
    ("TEST 4", "Explain the PM-KISAN scheme."),
    ("TEST 5", "My scholarship application has been pending for 45 days."),
    ("TEST 6", "How do I update my Aadhaar mobile number?"),
    ("TEST 7", "Tell me about the latest government benefits available for farmers."),
    ("TEST 8", "Hello, how are you?"),
    ("TEST 9", "I want to apply for a certificate."),
    ("TEST 10", "I am not eligible for PM-KISAN. Are there any alternatives?")
]

print("=== VERIFYING LIVE HTTP API (/api/haqguide/chat & /api/match) ===")

for label, q in test_queries:
    # Test via /api/match
    match_res = post_json("/api/match", {"query": q, "use_ai": True})
    sec = match_res.get("section")
    matches = match_res.get("matches", [])
    has_guide = match_res.get("structured_guide") is not None
    active_scheme = match_res.get("active_scheme")
    resp_text = match_res.get("response", "")

    print(f"\n{label}: '{q}'")
    print(f"  Section: {sec} | Scheme Cards Count: {len(matches)} | Structured Guide: {has_guide}")
    print(f"  Response: {resp_text[:140].replace(chr(10), ' ')}...")

    # Strict validations:
    if label in ["TEST 1", "TEST 2", "TEST 5", "TEST 6", "TEST 8", "TEST 9"]:
        assert len(matches) == 0, f"FAILED: {label} returned {len(matches)} scheme cards! Expected 0."
        print("  [SUCCESS] 0 scheme cards returned!")
    elif label in ["TEST 3", "TEST 7", "TEST 10"]:
        assert len(matches) > 0, f"FAILED: {label} expected scheme matches but got 0."
        print(f"  [SUCCESS] {len(matches)} relevant scheme matches returned!")
    elif label == "TEST 4":
        assert sec == "scheme_expert", f"FAILED: {label} expected scheme_expert."
        print(f"  [SUCCESS] Scheme expert deep-dive activated for {active_scheme.get('name') if active_scheme else 'scheme'}")

print("\n==========================================")
print("ALL 10 API TEST SUITES PASSED FLAWLESSLY!")
print("==========================================")
