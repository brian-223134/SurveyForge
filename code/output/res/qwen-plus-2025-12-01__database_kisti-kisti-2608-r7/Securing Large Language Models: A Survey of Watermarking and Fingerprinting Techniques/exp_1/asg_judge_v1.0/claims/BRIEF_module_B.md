# Module B judging brief (asg-judge v1.0) — one chapter group per subagent

ROOT = /data2/chanjoong/survey-agent/SurveyForge/code/output/res/qwen-plus-2025-12-01__database_kisti-kisti-2608-r7/Securing Large Language Models: A Survey of Watermarking and Fingerprinting Techniques/exp_1/asg_judge_v1.0

Protocol: /data2/chanjoong/survey-agent/SurveyForge/asg_judge_prompt.md. Read Section 3 (ground rules), Section 7 (B1, B2, B3, B5) and Appendices B and C before judging. Follow Appendix B.2 rule order literally and read the B.5 calibration examples.

Topic: "Securing Large Language Models: A Survey of Watermarking and Fingerprinting Techniques". Generator: SurveyForge / qwen-plus. Judge model: claude-opus-5-5.

## Inputs
- `ROOT/claims/input_<G>.jsonl`: one row per body sentence of your chapters, in order. Fields: sid, section, role, text (markers stripped), raw (with [n] markers), cites, artifact, duplicate_of, prev_sentence.
  - role `claim`: has ≥1 citation → full B2+B3 judgment.
  - role `uncited_sample`: B5 classification.
  - role `scope_only`: only the D3 scope label.
  - role `duplicate`: verbatim repeat of an earlier sentence; give only the D3 scope label, nothing else.
  - `artifact: true` marks leaked generation notes (the generator's citation-checker talking about "the provided list"). Judge them like any other sentence of their role; they are usually `claim_type: meta_self`.
- Evidence: `ROOT/evidence/ref_<n>.md` (canonical title, first_public, corpus abstract). The bibliography is `ROOT/parsed/references.json` (ref_id → title) — use it to find `alt_ref` for misattributions.
- Survey text itself (for context only): `ROOT/../Securing Large Language Models: A Survey of Watermarking and Fingerprinting Techniques.md`.

## Evidence policy
- A pair is `SUPPORTED` only on retrieved evidence (the abstract file, or full text you fetched). Memory alone → `NEI` with evidence `prior_knowledge`. Use memory freely for `world_truth`.
- Full text: at most 4 fetches for your whole group, only from arxiv.org (abs/html/pdf) for arXiv refs. Use them for specific claims (numbers, named sub-methods) where the abstract is silent and the cited paper is plausibly the right one. If you fetch, append the checked passage (≤25 words quoted, with section name) under `## fulltext notes` in that ref's evidence file and set the pair's evidence to `fulltext`. Do not do general web search.
- When the abstract is silent on a specific unit and you do not fetch: if the paper is clearly on a different subject → `NOT_SUPPORTED`; if the unit is plausibly in the body → `NEI` (sparingly), else `PARTIAL` naming the absent unit.

## Outputs (append one JSON line per item as you go; never hold everything in memory)
1. `ROOT/claims/l2_<G>.jsonl` — one line per `claim` row, Appendix C schema exactly:
   `{"sid","duplicate_of":null,"claim_type","sentence_support","world_truth","severity","autosurvey":{"joint","per_ref":[{"ref","alone","without","relevant"}]},"pairs":[{"ref","support","error_type","alt_ref","absent_or_conflicting_units","evidence"}],"rationale","artifact"}`
   - `autosurvey.joint` = AutoSurvey binary NLI (B.1) with all cited abstracts as Source; run the necessity test (alone/without) only when joint is true; when joint is false, per_ref may be `[]`.
   - `severity` null when sentence_support is SUPPORTED.
   - rationale: 1–2 sentences stating what the source actually says.
2. `ROOT/claims/uncited_<G>.jsonl` — one line per `uncited_sample` row: `{"sid","chapter","content_type","world_truth","needs_citation","overreach","rationale"}`. world_truth only meaningful for specific_factual (else "n/a"). Check the "continues describing the previously cited paper with added details" pattern using prev_sentence.
3. `ROOT/structure/scope_<G>.jsonl` — one line for EVERY row in your input (all roles): `{"sid","scope":"on_topic|adjacent|off_topic"}`. Definitions: on_topic = about watermarking/fingerprinting/provenance of LLMs, their outputs or data (incl. attacks, evaluation, deployment, governance of such schemes); adjacent = watermarking of other modalities/models, or LLM security/privacy/regulation without a watermark/fingerprint link; off_topic = unrelated (leaked notes about the survey's own citation list count as off_topic).

Keep `ROOT/claims/progress_<G>.json` updated with the last sid done. If files already exist (resume), continue after the last sid present.

## Final reply (short)
Counts of sentence_support labels, number of full-text fetches used and for which refs, and the 5 most severe problems (sid, ≤15-word quote, label, what the source says).
