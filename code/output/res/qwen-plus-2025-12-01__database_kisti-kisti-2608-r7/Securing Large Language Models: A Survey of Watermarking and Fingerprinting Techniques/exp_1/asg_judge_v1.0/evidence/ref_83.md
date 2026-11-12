# [83] Advancing Beyond Identification: Multi-bit Watermark for Large Language Models
source_url: https://doi.org/10.18653/v1/2024.naacl-long.224
arxiv_id: none   doi: 10.18653/v1/2024.naacl-long.224
first_public: 2024
fetch_status: ok
printed_title: Advancing Beyond Identification: Multi-bit Watermark for Large Language Models
corpus_title: Advancing Beyond Identification: Multi-bit Watermark for Large Language Models
## abstract
We show the viability of tackling misuses of large language models beyond the identification of machine-generated text. While existing zero-bit watermark methods focus on detection only, some malicious misuses demand tracing the adversary user for counteracting them. To address this, we propose Multi-bit Watermark via Position Allocation, embedding traceable multi-bit information during language model generation. Through allocating tokens onto different parts of the messages, we embed longer messages in high corruption settings without added latency. By independently embedding sub-units of messages, the proposed method outperforms the existing works in terms of robustness and latency. Leveraging the benefits of zero-bit watermarking (Kirchenbauer et al., 2023a), our method enables robust extraction of the watermark without any model access, embedding and extraction of long messages (≥ 32-bit) without finetuning, and maintaining text quality, while allowing zero-bit detection all at the same time. Code is released here: https://github.com/bangawayoo/mb-lmwatermarking.
## fulltext notes (optional)
