# [17] Model Provenance Testing for Large Language Models
source_url: https://arxiv.org/abs/2502.00706
arxiv_id: 2502.00706   doi: none
first_public: 2025-02-02
fetch_status: ok
printed_title: Model Provenance Testing for Large Language Models
corpus_title: Model Provenance Testing for Large Language Models
## abstract
Large language models are increasingly customized through fine-tuning and other adaptations, creating challenges in enforcing licensing terms and managing downstream impacts. Tracking model origins is crucial both for protecting intellectual property and for identifying derived models when biases or vulnerabilities are discovered in foundation models. We address this challenge by developing a framework for testing model provenance: Whether one model is derived from another. Our approach is based on the key observation that real-world model derivations preserve significant similarities in model outputs that can be detected through statistical analysis. Using only black-box access to models, we employ multiple hypothesis testing to compare model similarities against a baseline established by unrelated models. On two comprehensive real-world benchmarks spanning models from 30M to 4B parameters and comprising over 600 models, our tester achieves 90-95% precision and 80-90% recall in identifying derived models. These results demonstrate the viability of systematic provenance verification in production environments even when only API access is available.
## fulltext notes (optional)
