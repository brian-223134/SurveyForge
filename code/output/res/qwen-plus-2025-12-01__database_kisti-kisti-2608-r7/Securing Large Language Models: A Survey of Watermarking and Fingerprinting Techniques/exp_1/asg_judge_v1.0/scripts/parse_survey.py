"""Phase 1: parse the survey Markdown into sentences, sections, references (asg-judge v1.0 §5.1)."""
import json, re, sys, os
RUN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.dirname(RUN)
F = "Securing Large Language Models: A Survey of Watermarking and Fingerprinting Techniques"
md = open(os.path.join(EXP, F + ".md"), encoding="utf-8").read()
meta = json.load(open(os.path.join(EXP, "reference_metadata.json")))
refmap = json.load(open(os.path.join(EXP, F + ".json")))["reference"]  # num -> paper id

body, refs_txt = md.split("\n## References\n", 1)
CITE = re.compile(r"\[(\d+(?:\s*[;,]\s*\d+)*)\]|\[(\d+)\s*[-–]\s*(\d+)\]")
ABBR = ["e.g.", "i.e.", "et al.", "vs.", "Fig.", "Eq.", "Sec.", "Art.", "cf.", "approx.", "U.S.", "No.", "Ref.", "etc.)"]

def split_sentences(par):
    # mask inline math and abbreviations so their periods do not split
    masks = []
    def m(x):
        masks.append(x.group(0)); return f"\x00{len(masks)-1}\x00"
    t = re.sub(r"\$[^$]+\$", m, par)
    for a in ABBR:
        t = t.replace(a, a.replace(".", "\x01"))
    t = re.sub(r"(\d)\.(\d)", "\\1\x01\\2", t)
    t = t.replace("My Model!", "My Model\x02")  # paper title "Hey, That's My Model! Introducing Chain & Hash"
    parts = re.split(r"(?<=[.!?])(?:\*\*|\*)?\s+(?=[A-Z\*\"“(\[$\x00_])", t)
    out = []
    for p in parts:
        p = p.replace("\x01", ".").replace("\x02", "!")
        p = re.sub(r"\x00(\d+)\x00", lambda x: masks[int(x.group(1))], p)
        if p.strip():
            out.append(p.strip())
    return out

def cites_of(s):
    c = []
    for mm in CITE.finditer(s):
        if mm.group(1):
            c += [int(x) for x in re.split(r"\s*[;,]\s*", mm.group(1))]
        else:
            c += list(range(int(mm.group(2)), int(mm.group(3)) + 1))
    return c

def strip(s):
    s = CITE.sub("", s)
    s = re.sub(r"\(\s*;?\s*\)", "", s)
    s = re.sub(r"\s+([.,;:])", r"\1", s)
    return re.sub(r"\s{2,}", " ", s).strip()

# artifact markers: leaked refinement notes (D2)
ART = re.compile(r"(provided (papers|list|corpus)|must be (\*\*)?removed|no citation applies|Corrected subsection|"
                 r"not directly attributable to any single listed paper|lacks support|Final note:|"
                 r"is unsupported here|none support the specific technical claims|contains \*\*no citations\*\*|"
                 r"\*\*not in the provided list\*\*|is \*\*not)", re.I)

sentences, sections = [], []
cur_ch, cur_sec = None, None
sec_words = {}
sid = 0
for line in body.split("\n"):
    if line.startswith("# "):
        continue
    h = re.match(r"^(#{2,4})\s+(\d+(?:\.\d+)*)\s+(.*)", line)
    if h:
        cur_sec = f"{h.group(2)} {h.group(3).strip()}"
        sections.append({"num": h.group(2), "title": h.group(3).strip(), "level": len(h.group(1)) - 1, "words": 0})
        continue
    if not line.strip():
        continue
    text = re.sub(r"^\s*[-*]\s+", "", line)
    is_bullet = text != line
    for s in split_sentences(text):
        sid += 1
        rec = {"sid": f"S{sid:04d}", "section": cur_sec, "chapter": cur_sec.split(".")[0].split()[0],
               "text": strip(s), "cites": cites_of(s), "raw": s, "bullet": is_bullet,
               "artifact": bool(ART.search(s))}
        sentences.append(rec)
        w = len(strip(s).split())
        sections[-1]["words"] += w

# Manually verified leaked refinement notes (regex hits + neighbours reviewed by the judge, see structure/d2_notes.md)
ART_PREFIXES = [  # leaked refinement notes, reviewed by the judge (content-anchored so sids can change)
    "Vision-language alignment–preserving watermarking exemplifies the first principle—though no cited paper",
    "The reference to [21; 105] is incorrect", "Therefore, these citations are removed",
    "However, neither “LR-DWM” nor", "The only diffusion-related paper is", "Thus, citing [105]",
    "None of the provided papers address audio", "Therefore, this sentence lacks supporting citations",
    "While *Double-I Watermark* introduces", "Thus, citing [43; 106]", "Neither “WMVLM” nor",
    "*Evaluating Durability: Benchmark Insights into Multimodal Watermarking* evaluates",
    "*Proving membership in LLM pretraining data via data watermarks* uses", "Therefore, citing [20; 107]",
    "This insight is conceptual and not directly attributable", "So no citation is warranted",
    "*Securing Rag: A Risk Assessment", "So [77] is unsupported", "*Enhancing Privacy and Security in Large-Language Models",
    "So [108] is also unsupported", "Final note:", "*FT-Shield* (text-to-image", "*Evaluating Durability: Benchmark Insights into Multimodal Watermarking* (empirical",
    "*Latent Diffusion Models for Image Watermarking", "However, none support the specific technical claims",
    "Since *no provided paper supports", "Thus, the corrected subsection contains",
    "Such asymmetry violates foundational principles", "Similarly, multi-party computation (MPC)-backed protocols like [118]",
    "Crucially, unforgeability must be strengthened against *contextual exploitation*: recent work demonstrates that watermark-induced token distribution shifts can degrade safety guardrails—either attenuating protections (e.g., permitting harmful outputs) or amplifying them excessively (e.g., suppressing legitimate medical advice)—a phenomenon empirically quantified in [18]",
    "Likewise, [111] *does* explicitly", "Ethical redlines must therefore be technically enforceable: mandatory human-readable",
    "**Corrected subsection with only valid citations",
]
for r in sentences:
    r["artifact"] = any(r["raw"].startswith(p) for p in ART_PREFIXES)
    r["cites"] = list(dict.fromkeys(r["cites"]))  # drop repeated markers within a sentence

# verbatim duplicates (raw text incl. markers)
seen = {}
for r in sentences:
    k = re.sub(r"\s+", " ", r["raw"]).strip()
    r["duplicate_of"] = seen.get(k)
    seen.setdefault(k, r["sid"])

refs = []
for mm in re.finditer(r"^\[(\d+)\]\s+(.*)$", refs_txt, re.M):
    n = mm.group(1); pid = refmap[n]; md_ = meta.get(pid, {})
    arx = pid if re.match(r"^\d{4}\.\d{4,5}$", pid) else None
    doi = pid if pid.startswith("10.") else None
    refs.append({"ref_id": int(n), "printed": mm.group(2).strip(), "title": md_.get("title", mm.group(2).strip()),
                 "paper_id": pid, "arxiv_id": arx, "doi": doi, "year": (md_.get("date") or "")[:4] or None,
                 "db_date": md_.get("date")})

os.makedirs(os.path.join(RUN, "parsed"), exist_ok=True)
with open(os.path.join(RUN, "parsed/sentences.jsonl"), "w") as f:
    for r in sentences:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
json.dump(refs, open(os.path.join(RUN, "parsed/references.json"), "w"), ensure_ascii=False, indent=1)
json.dump(sections, open(os.path.join(RUN, "parsed/sections.json"), "w"), ensure_ascii=False, indent=1)
open(os.path.join(RUN, "parsed/tables.jsonl"), "w").close()  # no tables in this survey

cited = [r for r in sentences if r["cites"]]
allc = sorted({c for r in sentences for c in r["cites"]})
print(f"sentences={len(sentences)} cited={len(cited)} links={sum(len(r['cites']) for r in sentences)} "
      f"refs={len(refs)} sections={len(sections)} cited_ref_ids={len(allc)} max_cite={max(allc)} "
      f"dups={sum(1 for r in sentences if r['duplicate_of'])} artifacts={sum(r['artifact'] for r in sentences)} "
      f"bad_cites={[c for c in allc if c < 1 or c > len(refs)]} uncited_refs={[i for i in range(1,len(refs)+1) if i not in allc]}")
