# Edge Computing 파일럿 생성 — 실험 메트릭 기록

세미나 발표 참고용. 공용 코퍼스 통합([common-corpus-integration.md](common-corpus-integration.md) §10)
후 첫 파일럿 생성 1편의 실측 지표를 원본 로그에서 재확인해 정리한 것이다.
모든 수치는 아래 산출물 경로의 로그·파일에서 직접 계산했다.

## 1. 실험 구성

| 항목 | 값 |
|---|---|
| 주제 | Edge Computing (SurveyBench GT 밖 토픽, 자유 생성) |
| 실행 일시 | 2026-09-01 00:26:20 ~ 01:02:55 (KST) |
| 브랜치 | `common-corpus` |
| 백본 LLM | `meta-llama/llama-3.3-70b-instruct` (OpenRouter, provider `akashml/fp8` 고정) |
| 검색 코퍼스 | `database_cc-surveyeval-2512` — asg-common-corpus 뷰 `surveyeval-2512`, 947,444편, 컷오프 2025-12-31 |
| 임베딩 | `gte-large-en-v1.5` (로컬 GPU, LLM 비용에 미포함) |
| 실행 방식 | run_demo 무인 체인, exit 0 (아웃라인 → 서브아웃라인 → 본문 → 정제 → PDF 컴파일) |
| 산출물 | `code/output/res/meta-llama_llama-3.3-70b-instruct__database_cc-surveyeval-2512/Edge Computing/exp_1/` |

## 2. 핵심 메트릭 요약

| 메트릭 | 값 | 비고 |
|---|---|---|
| **실비용** | **$0.3884** | OpenRouter 크레딧 스냅샷 전후 차 (§3) |
| **소요 시간** | **36분 35초** | `experiment_times.log` 실측 (§4) |
| **본문 길이** | **31,455 words** (refined) | 저자 기준선 13k~33k words의 상단부 |
| **PDF** | **46쪽**, 0.54 MB | pdflatex 3패스 무경고, ≈684 words/쪽 |
| **참고문헌** | **101편** | json·bib·metadata 3곳 모두 101로 일치, id 매핑 정상 |
| **섹션** | 7/7 완결 | 결론 포함, 구조 손상 없음 |
| **토큰 사용량** | 입력 1,589,034 / 출력 112,926 | Writer 2단계 합 (§5) |

비용 비교: 같은 파이프라인의 deepseek 계열 실측이 편당 $0.7~2.2였으므로 **약 45~82% 절감**.

## 3. 비용 — 산출 방식과 원본

`scripts/check_credits.py`로 생성 직전·직후 OpenRouter 크레딧을 스냅샷해서 차이로 측정했다
(`eval_out/credits.log`).

```
2026-09-01 00:26:20 [before-edge-computing]  key: used=$21.6010  today=$0.0000
2026-09-01 01:03:00 [after-edge-computing]   key: used=$21.9894  today=$0.3884
```

- 키 used 차이 = **$0.3884** (`today` 필드와도 일치 — 당일 이 실행 외 사용 없음)
- 문서·커밋의 "$0.39"는 이 값의 반올림
- 임베딩·FAISS 검색은 전부 로컬이므로 이 금액은 순수 LLM 호출 비용

## 4. 시간 — 전체와 단계별 분해

`experiment_times.log`: Start 00:26:20 → End 01:02:55, **Duration 0:36:35** (후처리 마감까지 총 0:36:40).

`time_cost.log`의 API 호출 시간을 종류별로 합산하면 (8-thread 병렬이라 합계는 벽시계 시간을 초과):

| 단계 | API 시간 합 | 관찰 |
|---|---|---|
| RAG (검색) | 539.2s | 대형 검색 ~250s × 2회가 지배 — retrieve마다 벡터스토어를 재인스턴스화하는 기존 구조가 947K 코퍼스에서 드러난 것 (실행당 ~8분, 최적화 후보) |
| Outline | 91.2s | 1회 |
| SubOutline | 41.4s | 1회 |
| Content (본문 작성) | 705.3s | 최장 1회 477.6s |
| Content Check (정제) | 688.2s | 최장 1회 486.4s |

즉 벽시계 기준으로는 검색 ~8분 + 아웃라인 ~2분 + 본문 작성·정제(병렬) ~26분 정도의 그림이다.

## 5. 텍스트 길이 상세

| 산출물 | words | 크기 | 설명 |
|---|---|---|---|
| `raw_survey.txt` | 30,426 | — | 정제 전 초안 |
| `refined_survey.txt` | 31,455 | 216 KB | 정제 후 최종 본문 — **인용 지표 기준값** |
| `Edge Computing.md` | 26,153 | 174 KB | 인용 표기 변환 후 배포본 (word 수 차이는 인용 id 표기 방식 차이) |
| `Edge Computing.pdf` | — | 0.54 MB, 46쪽 | md → tex(§7 sections, 101 bib entries) → pdflatex 3패스 |

토큰 사용량 (`experiment_times.log`):

| Writer | 입력 토큰 | 출력 토큰 |
|---|---|---|
| OutlineWriter | 443,728 | 11,594 |
| SubsectionWriter | 1,145,306 | 101,332 |
| **합** | **1,589,034** | **112,926** |

## 6. 정합성 게이트 (전부 통과)

| 게이트 | 결과 |
|---|---|
| 컷오프 (outline/writer) | 947,444/947,444 retrievable, **0 excluded** |
| TRE 인용 창 폐기 | **0/5,175** (`[1991-01-01, 2026-01-01]` 창) |
| provider 고정 | `[PROVIDER] served by: AkashML` 단일 |
| 참고문헌 정합 | 101편, id → DB 매핑 정상 |
| PDF 컴파일 | pdflatex 3패스 무경고 |

## 7. 한계·잔여 관찰

1. **[TRUNCATED] 2건** — 단계 경계 대형 호출이 `max_tokens=16384` 상한에 닿음
   (finish_reason=length). 결과물 구조 손상은 없었으나 다음 실행 전
   `SURVEYFORGE_MAX_TOKENS=32768` 상향 검토.
2. **대형 검색 ~250s × 2회** — §4의 벡터스토어 재인스턴스화. 급하지 않은 최적화 후보.
3. **서지의 저자·게재처 결손** — 코퍼스에 authors/venue가 없어 `.bib`은 제목·연도·arXiv
   링크만 표기. 평가 지표는 전부 arXiv id 기반이라 지표 영향 0.

n=1 파일럿이므로 비용·시간은 토픽·검색 풀 크기에 따라 변동 여지가 있다.
