# [16] SLIM: Stealthy Low-Coverage Black-Box Watermarking via Latent-Space Confusion Zones
source_url: https://arxiv.org/abs/2601.03242
arxiv_id: 2601.03242   doi: none
first_public: 2026-01-06
fetch_status: ok
printed_title: SLIM: Stealthy Low-Coverage Black-Box Watermarking via Latent-Space Confusion Zones
corpus_title: SLIM: Stealthy Low-Coverage Black-Box Watermarking via Latent-Space Confusion Zones
## abstract
Training data is a critical and often proprietary asset in Large Language Model (LLM) development, motivating the use of data watermarking to embed model-transferable signals for usage verification. We identify low coverage as a vital yet largely overlooked requirement for practicality, as individual data owners typically contribute only a minute fraction of massive training corpora. Prior methods fail to maintain stealthiness, verification feasibility, or robustness when only one or a few sequences can be modified. To address these limitations, we introduce SLIM, a framework enabling per-user data provenance verification under strict black-box access. SLIM leverages intrinsic LLM properties to induce a Latent-Space Confusion Zone by training the model to map semantically similar prefixes to divergent continuations. This manifests as localized generation instability, which can be reliably detected via hypothesis testing. Experiments demonstrate that SLIM achieves ultra-low coverage capability, strong black-box verification performance, and great scalability while preserving both stealthiness and model utility, offering a robust solution for protecting training data in modern LLM pipelines.
## fulltext notes (optional)
