# [21] No Free Lunch in LLM Watermarking: Trade-offs in Watermarking Design Choices
source_url: https://arxiv.org/abs/2402.16187
arxiv_id: 2402.16187   doi: none
first_public: 2024-02-25
fetch_status: ok
printed_title: Attacking LLM Watermarks by Exploiting Their Strengths
corpus_title: Attacking LLM Watermarks by Exploiting Their Strengths
## abstract
Advances in generative models have made it possible for AI-generated text, code, and images to mirror human-generated content in many applications. Watermarking, a technique that aims to embed information in the output of a model to verify its source, is useful for mitigating misuse of such AI-generated content. However, existing watermarking schemes remain surprisingly susceptible to attack. In particular, we show that desirable properties shared by existing LLM watermarking systems such as quality preservation, robustness, and public detection APIs can in turn make these systems vulnerable to various attacks. We rigorously study potential attacks in terms of common watermark design choices, and propose best practices and defenses for mitigation---establishing a set of practical guidelines for embedding and detection of LLM watermarks.
## fulltext notes (optional)
- [G1 judge, arxiv.org/html/2402.16187] Attacks: piggyback spoofing (Sec. 4), removal via multiple keys with token-frequency histogram from repeated queries (Sec. 5), detection-API removal/spoofing (Sec. 6). Defenses: digital signatures (Sec. 4.2: "requiring proof of digital signatures on the LLM generated content"), query rate limiting (Sec. 5.2), DP-style noisy detection scores (Sec. 6.3). Paraphrasing only in Related Work (Sec. 2). Not discussed: speculative decoding, homoglyph/whitespace, ensemble inhibition, token filtering, low-resource languages, fingerprinting, O(sqrt Q)/Wald testing, zero-knowledge proofs, collusion/ensemble watermarking.
- [G3 judge, arxiv.org/html/2402.16187, first 100k chars] Attacks: piggyback spoofing exploiting robustness (Sec. 4), removal exploiting multiple keys (Sec. 5), removal/spoofing via public detection APIs (Sec. 6). Only noise mechanism is a defense, Sec. 6.3: "we consider adding Gaussian noise to the distance score in the watermark detection." No softmax-noise attack.
