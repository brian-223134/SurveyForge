# [28] Watermark Stealing in Large Language Models
source_url: https://arxiv.org/abs/2402.19361
arxiv_id: 2402.19361   doi: none
first_public: 2024-02-29
fetch_status: ok
printed_title: Watermark Stealing in Large Language Models
corpus_title: Watermark Stealing in Large Language Models
## abstract
LLM watermarking has attracted attention as a promising way to detect AI-generated content, with some works suggesting that current schemes may already be fit for deployment. In this work we dispute this claim, identifying watermark stealing (WS) as a fundamental vulnerability of these schemes. We show that querying the API of the watermarked LLM to approximately reverse-engineer a watermark enables practical spoofing attacks, as hypothesized in prior work, but also greatly boosts scrubbing attacks, which was previously unnoticed. We are the first to propose an automated WS algorithm and use it in the first comprehensive study of spoofing and scrubbing in realistic settings. We show that for under $50 an attacker can both spoof and scrub state-of-the-art schemes previously considered safe, with average success rate of over 80%. Our findings challenge common beliefs about LLM watermarking, stressing the need for more robust schemes. We make all our code and additional examples available at https://watermark-stealing.org.
## fulltext notes (optional)
