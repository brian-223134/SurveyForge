import json, hashlib, os, datetime
RUN = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); EXP = os.path.dirname(RUN)
F = "Securing Large Language Models: A Survey of Watermarking and Fingerprinting Techniques"
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
run = {
  "run_id": "surveyforge_qwen-plus_kisti-r7_llm-watermarking_2026-11",
  "survey_file": os.path.join(EXP, F + ".md"), "survey_sha256": h(os.path.join(EXP, F + ".md")),
  "survey_pdf_sha256": h(os.path.join(EXP, F + ".pdf")),
  "topic": F, "topic_id": "llm-watermarking",
  "generator": "SurveyForge (KISTI fork, kisti branch) / qwen-plus-2025-12-01 @ DashScope, temperature 0.6",
  "judge_model": "claude-opus-5-5", "judge_generator_same_family": False,
  "prompt_version": "asg-judge v1.0", "elicitation": "rationale_first",
  "date": str(datetime.date.today()),
  "modules": ["A1", "A2", "B", "C", "D"],
  "module_A_repeats": 3,
  "search_policy": "limited",
  "search_policy_note": "Evidence = corpus abstracts (reference_metadata.json, KISTI view kisti-2608-r7). Web use limited to arXiv/Crossref ID lookups for C1 and a small number of arXiv full-text checks for Module B.",
  "evidence_dir": os.path.join(EXP, "reference_metadata.json") + " (abstracts per paper id)",
  "gt_survey": {"refs": "/data2/chanjoong/kisti_data/candidates/csur2026_gt_refs.jsonl (slug llm-watermarking, 211 refs, 209 before cutoff)",
                 "outline": None, "gt_doi": "10.1145/3773028"},
  "allowed_set": "KISTI view kisti-2608-r7 allowed set under retrieval policy (1,666,650 ids, fingerprint 675fdac8...); run_manifest.reference_violations = []",
  "writer_input_set": os.path.join(EXP, "total_ids.txt") + " (433 ids, writing-stage retrieval pool)",
  "cutoff_date": "2026-02-04",
  "uncited_sample": 150,
  "relevance_definitions": {
    "core": "Watermarking, fingerprinting, provenance/ownership verification or source attribution of LLMs / language models, their generated text, or their training data — including attacks on, and evaluations/benchmarks of, such schemes.",
    "adjacent": "The broader area but not the topic: watermarking/fingerprinting of non-language models or media (DNN classifiers, diffusion/image models), non-watermark AI-text detection, general LLM security/privacy/safety/alignment/copyright/governance, membership inference, LLM trustworthiness benchmarks.",
    "unrelated": "Not about ML security, LLMs or content provenance at all (e.g., domain applications of LLMs with no security/provenance angle)."
  },
  "scope_definitions_D3": {
    "on_topic": "Sentence is about watermarking/fingerprinting/provenance of LLMs, their outputs or data (incl. attacks, evaluation, deployment, governance of such schemes).",
    "adjacent": "About watermarking of other modalities/models, or LLM security/privacy/regulation generally, without a watermark/fingerprint link.",
    "off_topic": "Unrelated to the topic."
  },
  "excluded_from_rates": "verbatim duplicates (duplicate_of != null). Leaked refinement notes (artifact=true) are judged and included in main rates; an excluding-artifacts variant is also reported.",
}
json.dump(run, open(os.path.join(RUN, "run.json"), "w"), indent=1, ensure_ascii=False)
json.dump({"phase0": "done", "phase1_parse": "done"}, open(os.path.join(RUN, "progress.json"), "w"), indent=1)
print("ok")
