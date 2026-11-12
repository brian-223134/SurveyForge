# [80] Swallowing the Poison Pills: Insights from Vulnerability Disparity Among LLMs
source_url: https://arxiv.org/abs/2502.18518
arxiv_id: 2502.18518   doi: none
first_public: 2025-02-23
fetch_status: ok
printed_title: Swallowing the Poison Pills: Insights from Vulnerability Disparity Among LLMs
corpus_title: Swallowing the Poison Pills: Insights from Vulnerability Disparity Among LLMs
## abstract
Modern large language models (LLMs) exhibit critical vulnerabilities to poison pill attacks: localized data poisoning that alters specific factual knowledge while preserving overall model utility. We systematically demonstrate these attacks exploit inherent architectural properties of LLMs, achieving 54.6% increased retrieval inaccuracy on long-tail knowledge versus dominant topics and up to 25.5% increase retrieval inaccuracy on compressed models versus original architectures. Through controlled mutations (e.g., temporal/spatial/entity alterations) and, our method induces localized memorization deterioration with negligible impact on models' performance on regular standard benchmarks (e.g., <2% performance drop on MMLU/GPQA), leading to potential detection evasion. Our findings suggest: (1) Disproportionate vulnerability in long-tail knowledge may result from reduced parameter redundancy; (2) Model compression may increase attack surfaces, with pruned/distilled models requiring 30% fewer poison samples for equivalent damage; (3) Associative memory enables both spread of collateral damage to related concepts and amplification of damage from simultaneous attack, particularly for dominant topics. These findings raise concerns over current scaling paradigms since attack costs are lowering while defense complexity is rising. Our work establishes poison pills as both a security threat and diagnostic tool, revealing critical security-efficiency trade-offs in language model compression that challenges prevailing safety assumptions.
## fulltext notes (optional)
