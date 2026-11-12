"""Module D (D2 repetition/artifacts, D4 length profile). D1 and D3 labels are merged in aggregate.py."""
import json, os, re, statistics, itertools, collections
RUN = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); EXP = os.path.dirname(RUN)
F = "Securing Large Language Models: A Survey of Watermarking and Fingerprinting Techniques"
md = open(os.path.join(EXP, F + ".md")).read()
S = [json.loads(l) for l in open(os.path.join(RUN, "parsed/sentences.jsonl"))]
secs = json.load(open(os.path.join(RUN, "parsed/sections.json")))
refs = json.load(open(os.path.join(RUN, "parsed/references.json")))
words = lambda t: set(re.findall(r"[a-z0-9]+", t.lower()))
# D2 repetition
exact = [(r["sid"], r["duplicate_of"]) for r in S if r["duplicate_of"]]
near = []
W = {r["sid"]: words(r["text"]) for r in S}
for a, b in itertools.combinations(S, 2):
    if b["duplicate_of"] == a["sid"] or a["duplicate_of"] or b["duplicate_of"]: continue
    A, B = W[a["sid"]], W[b["sid"]]
    if len(A) < 6 or len(B) < 6: continue
    j = len(A & B) / len(A | B)
    if j >= 0.8: near.append({"a": a["sid"], "b": b["sid"], "jaccard": round(j, 3)})
# math/code brackets turned into citations
math_cites = []
for m in re.finditer(r"(\\mathbb\{I\}\[\d+\]|\$\[\d+\]\$|\\Pr\[\d+\]|‘\[\d+\]’|using a \$\[\d+\]\$)", md):
    math_cites.append(m.group(0))
# same number reused for different named papers in §4.5 ([86])
sec45 = md.split("### 4.5")[1].split("## 5")[0]
named86 = re.findall(r"\*([^*]+)\*\s*\[86\]", sec45)
double_br = re.findall(r"\[\d+\]\]", md)
self_cite = [t for t in named86 if "Securing Large Language Models" in t] + re.findall(r"\*Securing Large Language Models[^*]*\*", sec45)
artifacts = [r["sid"] for r in S if r["artifact"]]
art_words = sum(len(r["text"].split()) for r in S if r["artifact"])
dup_words = sum(len(r["text"].split()) for r in S if r["duplicate_of"])
d2 = {"exact_duplicates": exact, "near_duplicates_jaccard_ge_0.8": near,
      "leaked_generation_notes": {"sids": artifacts, "n": len(artifacts), "words": art_words},
      "duplicate_words": dup_words,
      "math_brackets_as_citations": math_cites,
      "citation_number_reused_for_distinct_named_papers": {"marker": "[86]", "section": "4.5", "named_papers": named86,
            "ref_86_actual_title": refs[85]["title"]},
      "double_bracket_markers": double_br,
      "self_citation_of_survey_title": bool(self_cite),
      "placeholders": re.findall(r"(TODO|TBD|\[citation needed\]|XX+)", md)}
json.dump(d2, open(os.path.join(RUN, "structure/d2_consistency.json"), "w"), indent=1, ensure_ascii=False)
# D4 length profile
body = [r for r in S if not r["duplicate_of"]]
tw = sum(len(r["text"].split()) for r in S)
links = sum(len(r["cites"]) for r in S)
sub = [s for s in secs if s["level"] == 2 or (s["level"] == 1 and s["words"] > 0)]
sub_w = [s["words"] for s in secs if s["level"] == 2]
per_sub_cites = collections.defaultdict(int)
for r in S: per_sub_cites[r["section"].split()[0]] += len(r["cites"])
ch = collections.defaultdict(int)
for s in secs: ch[s["num"].split(".")[0]] += s["words"]
d4 = {"total_words_body": tw, "sections": secs, "words_per_chapter": dict(ch),
      "subsection_words_mean": round(statistics.mean(sub_w), 1), "subsection_words_sd": round(statistics.stdev(sub_w), 1),
      "subsection_words_cv": round(statistics.stdev(sub_w) / statistics.mean(sub_w), 3), "n_subsections": len(sub_w),
      "subsection_words_mean_excl_7.1": round(statistics.mean([s["words"] for s in secs if s["level"] == 2 and s["num"] != "7.1"]), 1),
      "subsection_words_sd_excl_7.1": round(statistics.stdev([s["words"] for s in secs if s["level"] == 2 and s["num"] != "7.1"]), 1),
      "citation_links": links, "citations_per_1000_words": round(1000 * links / tw, 2),
      "median_citations_per_subsection": statistics.median([per_sub_cites[s["num"]] for s in secs if s["level"] == 2]),
      "citations_per_subsection": {s["num"]: per_sub_cites[s["num"]] for s in secs if s["words"] > 0},
      "config_subsection_len_target": 500,
      "sentences": len(S), "words_per_sentence_mean": round(tw / len(S), 1)}
json.dump(d4, open(os.path.join(RUN, "structure/d4_length.json"), "w"), indent=1, ensure_ascii=False)
print("near dups", near); print("math cites", math_cites); print("[86] papers", len(named86), named86[:12]); print("double", double_br)
print({k: v for k, v in d4.items() if k not in ("sections", "citations_per_subsection")})
