# SurveyForge — 재현 · DB 최신화 · 컷오프 통제

[SurveyForge (ACL 2025)](https://arxiv.org/abs/2503.04629)의 포크입니다.
GPU 서버에서 **서베이 생성 파이프라인을 end-to-end로 재현**했고(§2),
**2024-09에 멈춰 있던 논문 DB를 2026-08까지 최신화**했으며(58.9만 → 90.9만편, §3),
DB를 갱신해도 신규 논문을 조용히 가려 버리던 **하드코딩 컷오프 게이트를 통제 가능하게** 만들었습니다(§4).

원본 README(논문 소개)는 맨 아래 [원본 프로젝트](#원본-프로젝트)로 옮겼습니다.

| 문서 | 역할 |
|---|---|
| **`README.md`** (이 문서) | 프로젝트가 무엇이고, 무엇이 나왔고, 다음에 무엇을 하는지 |
| [`HANDOFF.md`](HANDOFF.md) | 지금 어디까지 됐고 다음에 뭘 하면 되는지 — **작업 시작 전 필독** |
| [`REPRODUCTION.md`](REPRODUCTION.md) | 산출물 재현에 필요한 입력값 일체 (환경·DB 지문·커밋·하이퍼파라미터) |
| [`RESULT.md`](RESULT.md) | 파일럿 결과의 배경 설명과 엔드포인트 비교 |
| [`.env.example`](.env.example) | 환경변수 템플릿 — `cp .env.example .env` 후 키만 채우면 됩니다 |
| [`tests/`](tests/) | `cd code && ../.venv/bin/python ../tests/test_cutoffs.py` — 10개. 네트워크·GPU 불필요 |

> 세 프로젝트(AutoSci·AutoSurvey·SurveyForge) 비교와 **시스템 간 통제 프로토콜**은
> 이 저장소 밖 `../SURVEY_REPORT.md`에 있습니다. git 추적 대상이 아닙니다.

---

## 1. 경로

**서버 작업 경로**: `/data2/chanjoong/survey-agent/SurveyForge` (브랜치 `main`)

같은 상위 디렉터리에 비교 대상 프로젝트가 함께 있습니다 — `AutoSurvey/`, `SurGE/`.
실행 자산(약 15GB)은 git을 깨끗하게 유지하려고 **저장소 밖** `../SurveyForge_data/`에 둡니다.

```
SurveyForge/
├── code/
│   ├── run_demo.py          실행 진입점 — 환경변수로 모델·스냅샷 선택
│   ├── main.py              검색 → 아웃라인 → 본문 → LCE
│   └── src/
│       ├── database.py         TinyDB + FAISS, gte-large-en-v1.5 임베딩
│       ├── rag.py              검색·리랭킹, 시간창 폐기 집계
│       ├── model.py            OpenRouter 호출, provider·reasoning 핀, 재시도
│       ├── utils.py            컷오프 헬퍼, arXiv id 파싱, 인덱스 글롭 탐색
│       ├── prompt.py           프롬프트 템플릿 (원본 그대로)
│       └── agents/
│           ├── outline_writer.py  아웃라인 생성·파싱
│           └── writer.py          서브섹션 병렬 작성 + LCE 정제
├── scripts/                 이 포크에서 추가한 도구 (§6)
├── tests/                   컷오프 회귀 테스트 10개
├── SurveyBench/             평가 자산 (벤치마크 참고문헌 10토픽, test.py)
├── demo_papers/             저자들이 생성한 서베이 PDF 29편 (대조용)
├── output_paper/            파일럿 최종 PDF 사본
├── .env.example             환경변수 템플릿 (커밋됨)
└── .env                     API 키 등 — git에 없음

../SurveyForge_data/         실행 자산, git에 없음
├── database/                논문 DB — 저자 배포본, 5.5GB
├── database_2026-08/        논문 DB — 최신화본, 9.0GB (§3)
├── Final_outline/           사람 서베이 아웃라인 17,072개 (2단계)
├── Final_outline_First/     〃 14,376개 (1단계)
└── gte-large-en-v1.5/       임베딩 모델
```

### 데이터베이스 — 스냅샷 2개

기존 `database/`는 **읽기만 합니다.** 최신화본은 옆에 새로 쓰므로 파일럿과의 A/B 대조가 유지됩니다.

| 스냅샷 | 논문 수 | 수록 범위 | 크기 |
|---|---|---|---|
| 배포본 `database/` | 589,123 | 2012-01-01 ~ 2024-09-25 | 5.5GB |
| **최신화본 `database_2026-08/`** | **908,819** | **1991-03-13 ~ 2026-08-04** (배포본 589,123편 **전부 포함**) | 9.0GB |

| 파일 | 내용 |
|---|---|
| `arxiv_paper_db_with_cc.json` | 논문 레코드 — `id`/`title`/`url`/`date`/`abs`/`cat`/`authors`/`citation_count` |
| `faiss_paper_title_abs_embeddings_*.bin` | `encode(title+abs)` — `IndexIDMap(IndexFlatIP)`, N × 1024, **L2 정규화** |
| `faiss_paper_title_embeddings_*.bin` | `encode(title)` (동일 규격) |
| `arxivid_to_index_abs.json` | arXiv id → FAISS stored id (**1-based**) |
| `surveys_*` / `faiss_survey_*` | 서베이 DB — **갱신 대상 아님**, 2024-09 그대로 |

서베이 DB는 레코드 18,816개인데 벡터가 12,756개뿐이라 6,060편은 검색되지 않습니다(배포본의 결함).
아웃라인 코퍼스 커버리지도 90.7% / 76.4%입니다.

---

## 2. 결과 요약

### 생성한 서베이

아래 표의 토픽은 전부 `Retrieval-Augmented Generation for Large Language Models`(SurveyBench
10토픽 중 하나)이고, 파라미터는 `--section_num 7 --subsection_len 500 --rag_num 100
--rag_max_out 60 --outline_reference_num 1500` 고정입니다.
회귀 검사용으로 `LLM-based Multi-Agent`와 `3D Gaussian Splatting`도 구·신 DB 양쪽으로
생성했습니다(총 8편) — §3.5에 함께 놓았습니다.

| 실행 | 모델 | DB | 섹션/서브 | 단어 | 참고문헌 | coverage | 소요 | 비용 |
|---|---|---|---|---|---|---|---|---|
| 파일럿 (2026-07-31) | `v4-pro` | 배포본 | 9 / 30 | 18,210 | 101 | 0.396 | 34분 11초 | **$1.998** |
| 구 DB (2026-08-05) | `v4-flash-0731` | 배포본 | 9 / 34 | 29,977 | 131 | 0.304 | 14분 26초 | **$0.381** |
| **신 DB (2026-08-06)** | `v4-flash-0731` | **최신화본** | 8 / 29 | 24,493 | 128 | 0.643 ⚠ | 26분 29초 | **$0.329** |

- 단어·구조는 `.tex` 기준입니다. `.md` 헤딩 카운트는 부풀려진 전례가 있습니다.
- `coverage`는 `SurveyBench/test.py`의 Reference Coverage. **matched / 내 인용 수**라
  precision 성격이라서 인용을 많이 할수록 불리합니다 — flash가 pro보다 낮은 것은
  참고문헌이 101 → 131로 늘어난 영향이 큽니다.
- **⚠ coverage 비율만 비교하면 안 됩니다.** `ref_bench` 기준일(이 토픽은 2024-07)보다 새
  논문은 분자·분모 양쪽에서 빠지는데, 신 DB 인용 128편 중 **100편이 그 이후**라 분모가
  125 → 28로 바뀌었습니다. 해석은 §3.5에 있습니다 — 인간 서베이와 나란히 놓아야 읽힙니다.

**PDF로 컴파일해 둔 것** (`.tex`·`.bib`도 같은 자리에 있습니다. 만드는 법은 §7):

| 서베이 | DB | 쪽수 | 참고문헌 |
|---|---|---:|---:|
| RAG (파일럿, `v4-pro`) | 배포본 | 43 | 101 |
| RAG | 배포본 | 60 | 131 |
| RAG | 최신화본 | 51 | 128 |
| LLM-based Multi-Agent | 최신화본 | 57 | 151 |
| 3D Gaussian Splatting | 최신화본 | 54 | 147 |

### 원본 대비 코드 변경

| 파일 | 내용 | 왜 |
|---|---|---|
| `code/run_demo.py` | venv 인터프리터, `.env` 로딩, `--api_key` 미전달, 모델·스냅샷별 출력 경로 | 비밀 노출 차단 / 실행 간 충돌 방지 |
| `code/main.py` | API 키 마스킹, 컷오프 인자 3개 + 검증, 기동 정합성 점검 | §4 |
| `code/src/model.py` | provider·quantization·reasoning 핀, `MAX_TOKENS` 환경변수화, `[PROVIDER]`/`[TRUNCATED]`/`[EMPTY]` 로깅, 재시도 백오프 + 포기한 요청의 `None` 차단 | 통제 실험 조건 확보 / 429로 실행이 죽지 않게 |
| `code/src/utils.py` · `rag.py` · 두 agent | 컷오프 파라미터화, 폐기 건수 집계, arXiv id 날짜 파싱, 인덱스 글롭 탐색 | §4 |
| `code/src/agents/outline_writer.py` | `filter_by_outline()` 추가, `--debug` `UnboundLocalError` 수정, 번호 없는 `Description:` 허용 | 아래 |
| `code/requirements-fixed.txt` | 설치 가능한 의존성 (신규) | 원본이 해석 불가 |
| `code/tools/md_to_tex.py` | Markdown → LaTeX 변환기 (신규). 실행 경로에서 스냅샷 되짚기, 인용 연도를 arXiv id에서 |  `.md` 참고문헌에 링크가 없음 / `date`는 개정 연도라 인용 연도로 틀림 |

발견한 업스트림 버그는 [`REPRODUCTION.md`](REPRODUCTION.md) §6에 6건 정리돼 있습니다.
그중 셋은 **예외를 내지 않고 조용히 틀리는** 종류입니다 — 시간창 밖 문서 폐기,
`get_time_windows` 경계 off-by-one, 아웃라인 코퍼스 미커버.

### 범위 밖

- **SurveyBench 정량 평가 전체 미실시** — 10토픽 중 3토픽만 씁니다. Outline·Content 품질(SAM-O/SAM-C)은 LLM judge라 별도 비용이 듭니다.
- **서베이 DB·아웃라인 코퍼스는 여전히 2024-09** — 최신 논문을 인용하지만 최신 서베이의 구조는 학습하지 않습니다.
- **1편만 실행** — `temperature=1`에 시드가 없어 분산을 알려면 반복이 필요합니다.
- **인용 정합성 미검증** — 인용 번호는 LLM이 쓴 제목을 임베딩 최근접(top_k=1)으로 스냅한 것이라 임계값도 검증도 없습니다.

---

## 3. 개선 방향 — DB 최신화

### 3.1 문제

배포 DB는 2024-09-25에서 끝납니다. 최신 논문을 인용할 수 없고, 논문이 내세우는
**TRE**(2년 단위 시간창으로 최신·정착 문헌을 안배하는 리랭커)도 최신 창이 2년째 비어 있어
사실상 죽어 있습니다.

### 3.2 표기 규약은 실측으로 확정했다

증분의 전제는 신규 논문이 기존과 **구별되지 않는** 형태로 들어가는 것입니다.
그런데 **이 DB는 이미 두 층**이었습니다 — 제목의 문자 치환 여부로 정확히 갈리고 교집합이 0입니다.

| 층 | 편수 | 날짜 범위 |
|---|---|---|
| `:` → 공백 치환됨 | 149,036 | 2012-01-01 ~ **2024-04-26** |
| `:` 보존 (raw) | 21,791 | 2024-04-23 ~ 2024-09-25 |

경계 2024-04-26은 AutoSurvey 배포 DB의 컷오프와 같습니다. 즉 이 코퍼스는 AutoSurvey 계열
베이스 위에 저자들이 직접 증분한 것이고 **그 증분에서는 치환을 걸지 않았습니다.**
따라서 신규 논문은 최신 층, 곧 raw 표기를 따릅니다.

`scripts/check_oai_schema.py`로 최신 층 25편을 OAI에서 재취득해 문자 단위 대조한 결과
**7필드 0불일치**입니다. 확정된 규약과, AutoSurvey 스크립트를 그대로 옮기면 깨지는 지점:

| 필드 | 규약 | AutoSurvey와 다른 점 |
|---|---|---|
| `id` | base + 최신 버전 접미사 | — |
| `date` | **id에 적힌 버전의 날짜** | 그쪽은 v1을 쓴다 → 개정본이 최대 1년 어긋남 |
| `title` | arXiv 형식, **치환 없음** | 그쪽은 `<>:"/\|?*#`를 공백 치환 |
| `abs` | arXivRaw (TeX escape 보존) | 동일 |

임베딩 규약도 저장 벡터를 복원해 맞춰 봤습니다 — `encode(title+abs)` **구분자 없는 연결**,
L2 정규화, prefix 없음(cos 1.000000). 구분자를 하나만 끼워도 0.990으로 떨어집니다.

### 3.3 실행 결과 — 2026-08-05 완료

```
수집 370,292건  →  기존 DB 중복 50,511건 제외  →  제목+저자 재게시 85건 제외
             →  신규 319,696편  →  총 908,819편
```

| 단계 | 스크립트 | 소요 | 결과 |
|---|---|---|---|
| 1. 수집 | `harvest_arxiv.py` | 1시간 13분 | 두 패스 각 370,292건, **조인 손실 0** |
| 2. 피인용수 | `fetch_citations.py` | 15분 | 319,781편 **전수 조회 성공**, 59.2%가 >0 |
| 3. 임베딩+append | `append_snapshot.py` | 1시간 40분 | 67편/s (유휴 L40S 1장) |
| 4. 검증 | `check_db.py` | 3분 | **재임베딩 최저 cos 1.000000** |

검증은 건수 일치·id 체계(1..908819 전단사)에 더해 **저장 벡터를 꺼내 다시 임베딩해 대조**합니다.
기존 구간과 신규 구간을 반씩 뽑는 이유는, 기존만 보면 append 코드가 틀려도 통과하고
신규만 보면 규약을 잘못 읽었을 때 나란히 틀려서 통과하기 때문입니다.

### 3.4 검색까지 도달했는가

DB에 넣은 것과 실제로 검색되는 것은 다른 문제입니다. 같은 토픽의 아웃라인 검색 풀 1,500편:

| | 구 DB | 신 DB |
|---|---|---|
| 날짜 범위 | 2015-02 ~ 2024-09-25 | 2018-08 ~ **2026-08-03** |
| 2024-09-25 이후 | **0편 (0%)** | **980편 (65.5%)** |

### 3.5 회귀 검사 — 희석은 일어나지 않았다

같은 모델(flash)로 **DB만** 바꿔 세 토픽을 생성하고, 인간 서베이를 기준선으로 함께 놓았습니다.
토픽은 신규 논문 비중이 서로 다른 것으로 골랐습니다(Multi-Agent 81.5% / 3DGS 75.7% / RAG 65.3%).

| 토픽 | | 총 인용 | 판정 가능 | matched | **판정가능분 정확도** | 최신 인용 |
|---|---|---:|---:|---:|---:|---:|
| **RAG** | 인간 | 190 | 190 | 103 | 54.2% | 0% |
| | 구 DB | 131 | 125 | 38 | 30.4% | 0.0% |
| | 신 DB | 128 | 28 | 18 | **64.3%** | 78.1% |
| **Multi-Agent** | 인간 | 172 | 172 | 131 | 76.2% | 0% |
| | 구 DB | 116 | 105 | 31 | 29.5% | 0.0% |
| | 신 DB | 151 | 18 | 11 | **61.1%** | 89.4% |
| **3DGS** | 인간 | 271 | 266 | 166 | 62.4% | 0% |
| | 구 DB | 119 | 117 | 71 | 60.7% | 0.0% |
| | 신 DB | 147 | 32 | 30 | **93.8%** | 78.9% |

matched가 세 토픽 모두 줄어든 것(38→18, 31→11, 71→30)만 보면 정전 문헌을 놓친 것처럼
보입니다. 그러나 **판정 가능한 인용 안에서의 정확도는 세 토픽 모두 올랐고, 상승폭이
거의 같습니다:**

| | 구 DB | 신 DB | 증가 |
|---|---:|---:|---:|
| RAG | 30.4% | 64.3% | **+33.9p** |
| Multi-Agent | 29.5% | 61.1% | **+31.6p** |
| 3DGS | 60.7% | 93.8% | **+33.1p** |

**출발점이 30%든 61%든 +33포인트 근처로 같이 올라갑니다** (편차 2.3p). 3DGS는 구 DB가
이미 60.7%로 잘하고 있었는데도 같은 폭으로 올랐으니, "못하던 게 고쳐진 것"이 아니라
**배분이 바뀐 것**입니다 — 인용 슬롯의 약 80%를 최신 논문에 쓰고, 남은 20%를 훨씬 잘 고릅니다.

정직하게 덧붙일 것 셋:

- **인간을 넘은 것은 3개 중 2개입니다** (RAG 64.3 vs 54.2, 3DGS 93.8 vs 62.4). Multi-Agent는
  61.1 vs 76.2로 못 넘었습니다. 주장할 수 있는 것은 "DB 최신화가 옛 논문 선택 정확도를
  올린다"이지 "인간을 넘는다"가 아닙니다.
- **분모가 작습니다** (28 / 18 / 32편). 비율의 표본이 작으니 소수점을 믿지 마세요.
- **세 토픽 모두 신규 논문 비중이 높은 편**(65~82%)입니다. GNN(17.3%)이나
  3D Detection(26.7%) 같은 토픽에서도 같은 폭이 나올지는 **확인하지 않았습니다.**

**벤치마크는 이 배분을 볼 수 없습니다.** 참고문헌이 2024-06/07 이전 인간 서베이에서
나왔기 때문입니다. 2026년에 쓰는 서베이가 최신 논문을 많이 인용하는 것이 옳다면, 이
지표로는 그 판단을 할 수 없습니다 — 지표의 한계이지 산출물의 결함이 아닙니다.

세 토픽의 원본 표는 [`eval_out/eval_*.md`](eval_out/)에 있고,
[`scripts/compare_runs.py`](scripts/compare_runs.py)가 생성합니다.

### 3.6 알려진 제약

- **2012년 이전 약 4,200편은 인용 불가.** OAI `from`이 수정일 기준이라 옛 논문이 딸려 들어왔는데
  (구형 id 992편 + 2007~2011년 신형 3,218편), 리랭커 시간창이 2012-01-01에서 시작합니다.
  기동 시 경고로 알려 줍니다. 창을 1991년까지 늘리면 7개 → 18개가 되어 파일럿과의 비교가 깨집니다.
- **비용은 거의 안 늘지만 검색 시간은 늡니다** — 프롬프트에 들어가는 논문 수는 `rag_max_out`이
  정하지 코퍼스 크기가 정하지 않습니다. `IDSelectorArray` 선형 스캔이 97초 → 244초가 됩니다.

---

## 4. 개선 방향 — 컷오프 게이트 통제

### 4.1 문제 — 게이트가 넷인데 성격이 다르다

DB만 갱신해서는 작동하지 않습니다. 코드에 컷오프가 박혀 있었고, 배포 DB에서는 셋 다
아무것도 거르지 않아 **보이지 않던** 것들입니다.

| # | 위치 | 성격 |
|---|---|---|
| A | `outline_writer.py` 아웃라인 검색 | `arxivid.split('.')[0] <= '2412'` |
| B | `writer.py` 본문 검색 (서브섹션 전체를 게이팅) | 동일 필터 → 인용 불가 |
| C | `utils.py` `sort_by_citation_period` 시간창 | `time_newest = '2024-09-26'` — **예외도 로그도 없이 폐기** |
| D | `outline_writer.py` sub-outline 검색 | **필터 없음 — DB 전체를 본다** |

D 때문에 비대칭이 생깁니다. 컷오프를 안 올린 채 DB만 갱신하면 sub-outline은 최신 논문을 보고
2025~2026 서브섹션을 제안하는데 writer는 A·B에 막혀 그 논문을 꺼내오지 못합니다.

### 4.2 대응

`--paper_id_cutoff` / `--paper_date_oldest` / `--paper_date_newest` 세 인자로 노출했습니다.
**기본값은 하드코딩돼 있던 값 그대로**라 인자를 주지 않으면 파일럿이 그대로 재현됩니다.

하나로 합치지 않은 이유: `'2412'`(12월)와 `'2024-09-26'`(9월)은 같은 시점이 아니라 단일 값으로
둘 다 만들 수 없고, arXiv id의 YYMM은 *공개* 월이지만 `date`는 *제출일*이라 월 경계마다 어긋납니다.

침묵을 없애는 쪽에 더 공을 들였습니다:

- 게이트가 제외한 편수와 시간창이 폐기한 문서 수를 집계해 실행 끝에 총계를 남깁니다.
- 기동 시 설정값과 DB의 실제 범위를 비교해 **경고**합니다(중단하지는 않습니다 — 과거 시점 재현도 정당한 실험입니다).
- 출력은 콘솔과 `<실행 디렉터리>/cutoff_report.log` 양쪽. `run_demo.py`가 자식 stdout을 저장하지 않기 때문입니다.

### 4.3 검증

오늘의 DB에서는 변경이 전부 no-op이라 "돌려보니 잘 나왔다"는 아무것도 증명하지 못합니다.
4계층으로 나눴습니다.

| 계층 | 방법 | 결과 |
|---|---|---|
| 1. 차분 | 교체 이전 구현을 테스트 파일에 고정해 비교 | 기본값에서 **원소 단위 동일** |
| 2. no-op 종단 | 플래그 없이 실행 | `1-Total_1500_papers.txt`가 파일럿과 **md5 동일** |
| 3. 게이트 동작 | 컷오프를 과거로 이동 | 534,059/589,123 제외, 경고가 실제 범위를 지목 |
| 4. 입력 검증 | 잘못된 값 3종 | DB 로드 전 즉시 종료 |

`tests/test_cutoffs.py` 10개가 이를 고정합니다. 커밋 이후에도 의미가 있도록 **교체 이전 구현을
파일 안에 그대로 박아** 뒀습니다 — `git show HEAD`로 비교하면 커밋한 순간 무의미해집니다.

증분 이후 잡힌 것 하나: **구형 arXiv id 992편이 조용히 제외**되고 있었습니다.
`'cs/0503039v25'.split('.')[0]`은 id 전체라 `'c' > '2'`로 모든 컷오프에서 탈락했고,
구형은 연도가 91~07이라 사전식으로는 1992년이 2026년보다 큽니다. `arxiv_month()`로 두 형식을
(연, 월)로 파싱해 고쳤습니다.

---

## 5. 비용

모두 OpenRouter 실청구 기준입니다.

| 실행 | 토픽 | 모델 | provider | reasoning | 입력 / 출력 토큰 | **비용** |
|---|---|---|---|---|---|---:|
| 파일럿 | RAG | `deepseek-v4-pro` | `streamlake/fp8` | 기본값 (ON) | 2,241,756 / 127,848 | **$1.998** |
| 구 DB | RAG | `deepseek-v4-flash-0731` | `parasail/fp8` | **OFF** | 2,406,633 / 158,181 | **$0.381** |
| 신 DB | RAG | 〃 | 〃 | **OFF** | 2,064,277 / 143,354 | **$0.329** |
| 구 DB | Multi-Agent | 〃 | 〃 | **OFF** | 1,891,900 / 124,392 | $0.300 |
| 신 DB | Multi-Agent | 〃 | 〃 | **OFF** | 2,149,845 / 154,967 | $0.344 |
| 구 DB | 3DGS | 〃 | 〃 | **OFF** | 2,356,021 / 147,279 | $0.371 |
| 신 DB | 3DGS | 〃 | 〃 | **OFF** | 2,259,869 / 151,458 | $0.359 |

단가: `v4-pro` fp8 $0.67/$1.34 per M, `v4-flash-0731` fp8 $0.140/$0.280 per M.
아래 세 줄은 정가 환산입니다(reasoning이 꺼져 있어 실청구와 거의 같습니다).
**flash는 토픽·DB에 관계없이 편당 $0.30~0.38**로, 회귀 검사 3토픽 6편이 약 $2 — 파일럿 1편 값입니다.

실패한 실행에도 돈은 듭니다. 3DGS는 두 번 엎어졌는데(아웃라인 파서 `IndexError`,
OpenRouter 429), 둘 다 아웃라인 입력 토큰까지는 이미 지불한 뒤였습니다 — 편당 $0.07 정도씩입니다.

**비용의 90%가 입력 토큰입니다.** 서브섹션마다 검색한 초록을 프롬프트에 넣기 때문이며,
줄이려면 `rag_max_out` / `outline_reference_num`을 낮춰야 합니다. 출력을 줄여 봐야 거의 안 줍니다.

**reasoning을 끄는 것이 5배 차이의 일부입니다.** 파일럿은 토큰 카운터에 잡히지 않는 reasoning
토큰이 총액의 16%($0.325)였습니다 — 정가 환산 $1.673 대 실청구 $1.998. `deepseek` 계열은
기본이 ON이라 `SURVEYFORGE_REASONING_EFFORT=none`으로 명시해야 하고, 껐는지는 응답의
`reasoning_tokens`로 확인합니다. 나머지는 단가 차이(1/4.8)입니다.

모델을 바꾸면 분량도 바뀌므로 토큰 수를 그대로 옮기면 안 됩니다 — flash는 같은
`subsection_len 500`에서 29,977단어(34서브섹션), pro는 18,210단어(30서브섹션)였습니다.

DB 구축 자체는 무료입니다 (arXiv OAI-PMH와 Semantic Scholar 모두 키만 있으면 무과금, GPU 약 2시간).

---

## 6. 스크립트

`scripts/update_snapshot.sh`가 1~4를 순서대로 돌리고 어느 단계든 실패하면 멈춥니다.
가장 한가한 GPU를 골라 씁니다 — 남의 학습에 얹으면 임베딩이 68 → 32편/s로 반토막 납니다.

| 스크립트 | 역할 |
|---|---|
| `check_oai_schema.py` | DB에 있는 논문을 OAI로 재취득해 표기 규약을 문자 단위 대조 (**증분 전 필수**) |
| `harvest_arxiv.py` | OAI-PMH 수집. 재개 가능, 503 백오프, dual-prefix 조인 |
| `fetch_citations.py` | Semantic Scholar 배치로 `citation_count`. 재개 가능 |
| `append_snapshot.py` | 임베딩 + FAISS append + 새 스냅샷. 정합성 실패 시 아무것도 쓰지 않음 |
| `check_db.py` | 건수·id 체계·**재임베딩 대조**·md5 지문 |
| `to_surveybench_ref.py` | 생성 결과를 SurveyBench `ref.json` 형식으로 변환 |
| `compare_runs.py` | 두 실행을 coverage·최신성·분량·무결성 네 축으로 비교 |

---

## 7. 빠른 시작

```bash
git clone git@github.com:brian-223134/SurveyForge.git && cd SurveyForge
python3 -m venv .venv && .venv/bin/pip install -r code/requirements-fixed.txt
cp .env.example .env          # OPENROUTER_API_KEY, SURVEYFORGE_DATA 채우기

# 데이터 자산 (약 15GB)
export DATA=/path/to/SurveyForge_data
hf download InternScience/SurveyForge_database --repo-type dataset --local-dir "$DATA"
hf download Alibaba-NLP/gte-large-en-v1.5 --local-dir "$DATA/gte-large-en-v1.5"
cd "$DATA" && unzip -q Final_outline.zip && unzip -q Final_outline_First.zip

cd code && ../.venv/bin/python run_demo.py "Retrieval-Augmented Generation for Large Language Models"
```

> README 원문은 데이터셋 org를 `U4R/`로 적고 있으나 실제로는 **`InternScience/`**입니다.
> 또 설명이 없는 `Final_outline.zip` / `Final_outline_First.zip` 두 개가 **필수**입니다.

### 반드시 의식하고 골라야 하는 두 가지

**provider를 핀하지 않으면 통제 실험이 아닙니다.** OpenRouter는 요청마다 독립 라우팅하는데
같은 모델의 엔드포인트들이 서로 다른 quantization(fp4/fp8)으로 서빙합니다.
핀하지 않으면 서베이 한 편의 서브섹션들이 섞인 정밀도로 작성됩니다.

**DB를 갱신했다면 컷오프도 함께 올려야 합니다.** 안 올리면 §4의 게이트가 새로 넣은 논문을
전부 가립니다. `check_db.py`가 넣어야 할 값을 출력합니다.

```bash
SURVEYFORGE_DB_DIR=database_2026-08 \
SURVEYFORGE_PAPER_ID_CUTOFF=2608 \
SURVEYFORGE_PAPER_DATE_NEWEST=2026-08-31 \
  ../.venv/bin/python run_demo.py "<topic>"
```

`PAPER_DATE_NEWEST`를 **짝수 해 1월 1일로 두지 마세요** — 시간창이 2012-01-01부터 2년 단위라
경계에 정확히 걸리는 날짜가 생깁니다.

### 결과물을 PDF로

파이프라인이 내놓는 `.md`의 참고문헌은 **제목만** 있습니다. arXiv id는 옆의 `.json`에,
저자·URL·날짜는 논문 DB에만 있어서, 셋을 조인해야 쓸 만한 문헌 목록이 나옵니다.

```bash
.venv/bin/python code/tools/md_to_tex.py "<run_dir>" --compile
```

`<run_dir>`은 `.md`와 `.json`이 있는 `.../<topic>/exp_1` 입니다. `.tex`·`.bib`·`.pdf`가
같은 자리에 나옵니다. `--compile`을 빼면 변환만 하고, Overleaf에 올릴 거라면 그걸로 충분합니다.

- **스냅샷은 실행 경로에서 되짚습니다.** 최신화본으로 만든 서베이에 배포본 DB를 물리면
  최신 논문의 제목·저자가 통째로 빠지므로, 경로의 `__database_2026-08` 접미사를 읽습니다.
- **인용 연도는 `date`가 아니라 arXiv id에서 읽습니다.** DB의 `date`는 *id가 가리키는
  버전*의 날짜라(§3.2) 개정본이면 개정 연도가 들어갑니다 — 3DGS 참고문헌의 36%가
  이렇게 틀려 있었습니다. id의 YYMM은 v1 공개월이라 바뀌지 않습니다.
- 인용 번호는 `.md`의 것을 그대로 씁니다. `thebibliography`를 인라인으로 넣는 이유가
  이것으로, BibTeX 스타일을 쓰면 재정렬되면서 원본 실행과의 대조가 깨집니다.
- 매핑 안 된 유니코드가 남으면 경고합니다. 그대로 두면 pdflatex이 멈추니
  `UNICODE_MAP`에 추가하거나 xelatex으로 컴파일하세요.

---

## 원본 프로젝트

<div align="center">
<h3>(ACL-2025) SurveyForge: On the Outline Heuristics, Memory-Driven Generation, and Multi-dimensional Evaluation for Automated Survey Writing</h3>

[[ Paper 📓 ]](https://arxiv.org/abs/2503.04629) [[ SurveyBench Benchmark 🤗 ]](https://huggingface.co/datasets/U4R/SurveyBench) [[SurveyForge Database 🤗]](https://huggingface.co/datasets/U4R/SurveyForge_database/tree/main)
</div>

<p align="center">
  <img src="./assets/framework_surveyforge.png" width="99%">
</p>

Survey papers are vital in scientific research, especially with the rapid increase in research publications. Recently, researchers have started using LLMs to automate survey creation for improved efficiency. However, LLM-generated surveys often fall short compared to human-written ones, particularly in outline quality and citation accuracy. To address this, we introduce **SurveyForge**, which first creates an outline by analyzing the structure of human-written outlines and consulting domain-related articles. Then, using high-quality papers retrieved by our scholar navigation agent, **SurveyForge** can automatically generate and refine the content of the survey.

Moreover, to achieve a comprehensive evaluation, we construct **SurveyBench**, which includes 100 human-written survey papers for win-rate comparison and assesses AI-generated survey papers across three dimensions: reference, outline, and content quality.

### SurveyBench

```
cd SurveyBench && python test.py --is_human_eval
```

`is_human_eval` True for human survey evaluation, False for generated surveys. Expected layout:

```
generated_surveys
|-- 3D Gaussian Splatting
    |-- exp_1
        |-- ref.json
...
```

지원 토픽 10개와 저자 생성 서베이 PDF 예시는 [`demo_papers/`](demo_papers/)에 있습니다.

### Acknowledgements

We sincerely thank the [AutoSurvey](https://github.com/AutoSurveys/AutoSurvey) for laying the foundation in automated survey generation and analysis. SurveyForge is developed on top of the AutoSurvey framework.

### Citations

```
@article{yan2025surveyforge,
  title={Surveyforge: On the outline heuristics, memory-driven generation, and multi-dimensional evaluation for automated survey writing},
  author={Yan, Xiangchao and Feng, Shiyang and Yuan, Jiakang and Xia, Renqiu and Wang, Bin and Zhang, Bo and Bai, Lei},
  journal={arXiv preprint arXiv:2503.04629},
  year={2025}
}
```
