"""D1: usage of declared taxonomies outside their declaring subsection; §4.4 placement check (judge labels)."""
import json, os, re, collections
RUN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = [json.loads(l) for l in open(os.path.join(RUN, "parsed/sentences.jsonl")) if not json.loads(l)["duplicate_of"]]
TAX = {
 "embedding_locus (§2.1)": ("2.1", r"(output|parameter|behaviou?r)[- ]space|embedding locus|\blocus\b|loci"),
 "detection_modality (§2.2)": ("2.2", r"(white|gr[ae]y|black)[- ]box"),
 "security_properties (§2.3)": ("2.3", r"unforgeab|collusion resistan|detectability"),
 "threat_axes (§2.4)": ("2.4", r"(capability|operational goal|attack surface|removal|spoofing|neutraliz|false attribution)"),
 "triaxial_adversary (§5.1)": ("5.1", r"(access modality|operational intent|knowledge assumption|triaxial)"),
}
out = {}
for name, (sec, pat) in TAX.items():
    hits = [r for r in S if re.search(pat, r["text"], re.I)]
    outside = [r for r in hits if not r["section"].startswith(sec + " ")]
    out[name] = {"declared_in": sec, "sentences_using": len(hits), "outside_declaring_section": len(outside),
                 "chapters_using": dict(collections.Counter(r["chapter"] for r in outside))}
# §4.4 is titled "Parameter-Space Watermarking"; judge classification of each named method by actual locus (from abstracts)
placement_4_4 = [
 {"ref": 82, "name": "Multi-Bit Distortion-Free Watermarking", "actual_locus": "output", "misplaced": True},
 {"ref": 83, "name": "Advancing Beyond Identification (multi-bit)", "actual_locus": "output", "misplaced": True},
 {"ref": 65, "name": "WaterMod", "actual_locus": "output", "misplaced": True},
 {"ref": 84, "name": "Invisible Entropy", "actual_locus": "output", "misplaced": True},
 {"ref": 32, "name": "Permute-and-Flip decoder", "actual_locus": "output", "misplaced": True},
 {"ref": 85, "name": "CATER", "actual_locus": "output (API text)", "misplaced": True},
 {"ref": 24, "name": "WAPITI", "actual_locus": "parameter (watermark transfer into fine-tuned weights)", "misplaced": False},
 {"ref": 55, "name": "Robust and Efficient Watermarking ... ECC", "actual_locus": "output", "misplaced": True},
]
mis = sum(p["misplaced"] for p in placement_4_4)
res = {"taxonomy_usage": out, "taxonomy_tables": "none in survey (parsed/tables.jsonl empty)",
       "placement_4_4": placement_4_4, "placement_4_4_misplaced": {"value": round(mis / len(placement_4_4), 3), "num": mis, "den": len(placement_4_4)},
       "notes": ["§2.4 declares capability × goal × surface axes; §5.1 re-declares a different 'triaxial' framework (access × intent × knowledge) for the same purpose.",
                 "Chain & Hash [36] is filed as black-box/behaviour-space (§2.2), behaviour-space ensemble (§2.5), white-box-requiring (§6.3) and verifiable inference (§7.2).",
                 "HuRef (a weight-based fingerprinting method, ref [119]) is named in §5.3 but bound to [36] and described as an attack; its own number [119] appears only inside a leaked note in §7.5."]}
json.dump(res, open(os.path.join(RUN, "structure/d1_taxonomy.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1)); print(res["placement_4_4_misplaced"])
