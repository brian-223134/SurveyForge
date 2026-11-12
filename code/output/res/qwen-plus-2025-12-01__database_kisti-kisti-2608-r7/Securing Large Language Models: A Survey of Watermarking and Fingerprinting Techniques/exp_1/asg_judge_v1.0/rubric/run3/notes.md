# Module A running notes, run 3

- Judge: claude-opus-5-5 | prompt: asg-judge v1.0 | elicitation: rationale_first
- Generator: SurveyForge / qwen-plus-2025-12-01 (not Claude family, so judge_generator_same_family = false)
- Input: survey .md only (body lines 1-279, references 280-523, 121 refs). No other exp_1 files were opened.
- Topic: "Securing Large Language Models: A Survey of Watermarking and Fingerprinting Techniques"

## Reading log (whole file, in chunks)
- L1-48: Title, §1 Intro (2 paragraphs), §2.1-2.5
- L49-80: §3.1-3.5
- L81-118: §4.1-4.5
- L119-170: §5.1-5.6
- L171-196: §6.1-6.5
- L197-249: §7.1-7.4
- L250-279: §7.5, §8 Conclusion
- L280-523: reference list (skimmed titles)

## Things a reader sees regardless of criterion
- §7.1 (L201-224): leaked generation notes, e.g. "no cited paper in the provided list explicitly introduces 'VLA-Mark'", "these citations are removed", "Thus, the corrected subsection contains no citations". Then L226 repeats the whole subsection, including the claims the notes had just called unsupported (VLA-Mark 98.8% AUC, LR-DWM, prosody, AST, WMVLM).
- §7.5 (L252-274): the same leak, "[117] must be removed, as that paper is not in the provided list", then "**Corrected subsection with only valid citations from the provided list:**" and a second copy of the subsection.
- §4.5 (L117): [86] is cited for about 10 different papers (Functional Invariants, ECC watermarking, WAPITI, EmbMarker, Chain & Hash, PLMmark, Waterfall, and the survey's own title "Securing Large Language Models: ..." [86]). Stray "]]" brackets.
- §3.1 (L53): "\mathbb{I}[61]" (the ref number for TimeWak, a time-series paper, sits inside the formula); [9] is cited for Kirchenbauer, KGW, ITS, BanglaLorica, SeqMark, and entropy/syntax/confidence gating.
- §8 starts "This subsection synthesizes..."
- No tables or figures anywhere.
- Repeated figures and phrases: the RTT "88% -> <13%" collapse appears 6 times (§3.5, 5.4, 5.6, 6.4, 7.3, 7.5); "longitudinal" 12 times, with "no benchmark tracks decay across fine-tuning" in §3.5, 5.6, 6.2, 6.5, 7.2, 7.4 and §8; "guard attenuation/amplification" 7 times (§5.5, 6.1, 6.4, 7.3, 7.4, 7.5, §8).
- Descriptions that are internally inconsistent or wrong (background knowledge; not used as citation evidence, flagged for Module B):
  - Chain & Hash [36] is described with "latent-space confusion zones, repetition burstiness, calibration error profiles" (§2.5), but elsewhere as hash-bound prompt-response pairs (§2.2, §7.2). In §5.3 "HuRef [36]" reuses [36].
  - PLMmark is cited as both [19] and [21], and called black-box (§3.4) and gray-box (§2.2).
  - CATER is cited as both [66] and [85].
  - §3.2 says rejection-sampling watermarks "directly resolve" the impossibility result, which contradicts §2.3 and §5.4 (impossibility is "information-theoretically inevitable").
  - §3.1 presents KGW as a "variant" of Kirchenbauer et al. (they are the same scheme).
  - §5.2 attributes homoglyph attacks to "Undetectable Watermarks" [18].
  - §4.4 says Permute-and-Flip aligns "with draft-model coordination".
  - §6.3 says "Tracing Text Provenance via Context-Aware Lexical Substitution decouples ... via Thinking/Answering Phase separation".

## Coverage (A1)
Key areas for the topic (from background knowledge): (a) output text watermarking: KGW/green-red, EXP/Aaronson, distortion-free/Kuditipudi, undetectable/Christ, SynthID, Unigram, semantic watermarks (SIR, SemStamp), multi-bit, public/private verification, low-entropy/code (SWEET); (b) attacks: paraphrase/DIPPER, scrubbing, stealing/spoofing, radioactivity, impossibility; (c) model/parameter watermarks: backdoor watermarks (EmbMarker, Double-I), weight watermarks (EmMark, functional invariants), training-data/dataset watermarks; (d) fingerprinting: intrinsic weight (HuRef, REEF, AWM), behavioral (LLMmap, provenance testing), injected backdoor fingerprints (IF, Chain & Hash), fingerprint attacks (MEraser, inhibitory); (e) evaluation/benchmarks (MarkMyWords, WaterBench, MarkLLM); (f) multimodal/code; (g) governance/regulation.
- + §3.1-3.4: KGW, EXP, GumbelSoft, SynthID, distortion-free [31], undetectable [18], ECC multi-bit, RL-learned watermark [64], WaterMod, SIR/SemaMark, CATER, PostMark, private watermark [100]: output-space is well populated.
- + §4.1-4.4: AWM, SELF, functional invariants, EmMark, EmbMarker, Instructional Fingerprinting [79], Chain & Hash, WAPITI, EverTracer. Fingerprinting gets its own chapter.
- + §5: stealing [28][29], spoofing, Bileve, inhibitory attacks [48], radioactivity [89], impossibility [39], cross-lingual [52], speculative-decoding trade-off. Attacks are covered broadly.
- + §6-7: WaterBench, WaterJudge, benchmark-contamination watermarking, regulation (EU AI Act, NIST, Daubert), equity.
- - §7.1: multimodal/code watermarking is hollow. The text admits none of its claims are supported, then restates them. Code watermarking (SWEET-type low-entropy code) gets only the STONE mention in §3.3.
- - Gaps: training-data watermarking / membership proof (only a passing mention in §7.1 notes, and contamination in §6.2); no Unigram, SemStamp, MarkMyWords, MarkLLM, REEF or LLMmap; HuRef appears once and is misdescribed. The intro is 2 paragraphs with no scope statement.
- Mapping: anchor 4 needs "most key areas comprehensively, only very minor topics left out". Multimodal/code is effectively missing and data watermarking is thin, so 4 is not fully met. Anchor 3, "generally comprehensive but misses a few key points", fits. **Score 3.**

## Structure (A1)
- + The macro order is logical: foundations/taxonomy (§2) -> output-level (§3) -> model-centric (§4) -> attacks (§5) -> evaluation (§6) -> extensions/governance (§7) -> conclusion. The tripartite locus taxonomy (§2.1) does organize §3 and §4.
- - §2.4 (threat model, 3 axes) and §5.1 (triaxial adversarial framework) are near-duplicate taxonomies.
- - Evaluation is treated in §3.5, §5.6, §6.1-6.5, §7.3 and §7.4, with the same longitudinal and RTT points repeated; §6.4 and §7.3 overlap (human-centred evaluation, equity).
- - §4.4 is titled "Parameter-Space Watermarking" but discusses output-space multi-bit schemes (Multi-bit distortion-free, WaterMod, Invisible Entropy, PF decoder, CATER), so the declared taxonomy is not used consistently.
- - §7.1 and §7.5 contain leaked correction notes plus duplicate copies of the subsection, which leaves them internally incoherent. §8 calls itself "This subsection". The intro has no roadmap.
- - Transitions are formulaic cross-references ("as foreshadowed in the prior subsection", "directly leveraged in the subsequent") rather than real links.
- Mapping: anchor 3 ("generally reasonable logical structure, most content orderly, ... repeated subsections") is fully met at the macro level. Anchor 4 ("good logical consistency, natural transitions") fails because of the duplication, the leaked notes and the §4.4 mismatch. I considered 2 because of the leaked-note subsections, but they are 2 of about 32 subsections and the overall framework is clear. **Score 3.**

## Relevance (A1)
- + Nearly all of §2-§6 is about LLM watermarking, fingerprinting and attacks on them.
- + The governance material (§7.2, §7.5) bears on the topic (forensic admissibility, dual use).
- - §5.5: BadToken and AnyDoor (MLLM backdoor attacks) and universal adversarial jailbreak suffixes [91] are presented as watermark attack vectors. These are digressions.
- - §7.1 and §7.5: large blocks of meta-text about which citations are "in the provided list" are not survey content at all. §7.1 also drifts into diffusion and audio watermarking with no LLM tie.
- - The reference list includes off-topic items cited in the text (e.g. [49] device fingerprinting, [61] TimeWak time series, [51] unlearning vs obfuscation; "Securing RAG" [77] cited for weight-space fingerprinting in §4.1).
- - Generic governance padding (UNESCO, "epistemic exclusion") dilutes focus in places.
- Mapping: anchor 4 needs "consistent relevance with infrequent digressions". The leaked meta-text blocks plus the §5.5 digressions break the "clear focus". Between 3 and 4, so choose the lower. **Score 3.**

## Synthesis (A1)
- + §2.2 maps detection modality onto embedding locus. §2.3 links watermark unforgeability to fingerprint collision resistance. §2.4 crosses threat axes with security properties. This is an attempt at a unified frame ("provenance assurance stack/calculus").
- + §5.2 identifies a recurring pattern: detection needs statistical deviation while spoofing needs only mimicry. §5.4 reframes radioactivity as both a defence and an attack surface. §3.4 relates semantic invariance to certified robustness.
- - Many connections are asserted without grounding: §2.5 says "the convergence is mathematically precise", with KL over a product space and Chain & Hash fused with confusion zones; §3.3 gives a "risk-proportional embedding constraint" formula that no study states. Under the protocol these lineages do not count.
- - Cross-references are formulaic and repeated, which links sections but adds no explanation of patterns.
- - Some syntheses rest on misdescribed studies (PLMmark with ZKP/MPC, Waterfall as non-autoregressive), and the framework is contradicted in places (§3.2 vs §2.3/§5.4 on impossibility; §4.4 vs the locus taxonomy).
- Mapping: anchor 4 needs "most studies synthesised into coherent themes". Themes exist, but too many links are unsupported or contradictory. Anchor 3 ("some thematic relationships but lacks a unified framework to explain their significance") fits better, since the declared framework is rhetorical rather than explanatory. **Score 3.**

## Critical Analysis (A1)
- + §5.6 gives specific critique of evaluation practice: synthetic token edits versus human paraphrase, composite attacks, longitudinal blindness, missing low-resource testing.
- + §2.1/§2.2 note the limits of each locus (output-space is non-radioactive; white-box is infeasible for APIs); §4.1 notes spectral fingerprints degrade below INT4; §4.2 notes key-leakage vulnerability; §4.5 notes formal guarantees that assume static white-box models.
- + §5.4 critiques the radioactivity assumption.
- - The critique is mostly at paradigm level and repeated; individual key studies are rarely critiqued in reasoned detail. Much of it relies on specific numbers that look unanchored (e.g. "-18.3% GPT-4-Judge", "42-68% latency penalty").
- - It is inconsistent: §3.2 claims rejection sampling resolves the impossibility while §5.4 says removal is inevitable; §4.5's critique is self-referential ("Chain & Hash vulnerable to attacks uncovered in Chain & Hash").
- - Many subsections end in "Future work must..." (9 times).
- Mapping: the critique is more than "occasional" (2) but not a systematic critique of most key studies (4), and it is inconsistent in depth and correctness, so anchor 3. **Score 3.**

## Objective Clarity (A2)
- + §1 para 1 separates watermarking/fingerprinting from safety, privacy and alignment, and defines them as provenance primitives.
- + §1 para 2 gives a three-part motivation (economic, legal, societal) and the active/passive distinction.
- - There is no explicit objective, research questions, scope, contribution list or roadmap. "As we synthesize across over 50 foundational works" is the only scope cue, and the thesis "unified provenance assurance stack" stands in for an objective.
- - The intro is only 2 paragraphs; background on how the field developed is absent.
- Mapping: anchor 4 needs a clear objective with somewhat brief background. Here the objective is only implicit (title plus thesis) and both background and motivation are thin. Anchor 3 ("objective is present, but background and motivation lack depth") fits. **Score 3.**

## Classification-Evolution Coherence (A2)
- + §2.1 output/parameter/behavior locus taxonomy, §2.2 white/gray/black-box spectrum, §2.4 threat axes; §3 and §4 follow the locus split.
- + Some evolution narrative: §3.2 "evolved from heuristic statistical modulation toward cryptographic ... learning", §4.4 "from static ... to adaptive", §3.4 "from heuristic resilience to principled".
- - Categories are used inconsistently: §4.4 places output-space methods under parameter-space; Bileve and Chain & Hash are called behavior-space; PLMmark is black-box in one place and gray-box in another; Functional Invariants is called "trigger-free neuron-level watermarking" in §4.2.
- - There is no chronology (no years, no milestone sequence), and the evolution is described as abstract shifts.
- Mapping: anchor 3 "classification somewhat vague, evolution partially clear; some categories overlap or are not used consistently" matches exactly. **Score 3.**

## Dataset & Metric Coverage (A2)
- + §6.1 metric taxonomy: TPR/FPR, p-value calibration, AUROC, minimum token length, BER, perplexity vs LLM-judge, safety violation rate. Scattered mentions of BLEU, ROUGE-L, FID, MOS and ECE.
- + Benchmarks named: WaterBench, WaterJudge, benchmark-contamination watermarking (ARC-Easy/MMLU), "Dual Attribution Benchmark"; datasets named in passing: GLUE, HumanEval, TruthfulQA, SafetyBench.
- - No dataset is described (scope, size, domain). There is no table, and the standard text-watermark eval corpora/benchmarks (C4 RealNewsLike, MarkMyWords, MarkLLM) are missing.
- - MUSE is presented as a watermark-decay benchmark and "JailbreakBench-inspired" stress testing is vague, so the descriptions are unreliable.
- Mapping: anchor 4 needs fairly detailed dataset descriptions, which are not here. Anchor 3 ("limited set, descriptions lack detail") fits. Metrics alone are richer, but datasets are thin. **Score 3.**

## In-depth Comparison (A2)
- + Paradigm-level trade-offs: §2.1/§2.2 (access needed, robustness, deployability per locus/modality); §4.2-4.3 contrast backdoor, weight-space and behavior-space niches; §3.4 semantic invariance versus formal certificates.
- + §6.3 compares operational costs (DeepTextMark >100MB vs multi-bit <1MB, SynthID vs speculative decoding, PostMark post-hoc).
- - There is no comparison table and no consistent dimensions applied across methods; method-level comparisons are scattered and the numbers are unanchored.
- - Within §3.1-3.3 and §5.2-5.3, methods are mostly described one after another.
- Mapping: anchor 4 needs a clear comparison of the major advantages and disadvantages of the methods. The paradigm-level contrast is fairly clear, but the method-level comparison is scattered, so it sits between 3 and 4 and takes the lower. **Score 3.**

## Critical Analysis, DeepSurvey-Bench (A2)
- + Several "why" explanations: low-entropy text gives low green-list coverage, hence weak detection (§3.1); tokenizer segmentation explains RTT failure (§3.1, §5.2); semantic anchoring survives paraphrase because it does not depend on surface form (§3.4); detection/spoofing asymmetry (§5.2); why white-box methods fail for APIs (§2.1).
- - Several explanations are technically wrong or contradictory (rejection sampling "inheriting robustness" against Unicode normalization in §3.2; Permute-and-Flip and draft models in §4.4; the §3.2/§5.4 impossibility contradiction), so they are not "technically grounded".
- - Much of the explanation is abstract ("crack between layers", "adversarial epistemology").
- Mapping: anchor 4 needs meaningful interpretation, with some explanations staying high level. The errors and contradictions undercut "meaningful", so anchor 3 ("basic analytical comments ... superficial"). **Score 3.**

## Research Gaps (A2)
- + Multiple gaps identified: longitudinal persistence (§3.5, 5.6, 6.2, 6.5, 7.2, 7.4), cross-lingual/low-resource (§5.6, 6.4, 7.3), composite attacks (§5.6), no formal model of structural collusion resistance (§5.3), cross-axis stress testing (§2.4), human-centred metrics (§6.4), p-value calibration across modalities (§2.2), formal guarantees versus operational settings (§2.3, §4.5).
- + §5.6 gives reasons for its gaps (iid noise assumptions, attackers chaining operations).
- - The analysis is repeated rather than deepened, and some gap claims are grounded on dubious statistics. It also admits that parameter/behavior neutralization is "underexplored in the provided literature" (§2.4, leaked).
- Mapping: anchor 4 ("several research gaps, analysis somewhat limited in depth") is met. Anchor 5 needs comprehensive, deeply analysed gaps, which is not the case. **Score 4.**

## Future Work (A2)
- + Directions appear in most subsections and are tied to gaps: cross-modality information flow and detection-latency lower bounds (§2.2), cross-axis stress tests (§2.4), semantic codes inside smoothed detectors (§3.4), SDE/persistent-homology weight-drift fingerprints (§4.1), composable assurance contracts (§4.5), version-aware decay curves (§6.2, 6.5), vLLM-aware verification (§5.5), jurisdiction-aware descriptors (§7.2).
- - Feasibility is almost never discussed. Several directions are buzzword-level ("adversarial epistemology", "regulatory temporal logic", "verifiably non-instrumentalizable"), and the conclusion lists blockchain trails and ZKPs generically.
- Mapping: anchor 4 needs "some discussion of feasibility", which is absent. Anchor 3 ("broad and lack an in-depth discussion of forward-looking value or feasibility") fits, though some directions are more specific than "broad". **Score 3.**
