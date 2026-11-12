# Module A run 1 notes (judge: claude-opus-5-5, asg-judge v1.0; survey text only, before any evidence was read)

## Coverage (vs requested topic)
- §3.1–3.4: output watermarking covered: green-list/KGW, Gumbel/EXP, distortion-free (Kuditipudi), ECC multi-bit, semantic (SemaMark, SIR), post-hoc lexical substitution, certified (IPCert). Depth is uneven and padded with numbers.
- §4.1–4.4: model watermarking/fingerprinting: weight-space (AWM, functional invariants), backdoor/instructional fingerprinting, EmbMarker, behaviour-space; multi-bit.
- §5.x: attacks: stealing/spoofing, paraphrase/RTT scrubbing, inhibition attacks on fingerprints, radioactivity/distillation, speculative sampling trade-off.
- §6.x: evaluation (WaterBench, WaterJudge, contamination detection), operational constraints.
- Gaps: §7.1 multimodal is effectively empty (half is leaked citation-check notes, the rest uncited and presented as fact); code watermarking (only uncited AST paragraph), public detectability / publicly verifiable schemes thin, data watermarking / dataset-ownership only in passing, no treatment of standard benchmarks like MarkMyWords, no history of DNN watermarking beyond one citation, no discussion of non-watermark detection as the alternative baseline. Unbiased/reweighting family barely named.

## Structure
- Declared tripartite locus taxonomy (§2.1) actually organizes ch.3 (output), ch.4 (parameter/behaviour), §5.2–5.3 (attacks by locus). +
- Near-duplicate subsections: threat taxonomy in §2.4 and again §5.1 (same three axes); evaluation gaps in §3.5, §5.6, §6.1–6.5; equity/human-centred in §6.4 and §7.3; "longitudinal decay gap" repeated in §3.5, 5.6, 6.2, 6.5, 7.2, 7.4, 8.
- §7.1 and §7.5 contain leaked refinement notes ("must be removed", "Corrected subsection with only valid citations") and then repeat the whole subsection; disorderly locally.
- Conclusion opens with "This subsection synthesizes"; transitions are formulaic ("as the following subsection…") and sometimes point to the wrong place.
- Macro order (foundations → output → model-centric → attacks → evaluation → governance) is reasonable.

## Relevance
- Nearly every paragraph is about watermarking/fingerprinting of LLMs. +
- Digressions: governance/legal rhetoric (EU AI Act articles, Daubert, UNESCO) in §7.2/7.5; leaked meta-notes about the survey's own citation list (§7.1, §7.5) are not about the topic at all.
- Intro opens with safety/privacy/alignment contrast — fine as framing.

## Synthesis
- Repeated framework (locus × detection modality × security property) is used to connect ch.2–5; cross-references between subsections are frequent. +
- Many connections are asserted, not derived: "convergence is mathematically precise" product-space KL (§2.5), "risk-proportional embedding constraint" (§2.5), "provenance assurance calculus"; lineages like "WaterMod refines end-to-end differentiable watermarking" (§3.2).
- Patterns identified: paraphrase/RTT fragility across schemes, speculative-decoding conflict, radioactivity as double-edged (§5.4) — genuine themes but stated rather than built from compared results.

## Critical Analysis
- Limitations named: white-box infeasible for APIs (§2.2), backdoor needs training control and key leakage (§4.2), spectral fingerprints degrade below INT4 (§4.1), evaluation uses synthetic perturbations not human paraphrase (§5.6), composite attacks missing from benchmarks (§5.6).
- Critique of specific studies is sporadic; most "future work must" paragraphs are generic; the same gap (longitudinal) is restated ~7 times rather than analysed.
- Several critical claims are internally inconsistent (e.g., §3.2 says rejection sampling "resolves" the Watermarks-in-the-Sand impossibility; §5.4 says removal is "information-theoretically inevitable").

## A2 notes
- Objective clarity: §1 has motivation (economic/legal/societal) but no explicit scope, research questions, contributions, comparison with prior surveys, or roadmap. "over 50 foundational works".
- Classification–evolution: locus classification clear; evolution only rhetorical ("evolved from heuristic to cryptographic"); categories overlap (Chain & Hash labelled black-box, behaviour-space, verifiable inference, white-box in different places §2.2/§4.5/§6.3; HuRef appears as an attack in §5.3).
- Datasets/metrics: metrics listed in §6.1 (TPR/FPR, AUROC, BER, perplexity, GPT-4-judge, BLEU); benchmarks named (WaterBench, WaterJudge, MUSE, contamination detection on ARC-Easy/MMLU, GLUE, HumanEval, TruthfulQA) but none described in scope/size/protocol; no table.
- Comparison: no comparison table; trade-offs discussed per modality (§2.2), per paradigm (§4.2 vs §4.1/4.3), certified vs semantic (§3.4). Scattered.
- Critical analysis (why methods differ): some mechanistic reasons (semantic anchoring vs token-level, key-gated vs passive) but mostly high-level.
- Gaps: longitudinal decay, cross-lingual, composite attacks, structural collusion resistance, human-centred evaluation — listed, repeated, little analysis of why they persist.
- Future work: many directions (cross-axis stress testing §2.4, SDE / persistent homology §4.1, version-aware decay curves §6.2, jurisdiction-aware descriptors §7.2, assurance contracts §4.5/7.4) — broad, feasibility not discussed.
