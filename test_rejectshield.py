
from ai_engine.auditor import audit_application

# Synthetic demo documents
document_paths = {
    "application": "samples/application.txt",
    "identity": "samples/identity.txt",
    "certificate": "samples/certificate.txt"
}

# Required documents for this demo service
requirements = [
    "application",
    "identity",
    "certificate",
    "income_proof"
]

report = audit_application(document_paths, requirements)

print("\n========== REJECTSHIELD AI ==========")

print("Overall status:", report["overall_status"])

print("\nDocuments processed:")
for document in report["documents_processed"]:
    print("-", document)

print("\nAudit findings:")
for finding in report["findings"]:
    print(finding)
