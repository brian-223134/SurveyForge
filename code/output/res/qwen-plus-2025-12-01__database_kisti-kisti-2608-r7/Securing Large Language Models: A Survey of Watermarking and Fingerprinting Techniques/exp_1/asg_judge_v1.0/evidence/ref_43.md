# [43] WaterMax: breaking the LLM watermark detectability-robustness-quality trade-off
source_url: https://arxiv.org/abs/2403.04808
arxiv_id: 2403.04808   doi: none
first_public: 2024-03-06
fetch_status: ok
printed_title: WaterMax: breaking the LLM watermark detectability-robustness-quality trade-off
corpus_title: WaterMax: breaking the LLM watermark detectability-robustness-quality trade-off
## abstract
Watermarking is a technical means to dissuade malfeasant usage of Large Language Models. This paper proposes a novel watermarking scheme, so-called WaterMax, that enjoys high detectability while sustaining the quality of the generated text of the original LLM. Its new design leaves the LLM untouched (no modification of the weights, logits, temperature, or sampling technique). WaterMax balances robustness and complexity contrary to the watermarking techniques of the literature inherently provoking a trade-off between quality and robustness. Its performance is both theoretically proven and experimentally validated. It outperforms all the SotA techniques under the most complete benchmark suite. Code available at https://github.com/eva-giboulot/WaterMax.
## fulltext notes (optional)
- [G1 judge, arxiv.org/html/2403.04808] Sect. 3: "The performance does not depend on the length of the text." Power formulas at fixed false-alarm rate (Prop. 4.1, 5.1); no token-count lower bound. Mechanism: generate n drafts/chunks, keep text with lowest p-value. No error-correcting codes or ensembles (codes only in related work, App. A.2).
