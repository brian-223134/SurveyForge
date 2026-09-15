# topic 별 retrieval cutoff — GT survey 최초 공개일 이전 문헌만 검색 (2026-09-15, 브랜치 `kisti`)

**규약 (교수님 지시, 2026-09-14):** reference cutoff 를 2025-12-31 로 고정하지 않는다. corpus 는 시간 컷 없는 view
**`kisti-2608`** 전체를 두고(KISTI 는 앞으로 API 로 증분 적재), **retrieval 이 각 topic 의 GT survey 최초 공개일 이전 문헌만**
뽑는다. 규약 정본은 `kisti_data/docs/asg/AGENT-HANDOFF.md` §0, 규칙 정본은 AutoSurvey `docs/retrieval-policy.md`
(4 agent 공통 판정 모듈 `kisti_data/adapter/common/retrieval_policy.py`). 이 문서는 SurveyForge 가 그 규칙을 **어디에, 어떻게**
붙였고 무엇을 확인했는지 적는다. 검색 구조의 배경은 [`retrieval-architecture.md`](retrieval-architecture.md) §9.

## 0. 한눈에

| 항목 | 값 |
|---|---|
| cutoff | topic 별 `retrieval_cutoff_at` = GT 의 가장 이른 공개일 (arXiv 선행판 v1 > Crossref created > published-online). 정책 파일 `AutoSurvey/data/topic_policy.kisti-2608.jsonl` (25행 전부 `ok`; cutoff 값은 view 무관) |
| 판정 | **문헌 공개일의 상한 < cutoff.** day `YYYY-MM-DD` 그 날짜 · month `YYYY-MM` 말일 · year `YYYY` 12-31. 당일 제외, 날짜 없음 제외. 문자열 길이 = 정밀도 |
| 문헌 날짜 | `kisti_data/data/views/kisti-2608/paper_dates.json` **하나만** (view 전편 1,663,704, arXiv id → 투고월 460,772 · DOI → OpenAlex 일 1,198,375 · KISTI 연 4,557). DB 에 복사하지 않는다. export 의 `date`(`YYYY-01-01`)는 쓰지 않는다 |
| 제외 | 정책 행 `exclude_ids`(GT 본체·선행판·사본)는 날짜 무관 차단. outline DB 는 `.env SURVEYFORGE_SURVEY_EXCLUDE_IDS` 36개 ∪ 정책 exclude_ids |
| 적용 | **허용 집합 안에서 검색** — FAISS `IDSelectorBatch` 를 검색 자체에 넘긴다 (전체 Top-K 뒤 사후 필터 아님). 검색 경로 전부 + 직접 조회 + outline DB (§2) |
| topic 지정 | env 하나 `SURVEYFORGE_TOPIC_ID=<slug>`. `main.py` 는 이 값 없이는 돌지 않는다 (`none` 을 주면 정책 없이 = 비교 실험 밖) |
| 구현 | `code/src/retrieval_policy.py`(얇은 층) · `utils.get_retrieval_filter` · `database.py` · `agents/{outline_writer,writer}.py` · `main.py` · `run_demo.py` |
| 기록 | 로그 `[policy] …`, `cutoff_report.log`, `run_manifest.json['retrieval_policy']`, `<topic>.json['retrieval_policy']` (§4) |
| DB | `SurveyForge_data/database_kisti-kisti-2608/` = kisti-2512 v2 인덱스 + 추가분 12,217편 append ([`kisti-integration.md`](kisti-integration.md) §8) |
| 결과 버전 열 | **`c1a0c6b3` / 2026-09-14T13:18:56Z** (view `kisti-2608` papers.parquet sha 앞 8자 · created_at). 기존 실행(Visual Adversarial…, 2026-09-08)은 **v1 · 정책 없음** |
| 채점 분모 | `kisti_data/data/topics.kisti.jsonl` 의 **`n_gt_refs_cutoff`** |

## 1. 판정 규칙 (요약 — 정본은 공통 모듈)

`upper_bound(date) < cutoff`. 예: cutoff `2022-11-03` 에서 `2022-11-02` 허용, `2022-11-03` 제외, `2022-10`(월말 10-31) 허용,
`2022-11`(11-30) 제외, `2021` 허용, `2022` 제외, 날짜 없음 제외. SurveyForge 는 `common.retrieval_policy` 의
`is_allowed · allowed_ids · allowed_summary · parse_day · upper_bound · arxiv_yymm` 을 그대로 부른다 (규칙을 다시 쓰지 않는다).
sidecar 가 view 전편을 덮으므로 DB 의 `no_date` 는 0 이다 — 0 이 아니면 DB 와 sidecar 의 view 가 다른 것이다.

## 2. 어디에 걸리는가

| 검색·조회 경로 | 파일 · 함수 | 종전 | 정책 아래 |
|---|---|---|---|
| 아웃라인 풀 top-1500 | `outline_writer.draft_outline` → `utils.get_retrieval_filter(stage='outline')` | arXiv YYMM 게이트 | 허용 집합 ∩ 게이트 → `IDSelectorBatch` |
| 서브아웃라인 top-50 (섹션 설명 질의) | `outline_writer.generate_subsection_outlines_with_survey` (`suboutline_index_filter`) | **선택자 없음**(원 코드) | 같은 선택자 |
| 집필 풀 top-1500 | `writer.write` → `get_retrieval_filter(stage='writer')` | YYMM 게이트 | 같은 선택자; 서브섹션 질의는 그 풀에 잠금(종전 동일) |
| 인용 정합 (제목 → id top-1) | `writer.replace_citations_with_numbers` | 집필 id 잠금 | 잠금 집합 ∩ 허용 (`[policy/citation]` 로그) |
| TinyDB 직접 조회 | `database.database.get_paper_info_from_ids` | 제한 없음 | 허용 밖 id 차단 (`[policy/lookup]`, `lookup_dropped` 집계) |
| 논문 DB 자체 검색 (파이프라인 미사용) | `database.database.search/batch_search` | 제한 없음 | `SearchParameters(sel=IDSelectorBatch)` |
| outline DB 예시 (human survey 18,816) | `database.database_survey.get_ids_from_query` | env 제외 후필터 | arXiv id **YYMM 상한 < cutoff** ∧ (env ∪ 정책) 제외 → 선택자 안 검색 (`[policy/survey-db]`) |
| 최종 참고문헌 | `main.verify_references_allowed` | — | 위반이면 산출물은 남기고 `run_manifest` 에 기록 후 exit≠0 |

- 종전 id 게이트(`SURVEYFORGE_PAPER_ID_CUTOFF`)는 **대체가 아니라 교집합**으로 남는다. YYMM 게이트는 DOI id 를 통과시키므로
  정책을 대신할 수 없고, 정책 아래에서는 2612 로 두어 아무것도 거르지 않는다(`[policy/<stage>] id 게이트가 … 더 걸렀다` 가 찍히면 값이 잘못된 것).
  TRE 창도 `[1922-01-01, 2026-12-31]` 로 코퍼스 전체를 덮는다 — 허용 집합이 이미 cutoff 이전뿐이라 거르는 역할이 없다.
- outline DB 는 sidecar 밖 자산이라 arXiv id 의 YYMM(v1 투고월, 월 상한)으로 판정한다. 레코드 `date` 는 최신판 날짜라 쓰지 않는다.
  outline DB 가 2024-09 에서 끝나므로 2026년 cutoff topic 에서는 GT 제외 24편만 빠진다.
- 선택자는 `IDSelectorBatch`(해시 집합)라 허용 편수가 120만이어도 검색 수 초다 (`retrieval-architecture.md` §4 의 O(n²) 비용 없음).

## 3. 실행

```bash
# 파일럿 1편 (크레딧 전후 스냅샷 포함) — slug 하나만 준다; 제목은 정책 행의 topic 에서 푼다
scripts/run_pilot.sh physical-adversarial-attacks
# 직접
cd code && SURVEYFORGE_TOPIC_ID=physical-adversarial-attacks ../.venv/bin/python run_demo.py
# LLM 없이 검색 경로 확인 (§6)
cd code && CUDA_VISIBLE_DEVICES=6 ../.venv/bin/python ../scripts/probe_retrieval.py \
    --topic_id physical-adversarial-attacks --expect_allowed physical-adversarial-attacks=1186466 \
    --topic_id kv-cache-serving --expect_2026 kv-cache-serving --out ../eval_out/probe_policy.json
```

| env (`.env`) | 값 | 비고 |
|---|---|---|
| `SURVEYFORGE_TOPIC_ID` | slug | 비우면 `main.py` 가 DB 로드 전에 거부. `none` = 정책 없이(원 코드 게이트만) |
| `SURVEYFORGE_TOPIC_POLICY` | (비움) | 기본 `../AutoSurvey/data/topic_policy.kisti-2608.jsonl` (없으면 2512 정본) |
| `SURVEYFORGE_PAPER_DATES` | (비움) | 기본 `kisti_data/data/views/kisti-2608/paper_dates.json` |
| `SURVEYFORGE_DB_DIR` | `database_kisti-kisti-2608` | |
| `SURVEYFORGE_PAPER_ID_CUTOFF` / `_DATE_OLDEST` / `_DATE_NEWEST` | 2612 / 1922-01-01 / 2026-12-31 | 아무것도 거르지 않는 값 |

`main.py` 가 거부하는 경우(전부 DB 로드 전, 비용 0): topic_id 없음 · 정책 파일에 없는 slug · `status != ok` · `--topic` 문자열이
정책 행의 `topic` 과 다름(잘못된 cutoff 로 $ 를 쓰는 것을 막는다) · 정책 파일/sidecar 없음.

로그 (stdout + `cutoff_report.log`):
```
[policy] topic_id=physical-adversarial-attacks cutoff<2022-11-03 (근거: arxiv:2211.01671 v1 published (twin)) 제외 id 2개 [...]
[policy] sidecar 허용 1,186,466/1,663,704편 -- 제외: exclude_id 0 · no_date 0 · after_cutoff day 332,849 / month 142,636 / year 1,753
[policy/outline] DB 허용 1,186,466/1,663,704편 -- 제외: exclude_id 0 · no_date 0 · after_cutoff 477,238; 허용 id 정렬 sha256 4bee99cd9f46c4fc…
[policy/survey-db] cutoff<2022-11-03 outline DB(human survey) 허용 14,814/18,816편 -- 제외: cutoff 이후 3,978 · GT 제외(env ∪ 정책) 24 · id 형식 불명 0
[policy] 최종 참고문헌 N편 전부 허용 집합 안 (cutoff<2022-11-03)
```

## 4. 기록 — `run_manifest.json['retrieval_policy']`

`topic_id` · `topic` · `retrieval_cutoff_at` · `gt_first_public_at` · `gt_first_public_source` · `exclude_ids` · `status` ·
`corpus_snapshot_id` · `policy_file`(+sha256) · `rule` · `sidecar{path, meta(created_at·view·view_papers_sha256·view_created_at·records·
by_precision·by_source·rule)}` · `view_sha256` · `view_created_at` · `sidecar_allowed/total/excluded/dated_by_precision` ·
`db_records` · **`allowed`** · **`allowed_fingerprint_sha256`**(허용 id 정렬 sha256, AutoSurvey `fingerprint` 와 같은 식) ·
`db_excluded{exclude_id,no_date,after_cutoff}` · `excluded_ids_present_in_db` · `reference_violations` · `outline_db`(허용/제외 편수) ·
`direct_lookup_dropped`. 최상위에 `topic_id`, `db_build.append`(base 편수·view·추가 편수·stored id 범위).
`<topic>.json` 에도 `retrieval_policy{topic_id, retrieval_cutoff_at, exclude_ids, reference_violations}`. 정책 없는 실행은 `retrieval_policy: null`.

## 5. 테스트 · 검증 (2026-09-15, LLM 호출 0)

| 검사 | 결과 |
|---|---|
| `tests/test_retrieval_policy.py` (8) | 판정 위임 경계 · db_view 순서/집계/지문 · **지문 == AutoSurvey.fingerprint** · 가짜 IndexIDMap 에서 k > 허용 편수여도 허용분만, 선택자 결과 == 전체 순위의 허용 부분열(사후 필터가 아니라는 증거) · 게이트 교집합 · outline DB YYMM 규칙 · 실제 정책 파일+sidecar(허용 1,186,466 / 1,663,704, 불일치·미지 slug 거부) · `main.validate_cutoffs` 거부 — **8/8** |
| `tests/test_kisti_corpus.py` (kisti-2608 DB) | view/export sha256 정합, append 본 검사(base 접두 보존·추가분 stored id 1651488..1663704·DB id 집합 == 전체 export), 제외 키 40개 부재, twin 16개 .env 포함, id→DOI→원문, gte+FAISS 질의(연도 1922..2026) — **8/8** |
| `tests/test_cutoffs.py` | 종전 게이트·TRE 특성화 **10/10** (정책 없는 경로는 그대로) |
| `scripts/check_db.py --verify-embeddings 20` | 1..1,663,704 전단사, 재임베딩 cos **1.000000** (신규 구간 10건 포함) |

`scripts/probe_retrieval.py` — 파이프라인과 같은 객체·호출로 세 topic (`docs/experiments/retrieval-policy-probe.kisti-2608.json`), 기동 105s:

| topic_id | cutoff | 허용 (sidecar = DB) | 허용 id sha256 | 아웃라인 1,500 · 서브아웃라인 50 · 리랭크 · 인용 5 · outline DB 20 위반 | 가장 늦은 허용 날짜 (풀) | 2026년 (풀 / 리랭크) | 직접 조회 차단 |
|---|---|---:|---|---|---|---|---|
| physical-adversarial-attacks | 2022-11-03 | **1,186,466** (AutoSurvey 와 동일) | **`4bee99cd9f46c4fc…`** (AutoSurvey 와 동일) | 0 · 0 · 0 (61편) · 0 · 0 | 2022-11-02 | 0 / 0 | after-cutoff 1 + 제외 id 2 → 반환 0 |
| kv-cache-serving | 2026-07-01 | 1,663,704 (전편) | `ab09ca72fcb7959b…` | 0 · 0 · 0 (63편) · 0 · 0 | 2026-01-22 | **39 / 1** | 제외 id 1 → 반환 0 |
| llm-training-data-detection | 2026-01-07 | 1,653,071 | `44a010367d2bb75f…` | 0 · 0 · 0 (64편) · 0 · 0 | 2025-12-30 | 0 / 0 (1월 문헌은 상한 규칙으로 제외) | after-cutoff 1 + 제외 id 1 → 반환 0 |

- 세 topic 모두 TRE 창 폐기 0/100, 인용 정합 자기-적중 5/5, outline DB 예시 20편 위반 0 (physical-adversarial 은 human survey 3,978편이 cutoff 이후로 빠져 14,814편 안에서 검색).
- 허용 편수·지문이 AutoSurvey 와 같으므로 두 agent 의 허용 집합은 **id 단위로 동일**하다 (같은 view, 같은 sidecar, 같은 규칙).
- 비교: 정책 없는 종전 실행(§0 결과 버전 열 v1)은 physical-adversarial 풀 1,500 중 cutoff 이후 문헌이 절반 이상이었다 (AutoSurvey 스모크 526/1,200).

### 5.1 정책 아래 첫 생성 (2026-09-15)

physical-adversarial-attacks 1편, 21분 · $0.40: refs 91편(DOI 59) 전부 허용 집합 안, 연도 2017~2022, GT 누수 0,
적중 23/128 → **recall 18.0% · precision 25.3%**. 정책 없는 종전 실행(129편)은 같은 분모로 25/128 이지만 refs 의 40편이 cutoff
이후 문헌이었다 — 정책이 그 40편을 검색 단계에서 없앴고 recall 은 오차(±1.7%p) 안에서 같다. 상세는 [`kisti-integration.md`](kisti-integration.md) §8.4,
채점 `scripts/score_run.py`.

## 6. 한계·미결

1. **arXiv 레코드의 판** — KISTI arXiv 레코드는 버전 없는 키라 초록이 최신판일 수 있다. 월 상한으로 v1 이 cutoff 이전임은 보장하지만 초록이 v1 것이라는 보장은 없다 (AutoSurvey 와 공통, 미착수).
2. **2026년 arXiv 초록 결손** — `2602.*`~`2606.*` 는 초록이 없어 view 에서 빠진다. 회수는 corpus 측 결정 대기; SurveyForge 는 시도하지 않는다.
3. **outline DB 의 날짜 정밀도** — YYMM 월 상한뿐. cutoff 당월의 human survey 는 제외된다(보수적).
4. **정책 없는 실행 경로**(`topic_id=none`)는 종전 게이트·env 제외만 남아 있다 — 비교 실험에 쓰지 않는다.
5. 기존 파일럿(2026-09-08)은 재실행 대상. 25편 본배치는 편당 약 $0.6 · 50분(검색 오버헤드는 이제 수 초) — 사용자 지시 후.

## 7. 하지 않은 것 (지시)

`KISTI_VIEW` 기본값 변경 · 2026년 arXiv 초록 결손 회수 · outline DB 교체.
