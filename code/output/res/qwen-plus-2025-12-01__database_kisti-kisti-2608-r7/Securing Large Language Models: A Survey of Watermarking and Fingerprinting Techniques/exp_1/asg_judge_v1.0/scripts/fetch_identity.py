"""C1/C3: resolve each reference's printed ID via arXiv API / Crossref, record canonical title + first-public date."""
import json, os, re, time, urllib.request, urllib.parse, xml.etree.ElementTree as ET
RUN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
refs = json.load(open(os.path.join(RUN, "parsed/references.json")))
out_p = os.path.join(RUN, "refs/id_lookup.json")
out = json.load(open(out_p)) if os.path.exists(out_p) else {}
UA = {"User-Agent": "asg-judge-eval/1.0 (research evaluation script)"}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()
arx = [r["arxiv_id"] for r in refs if r["arxiv_id"] and r["arxiv_id"] not in out]
ns = {"a": "http://www.w3.org/2005/Atom"}
for i in range(0, len(arx), 40):
    chunk = arx[i:i+40]
    x = get("http://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": ",".join(chunk), "max_results": 100}))
    root = ET.fromstring(x)
    for e in root.findall("a:entry", ns):
        aid = re.sub(r"v\d+$", "", e.find("a:id", ns).text.rsplit("/abs/", 1)[-1])
        out[aid] = {"source": "arxiv_api", "title": re.sub(r"\s+", " ", e.find("a:title", ns).text).strip(),
                    "first_public": e.find("a:published", ns).text[:10],
                    "first_author": (e.find("a:author/a:name", ns).text if e.find("a:author/a:name", ns) is not None else None)}
    time.sleep(3)
for r in refs:
    d = r["doi"]
    if not d or d in out: continue
    try:
        m = json.loads(get("https://api.crossref.org/works/" + urllib.parse.quote(d)))["message"]
        def dp(k):
            v = m.get(k, {}).get("date-parts", [[None]])[0]
            return "-".join(f"{p:02d}" if j else str(p) for j, p in enumerate(v) if p) if v and v[0] else None
        dates = [x for x in [dp("published-online"), dp("published-print"), dp("issued"), dp("created")] if x]
        out[d] = {"source": "crossref", "title": " ".join(m.get("title", [""])), "first_public": min(dates) if dates else None,
                  "issued": dp("issued"), "type": m.get("type"), "container": " ".join(m.get("container-title", [])),
                  "first_author": (m.get("author", [{}])[0].get("family") if m.get("author") else None)}
    except Exception as ex:
        out[d] = {"source": "crossref", "error": str(ex)}
    time.sleep(0.3)
json.dump(out, open(out_p, "w"), indent=1, ensure_ascii=False)
print(len(out), "resolved;", sum(1 for v in out.values() if v.get("error")), "errors;",
      "missing arxiv:", [a for a in [r["arxiv_id"] for r in refs if r["arxiv_id"]] if a not in out])
