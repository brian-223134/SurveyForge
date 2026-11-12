# [51] Unlearning vs. Obfuscation: Are We Truly Removing Knowledge?
source_url: https://arxiv.org/abs/2505.02884
arxiv_id: 2505.02884   doi: none
first_public: 2025-05-05
fetch_status: ok
printed_title: Unlearning vs. Obfuscation: Are We Truly Removing Knowledge?
corpus_title: Unlearning vs. Obfuscation: Are We Truly Removing Knowledge?
## abstract
Unlearning has emerged as a critical capability for large language models (LLMs) to support data privacy, regulatory compliance, and ethical AI deployment. Recent techniques often rely on obfuscation by injecting incorrect or irrelevant information to suppress knowledge. Such methods effectively constitute knowledge addition rather than true removal, often leaving models vulnerable to probing. In this paper, we formally distinguish unlearning from obfuscation and introduce a probing-based evaluation framework to assess whether existing approaches genuinely remove targeted information. Moreover, we propose DF-MCQ, a novel unlearning method that flattens the model predictive distribution over automatically generated multiple-choice questions using KL-divergence, effectively removing knowledge about target individuals and triggering appropriate refusal behaviour. Experimental results demonstrate that DF-MCQ achieves unlearning with over 90% refusal rate and a random choice-level uncertainty that is much higher than obfuscation on probing questions.
## fulltext notes (optional)
