# SurveyForge 검색 구조 — corpus 에서 무엇을, 어떻게 가져오는가

**2026-09-08.** 코드 기준: `code/main.py` · `code/src/rag.py` · `code/src/faiss_param.py` · `code/src/utils.py` ·
`code/src/database.py` · `code/src/agents/{outline_writer,writer}.py`. 실측치는 bench-2512 실행 2편(Edge Computing,
Instruction Tuning)의 `time_cost.log`·`rag_outline_subset_ids.jsonl`·`total_ids.txt`에서 뽑았다.
KISTI 로 옮기면서 검색 스택은 한 줄도 바꾸지 않았다 — 바뀐 것은 입력(스냅샷)뿐이다 (§7).

## 0. 한눈에

```
 corpus (KISTI view kisti-2512, 1,651,701편)
   │  adapter export → TinyDB JSON {id,title,url,date,abs,cat,citation_count}
   │  build_db_from_corpus.py → gte-large-en-v1.5 임베딩 2종 (title+abs / title), 1-based id map
   ▼
 스냅샷 database_kisti-kisti-2512/            outline DB (corpus 밖, human survey 18,816편)
   ├ arxiv_paper_db_with_cc.json  ─┐            ├ surveys_arxiv_paper_db.json
   ├ arxivid_to_index_abs.json     │            ├ faiss_survey_title_abs_embeddings_*.bin
   ├ faiss_paper_title_abs_*.bin   │            └ Final_outline{,_First}/<id>.md
   └ faiss_paper_title_*.bin       │
                                   ▼
 [1] 아웃라인   topic ──gate──▶ abs 인덱스 top-1500 ─▶ 30K-token 청크 ×(초록 + 서베이 예시 5) ─▶ 거친 아웃라인들
                ─▶ 최신 서베이 5편의 아웃라인과 병합 ─▶ 섹션 아웃라인
 [1'] 서브아웃라인 섹션 설명 ─▶ abs 인덱스 top-50 (게이트·풀 잠금 없음, 'survey' 제목 제거) ─▶ 서브섹션 아웃라인
 [2] 집필       topic ──gate──▶ abs 인덱스 top-1500 = 풀(IDSelector 잠금)
                서브섹션 질의(제목+하위질의) ─▶ 풀 안 top-100 ─▶ 합집합 ─▶ TRE(2년 창 × citation_count) ─▶ ≤60편
                ─▶ 초록 60편 프롬프트 ─▶ 초안 ─▶ 인용 검사 ─▶ LCE 정리
 [3] 인용 정합   본문의 [제목] ─▶ title 인덱스 top-1 (집필 단계에서 검색된 id 안에서만) ─▶ [n] 번호 ─▶ <topic>.json
```

## 1. 데이터 층 — 스냅샷 디렉터리 (`--db_path`)

| 파일 | 내용 | 불변식 |
|---|---|---|
| `arxiv_paper_db_with_cc.json` | TinyDB `{"cs_paper_info": {"1": rec, "2": rec, …}}`. rec = `id, title, url, date, abs, cat, citation_count`. **export 파일의 바이트 동일 사본** | 키 `"1"…"n"` 연속 |
| `arxivid_to_index_abs.json` | `{id: k}` | k == TinyDB 키 == FAISS stored id (1-based) |
| `faiss_paper_title_abs_embeddings_<TAG>.bin` | `IndexIDMap(IndexFlatIP)`, 1024-d, `encode(title + abs)` — 구분자 없이 이어붙임, L2 정규화, 프롬프트 접두사 없음 | glob 이 **정확히 1개** 매칭돼야 기동 (`find_index`) |
| `faiss_paper_title_embeddings_<TAG>.bin` | 같은 규약으로 `encode(title)` | 〃 |
| `build_manifest.json` · `corpus_export_manifest.json` | 빌드 지문(export sha256·id 형식 집계·태그) · export manifest 사본 | run_manifest 가 인용 |
| `surveys_*` 4종 + `Final_outline{,_First}/` | outline DB. human survey 의 title+abs 임베딩과 MinerU 가공 아웃라인 | corpus 와 무관. GT 서베이는 `.env` 제외 목록으로 거른다 |

임베딩 모델은 질의 쪽과 문서 쪽이 같아야 한다 (`gte-large-en-v1.5`, `SurveyForge_data/gte-large-en-v1.5`).
`check_db.py --verify-embeddings` 가 저장 벡터를 재임베딩과 대조한다 (cos 1.000000 이 관문).

## 2. 기동 (`main.py main()`)

| 객체 | 읽는 것 | 용도 |
|---|---|---|
| `database(db_path)` | TinyDB JSON 파싱 (+ 자체 FAISS 로드) | **id → 레코드 조회만** 쓴다 (`get_paper_info_from_ids`, TinyDB `Query().id.one_of` = 선형 스캔) |
| `database_survey(db_path)` | outline DB 4종 | 아웃라인 예시 검색 `get_ids_from_query(topic, n)`; `SURVEYFORGE_SURVEY_EXCLUDE_IDS` 로 GT 서베이 제외 |
| `GeneralRAG_langchain(abs)` | `faiss.read_index` + JSON 파싱 → `Document(page_content=abs, metadata=나머지)` 리스트 + `InMemoryDocstore` + `index2id` | outline / suboutline / subsection 검색 (셋이 **같은 객체**) |
| `GeneralRAG_langchain(title)` | title 인덱스 + JSON 파싱 | 인용 정합 |

같은 JSON 을 세 번 파싱한다(TinyDB 1 + RAG 2). 질의 임베딩은 `HuggingFaceEmbeddings(gte, cuda)`.
기동 직후 `report_cutoffs_vs_database` 가 `[cutoff/db]` 로 편수·최신 arXiv id·날짜 범위·**DOI id 수**를 찍는다.

## 3. 단계별 검색

### 3.1 아웃라인 (`outlineWriter.draft_outline`, `--outline_reference_num 1500`)

1. **게이트**: `get_index_filter_by_id_prefix(id_to_index, paper_id_cutoff)` — arXiv id 의 YYMM 이 컷오프 이하인 id 전부를
   `IDSelectorArray` 로 만든다. **파싱되지 않는 id(DOI·구식)는 통과**시킨다(조용히 잃는 것이 이 장치가 막으려는 실패라서).
   `[cutoff/outline] … N/N retrievable, 0 excluded` 로 기록.
2. `rag_outline.retrieve_id(topic, top_k=1500)` — 질의 1개, 코사인(정규화 벡터의 IP) top-1500, rerank `raw`.
3. `database.get_paper_info_from_ids` 로 제목·날짜·초록을 받아 `chunking(chunk_size=30000 tokens)` 으로 나눈다
   (실측 3~4 청크). 청크마다 outline DB 예시 5편(`get_ids_from_query(topic, 20)` → 아웃라인 파일이 있는 것만 → 5)을
   붙여 거친 아웃라인을 만든다 (`ROUGH_OUTLINE_WITH_SURVEY_PROMPT`, batch).
4. 병합: `get_ids_from_query(topic, 10)` → 두 아웃라인 디렉터리에 다 있는 것 → 날짜 내림차순 5편의
   `Final_outline_First/<id>.md` 를 예시로 `MERGING_OUTLINE_WITH_SURVEY_PROMPT` (단일 호출) → 섹션 아웃라인.
5. **서브아웃라인** (`generate_subsection_outlines_with_survey(rag_num=50)`): 첫/끝 섹션을 뺀 각 섹션의 설명(리스트면 항목별)로
   `retrieve_id("{topic}:{설명}", top_k=50//len(설명)*5)` — **게이트도 풀 잠금도 없다**(원 코드 그대로). 합집합 → TinyDB 조회 →
   제목에 'survey' 가 든 것 제거 → 50편 초과면 무작위 50 → `SUBSECTION_OUTLINE_WITH_SURVEY_PROMPT` → `edit_final_outline`.

산출물(`--debug`): `1-Total_1500_papers.txt`(풀 제목), `1-Chunk_outlines.json`, `Survey_titles_{rough,high}.txt`,
`2-Merged_outlines*.txt`, `3-Merged_Sub_outline*.txt`, `outlines_with{,out}_des_<ts>.txt`.

### 3.2 집필 (`subsectionWriter.write`, `--rag_num 100 --rag_max_out 60 --subsection_len 500`)

1. 게이트를 다시 걸고(`[cutoff/writer]`) `retrieve_id([topic], top_k=1500)` 로 **집필 풀**을 뽑는다 → `rag_outline_subset_ids.jsonl`.
   이 1,500 id 로 `IDSelectorArray` 를 만들어 이후 모든 서브섹션 검색을 **풀 안으로 잠근다**.
2. 아웃라인 파싱 → 섹션/서브섹션/설명/**하위 질의**(아웃라인 단계가 서브섹션마다 써 둔 질의 문장들).
3. 서브섹션마다 질의 = `"{서브섹션 제목(번호 제거; Introduction/Conclusion 이면 빈 문자열)} {하위 질의}"` × 하위 질의 수
   (없으면 설명 1개). `retrieve_id(질의들, rerank='citation', top_k=100, max_out=60, id_selector=풀)`:
   - 질의별 풀 안 top-100 → `_unite('union')` 순서 보존 중복 제거 → **TRE** `sort_by_citation_period(top_k=60, period=2)` (§5)
   - 산출: 서브섹션당 ≤60편 (창별 `ceil` 때문에 60 을 약간 넘을 수 있다). `rag_docs_writer_{unique,rerank}.jsonl` 에 기록.
4. 전체 서브섹션의 id 합집합을 TinyDB 에서 **한 번에** 조회 → 서브섹션별 `paper_texts`
   (`---\n\npaper_title: …\n\npaper_content:\n\n<초록>\n` 반복) → `SUBSECTION_WRITING_PROMPT`(`WORD NUM 500`, `CITATION NUM 8`)
   → 초안(batch, 섹션 병렬 `MAX_SECTION_THREADS` × 서브섹션 병렬 `MAX_THREADS`) → `CHECK_CITATION_PROMPT` → `LCE_PROMPT`(이웃 서브섹션과 정리).
5. `writer_rag_results` = 집필 단계에서 검색된 모든 id (`total_ids.txt`) — 인용 정합의 후보 집합.

LLM 은 프롬프트에 있는 제목만 `[제목]` 형식으로 인용할 수 있다. 검색이 못 가져온 논문은 어느 단계에서도 인용될 수 없다.

### 3.3 인용 정합 (`replace_citations_with_numbers`)

본문에서 `[제목; 제목]` 을 뽑아 **title 인덱스**에 질의하되 `writer_rag_results` 로 잠근다 → 질의 N개 → id N개 (순서 보존, 리랭크 없음, top-1)
→ TinyDB 제목 → `[n]` 번호 → `<topic>.json["reference"] = {n: id}`. LLM 이 제목을 조금 바꿔 써도 가장 가까운 검색 id 로 붙는다.
실측: 최종 refs 101/135편이 전부 집필 id 안에 있었고, 집필 id 384/525편이 전부 1,500 풀 안에 있었다 — 잠금이 동작한다.

## 4. 게이트·풀 잠금의 실제 구현과 비용

langchain 의 `FAISS.similarity_search_with_score_by_vector` 는 `id_selector` 를 무시한다. SurveyForge 는
[faiss_param.py](../code/src/faiss_param.py) 의 서브클래스 `FAISS_param` 으로 이 메서드를 덮어 `kwargs['id_selector']` 가 있으면
`index.search(v, k, params=faiss.SearchParametersIVF(sel=selector))` 로 넘긴다. `rag.py` 는 이 클래스를 `FAISS` 라는 이름으로 쓴다.

선택자는 늘 `faiss.IDSelectorArray(list_of_stored_ids)` 다. **IDSelectorArray 의 멤버십 검사는 배열 선형 탐색**이라, 검색 비용은
`(인덱스 편수) × (선택자 길이)` 에 비례한다.

| 검색 | 선택자 길이 | 실측 (bench-2512, 947K) | 추정 (KISTI, 1.65M) |
|---|---|---|---|
| 아웃라인 풀 top-1500 (게이트 = 전체 DB) | 947,451 | **250s** | ≈ 760s |
| 집필 풀 top-1500 (게이트 = 전체 DB) | 947,451 | **250s** | ≈ 760s |
| 서브섹션 검색 (풀 1,500 잠금) × ~40 | 1,500 | 중앙값 0.9s | ≈ 1.5s |
| 서브아웃라인 검색 (선택자 없음) | — | ~1s | ~2s |
| 인용 정합 (writer ids 잠금) | 384~525 | 4~6s | 비슷 |

실행당 검색 합계 539~545s 중 500s 가 두 번의 전체-DB 선택자 검색이다. KISTI 파일럿(v1) 실측은 760s + 761s = 실행 50분의 절반.

**등가성 실측 (2026-09-08, v2, `scripts/probe_selector.py`, `docs/experiments/selector-equivalence.json`)** — 같은 질의, 같은 허용 id 집합:

| 선택자 | 소요 | top-1500 id 목록 |
|---|---|---|
| `IDSelectorArray` (현행) | **761.5s** | 기준 |
| `IDSelectorBatch` (해시 집합) | **3.3s** | 순서까지 동일 |
| 없음 (게이트 0 제외일 때) | 1.3s | 순서까지 동일 |

즉 바뀌는 것은 멤버십 검사의 자료구조뿐이고 검색 대상 집합·점수·순위·TRE 는 그대로다(agent 논리 무관). 적용은 `utils.get_index_filter` 의
`faiss.IDSelectorArray(results_index)` 한 줄을 `IDSelectorBatch` 로 바꾸는 것. **2026-09-08 현재 미적용** — 사용자 결정 대기.

## 5. TRE — citation 리랭크의 세부 (`utils.sort_by_citation_period`)

- 창: `get_time_windows(oldest, newest, period=2)` — `oldest` 부터 2년씩, 마지막 창은 `newest` 에서 잘린다. 양끝 포함.
- 창마다 그 창의 문서를 `citation_count` 내림차순으로 `ceil(60 / 전체 문서 수 × 창 문서 수)` 편 남긴다. 즉 **연도별 비례 할당** —
  오래된 창은 문서가 적어 `ceil` 로 1편은 살아남는다.
- **어느 창에도 안 드는 문서는 무음 폐기**되고 그 수가 `[cutoff/rerank]` 에 누적된다. `oldest` 를 corpus 하한보다 위에 두면 그
  이전 논문이 여기서 사라진다 — KISTI view 는 1922 년부터라 `.env` 의 `SURVEYFORGE_PAPER_DATE_OLDEST=1922-01-01`.
- KISTI 는 `date` 가 `YYYY-01-01` 뿐이라 창은 사실상 **연도 2개 묶음**이다(예: 2024·2025). 정밀도는 그뿐이고 동작은 같다.

## 6. 통제 변수 — 어디에 사는가

| 변수 | 위치 | 값 (KISTI 실험) |
|---|---|---|
| corpus·컷오프·GT/twin 제외 | kisti_data view `kisti-2512` → export → 스냅샷 | year ≤ 2025, 38키 제외 |
| outline DB 의 GT 서베이 제외 | `.env SURVEYFORGE_SURVEY_EXCLUDE_IDS` | 35개 (KISTI twin 15 포함) |
| id 게이트 / TRE 창 | `.env SURVEYFORGE_PAPER_ID_CUTOFF` / `PAPER_DATE_OLDEST·NEWEST` | 2612 / 1922-01-01 · 2026-01-01 |
| 임베딩 모델 | 스냅샷 빌드 + 질의 | gte-large-en-v1.5 (agent 고유) |
| 검색 예산 | `run_demo.py` 인자 / 코드 상수 | 풀 1500 · 서브아웃라인 50 · 서브섹션 100→60 · 인용 top-1 |
| topic 문자열 | `run_demo.py --topic` | `topics.kisti.jsonl` 의 `title` 그대로 |
| 백본·provider·temperature·max_tokens | `.env` | llama-3.3-70b @ akashml/fp8 · 0.6 · 8192 |

## 7. KISTI 스냅샷에서 달라지는 것 (검색 스택 관점)

| 항목 | bench-2512 | KISTI kisti-2512 | 검색에 미치는 영향 |
|---|---|---|---|
| id | arXiv base id 100% | arXiv 27.6% + **DOI 72.4%** | 게이트는 DOI 를 통과시킨다. 나머지 경로는 id 를 불투명 키로만 쓴다 |
| date | 일 단위 | `YYYY-01-01` | TRE 창이 연도 묶음이 된다 (§5) |
| citation_count | OpenAlex 2026-02 | KISTI `cited_by_count` | TRE 순위 분포가 다르다 — 의도된 통일 |
| abs | 그대로 | 10,000자 절단 111편 | 임베딩·프롬프트 입력 상한 |
| authors / venue | 없음 | 없음 (view 의 `authors.parquet` 로 후처리 가능) | 검색 무관, BibTeX 표기만 |
| 원문 | 불필요 | 불필요 | SurveyForge 는 초록만 쓴다 |
| 규모 | 947K, JSON 1.23GB | 1.65M, JSON 2.38GB | 기동 시 JSON 3회 파싱, 선택자 검색 ≈3배 (§4) |

## 8. 산출물 ↔ 단계

| 파일 (`exp_1/`) | 단계 |
|---|---|
| `cutoff_report.log` | 기동 `[cutoff/db]`, 게이트 `[cutoff/outline|writer]`, TRE 폐기 `[cutoff/rerank]` |
| `1-Total_1500_papers*.txt`, `1-Chunk_outlines.json`, `Survey_titles_*.txt`, `2-*`, `3-*`, `outlines_*` | §3.1 |
| `rag_outline_subset_ids.jsonl` (풀), `rag_docs_writer_{unique,rerank}.jsonl`, `section_references_ids.json`, `total_ids.txt`, `paper_texts.txt`(gitignore) | §3.2 |
| `raw_survey*.{txt,jsonl}`, `refined_survey*.{txt,jsonl}`, `<topic>.md`, `<topic>.json` | 집필·정리·인용 정합 |
| `time_cost.log` (`RAG API:` 행 = 검색 1회) , `run_manifest.json` | 실측·기록 |

비용 0 으로 검색 스택만 확인하려면 `scripts/probe_retrieval.py --topic "<title>"` (기동 + §3.1 풀 검색 + §3.2 TRE 한 번),
corpus 자체의 정합·질의 가능성은 `tests/test_kisti_corpus.py`.
