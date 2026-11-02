# HaqSetu AI + Vachan Setu — Project Brief

> **Role:** Senior full-stack engineer, product designer and QA lead working autonomously.  
> **Mission:** Build a working, demo-ready web application: a citizen-service assurance platform for Indian government schemes.

---

## 0. Complete Citizen Flow

1. **Write their need in their own words** (English, Hindi or Hinglish; typed or by voice).
2. The **Eligibility Matcher** returns a ranked, explainable list of schemes and combinations.
3. Citizen selects scheme(s); app shows a **personalised document checklist** with source for each requirement.
4. Citizen **uploads documents** (PDF/image) or uses synthetic samples. App does OCR/field extraction + **cross-document consistency check** → **Red/Amber/Green Application Readiness Report**.
5. Citizen "submits" via official channel (simulated, clearly labelled), records acknowledgement → **Case created**.
6. **Vachan Setu** tracks the case: calculates deadline from versioned rule, shows **Promise Timeline** with milestones, countdown, status source labels, and change/audit history.
7. **Silent-File Detector** raises approaching/overdue/stale alerts, explains why, suggests next step with a generated letter.
8. **Notice Decoder** explains a rejection/deficiency notice in plain language vs the rules.
9. **Service Health Console** shows aggregate, privacy-safe insights for authorised staff.

---

## 1. Non-Negotiable Principles

- **AI explains; deterministic code calculates and validates; official sources establish rules; humans make consequential decisions.**
- Every rule has a verification state: `verified | needs_review | unverified`. Only `verified` rules shown as official/statutory deadline.
- Every data point has an origin label: `official_source | citizen_entered | ai_inferred | synthetic_demo`.
- **Deadline ≠ live status.** Never claim knowledge of what happens inside a government department.
- **A discrepancy is a reason to verify, not proof of wrongdoing.**
- **No binding decisions.** Eligibility = "likely / possibly / needs info / likely not eligible: please confirm with official source".
- **No fabricated integrations.** All simulated adapters visibly labelled "SIMULATED".
- **Privacy:** synthetic data only for demo; consent before upload; data-minimisation; delete-my-data button; PII masking in logs; small-group suppression (k < 5) in dashboards.

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLModel/SQLAlchemy, SQLite, Pydantic v2, APScheduler, pytest |
| Frontend | React + Vite + TypeScript, Tailwind CSS, React Router, i18next (en/hi), Recharts, PWA |
| Matching/AI | Hybrid: multilingual keyword/TF-IDF + BM25 + rule-based profile extraction; optional LLM via `LLMProvider` interface |
| OCR | pytesseract + Pillow + pdfplumber/PyMuPDF; graceful fallback to embedded text or `.fields.json` sidecars |
| Voice | Browser Web Speech API (Hindi/English) with feature detection |
| Sarvam AI | `sarvam-105b-conversations` via sarvamai SDK for LLM layer |

---

## 3. Repo Structure

```
/backend
  /app
    main.py, config.py, db.py, models.py, schemas.py
    /routers   (matcher, schemes, documents, cases, clock, alerts, notices, escalation, dashboard, audit, admin, privacy)
    /services  (registry, matcher, profile_extractor, checklist, ocr, field_extractors, consistency, readiness,
                deadline_engine, status, silent_file, notice_decoder, letters, fees, audit_chain, consent, llm)
    /adapters  (sim_portal.py, sim_sms.py, sim_payment.py)   # all labelled SIMULATED
  /tests
/frontend  (React app)
/data
  eligibility_matcher_dataset.json
  timeline_tracker_dataset.json
  /rules        # one YAML per service: versioned Promise Registry records
  /samples      # synthetic documents
/docs  (ARCHITECTURE.md, DEMO_SCRIPT.md, EVALUATION.md, PRIVACY.md)
PROGRESS.md
PROJECT_BRIEF.md
Makefile
docker-compose.yml
.env.example
```

---

## 4. Core Data Model

- **Scheme/Service (Promise Registry):** id, name, department, level, jurisdiction, eligibility criteria, required documents, fees, time limit, designated officer, appeal chain, official source, verification state, rule_version, changelog.
- **RuleVersion + RuleDiff**
- **CitizenProfile, MatchSession**
- **Document, ExtractedField** (value, confidence, origin), **Finding** (type, severity R/A/G, rule reference)
- **Case, Milestone, CaseEvent, Task, Alert, Notice, Letter, Receipt**
- **AuditLog:** append-only, hash-chained

---

## 5. Features

### A. Eligibility Matcher
- Single text box + mic; language auto-detected; pipeline: extract profile → retrieve → deterministic criteria eval → rank → explain.
- Output cards with rank, eligibility badge, rationale, criteria checklist, confidence, verification state.
- At most 3 follow-up questions; re-rank live.

### B. Documents + Cross-check (RejectShield)
- Personalised checklist merged across schemes.
- Upload PDF/PNG/JPG, camera capture, or sample docs.
- Extraction: name, father/spouse name, DOB, address, document number (masked), issue date, income, category.
- Cross-Document Consistency Graph (visual, colour-coded).
- Readability check, validity checks, missing-doc detection.
- Readiness Report: overall R/A/G, grouped findings, downloadable PDF.

### C. Submission + Case Creation
- Simulated "Submit on official portal" with SIMULATED banner.
- Case created with readiness report, receipts, checklist version.

### D. Vachan Setu: Promise Clock + Timeline
- `deadline_engine`: pure functions; calendar/working days, holiday calendars, pause/resume, calculation trace.
- Promise Timeline UI: milestones (expected vs actual), countdown, status-source badges.
- Change history: hash-chained audit trail.
- Time-travel demo clock (injectable `Clock`, never `datetime.now()` directly).

### E. Silent-File Detector
- Sweep: approaching (≤7 days), overdue, stale (>14 days no update).
- Explainable risk score with factor contributions.
- Loop: Detect → Explain → Act → Measure.
- Staff Intervention Queue with role-based access.

### F. NoticeDecoder
- Paste text or upload notice; extract + explain in plain Hindi/English; compare with rules; classify `matched | needs_clarification | possible_mismatch | unable_to_verify`.

### G. Escalation Copilot
- Ladder: status inquiry → nodal officer → state grievance → CPGRAMS → appeal.
- Letter generator: factual draft, export PDF, submission tracker.

### H. Fees (light)
- Fee registry, "Is this fee right?" comparator, receipt organiser.

### I. Service Health Console (staff view)
- Aggregates over synthetic cases; suppress groups n < 5; SYNTHETIC DATA banner; CSV/PDF export.

### J. JanSetu (inclusion)
- Hindi/English toggle; voice I/O; large-text; high-contrast; WCAG AA; low-bandwidth mode; Assisted mode; human-help route.

### K. Admin: Department Knowledge Studio
- Add/edit service via form or YAML; set verification state; publish rule version; show diff; test against example cases.

---

## 6. Innovation Layer (implement in this order after core)

1. Promise-to-Proof cards
2. Case Passport (printable, QR code)
3. What-If simulator
4. Rule-change radar
5. Smart document pre-flight on mobile
6. Family bundle mode
7. Benefit gap finder
8. Tamper-evident audit chain (public verify button)
9. Fairness test harness
10. PatternWatch-lite (pattern confidence labels, k-anonymity)

---

## 7. Demo Scenario

**Persona 1: Sunita, 68, widow, Gaya (Bihar), Hindi**
1. Types in Hindi → Matcher returns NSAP old-age pension + PM-JAY with rationales.
2. Checklist with merged documents shown.
3. Uploads sample docs with transliteration mismatch → Amber finding → confirms same person → Green.
4. Submits (simulated), Case created with deadline.
5. Demo clock advances → overdue → Silent-File alert → letter generated.
6. Pastes deficiency notice → NoticeDecoder → clock paused → task created.
7. Staff view shows aggregate; admin publishes rule change → case flagged.

**Persona 2: Student, Kerala, English — income certificate → scholarship chain.**

---

## 8. Testing + Evaluation

- Unit tests: deadline engine, name matcher, profile extractor, checklist merge, risk score, k-anonymity, audit chain.
- Integration tests: full demo flow via API.
- `make eval`: precision@k, recall@k, nDCG@k, extraction F1, due-date accuracy, risk recall, consistency accuracy.
- Results written to `docs/EVALUATION.md` with honest numbers.

---

## 9. Build Phases

| Phase | Scope |
|-------|-------|
| P0 | Scaffold, tooling, seed loading, PROGRESS.md |
| P1 | Promise Registry + rule YAMLs + admin read views |
| P2 | Eligibility Matcher + evaluation script + UI |
| P3 | Checklist + upload + OCR + consistency graph + readiness report |
| P4 | Cases + Vachan Clock + timeline + demo clock + audit chain |
| P5 | Silent-File Detector + alerts + letters + escalation ladder |
| P6 | NoticeDecoder + fees + tasks |
| P7 | Service Health Console + synthetic case generator |
| P8 | JanSetu (i18n, voice, accessibility, low-bandwidth, assisted mode) + PWA |
| P9 | Admin Studio (rule versions, diff, impact) + innovation layer |
| P10 | Evaluation docs, demo script, README, polish, final QA |

After each phase: update `PROGRESS.md`, commit, keep app runnable.

---

## 10. Commands

```bash
make setup   # install all deps
make seed    # load seed data
make dev     # backend :8000 + frontend :5173
make test    # run all tests
make eval    # evaluation metrics
make demo    # one-click guided demo
```
