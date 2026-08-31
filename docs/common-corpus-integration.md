# asg-common-corpus 통합 설계

브랜치 `common-corpus`. `survey-search` 통합(`survey-search-arm` 브랜치)은 폐기하고,
다른 ASG agent(AutoSurvey, SurveyX, LLM×MapReduce-V2)와 동일한 공용 코퍼스
`../asg-common-corpus`를 검색 데이터로 쓴다. 이 문서는 "무엇을 어디서 바꾸는가"를
구현 전에 고정하기 위한 설계 문서다.

## 0. 결정 요약

| 항목 | 결정 |
|---|---|
| 코퍼스 | `../asg-common-corpus`, 뷰 `surveyeval-2512` (컷오프 2025-12-31, SurveyBench GT 20편 제외, 947,444편) |
| 통합 방식 | 코퍼스가 SurveyForge 네이티브 DB 포맷을 내보내고, **agent 검색 코드는 0줄 수정** (코퍼스 저장소 결정 D3) |
| 포맷 변환 어댑터 | 이미 asg-common-corpus에 존재 (`export-agent-db --format surveyforge`) — 여기서 새로 설계하지 않는다 |
| SurveyForge가 소유하는 것 | 임베딩 인덱스 빌더(신규 `scripts/build_db_from_corpus.py`)와 실행 설정 |
| 임베딩 모델 | 기존과 동일한 `gte-large-en-v1.5` (임베딩은 agent별 통제 변수 — integration-guide §4) |
| 백본 LLM | `meta-llama/llama-3.3-70b-instruct`, OpenRouter provider **`akashml/fp8` 고정** |
| Survey Outline DB | 코퍼스 범위 밖 — 기존 `SurveyForge_data/surveys_*` 유지 (§7) |

## 1. 왜 survey-search가 아니라 공용 코퍼스인가

두 가지가 겹친다.

1. **비교 실험의 전제.** agent 아키텍처 차이를 코퍼스 차이와 분리하려면 모든 agent가
   같은 논문 우주·같은 컷오프·같은 메타데이터를 봐야 한다. asg-common-corpus가 그
   단일 원천이다 (spec §1).
2. **코퍼스 저장소의 결정 D3** (`../asg-common-corpus/docs/decisions.md`)가
   survey-search 백엔드 경로를 명시적으로 기각했다. 공인 경로는 "코퍼스가 agent의
   네이티브 DB 포맷을 생성하고, agent는 입력 경로만 바꾼다"이며, AutoSurvey가 이미
   이 패턴으로 통합을 마쳤다 (`docs/autosurvey-usage.md`).

survey-search-arm에서 얻은 것이 무의미해지는 것은 아니다. 그 브랜치가 확정한
**호스트 인터페이스 표면**(§2.1)과 두 함정(spread 필터, `retrieve_id4citation`의
길이·순서 계약)은 이번 경로에서 검색 스택을 아예 건드리지 않기로 하는 근거가 된다 —
저 표면을 재구현하는 비용·위험 대비, 데이터만 갈아끼우면 SANA의 세 모듈(MS/MR/TRE)이
논문 그대로 보존된다. 특히 ablation에서 기여가 가장 큰 TRE(citation×2년 윈도우
리랭킹, Table 4)는 `citation_count`와 `date` 필드만 맞으면 무수정으로 동작한다.

## 2. 두 시스템의 현재 상태

### 2.1 SurveyForge 검색 스택이 기대하는 것

검색은 두 스택이 분업한다 (`code/main.py:282-289`의 `db` dict).

- **`code/src/rag.py` `GeneralRAG_langchain`** — 실제 논문 검색.
  아웃라인(topic, top_k=1500) → 서브아웃라인(불릿별, 게이트 없음) → 본문(1500 풀을
  `IDSelectorArray`로 잠그고 서브섹션별 top_k=100 → TRE로 60) → 인용 정합
  (title 인덱스, top_k=1, N질의→N id 순서 보존).
- **`code/src/database.py` `database`** — 실행 경로에서는 사실상 **id→레코드 저장소**
  (`get_paper_info_from_ids`만 쓰임). `database_survey`는 아웃라인 예시 검색에 쓰인다.

`--db_path` 디렉터리에서 기대하는 파일과 불변식 (`scripts/append_snapshot.py` 실측 문서):

```
arxiv_paper_db_with_cc.json        TinyDB, root key cs_paper_info, 키 "1","2",… (1-based)
faiss_paper_title_abs_embeddings_*.bin   IndexIDMap(IndexFlatIP), 1024-dim, L2 정규화
faiss_paper_title_embeddings_*.bin       encode(title) / abs쪽은 encode(title+abs) 단순 연결
arxivid_to_index_abs.json          {arxiv_id: stored_id}, 1-based, TinyDB 키와 일치
```

`find_index()`는 glob에 **정확히 하나** 매칭될 때만 통과하므로, 새 코퍼스는 반드시
새 스냅샷 디렉터리에 만들어야 한다 (구 인덱스와 혼용 자체가 불가능하게).

레코드 필드 중 생성 파이프라인이 실제로 읽는 것은 `id, title, abs, date,
citation_count` 뿐이다. `url, cat, authors`는 생성 중엔 안 읽는다
(`code/tools/md_to_tex.py`의 BibTeX 생성만 예외 — §5).

### 2.2 asg-common-corpus가 제공하는 것

- **검색 API 없음 — 의도된 설계다** (spec §10). 임베딩·FAISS·BM25·리랭킹은 전부
  agent 책임. 코퍼스는 메타데이터+초록 parquet과 재현성 사슬(manifest+sha256)만 준다.
- `data/corpus/v0.1-poc/papers.parquet` 947,716편 (CS, arXiv id 100%, 초록 100%,
  1967–2026). `paper_topics.parquet`에 OpenAlex 토픽.
- 뷰 `surveyeval-2512`: 컷오프 2025-12-31(strict), SurveyBench GT 20편 제외, 947,444편.
- **exporter가 이미 있다**: `common-corpus export-agent-db --view surveyeval-2512
  --format surveyforge --out …` → `cs_paper_info` 1-based TinyDB JSON
  (`id, title, url, date, abs, cat, citation_count`) + 사이드카 manifest
  (`content_sha256`, 뷰 sha, `id_convention`). 단 **surveyforge 포맷의 실물 export는
  아직 안 만들어져 있다** (autosurvey 포맷만 존재) — CLI 한 번, ~1분, 1.23 GB.

## 3. 채택 경로

```
[asg-common-corpus]                          [SurveyForge]
surveyeval-2512 뷰
  → export-agent-db --format surveyforge     → SurveyForge_data/database_cc-surveyeval-2512/
      (1.23 GB TinyDB JSON + manifest)            arxiv_paper_db_with_cc.json (이름 변경해 배치)
                                             → scripts/build_db_from_corpus.py (신규, GPU)
                                                  faiss_paper_title_abs_embeddings_*.bin
                                                  faiss_paper_title_embeddings_*.bin
                                                  arxivid_to_index_abs.json
                                             → scripts/check_db.py 재임베딩 검증
                                             → SURVEYFORGE_DB_DIR=database_cc-surveyeval-2512 로 실행
```

- 새 스냅샷 디렉터리는 `database_cc-surveyeval-2512/` 로 한다. 기존
  `database/`(589K, ~2024-09)와 `database_2026-08/`(908K)는 읽기만 하고 남겨서
  A/B 대조를 유지한다 (append_snapshot과 같은 원칙).
- 인덱스 파일명의 `*` 자리에는 뷰 식별자를 박는다
  (예: `faiss_paper_title_abs_embeddings_CC_SURVEYEVAL_2512.bin`) — glob 단일 매칭
  규칙에 맞고, 파일명만으로 어느 코퍼스인지 드러난다.
- 빌드 산출물 옆에 코퍼스 사이드카 manifest를 **복사해 둔다**. 인덱스가 어느
  `content_sha256`에서 나왔는지가 재현성 사슬의 SurveyForge 쪽 끝이 된다.

### 비용 추정

| 단계 | 비용 |
|---|---|
| export (코퍼스 쪽 CLI) | ~1분, 디스크 1.23 GB |
| 임베딩 2회 패스 (title+abs, title) × 947K | 유휴 GPU 실측 68편/s 기준 **패스당 ~4시간, 합 ~8시간** (GPU 공유 시 2배) — `run_detached.sh` 급 분리 실행 필요 |
| 인덱스 디스크 | 947K × 1024 × 4 B × 2 ≈ 7.8 GB + JSON 1.23 GB ≈ **9 GB** |
| LLM 비용 | 없음 (빌드·검증은 전부 로컬) — 파일럿 생성은 별도 지시 후 |

## 4. 어댑터 소유권 — 무엇을 어디서 설계하나

"asg-common-corpus의 어댑터를 SurveyForge에서 설계할 것인가"에 대한 답: **아니다,
포맷 어댑터는 이미 코퍼스 쪽에 있고 그대로 쓴다.** 경계는 이렇게 긋는다.

| 책임 | 소유 | 근거 |
|---|---|---|
| 뷰 정의(컷오프·GT 제외)와 재현성 manifest | asg-common-corpus | 모든 agent가 공유해야 하는 통제 변수 |
| SurveyForge 포맷 변환 (`integrations/survey_search.py`, `FORMATS=("autosurvey","surveyforge")`) | asg-common-corpus | 이미 구현·검증됨. 필드 매핑이 바뀌면 코퍼스 쪽 한 곳만 고치면 됨 |
| 임베딩·FAISS 인덱스 빌드 | **SurveyForge** (`scripts/build_db_from_corpus.py` 신규) | 임베딩 모델은 agent별 통제 변수(integration-guide §4). append_snapshot.py의 불변식·임베딩 규약·검증 코드를 재사용 |
| 실행 설정(.env, 날짜 창, 컷오프 게이트) | SurveyForge | §6 |

코퍼스 쪽에 넘길 요청 두 가지(코퍼스 저장소에서 처리):
1. `surveyeval-2512.surveyforge.json` export 생성 (CLI 한 번).
2. `surveyeval-2512` 뷰가 CLI 플래그로만 만들어져 `benchmark_policy.yaml`의 `views:`에
   없다 — config로 재현 불가능한 상태이니 등록 요청.

## 5. 필드 매핑과 함정

exporter 매핑: `id`=arXiv **base id**, `url`=`http://arxiv.org/abs/<id>`,
`date`=`first_public_date`, `abs`=초록, `cat`=OpenAlex subfield 최고점,
`citation_count`=OpenAlex@2026-02-03.

| # | 함정 | 영향 | 대응 |
|---|---|---|---|
| 1 | **arXiv id에 버전 접미사 없음** (`1209.5292`; 구 DB는 `1811.06122v1`) | 새 DB 내부적으로는 일관되어 무해. 구 DB와의 id 혼용만 금지 | 새 스냅샷 디렉터리로 격리 (§3). 실행 로그·인용 id가 base id로 바뀜을 인지 |
| 2 | **구식 id** (`cs/0503039`) **54,217편** 포함 (코퍼스가 1991-08까지 소급) | YYMM 접두사 컷(`get_index_filter_by_id_prefix`)이 구식 id를 통과시킴 — 다만 check_db 실측대로 구식 id는 전부 2007-04 이전이라 어떤 컷오프에도 안 걸려 무해 | **`--paper_id_cutoff` 게이트를 끈다** — 뷰가 이미 2025-12-31로 잘라서 이중 게이트는 불필요. 서브아웃라인 단계가 원래 게이트 밖이던 비대칭도 함께 소멸 |
| 3 | **TRE 날짜 창 밖 논문 무음 폐기** (`sort_by_citation_period`) | 코퍼스가 1991년까지 있는데 `--paper_date_oldest`가 2012면 그 이전 논문이 조용히 사라짐 | oldest를 뷰 범위에 맞추고(잠정 1991-01-01 / newest 2025-12-31), 매 실행 `report_window_drops()` 확인. 창 개수 증가(~17개)가 TRE 쿼터에 주는 영향은 파일럿에서 관찰 |
| 4 | **`citation_count` 출처 교체** (S2 → OpenAlex@2026-02-03) | TRE 랭킹 분포가 달라짐 | 의도된 변화 — agent 간 인용수 출처 통일이 목적에 부합. 구 DB와 점수 직접 비교만 금지 |
| 5 | **`date` 월 정밀도 44.5만 편** (월초로 저장) | TRE 2년 윈도우엔 무해, 일 단위 정렬만 부정확 | 무대응. manifest의 `date_precision` 통계 인지 |
| 6 | **`authors` 없음, `cat`은 OpenAlex subfield** | 생성 파이프라인은 안 읽음. `md_to_tex.py` BibTeX만 저자 결손·카테고리 상이 | 생성 실험 범위 밖. BibTeX가 필요해지면 arXiv 메타데이터로 후보강 (00-status §8) |
| 7 | **초록의 `\n` 오염 — 실측 확정** (표본 2만: 리터럴 `\n` 10%, 개행 문자 6%, 선두 공백) | 프롬프트·임베딩에 그대로 노출 | **정규화하지 않는다 (결정).** 근거 둘: AutoSurvey가 같은 export를 바이트 그대로 임베딩했으므로 agent 간 텍스트 통일이 우선하고, 리터럴 `\n` 블라인드 치환은 LaTeX 명령(`\nu`, `\nabla`)을 오손한다. 덤으로 스냅샷 JSON = export 사본이 되어 manifest의 `content_sha256`이 파일 지문으로 그대로 유효 |
| 8 | **1-based 불변식 + L2 정규화 + prefix 없음** | 어기면 예외 없이 랭킹만 망가짐 | append_snapshot.py 규약 재사용, check_db.py 재임베딩 검증을 관문으로 |
| 9 | **레코드 947K로 증가** (589K 대비 1.6배) | TinyDB JSON 전체 로드 — 실행당 RAM·기동 시간 증가 | 파일럿에서 기동 실측. 문제가 되면 그때 논의 (검색 코드 무수정 원칙 우선) |

## 6. 백본·실행 설정

백본은 `meta-llama/llama-3.3-70b-instruct`, provider `akashml/fp8` 고정.

```dotenv
SURVEYFORGE_MODEL=meta-llama/llama-3.3-70b-instruct
SURVEYFORGE_PROVIDER=akashml/fp8
SURVEYFORGE_DB_DIR=database_cc-surveyeval-2512
SURVEYFORGE_PAPER_DATE_OLDEST=1991-01-01   # 잠정 — 함정 3
SURVEYFORGE_PAPER_DATE_NEWEST=2025-12-31
# SURVEYFORGE_PAPER_ID_CUTOFF는 설정하지 않는다 — 함정 2
```

**단, `model.py`의 라우팅이 문제다.** `APIModel.__req`는 모델 id 부분 문자열로
분기하는데(`code/src/model.py:102`), `meta-llama/…`는 "deepseek"도 "claude"도 아니라서
중간 분기(raw `requests.post`)로 떨어진다. 이 분기는 (a) `SURVEYFORGE_API_URL`에
`/chat/completions`까지 붙은 전체 엔드포인트를 요구하고, (b) 지수 백오프·
`[PROVIDER]`/`[TRUNCATED]`/`[EMPTY]` 진단이 없는 약한 재시도 경로다. 수만 토큰짜리
호출을 8-thread로 돌리는 파이프라인에서 (b)는 감수할 수 없다.

**제안: `model.py:102`의 분기 조건을 "api_url이 OpenRouter base URL(`/api/v1`로 끝남)
이면 OpenAI SDK 분기"로 바꾼다.** 모델명 하드코딩 목록을 늘리는 것보다 URL 모양으로
라우팅하는 쪽이 다음 백본 교체에도 견딘다. 검색 코드 0줄 원칙(D3)은 코퍼스 통합에
대한 것이고, LLM 클라이언트는 그 경계 밖이다 — 이 저장소는 이미 main에서 model.py를
env 주도로 손봐 왔다. 이것이 이번 통합의 **유일한 소스 코드 수정**이다.

컨텍스트 주의: llama-3.3-70b는 131K ctx다. 1500편 풀 시대의 프롬프트가 DeepSeek
(1M ctx) 기준으로 튜닝된 구간이 있는지 파일럿 첫 실행에서 `finish_reason`과 입력
토큰 수를 로깅해 확인한다.

## 7. Survey Outline DB — 코퍼스 범위 밖

`database_survey`(아웃라인 예시 검색)는 공용 코퍼스가 커버하지 않는다
(00-status §8 결정 6: 아웃라인은 MinerU+LLM 가공 산출물이라 코퍼스의 원천 데이터
원칙에 안 맞음). 기존 `SurveyForge_data/surveys_*`(2024-09, 18,816편)를 그대로 쓴다.

두 가지를 점검 항목으로 남긴다.

1. **GT 누출**: 뷰는 논문 DB에서 SurveyBench GT 20편을 제외했지만, survey DB에는
   같은 서베이가 남아 있을 수 있다. GT 20편의 arXiv id로 `surveys_arxiv_paper_db.json`
   을 조회해서, 있으면 제외 목록을 만들어 아웃라인 예시 검색에서 빠지게 한다
   (DB 재빌드 없이 `get_ids_from_query` 결과 필터링으로 충분한지 구현 시 판단).
2. 컷오프는 2024-09 스냅샷이라 뷰 컷(2025-12-31)보다 이미 보수적 — 추가 조치 불필요.

## 8. 작업 순서

| # | 작업 | 위치 | 상태 (2026-08-31) |
|---|---|---|---|
| 1 | `surveyeval-2512.surveyforge.json` export + 뷰의 config 등록 | asg-common-corpus | **완료** — 947,444편, 12초, `content_sha256=d64bd71d…`. 뷰는 `benchmark_policy.yaml` `views:`에 등록 |
| 2 | `scripts/build_db_from_corpus.py` 작성 | SurveyForge | **완료** — 청크 체크포인트로 재시작 가능, 스모크 2,000편 + check_db 재임베딩 cos 1.000000 통과 |
| 3 | 인덱스 빌드 실행 | GPU 박스 | **진행 중** — GPU 5, detached, `SurveyForge_data/database_cc-surveyeval-2512/build.log` |
| 4 | `check_db.py`로 재임베딩 검증 + manifest 사이드카 배치 | SurveyForge | 함정 8의 관문. 사이드카·build_manifest는 빌드 스크립트가 배치 |
| 5 | `.env` 갱신 + `model.py` 라우팅 수정 | SurveyForge | **완료** — URL 모양(…/v1) 라우팅. 헬로 프로브에서 `[PROVIDER] served by: AkashML` 확인 |
| 6 | survey DB GT 누출 점검 | SurveyForge | **완료** — GT 20편 중 **17편 실재** 확인. `SURVEYFORGE_SURVEY_EXCLUDE_IDS` env로 `database_survey.get_ids_from_query`에서 제외 (상시 켜 둠) |
| 7 | 검증: 기동(로드 시간·RAM), `report_cutoffs_vs_database`, `report_window_drops` | SurveyForge | 빌드 완료 후 |
| 8 | 파일럿 생성 | — | **지시됨 (2026-08-31)**: topic "Edge Computing" 1편 — SurveyBench GT 밖 토픽이라 GT 비교 없는 자유 생성 |

## 9. 검증 계획

- **빌드 정합**: check_db.py 재임베딩 cos ≈ 1.000000, TinyDB 키 == 매핑 값 ==
  IndexIDMap id (1-based 연속), 레코드 수 947,444 == export manifest `records`.
- **컷오프 정합**: `report_cutoffs_vs_database`가 date 최대값 ≤ 2025-12-31을
  보고하는지. GT 20편 id가 DB에 없는지 직접 조회.
- **검색 스택 무수정 확인**: `git diff main -- code/src/rag.py code/src/database.py
  code/src/agents/` 가 비어 있어야 한다 (model.py만 예외).
- **동작 등가성**: 구 스냅샷과 새 스냅샷으로 같은 topic의 아웃라인 단계까지만 돌려
  retrieved id 분포(연도 히스토그램, window drop 수)를 비교 — TRE가 새 날짜 범위에서
  기대대로 동작하는지 본다.
