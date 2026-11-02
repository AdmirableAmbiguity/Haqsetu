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

print("=== TESTING SCHEME FINDER WITH AI DISCOVERY FALLBACK ===")

# Test 1: In-catalog query (Existing matching logic must be used)
res1 = post_json("/api/scheme-finder/search", {
    "query": "I am an OBC college student in UP with 1.5 lakh income. Find scholarships.",
    "profile": {"state": "Uttar Pradesh", "category": "OBC", "annual_income": 150000, "occupation": "Student"}
})
print("\n[TEST 1 - In-Catalog Query]")
print(f"Matches count: {len(res1.get('matches', []))}")
assert len(res1.get("matches", [])) > 0
top_match = res1["matches"][0]
print(f"Top matched scheme: {top_match.get('name')}")
print(f"Verification state: {top_match.get('verification_state')}")

# Test 2: Non-catalog live query in English (Should trigger AI Discovery fallback)
res2 = post_json("/api/scheme-finder/search", {
    "query": "PM Surya Ghar Muft Bijli Yojana rooftop solar panel subsidy",
    "profile": {"state": "Uttar Pradesh", "occupation": "General"}
})
print("\n[TEST 2 - Non-Catalog English Query (AI Fallback)]")
print(f"Matches count: {len(res2.get('matches', []))}")
assert len(res2.get("matches", [])) > 0
live_match = res2["matches"][0]
print(f"Discovered Scheme: {live_match.get('name')}")
print(f"Department: {live_match.get('department')}")
print(f"Source: {live_match.get('source_basis')}")
print(f"Verification State: {live_match.get('verification_state')}")
assert live_match.get("verification_state") == "verified_live"

# Test 3: Non-catalog live query in Hinglish (Should trigger AI Discovery fallback)
res3 = post_json("/api/scheme-finder/search", {
    "query": "Mahilaon ke liye self employment udyami loan yojana in Bihar",
    "profile": {"state": "Bihar", "gender": "Female"}
})
print("\n[TEST 3 - Non-Catalog Hinglish Query (AI Fallback)]")
print(f"Matches count: {len(res3.get('matches', []))}")
assert len(res3.get("matches", [])) > 0
hinglish_match = res3["matches"][0]
print(f"Discovered Scheme: {hinglish_match.get('name')}")
print(f"Department: {hinglish_match.get('department')}")
print(f"Verification State: {hinglish_match.get('verification_state')}")

# Test 4: Generic certificate query to HaqGuide (MUST NOT trigger Scheme Finder or schemes)
res4 = post_json("/api/haqguide/chat", {
    "query": "How can I apply for a domicile certificate in Uttar Pradesh?"
})
print("\n[TEST 4 - Generic HaqGuide Query]")
print(f"Section: {res4.get('section')}")
print(f"Matches count: {len(res4.get('matches', []))}")
assert res4.get("section") == "haqguide"
assert len(res4.get("matches", [])) == 0
print("Zero scheme cards returned as expected!")

print("\n=======================================================")
print("ALL SCHEME FINDER FALLBACK INTEGRATION TESTS PASSED!")
print("=======================================================")
