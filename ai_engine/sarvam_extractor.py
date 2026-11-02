"""
AI-powered field extraction using Sarvam-105B.
Replaces the regex-based extractor with an LLM that understands
Indian government documents in English and Hindi.
"""

import json
import re

from ai_engine import sarvam_client
from ai_engine.extractor import extract_fields as regex_extract_fields


_EXTRACTION_SYSTEM_PROMPT = """You are a document field extraction engine for Indian government documents.
Extract structured fields from the provided document text.
Return ONLY a valid JSON object with these keys (use null for missing fields):
{
  "name": "Full name as written",
  "date_of_birth": "DD/MM/YYYY or as written",
  "address": "Full address as written",
  "father_name": "Father's name if present",
  "aadhaar_last4": "Last 4 digits of Aadhaar if present (never the full number)",
  "document_type": "Type of document (e.g. Aadhaar Card, Income Certificate, Caste Certificate)",
  "issue_date": "Document issue date if present",
  "issuing_authority": "Authority that issued this document",
  "gender": "Gender if stated",
  "mobile": "Last 4 digits of mobile if present (never full number)"
}
Rules:
- Extract exactly what is written, do not infer or guess
- For Aadhaar numbers, store ONLY the last 4 digits as aadhaar_last4
- For phone/mobile numbers, store ONLY the last 4 digits
- Return valid JSON only, no explanation text
"""


def extract_fields(text):
    """
    AI-powered field extraction using sarvam-105b.
    Falls back to regex extraction if AI call fails.

    Args:
        text: raw OCR text from a document

    Returns:
        dict of extracted fields
    """
    try:
        response = sarvam_client.chat(
            messages=[
                {
                    "role": "user",
                    "content": f"Extract fields from this document:\n\n{text[:4000]}"
                }
            ],
            system_prompt=_EXTRACTION_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=512,
        )

        # Parse JSON from response
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            fields = json.loads(json_match.group())
            # Remove null values
            return {k: v for k, v in fields.items() if v is not None}

    except Exception as error:
        print(f"[sarvam_extractor] AI extraction failed, falling back to regex: {error}")

    # Fallback to regex extractor
    return regex_extract_fields(text)
