# Module A running notes — run 2 (judge claude-opus-5-5, asg-judge v1.0, rationale_first)

Survey: "Securing Large Language Models: A Survey of Watermarking and Fingerprinting Techniques" (SurveyForge / qwen-plus-2025-12-01).
Body = lines 1-279 (§1-§8), references from line 280. ~18.7k words total file incl. references.
Read in chunks: L1-48 (§1-§2), L49-80 (§3), L81-118 (§4), then §5-§8.

## Chunk log (raw observations, tagged by criterion)

### §1 Introduction (L3-7)
- [Obj] Two paragraphs. States motivation (economic IP, legal mandates EU AI Act/GDPR, societal misuse) and the active (watermark) vs passive (fingerprint) distinction. No explicit research questions, no scope statement, no contribution list, no paper roadmap. "over 50 foundational works" claimed.
- [Rel] Opens by distinguishing WM/FP from safety, privacy, alignment — on topic.
- [Style] Heavy rhetoric ("not ... but", "provenance assurance stack"), padding.

### §2 Foundations & taxonomy (L9-47)
- [Struct/CEC] 2.1 tripartite locus taxonomy (output / parameter / behavior); 2.2 detection modality (white/gray/black-box); 2.3 four security properties (detectability, robustness, unforgeability, collusion resistance); 2.4 threat model 3 axes (capability, goal, surface); 2.5 convergence. Clear explicit taxonomy axes, cross-referenced to each other.
- [Struct] 2.4 threat taxonomy is substantially repeated in §5.1 (taxonomy of adversarial capabilities) — check.
- [Leak] 2.4 L35: "remain underexplored in the provided literature: no cited paper substantiates concrete neutralization mechanisms ... we refrain from speculative claims" — generation note leaked to reader.
- [Synth] 2.3 links impossibility result [39] to properties; draws parallel "watermark unforgeability mirrors fingerprint collision resistance". 2.5 argues convergence via ensemble/adaptive/modular principles — attempt at framework, but supporting claims look fabricated: Chain & Hash [36] described as fusing "latent-space confusion zones, repetition burstiness, calibration error profiles" (that is not Chain & Hash); PLMmark [19] "embeds zero-knowledge proofs within MPC ... satisfying GDPR Article 32"; ECC multibit papers [54][55] combining "acrostic constraints, sensorimotor norm deviations". Note for Module B; for Synthesis this means the framework is partly built on misattributed connections.
- [Crit] 2.1 notes output-space fragility (paraphrase, speculative decoding, homoglyph), parameter-space needs white-box. 2.2 notes black-box statistical limits. Reasonably specific limitations, though some sourced oddly ([21] cited for many unrelated claims; PLMmark cited as both [19] and [21]).
- [Cov] Covers KGW-style green list, distortion-free (Kuditipudi [31]), Chain&Hash, WASA, ZKROWNN, Hufu, EmbMarker, WAPITI, functional invariants, SLIM, Bileve, impossibility (Zhang et al. "Watermarks in the sand" [39]).

### §3 Output-level watermarking (L49-79)
- [Cov] 3.1 green-list/KGW, EXP, GumbelSoft, tokenizer issues; 3.2 cryptographic/undetectable (rejection sampling), ECC multi-bit, end-to-end learned, WaterMod; 3.3 adaptive/semantic (SemaMark, SIR, EWD, alignment resampling); 3.4 robustness/black-box (lexical substitution, CATER, PLMmark, IPCert); 3.5 eval (WaterBench, WaterJudge, speculative decoding, cross-lingual).
- [Cov-gap] No dedicated treatment of Aaronson/Gumbel-max scheme origins, Christ et al. undetectable WM by name, SynthID-Text (deployed), Unigram-WM, SWEET (code), publicly-detectable WM; post-hoc AI-text detectors (DetectGPT etc.) as comparison baseline absent (arguably peripheral). Watermark stealing / spoofing (Jovanović et al.) only implicitly.
- [Citation collapse] 3.1: [9] cited for Kirchenbauer, KGW, ITS, BanglaLorica, entropy-aware, syntactic gating, confidence scaling, SeqMark — single ref for ~8 different works. Leaked bracket refs inside math: "\mathbb{I}[61]", "$[63]$ linear code". 
- [Rel/accuracy] 3.2 claims rejection sampling "directly resolves the 'Watermarks in the Sand' impossibility result [37]" — contradicts §2.3 where the same impossibility is [39] and is a general limit. Internal inconsistency.
- [Synth] 3.2 frames an evolution: statistical -> cryptographic -> ECC multi-bit -> end-to-end learned; explicit "motivated by limitations exposed in preceding subsection". 3.4 links semantic invariance to certified guarantees "fundamental tension: only randomized smoothing and ECC yield formal certificates" — a genuine synthesized point.
- [Crit] 3.1 tokenizer/low-entropy fragility; 3.4 tension empirical vs formal robustness; 3.5 critiques over-indexing on detectability, scarcity of longitudinal studies. Many specific numbers (AUROC 0.92->0.58, -18.3% GPT-4-judge, >42% throughput penalty, 88.2%->9.7%) that look unverifiable/fabricated; critique is specific in form.
- [DMC] 3.5: WaterBench, WaterJudge, MUSE mentioned; metrics: p-value, AUROC, F1, perplexity, ROUGE-L, LLM-as-judge, TruthfulQA, SafetyBench, HumanEval (4.4), GLUE (4.2). Mentions but little description of datasets themselves (no C4/OpenGen/RealNewsLike etc.).
- [Comp] 3.4: "only randomized smoothing and ECC yield formal certificates" vs semantic invariance — explicit contrast. 2.1/2.2 compare loci/modalities by access, robustness. No tables.

### §4 Model-centric (L81-117)
- [CEC] 4.1 weight-space (passive, training-free), 4.2 backdoor-based (fine-tuning), 4.3 behavior-space (black-box), 4.4 adaptive/multi-layer parameter-space, 4.5 formal security & governance.
- [Struct/CEC problem] 4.4 "parameter-space watermarking" discusses multi-bit text watermarking (MPAC [83], WaterMod [65], Invisible Entropy [84], Permute-and-Flip decoder [32], CATER [85]) — these are output-level/decoding methods, already covered in §3; misplaced, duplicates §3.2/3.4 (WaterMod, CATER, ECC 98.4% stat repeated). Category not used consistently.
- [Accuracy] 4.1 AWM [57] described in detail; 4.2 "trigger-free neuron-level watermarking pioneered by [22]" — [22] is Functional Invariants elsewhere; inconsistent. 4.2 quoted prompt contains leaked "[80]".
- [Leak/broken] 4.5: nearly every citation is [86], including the survey's own title "Securing Large Language Models: A Survey of Watermarking and Fingerprinting Techniques [86]"; stray "]]"; "Chain & Hash ... vulnerable to ... attacks uncovered in Chain & Hash [86]" (circular). Reader-visible generation breakage. Also "satisfying the Daubert standard" asserted for an ECC paper.
- [Crit] 4.1 limitations (INT4 quantization, pruned models); 4.2 key leakage, side-channels; 4.5 "formal security ... largely aspirational", white-box/static-model assumptions violated in practice. Specific but sometimes unsupported.
- [Synth] 4.2/4.3 explicitly position backdoor vs behavior-space niches ("when training control is available" vs "when only queries are accessible") — good comparison.
- [Cov] Model fingerprinting: covers instructional fingerprinting (IF [79]), Chain&Hash, weight-similarity (AWM), EmbMarker, Hide-and-Seek, but missing/thin: HuRef, REEF, model-merging fingerprint robustness (e.g., MergePrint), TRAP, LLMmap, ProFLingo, dataset/training-data watermarking & membership (data provenance, "radioactive" data is in §5.4?), copyright of training data (e.g. dataset inference) — check later.

### §5 Robustness & attacks (L119-169)
- [Struct] 5.1 "triaxial adversarial framework" (access, intent, knowledge) re-proposes the 3-axis threat taxonomy of 2.4 (capability, goal, surface) with overlapping content (white/gray/black-box, green-list stealing via MIP, distillation spoofing). Same topic treated in two chapters.
- [Cov] 5.2 scrubbing/paraphrase, lexical substitution, spoofing (watermark stealing [28], MIP stealing [29], Bileve); 5.3 erasure/neutralization/collusion (inhibitory attacks [48], dummy-neuron [27], HuRef, EverTracer); 5.4 radioactivity & distillation; 5.5 speculative sampling, alignment degradation, MLLM; 5.6 evaluation methodology gaps.
- [Accuracy, Module B note] [28] Watermark Stealing described as "recursive rewriting framework" and as "third-party black-box insertion ... via synonym chains"; [18] Undetectable Watermarks described as homoglyph attack; WAPITI [88] as an erasure attack (elsewhere [24] a watermark transfer method); HuRef cited as [36] (= Chain&Hash); DeepSigns called behavior-space PLM technique. Pervasive misattribution undermines comparisons/critique.
- [Rel] 5.5 digressions: universal adversarial suffix jailbreak [91], BadToken / AnyDoor MLLM backdoor attacks [92][93] — not watermark attacks; Signal Watermark FFT audio leakage.
- [Synth] 5.2/5.4 articulate a recurring asymmetry (detection needs significance, spoofing/removal needs mimicry; O(n) vs O(1)); 5.4 reframes radioactivity as attack surface — genuine cross-study pattern. 5.3 "structural collusion resistance" gap synthesized.
- [Crit] 5.6 methodical critique of evaluation: synthetic perturbations vs human paraphrasing, composite attacks absent from benchmarks, longitudinal blindness, BLEU/perplexity insufficiency, low-resource testing. Specific and reasoned (though numbers dubious and repeated: "88% to <13%" RTT stat appears in 5.4, 5.6, 6.4, 7.5 x2, and as 88.2%->9.7% in 3.5).
- [Gaps] 5.3 formal models of structural collusion resistance; 5.6 composite attacks, temporal fidelity curves, participatory validation.

### §6 Evaluation (L171-195)
- [Struct] 6.1 eval taxonomy re-covers 3.5 (holistic assessment beyond detection accuracy; same "dangerous myopia" opening sentence nearly verbatim in 3.5 and 6.1). Longitudinal gap restated in 3.5, 5.6, 6.2, 6.5, 7.2, 7.4, §8.
- [DMC] 6.1: metric taxonomy in 4 dimensions (detection: p-value calibration, min detectable length, AUROC w/ CIs; quality: perplexity insufficiency, GPT-4-judge, human fluency; alignment-aware robustness; payload: BER). Reasoned rationale for metric choice — strongest DMC content. 6.2: WaterBench, MUSE, MEraser, "Dual Attribution Benchmark", benchmark contamination watermarking on ARC-Easy/MMLU, "JailbreakBench-inspired stress-testing", WaterPool. Descriptions are one-clause, no scope/size/task details; no MarkMyWords, MarkLLM toolkit, C4/OpenGen datasets standard in WM evaluation.
- [Comp] 6.3 compares operational costs: SynthID-Text overhead, WaterMax latency, DeepTextMark >100MB vs MPAC <1MB, Private Watermark ZKP latency, Chain&Hash white-box requirement, post-hoc black-box watermark. Closest thing to a cross-method comparison, but ad hoc, no table, numbers unverifiable. Contradiction: Chain&Hash "requires white-box access" (6.3) vs black-box ownership proof "without model access" (2.2).
- [Accuracy] 6.5: Waterfall [60] "proposes JSON-LD schemas"; 6.3: lexical substitution paper [34] does "Thinking/Answering phase separation"; watermark-conditioned diffusion [101] "bidirectional neighbor biasing" for non-AR LMs. Fabricated-looking.
- [Leak] 6.5 "\Pr[104]" bracket citation inside math.
- [Crit] 6.1 "no single dimension suffices"; 6.4 human-centered and linguistic-equity gaps; dual-use surveillance risk. 
- [Future] 6.2 version-aware decay curves; 6.4 tripartite augmentation (participatory assessment, RTT-as-baseline, misuse impact modeling); 6.5 version-aware evaluation datasets.

### §7 Cross-domain & governance (L197-274)
- [Struct/Rel — severe] 7.1 (~1,300 words): after the intro paragraph, ~850 words of leaked citation-verification notes visible to the reader ("The reference to [21; 105] is incorrect here ... Therefore, these citations are removed", "None of the provided papers address audio...", "Final note: The only papers in the list...", "Thus, the corrected subsection contains no citations"). Then the full original paragraph is repeated (L226) with the claims the notes just said were unsupported (VLA-Mark 98.8% AUC, LR-DWM, DMark, audio MOS, AST code WM, WMVLM) now uncited. The subsection admits its multimodal/code/audio content is unsupported by its corpus.
- [Struct/Rel — severe] 7.5: draft with inline verification notes ("the citation '[117]' must be removed, as that paper is not in the provided list"; "this citation is correct and retained"), followed by "**Corrected subsection with only valid citations from the provided list:**" and a second version. Two versions of the same subsection in the text.
- [Struct] 4.5 (noted above): citations collapse to [86] incl. survey's own title.
- [Cov] 7.2 regulation (EU AI Act Art. 52, NIST AI RMF, Daubert), Chain&Hash, ZKROWNN, WASA; 7.3 equity; 7.4 system integration (PostMark, WaterMax, PRIVMARK, ReasonMark, DualGuard, MEraser); 7.5 dual-use ethics. Governance coverage is broad (peripheral topics present).
- [Accuracy] 7.2 "WASA's JSON-LD-encoded source-attribution payloads"; 7.4 PRIVMARK cited as [26] (=ZKROWNN); "GPT-5 and Gemini 2.5 Pro" detection claim.
- [Crit] 7.2 gap: no formal model of longitudinal decay, disparity across registers; 7.3 linguistic inequity/false attribution; 7.5 dual-use (surveillance, coercive licensing via radioactivity). Mostly normative, some reasoning.
- [Future] 7.2 regulatory temporal logic, jurisdiction-aware descriptors; 7.4 watermark-as-contract with verified latency bounds; 7.1 co-embedding spaces.

### §8 Conclusion (L276-278)
- Single paragraph, starts "This subsection synthesizes" (generation artifact). Introduces new numbers (92% -> <15%, -37% safety, -29% helpfulness) and new claims; "Inevitable Trade-off theorem [9]" and "SynthID-Text [9]" (same [9] used for KGW, BanglaLorica etc.); "PRIVMARK [2]" (earlier [2] = privacy mechanism). Restates convergence thesis and longitudinal gap; future: ZKPs, blockchain trails, human-centered eval.

## Cross-cutting
- Citation collapse: [9] used for ~10 distinct works; [21] for PLMmark, public-key signatures, ensemble watermarking, low-resource failure, ensemble inhibition, calibrated-noise attacks; [86] for all of 4.5. Bracket refs leaked into math (L53, L59, L195) and a quoted prompt (L91).
- Internal contradictions: "Watermarks in the Sand" impossibility = [39] in 2.3/5.4 but [37] in 3.2 where rejection sampling "resolves" it; 2.3 says no watermark is strongly robust and undetectable, 3.2 says crypto paradigm inherits robustness against those attacks.
- Rhetorical padding pervasive ("paradigm shift" ~10x, "not merely ... but", "Crucially"), counted against depth per ground rule 5.

## Coverage key-area checklist (background knowledge of the field)
Present with discussion: KGW green-list & variants; distortion-free (Kuditipudi), undetectable (Christ et al.) mentioned; multi-bit/ECC (MPAC, ECC papers); semantic/robust WM (SIR, SemaMark); entropy-adaptive (EWD, adaptive); post-hoc/black-box WM (lexical substitution, PostMark); impossibility (Zhang et al.); watermark stealing/spoofing; radioactivity/distillation; paraphrase attacks (DIPPER mentioned only in §8); speculative sampling trade-off; alignment degradation; WaterBench/WaterJudge; model WM (EmbMarker, functional invariants, EmMark, WAPITI); fingerprinting (Instructional FP, Chain&Hash, AWM weight-similarity, HuRef mentioned, inhibitory attacks); governance/regulation; equity.
Thin / missing: training-data / dataset watermarking and copyright-data provenance (only incidental: contamination watermarking in 6.2, data-watermark membership paper named only inside leaked notes); code watermarking (SWEET etc.) only in an uncited, self-flagged paragraph; multimodal (7.1 hollow by its own admission); publicly-detectable / asymmetric schemes only one sentence; fingerprinting families thin (no REEF, LLMmap/TRAP-style query fingerprinting, merge-robust fingerprints); SynthID-Text deployment only named; relation to post-hoc AI-text detection not discussed; Aaronson/Gumbel scheme origins not explained.

## Per-criterion passes (one at a time; evidence -> anchor -> score)

### A1 Coverage
For: broad map of output WM (§3), model-centric WM/FP (§4), attacks (§5), evaluation (§6), governance/ethics (§7); peripheral topics (regulation, equity, speculative decoding) present.
Against: fingerprinting families thin; data/training-set watermarking essentially absent; multimodal/code/audio (7.1) declared in outline but self-admittedly unsupported; SynthID/public-detectability only named.
Anchor: 4 needs "most key areas comprehensively, only very minor topics left out" — data watermarking and fingerprinting depth are not very minor. 3 "generally comprehensive but misses a few key points" fully holds. -> 3.

### A1 Structure
For: clean macro-outline (taxonomy -> output -> model-centric -> attacks -> eval -> governance); explicit forward/backward transitions.
Against: 7.1 and 7.5 contain leaked verification notes and two versions of the same subsection; 4.5 citation collapse incl. self-citation; 4.4 places output-level methods under parameter-space; 2.4 vs 5.1 duplicate threat taxonomy; 3.5 vs 6.1 duplicate eval opening; conclusion opens "This subsection".
Anchor: 3's "most content orderly ... repeated subsections" partially fits, but 2's "some content arranged in a disordered or unreasonable manner" is literally true for 7.1/7.5/4.4/4.5. Sits between 2 and 3 -> lower -> 2.

### A1 Relevance
For: nearly all sections about LLM WM/FP.
Against: reader-visible meta-commentary about citations (7.1, 7.5) is off-topic content; jailbreak suffixes, MLLM backdoors (5.5), RAG/ZKP privacy (7.1); many sentences misattributed so content is not reliably about the cited work.
Anchor: 4 requires "infrequent digressions" — ~1,500 words of meta notes plus scattered digressions exceed infrequent. 3 "generally on topic, despite a few unrelated details" holds. -> 3.

### A1 Synthesis
For: §2 cross-linked axes (locus x modality x properties x threats); recurring detection-vs-removal asymmetry (5.2, 5.4); radioactivity reframed (5.4); empirical vs certified robustness tension (3.4); backdoor vs behavior niche (4.2/4.3).
Against: the headline "convergence" thesis (2.5, §8) rests on misattributed descriptions (Chain&Hash, PLMmark, ECC "acrostic/sensorimotor"); many links are rhetorical "foreshadowing/echoing" cross-refs, not substantive; same synthesized point repeated rather than developed.
Anchor: 4 "most studies into coherent themes or debates" — studies are grouped by paradigm but the integrating claims are unreliable; 3 "some thematic relationships but lacks a unified framework" — it does attempt a framework, but it is declared more than demonstrated. Between 3 and 4 -> 3.

### A1 Critical Analysis
For: paradigm-level limits stated (2.1, 2.2, 4.1, 4.5); 5.6 is a reasoned critique of evaluation methodology; 6.4/7.3 equity critique.
Against: individual studies rarely critiqued — they are usually reported with (unverifiable) success numbers; critique repeated (longitudinal gap x7, RTT stat x6); internal contradictions (impossibility [37]/[39]); many future-work lists.
Anchor: 4 "systematically critiques most key studies" — no, critique is of paradigms not most key studies, and inconsistent. 3 "sporadic ... shallow or inconsistent" fits. -> 3.

### A2 Objective Clarity
§1 only two paragraphs: motivation (economic/legal/societal) is decent; active vs passive distinction given; but no explicit objective statement, research questions, scope, contribution list or roadmap. Objective is inferred ("we synthesize across over 50 foundational works ... provenance assurance stack").
Anchor 4 needs "objective is clear" — it is implicit, not specific. 3 "objective present, background and motivation lack depth" — background is compressed into one paragraph. -> 3.

### A2 Classification-Evolution Coherence
Classification explicit (2.1 locus, 2.2 modality, 2.4 threats) and drives §3/§4. But categories not used consistently: 4.4 output-level methods under parameter-space; PLMmark called black-box (3.4), gray-box (2.2), parameter-space (2.1); Chain&Hash black-box (2.2) vs white-box (6.3). Evolution only in 3.2 (statistical -> crypto -> ECC -> learned) and 4.4 framing; no chronology elsewhere.
Anchor 3 "somewhat vague ... some categories overlap or are not used consistently" literal fit; 4 needs "relatively clear ... few gaps". -> 3.

### A2 Dataset & Metric Coverage
Metrics: many named, 6.1 gives reasoned metric taxonomy. Datasets/benchmarks: WaterBench, WaterJudge, MUSE, MEraser, ARC-Easy/MMLU, GLUE, HumanEval, TruthfulQA, SafetyBench — named in passing, no scope/size details; standard WM eval datasets and toolkits (C4, MarkMyWords, MarkLLM) absent.
Anchor 4 "description of each dataset is fairly detailed" fails. 3 "limited set ... descriptions lack detail" fits. -> 3.

### A2 In-depth Comparison
Paradigm-level comparison along access/robustness/deployability (2.1, 2.2, 4.2-4.3); 3.4 formal vs empirical; 6.3 cost comparisons. No tables, no consistent dimensions across methods, method-level comparisons scattered and numbers unverifiable/misattributed.
Anchor 4 "clear comparison of major advantages and disadvantages" — paradigm level yes, method level no; 3 "scattered or shallow" fits method level. Between -> 3.

### A2 Critical Analysis (DSB)
Explains some why: output signals not radioactive because confined to text (2.1); detectors assume i.i.d. tokens (5.1); tokenizer segmentation explains RTT failure (3.1); ECC/smoothing give certificates where semantics cannot (3.4); O(n) detection vs O(1) removal (5.1). But many explanations are fabricated-specific (WaterMax latency due to draft caching, 6.3) or contradictory (3.2 vs 2.3).
Anchor 4 "meaningful analytical interpretation ... some explanations high level" — partially; reliability issues. 3 "basic analytical comments ... superficial" — more than basic in places. Between -> 3.

### A2 Research Gaps
Several gaps: longitudinal persistence (3.5, 5.6, 6.2, 6.5, 7.2), composite attacks absent from benchmarks (5.6), structural collusion resistance (5.3), cross-axis stress testing (2.4), low-resource/linguistic equity (6.4, 7.3), formal security aspirational for model-centric (4.5), cross-modality p-value calibration (2.2). Some reasoning (5.6 explains why synthetic perturbations underestimate). Depth limited, heavy repetition, and the longitudinal gap claim conflicts with studies it cites (Mark Your LLM, MUSE, WAPITI decay).
Anchor 4 "several research gaps, analysis somewhat limited in depth" holds. 5 needs comprehensive + deep + grounded — no. -> 4.

### A2 Future Work
Many directions, fairly specific: cross-axis stress testing (2.4), trajectory-aware benchmarks (3.5, 6.2), semantically invariant codes inside smoothed detectors (3.4), SDE/persistent homology for weight drift (4.1), game-theoretic fingerprint persistence (5.3), vLLM-aware verification (5.5), regulatory temporal logic / jurisdiction-aware descriptors (7.2), watermark-as-contract (7.4). Derived from stated gaps, but almost no feasibility discussion; some speculative (blockchain trails, persistent homology).
Anchor 4 requires "some discussion of feasibility" — essentially absent for the proposed directions. 3 "broad and lack in-depth discussion of forward-looking value or feasibility" — feasibility clause fits though directions are not all broad. Between -> 3.
