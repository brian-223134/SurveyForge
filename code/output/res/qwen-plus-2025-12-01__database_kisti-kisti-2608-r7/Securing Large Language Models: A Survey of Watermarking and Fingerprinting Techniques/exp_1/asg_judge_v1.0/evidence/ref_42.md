# [42] Watermarking Language Models with Error Correcting Codes
source_url: https://arxiv.org/abs/2406.10281
arxiv_id: 2406.10281   doi: none
first_public: 2024-06-12
fetch_status: ok
printed_title: Watermarking Language Models with Error Correcting Codes
corpus_title: Watermarking Language Models with Error Correcting Codes
## abstract
Recent progress in large language models enables the creation of realistic machine-generated content. Watermarking is a promising approach to distinguish machine-generated text from human text, embedding statistical signals in the output that are ideally undetectable to humans. We propose a watermarking framework that encodes such signals through an error correcting code. Our method, termed robust binary code (RBC) watermark, introduces no noticeable degradation in quality. We evaluate our watermark on base and instruction fine-tuned models and find that our watermark is robust to edits, deletions, and translations. We provide an information-theoretic perspective on watermarking, a powerful statistical test for detection and for generating $p$-values, and theoretical guarantees. Our empirical findings suggest our watermark is fast, powerful, and robust, comparing favorably to the state-of-the-art.
## fulltext notes (optional)
- [G4 judge, arxiv.org/pdf/2406.10281] Full text searched: no mention of false discovery rate, Benjamini-Hochberg or heterogeneous prompt distributions. Appendix C.1 "Empirical False Positive Rates and p-values": "Our method uses the Binomial Comparison (BC) test to compute p-values and detect watermarks by comparing each p-value against a threshold α." Contributions: "theoretical guarantees linking watermark detectability directly to language model entropy."
