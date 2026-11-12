"""Phase 3: evidence/ref_<n>.md from the corpus abstracts (reference_metadata.json) + ID lookup."""
import json, os, re, html
RUN = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); EXP = os.path.dirname(RUN)
refs = json.load(open(os.path.join(RUN, "parsed/references.json")))
meta = json.load(open(os.path.join(EXP, "reference_metadata.json")))
look = json.load(open(os.path.join(RUN, "refs/id_lookup.json")))
def clean(a):
    a = re.sub(r"<jats:title>.*?</jats:title>", "", a or "", flags=re.S)
    a = re.sub(r"<[^>]+>", " ", a); return re.sub(r"\s+", " ", html.unescape(a)).strip()
for r in refs:
    p = os.path.join(RUN, f"evidence/ref_{r['ref_id']}.md")
    pid = r["paper_id"]; m = meta.get(pid, {}); L = look.get(pid, {})
    ab = clean(m.get("abs"))
    url = f"https://arxiv.org/abs/{pid}" if r["arxiv_id"] else f"https://doi.org/{pid}"
    if os.path.exists(p):
        continue
    with open(p, "w") as f:
        f.write(f"# [{r['ref_id']}] {L.get('title') or r['title']}\n")
        f.write(f"source_url: {url}\n")
        f.write(f"arxiv_id: {r['arxiv_id'] or 'none'}   doi: {r['doi'] or 'none'}\n")
        f.write(f"first_public: {L.get('first_public') or m.get('date')}\n")
        f.write(f"fetch_status: {'ok' if ab else 'not_found'}\n")
        f.write(f"printed_title: {r['printed']}\n")
        f.write(f"corpus_title: {m.get('title')}\n")
        f.write("## abstract\n" + (ab or "(no abstract in corpus)") + "\n")
        f.write("## fulltext notes (optional)\n")
print("evidence files:", len(os.listdir(os.path.join(RUN, "evidence"))))
short = [(r['ref_id'], len(clean(meta.get(r['paper_id'],{}).get('abs')).split())) for r in refs]
print("abstract words <60:", [s for s in short if s[1] < 60])
