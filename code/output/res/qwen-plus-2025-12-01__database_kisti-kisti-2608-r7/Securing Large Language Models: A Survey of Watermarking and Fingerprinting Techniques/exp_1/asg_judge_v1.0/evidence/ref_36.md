# [36] Hey, That's My Model! Introducing Chain & Hash, An LLM Fingerprinting Technique
source_url: https://arxiv.org/abs/2407.10887
arxiv_id: 2407.10887   doi: none
first_public: 2024-07-15
fetch_status: ok
printed_title: Hey, That's My Model! Introducing Chain & Hash, An LLM Fingerprinting Technique
corpus_title: Hey, That's My Model! Introducing Chain & Hash, An LLM Fingerprinting Technique
## abstract
Growing concerns over the theft and misuse of Large Language Models (LLMs) have heightened the need for effective fingerprinting, which links a model to its original version to detect misuse. In this paper, we define five key properties for a successful fingerprint: Transparency, Efficiency, Persistence, Robustness, and Unforgeability. We introduce a novel fingerprinting framework that provides verifiable proof of ownership while maintaining fingerprint integrity. Our approach makes two main contributions. First, we propose a Chain and Hash technique that cryptographically binds fingerprint prompts with their responses, ensuring no adversary can generate colliding fingerprints and allowing model owners to irrefutably demonstrate their creation. Second, we address a realistic threat model in which instruction-tuned models' output distribution can be significantly altered through meta-prompts. By integrating random padding and varied meta-prompt configurations during training, our method preserves fingerprint robustness even when the model's output style is significantly modified. Experimental results demonstrate that our framework offers strong security for proving ownership and remains resilient against benign transformations like fine-tuning, as well as adversarial attempts to erase fingerprints. Finally, we also demonstrate its applicability to fingerprinting LoRA adapters.
## fulltext notes (optional)
- [G4 judge, arxiv.org/html/2407.10887] Section 1 Introduction: "our approach operates in a black-box setting, requiring only API-level access for verification". Binding uses cryptographic hashes (e.g., SHA-256); no zero-knowledge proofs, no mention of EU AI Act or GDPR.
