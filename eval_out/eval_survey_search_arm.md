# 회귀 검사 — Retrieval-Augmented Generation for Large Language Models

인용 날짜 기준 DB: `database_2026-08`  / 최신 판정 기준: 2024-09-25 이후

| 실행 | 참고문헌 | **matched** | **정전 비중** | **재현율** | 분모 | coverage | 평가 제외 | 최신 인용 | 최신 비율 | 단어 | 섹션/서브 | 무결성 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 구 DB | 131 | **38** | **29.2%** | **6.2%** | 125 | 0.304 | 5 | 0/131 | 0.0% | 29008 | 9/34 | OK |
| 신 DB | 128 | **18** | **14.1%** | **3.0%** | 28 | 0.643 | 100 | 100/128 | 78.1% | 23608 | 8/29 | OK |
| survey-search | 122 | **12** | **9.8%** | **2.0%** | 30 | 0.400 | 92 | 89/122 | 73.0% | 21663 | 8/24 | OK |

**정전 비중** = matched / 전체 인용, **재현율** = matched / 정전 문헌 608편. 둘 다 분모가 실행과 무관하게 고정이라 **실행끼리 그대로 견줄 수 있다** — coverage 는 분모가 실행마다 달라져 그렇게 못 쓴다.

> **코퍼스가 다른 실행끼리는 이 표의 어느 열로도 비교하지 마라.** 정답이 과거 시점 서베이의 인용 목록이라, 기준일 이후 논문은 원리적으로 정답에 들 수 없다. 그래서 정규화를 어느 쪽으로 하든 편향이 남는다 — `coverage` 는 분모가 줄어 **최신 논문을 미는 실행에 유리**하고, `정전 비중`·`재현율` 은 같은 이유로 **불리**하다. 실제로 두 지표가 구 DB 대 신 DB 에서 정반대 순위를 낸다. 지표를 바꿔서 풀리는 문제가 아니다 (SurGE 정답 집합도 2019~2023 서베이라 마찬가지다).

> **읽어도 되는 비교는 코퍼스·모델·인자가 같고 검색만 다른 짝뿐이다.** 이 표에서는 신 DB 대 survey-search 가 거기 해당한다(최신 비율 78.1% 대 73.0% 로 시기 분포도 비슷하다). 구 DB 는 코퍼스가 2024-09 에서 멈춰 인용이 전부 판정 대상이 되므로 어느 열에서도 나머지 둘과 같은 자에 놓이지 않는다.

---

원본 출력:

- **구 DB** `code/output/res/deepseek_deepseek-v4-flash-0731/Retrieval-Augmented Generation for Large Language Models/exp_1`
  - Retrieval-Augmented Generation for Large Language Models citation coverage: 0.304
Average Coverage Across Topics: 0.304
- **신 DB** `code/output/res/deepseek_deepseek-v4-flash-0731__database_2026-08/Retrieval-Augmented Generation for Large Language Models/exp_1`
  - Retrieval-Augmented Generation for Large Language Models citation coverage: 0.643
Average Coverage Across Topics: 0.643
- **survey-search** `code/output/res/deepseek_deepseek-v4-flash-0731/survey-search/Retrieval-Augmented Generation for Large Language Models/exp_1`
  - Retrieval-Augmented Generation for Large Language Models citation coverage: 0.4
Average Coverage Across Topics: 0.4
