# VachanSetu — Sarvam-105B Integration

This branch (`feat/sarvam-integration`) adds **Sarvam-105B** as the AI backbone for VachanSetu, replacing simple regex patterns with intelligent, India-aware reasoning across three core modules.

## What's New

### AI Modules Added

| Module | File | Purpose |
|--------|------|---------|
| Sarvam Client | `ai_engine/sarvam_client.py` | Central API wrapper for sarvam-105b |
| AI Extractor | `ai_engine/sarvam_extractor.py` | LLM-powered document field extraction |
| AI Comparator | `ai_engine/sarvam_comparator.py` | Intelligent cross-document consistency |
| HaqGuide | `ai_engine/haqguide.py` | Citizen rights & service information |
| NoticeDecoder | `ai_engine/notice_decoder.py` | Rejection notice explanation |
| Sarvam Auditor | `ai_engine/sarvam_auditor.py` | AI-powered RejectShield audit |

### Why Sarvam-105B?

- **Indian language understanding**: Native support for Hindi, Hinglish, and other Indian languages
- **Government domain knowledge**: Pre-trained on Indian legal and administrative content
- **MoE architecture**: 105B Mixture-of-Experts model — powerful reasoning with efficiency
- **Official Cloud API**: No GPU required, production-ready via `sarvamai` SDK

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get your Sarvam API key
Visit [dashboard.sarvam.ai](https://dashboard.sarvam.ai) and create an account.

### 3. Set your API key
```bash
# Windows
set SARVAM_API_KEY=your_key_here

# Or create a .env file
cp .env.example .env
# Edit .env and add your key
```

### 4. Run the demo
```bash
python demo_sarvam.py
```

## Architecture

```
Citizen Query / Document
        │
        ▼
   HaqGuide.py          ← Service finder, eligibility, checklist
   sarvam_auditor.py    ← Document audit orchestrator
   notice_decoder.py    ← Notice interpretation
        │
        ▼
   sarvam_client.py     ← sarvam-105b API (OpenAI-compatible)
        │
        ▼
   sarvam_extractor.py  ← AI field extraction (fallback: extractor.py)
   sarvam_comparator.py ← AI consistency check (fallback: comparator.py)
```

## Key Design Principles

- **Graceful fallback**: All AI modules fall back to rule-based logic if the API is unavailable
- **Privacy-first**: Only stores last 4 digits of Aadhaar/phone numbers
- **Honest uncertainty**: AI says when it doesn't know rather than inventing answers
- **Hindi + English**: All citizen-facing outputs available in both languages
- **No auto-decisions**: AI assists; humans and official sources make authoritative decisions

## Module Reference

### HaqGuide
```python
from ai_engine.haqguide import find_service, explain_eligibility, generate_checklist, answer_rights_question

# Find the right service
service = find_service("I need a caste certificate for a government job")

# Get eligibility info
eligibility = explain_eligibility("Caste Certificate", language="Hindi")

# Generate document checklist
checklist = generate_checklist("Caste Certificate", {"state": "UP", "category": "OBC"})

# Answer rights question
answer = answer_rights_question("What is the time limit for getting an income certificate?")
```

### RejectShield (AI-enhanced)
```python
from ai_engine.sarvam_auditor import audit_application

report = audit_application(
    document_paths={"application": "app.pdf", "identity": "aadhar.pdf"},
    requirements=["application", "identity", "income_proof"]
)
print(report["ai_summary"]["verdict"])        # GREEN/AMBER/RED
print(report["ai_summary"]["summary_hindi"])  # Hindi explanation
```

### NoticeDecoder
```python
from ai_engine.notice_decoder import decode_notice, suggest_next_steps, draft_response_letter

decoded = decode_notice(notice_text, service_name="Income Certificate")
steps = suggest_next_steps(notice_text, language="Hindi")
letter = draft_response_letter(notice_text, "Ravi Kumar", "LKO/IC/2026/4521")
```

## Related Modules (from `rejectshield-ai` branch)

- `ai_engine/auditor.py` — original rule-based auditor (unchanged)
- `ai_engine/extractor.py` — regex field extractor (used as fallback)
- `ai_engine/comparator.py` — rule-based comparator (used as fallback)
- `ai_engine/ocr.py` — PDF/image OCR (shared, unchanged)
