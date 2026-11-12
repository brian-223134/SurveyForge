# [22] Functional Invariants To Watermark Large Transformers
source_url: https://doi.org/10.1109/icassp48485.2024.10447264
arxiv_id: none   doi: 10.1109/icassp48485.2024.10447264
first_public: 2024-03-18
fetch_status: ok
printed_title: Functional Invariants To Watermark Large Transformers
corpus_title: Functional Invariants To Watermark Large Transformers
## abstract
The rapid growth of transformer-based models increases the concerns about their integrity and ownership insurance. Watermarking addresses this issue by embedding a unique identifier into the model, while preserving its performance. However, most existing approaches require to optimize the weights to imprint the watermark signal, which is not suitable at scale due to the computational cost. This paper explores watermarks with virtually no computational cost, applicable to a non-blind white-box setting (assuming access to both the original and watermarked networks). They generate functionally equivalent copies by leveraging the models' invariance, via operations like dimension permutations or scaling/unscaling. This enables to watermark models without any change in their outputs and remains stealthy. Experiments demonstrate the effectiveness of the approach and its robustness against various model transformations (fine-tuning, quantization, pruning), making it a practical solution to protect the integrity of large models.
## fulltext notes (optional)
