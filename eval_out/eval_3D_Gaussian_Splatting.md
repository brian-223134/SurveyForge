# 회귀 검사 — 3D Gaussian Splatting

인용 날짜 기준 DB: `database_2026-08`  / 최신 판정 기준: 2024-09-25 이후

| 실행 | 참고문헌 | **matched** | 분모 | coverage | 평가 제외 | 최신 인용 | 최신 비율 | 단어 | 섹션/서브 | 무결성 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 구 DB (flash) | 119 | **71** | 117 | 0.607 | 2 | 0/119 | 0.0% | 24896 | 8/30 | OK |
| 신 DB (flash) | 147 | **30** | 32 | 0.938 | 115 | 116/147 | 78.9% | 24306 | 8/30 | OK |

**정전 문헌 적중: 71 -> 30편** (벤치마크 참고문헌 기준). 이게 희석 여부를 보는 값이다.

**coverage 비율: 0.607 -> 0.938 (+0.331)** — **비율만 보면 안 된다.** 분모가 117 -> 32 로 바뀌었다. 벤치마크 기준일(2024-06)보다 새 논문은 분자·분모 양쪽에서 빠지므로, 최신 논문을 많이 인용할수록 분모가 작아져 실제로 덜 맞혀도 비율이 오른다.

**최신성: 0.0% -> 78.9%** (평가에서 무시된 인용 2 -> 115편). 벤치마크는 이 축을 보지 못한다.

---

원본 출력:

- **구 DB (flash)** `code/output/res/deepseek_deepseek-v4-flash-0731/3D Gaussian Splatting/exp_1`
  - 3D Gaussian Splatting citation coverage: 0.607
Average Coverage Across Topics: 0.607
- **신 DB (flash)** `code/output/res/deepseek_deepseek-v4-flash-0731__database_2026-08/3D Gaussian Splatting/exp_1`
  - 3D Gaussian Splatting citation coverage: 0.938
Average Coverage Across Topics: 0.938
