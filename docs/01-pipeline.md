# 01 — 무엇을 어떻게 생성했나

## 1. 문제 설정

서베이 자동 생성은 "긴 글을 잘 쓰는 문제"로 보이지만, 실제로는 **본문을 쓰기 전에
참고문헌이 결정되는 구조**입니다. 파이프라인이 검색으로 후보 논문을 뽑고, 그 안에서만
아웃라인과 본문이 만들어집니다. 검색이 못 데려온 논문은 서베이에 존재할 수 없습니다.

그래서 이 작업의 축은 **검색 레이어**입니다.

## 2. 파이프라인 5단계 (SurveyForge)

```
토픽 문자열
  ↓ ① 검색: 토픽 1쿼리 → 후보 1,500편          ← 여기서 후보 풀이 확정됨
  ↓ ② 청크 아웃라인 → ③ 병합/서브아웃라인
  ↓ ④ 서브섹션 본문 작성 (서브섹션마다 재검색, 풀 안으로 제한)
  ↓ ⑤ 정제(LCE) + 인용 번호 매핑
서베이 (.md/.json) → .tex/.bib → PDF
```

**중요한 구조 하나** — `writer.py:41` 이 토픽 하나로 1,500편을 뽑고, `writer.py:50` 이
그 집합을 `id_selector` 로 만들어 **이후 모든 서브섹션 검색에 겁니다.**
즉 ①이 후보 풀을 정하고, ④는 그 안에서 순서만 바꿉니다. 이 사실이 나중에 진단의
핵심 근거가 됩니다(→ [04-results.md](04-results.md) §3).

## 3. 세 개의 arm — 무엇을 고정하고 무엇을 바꿨나

| | 코퍼스 | 검색 레이어 | 목적 |
|---|---|---|---|
| **구 DB** | 2024-09 스냅샷 | 원본 (dense top-k + 인용수 정렬) | 원논문 재현 기준선 |
| **신 DB** | **2026-08** 스냅샷 | 원본 | 코퍼스 최신화 효과 |
| **survey-search** | 2026-08 (동일) | **교체** (facet 분해 + RRF + freshness) | 검색 교체 효과 |
| survey-search(fresh 끔) | 2026-08 (동일) | 교체, 랭킹만 RRF | 원인 분리용 |

구 DB 와 신 DB 의 차이(논문 DB 를 2024-09 → 2026-08 로 증분한 작업)는
[02-corpus-update.md](02-corpus-update.md) 에서 따로 다룹니다.

**고정한 것**: 모델·프롬프트·생성 로직·파라미터(`--section_num 7 --rag_num 100
--rag_max_out 60 --outline_reference_num 1500`)·프로바이더·토픽.
**바꾼 것**: 신 DB 대비 survey-search 는 **검색 레이어 하나**뿐입니다.

호스트 수정은 `code/main.py` 의 **import 한 줄 + 생성자 2곳**입니다. 생성 로직·프롬프트·
평가에는 손대지 않았습니다 — 그래야 "검색만 바꿨을 때의 차이"라고 말할 수 있습니다.

## 4. 실행 조건 (실측)

| 항목 | 값 |
|---|---|
| 모델 | `deepseek/deepseek-v4-flash-0731` (open weight) |
| 경유 / 엔드포인트 | OpenRouter, **provider 핀** (`parasail/fp8`, `allow_fallbacks=false`) |
| 왜 핀했나 | 핀 없이는 한 서베이의 서브섹션들이 fp4·fp8 혼합으로 작성됨 = 통제 실험이 아님 |
| 동시 요청 | 최대 16 (`MAX_SECTION_THREADS 2 × MAX_THREADS 8`) |
| 코퍼스 | arXiv 초록 908,819편, 컷오프 **2026-08-04** |
| GPU | 임베딩·FAISS 용 1장 |

### 소요 시간 (실측)

| 실행 | 시간 | 429 | facet fallback |
|---|---:|---:|---:|
| survey-search / RAG (서브섹션 facet 켬) | **106분** | 6 | **2** |
| survey-search / 3DGS (facet 분리 후) | **16분** | 0 | 0 |
| survey-search(fresh 끔) / 3DGS | **10분** | 0 | 0 |

서브섹션마다 LLM facet 분해를 돌리던 것을 끊자 **106분 → 16분**이 됐습니다. 근거는
§2 의 구조입니다 — 풀은 ①이 정하므로 ④에서 facet 을 또 돌려도 풀이 넓어지지 않습니다.
같은 수정으로 **facet 분해 실패(fallback) 경로도 사라졌습니다.**

### 비용 — 편당 $0.28 ~ $0.38 (flash), 10편 총액 약 $4.95

| 실행 | 입력 / 출력 토큰 | 비용 |
|---|---|---:|
| 파일럿 (`v4-pro`, reasoning ON) | 2,241,756 / 127,848 | **$1.998** |
| 구 DB × 3토픽 | 190만~241만 / 12만~16만 | $0.300 ~ $0.381 |
| 신 DB × 3토픽 | 206만~226만 / 14만~16만 | $0.329 ~ $0.359 |
| **survey-search × 3편** | 170만~180만 / 14만~16만 | **$0.282 ~ $0.298** |

단가: `v4-flash-0731` fp8 $0.140 / $0.280 per M. 전체 표는 [`../README.md`](../README.md) §5.

읽는 법 셋:

1. **비용의 90%가 입력 토큰입니다.** 서브섹션마다 검색한 초록을 프롬프트에 다시 넣기
   때문입니다. 줄이려면 출력이 아니라 `rag_max_out` / `outline_reference_num` 을 낮춰야 합니다.
2. **reasoning 을 끄는 것이 5배 차이의 일부입니다.** 파일럿은 토큰 카운터에 안 잡히는
   reasoning 토큰이 총액의 16%($0.325)였습니다 — 정가 환산 $1.673 대 실청구 $1.998.
   `deepseek` 계열은 기본이 ON 이라 명시적으로 꺼야 합니다.
3. **검색 레이어를 바꿔도 생성 비용은 거의 안 변합니다.** 입력 토큰량을 정하는 것은
   검색 방식이 아니라 `rag_max_out`·`outline_reference_num` 이기 때문입니다.
   survey-search 는 facet 분해 LLM 호출이 따로 붙지만(호출당 $0.0006) 편당 $0.03 이하입니다.

> **실패한 실행에도 돈이 듭니다.** 3DGS 는 두 번 엎어졌는데(아웃라인 파서 `IndexError`,
> OpenRouter 429) 둘 다 아웃라인 입력 토큰까지는 이미 지불한 뒤였습니다 — 편당 $0.07 정도.

## 5. 품질을 어떻게 담보했나 (생성 쪽)

정답 기준 평가와 **별개로**, 매 실행에서 돈 안 드는 검사를 자동으로 돌립니다.

| 검사 | 무엇을 잡나 | 결과 |
|---|---|---|
| `[TRUNCATED]` / `[EMPTY]` / `[GIVE UP]` 마커 | 응답 잘림·빈 응답·재시도 포기 | **10편 전부 0건** |
| 본문 단어 수·섹션/서브섹션 수 | 구조가 무너진 실행 | 2.0만~3.0만 단어, 8~9섹션 |
| 인용 번호 ↔ 논문 매핑 | 본문 `[n]` 이 엉뚱한 논문을 가리키는 것 | 어댑터에 길이 계약 검사 내장 |
| PDF 3패스 컴파일 | 미해소 인용(`[?]`)·LaTeX 에러 | **전부 0** |
| 날짜 컷오프 게이트 | 코퍼스 밖 논문이 새는 것 | 매 실행 로그로 보고 |

**"조용히 틀리는 것"을 특히 경계했습니다.** 실제로 두 번 겪었습니다 —
어댑터가 필터를 말없이 버린 것, 인용 번호가 순서 계약을 깬 것. 둘 다 예외 없이
그럴듯한 산출물을 냅니다. 그래서 배선 검사를 $0 로 먼저 돌린 뒤에야 생성을 시작합니다
(→ [05-artifacts.md](05-artifacts.md) §3).

## 6. 재현

```bash
cd /data2/chanjoong/survey-agent/SurveyForge && git checkout survey-search-arm
.venv/bin/pip install -e ../survey-search

# 원본 검색 (신 DB arm)
SURVEYFORGE_DB_DIR=database_2026-08 SURVEYFORGE_PAPER_ID_CUTOFF=2608 \
  .venv/bin/python code/run_demo.py "3D Gaussian Splatting"

# survey-search arm
bash scripts/run_survey_search_arm.sh "3D Gaussian Splatting"

# 비교표
.venv/bin/python scripts/compare_runs.py --topic "3D Gaussian Splatting" \
  --run "신 DB=..." --run "survey-search=..." --out out.md
```

원본 검색으로 되돌리는 절차는 [`../README.md`](../README.md) §2 「survey-search arm」.
