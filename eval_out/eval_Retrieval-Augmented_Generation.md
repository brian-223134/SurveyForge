# 회귀 검사 — Retrieval-Augmented Generation for Large Language Models

인용 날짜 기준 DB: `database_2026-08`  / 최신 판정 기준: 2024-09-25 이후

| 실행 | 참고문헌 | **matched** | 분모 | coverage | 평가 제외 | 최신 인용 | 최신 비율 | 단어 | 섹션/서브 | 무결성 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 구 DB (flash) | 131 | **38** | 125 | 0.304 | 5 | 0/131 | 0.0% | 29977 | 9/34 | OK |
| 신 DB (flash) | 128 | **18** | 28 | 0.643 | 100 | 100/128 | 78.1% | 24493 | 8/29 | OK |

**정전 문헌 적중: 38 -> 18편** (벤치마크 참고문헌 기준). 이게 희석 여부를 보는 값이다.

**coverage 비율: 0.304 -> 0.643 (+0.339)** — **비율만 보면 안 된다.** 분모가 125 -> 28 로 바뀌었다. 벤치마크 기준일(2024-07)보다 새 논문은 분자·분모 양쪽에서 빠지므로, 최신 논문을 많이 인용할수록 분모가 작아져 실제로 덜 맞혀도 비율이 오른다.

**최신성: 0.0% -> 78.1%** (평가에서 무시된 인용 5 -> 100편). 벤치마크는 이 축을 보지 못한다.

---

원본 출력:

- **구 DB (flash)** `code/output/res/deepseek_deepseek-v4-flash-0731/Retrieval-Augmented Generation for Large Language Models/exp_1`
  - Retrieval-Augmented Generation for Large Language Models citation coverage: 0.304
Average Coverage Across Topics: 0.304
- **신 DB (flash)** `code/output/res/deepseek_deepseek-v4-flash-0731__database_2026-08/Retrieval-Augmented Generation for Large Language Models/exp_1`
  - Retrieval-Augmented Generation for Large Language Models citation coverage: 0.643
Average Coverage Across Topics: 0.643
