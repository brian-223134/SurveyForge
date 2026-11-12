# ASG Judge report: SurveyForge / qwen-plus on "Securing Large Language Models: A Survey of Watermarking and Fingerprinting Techniques"

## 1. Header

| | |
| --- | --- |
| Topic (requested) | Securing Large Language Models: A Survey of Watermarking and Fingerprinting Techniques (`llm-watermarking`) |
| Survey file | `exp_1/Securing Large Language Models….md` (sha256 `9b4bd952…`), 16,655 body words, 479 sentences, 121 references |
| Generator | SurveyForge (KISTI fork, branch `kisti`) / qwen-plus-2025-12-01 @ DashScope, temperature 0.6, view kisti-2608-r7 |
| Judge | claude-opus-5-5 (main session + subagents) |
| Prompt version | asg-judge v1.0, elicitation `rationale_first` |
| Date | 2026-11-11 |
| Modules run | A1, A2 (×3 runs), B (B2, B3, B5), C (C1–C6), D (D1–D4), reliability check |
| Not run | A3, A4, A5, B4 (optional, not requested); D3 GT-category coverage and A3b (no GT outline available) |
| Search policy | `limited+fulltext`: corpus abstracts, arXiv/Crossref ID lookups, ≤4 arXiv full-text fetches per judging subagent (15 used successfully) |
| Judge and generator same family | **false** (Claude judge, Qwen generator) |

## 2. Headline

The survey looks like a competent survey (rubric scores are a flat 3/5), and every one of its 121 references is a real, correctly identified paper. But what it says about those papers is mostly wrong. Only **6.4% of cited sentences (15/234) are fully supported** by the papers they cite, **21.4% (50/234) directly contradict** their source, and **76.1% (178/234) carry a major error**. The dominant failure is **misattribution** (166 of 350 non-supported pairs): a real, on-topic paper gets credited with a method, number or mechanism from somewhere else, or invented. 27% of cited sentences (63/234) are false even by general knowledge. The generator also leaked its own citation-checking notes into the text: 33 sentences (817 words) in §7.1 and §7.5, followed by full duplicate "corrected" versions of both subsections.

## 3. Rubric scores (judge: claude-opus-5-5, asg-judge v1.0; 3 independent runs)

| Module | Criterion | Scale | Run 1 / 2 / 3 | Mean | Source |
| --- | --- | --- | --- | --- | --- |
| A1 | Coverage | 1–5 | 3 / 3 / 3 | 3.00 | AutoSurvey 2024 |
| A1 | Structure | 1–5 | 3 / 2 / 3 | 2.67 | AutoSurvey 2024 |
| A1 | Relevance | 1–5 | 4 / 3 / 3 | 3.33 | AutoSurvey 2024 |
| A1 | Synthesis | 1–5 | 3 / 3 / 3 | 3.00 | SurveyX 2025 |
| A1 | Critical Analysis | 1–5 | 3 / 3 / 3 | 3.00 | SurveyX 2025 |
| A2 | Objective Clarity | 1–5 | 3 / 3 / 3 | 3.00 | DeepSurvey-Bench 2026 |
| A2 | Classification-Evolution Coherence | 1–5 | 3 / 3 / 3 | 3.00 | DeepSurvey-Bench 2026 |
| A2 | Dataset & Metric Coverage | 1–5 | 3 / 3 / 3 | 3.00 | DeepSurvey-Bench 2026 |
| A2 | In-depth Comparison | 1–5 | 3 / 3 / 3 | 3.00 | DeepSurvey-Bench 2026 |
| A2 | Critical Analysis (DSB) | 1–5 | 3 / 3 / 3 | 3.00 | DeepSurvey-Bench 2026 |
| A2 | Research Gaps | 1–5 | 3 / 4 / 4 | 3.67 | DeepSurvey-Bench 2026 |
| A2 | Future Work | 1–5 | 3 / 3 / 3 | 3.00 | DeepSurvey-Bench 2026 |

- **A1 mean:** 3.00.
- **A2 dimensions:** Information 3.00, Scholarly communication 3.00, Research guidance 3.33.
- **A2 overall:** 3.10, so the survey is not "select" (that needs at least 4).
- **Module A was scored on the survey text only, before any evidence was read.** All three runs independently flagged the same problems: the leaked notes in §7.1/§7.5, the duplicated threat taxonomy (§2.4 vs §5.1), §4.4 filing output-level methods under "parameter-space", and §7.1 having no real multimodal content.

## 4. Layered metrics

| Layer | Metric | Value | n | Reference point |
| --- | --- | --- | --- | --- |
| L1a | Hallucinated references (id_title_mismatch + not_found) | 0.0% | 0/121 | IDs resolved via arXiv API / Crossref |
| L1a | Identity `match` | 100% | 121/121 | 8 are retitled arXiv versions, verified by abstract |
| L1b | Title quality ok | 100% | 121/121 | |
| L1b | Year matches cited version | 99.2% | 120/121 | [53] printed 2025, NDSS DOI 2026 |
| C3 | References first public after cutoff 2026-02-04 | 0 | 0/121 | Policy applied; 0 leaks |
| C4 | Relevance_LLM (core + adjacent) | 99.2% | 120/121 | SurveyX binary |
| C4 | Core share | 55.4% | 67/121 | 1 unrelated: [49], network-device fingerprinting (name collision) |
| C5 | GT recall (SurGE) | 12.8% | 27/211 | Published GT list; 27/209 = 12.9% on the pre-cutoff pool |
| C5 | Reference IoU (SurveyX) | 8.9% | 27/305 | |
| C5 | SAM-R (single-GT) | 22.3% | 27/121 | |
| C6 | Input-reference usage | 27.9% | 121/433 | Writing-stage retrieval pool |
| L2 | recall_strict | **6.4%** [3.9–10.3%] | 15/234 | Wilson 95% |
| L2 | recall_lenient (SUPPORTED + PARTIAL) | 38.9% | 91/234 | |
| L2 | precision_strict (pairs) | 13.2% | 53/403 | |
| L2 | precision_lenient | 35.0% | 141/403 | |
| L2 | major_rate | **76.1%** | 178/234 | |
| L2 | contradiction_rate | **21.4%** | 50/234 | |
| L2 | world_false_rate | **26.9%** | 63/234 | world_truth `unclear` in 114 |
| L2 | nei_rate | 0.0% | 0/234 | |
| L2 | synthesis_support | 1.7% | 1/58 | Synthesis claims are almost never supported |
| L2 | Uncited specific-factual error rate | 27.3% [13.2–48.2%] | 6/22 | Lower bound: 10/22 are unclear |
| L2 | Uncited share of body sentences | 49.7% | 231/465 | 24.4 citations per 1,000 words |
| L3 | §4.4 ("parameter-space") items that are really output-level | 87.5% | 7/8 | |
| L3 | Declared taxonomies used outside their declaring section | Locus 40, modality 42, security properties 35, threat axes 39 sentences | | Taxonomies are used; §5.1 re-declares a different three-axis adversary framework |
| L4 | Leaked generator notes | 6.9% of sentences | 33/479 (817 words) | §7.1, §7.5 |
| L4 | Exact duplicate sentences | 14 (469 words) | | §7.1 and §7.5 "corrected" copies |
| L4 | Near duplicates (Jaccard ≥ 0.8) | 4 | | |
| L4 | Math brackets turned into citations | 4 | | `\mathbb{I}[61]`, `$[63]$` linear code, `'[80]'`, `\Pr[104]` |
| L4 | One marker bound to many distinct papers | [86] stands for 9 named papers | §4.5 | Root cause in §7 below |
| L5 | On-topic sentences | 90.5% | 421/465 | Adjacent 2.2%, off-topic 7.3% (mostly the leaked notes) |
| D4 | Subsection words | mean 513 ± 200 (485 ± 128 without §7.1) | 31 | Configured `subsection_len` = 500; CV 0.26 without §7.1 |

D4 hypothesis, not a finding: subsection lengths cluster tightly around the 500-word target, while citation density is moderate (median 11 links per subsection). This suggests length was driven by the target rather than by the evidence. The many fabricated figures fit that reading.

## 5. AutoSurvey-compatible vs. strict citation metrics

| Metric | AutoSurvey-compatible (B2) | Strict (B3) |
| --- | --- | --- |
| Recall | 23.9% (56/234) | 6.4% (15/234) supported; 38.9% lenient |
| Precision | 17.6% (71/403) | 13.2% (53/403) supported; 35.0% lenient |
| F1 | 0.203 | — |

The AutoSurvey binary question only asks whether the "core part" of a claim is supported. That forgives the specific numbers, sub-method names and mechanisms that this survey gets wrong, so B2 recall is almost 4× the strict recall. Even so, both numbers are low.

## 6. Top 10 problems

| # | sid (§) | Quote | Label | What the source says | Why it matters |
| --- | --- | --- | --- | --- | --- |
| 1 | S0326 (6.3) | "SynthID-Text [9] … this design precludes compatibility with speculative decoding" | CONTRADICTED, major | [9] says it develops "an algorithm integrating watermarking with speculative sampling" | Reverses the main contribution of a landmark paper; the "α·β ≤ C" bound is invented |
| 2 | S0273 (5.4) | "[39] proves such removal is information-theoretically inevitable" | CONTRADICTED, major | [39] (Sandcastles) argues mixing is slow; attacks remove watermarks only 26% of the time | Inverts the conclusion of the cited paper on a central theoretical question |
| 3 | S0244 (5.2) | "Bileve … showing bi-level signature spoofing can forge fine-grained integrity bits" | CONTRADICTED, major | [25] proposes the bi-level signature as a defense against spoofing | A defense is reported as an attack; chapter 5 does this repeatedly ([25], [34], [87], [55], [89]) |
| 4 | S0189 (4.4) | "Multi-Bit Distortion-Free … embed user IDs … directly into weight perturbations" | CONTRADICTED, major | [82], [83] and [54] embed multi-bit marks in generated text | Output-level methods filed as parameter-space; the "BER < 2%" figure is not in any source |
| 5 | S0144 (3.5) | "BanglaLorica shows round-trip translation collapses detection from 88.2% to 9.7%" | CONTRADICTED, major | [52] (X-SIR) tests zh/ja/fr/de; AUC drops to ~0.6 | A fabricated study name and fabricated numbers, BanglaLorica or the 88% figure recur in 10 sentences (§3.1–3.5, 5.4, 5.6, 6.4, 7.5) |
| 6 | S0085 (2.5) | "PLMmark … embeds zero-knowledge proofs within MPC protocols … GDPR Article 32" | CONTRADICTED, major | [19] uses digital signatures and a contrastive loss; no ZKP or MPC | Invented mechanism plus regulatory compliance claims |
| 7 | S0332 (6.3) | "Chain & Hash … requires white-box access" | CONTRADICTED, major | [36] works "in a black-box setting, requiring only API-level access" (full text) | Chain & Hash is filed under 4 different modalities across the survey |
| 8 | S0204–S0210 (4.5) | "Functional Invariants … [86], which proves computational indistinguishability" | NOT_SUPPORTED, misattribution, world-false | [86] is an image-watermarking review; [22] has no cryptographic proof | Nine different papers, including the survey's own title, are all cited as [86] |
| 9 | S0434 (7.4) | "PostMark's logit-free … sub-50ms overhead … 95%+ detection [81]" | NOT_SUPPORTED, misattribution, world-false | [81] is Yang et al.'s synonym-substitution watermark, not PostMark | A method not in the bibliography gets invented performance numbers |
| 10 | S0445 (7.5) | "GPT-5 and Gemini 2.5 Pro exhibit strong detection capability for watermarks [115; 116]" | NOT_SUPPORTED, major | [115] is a 2006 synonym-watermarking paper; [116] is about confidentiality in agentic systems | An empirical claim about current models backed by sources that cannot contain it |

Also notable:
- **Leaked notes that are themselves wrong.** S0446 says no listed paper proposes cryptographic undetectability, but [18] does. S0449, S0450 and S0455 say [118], [18] and [119] are "not in the provided list", but all three are in the bibliography.
- **Numbers on a DNN paper.** S0005 attaches "a 7B-parameter model incurs multi-million-dollar compute costs" to [7], Uchida et al. 2017 (DNN watermarking).

## 7. Inferred causes (all inferred from the output files, not from the code)

| Failure | Most likely stage | Evidence |
| --- | --- | --- |
| Misattribution and invented numbers and mechanisms (166 misattribution pairs, 76 baseless additions) | **Writing / length target.** Citation binding is not the cause | In `raw_survey.txt` the writer already cites by title, e.g. "Kirchenbauer et al. [Scalable watermarking for identifying large language model outputs]" and "HuRef [Hey, That's My Model! … Chain & Hash]". Title→ID resolution is faithful (C1 100% match). The ~500-word target per subsection, filled from abstracts, plausibly drives the padding with figures |
| [86] bound to 9 different papers in §4.5 | **Writing + citation resolution** | The raw draft has 13 literal `[paper_title]` template placeholders, all in §4.5. The resolver mapped each one to the same paper ([86]), and the output was not checked for repeated identical markers |
| Leaked notes and duplicated "corrected" subsections in §7.1/§7.5 | **Writing-stage self-check, not the refinement step** | The same notes are already in `raw_survey.txt` (17 marker hits). The LLM returned its reasoning plus a corrected version, and the output parser kept both. Its "provided list" numbering differs from the final bibliography, so the notes call real references missing |
| Math brackets as citations (`\mathbb{I}[61]`, `\Pr[104]`, `[63]` code) | **Post-processing / citation numbering** | Bracketed math (`\mathbb{I}[·]`, `[n,k,d]`) appears to have been parsed as citation slots and renumbered |
| 45% of references only "adjacent"; unrelated [49] (device fingerprinting) | **Retrieval / query expansion** | Keyword match on "fingerprinting" pulls in network fingerprinting; general LLM privacy/safety surveys are cited in the introduction |
| Duplicated threat taxonomy (§2.4 / §5.1); §4.4 mis-scoped | **Outline** | Two chapters were each given a "taxonomy of adversaries" subsection, and §4.4 was given multi-bit methods regardless of locus |
| §7.1 multimodal section empty | **Retrieval + outline** | The outline asked for multimodal/code/audio watermarking. The writing pool had almost no such papers (the self-check notes say so), and the writer invented LR-DWM/DMark/VLA-Mark details |

## 8. Reliability

- **Claims check.** A fresh subagent re-judged 30 claims, stratified by claim_type × first-pass label. It saw only Appendix B/C, the sample, the evidence and the bibliography, and no first-pass labels.

  | Measure | Agreement | κ |
  | --- | --- | --- |
  | Five labels | 83.3% | 0.772 |
  | Binary SUPPORTED vs. not | 96.7% | 0.870 |
  | Binary NOT_SUPPORTED/CONTRADICTED vs. not | 90.0% | 0.802 |
  | Pair level, five labels (58 pairs) | 89.7% | 0.851 |
  | AutoSurvey `joint` | 100% | 1.0 |

  - **Disagreements: 5 of 30.** The first pass was stricter on 3 (2× NOT_SUPPORTED→PARTIAL, 1× CONTRADICTED→PARTIAL); the second pass was stricter on 2 (SUPPORTED→PARTIAL, NOT_SUPPORTED→CONTRADICTED).
  - **Rules involved.** As in earlier runs, they sit on the PARTIAL boundary: how much overlap counts as "some unit stated" (B.2 PARTIAL vs. NOT_SUPPORTED), and whether a mechanism that is wrong by background knowledge but not addressed in the abstract counts as CONTRADICTED.
  - **What this measures.** Both judges are claude-opus-5-5, so this is agreement between two LLM judges, not accuracy.
- **Module A runs.** The ranges are narrow. Only Structure (2–3), Relevance (3–4) and Research Gaps (3–4) varied across runs.

## 9. Limitations

- **Evidence depth.** 93.3% of pairs (376/403) were judged on the abstract only and 27 on full text. Abstract-only judging makes PARTIAL more likely for specific claims. However, most failures here are misattributions to papers on a different subject, which abstracts settle.
- **Uncertain truth values.** world_truth is `unclear` for 114 of 234 claims, so world_false_rate (26.9%) is a lower bound.
- **Unverified references.** None; all 121 IDs resolved.
- **Sample sizes.** The uncited sample had 150 sentences, with only 22 specific-factual (wide CI). The reliability sample had 30 claims.
- **Unchecked parts.**
  - No GT outline, so A3b SQS and the D3 GT-category mapping were not computed.
  - B4 (SurGE accuracy) was not run.
  - Scope labels were assigned per chapter group by different subagents. G3 labelled all of chapter 5 on_topic, including §5.5 (MLLM backdoors, jailbreak suffixes), which another judge might call adjacent.
- **Judge family.** The judge is Claude and the generator is Qwen, so there is no self-preference issue. LLM-judge rubric scores are not comparable across judge models; compare only against runs judged by claude-opus-5-5 with asg-judge v1.0.
- **Run settings.** Taken from `run_manifest.json`. No generator internals were inspected beyond the raw/refined draft files used for §7.

## 10. Files

| File | Description |
| --- | --- |
| `run.json` | Run metadata, input hashes, judge, topic definitions for C4/D3, policy |
| `progress.json` | Phase completion log |
| `parsed/sentences.jsonl` | 479 body sentences with cites, artifact and duplicate flags |
| `parsed/references.json`, `parsed/sections.json`, `parsed/tables.jsonl` | Bibliography (121), section word counts, tables (none) |
| `rubric/run{1,2,3}/A1.json`, `A2.json`, `notes.md` | Module A scores with observations, three independent runs |
| `evidence/ref_<n>.md` | 121 evidence files (corpus abstract; full-text notes for 11 refs) |
| `refs/id_lookup.json` | arXiv API / Crossref resolution results |
| `refs/references_l1.jsonl` | Module C labels per reference |
| `claims/l2_G{1..5}.jsonl` | Module B judgments, one line per cited sentence (234) |
| `claims/uncited_G{1..5}.jsonl` | B5 uncited sample (150) |
| `claims/input_G*.jsonl`, `claims/BRIEF_module_B.md`, `claims/progress_G*.json` | Subagent work packages, brief and progress |
| `structure/d1_taxonomy.json`, `d2_consistency.json`, `d4_length.json`, `scope_G*.jsonl` | Module D results and per-sentence scope labels |
| `check/input_sample.jsonl`, `second_pass.jsonl`, `agreement.json` | Reliability sample, second-judge labels, agreement |
| `metrics.json` | Every number, as {value, num, den} |
| `claims_labeled.csv`, `references_labeled.csv` | Flat tables, one row per sentence / per reference |
| `scripts/*.py` | parse_survey, setup_run, fetch_identity, build_evidence, module_c, module_d, module_d1, make_b_inputs, reliability, aggregate |
