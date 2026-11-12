# [41] On the Reliability of Watermarks for Large Language Models
source_url: https://arxiv.org/abs/2306.04634
arxiv_id: 2306.04634   doi: none
first_public: 2023-06-07
fetch_status: ok
printed_title: On the Reliability of Watermarks for Large Language Models
corpus_title: On the Reliability of Watermarks for Large Language Models
## abstract
-1 Large language models (LLMs) are now deployed to everyday use and positioned to produce large quantities of text in the coming decade. Machine-generated text may displace human-written text on the internet and has the potential to be used for malicious purposes, such as spearphishing attacks and social media bots. Watermarking is a simple and effective strategy for mitigating such harms by enabling the detection and documentation of LLM-generated text. Yet, a crucial question remains: How reliable is watermarking in realistic settings in the wild? There, watermarked text might be mixed with other text sources, paraphrased by human writers or other language models, and used for applications in a broad number of domains, both social and technical. In this paper, we explore different detection schemes, quantify their power at detecting watermarks, and determine how much machine-generated text needs to be observed in each scenario to reliably detect the watermark. We especially highlight our human study, where we investigate the reliability of watermarking when faced with human paraphrasing. We compare watermark-based detection to other detection strategies, finding overall that watermarking is a reliable solution, especially because of its sample complexity - for all attacks we consider, the watermark evidence compounds the more examples are given, and the watermark is eventually detected.
## fulltext notes (optional)
- [G5, arxiv.org/html/2306.04634] §4.3 "Paraphrasing by Human Writers": 14 graduate-student writers asked to "paraphrase the text with the goal of removing the watermark"; detected after ~800 tokens. No fluency ratings by native language/education in main text; no translation attacks; no LLM-as-judge.
