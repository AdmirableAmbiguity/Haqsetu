# HaqSetu + Vachan Setu: Synthetic Seed Datasets (v0.1.0)

Files
- `eligibility_matcher_dataset.json` – scheme catalog (13 schemes) + 12 free-text queries (en / hi / Hinglish) with gold ranked matches, rationales, combinations and follow-up questions.
- `timeline_tracker_dataset.json` – 12 application timelines across 12 states, with milestones, derived deadlines, freshness/risk labels and grievance pathways. All derived values are computed relative to `as_of_date` = 2026-11-02.

Each file contains `dataset_info`, a `schema` (field descriptions), and `records`. Every record has `metadata` with `data_origin` ("synthetic"), `source_basis`, `source_urls`, `confidence_score`, `version`, `verification_state`.

## Read this first: what is and is not real
- All records are synthetic. No real citizen or application data.
- Scheme names and portal domains are real; **eligibility text is a paraphrased summary and is `needs_review`**, not verified against current notifications.
- Milestone durations are **illustrative, not statutory** (`deadline_basis: illustrative_synthetic`). Only the MGNREGA job-card record (T009) is marked `statutory_candidate`, and still needs human verification. This follows the project rule: never present an unverified number as a statutory deadline.
- A calculated deadline is not live status. Output must say status is citizen-entered unless an official integration exists.
- Licensing: if you add real data (e.g., data.gov.in), check each dataset's licence (often GODL-India, attribution required) and keep a source/date per record. Do not train on private grievance data.

## Pipeline integration

### 1. Eligibility Matcher
1. Load `scheme_catalog` as the retrieval index (embed `name + eligibility_summary`; later replace with verified rule passages from the Vachan registry).
2. Stage A, extraction: LLM/NER maps `input.text` to `parsed_profile` (train/evaluate against that field).
3. Stage B, deterministic filter: apply exclusion/age/state rules from the registry; produce `criteria_met/unmet/unknown`.
4. Stage C, ranking + explanation: rank candidates, generate rationale from the criteria lists only (no unsupported claims), and emit `follow_up_questions` when unknowns dominate (`needs_clarification`).
5. Never output a binding eligibility verdict; use the `eligibility_signal` vocabulary.

### 2. Timeline Tracker
1. Deadline = `submission_date + expected_offset_days` using `rule_ref` (calendar days here; plug in working-day/holiday logic when verified rules exist). This is deterministic code, not an LLM.
2. Classify `deadline_state` (approaching = due within 7 days; stale status = no update for over 14 days; `paused_awaiting_citizen` if an unanswered deficiency notice exists).
3. Risk = transparent rules over `risk_factors`; an LLM may only phrase `recommended_next_action` and draft letters.
4. Walk `grievance_pathway` in order; state portal names beyond the four listed must be verified per state.

### Scaling the data
Template-expand: vary state/district, scheme, age/income bands, language/spelling, and noise (typos, code-mixing, missing fields). Keep a hand-verified gold test split that is never used for training. Replace synthetic `source_basis` with real citations and set `verification_state: verified` plus `last_verified_date` only after human review.

## Evaluation schema

Eligibility Matcher (per query, averaged; also report per `tags` slice and per language)
```json
{"precision_at_k": "|top-k predicted ∩ gold with relevance_grade>=2| / k",
 "recall_at_k": "|top-k predicted ∩ gold with relevance_grade>=2| / |gold with grade>=2|",
 "ndcg_at_k": "uses relevance_grade 0-3",
 "profile_extraction_f1": "field-level F1 vs parsed_profile",
 "signal_accuracy": "match of eligibility_signal for gold schemes",
 "clarification_accuracy": "needs_clarification predicted vs gold",
 "unsupported_claim_rate": "rationale statements not traceable to criteria lists / sources (lower is better)"}
```

Timeline Tracker
```json
{"due_date_exact_match": "predicted final_due_date == gold",
 "due_date_abs_error_days": "mean |predicted - gold|",
 "deadline_state_accuracy": "plus confusion matrix",
 "approaching_overdue_precision_recall": "treat approaching/overdue as positive class",
 "risk_level_accuracy_and_high_recall": "recall on risk_level=high matters most (missed alerts)",
 "freshness_accuracy": "fresh/stale/no_status_data",
 "pathway_order_accuracy": "levels in correct order",
 "false_claim_rate": "outputs implying live government status without an official source"}
```

Minimal sketch
```python
def prf(pred, gold):
    p=set(pred); g=set(gold); tp=len(p&g)
    return tp/max(len(p),1), tp/max(len(g),1)
gold=[m["scheme_id"] for m in rec["expected_output"]["ranked_matches"] if m["relevance_grade"]>=2]
precision, recall = prf(pred_ids[:3], gold)
```

With 12 records per file, treat metrics as smoke-test only; report confidence intervals once the set grows.
