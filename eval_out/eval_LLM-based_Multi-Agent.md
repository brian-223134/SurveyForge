# 회귀 검사 — LLM-based Multi-Agent

인용 날짜 기준 DB: `database_2026-08`  / 최신 판정 기준: 2024-09-25 이후

| 실행 | 참고문헌 | **matched** | 분모 | coverage | 평가 제외 | 최신 인용 | 최신 비율 | 단어 | 섹션/서브 | 무결성 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 구 DB (flash) | 116 | **31** | 105 | 0.295 | 11 | 0/116 | 0.0% | 20233 | 8/25 | OK |
| 신 DB (flash) | 151 | **11** | 18 | 0.611 | 133 | 135/151 | 89.4% | 24671 | 8/30 | OK |

**정전 문헌 적중: 31 -> 11편** (벤치마크 참고문헌 기준). 이게 희석 여부를 보는 값이다.

**coverage 비율: 0.295 -> 0.611 (+0.316)** — **비율만 보면 안 된다.** 분모가 105 -> 18 로 바뀌었다. 벤치마크 기준일(2024-07)보다 새 논문은 분자·분모 양쪽에서 빠지므로, 최신 논문을 많이 인용할수록 분모가 작아져 실제로 덜 맞혀도 비율이 오른다.

**최신성: 0.0% -> 89.4%** (평가에서 무시된 인용 11 -> 133편). 벤치마크는 이 축을 보지 못한다.

---

원본 출력:

- **구 DB (flash)** `code/output/res/deepseek_deepseek-v4-flash-0731/LLM-based Multi-Agent/exp_1`
  - LLM-based Multi-Agent citation coverage: 0.295
Average Coverage Across Topics: 0.295
- **신 DB (flash)** `code/output/res/deepseek_deepseek-v4-flash-0731__database_2026-08/LLM-based Multi-Agent/exp_1`
  - LLM-based Multi-Agent citation coverage: 0.611
Average Coverage Across Topics: 0.611
