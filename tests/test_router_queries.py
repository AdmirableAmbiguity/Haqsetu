import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding='utf-8')

from ai_engine.query_router import query_router

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

print("==================================================")
print("TESTING 10 QUERIES WITH QUERY ROUTER")
print("==================================================")

for label, q in test_queries:
    res = query_router.route(q, session_id="test_sess")
    sec = res.get("section")
    matches = res.get("matches", [])
    has_guide = res.get("structured_guide") is not None
    active_scheme = res.get("active_scheme")
    resp_preview = res.get("response", "")[:120].replace("\n", " ")

    print(f"\n{label}: '{q}'")
    print(f"  -> Section: {sec}")
    print(f"  -> Matches Count: {len(matches)}")
    print(f"  -> Has Structured Guide: {has_guide}")
    print(f"  -> Active Scheme: {active_scheme.get('name') if active_scheme else None}")
    print(f"  -> Response Preview: {resp_preview}...")

    # Assertions
    if label in ["TEST 1", "TEST 2", "TEST 5", "TEST 6", "TEST 8", "TEST 9"]:
        assert len(matches) == 0, f"FAILED: {label} returned {len(matches)} scheme matches!"
        print("  [PASSED] Zero scheme cards returned as expected.")
    elif label in ["TEST 3", "TEST 7", "TEST 10"]:
        assert len(matches) > 0, f"FAILED: {label} expected scheme matches but got none!"
        print(f"  [PASSED] Scheme Finder successfully retrieved {len(matches)} relevant scheme matches.")
    elif label == "TEST 4":
        assert sec == "scheme_expert", f"FAILED: {label} expected scheme_expert but got {sec}!"
        print("  [PASSED] Scheme Expert activated for specific scheme.")

print("\nALL 10 TESTS VERIFIED AND PASSED!")
