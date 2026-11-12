# [68] Marking Code Without Breaking It: Code Watermarking for Detecting LLM-Generated Code
source_url: https://arxiv.org/abs/2502.18851
arxiv_id: 2502.18851   doi: none
first_public: 2025-02-26
fetch_status: ok
printed_title: Marking Code Without Breaking It: Code Watermarking for Detecting LLM-Generated Code
corpus_title: Marking Code Without Breaking It: Code Watermarking for Detecting LLM-Generated Code
## abstract
Identifying LLM-generated code through watermarking poses a challenge in preserving functional correctness. Previous methods rely on the assumption that watermarking high-entropy tokens effectively maintains output quality. Our analysis reveals a fundamental limitation of this assumption: syntax-critical tokens such as keywords often exhibit the highest entropy, making existing approaches vulnerable to logic corruption. We present STONE, a syntax-aware watermarking method that embeds watermarks only in non-syntactic tokens and preserves code integrity. For its rigorous assessment, we also introduce STEM, a comprehensive framework that balances three critical dimensions: correctness, detectability, and imperceptibility. Across Python, C++, and Java, STONE preserves correctness, sustains strong detectability, and achieves balanced performance with minimal overhead. Our implementation is available at https://anonymous.4open.science/r/STONE-watermarking-AB4B/.
## fulltext notes (optional)
