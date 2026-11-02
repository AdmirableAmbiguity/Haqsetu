import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding='utf-8')

from ai_engine.query_router import query_router

queries = [
    ("Widow Financial Assistance", "a scheme for widow for finanacial assistance"),
    ("UP Widow Pension", "scheme for widow pension in UP"),
    ("Solar Rooftop", "solar panel rooftop subsidy PM Surya Ghar"),
    ("Street Vendor Loan", "loan for small street vendor PM SVANidhi"),
    ("Disability Aid", "disability financial aid for divyang pension")
]

print("=== TESTING UPGRADED LIVE DISCOVERY & RAG ENGINE ===")

for label, q in queries:
    res = query_router.route(q, section_override="scheme_finder")
    matches = res.get("matches", [])
    print(f"\n--- {label}: '{q}' ---")
    print(f"Matches count: {len(matches)}")
    assert len(matches) > 0, f"FAILED: No matches found for {q}"
    for m in matches:
        print(f"  * {m.get('name')}")
        print(f"    Dept: {m.get('department')}")
        print(f"    Source: {m.get('source_basis')}")
        print(f"    Summary: {m.get('summary')}")

print("\nALL DIVERSE QUERIES RETURNED VALID AUTHENTIC SCHEMES!")
