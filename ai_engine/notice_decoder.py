"""
NoticeDecoder: AI-powered government notice interpretation using Sarvam-105B.
Helps citizens understand rejection, return, and deficiency notices
in plain Hindi and English without making legal claims.
"""

import json
import re

from ai_engine import sarvam_client


_NOTICE_SYSTEM = """You are NoticeDecoder, an assistant that helps Indian citizens understand
government rejection notices, return memos, and deficiency letters.
You:
- Explain notices in simple Hindi and English
- Extract the stated reason clearly
- Compare against known rules when possible
- Never claim an official decision is wrong or corrupt
- Always distinguish between AI interpretation and official decisions
- Suggest the correct official channel for appeals
- Tell citizens to verify your interpretation with official sources
"""


def decode_notice(notice_text, service_name=None):
    """
    Decode and explain a government rejection or return notice.

    Args:
        notice_text: the full text of the notice
        service_name: optional service context

    Returns:
        dict with extracted information and plain-language explanation
    """
    service_context = f" (Service: {service_name})" if service_name else ""

    response = sarvam_client.chat(
        messages=[
            {
                "role": "user",
                "content": (
                    f"Decode this government notice{service_context}:\n\n{notice_text}\n\n"
                    "Return JSON:\n"
                    "{\n"
                    '  "notice_type": "rejection/return/deficiency/query",\n'
                    '  "reference_number": "ref if found",\n'
                    '  "date": "date if found",\n'
                    '  "stated_reasons": ["Reason 1", "Reason 2"],\n'
                    '  "required_action": "What the citizen must do",\n'
                    '  "deadline": "Response deadline if stated",\n'
                    '  "explanation_english": "Plain English explanation",\n'
                    '  "explanation_hindi": "Simple Hindi explanation",\n'
                    '  "classification": "matched_rule/needs_clarification/possible_mismatch/unable_to_verify",\n'
                    '  "confidence": "high/medium/low"\n'
                    "}"
                )
            }
        ],
        system_prompt=_NOTICE_SYSTEM,
        temperature=0.2,
        max_tokens=1024,
    )

    json_match = re.search(r"\{.*\}", response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except Exception:
            pass

    return {
        "notice_type": "unknown",
        "explanation_english": response,
        "confidence": "low",
    }


def suggest_next_steps(notice_text, service_name=None, language="Hindi"):
    """
    Suggest what a citizen should do after receiving a rejection/return notice.

    Args:
        notice_text: the notice text
        service_name: optional service context
        language: response language

    Returns:
        str: actionable next steps
    """
    lang_note = {
        "Hindi": "Explain in simple Hindi.",
        "Hinglish": "Explain in Hinglish.",
    }.get(language, "Explain in simple English.")

    service_context = f" for the service '{service_name}'" if service_name else ""

    return sarvam_client.chat(
        messages=[
            {
                "role": "user",
                "content": (
                    f"A citizen received this notice{service_context}:\n\n{notice_text}\n\n"
                    "What should they do next? Provide:\n"
                    "1. Immediate action required\n"
                    "2. Documents to gather\n"
                    "3. Who to contact\n"
                    "4. Appeal options if applicable\n"
                    "5. Deadlines to be aware of\n"
                    f"{lang_note} Be specific and practical."
                )
            }
        ],
        system_prompt=_NOTICE_SYSTEM,
        temperature=0.3,
        max_tokens=1024,
    )


def draft_response_letter(notice_text, applicant_name, application_ref,
                           service_name=None, additional_context=None):
    """
    Draft a factual response letter for the citizen to review and submit.

    Args:
        notice_text: the rejection/return notice
        applicant_name: citizen's name
        application_ref: application reference number
        service_name: optional service name
        additional_context: any additional information the citizen wants to include

    Returns:
        str: draft letter (clearly marked as AI-generated draft for review)
    """
    service_context = f" for '{service_name}'" if service_name else ""
    extra = f"\nAdditional context: {additional_context}" if additional_context else ""

    return sarvam_client.chat(
        messages=[
            {
                "role": "user",
                "content": (
                    f"Draft a polite, factual response letter{service_context} for:\n"
                    f"Applicant: {applicant_name}\n"
                    f"Application Reference: {application_ref}\n"
                    f"{extra}\n\n"
                    f"In response to this notice:\n{notice_text}\n\n"
                    "The letter should:\n"
                    "- Be formal and respectful\n"
                    "- State the application reference clearly\n"
                    "- Address each stated reason factually\n"
                    "- Request specific clarification if needed\n"
                    "- Include a clear heading: DRAFT LETTER — PLEASE REVIEW BEFORE SUBMITTING\n"
                    "- Write in English with a Hindi version below it"
                )
            }
        ],
        system_prompt=_NOTICE_SYSTEM,
        temperature=0.4,
        max_tokens=2000,
    )
