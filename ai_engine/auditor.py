
from ai_engine.ocr import extract_text
from ai_engine.extractor import extract_fields
from ai_engine.comparator import compare_documents


def audit_application(document_paths, requirements):
    """
    Main RejectShield audit function.

    document_paths:
        {
            "application": "path/to/application.pdf",
            "identity": "path/to/identity.pdf"
        }

    requirements:
        ["application", "identity"]
    """

    documents = {}
    findings = []

    # Step 1: Read and extract information
    for document_name, file_path in document_paths.items():

        try:
            text = extract_text(file_path)
            fields = extract_fields(text)

            documents[document_name] = fields

        except Exception as error:
            findings.append({
                "type": "document_processing_error",
                "document": document_name,
                "severity": "warning",
                "explanation": str(error)
            })

    # Step 2: Check missing documents
    for required_document in requirements:

        if required_document not in document_paths:
            findings.append({
                "type": "missing_document",
                "document": required_document,
                "severity": "error",
                "explanation":
                    f"Required document '{required_document}' was not uploaded."
            })

    # Step 3: Compare document information
    findings.extend(compare_documents(documents))

    # Step 4: Prepare report
    return {
        "overall_status": (
            "NEEDS_REVIEW" if findings else "READY_FOR_REVIEW"
        ),
        "documents_processed": list(documents.keys()),
        "findings": findings
    }
