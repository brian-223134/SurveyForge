# [64] Learning to Watermark LLM-generated Text via Reinforcement Learning
source_url: https://arxiv.org/abs/2403.10553
arxiv_id: 2403.10553   doi: none
first_public: 2024-03-13
fetch_status: ok
printed_title: Learning to Watermark LLM-generated Text via Reinforcement Learning
corpus_title: Learning to Watermark LLM-generated Text via Reinforcement Learning
## abstract
We study how to watermark LLM outputs, i.e. embedding algorithmically detectable signals into LLM-generated text to track misuse. Unlike the current mainstream methods that work with a fixed LLM, we expand the watermark design space by including the LLM tuning stage in the watermark pipeline. While prior works focus on token-level watermark that embeds signals into the output, we design a model-level watermark that embeds signals into the LLM weights, and such signals can be detected by a paired detector. We propose a co-training framework based on reinforcement learning that iteratively (1) trains a detector to detect the generated watermarked text and (2) tunes the LLM to generate text easily detectable by the detector while keeping its normal utility. We empirically show that our watermarks are more accurate, robust, and adaptable (to new attacks). It also allows watermarked model open-sourcing. In addition, if used together with alignment, the extra overhead introduced is low -- only training an extra reward model (i.e. our detector). We hope our work can bring more effort into studying a broader watermark design that is not limited to working with a fixed LLM. We open-source the code: https://github.com/xiaojunxu/learning-to-watermark-llm .
## fulltext notes (optional)
- [S0107/S0108, arxiv.org/html/2403.10553] Section 5.1 (Task and Data): experiments use OPT-1.3B and Llama2-7B; no Alpaca, no LLaMA-1.
- Section 2 (Preliminary): "we use Proximal Policy Optimization (PPO) ... to maximize the following objective for the LLM." RL co-training of detector and LLM.
- No encoder-decoder, online prompting, dense-to-sparse logits mapping, binary signature injection, or quantized-model deployment; Section 1 notes "a higher detection overhead".
