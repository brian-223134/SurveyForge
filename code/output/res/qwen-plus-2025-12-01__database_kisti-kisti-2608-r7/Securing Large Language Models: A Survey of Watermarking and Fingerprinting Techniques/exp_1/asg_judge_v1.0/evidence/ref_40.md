# [40] A Watermark for Large Language Models
source_url: https://arxiv.org/abs/2301.10226
arxiv_id: 2301.10226   doi: none
first_public: 2023-01-24
fetch_status: ok
printed_title: A Watermark for Large Language Models
corpus_title: A Watermark for Large Language Models
## abstract
-1 Potential harms of large language models can be mitigated by watermarking model output, i.e., embedding signals into generated text that are invisible to humans but algorithmically detectable from a short span of tokens. We propose a watermarking framework for proprietary language models. The watermark can be embedded with negligible impact on text quality, and can be detected using an efficient open-source algorithm without access to the language model API or parameters. The watermark works by selecting a randomized set of ``whitelist'' tokens before a word is generated, and then softly promoting use of whitelist tokens during sampling. We propose a statistical test for detecting the watermark with interpretable p-values, and derive an information-theoretic framework for analyzing the sensitivity of the watermark. We test the watermark using a multi-billion parameter model from the Open Pretrained Transformer (OPT) family, and discuss robustness and security.
## fulltext notes (optional)
