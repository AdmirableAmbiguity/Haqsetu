"""
AI-powered cross-document consistency analysis using Sarvam-105B.
Reasons about whether discrepancies are genuine mismatches or
acceptable formatting/abbreviation variations in Indian documents.
"""

import json
import re

from ai_engine import sarvam_client
from ai_engine.comparator import compare_documents as rule_compare_documents


_CONSISTENCY_SYSTEM_PROMPT = """You are an expert in Indian government document verification.
You will be given extracted fields from multiple documents. Analyze them for consistency.

For each potential discrepancy, determine:
1. Is this a GENUINE MISMATCH that needs correction? (e.g., different dates of birth)
2. Is this an ACCEPTABLE VARIATION? (e.g., "R. Kumar" vs "Ravi Kumar", transliteration differences)
3. Is this AMBIGUOUS and needs human review?

Return ONLY a JSON array of findings:
[
  {
    "type": "cross_document_mismatch" | "acceptable_variation" | "needs_human_review",
    "field": "field_name",
    "severity": "error" | "warning" | "info",
    "documents": ["doc1", "doc2"],
    "values": ["value1", "value2"],
    "explanation": "Plain language explanation for the citizen",
    "explanation_hindi": "Same explanation in simple Hindi",
    "recommended_action": "What the citizen should do"
  }
]
Return an empty array [] if all documents are consistent. Return valid JSON only."""


def compare_documents(documents):
    """
    AI-powered cross-document consistency analysis.
    Uses sarvam-105b to intelligently reason about discrepancies
    rather than simple string matching.

    Args:
        documents: dict of {document_name: {field: value}}

    Returns:
        list of finding dicts
    """
    if not documents or len(documents) < 2:
        return []

    try:
        doc_summary = json.dumps(documents, ensure_ascii=False, indent=2)

        response = sarvam_client.chat(
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Analyze these extracted document fields for consistency:\n\n"
                        f"{doc_summary}"
                    )
                }
            ],
            system_prompt=_CONSISTENCY_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=1024,
        )

        json_match = re.search(r"\[.*\]", response, re.DOTALL)
        if json_match:
            findings = json.loads(json_match.group())
            return findings if isinstance(findings, list) else []

    except Exception as error:
        print(f"[sarvam_comparator] AI comparison failed, falling back to rule-based: {error}")

    # Fallback to rule-based comparator
    return rule_compare_documents(documents)
