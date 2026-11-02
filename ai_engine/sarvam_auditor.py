"""
Sarvam-powered document auditor for RejectShield.
Enhanced version of auditor.py using sarvam-105b for intelligent
field extraction, consistency analysis, and plain-language reporting.

Drop-in compatible with auditor.py — same function signature.
"""

from ai_engine.ocr import extract_text
from ai_engine.sarvam_extractor import extract_fields
from ai_engine.sarvam_comparator import compare_documents
from ai_engine import sarvam_client


_REPORT_SYSTEM = """You are an application readiness assistant for Indian government services.
Generate clear, citizen-friendly audit reports. Be honest about issues found.
Use simple language. Give a Red/Amber/Green verdict with clear explanation."""


def audit_application(document_paths, requirements):
    """
    AI-powered RejectShield audit using Sarvam-105B.

    document_paths: {"application": "path/to/file", "identity": "path/to/file"}
    requirements: ["application", "identity", "certificate"]

    Returns:
        dict with overall_status, documents_processed, findings, ai_summary
    """
    documents = {}
    findings = []

    # Step 1: Extract text and fields using AI-powered extractor
    for document_name, file_path in document_paths.items():
        try:
            text = extract_text(file_path)
            fields = extract_fields(text)
            fields["_raw_text_preview"] = text[:200]
            documents[document_name] = fields

        except Exception as error:
            findings.append({
                "type": "document_processing_error",
                "document": document_name,
                "severity": "warning",
                "explanation": str(error),
            })

    # Step 2: Check for missing required documents
    for required_doc in requirements:
        if required_doc not in document_paths:
            findings.append({
                "type": "missing_document",
                "document": required_doc,
                "severity": "error",
                "explanation": f"Required document '{required_doc}' was not uploaded.",
                "explanation_hindi": f"आवश्यक दस्तावेज़ '{required_doc}' अपलोड नहीं किया गया है।",
                "recommended_action": f"Please upload your {required_doc} document.",
            })

    # Step 3: AI-powered cross-document consistency check
    # Remove internal _raw_text_preview before comparison
    docs_for_comparison = {
        name: {k: v for k, v in fields.items() if not k.startswith("_")}
        for name, fields in documents.items()
    }
    findings.extend(compare_documents(docs_for_comparison))

    # Step 4: Determine overall status
    has_errors = any(f.get("severity") == "error" for f in findings)
    has_warnings = any(f.get("severity") == "warning" for f in findings)

    if has_errors:
        overall_status = "NOT_READY"
    elif has_warnings:
        overall_status = "NEEDS_REVIEW"
    else:
        overall_status = "READY_FOR_SUBMISSION"

    result = {
        "overall_status": overall_status,
        "documents_processed": list(documents.keys()),
        "findings": findings,
    }

    # Step 5: Generate AI readiness report
    result["ai_summary"] = generate_readiness_report(result)

    return result


def generate_readiness_report(audit_result):
    """
    Generate a citizen-friendly readiness report using Sarvam-105B.

    Args:
        audit_result: the audit result dict from audit_application()

    Returns:
        dict with verdict, explanation_english, explanation_hindi, action_items
    """
    import json, re

    status = audit_result.get("overall_status", "UNKNOWN")
    findings = audit_result.get("findings", [])
    docs = audit_result.get("documents_processed", [])

    findings_summary = json.dumps(findings, ensure_ascii=False, indent=2)

    response = sarvam_client.chat(
        messages=[
            {
                "role": "user",
                "content": (
                    f"Generate an application readiness report:\n"
                    f"Status: {status}\n"
                    f"Documents processed: {docs}\n"
                    f"Findings:\n{findings_summary}\n\n"
                    "Return JSON:\n"
                    "{\n"
                    '  "verdict": "GREEN/AMBER/RED",\n'
                    '  "verdict_hindi": "हरा/पीला/लाल",\n'
                    '  "summary_english": "2-3 sentence summary for citizen",\n'
                    '  "summary_hindi": "Simple Hindi summary",\n'
                    '  "action_items": ["Action 1", "Action 2"],\n'
                    '  "action_items_hindi": ["कार्य 1", "कार्य 2"],\n'
                    '  "can_submit": true/false\n'
                    "}"
                )
            }
        ],
        system_prompt=_REPORT_SYSTEM,
        temperature=0.3,
        max_tokens=1024,
    )

    json_match = re.search(r"\{.*\}", response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except Exception:
            pass

    return {
        "verdict": "AMBER",
        "summary_english": response,
        "can_submit": False,
    }
