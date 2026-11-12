# [32] Permute-and-Flip: An optimally stable and watermarkable decoder for LLMs
source_url: https://arxiv.org/abs/2402.05864
arxiv_id: 2402.05864   doi: none
first_public: 2024-02-08
fetch_status: ok
printed_title: Permute-and-Flip  An optimally robust and watermarkable decoder for LLMs
corpus_title: Permute-and-Flip  An optimally robust and watermarkable decoder for LLMs
## abstract
In this paper, we propose a new decoding method called Permute-and-Flip (PF) decoder. It enjoys robustness properties similar to the standard sampling decoder, but is provably up to 2x better in its quality-robustness tradeoff than sampling and never worse than any other decoder. We also design a cryptographic watermarking scheme analogous to Aaronson's Gumbel watermark, but naturally tailored for PF decoder. The watermarking scheme does not change the distribution to sample, while allowing arbitrarily low false positive rate and high recall whenever the generated text has high entropy. Our experiments show that the PF decoder (and its watermarked counterpart) significantly outperform(s) naive sampling (and it's Gumbel watermarked counterpart) in terms of perplexity, while retaining the same robustness (and detectability), hence making it a promising new approach for LLM decoding. The code is available at https://github.com/XuandongZhao/pf-decoding
## fulltext notes (optional)
