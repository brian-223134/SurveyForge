# HANDOFF — SurveyForge 세팅 인수인계

**최종 갱신**: 2026-08-06 03:35 (3차 — 회귀 검사 3토픽 완료, 결론 확정)
**목표**: 논문(초록 DB)을 토대로 **서베이가 실제로 생성되는 것까지** + **DB를 최신 상태로 유지**.
논문 수치 재현은 범위 밖입니다.
**상세 배경**: [`README.md`](README.md) (전체 개관) / [`REPRODUCTION.md`](REPRODUCTION.md) (재현 입력값 일체) / [`RESULT.md`](RESULT.md) (파일럿 결과 배경).
이 문서는 **"지금 어디까지 됐고 다음에 뭘 하면 되는지"**만 다룹니다.

---

## 이 문서를 읽었다면 먼저 이것부터

백그라운드 작업이 돌고 있을 수 있습니다. 컨텍스트가 끊긴 뒤에는 **무엇이 돌고 있는지부터**
확인하세요 — 로그는 `eval_out/`에 있고 git 추적 대상이 아닙니다.

```bash
cd /data2/chanjoong/survey-agent/SurveyForge
ps -ef | grep -E "[m]ain.py --topic|[r]un_demo|eval_out/.*[.]sh" | awk '{print $2, $9, $10, $11}'
tail -3 eval_out/*.log 2>/dev/null
ls eval_out/eval_*.md 2>/dev/null          # 완료된 회귀 검사
git log --oneline -5 ; git status --short
```

**2026-08-06 03:35 기준 — 돌고 있는 것 없습니다.** 회귀 검사 3토픽이 전부 끝났습니다(§A).
다음에 무언가를 백그라운드로 띄우면 이 표를 갱신하세요.

| 작업 | 스크립트 | 로그 | 산출 |
|---|---|---|---|
| *(없음)* | | | |

서베이 생성은 **사용자가 지시할 때만** 합니다(편당 실비 $0.3~2). 검증·집계처럼 돈이 안 드는
구간은 알아서 진행해도 됩니다.

---

## 현재 상태

**파이프라인 end-to-end 동작 확인 + 논문 DB 2026-08까지 최신화 완료.**

| 항목 | 상태 |
|---|---|
| 서베이 생성 | ✅ **7편** — 파일럿 1 + flash 3토픽 × 2 DB |
| 논문 DB 최신화 | ✅ 589,123 → **908,819편**, 2024-09-25 → **2026-08-04** |
| 컷오프 게이트 통제 | ✅ 하드코딩 3곳 파라미터화, 회귀 테스트 10개 |
| SurveyBench 회귀 검사 | ✅ **3토픽 재현** — 판정가능분 정확도 **+33p 일정** (§A) |
| 서베이 DB·아웃라인 코퍼스 | ❌ 여전히 2024-09 — **손대지 않았음** |
| SurveyBench 정량 평가 (SAM-O/SAM-C) | ❌ 미실시 (LLM judge, 별도 비용) |

### 생성한 서베이

파라미터는 전부 `--section_num 7 --subsection_len 500 --rag_num 100 --rag_max_out 60
--outline_reference_num 1500` 고정. 모델은 파일럿만 `v4-pro`, 나머지는 `v4-flash-0731`.

| 토픽 | DB | 섹션/서브 | 단어 | 참고문헌 | 소요 |
|---|---|---|---|---|---|
| RAG (파일럿, `v4-pro`) | 배포본 | 9 / 30 | 18,210 | 101 | 34분 11초 |
| RAG | 배포본 | 9 / 34 | 29,977 | 131 | 14분 26초 |
| RAG | 최신화본 | 8 / 29 | 24,493 | 128 | 26분 29초 |
| Multi-Agent | 배포본 | 8 / 25 | 20,233 | 116 | 23분 50초 |
| Multi-Agent | 최신화본 | 8 / 30 | 24,671 | 151 | 21분 44초 |
| 3D Gaussian Splatting | 배포본 | 8 / 30 | 24,896 | 119 | 28분 50초 |
| 3D Gaussian Splatting | 최신화본 | 8 / 30 | 24,306 | 147 | 28분 50초 |

산출물 경로는 모델·스냅샷별로 갈립니다 —
`code/output/res/deepseek_deepseek-v4-flash-0731{,__database_2026-08}/<topic>/exp_1/`.

> **coverage를 그냥 읽으면 안 됩니다.** `SAM_R`은 `matched / 내 인용 수`라 **precision 성격**이고,
> 인용을 많이 할수록 불리합니다. flash가 pro보다 낮은 건 참고문헌이 101 → 131로 늘어난 영향이 큽니다.
> 게다가 `ref_bench` 기준일이 토픽마다 2023-10 ~ 2024-07이라 **증분분은 10토픽 전부에서 비가시**입니다
> (분자·분모 양쪽에서 빠짐). coverage는 "정전 문헌을 여전히 찾는가"(희석 여부)만 답합니다.

---

## DB 최신화 — 2026-08-05 완료

```
수집 370,292건 → 기존 중복 50,511 제외 → 제목+저자 재게시 85 제외 → 신규 319,696편
```

| 스냅샷 | 경로 | 논문 수 | 수록 범위 | 크기 |
|---|---|---|---|---|
| 배포본 | `../SurveyForge_data/database/` | 589,123 | 2012-01-01 ~ 2024-09-25 | 5.5GB |
| **최신화본** | `../SurveyForge_data/database_2026-08/` | **908,819** | **1991-03-13 ~ 2026-08-04** | 9.0GB |

**배포본은 읽기만 했습니다.** 최신화본을 옆에 새로 썼으므로 파일럿과의 A/B 대조가 유지됩니다.

지문 (`REPRODUCTION.md` §7.4에도 있음):

| 파일 | 크기 | md5 |
|---|---|---|
| `arxiv_paper_db_with_cc.json` | 1,400,883,616 | `700142dddbd8a70f26a9b02ca5b366ec` |
| `arxivid_to_index_abs.json` | 21,658,441 | `4c8a884626cd5ae72aa4890f5a4a74d5` |
| `faiss_paper_title_abs_embeddings_FROM_2012_0101_TO_260804.bin` | 3,729,793,266 | `189d6b42b587c5e6c3b3aecfe2b19445` |
| `faiss_paper_title_embeddings_FROM_2012_0101_TO_260804.bin` | 3,729,793,266 | `99105a8b24475ea6cd1e814f59f14b64` |

**검증 통과** — 건수 4파일 일치, id 체계 1..908819 전단사, **재임베딩 최저 cos 1.000000**
(기존 20편 + 신규 20편). `citation_count`는 319,781편 전수 조회 성공, 59.2%가 >0.

**검색까지 도달 확인** — 같은 토픽 아웃라인 검색 풀 1,500편 중 2024-09-25 이후가
구 DB **0편(0%)** → 신 DB **980편(65.5%)**.

---

## 컷오프 게이트 — 2026-08-05 통제 가능해짐

**DB만 갱신해서는 작동하지 않습니다.** 코드에 컷오프가 박혀 있었고, 배포 DB에서는
아무것도 거르지 않아 보이지 않던 것들입니다.

| # | 위치 | 통제 수단 |
|---|---|---|
| A | `outline_writer.py` 아웃라인 검색 | `--paper_id_cutoff` |
| B | `writer.py` 본문 검색 (서브섹션 전체 게이팅) | `--paper_id_cutoff` |
| C | `utils.py` 시간창 — **예외도 로그도 없이 폐기** | `--paper_date_{oldest,newest}` |
| D | `outline_writer.py` sub-outline 검색 | **없음 — DB 전체를 본다** |

**기본값은 하드코딩돼 있던 값 그대로**라 인자를 안 주면 파일럿이 그대로 재현됩니다.
게이트가 제외한 편수와 시간창이 폐기한 문서 수를 집계해 `<실행 디렉터리>/cutoff_report.log`에 남깁니다.

D 때문에 비대칭이 생깁니다 — 컷오프를 안 올린 채 DB만 갱신하면 sub-outline은 최신 논문을 보고
2025~2026 서브섹션을 제안하는데 writer는 A·B에 막혀 그 논문을 못 꺼냅니다.

---

## git 상태

`main` 브랜치. **push와 PR 생성은 사용자가 직접 합니다.**
origin은 SSH URL(`git@github.com:brian-223134/SurveyForge.git`)입니다.
현재 `origin/main`과 동기화돼 있습니다.

`.gitignore` 대상: `.env`, `../SurveyForge_data/`(저장소 밖), `SurveyBench/eval_runs/`, `eval_out/`.

---

## 재실행 방법

DB와 `.env`는 준비돼 있습니다. **최신화본 + flash** 기준 한 줄입니다.

```bash
cd code
SURVEYFORGE_DB_DIR=database_2026-08 \
SURVEYFORGE_PAPER_ID_CUTOFF=2608 \
SURVEYFORGE_PAPER_DATE_NEWEST=2026-08-31 \
CUDA_VISIBLE_DEVICES=<빈 GPU> \
  ../.venv/bin/python run_demo.py "<topic>"
```

배포본으로 돌리려면 위 환경변수 3개를 빼면 됩니다(기본값이 배포본 + 원래 컷오프).

> `.env`가 없다면: `cp .env.example .env && chmod 600 .env` 후 `OPENROUTER_API_KEY`와
> `SEMANTIC_SCHOLAR_API_KEY`만 채우세요. 나머지는 실제로 쓰는 값 그대로입니다.

### 현재 `.env` 설정

| 변수 | 값 | 비고 |
|---|---|---|
| `SURVEYFORGE_MODEL` | `deepseek/deepseek-v4-flash-0731` | 날짜 고정 태그 — 제공자가 갱신하지 않음 |
| `SURVEYFORGE_PROVIDER` | `parasail/fp8` | **반드시 핀** (아래) |
| `SURVEYFORGE_REASONING_EFFORT` | `none` | deepseek 계열은 기본 ON |
| `SURVEYFORGE_MAX_TOKENS` | `65536` | 길이 통제가 아니라 잘림 방지 |
| `SURVEYFORGE_MAX_THREADS` | `8` | 동시 요청 = 2 × 8 = 16 |
| `SURVEYFORGE_MAX_SECTION_THREADS` | `2` | 〃 |

**provider를 핀하지 않으면 통제 실험이 아닙니다.** OpenRouter는 요청마다 독립 라우팅하는데
`v4-flash-0731`은 엔드포인트 20개가 fp4/fp8/unknown으로 섞여 있습니다.
핀하면 `allow_fallbacks=false`도 함께 켜집니다.

**reasoning이 꺼졌는지 확인하세요** — 응답의 `reasoning_tokens`가 0이어야 합니다.
파일럿(pro, 기본값 ON)은 토큰 카운터에 안 잡히는 reasoning에 총액의 16%($0.325)를 냈습니다.

### 크레딧 — 한도 $30

```bash
.venv/bin/python -c "
import os,requests; from dotenv import load_dotenv; load_dotenv('.env')
d=requests.get('https://openrouter.ai/api/v1/key',
  headers={'Authorization':'Bearer '+os.environ['OPENROUTER_API_KEY']},timeout=30).json()['data']
print(f\"사용 \${d['usage']:.3f} / 한도 \${d['limit']}  잔여 \${d['limit']-d['usage']:.2f}\")"
```

2026-08-06 03:35 기준 **사용 $12.95 / 잔여 $17.05** — flash 기준 약 46편분입니다.
`/api/v1/credits`가 아니라 **`/api/v1/key`**를 쓰세요. 전자는 계정 전체 잔액이라
이 키에 걸린 한도가 안 보입니다.

---

## 확정된 결정사항

- **백본은 `deepseek/deepseek-v4-flash-0731`, provider `parasail/fp8`, reasoning OFF.**
  pro 대비 1/5.2 비용($0.381 vs $1.998).
- **서베이 생성은 사용자가 지시할 때만.** 검증 목적이라도 임의로 돌리지 않습니다.
  비용 없는 구간(아웃라인 LLM 호출 직전 중단)까지는 알아서 진행합니다.
- **배포본 DB는 동결.** 최신화본을 옆에 두는 방식이라 A/B 대조가 유지됩니다.
- **2012년 이전 논문(약 4,200편)은 인용 불가로 둡니다.** 시간창을 1991년까지 늘리면
  7개 → 18개가 되어 파일럿과의 비교가 깨집니다.
- **평가는 SurveyBench 인용 커버리지를 회귀 검사로만.** LLM judge(SAM-O/SAM-C)는 별도 비용이라 미실시.

---

## 남은 작업

### A. 회귀 검사 — **완료 (2026-08-06 03:35)**

3토픽 × 2 DB, `eval_out/eval_<토픽>.md`. 인간 서베이를 기준선으로 함께 놓았습니다.

| 토픽 | | 총인용 | 판정가능 | matched | **정확도** | 최신 인용 |
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

**확정된 결론: 판정 가능한 인용 안에서의 정확도가 세 토픽 모두 +33포인트 근처로 오릅니다.**

| | 구 DB | 신 DB | 증가 |
|---|---:|---:|---:|
| RAG | 30.4% | 64.3% | +33.9p |
| Multi-Agent | 29.5% | 61.1% | +31.6p |
| 3DGS | 60.7% | 93.8% | +33.1p |

편차가 2.3p뿐이고, **출발점과 무관합니다** — 3DGS는 구 DB가 이미 60.7%였는데도 같은 폭으로
올랐습니다. 그래서 "못하던 게 고쳐졌다"가 아니라 **"배분이 바뀌었다"**로 읽어야 합니다.
인용 슬롯의 약 80%가 최신 논문으로 가고, 남은 20%를 훨씬 정확하게 고릅니다.

주장할 때 지켜야 할 선 셋:

- **"인간을 넘는다"고 쓰지 마세요.** 3개 중 2개만 넘었습니다(Multi-Agent는 61.1 vs 76.2).
  확인된 주장은 **"DB 최신화가 옛 논문 선택 정확도를 +33p 올린다"**입니다.
- **분모가 28 / 18 / 32편으로 작습니다.** 소수점을 믿지 마세요.
- **세 토픽 모두 신규 논문 비중 65~82%**입니다. GNN(17.3%)·3D Detection(26.7%)에서도
  같은 폭이 나올지는 **확인 안 했습니다** (§C).

**matched 절대값은 셋 다 줄었습니다**(38→18, 31→11, 71→30). 분모가 125→28, 105→18,
117→32로 무너지기 때문입니다. `coverage` 비율도 같은 이유로 오릅니다(0.304→0.643,
0.295→0.611, 0.607→0.938). **세 숫자 중 어느 것도 단독으로 읽으면 안 됩니다** —
`compare_runs.py`가 셋을 함께 냅니다.

결과는 [`README.md`](README.md) §3.5에 반영돼 있습니다.

> 3DGS는 두 번 엎어진 뒤에 나온 결과입니다 — 아웃라인 파서 `IndexError`, 그리고 OpenRouter
> 429. 재실행 두 편은 429를 각각 30회·42회 맞고도 `[GIVE UP]` 0회로 끝났습니다(백오프가
> 흡수). 같은 일이 또 나면 §함정 모음을 먼저 보세요.

### B. 서베이 DB · 아웃라인 코퍼스 증분 (미착수)

논문 DB만 갱신해서 "최신 논문을 인용"은 되지만 "최신 서베이의 구조를 학습"은 안 됩니다.
필요한 것:
- 신규 서베이 논문 수집 → MinerU로 PDF에서 아웃라인 추출 → LLM으로 정제 → `Final_outline{,_First}/`에 추가
- 서베이 DB 임베딩 append (논문 DB와 같은 방식)

참고로 배포본 서베이 DB는 레코드 18,816개인데 **벡터가 12,756개뿐**이라 6,060편은
애초에 검색되지 않습니다. 아웃라인 커버리지도 90.7% / 76.4%입니다.

### C. 나머지 7개 토픽 (필요해지면)

`SurveyBench/topics.txt`의 10개 중 RAG·Multi-Agent·3DGS를 썼습니다.
신 DB + flash 기준 편당 약 $0.33이라 쌍당 $0.7입니다.

**신규 비율이 낮은 토픽을 아직 안 봤습니다.** 지금까지 고른 셋은 전부 65~82%로 높은 쪽이라,
"신규 논문이 적은 토픽에서도 정확도가 오르는가"는 미확인입니다. 이걸 보려면
**Graph Neural Networks (17.3%)** 나 **3D Object Detection (26.7%)** 를 돌려야 합니다.
메커니즘이 "옛 슬롯이 줄어서 남은 걸 잘 고른다"라면 이 토픽들에서는 효과가 작아야 합니다.

토픽별 신규 비율(신 DB 검색 풀 1,500편 중 2024-09 이후):

| 토픽 | 신규 비율 | | 토픽 | 신규 비율 |
|---|---:|---|---|---:|
| LLM-based Multi-Agent | 81.5% ✅ | | Evaluation of LLMs | 51.2% |
| 3D Gaussian Splatting | 75.7% ✅ | | Vision Transformers | 27.7% |
| Hallucination in LLMs | 72.5% | | 3D Object Detection | 26.7% |
| RAG | 65.3% ✅ | | Graph Neural Networks | 17.3% |
| Multimodal LLM | 63.8% | | Generative Diffusion | 53.5% |

### D. DB 재갱신 (필요해지면)

```bash
scripts/update_snapshot.sh          # 수집 → 피인용수 → append → 검증, 실패 시 중단
```

소요 약 3시간 30분 (수집 1:13 / 피인용수 0:15 / 임베딩 1:40 / 검증 0:03).
arXiv OAI-PMH와 Semantic Scholar 모두 무과금입니다.
`harvest_arxiv.py`의 `--oai-from`을 현재 스냅샷 최신일로 바꾸세요.

---

## 테스트

```bash
cd code && ../.venv/bin/python ../tests/test_cutoffs.py     # 10개, 네트워크·GPU 불필요
```

교체 **이전 구현을 테스트 파일 안에 그대로 박아** 두고 기본값에서 결과가 원소 단위로
같은지 비교합니다. `git show HEAD`로 비교하면 커밋한 순간 무의미해지기 때문입니다.

---

## 함정 모음

- **`--api_url`에 `/chat/completions`를 붙이지 마세요.** id에 `deepseek`이 들어가면
  `APIModel`이 OpenAI SDK 분기를 타고 이 값을 `base_url`로 씁니다. (AutoSurvey는 반대입니다)
- **`run_demo.py`는 출력 디렉터리가 이미 있으면 조용히 건너뛰고 "성공"으로 보고합니다.**
  재실행하려면 기존 `exp_N`을 먼저 치우세요.
- **아웃라인 파서는 `Description {n}:`이 없으면 죽습니다.** 모델이 첫 항목에만 번호를 붙이고
  이후를 `Description:`으로 쓰면 `IndexError`가 나고, 아웃라인 값을 이미 지불한 뒤라
  8~12분이 통째로 날아갑니다. **섹션·서브섹션 두 레벨 모두** 고쳤지만
  (`_description_tail`), 파서가 LLM 출력 형식에 기대는 곳이 더 있을 수 있습니다.
  `temperature=1`에 시드가 없어 같은 설정에서도 재현되지 않습니다 —
  **여러 편 돌릴 때는 `set -e` 대신 `|| echo` 로 한 편 실패가 나머지를 죽이지 않게 하세요.**
- **DB를 갱신했으면 컷오프도 올리세요.** 안 올리면 §게이트 A·B가 새 논문을 전부 가립니다.
  `check_db.py`가 넣어야 할 값을 출력합니다.
- **`PAPER_DATE_NEWEST`를 짝수 해 1월 1일로 두지 마세요.** 시간창이 2012-01-01부터 2년
  단위라 경계에 정확히 걸리면 그 날짜 논문이 사라집니다(`get_time_windows`).
- **`main.py --gpu` 인자는 아무 데서도 안 쓰입니다** (파싱만 하고 버림). `CUDA_VISIBLE_DEVICES`를 쓰세요.
- **GPU 번호를 고정하지 마세요.** 공용 서버입니다. 남의 학습에 얹으면 임베딩이 68 → 32편/s로 반토막 납니다.
  `nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits | sort -t, -k2 -n | head -1`
- **`IndexIDMap`은 `add()`를 거부합니다.** `add_with_ids()`를 쓰고, stored id는 **1-based**입니다
  (AutoSurvey는 0-based라 코드를 그대로 옮기면 전부 한 칸씩 어긋납니다).
- **`downcast_index()`로 얻은 내부 인덱스를 쓸 때 부모 `IndexIDMap` 레퍼런스를 살려 두세요.**
  놓으면 dangling pointer가 되어 조용히 segfault 합니다.
- **임베딩 텍스트에 구분자를 넣지 마세요.** 규약은 `title + abs` **구분자 없는 연결**입니다.
  공백 하나만 끼워도 cos가 0.990으로 떨어집니다. 정규화·prefix 없음도 마찬가지입니다.
- **Semantic Scholar의 429는 속도 초과가 아닙니다.** 요청 간격 1s/3s/6s에서 429 비율이 모두
  50%로 동일하고 `Retry-After` 헤더도 없습니다. 확률적 거절이라 **길게 물러서면 손해**입니다
  (0.5s 재시도 329 id/s vs 2s 재시도 151 id/s).
- **OpenRouter의 429는 반대입니다 — 물러서야 합니다.** S2와 헷갈리지 마세요. Parasail
  공유 풀(`limit_source: upstream_provider_shared_pool`)은 진짜 혼잡이라 즉시 재시도하면
  워커 16개(`MAX_THREADS 8` × `MAX_SECTION_THREADS 2`)가 몇 초 만에 재시도 예산을 다 태웁니다.
  3DGS 신 DB 편이 이렇게 죽었습니다. 지금은 지터 백오프 + 실패분 **순차** 재시도가 들어가
  있습니다(`SURVEYFORGE_RETRY_BASE` / `_BATCH_RETRY_COOLDOWN`). 그래도 계속 429면 시간을
  두고 다시 돌리세요 — `SURVEYFORGE_MAX_THREADS`를 낮추는 것도 방법입니다.
  provider 폴백은 켜지 마세요, 양자화가 섞여 재현성이 깨집니다.
- **감시 스크립트에서 `pgrep -f "<대상 명령>"`을 쓰지 마세요.** 그 문자열이 감시자 자신의
  명령줄에도 들어 있어서 **자기 자신을 매치하고 영원히 기다립니다.** 실제로 3DGS 대기 루프가
  이렇게 교착됐습니다. PID로 기다리거나(`kill -0 $PID`) 대괄호 트릭(`finish_3dgs[.]sh`)을
  쓰세요. PID를 `pgrep | head -1`로 잡는 것도 위험합니다 — 순간적으로 뜬 다른 프로세스를
  잡을 수 있으니, 띄운 쪽에서 `$!`로 받으세요.
- **OAI-PMH의 `from`은 수정일 기준입니다.** 메타데이터만 갱신된 옛 논문이 딸려 옵니다
  (1991년 논문까지). `--exclude-db`로 기존 것을 걸러야 합니다.
- **`code/requirement.txt`는 그대로 설치되지 않습니다** (`numpy==1.23.5` 핀이 faiss와 충돌).
  `code/requirements-fixed.txt`를 쓰세요.
- **데이터셋 org는 `InternScience/`입니다** (README 원문은 `U4R/`). 설명이 없는
  `Final_outline.zip` / `Final_outline_First.zip` 두 개가 **필수**입니다.

---

## 서버 환경 메모

- **L40S 46GB × 8**, RAM 503GB, `/data2` 여유 약 2.6TB. **공용 서버** — GPU 0·1은 다른 사용자가 쓰는 일이 잦습니다
- 파이썬 환경은 **`.venv`** (Python 3.10.12, torch 2.1.0+cu121, faiss-cpu 1.9.0, sentence-transformers 2.7.0).
  conda `autosurvey` env은 AutoSurvey 전용이고 langchain이 없습니다
- 네트워크: `oaipmh.arxiv.org` 가능 / `api.semanticscholar.org` 가능 / HuggingFace 가능
- 실행 자산은 저장소 밖 `../SurveyForge_data/` (약 15GB)
