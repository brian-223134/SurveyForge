"""§9: draw the 30-claim check sample (mode=sample) or compute agreement (mode=agree)."""
import json, os, glob, random, sys, collections
RUN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(RUN, *a)
jl = lambda p: [json.loads(l) for l in open(p) if l.strip()]
S = {r["sid"]: r for r in jl(P("parsed/sentences.jsonl"))}
L2 = {}
for f in glob.glob(P("claims/l2_G*.jsonl")):
    for r in jl(f): L2[r["sid"]] = r
first = {s: r for s, r in L2.items() if not S[s]["duplicate_of"]}
if sys.argv[1] == "sample":
    strata = collections.defaultdict(list)
    for s, r in sorted(first.items()): strata[(r["claim_type"], r["sentence_support"])].append(s)
    rng = random.Random(30); pick = []
    keys = sorted(strata, key=lambda k: -len(strata[k]))
    # proportional with at least one per stratum, round-robin until 30
    pools = {k: rng.sample(v, len(v)) for k, v in strata.items()}
    while len(pick) < 30 and any(pools.values()):
        for k in keys:
            if pools[k] and len(pick) < 30: pick.append(pools[k].pop())
    with open(P("check/input_sample.jsonl"), "w") as f:
        for s in sorted(pick):
            f.write(json.dumps({"sid": s, "text": S[s]["text"], "raw": S[s]["raw"], "cites": S[s]["cites"], "section": S[s]["section"]}, ensure_ascii=False) + "\n")
    print(len(pick), collections.Counter((first[s]["claim_type"], first[s]["sentence_support"]) for s in pick))
else:
    sec = {r["sid"]: r for r in jl(P("check/second_pass.jsonl"))}
    sids = [s for s in sec if s in first]
    def kappa(a, b):
        n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
        ca, cb = collections.Counter(a), collections.Counter(b)
        pe = sum(ca[k] * cb[k] for k in set(a) | set(b)) / (n * n)
        return round(po, 4), (round((po - pe) / (1 - pe), 4) if pe < 1 else 1.0)
    A = [first[s]["sentence_support"] for s in sids]; B = [sec[s]["sentence_support"] for s in sids]
    order = {"SUPPORTED": 4, "PARTIAL": 3, "NEI": 2, "NOT_SUPPORTED": 1, "CONTRADICTED": 0}
    dis = []
    for s, a, b in zip(sids, A, B):
        if a != b: dis.append({"sid": s, "first": a, "second": b, "stricter": "second" if order[b] < order[a] else "first"})
    f5 = kappa(A, B); fs = kappa([x == "SUPPORTED" for x in A], [x == "SUPPORTED" for x in B])
    fu = kappa([x in ("NOT_SUPPORTED", "CONTRADICTED") for x in A], [x in ("NOT_SUPPORTED", "CONTRADICTED") for x in B])
    # pair level too
    pa, pb = [], []
    for s in sids:
        p1 = {p["ref"]: p["support"] for p in first[s]["pairs"]}; p2 = {p["ref"]: p["support"] for p in sec[s].get("pairs", [])}
        for k in p1:
            if k in p2: pa.append(p1[k]); pb.append(p2[k])
    out = {"n": len(sids), "five_label": {"agreement": f5[0], "kappa": f5[1]},
           "binary_supported": {"agreement": fs[0], "kappa": fs[1]}, "binary_unsupported": {"agreement": fu[0], "kappa": fu[1]},
           "pair_five_label": dict(zip(["agreement", "kappa"], kappa(pa, pb))) | {"n_pairs": len(pa)},
           "disagreements": dis, "stricter_counts": dict(collections.Counter(d["stricter"] for d in dis)),
           "label_pairs": dict(collections.Counter(f"{d['first']}->{d['second']}" for d in dis))}
    json.dump(out, open(P("check/agreement.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
