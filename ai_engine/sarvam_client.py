"""
Sarvam-105B Cloud API client wrapper for VachanSetu.
Uses the official sarvamai SDK (pip install sarvamai).
Set SARVAM_API_KEY environment variable before use.

Model notes:
  - sarvam-105b              : Deep reasoning model. Uses internal chain-of-thought
                               tokens heavily; best for complex analysis tasks.
  - sarvam-105b-conversations: Optimised for real-time chat / voice. Returns
                               content directly without burning tokens on reasoning.
                               Used as the default for all VachanSetu modules.
"""

import os
from sarvamai import SarvamAI

_client = None

# Use the conversations variant by default — it returns content reliably
# without exhausting the token budget on internal reasoning steps.
DEFAULT_MODEL = "sarvam-105b-conversations"


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("SARVAM_API_KEY") or "sk_dwlnlpua_lms1lJhcnSxkZIGEB8WD9819"
        _client = SarvamAI(api_subscription_key=api_key)
    return _client


def chat(messages, system_prompt=None, temperature=0.3, max_tokens=1024,
         model=DEFAULT_MODEL):
    """
    Send a chat request to Sarvam AI.

    Args:
        messages: list of {"role": "user"/"assistant", "content": str}
        system_prompt: optional system-level instruction string
        temperature: float 0-1, lower = more deterministic
        max_tokens: int
        model: Sarvam model ID (default: sarvam-105b-conversations)

    Returns:
        str: model response text
    """
    client = _get_client()

    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    try:
        # sarvamai SDK: client.chat.completions() is a direct method call,
        # NOT client.chat.completions.create()
        response = client.chat.completions(
            model=model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError(
                f"Model returned no content (finish_reason="
                f"{response.choices[0].finish_reason}). "
                "Try increasing max_tokens or switching to sarvam-105b-conversations."
            )
        return content.strip()

    except Exception as error:
        raise RuntimeError(f"Sarvam API error: {error}") from error


# 11 Indian Languages supported by Sarvam-105B
SARVAM_LANGUAGES = {
    "English": {"name": "English", "native": "English", "code": "en-IN", "instruction": "simple, plain English"},
    "Hindi": {"name": "Hindi", "native": "हिन्दी", "code": "hi-IN", "instruction": "simple Hindi (Devanagari script)"},
    "Bengali": {"name": "Bengali", "native": "বাংলা", "code": "bn-IN", "instruction": "simple Bengali (Bangla script)"},
    "Telugu": {"name": "Telugu", "native": "తెలుగు", "code": "te-IN", "instruction": "simple Telugu (Telugu script)"},
    "Marathi": {"name": "Marathi", "native": "मराठी", "code": "mr-IN", "instruction": "simple Marathi (Devanagari script)"},
    "Tamil": {"name": "Tamil", "native": "தமிழ்", "code": "ta-IN", "instruction": "simple Tamil (Tamil script)"},
    "Gujarati": {"name": "Gujarati", "native": "ગુજરાતી", "code": "gu-IN", "instruction": "simple Gujarati (Gujarati script)"},
    "Kannada": {"name": "Kannada", "native": "ಕನ್ನಡ", "code": "kn-IN", "instruction": "simple Kannada (Kannada script)"},
    "Malayalam": {"name": "Malayalam", "native": "മലയാളം", "code": "ml-IN", "instruction": "simple Malayalam (Malayalam script)"},
    "Odia": {"name": "Odia", "native": "ଓଡ଼ିଆ", "code": "od-IN", "instruction": "simple Odia (Odia script)"},
    "Punjabi": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "code": "pa-IN", "instruction": "simple Punjabi (Gurmukhi script)"},
    "Hinglish": {"name": "Hinglish", "native": "Hinglish", "code": "hi-IN", "instruction": "Hinglish (a conversational blend of Hindi and English that Indian citizens use daily)"},
}


def translate_text(text: str, target_language: str = "Hindi") -> str:
    """Translate text into any of the 11 Sarvam-supported Indian languages."""
    if not text or not text.strip():
        return ""
    if target_language.lower() == "english":
        return text

    info = SARVAM_LANGUAGES.get(target_language.capitalize()) or SARVAM_LANGUAGES.get("Hindi")
    instruction = info.get("instruction", f"simple {target_language}")

    return chat(
        messages=[{"role": "user", "content": text}],
        system_prompt=(
            f"You are a professional government and legal translator for Indian citizens. "
            f"Translate the following text accurately into {instruction}. "
            f"Keep official identifiers, dates, application numbers, and amounts clear and accurate. "
            f"Return only the direct translation with no preface, commentary, or meta remarks."
        ),
        temperature=0.1,
        max_tokens=2048,
    )


def translate_to_hindi(text):
    """Translate English text to Hindi using sarvam-105b."""
    return translate_text(text, "Hindi")


def explain_in_simple_language(text, language="Hindi"):
    """
    Explain complex government/legal text in simple language across any of the
    11 Sarvam-supported Indian languages.
    """
    info = SARVAM_LANGUAGES.get(language.capitalize())
    if info:
        lang_instruction = info["instruction"]
    else:
        lang_instruction = f"simple {language}"

    return chat(
        messages=[
            {
                "role": "user",
                "content": (
                    f"Explain the following government document, rejection notice, or rule "
                    f"in {lang_instruction} for a common citizen. "
                    f"Use short sentences, clear bullet points, and avoid bureaucratic jargon:\n\n{text}"
                ),
            }
        ],
        system_prompt=(
            "You are a citizen rights advocate and administrative assistant. "
            "Explain Indian government notices, rejection reasons, and public procedures to ordinary citizens in clear, accessible language."
        ),
        temperature=0.3,
        max_tokens=1500,
    )
