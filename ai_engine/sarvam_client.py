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


def translate_to_hindi(text):
    """Translate English text to Hindi using sarvam-105b."""
    return chat(
        messages=[{"role": "user", "content": text}],
        system_prompt=(
            "You are a professional translator. "
            "Translate the following text to simple, clear Hindi. "
            "Return only the Hindi translation, nothing else."
        ),
        temperature=0.1,
        max_tokens=2048,
    )


def explain_in_simple_language(text, language="Hindi"):
    """
    Explain complex government/legal text in simple language.
    language: "Hindi", "English", or "Hinglish"
    """
    lang_instruction = {
        "Hindi": "simple Hindi (Devanagari script)",
        "English": "simple, plain English",
        "Hinglish": "Hinglish (a mix of Hindi and English that Indian citizens use daily)",
    }.get(language, "simple Hindi")

    return chat(
        messages=[
            {
                "role": "user",
                "content": (
                    f"Explain the following government document or rule "
                    f"in {lang_instruction} for a common citizen. "
                    f"Use short sentences and avoid jargon:\n\n{text}"
                ),
            }
        ],
        system_prompt=(
            "You are a helpful assistant that explains Indian government "
            "rules and procedures to ordinary citizens in clear, accessible language."
        ),
        temperature=0.4,
        max_tokens=1024,
    )
