"""Phase 8: aggregate everything into metrics.json, claims_labeled.csv, references_labeled.csv."""
import json, os, glob, math, csv, collections, statistics
RUN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(RUN, *a)
jl = lambda p: [json.loads(l) for l in open(p) if l.strip()]
run = json.load(open(P("run.json")))
S = jl(P("parsed/sentences.jsonl")); SID = {r["sid"]: r for r in S}
def V(num, den): return {"value": round(num / den, 4) if den else None, "num": num, "den": den}
def wilson(k, n, z=1.96):
    if not n: return None
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 4), round((c + h) / d, 4)]
M = {"run": run}
# ---- rubric
rub = {}
for mod in ["A1", "A2"]:
    runs = {}
    for f in sorted(glob.glob(P("rubric/run*/" + mod + ".json"))):
        for o in json.load(open(f)):
            runs.setdefault(o["criterion"], []).append(o["score"])
    rub[mod] = {c: {"scores": s, "mean": round(statistics.mean(s), 2), "range": [min(s), max(s)],
                    "scale": "1-5"} for c, s in runs.items()}
a2 = json.load(open(P("rubric/run1/A2.json")))
dims = collections.defaultdict(list)
for o in a2: dims[o["dimension"]].append(o["criterion"])
rub["A2_dimensions"] = {d: round(statistics.mean(rub["A2"][c]["mean"] for c in cs), 3) for d, cs in dims.items()}
rub["A2_overall_mean"] = round(statistics.mean(v["mean"] for v in rub["A2"].values()), 3)
rub["A2_select"] = rub["A2_overall_mean"] >= 4
rub["A1_mean"] = round(statistics.mean(v["mean"] for v in rub["A1"].values()), 3)
rub["judge_model"] = run["judge_model"]; rub["prompt_version"] = run["prompt_version"]; rub["n_runs"] = len(glob.glob(P("rubric/run*/A1.json")))
M["rubric"] = rub
# ---- claims
L2 = []
for f in sorted(glob.glob(P("claims/l2_G*.jsonl"))): L2 += jl(f)
L2 = {r["sid"]: r for r in L2}
judged = [L2[s] for s in sorted(L2) if not SID[s]["duplicate_of"]]
def strict(rows, tag):
    n = len(rows); pairs = [p for r in rows for p in r["pairs"]]
    cnt = collections.Counter(r["sentence_support"] for r in rows)
    pc = collections.Counter(p["support"] for p in pairs)
    syn = [r for r in rows if r["claim_type"] == "synthesis"]
    two = collections.Counter(f"{r['world_truth']}|{r['sentence_support']}" for r in rows)
    out = {"n_judged": n, "n_pairs": len(pairs),
        "recall_strict": V(cnt["SUPPORTED"], n), "recall_strict_ci": wilson(cnt["SUPPORTED"], n),
        "recall_lenient": V(cnt["SUPPORTED"] + cnt["PARTIAL"], n),
        "precision_strict": V(pc["SUPPORTED"], len(pairs)), "precision_lenient": V(pc["SUPPORTED"] + pc["PARTIAL"], len(pairs)),
        "major_rate": V(sum(r.get("severity") == "major" for r in rows), n),
        "world_false_rate": V(sum(r["world_truth"] == "false" for r in rows), n),
        "contradiction_rate": V(cnt["CONTRADICTED"], n), "nei_rate": V(cnt["NEI"], n),
        "synthesis_support": V(sum(r["sentence_support"] == "SUPPORTED" for r in syn), len(syn)),
        "sentence_label_counts": dict(cnt), "pair_label_counts": dict(pc),
        "error_types": dict(collections.Counter(p.get("error_type") for p in pairs if p["support"] != "SUPPORTED")),
        "by_claim_type": {t: dict(collections.Counter(r["sentence_support"] for r in rows if r["claim_type"] == t)) for t in sorted({r["claim_type"] for r in rows})},
        "by_chapter": {c: dict(collections.Counter(r["sentence_support"] for r in rows if SID[r["sid"]]["chapter"] == c)) for c in sorted({SID[r["sid"]]["chapter"] for r in rows}, key=int)},
        "two_axis": dict(two),
        "evidence_depth_pairs": dict(collections.Counter(p.get("evidence") for p in pairs)),
        "misattribution_with_alt_ref": sum(1 for p in pairs if p.get("error_type") == "misattribution" and p.get("alt_ref"))}
    return out
M["citation_strict"] = strict(judged, "all")
M["citation_strict"]["excluding_artifacts"] = {k: v for k, v in strict([r for r in judged if not SID[r["sid"]]["artifact"]], "noart").items()
                                              if k in ("n_judged", "recall_strict", "recall_lenient", "precision_strict", "major_rate", "world_false_rate", "contradiction_rate")}
# B2
n = len(judged); joint = sum(bool(r["autosurvey"]["joint"]) for r in judged)
tot = sum(len(SID[r["sid"]]["cites"]) for r in judged)
rel = sum(1 for r in judged if r["autosurvey"]["joint"] for p in r["autosurvey"].get("per_ref", []) if p.get("relevant"))
R = joint / n; Pp = rel / tot
any_single = sum(1 for r in judged if any(p.get("alone") for p in r["autosurvey"].get("per_ref", [])) or (r["autosurvey"]["joint"] and len(SID[r["sid"]]["cites"]) == 1))
M["citation_autosurvey"] = {"citation_recall_autosurvey": V(joint, n), "citation_precision_autosurvey": V(rel, tot),
                            "citation_f1": round(2 * Pp * R / (Pp + R), 4) if Pp + R else 0,
                            "note": "AutoSurvey Eq.2-3 definition; NLI judged by claude-opus-5-5 on corpus abstracts."}
M["citation_surge"] = {"status": "not run (B4 optional, not in modules)"}
# B5
U = []
for f in sorted(glob.glob(P("claims/uncited_G*.jsonl"))): U += jl(f)
body = [r for r in S if not r["duplicate_of"]]
unc_all = [r for r in body if not r["cites"]]
words = sum(len(r["text"].split()) for r in S)
sf = [u for u in U if u["content_type"] == "specific_factual"]
sf_false = sum(u["world_truth"] == "false" for u in sf); sf_unclear = sum(u["world_truth"] == "unclear" for u in sf)
M["uncited"] = {"share_uncited_body_sentences": V(len(unc_all), len(body)),
    "citations_per_1000_words": round(1000 * sum(len(r["cites"]) for r in S) / words, 2),
    "sample_n": len(U), "content_type_counts": dict(collections.Counter(u["content_type"] for u in U)),
    "specific_factual_error_rate": V(sf_false, len(sf)), "specific_factual_error_rate_ci": wilson(sf_false, len(sf)),
    "specific_factual_unclear": V(sf_unclear, len(sf)), "error_rate_is_lower_bound": sf_unclear > 0,
    "needs_citation": V(sum(bool(u.get("needs_citation")) for u in U), len(U)),
    "overreach_among_interpretive_general": V(sum(bool(u.get("overreach")) for u in U if u["content_type"] in ("interpretive", "general_claim")),
                                              sum(u["content_type"] in ("interpretive", "general_claim") for u in U))}
# C
C = jl(P("refs/references_l1.jsonl")); nC = len(C)
gt = [json.loads(l) for l in open("/data2/chanjoong/kisti_data/candidates/csur2026_gt_refs.jsonl")]
gt = [g for g in gt if g["slug"] == "llm-watermarking"]
hits = sum(c["in_gt"] for c in C)
gt_cut = sum(1 for g in gt if g.get("allowed", True))
cited_core_by_ch = {}
for ch in sorted({r["chapter"] for r in S}, key=int):
    ids = {c for r in S if r["chapter"] == ch for c in r["cites"]}
    cited_core_by_ch[ch] = V(sum(1 for c in C if c["ref_id"] in ids and c["relevance"] == "core"), len(ids))
M["references"] = {
    "n_refs": nC, "identity": {k: V(sum(c["identity"] == k for c in C), nC) for k in ["match", "id_title_mismatch", "not_found", "unverified_budget"]},
    "hallucinated_refs_L1a": V(sum(c["identity"] in ("id_title_mismatch", "not_found") for c in C), nC),
    "title_quality": dict(collections.Counter(c["title_quality"] for c in C)),
    "year_ok": V(sum(c["year_ok"] is True for c in C), sum(c["year_ok"] is not None for c in C)),
    "after_cutoff": V(sum(c["after_cutoff"] for c in C), nC), "cutoff_date": run["cutoff_date"],
    "relevance_llm_surveyx": V(sum(c["relevance"] in ("core", "adjacent") for c in C), nC),
    "core_share": V(sum(c["relevance"] == "core" for c in C), nC), "relevance_counts": dict(collections.Counter(c["relevance"] for c in C)),
    "core_share_by_chapter_cited": cited_core_by_ch,
    "gt_overlap": {"hits": hits, "gt_size_published": len(gt), "gt_before_cutoff": gt_cut,
                   "iou_surveyx": V(hits, len(gt) + nC - hits), "gt_recall_surge": V(hits, len(gt)),
                   "gt_recall_cutoff_pool": V(hits, gt_cut),
                   "ref_coverage_surveyforge_single_gt": V(hits, nC),
                   "label": "SAM-R (single-GT): G' = all 121 refs (all dated before GT publication 2026-02-04)"},
    "input_usage": V(sum(c["in_writer_input_set"] for c in C), len(open(os.path.join(os.path.dirname(RUN), "total_ids.txt")).read().split()))}
# D
d1 = json.load(open(P("structure/d1_taxonomy.json"))); d2 = json.load(open(P("structure/d2_consistency.json"))); d4 = json.load(open(P("structure/d4_length.json")))
SC = {}
for f in sorted(glob.glob(P("structure/scope_G*.jsonl"))):
    for r in jl(f): SC[r["sid"]] = r["scope"]
scope_rows = [SC[r["sid"]] for r in body if r["sid"] in SC]
sc_cnt = collections.Counter(scope_rows)
M["structure"] = {"D1": {"taxonomy_usage": d1["taxonomy_usage"], "placement_4_4_misplaced": d1["placement_4_4_misplaced"], "notes": d1["notes"]},
    "D2": {"exact_duplicates": len(d2["exact_duplicates"]), "near_duplicates": len(d2["near_duplicates_jaccard_ge_0.8"]),
           "duplicate_words": d2["duplicate_words"], "leaked_note_sentences": V(d2["leaked_generation_notes"]["n"], len(S)),
           "leaked_note_words": d2["leaked_generation_notes"]["words"], "math_brackets_as_citations": d2["math_brackets_as_citations"],
           "reused_marker_86_distinct_papers": len(set(d2["citation_number_reused_for_distinct_named_papers"]["named_papers"])),
           "double_bracket_markers": d2["double_bracket_markers"], "placeholders": d2["placeholders"]},
    "D3": {"n_labeled": len(scope_rows), "on_topic": V(sc_cnt["on_topic"], len(scope_rows)), "adjacent": V(sc_cnt["adjacent"], len(scope_rows)),
           "off_topic": V(sc_cnt["off_topic"], len(scope_rows)), "gt_category_coverage": "not computed: GT outline not available"},
    "D4": {k: d4[k] for k in d4 if k not in ("sections",)}}
# reliability
if os.path.exists(P("check/agreement.json")):
    M["reliability"] = json.load(open(P("check/agreement.json")))
M["reliability_moduleA"] = {mod: {c: v["range"] for c, v in rub[mod].items()} for mod in ["A1", "A2"]}
json.dump(M, open(P("metrics.json"), "w"), indent=1, ensure_ascii=False)
# CSVs
with open(P("claims_labeled.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["sid", "section", "chapter", "cites", "artifact", "duplicate_of", "role", "claim_type", "sentence_support", "world_truth", "severity",
                                   "pair_labels", "error_types", "autosurvey_joint", "content_type", "uncited_world_truth", "scope", "rationale", "text"])
    UD = {u["sid"]: u for u in U}
    for r in S:
        l = L2.get(r["sid"], {}); u = UD.get(r["sid"], {})
        w.writerow([r["sid"], r["section"], r["chapter"], ";".join(map(str, r["cites"])), r["artifact"], r["duplicate_of"] or "",
                    "claim" if r["cites"] else ("uncited_sample" if u else "uncited"), l.get("claim_type", ""), l.get("sentence_support", ""), l.get("world_truth", ""),
                    l.get("severity", "") or "", ";".join(f"{p['ref']}:{p['support']}" for p in l.get("pairs", [])),
                    ";".join(str(p.get("error_type")) for p in l.get("pairs", []) if p["support"] != "SUPPORTED"),
                    l.get("autosurvey", {}).get("joint", ""), u.get("content_type", ""), u.get("world_truth", ""), SC.get(r["sid"], ""),
                    l.get("rationale", "") or u.get("rationale", ""), r["text"]])
with open(P("references_labeled.csv"), "w", newline="") as f:
    keys = list(C[0].keys()); w = csv.DictWriter(f, fieldnames=keys + ["printed"]); w.writeheader()
    pr = {r["ref_id"]: r["printed"] for r in json.load(open(P("parsed/references.json")))}
    for c in C: w.writerow({**c, "printed": pr[c["ref_id"]]})
print(json.dumps({"rubric_A1": {k: v["mean"] for k, v in rub["A1"].items()}, "A2": {k: v["mean"] for k, v in rub["A2"].items()},
                  "strict": {k: M["citation_strict"][k] for k in ["n_judged", "recall_strict", "recall_lenient", "precision_strict", "major_rate", "world_false_rate", "contradiction_rate", "nei_rate"]},
                  "autosurvey": M["citation_autosurvey"], "uncited": M["uncited"], "D3": M["structure"]["D3"]}, indent=1))
