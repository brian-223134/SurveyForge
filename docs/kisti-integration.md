# KISTI DB 통합 (브랜치 `kisti`)

**2026-09-07.** asg-common-corpus(bench-2512)는 이날부로 쓰지 않는다. SurveyForge 는 다른 세 ASG agent
(AutoSurvey · SurveyX · LLM×MapReduce-V2)와 같은 **KISTI Science Data Lake 파생 스토어의 view `kisti-2512`** 를
검색 corpus 로 쓴다. 정본은 `/data2/chanjoong/kisti_data/docs/asg/surveyforge.md`(설계·함정)와
`kisti_data/adapter/README.md`(실행 순서)이며, 이 문서는 SurveyForge 쪽에서 실제로 무엇을 바꿨고 무엇을
확인했는지만 적는다.

## 0. 결정 요약

| 항목 | 값 |
|---|---|
| corpus | view `kisti-2512` — 1,651,701편, `year ≤ 2025`, GT 본체 25 + twin 15 제외. arXiv id 455,171 (27.6%) · DOI id 1,196,530 (72.4%) |
| id 규칙 B | `10.48550/arxiv.<id>` → arXiv base id, 그 외 DOI 소문자. **agent 는 id 를 불투명 키로 다룬다** |
| 논문 DB | `SurveyForge_data/database_kisti-kisti-2512/` — `kisti_data/adapter/surveyforge/build_db.sh` 가 `scripts/build_db_from_corpus.py` 로 빌드 (gte-large-en-v1.5, batch 8) |
| outline DB | corpus 밖 자산 그대로 (human survey 18,816편). `SURVEYFORGE_SURVEY_EXCLUDE_IDS` 35개 유지 — KISTI twin 15편이 이 안에 있음을 대조로 확인 |
| 백본 | `meta-llama/llama-3.3-70b-instruct` @ OpenRouter, provider `akashml/fp8` 고정 |
| 디코딩 | **temperature 0.6 · max_tokens 8,192 · 가드에 걸린 응답은 버리고 재요청** (4 agent 공통, `kisti_data/docs/asg/AGENT-HANDOFF.md` §4) |
| 분량 | 통제하지 않는다. `run_demo.py` 기본 인자 그대로 |
| 검색 스택 | `rag.py`·`agents/` 수정 0줄. 바꾼 것은 LLM 클라이언트, 보고/기록, 후처리뿐 (§2). 구조는 `docs/retrieval-architecture.md` |

## 1. 브랜치

`kisti` 는 **main(37050f3)에서 분기**했고, common-corpus 브랜치에서 corpus 에 독립적인 인프라 커밋 7개만
cherry-pick 했다 (`build_db_from_corpus.py`, model.py URL 라우팅, outline DB 제외 훅, `check_credits.py`,
.gitignore). bench-2512 산출물·설계 문서는 가져오지 않았다 — 그 브랜치가 기록으로 남는다.
main 은 건드리지 않았다.

## 2. 바꾼 것

| 파일 | 변경 | 이유 |
|---|---|---|
| `code/src/model.py` | `SURVEYFORGE_TEMPERATURE` 전역 오버라이드 | 호출부 7곳이 `temperature=1` 하드코딩 — 공통 프로파일 0.6 을 받을 길이 없었다 |
| 〃 | `finish_reason=length` 면 버리고 재요청 (`SURVEYFORGE_RETRY_TRUNCATED`, 기본 on), 재시도 소진 시 수용 | 8K 가드에 걸린 응답은 llama 반복 루프의 신호. AutoSurvey `baa46cc` 와 같은 규칙 |
| 〃 | `LLM_STATS` 집계 + `[DECODING]` 로그 | 편당 기록 항목(재요청·잘림 수) |
| `code/main.py` | `[cutoff/db]` 가 DOI id 를 "형식 불명"이 아니라 DOI 로 센다. 파싱 가능한 id 가 0이어도 죽지 않음 | DOI 72% 인 DB 에서 정상 상태가 정상으로 읽혀야 한다 |
| 〃 | 실행 끝에 `run_manifest.json` | 모델·provider·temperature·max_tokens·llm_stats·컷오프·DB 지문(build_manifest)·refs 수(DOI 분 포함) |
| `code/tools/md_to_tex.py` | DOI id 는 `doi:` 키·`DOI:` 라벨·doi.org 링크(레코드 url 우선)·BibTeX `doi=` 필드. `☆★` 제거 | 종전엔 모든 id 를 arXiv 로 링크했다. 채점과 무관, PDF 표기용 |
| `scripts/build_db_from_corpus.py` | id 형식(arXiv/DOI/기타) 집계 → 로그·`build_manifest.id_formats`. 인덱스 태그에서 `CC_` 접두사 제거 | 가정이 아니라 기록. 태그는 view 이름(`KISTI_2512`) |
| `scripts/check_db.py` | 요약이 DOI id 를 따로 센다 | 종전 문구는 DOI 를 "구형 arXiv id" 로 오독 |
| `scripts/probe_retrieval.py` (신규) | LLM 없이 RAG 기동 + 아웃라인 검색 + citation 리랭크 한 번 | 새 스냅샷의 DOI 비율·연도 분포·TRE 창 폐기를 비용 0 으로 확인 |

## 3. 실행 설정 (`.env`)

| 키 | 값 | 비고 |
|---|---|---|
| `SURVEYFORGE_DB_DIR` | `database_kisti-kisti-2512` | |
| `SURVEYFORGE_MAX_TOKENS` | `8192` | 16,384 → 8,192. bench-2512 파일럿에서 16K 에 닿은 호출 2건 — 첫 파일럿의 `llm_stats` 로 어느 호출인지 확인 |
| `SURVEYFORGE_TEMPERATURE` | `0.6` | |
| `SURVEYFORGE_RETRY_TRUNCATED` | (비움 = on) | |
| `SURVEYFORGE_PAPER_ID_CUTOFF` | **`2512`** | view 에 arXiv `2601.*` 논문 212편이 KISTI `year=2025` 로 들어와 있다(빌드 후 check_db 실측). 2026-01 투고분이라 컷오프 밖이고 이 게이트가 아웃라인·집필 양쪽에서 거른다(`… 212 excluded` 가 정상). DOI·구형 id 는 게이트를 그냥 통과 |
| `SURVEYFORGE_PAPER_DATE_OLDEST` | **`1922-01-01`** | view 연도 범위 1922..2025. kisti_data 문서의 1991 은 1922~1990 논문을 TRE 창 밖으로 무음 폐기한다 |
| `SURVEYFORGE_PAPER_DATE_NEWEST` | `2026-01-01` | date 가 `YYYY-01-01` 이라 2025 논문이 마지막 창에 든다 |
| `SURVEYFORGE_SURVEY_EXCLUDE_IDS` | 35개 유지 | |

## 4. 검증 (2026-09-07, 비용 ≈ 0)

| 검사 | 결과 |
|---|---|
| 스모크 빌드 1,000편 (`--limit 1000`) | 키 1..n 연속, 필드 OK, id 형식 집계 출력(앞 1,000편은 전부 arXiv), 정합성 OK |
| `check_db --verify-embeddings 4` (스모크) | 키/매핑/두 인덱스 전단사, 재임베딩 cos **1.000000** |
| `probe_retrieval.py` (스모크 DB) | 기동·`[cutoff/db]`·아웃라인 검색·citation 리랭크 동작, 창 `[1922-01-01, 2026-01-01]` 폐기 0/30 |
| model.py 프로브 A (`MAX_TOKENS=5`, `chat` 5회) | `[DECODING] temperature=0.6`, `[PROVIDER] AkashML`, 4회 재샘플 후 수용, `truncation_retries=4 truncated_accepted=1` |
| model.py 프로브 B (정상 프로파일 `hello`) | 정상 응답, 잘림 0 |
| temperature 프로브 (0 / 0.6 / 1.0 × 4, 실제 서브섹션 프롬프트) | 잘림·반복 0, 길이·인용 수 둔감 — `docs/experiments/temperature-probe.md` |
| `md_to_tex.py --compile` (arXiv 1 + DOI 3, `<>;()` 든 DOI 포함, 가짜 DB) | pdflatex 3패스 성공. DOI 항목은 `DOI:` 라벨·doi.org 링크·BibTeX `doi=`; 특수문자 DOI 는 cite 키만 `_` 로 치환하고 링크는 원문 유지; `☆` 제거 확인 |

## 5. 빌드

```
CUDA_VISIBLE_DEVICES=3 KISTI_VIEW=kisti-2512 bash /data2/chanjoong/kisti_data/adapter/surveyforge/build_db.sh
# 로그: eval_out/build_kisti-2512.log   (중단되면 같은 명령으로 재개 — 청크 체크포인트)
```

| 항목 | 값 |
|---|---|
| 시작 / 완료 | 2026-09-07 23:55 → 2026-09-08 06:34 (GPU 3, **6h39m**, check_db 포함) |
| 처리량 | title+abs 70→77편/s (batch 8, 장문 초록 때문에 스모크의 118편/s 보다 느림), title 676편/s |
| 산출 | `database_kisti-kisti-2512/` **16GB** — `arxiv_paper_db_with_cc.json`(export 사본 2.38GB, sha256 `49706624…` 일치) + FAISS 2종 각 6.78GB (`*_KISTI_2512.bin`) + id map 54MB + `build_manifest.json` + outline DB 자산 4종 |
| 정합성 | 키/매핑/두 인덱스 1..1,651,701 전단사. `id_formats` arXiv 455,171 · DOI 1,196,530 · 기타 0 (view manifest 와 일치). 날짜 1922-01-01 .. 2025-01-01 |
| check_db | 재임베딩 20건 × 2필드 **cos 1.000000** |
| 발견 | 신형 arXiv id 접두사 최대 **2601** — `2601.*` 212편이 `year=2025` 로 view 에 포함. → `.env` id 게이트 2512 (§3). 구형 arXiv id 25,872편, 신형 429,299편 |
| 후속 | `tests/test_kisti_corpus.py` 전체, `scripts/probe_retrieval.py` (아래 §5.1) |

### 5.1 빌드 후 검증

(테스트·프로브 결과는 실행 완료 후 기록)

## 6. 실행 절차

1. topic 문자열은 `kisti_data/data/topics.kisti.jsonl` 의 `title` 그대로.
2. `scripts/check_credits.py --label before-<slug>` → `cd code && python run_demo.py --topic "<title>"` → `check_credits.py --label after-<slug>`.
3. 산출물 `code/output/res/meta-llama_llama-3.3-70b-instruct__database_kisti-kisti-2512/<topic>/exp_1/` 의
   `run_manifest.json`(llm_stats·refs·DB 지문)과 `cutoff_report.log`(`[cutoff/db] … DOI ids (pass the id gate)`, `[cutoff/rerank]` 0) 확인.
4. 누수: GT DOI·twin arXiv id·twin 제목이 본문·refs 에 0회.
5. PDF 가 필요하면 `python tools/md_to_tex.py <exp_1> --compile` — 스냅샷은 경로에서 되짚는다.

## 7. 남은 위험

- **8K 가드 vs SurveyForge 의 큰 호출.** 아웃라인 병합·LCE 정리 호출이 정당하게 8K 를 넘으면 매 시도 가드에 걸려
  재시도를 소진하고 잘린 채 수용된다(`truncated_accepted > 0`). 첫 파일럿에서 반드시 본다.
- **검색 오버헤드.** rag.py 가 retrieve 마다 벡터스토어를 재인스턴스화한다 — 947K 에서 대형 검색 1회 ~250s 였으니
  1.65M 에서는 실행당 15분 안팎. 25편이면 6시간 남짓의 순수 오버헤드. 최적화 후보.
- **OpenRouter 키.** AutoSurvey 와 같은 키, 잔여 약 $5.4 / 한도 $30. 편당 $0.4 안팎 × 25편 + AutoSurvey 분 → 한도 상향 필요.
- **DOI 논문 저자.** export 에 authors 가 없어 `.bib` 은 DOI 논문도 제목·연도·링크만. `kisti_data/data/views/kisti-2512/authors.parquet` 로 후처리 가능(미구현, 채점 무관).
- **corpus 쪽 컷오프 누수 (전 agent 공통).** view 규칙 `year ≤ 2025` 는 KISTI `year` 에 의존하는데, arXiv `2601.*` 212편이 `year=2025` 로 통과했다.
  SurveyForge 는 id 게이트로 막지만 AutoSurvey 등 id 게이트가 없는 agent 는 이 212편을 검색한다. DOI 논문에도 같은 연도 오류가 있을 수
  있고 그것은 어느 agent 도 못 가린다 → view 생성기에 `arXiv YYMM ≤ 2512` 규칙 추가와 DOI 발행일 재검토를 corpus 쪽에 요청할 것.
