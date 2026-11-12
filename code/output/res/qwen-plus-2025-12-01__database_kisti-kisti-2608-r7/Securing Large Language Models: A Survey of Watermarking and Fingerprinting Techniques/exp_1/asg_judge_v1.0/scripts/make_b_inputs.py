"""Prepare Module B work packages: cited claims, stratified uncited sample (B5), and D3 scope items per group."""
import json, os, random, math, collections
RUN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = [json.loads(l) for l in open(os.path.join(RUN, "parsed/sentences.jsonl"))]
GROUPS = {"G1": ["1", "2"], "G2": ["3", "4"], "G3": ["5", "8"], "G4": ["6"], "G5": ["7"]}
N_UNCITED = 150
unc = [r for r in S if not r["cites"] and not r["duplicate_of"]]
by = collections.defaultdict(list)
for r in unc: by[r["chapter"]].append(r)
# largest-remainder proportional allocation by chapter
quota = {c: N_UNCITED * len(v) / len(unc) for c, v in by.items()}
alloc = {c: math.floor(q) for c, q in quota.items()}
for c in sorted(quota, key=lambda c: -(quota[c] - alloc[c]))[: N_UNCITED - sum(alloc.values())]:
    alloc[c] += 1
rng = random.Random(20261111)
sample = set()
for c, v in by.items():
    sample |= {r["sid"] for r in rng.sample(v, alloc[c])}
prev = {}
for i, r in enumerate(S):
    prev[r["sid"]] = S[i - 1]["text"] if i and S[i - 1]["section"] == r["section"] else None
for g, chs in GROUPS.items():
    with open(os.path.join(RUN, f"claims/input_{g}.jsonl"), "w") as f:
        for r in S:
            if r["chapter"] not in chs: continue
            role = "duplicate" if r["duplicate_of"] else "claim" if r["cites"] else ("uncited_sample" if r["sid"] in sample else "scope_only")
            f.write(json.dumps({"sid": r["sid"], "section": r["section"], "role": role, "text": r["text"], "raw": r["raw"],
                                "cites": r["cites"], "artifact": r["artifact"], "duplicate_of": r["duplicate_of"],
                                "prev_sentence": prev[r["sid"]]}, ensure_ascii=False) + "\n")
    rows = [json.loads(l) for l in open(os.path.join(RUN, f"claims/input_{g}.jsonl"))]
    print(g, collections.Counter(x["role"] for x in rows), "pairs", sum(len(x["cites"]) for x in rows if x["role"] == "claim"))
print("uncited alloc", alloc, sum(alloc.values()))
