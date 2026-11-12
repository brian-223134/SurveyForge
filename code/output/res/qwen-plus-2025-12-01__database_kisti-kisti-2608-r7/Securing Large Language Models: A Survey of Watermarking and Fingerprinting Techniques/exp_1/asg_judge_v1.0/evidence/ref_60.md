# [60] Waterfall: Framework for Robust and Scalable Text Watermarking and Provenance for LLMs
source_url: https://arxiv.org/abs/2407.04411
arxiv_id: 2407.04411   doi: none
first_public: 2024-07-05
fetch_status: ok
printed_title: Waterfall: Framework for Robust and Scalable Text Watermarking
corpus_title: Waterfall: Framework for Robust and Scalable Text Watermarking
## abstract
Protecting intellectual property (IP) of text such as articles and code is increasingly important, especially as sophisticated attacks become possible, such as paraphrasing by large language models (LLMs) or even unauthorized training of LLMs on copyrighted text to infringe such IP. However, existing text watermarking methods are not robust enough against such attacks nor scalable to millions of users for practical implementation. In this paper, we propose , the first training-free framework for robust and scalable text watermarking applicable across multiple text types (e.g., articles, code) and languages supportable by LLMs, for general text and LLM data provenance. comprises several key innovations, such as being the first to use LLM as paraphrasers for watermarking along with a novel combination of techniques that are surprisingly effective in achieving robust verifiability and scalability. We empirically demonstrate that achieves significantly better scalability, robust verifiability, and computational efficiency compared to SOTA article-text watermarking methods, and also showed how it could be directly applied to the watermarking of code.
## fulltext notes (optional)
- [G1 judge, arxiv.org/html/2407.04411] Sec. 3.4: "uses an LLM paraphraser to autoregressively paraphrase a text"; Sec. 3.3: keys via hash generating "pseudorandom Kπ sequences", vocab permutation seeded by previous n-1 tokens, orthogonal-function logit perturbation. No non-autoregressive models, no Markov-chain keys, no token-reordering invariance claim.
