# [71] Semantic Differentiation for Tackling Challenges in Watermarking Low-Entropy Constrained Generation Outputs
source_url: https://arxiv.org/abs/2601.11629
arxiv_id: 2601.11629   doi: none
first_public: 2026-01-14
fetch_status: ok
printed_title: Semantic Differentiation for Tackling Challenges in Watermarking Low-Entropy Constrained Generation Outputs
corpus_title: Semantic Differentiation for Tackling Challenges in Watermarking Low-Entropy Constrained Generation Outputs
## abstract
We demonstrate that while the current approaches for language model watermarking are effective for open-ended generation, they are inadequate at watermarking LM outputs for constrained generation tasks with low-entropy output spaces. Therefore, we devise SeqMark, a sequence-level watermarking algorithm with semantic differentiation that balances the output quality, watermark detectability, and imperceptibility. It improves on the shortcomings of the prevalent token-level watermarking algorithms that cause under-utilization of the sequence-level entropy available for constrained generation tasks. Moreover, we identify and improve upon a different failure mode we term region collapse, associated with prior sequence-level watermarking algorithms. This occurs because the pseudorandom partitioning of semantic space for watermarking in these approaches causes all high-probability outputs to collapse into either invalid or valid regions, leading to a trade-off in output quality and watermarking effectiveness. SeqMark instead, differentiates the high-probable output subspace and partitions it into valid and invalid regions, ensuring the even spread of high-quality outputs among all the regions. On various constrained generation tasks like machine translation, code generation, and abstractive summarization, SeqMark substantially improves watermark detection accuracy (up to 28% increase in F1) while maintaining high generation quality.
## fulltext notes (optional)
