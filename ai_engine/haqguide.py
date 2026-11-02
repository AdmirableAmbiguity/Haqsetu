"""
HaqGuide: AI-powered citizen rights and service information module.
Uses Sarvam-105B to help citizens understand government services,
eligibility, required documents, and their rights — in Hindi and English.
"""

from ai_engine import sarvam_client


_HAQGUIDE_SYSTEM = """You are HaqGuide, a helpful AI assistant for Indian citizens.
You help people understand government services, their rights, and how to apply for services.
You speak in simple, clear language that ordinary citizens can understand.
You always:
- Give factual, source-grounded information about government services
- Tell citizens when you are uncertain rather than inventing answers
- Explain processes step by step
- Use the language the citizen is comfortable with (Hindi or English)
- Never make eligibility decisions — you only explain criteria
- Remind citizens to verify with official sources for consequential decisions
"""


def find_service(query, language="English"):
    """
    Identify which government service a citizen needs from a natural query.

    Args:
        query: citizen's question in natural language (Hindi or English)
        language: response language preference

    Returns:
        dict with service_name, description, department, next_steps
    """
    import json, re

    response = sarvam_client.chat(
        messages=[
            {
                "role": "user",
                "content": (
                    f"A citizen asks: '{query}'\n\n"
                    "Identify the most relevant Indian government service(s) they need. "
                    "Return a JSON object:\n"
                    "{\n"
                    '  "service_name": "Official service name",\n'
                    '  "department": "Responsible department",\n'
                    '  "description": "What this service provides",\n'
                    '  "next_steps": ["Step 1", "Step 2"],\n'
                    '  "common_documents": ["Document 1", "Document 2"],\n'
                    '  "typical_timeframe": "Expected processing time",\n'
                    '  "confidence": "high/medium/low"\n'
                    "}"
                )
            }
        ],
        system_prompt=_HAQGUIDE_SYSTEM,
        temperature=0.3,
        max_tokens=512,
    )

    json_match = re.search(r"\{.*\}", response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except Exception:
            pass

    return {"service_name": "Unknown", "description": response, "confidence": "low"}


def explain_eligibility(service_name, citizen_profile=None, language="English"):
    """
    Explain eligibility criteria for a government service.

    Args:
        service_name: name of the government service
        citizen_profile: optional dict (e.g. {"age": 35, "category": "OBC", "state": "UP"})
        language: "Hindi", "English", or "Hinglish"

    Returns:
        str: eligibility explanation
    """
    profile_text = ""
    if citizen_profile:
        profile_text = f"\nCitizen profile: {citizen_profile}"

    lang_note = {
        "Hindi": "Respond in simple Hindi.",
        "Hinglish": "Respond in Hinglish (mix of Hindi and English).",
    }.get(language, "Respond in simple English.")

    return sarvam_client.chat(
        messages=[
            {
                "role": "user",
                "content": (
                    f"Explain the eligibility criteria for '{service_name}' "
                    f"in India.{profile_text}\n\n"
                    "If there are multiple categories (General, OBC, SC/ST etc.), "
                    "explain each. Mention income limits, age limits, and other "
                    "key criteria. Say clearly if eligibility depends on state rules. "
                    f"{lang_note}"
                )
            }
        ],
        system_prompt=_HAQGUIDE_SYSTEM,
        temperature=0.3,
        max_tokens=1024,
    )


def get_service_guide(service_name, language="Hindi"):
    """
    Get a step-by-step application guide for a service.

    Args:
        service_name: government service name
        language: "Hindi", "English", or "Hinglish"

    Returns:
        str: step-by-step guide
    """
    lang_note = {
        "Hindi": "Explain in simple Hindi.",
        "Hinglish": "Explain in Hinglish.",
    }.get(language, "Explain in simple English.")

    return sarvam_client.chat(
        messages=[
            {
                "role": "user",
                "content": (
                    f"Give a complete step-by-step guide for applying for "
                    f"'{service_name}' in India. Include:\n"
                    "1. Where to apply (online portal and offline office)\n"
                    "2. Documents required\n"
                    "3. How to fill the form\n"
                    "4. Fees involved\n"
                    "5. How to get the acknowledgement\n"
                    "6. Expected timeline\n"
                    "7. What to do if there is a delay\n"
                    f"{lang_note}"
                )
            }
        ],
        system_prompt=_HAQGUIDE_SYSTEM,
        temperature=0.3,
        max_tokens=1500,
    )


def answer_rights_question(question, language="Hindi"):
    """
    Answer a citizen's question about their rights or government services.

    Args:
        question: citizen's question (Hindi or English)
        language: response language

    Returns:
        str: answer with source guidance
    """
    lang_note = {
        "Hindi": "Answer in simple Hindi.",
        "Hinglish": "Answer in Hinglish.",
    }.get(language, "Answer in simple English.")

    return sarvam_client.chat(
        messages=[{"role": "user", "content": question}],
        system_prompt=(
            f"{_HAQGUIDE_SYSTEM}\n"
            f"Answer the citizen's question. {lang_note} "
            "If you are not sure, say so clearly. "
            "Always recommend verifying with official government sources."
        ),
        temperature=0.4,
        max_tokens=1024,
    )


def generate_checklist(service_name, citizen_profile=None):
    """
    Generate a personalized document checklist for a service.

    Args:
        service_name: government service name
        citizen_profile: optional dict with citizen details

    Returns:
        dict with required and optional document lists
    """
    import json, re

    profile_text = f" for a citizen with profile: {citizen_profile}" if citizen_profile else ""

    response = sarvam_client.chat(
        messages=[
            {
                "role": "user",
                "content": (
                    f"Generate a document checklist for '{service_name}'{profile_text}. "
                    "Return JSON:\n"
                    "{\n"
                    '  "service": "service name",\n'
                    '  "required_documents": [\n'
                    '    {"document": "Name", "purpose": "Why needed", "notes": "Format/validity"}\n'
                    '  ],\n'
                    '  "optional_documents": [\n'
                    '    {"document": "Name", "purpose": "Why it helps"}\n'
                    '  ],\n'
                    '  "important_notes": ["Note 1", "Note 2"],\n'
                    '  "verification_reminder": "Always verify with official sources"\n'
                    "}"
                )
            }
        ],
        system_prompt=_HAQGUIDE_SYSTEM,
        temperature=0.2,
        max_tokens=1024,
    )

    json_match = re.search(r"\{.*\}", response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except Exception:
            pass

    return {"service": service_name, "response": response}
