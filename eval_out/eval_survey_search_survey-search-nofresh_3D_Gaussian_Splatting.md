# 회귀 검사 — 3D Gaussian Splatting

인용 날짜 기준 DB: `database_2026-08`  / 최신 판정 기준: 2024-09-25 이후

| 실행 | 참고문헌 | **matched** | **정전 비중** | **재현율** | 분모 | coverage | 평가 제외 | 최신 인용 | 최신 비율 | 단어 | 섹션/서브 | 무결성 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 구 DB | 119 | **71** | **59.7%** | **21.5%** | 117 | 0.607 | 2 | 0/119 | 0.0% | 24896 | 8/30 | OK |
| 신 DB | 147 | **30** | **20.4%** | **9.1%** | 32 | 0.938 | 115 | 116/147 | 78.9% | 23603 | 8/30 | OK |
| survey-search | 157 | **16** | **10.2%** | **4.8%** | 39 | 0.410 | 118 | 112/157 | 71.3% | 26916 | 9/32 | OK |
| survey-search(fresh 끔) | 134 | **16** | **11.9%** | **4.8%** | 34 | 0.471 | 100 | 88/134 | 65.7% | 23689 | 8/32 | OK |

**정전 비중** = matched / 전체 인용, **재현율** = matched / 정전 문헌 330편. 둘 다 분모가 실행과 무관하게 고정이라 **실행끼리 그대로 견줄 수 있다** — coverage 는 분모가 실행마다 달라져 그렇게 못 쓴다.

> **코퍼스가 다른 실행끼리는 이 표의 어느 열로도 비교하지 마라.** 정답이 과거 시점 서베이의 인용 목록이라, 기준일 이후 논문은 원리적으로 정답에 들 수 없다. 그래서 정규화를 어느 쪽으로 하든 편향이 남는다 — `coverage` 는 분모가 줄어 **최신 논문을 미는 실행에 유리**하고, `정전 비중`·`재현율` 은 같은 이유로 **불리**하다. 실제로 두 지표가 구 DB 대 신 DB 에서 정반대 순위를 낸다. 지표를 바꿔서 풀리는 문제가 아니다 (SurGE 정답 집합도 2019~2023 서베이라 마찬가지다).

> **읽어도 되는 비교는 코퍼스·모델·인자가 같고 검색만 다른 짝뿐이다.** 이 표에서는 신 DB 대 survey-search 가 거기 해당한다(최신 비율 78.1% 대 73.0% 로 시기 분포도 비슷하다). 구 DB 는 코퍼스가 2024-09 에서 멈춰 인용이 전부 판정 대상이 되므로 어느 열에서도 나머지 둘과 같은 자에 놓이지 않는다.

---

원본 출력:

- **구 DB** `code/output/res/deepseek_deepseek-v4-flash-0731/3D Gaussian Splatting/exp_1`
  - 3D Gaussian Splatting citation coverage: 0.607
Average Coverage Across Topics: 0.607
- **신 DB** `code/output/res/deepseek_deepseek-v4-flash-0731__database_2026-08/3D Gaussian Splatting/exp_1`
  - 3D Gaussian Splatting citation coverage: 0.938
Average Coverage Across Topics: 0.938
- **survey-search** `code/output/res/deepseek_deepseek-v4-flash-0731/survey-search/3D Gaussian Splatting/exp_1`
  - 3D Gaussian Splatting citation coverage: 0.41
Average Coverage Across Topics: 0.41
- **survey-search(fresh 끔)** `code/output/res/deepseek_deepseek-v4-flash-0731/survey-search-nofresh/3D Gaussian Splatting/exp_1`
  - 3D Gaussian Splatting citation coverage: 0.471
Average Coverage Across Topics: 0.471
