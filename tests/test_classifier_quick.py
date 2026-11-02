import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding='utf-8')
from ai_engine.intent_classifier import intent_classifier

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

print("=== INTENT CLASSIFICATION TEST RESULTS ===")
for label, q in test_queries:
    res = intent_classifier.classify(q)
    print(f"{label}: '{q}'")
    print(f"   Intent: {res.get('intent')}")
    print(f"   Requires Scheme Discovery: {res.get('requires_scheme_discovery')}")
    print(f"   Requires Clarification: {res.get('requires_clarification', False)}")
    print(f"   Entities: {res.get('entities')}")
    print()
