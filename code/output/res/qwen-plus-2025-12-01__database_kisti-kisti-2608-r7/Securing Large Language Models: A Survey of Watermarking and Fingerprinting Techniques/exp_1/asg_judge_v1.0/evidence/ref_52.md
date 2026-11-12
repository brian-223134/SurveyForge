# [52] Can Watermarks Survive Translation? On the Cross-lingual Consistency of Text Watermark for Large Language Models
source_url: https://arxiv.org/abs/2402.14007
arxiv_id: 2402.14007   doi: none
first_public: 2024-02-21
fetch_status: ok
printed_title: Can Watermarks Survive Translation? On the Cross-lingual Consistency of Text Watermark for Large Language Models
corpus_title: Can Watermarks Survive Translation? On the Cross-lingual Consistency of Text Watermark for Large Language Models
## abstract
Text watermarking technology aims to tag and identify content produced by large language models (LLMs) to prevent misuse. In this study, we introduce the concept of cross-lingual consistency in text watermarking, which assesses the ability of text watermarks to maintain their effectiveness after being translated into other languages. Preliminary empirical results from two LLMs and three watermarking methods reveal that current text watermarking technologies lack consistency when texts are translated into various languages. Based on this observation, we propose a Cross-lingual Watermark Removal Attack (CWRA) to bypass watermarking by first obtaining a response from an LLM in a pivot language, which is then translated into the target language. CWRA can effectively remove watermarks, decreasing the AUCs to a random-guessing level without performance loss. Furthermore, we analyze two key factors that contribute to the cross-lingual consistency in text watermarking and propose X-SIR as a defense method against CWRA. Code: https://github.com/zwhe99/X-SIR.
## fulltext notes (optional)
- [G4 judge, arxiv.org/html/2402.14007] Section 3.2 Setup: target languages are Chinese, Japanese, French, German (from English); no Bangla or Hindi. Section 4.2: "The AUCs for KGW and UW under CWRA plummet to 0.61 and 0.54, respectively." SIR stays at 0.67.
- [G5, arxiv.org/html/2402.14007] §4.2: "The AUCs for KGW and UW under CWRA plummet to 0.61 and 0.54, respectively." Languages: English source; Chinese, Japanese, French, German targets (§3.2). No low-resource-language analysis; no ">88% / <13%" figures in text.
- [G3 judge, arxiv.org/html/2402.14007] Sec. 4.2 "CWRA vs Other Attack Methods": "The AUCs for KGW and UW under CWRA plummet to 0.61 and 0.54, respectively." No 88%->13% figure; attacks compared are CWRA, Paraphrase, Re-translation (Sec. 4.1); no TP/UP strategies, no composite paraphrase+translation+fine-tuning attack, no knowledge distillation. Models: Baichuan-7B, Llama-2-7B; watermarks KGW, UW, SIR.
