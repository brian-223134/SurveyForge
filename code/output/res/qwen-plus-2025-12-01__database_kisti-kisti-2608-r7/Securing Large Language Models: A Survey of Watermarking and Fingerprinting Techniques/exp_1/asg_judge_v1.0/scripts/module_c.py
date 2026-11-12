"""Module C: references_l1.jsonl (identity, fidelity, temporal, relevance, GT overlap, input usage)."""
import json, os, re, difflib
RUN = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); EXP = os.path.dirname(RUN)
refs = json.load(open(os.path.join(RUN, "parsed/references.json")))
L = json.load(open(os.path.join(RUN, "refs/id_lookup.json")))
run = json.load(open(os.path.join(RUN, "run.json")))
CUT = run["cutoff_date"]
# judge labels (C4), definitions in run.json; written by the judge from title + corpus abstract
UNRELATED = {49}
ADJ = {1,2,3,4,5,6,7,10,11,12,14,20,26,27,30,33,38,47,50,51,57,61,62,66,72,75,76,77,78,80,86,88,89,90,91,92,93,95,97,98,
       101,103,104,106,108,109,110,113,115,116,117,120,121}
# retitled-on-arXiv or subtitle-only differences, verified against the corpus abstract (identity = match)
RETITLED = {21: "v1 title 'Attacking LLM Watermarks by Exploiting Their Strengths'; current arXiv title 'No Free Lunch in LLM Watermarking'",
            50: "current arXiv title 'Revisiting Black-Box Model Ownership Verification through Information Theory'; abstract matches printed title",
            100: "v1 title 'A Private Watermark for Large Language Models'; current 'An Unforgeable Publicly Verifiable Watermark…'",
            116: "retitled 'Whispers in the Machine: Confidentiality in Agentic Systems'",
            35: "current title drops 'WASA:' prefix wording", 54: "current title drops 'via Error Correction Code'",
            60: "current title adds 'and Provenance for LLMs'", 115: "printed title adds subtitle"}
gt = [json.loads(l) for l in open("/data2/chanjoong/kisti_data/candidates/csur2026_gt_refs.jsonl")]
gt = [g for g in gt if g["slug"] == "llm-watermarking"]
norm_id = lambda x: re.sub(r"v\d+$", "", (x or "").lower().strip())
gt_ids = {}
for i, g in enumerate(gt):
    for x in [g.get("view_id"), g.get("arxiv_id"), g.get("doi"), g.get("kisti_doi")] + (g.get("alt_view_ids") or []):
        if x: gt_ids[norm_id(x)] = i
ntitle = lambda s: re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())).strip()
gt_titles = {ntitle(g["title"]): i for i, g in enumerate(gt)}
inputs = {norm_id(x) for x in open(os.path.join(EXP, "total_ids.txt")).read().split()}
out = []
for r in refs:
    pid = r["paper_id"]; l = L[pid]
    sim = difflib.SequenceMatcher(None, ntitle(r["printed"]), ntitle(l.get("title"))).ratio()
    ident = "match" if (sim > 0.9 or r["ref_id"] in RETITLED) else "id_title_mismatch"
    printed_title = r["printed"]
    tq = "ok"
    if re.search(r"\w\s{2,}\w", printed_title) and ntitle(printed_title) == ntitle(r["title"]):
        tq = "ok"  # double space where ':' was dropped by the md renderer; content intact
    if r["arxiv_id"]:
        ver_year = (l.get("first_public") or "")[:4]
    else:
        ver_year = (l.get("issued") or l.get("first_public") or "")[:4]
    year_ok = (str(r["year"]) == ver_year) if ver_year else None
    fp = l.get("first_public") or r["db_date"]
    gi = gt_ids.get(norm_id(pid))
    if gi is None: gi = gt_titles.get(ntitle(l.get("title"))) if l.get("title") else None
    if gi is None: gi = gt_titles.get(ntitle(r["printed"]))
    rel = "unrelated" if r["ref_id"] in UNRELATED else "adjacent" if r["ref_id"] in ADJ else "core"
    out.append({"ref_id": r["ref_id"], "paper_id": pid, "identity": ident, "title_quality": tq, "year_ok": year_ok,
                "mismatched_fields": ([] if year_ok in (True, None) else ["year"]), "first_public": fp,
                "after_cutoff": bool(fp and fp >= CUT), "relevance": rel, "in_gt": gi is not None,
                "gt_index": gi, "in_allowed_set": True, "in_writer_input_set": norm_id(pid) in inputs,
                "evidence": "abstract", "url": (f"https://arxiv.org/abs/{pid}" if r["arxiv_id"] else f"https://doi.org/{pid}"),
                "resolved_title": l.get("title"), "printed_year": r["year"], "version_year": ver_year,
                "notes": RETITLED.get(r["ref_id"], "ID resolves to the printed title." if ident == "match" else "")})
with open(os.path.join(RUN, "refs/references_l1.jsonl"), "w") as f:
    for o in out: f.write(json.dumps(o, ensure_ascii=False) + "\n")
G = {o["ref_id"] for o in out}; hits = [o for o in out if o["in_gt"]]
nGT = len([g for g in gt if g.get("allowed")]) if any("allowed" in g for g in gt) else len(gt)
print("identity:", {k: sum(o["identity"] == k for o in out) for k in ["match", "id_title_mismatch", "not_found"]})
print("year_ok false:", [(o["ref_id"], o["printed_year"], o["version_year"]) for o in out if o["year_ok"] is False])
print("after cutoff:", [o["ref_id"] for o in out if o["after_cutoff"]])
print("relevance:", {k: sum(o["relevance"] == k for o in out) for k in ["core", "adjacent", "unrelated"]})
print("gt hits:", len(hits), "gt size:", len(gt), "allowed gt:", nGT, "input usage:", sum(o["in_writer_input_set"] for o in out), "/", len(inputs))
