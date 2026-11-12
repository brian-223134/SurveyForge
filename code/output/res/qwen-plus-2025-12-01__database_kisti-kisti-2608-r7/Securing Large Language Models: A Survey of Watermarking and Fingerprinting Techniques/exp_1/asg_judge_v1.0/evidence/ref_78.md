# [78] Lossless Copyright Protection via Intrinsic Model Fingerprinting
source_url: https://arxiv.org/abs/2601.21252
arxiv_id: 2601.21252   doi: none
first_public: 2026-01-29
fetch_status: ok
printed_title: Lossless Copyright Protection via Intrinsic Model Fingerprinting
corpus_title: Lossless Copyright Protection via Intrinsic Model Fingerprinting
## abstract
The exceptional performance of diffusion models establishes them as high-value intellectual property but exposes them to unauthorized replication. Existing protection methods either modify the model to embed watermarks, which impairs performance, or extract model fingerprints by manipulating the denoising process, rendering them incompatible with black-box APIs. In this paper, we propose TrajPrint, a completely lossless and training-free framework that verifies model copyright by extracting unique manifold fingerprints formed during deterministic generation. Specifically, we first utilize a watermarked image as an anchor and exactly trace the path back to its trajectory origin, effectively locking the model fingerprint mapped by this path. Subsequently, we implement a joint optimization strategy that employs dual-end anchoring to synthesize a specific fingerprint noise, which strictly adheres to the target manifold for robust watermark recovery. As input, it enables the protected target model to recover the watermarked image, while failing on non-target models. Finally, we achieved verification via atomic inference and statistical hypothesis testing. Extensive experiments demonstrate that TrajPrint achieves lossless verification in black-box API scenarios with superior robustness against model modifications.
## fulltext notes (optional)
