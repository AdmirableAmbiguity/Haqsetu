import difflib
import re
from typing import Dict, List, Any, Optional
from ai_engine.ocr import extract_text
from ai_engine.sarvam_extractor import extract_fields
from ai_engine import sarvam_client
from backend.app.services.registry import registry

def normalize_text(text: str) -> str:
    """Normalize text by stripping whitespace and punctuation."""
    if not text:
        return ""
    text = re.sub(r'\b(mr|mrs|ms|shri|smt|dr|late|kumari)\b\.?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[,.\-_/]', ' ', text)
    return ' '.join(text.strip().lower().split())

def is_abbreviation_match(name1: str, name2: str) -> bool:
    """Detects if 'R. Kumar' matches 'Ravi Kumar'."""
    p1 = normalize_text(name1).split()
    p2 = normalize_text(name2).split()
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
        return {"status": "missing_data", "score": 0.0, "note": "Field missing or unreadable in one document"}
    
    n1, n2 = normalize_text(f1), normalize_text(f2)

    if field_type == "name" or field_type == "father_name":
        if n1 == n2:
            return {"status": "exact_match", "score": 1.0, "note": "Names match exactly across documents"}
        if is_abbreviation_match(f1, f2):
            return {
                "status": "abbreviation_variation",
                "score": 0.85,
                "note": f"Abbreviation format difference ('{f1}' vs '{f2}'). Needs review/affidavit to avoid scrutiny."
            }
        sim = difflib.SequenceMatcher(None, n1, n2).ratio()
        if sim > 0.80:
            return {"status": "minor_spelling_variation", "score": round(sim, 2), "note": f"Minor spelling difference ('{f1}' vs '{f2}'). Verify official ID."}
        return {"status": "mismatch", "score": round(sim, 2), "note": f"Significant mismatch ('{f1}' vs '{f2}'). Likely to trigger official rejection."}

    if field_type == "dob":
        d1 = re.sub(r'[-/.]', '-', f1.strip())
        d2 = re.sub(r'[-/.]', '-', f2.strip())
        if d1 == d2:
            return {"status": "exact_match", "score": 1.0, "note": "Date of Birth matches exactly"}
        return {"status": "mismatch", "score": 0.0, "note": f"Date of Birth conflict: '{f1}' vs '{f2}'. Critical rejection reason."}

    if field_type == "category":
        if n1 == n2:
            return {"status": "exact_match", "score": 1.0, "note": f"Social Category verified as '{f1}'"}
        return {"status": "mismatch", "score": 0.0, "note": f"Social Category conflict: '{f1}' vs '{f2}'. Instant disqualification risk."}

    if field_type == "income":
        try:
            val1 = float(re.sub(r'[^\d.]', '', f1))
            val2 = float(re.sub(r'[^\d.]', '', f2))
            if abs(val1 - val2) < 1.0:
                return {"status": "exact_match", "score": 1.0, "note": f"Reported Annual Income aligns (₹{int(val1):,})"}
            diff = abs(val1 - val2)
            return {"status": "mismatch", "score": 0.5, "note": f"Income declaration discrepancy of ₹{int(diff):,} ('{f1}' vs '{f2}')."}
        except Exception:
            pass

    # Generic string comparison (Address, Institute, etc.)
    sim = difflib.SequenceMatcher(None, n1, n2).ratio()
    if sim > 0.80:
        return {"status": "consistent", "score": round(sim, 2), "note": "Information is consistent"}
    return {"status": "variation", "score": round(sim, 2), "note": f"Noticeable variance in {field_type} ('{f1}' vs '{f2}')"}


class RejectShieldVerifier:
    def verify_application_package(self, scheme_id_or_name: str, submitted_documents: Dict[str, str]) -> Dict[str, Any]:
        """
        Complete verification system:
        1. Evaluates document shortages against the official scheme checklist.
        2. Performs multi-document entity extraction.
        3. Builds Cross-Document Consistency Matrix across all document pairs.
        4. Calculates R/A/G Readiness score with evidence-backed findings and Sarvam-105B AI guidance.
        """
        scheme_doc_info = registry.get_scheme_docs(scheme_id_or_name)
        scheme_name = scheme_doc_info.get("scheme_name", scheme_id_or_name)
        required_doc_list = scheme_doc_info.get("required_documents", [])

        # Step 1: Identify Document Shortage & Completeness
        submitted_keys = set(submitted_documents.keys())
        checklist_status = []
        shortage_list = []
        present_list = []

        for req in required_doc_list:
            doc_id = req["id"]
            doc_name = req["name"]
            is_mand = req.get("mandatory", True)
            is_present = doc_id in submitted_keys or any(doc_id in k or k in doc_id for k in submitted_keys)

            item = {
                "id": doc_id,
                "name": doc_name,
                "mandatory": is_mand,
                "purpose": req.get("purpose", ""),
                "authority": req.get("authority", ""),
                "is_present": is_present
            }
            checklist_status.append(item)

            if is_present:
                present_list.append(item)
            elif is_mand:
                shortage_list.append(item)

        # Step 2: Extract structured fields from all submitted documents
        extracted_entities = {}
        for doc_key, raw_content in submitted_documents.items():
            try:
                # If content is a filepath, extract
                if len(raw_content) < 300 and ("." in raw_content or "/" in raw_content or "\\" in raw_content):
                    text = extract_text(raw_content)
                else:
                    text = raw_content

                fields = extract_fields(text)
                fields["_doc_type"] = doc_key
                fields["_raw_preview"] = text[:200]
                extracted_entities[doc_key] = fields
            except Exception as e:
                extracted_entities[doc_key] = {
                    "_doc_type": doc_key,
                    "_error": str(e),
                    "_raw_preview": raw_content[:150]
                }

        # Step 3: Cross-Document Consistency Matrix
        consistency_matrix = []
        findings = []

        # 3A: Add Findings for Shortage of Documents
        for shortage in shortage_list:
            findings.append({
                "type": "document_shortage",
                "severity": "critical",
                "document": shortage["name"],
                "finding": f"Missing Mandatory Document: {shortage['name']}",
                "evidence": f"Mandatory requirement under {scheme_name} guidelines (Issued by {shortage['authority']}).",
                "correction": f"Obtain and upload a valid {shortage['name']}. Without this document, the portal scrutiny desk will reject the application at inward.",
                "origin": "official_source"
            })

        # 3B: Cross-check fields across all submitted document pairs
        doc_names = list(extracted_entities.keys())
        has_abbrev = False
        has_critical_mismatch = False

        for i in range(len(doc_names)):
            for j in range(i + 1, len(doc_names)):
                d1, d2 = doc_names[i], doc_names[j]
                f1, f2 = extracted_entities[d1], extracted_entities[d2]

                # Check Applicant Name
                if f1.get("name") and f2.get("name"):
                    res = compare_field_values(f1.get("name"), f2.get("name"), "name")
                    consistency_matrix.append({
                        "field": "Applicant Name",
                        "doc_a": d1,
                        "val_a": f1.get("name"),
                        "doc_b": d2,
                        "val_b": f2.get("name"),
                        "status": res["status"],
                        "score": res["score"],
                        "note": res["note"]
                    })
                    if res["status"] == "abbreviation_variation":
                        has_abbrev = True
                        findings.append({
                            "type": "name_abbreviation_warning",
                            "severity": "review_needed",
                            "document": f"{d1} & {d2}",
                            "finding": f"Name format variation: '{f1.get('name')}' vs '{f2.get('name')}'.",
                            "evidence": f"Cross-document consistency check ({d1} vs {d2})",
                            "correction": "Ensure your online scholarship form strictly matches the full name recorded in Aadhaar/Matriculation mark sheet, or upload an official name variation affidavit.",
                            "origin": "ai_inferred"
                        })
                    elif res["status"] in ["mismatch", "minor_spelling_variation"]:
                        has_critical_mismatch = True
                        findings.append({
                            "type": "name_spelling_mismatch",
                            "severity": "critical",
                            "document": f"{d1} & {d2}",
                            "finding": f"Name spelling conflict detected between {d1} and {d2}.",
                            "evidence": f"{f1.get('name')} != {f2.get('name')}",
                            "correction": "Correct applicant name to ensure character-by-character alignment across official KYC documents.",
                            "origin": "ai_inferred"
                        })

                # Check Father's Name
                if f1.get("father_name") and f2.get("father_name"):
                    f_res = compare_field_values(f1.get("father_name"), f2.get("father_name"), "father_name")
                    consistency_matrix.append({
                        "field": "Father's Name",
                        "doc_a": d1,
                        "val_a": f1.get("father_name"),
                        "doc_b": d2,
                        "val_b": f2.get("father_name"),
                        "status": f_res["status"],
                        "score": f_res["score"],
                        "note": f_res["note"]
                    })
                    if f_res["status"] == "mismatch":
                        has_critical_mismatch = True
                        findings.append({
                            "type": "father_name_mismatch",
                            "severity": "critical",
                            "document": f"{d1} & {d2}",
                            "finding": f"Father's name discrepancy: '{f1.get('father_name')}' vs '{f2.get('father_name')}'.",
                            "evidence": "Cross-verification against civil records",
                            "correction": "Ensure father's name matches matriculation certificate and Aadhaar.",
                            "origin": "ai_inferred"
                        })

                # Check Date of Birth
                if f1.get("dob") and f2.get("dob"):
                    d_res = compare_field_values(f1.get("dob"), f2.get("dob"), "dob")
                    consistency_matrix.append({
                        "field": "Date of Birth",
                        "doc_a": d1,
                        "val_a": f1.get("dob"),
                        "doc_b": d2,
                        "val_b": f2.get("dob"),
                        "status": d_res["status"],
                        "score": d_res["score"],
                        "note": d_res["note"]
                    })
                    if d_res["status"] == "mismatch":
                        has_critical_mismatch = True
                        findings.append({
                            "type": "dob_mismatch",
                            "severity": "critical",
                            "document": f"{d1} & {d2}",
                            "finding": f"Date of birth mismatch: '{f1.get('dob')}' vs '{f2.get('dob')}'.",
                            "evidence": "Cross-document verification",
                            "correction": "Fix DOB mismatch before applying; this is an automated disqualifier on the scholarship portal.",
                            "origin": "ai_inferred"
                        })

                # Check Category
                if f1.get("category") and f2.get("category"):
                    c_res = compare_field_values(f1.get("category"), f2.get("category"), "category")
                    consistency_matrix.append({
                        "field": "Social Category",
                        "doc_a": d1,
                        "val_a": f1.get("category"),
                        "doc_b": d2,
                        "val_b": f2.get("category"),
                        "status": c_res["status"],
                        "score": c_res["score"],
                        "note": c_res["note"]
                    })
                    if c_res["status"] == "mismatch":
                        has_critical_mismatch = True
                        findings.append({
                            "type": "category_mismatch",
                            "severity": "critical",
                            "document": f"{d1} & {d2}",
                            "finding": f"Social Category discrepancy: '{f1.get('category')}' vs '{f2.get('category')}'.",
                            "evidence": "Caste reservation verification",
                            "correction": "Ensure category declared in application matches the caste certificate.",
                            "origin": "official_source"
                        })

                # Check Annual Income
                if f1.get("income") and f2.get("income"):
                    inc_res = compare_field_values(f1.get("income"), f2.get("income"), "income")
                    consistency_matrix.append({
                        "field": "Annual Income",
                        "doc_a": d1,
                        "val_a": f1.get("income"),
                        "doc_b": d2,
                        "val_b": f2.get("income"),
                        "status": inc_res["status"],
                        "score": inc_res["score"],
                        "note": inc_res["note"]
                    })
                    if inc_res["status"] == "mismatch":
                        findings.append({
                            "type": "income_mismatch",
                            "severity": "review_needed",
                            "document": f"{d1} & {d2}",
                            "finding": f"Income figure discrepancy between application and certificate.",
                            "evidence": f"{f1.get('income')} vs {f2.get('income')}",
                            "correction": "Align annual family income precisely with the amount certified on the official Tehsildar Income Certificate.",
                            "origin": "ai_inferred"
                        })

        # Step 4: Overall RAG Score Calculation
        if len(shortage_list) > 0 or has_critical_mismatch:
            overall_rag = "RED"
            readiness_label = f"High Risk: {len(shortage_list)} Missing Document(s) & Inconsistencies"
            readiness_color = "#ef4444"
        elif has_abbrev or any(f["severity"] == "review_needed" for f in findings):
            overall_rag = "AMBER"
            readiness_label = "Complete But Needs Review (Format Variations Detected)"
            readiness_color = "#f59e0b"
        else:
            overall_rag = "GREEN"
            readiness_label = "Application 100% Ready for Official Submission"
            readiness_color = "#10b981"

        # Step 5: Sarvam-105B AI Citizen Guidance
        ai_summary = ""
        try:
            prompt = (
                f"Applicant is applying for: {scheme_name}.\n"
                f"Document completeness: {len(present_list)} uploaded, {len(shortage_list)} missing.\n"
                f"Missing documents list: {[s['name'] for s in shortage_list]}\n"
                f"Consistency findings: {[f['finding'] for f in findings]}\n"
                f"Readiness Score: {overall_rag} ({readiness_label}).\n"
                "Provide a concise, polite citizen-facing summary in simple English and Hindi. "
                "Highlight exact missing documents they must gather and how to resolve any name/detail variation."
            )
            ai_summary = sarvam_client.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are RejectShield AI verifier. Help Indian students and citizens prepare foolproof government service applications.",
                temperature=0.3,
                max_tokens=350
            )
        except Exception:
            ai_summary = (
                f"RejectShield Audit for {scheme_name}: Overall status is {overall_rag}. "
                f"You have {len(shortage_list)} missing mandatory document(s) and {len(findings)} flagged points. "
                f"Please ensure all required certificates are uploaded and personal details match before submitting."
            )

        return {
            "scheme_name": scheme_name,
            "scheme_id": scheme_doc_info.get("id", "S05"),
            "overall_status": overall_rag,
            "readiness_label": readiness_label,
            "readiness_color": readiness_color,
            "total_required_docs": len(required_doc_list),
            "uploaded_docs_count": len(submitted_documents),
            "shortage_count": len(shortage_list),
            "checklist_status": checklist_status,
            "shortage_list": shortage_list,
            "present_list": present_list,
            "extracted_entities": extracted_entities,
            "consistency_matrix": consistency_matrix,
            "findings": findings,
            "ai_summary": ai_summary,
            "data_origin": "ai_inferred"
        }

rejectshield_verifier = RejectShieldVerifier()
