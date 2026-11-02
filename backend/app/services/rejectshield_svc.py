import difflib
import re
from typing import Dict, List, Any
from ai_engine.ocr import extract_text
from ai_engine.sarvam_extractor import extract_fields
from ai_engine.sarvam_comparator import compare_documents
from ai_engine import sarvam_client

def normalize_name(name: str) -> str:
    """Normalize whitespace and lowercase for comparison."""
    if not name:
        return ""
    name = re.sub(r'\b(mr|mrs|ms|shri|smt|dr|late)\b\.?', '', name, flags=re.IGNORECASE)
    return ' '.join(name.strip().lower().split())

def is_abbreviation_match(name1: str, name2: str) -> bool:
    """Detects if 'R. Kumar' matches 'Ravi Kumar'."""
    p1 = normalize_name(name1).replace(".", " ").split()
    p2 = normalize_name(name2).replace(".", " ").split()
    if not p1 or not p2:
        return False
    if len(p1) == len(p2):
        matches = 0
        for w1, w2 in zip(p1, p2):
            if w1 == w2 or (len(w1) == 1 and w2.startswith(w1)) or (len(w2) == 1 and w1.startswith(w2)):
                matches += 1
        return matches == len(p1)
    return False

def compare_field_values(f1: str, f2: str, field_type: str) -> Dict[str, Any]:
    if not f1 or not f2:
        return {"status": "missing_data", "score": 0.0, "note": "Field missing in one or both documents"}
    
    if field_type == "name":
        n1, n2 = normalize_name(f1), normalize_name(f2)
        if n1 == n2:
            return {"status": "exact_match", "score": 1.0, "note": "Names match exactly"}
        if is_abbreviation_match(f1, f2):
            return {
                "status": "abbreviation_variation",
                "score": 0.85,
                "note": f"Format variation detected ('{f1}' vs '{f2}'). This appears to be an abbreviation rather than a genuine conflict."
            }
        similarity = difflib.SequenceMatcher(None, n1, n2).ratio()
        if similarity > 0.80:
            return {"status": "minor_spelling_variation", "score": round(similarity, 2), "note": f"Minor spelling difference ('{f1}' vs '{f2}'). Verify official ID."}
        return {"status": "mismatch", "score": round(similarity, 2), "note": f"Significant mismatch ('{f1}' vs '{f2}'). Likely to trigger official objection."}

    if field_type == "dob":
        d1 = re.sub(r'[-/.]', '-', f1.strip())
        d2 = re.sub(r'[-/.]', '-', f2.strip())
        if d1 == d2:
            return {"status": "exact_match", "score": 1.0, "note": "Dates of birth match"}
        return {"status": "mismatch", "score": 0.0, "note": f"Date of birth mismatch ('{f1}' vs '{f2}'). This is a primary rejection cause."}

    # Generic string similarity
    sim = difflib.SequenceMatcher(None, str(f1).lower(), str(f2).lower()).ratio()
    if sim > 0.85:
        return {"status": "consistent", "score": round(sim, 2), "note": "Information is consistent"}
    return {"status": "variation", "score": round(sim, 2), "note": f"Noticeable difference in {field_type}"}

class RejectShieldService:
    def audit_documents(self, doc_inputs: Dict[str, str], required_docs: List[str] = None) -> Dict[str, Any]:
        """
        Audits uploaded document contents or file paths.
        doc_inputs: { 'application': text_or_path, 'identity': text_or_path, 'certificate': text_or_path }
        """
        required_docs = required_docs or ["application", "identity", "income_proof"]
        extracted_docs = {}
        findings = []

        # 1. Extraction
        for doc_name, content_or_path in doc_inputs.items():
            try:
                # If content looks like a file path
                if len(content_or_path) < 300 and ("." in content_or_path or "/" in content_or_path or "\\" in content_or_path):
                    raw_text = extract_text(content_or_path)
                else:
                    raw_text = content_or_path
                
                fields = extract_fields(raw_text)
                fields["_raw_preview"] = raw_text[:250]
                extracted_docs[doc_name] = fields
            except Exception as e:
                findings.append({
                    "type": "extraction_error",
                    "severity": "warning",
                    "document": doc_name,
                    "finding": f"Unable to parse document '{doc_name}': {str(e)}",
                    "evidence": "Document scan readability check",
                    "origin": "ai_inferred"
                })

        # 2. Missing documents check
        for req in required_docs:
            if req not in doc_inputs:
                findings.append({
                    "type": "missing_document",
                    "severity": "critical",
                    "document": req,
                    "finding": f"Required document '{req}' is missing from application bundle.",
                    "evidence": f"Mandated checklist under service guidelines",
                    "correction": f"Upload or provide a clear copy of {req}.",
                    "origin": "official_source"
                })

        # 3. Cross-document consistency matrix
        consistency_matrix = []
        doc_names = list(extracted_docs.keys())
        has_abbrev = False
        has_mismatch = False

        for i in range(len(doc_names)):
            for j in range(i + 1, len(doc_names)):
                d1_name, d2_name = doc_names[i], doc_names[j]
                f1, f2 = extracted_docs[d1_name], extracted_docs[d2_name]

                # Name check
                name_res = compare_field_values(f1.get("name"), f2.get("name"), "name")
                consistency_matrix.append({
                    "field": "Applicant Name",
                    "doc_a": d1_name,
                    "val_a": f1.get("name", "N/A"),
                    "doc_b": d2_name,
                    "val_b": f2.get("name", "N/A"),
                    "status": name_res["status"],
                    "score": name_res["score"],
                    "note": name_res["note"]
                })
                if name_res["status"] == "abbreviation_variation":
                    has_abbrev = True
                    findings.append({
                        "type": "name_format_variation",
                        "severity": "review_needed",
                        "document": f"{d1_name} & {d2_name}",
                        "finding": f"Name differs in format ('{f1.get('name')}' vs '{f2.get('name')}').",
                        "evidence": f"Cross-document consistency graph: {d1_name} vs {d2_name}",
                        "correction": "Ensure your official application form precisely matches the name recorded on your Aadhaar card or attach an affidavit if your name differs officially.",
                        "origin": "ai_inferred"
                    })
                elif name_res["status"] == "mismatch":
                    has_mismatch = True
                    findings.append({
                        "type": "name_mismatch",
                        "severity": "critical",
                        "document": f"{d1_name} & {d2_name}",
                        "finding": f"Severe name discrepancy detected between {d1_name} and {d2_name}.",
                        "evidence": f"{f1.get('name')} != {f2.get('name')}",
                        "correction": "Correct applicant name to match official government identity card.",
                        "origin": "ai_inferred"
                    })

                # DOB check
                if f1.get("dob") and f2.get("dob"):
                    dob_res = compare_field_values(f1.get("dob"), f2.get("dob"), "dob")
                    consistency_matrix.append({
                        "field": "Date of Birth",
                        "doc_a": d1_name,
                        "val_a": f1.get("dob"),
                        "doc_b": d2_name,
                        "val_b": f2.get("dob"),
                        "status": dob_res["status"],
                        "score": dob_res["score"],
                        "note": dob_res["note"]
                    })
                    if dob_res["status"] == "mismatch":
                        has_mismatch = True
                        findings.append({
                            "type": "dob_mismatch",
                            "severity": "critical",
                            "document": f"{d1_name} & {d2_name}",
                            "finding": f"Date of birth mismatch: '{f1.get('dob')}' vs '{f2.get('dob')}'.",
                            "evidence": f"Cross-document verification",
                            "correction": "Align DOB across documents before applying.",
                            "origin": "ai_inferred"
                        })

        # 4. Overall RAG verdict
        if any(f["severity"] == "critical" for f in findings):
            overall_rag = "RED"
            readiness_label = "High Risk of Rejection"
            readiness_color = "#ef4444"
        elif has_abbrev or any(f["severity"] == "review_needed" for f in findings):
            overall_rag = "AMBER"
            readiness_label = "Needs Citizen Review"
            readiness_color = "#f59e0b"
        else:
            overall_rag = "GREEN"
            readiness_label = "Ready for Submission"
            readiness_color = "#10b981"

        # 5. Sarvam AI Plain Language Summary
        ai_summary = ""
        try:
            summary_prompt = (
                f"Application audit completed. Verdict: {overall_rag} ({readiness_label}).\n"
                f"Findings list: {[f['finding'] for f in findings]}\n"
                f"Documents checked: {list(extracted_docs.keys())}\n"
                "Write a clear, empathetic 2-3 sentence readiness summary for the citizen in English and Hindi. "
                "Do not make binding legal decisions. Advise them exactly what to double-check before submission."
            )
            ai_summary = sarvam_client.chat(
                messages=[{"role": "user", "content": summary_prompt}],
                system_prompt="You are RejectShield AI assistant. You help citizens prevent avoidable application rejections.",
                temperature=0.3,
                max_tokens=300
            )
        except Exception:
            ai_summary = f"RejectShield audit complete: Application status is {overall_rag}. Please inspect the findings and resolve any flagged discrepancies before official submission."

        return {
            "overall_status": overall_rag,
            "readiness_label": readiness_label,
            "readiness_color": readiness_color,
            "documents_processed": extracted_docs,
            "consistency_matrix": consistency_matrix,
            "findings": findings,
            "ai_summary": ai_summary,
            "data_origin": "ai_inferred"
        }

rejectshield_svc = RejectShieldService()
