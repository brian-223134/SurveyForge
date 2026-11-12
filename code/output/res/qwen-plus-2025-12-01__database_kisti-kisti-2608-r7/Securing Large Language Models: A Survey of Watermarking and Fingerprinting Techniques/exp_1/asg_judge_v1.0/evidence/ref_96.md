# [96] Fingerprinting LLMs via Prompt Injection
source_url: https://arxiv.org/abs/2509.25448
arxiv_id: 2509.25448   doi: none
first_public: 2025-09-29
fetch_status: ok
printed_title: Fingerprinting LLMs via Prompt Injection
corpus_title: Fingerprinting LLMs via Prompt Injection
## abstract
Large language models (LLMs) are often modified after release through post-processing such as post-training or quantization, which makes it challenging to determine whether one model is derived from another. Existing provenance detection methods have two main limitations: (1) they embed signals into the base model before release, which is infeasible for already published models, or (2) they compare outputs across models using hand-crafted or random prompts, which are not robust to post-processing. In this work, we propose LLMPrint, a novel detection framework that constructs fingerprints by exploiting LLMs' inherent vulnerability to prompt injection. Our key insight is that by optimizing fingerprint prompts to enforce consistent token preferences, we can obtain fingerprints that are both unique to the base model and robust to post-processing. We further develop a unified verification procedure that applies to both gray-box and black-box settings, with statistical guarantees. We evaluate LLMPrint on five base models and around 700 post-trained or quantized variants. Our results show that LLMPrint achieves high true positive rates while keeping false positive rates near zero.
## fulltext notes (optional)
