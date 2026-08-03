# 재현 가이드 (Reproduction)

2026-07-31에 수행한 SurveyForge 파일럿 실행을 **다른 사람이 같은 조건으로 다시 돌릴 수 있도록**
사용한 모든 입력값을 고정하고, 그 결과를 어떤 기준으로 검증했는지 정리한 문서.

- 대상 실행: `Retrieval-Augmented Generation for Large Language Models` / `exp_1`
- 결과물 경로: `code/output/res/deepseek_deepseek-v4-pro/Retrieval-Augmented Generation for Large Language Models/exp_1/`
- 이 문서는 **입력 고정과 검증**에 집중한다. 결과의 배경 설명과 엔드포인트 비교는 [`RESULT.md`](RESULT.md) 참조.

---

## 0. 한 줄 요약

| | |
|---|---|
| 모델 | `deepseek/deepseek-v4-pro` (open weight), OpenRouter 경유, **StreamLake fp8** 엔드포인트 핀 |
| 입력 | 주제 1개 + CLI 인자 6개 + 환경변수 9개 + 로컬 데이터 자산 4종 |
| 실행 | 2026-07-31 07:20:53 ~ 07:55:05 KST, **34분 11초**, GPU L40S 1장 |
| 출력 | 본문 **18,788 words** / 9 섹션 / 30 서브섹션 / 참고문헌 101편, PDF 43쪽 |
| 비용 | 1편 **$1.998** (OpenRouter 실청구). 이 중 90%가 입력 토큰, 16%가 카운터에 안 잡히는 reasoning |
| 무결성 | 잘림 0건, 빈 응답 0건, 재시도 소진 0건, 단일 provider |

---

## 1. 재현 절차

### 1.1 코드

```bash
git clone git@github.com:brian-223134/SurveyForge.git
cd SurveyForge
git checkout 0e5383d          # 이 문서가 기술하는 상태
```

업스트림은 `https://github.com/InternScience/SurveyForge`이며, 이 저장소는 `2d48aca`(Add SurveyBench)
시점의 코드를 기반으로 한다. 그 위에 올린 로컬 수정은 [6장](#6-업스트림-대비-코드-수정)에 전부 나열했다.

### 1.2 데이터 자산 (약 5.7GB, 저장소 밖)

`.env`의 `SURVEYFORGE_DATA`가 가리키는 디렉터리에 아래 4종을 받아 둔다.
저장소 밖에 두는 이유는 git을 깨끗하게 유지하기 위함이며, 경로는 자유롭다.

```bash
export DATA=/path/to/SurveyForge_data
hf download InternScience/SurveyForge_database --repo-type dataset --local-dir "$DATA"
hf download Alibaba-NLP/gte-large-en-v1.5 --local-dir "$DATA/gte-large-en-v1.5"
cd "$DATA" && unzip -q Final_outline.zip && unzip -q Final_outline_First.zip
```

> README는 데이터셋 org를 `U4R/`로 적고 있으나 실제로는 **`InternScience/`**다.
> 또 README에 설명이 없는 `Final_outline.zip` / `Final_outline_First.zip` 두 개가 **필수**다.
> 압축을 풀지 않으면 아웃라인 단계에서 참조할 예시 코퍼스가 없어 실패한다.

실행 시점의 자산 구성 (파일 크기까지 일치해야 동일 조건이다):

| 경로 | 크기 / 개수 | 용도 |
|---|---:|---|
| `database/arxiv_paper_db_with_cc.json` | 880 MB | 논문 메타데이터 + 인용수 |
| `database/arxivid_to_index_abs.json` | 15 MB | arxiv id → FAISS 인덱스 |
| `database/faiss_paper_title_abs_embeddings_FROM_2012_0101_TO_240926.bin` | 2.42 GB | 논문 title+abstract 임베딩 |
| `database/faiss_paper_title_embeddings_FROM_2012_0101_TO_240926.bin` | 2.42 GB | 논문 title 임베딩 |
| `database/surveys_arxiv_paper_db.json` | 33 MB | 서베이 메타데이터 |
| `database/surveys_arxivid_to_index_abs.json` | 454 KB | 서베이 id → 인덱스 |
| `database/faiss_survey_title_abs_embeddings_FROM_1501_TO_2409_gte.bin` | 52 MB | 서베이 title+abstract 임베딩 |
| `database/faiss_survey_title_embeddings_FROM_1501_TO_2409_gte.bin` | 52 MB | 서베이 title 임베딩 |
| `Final_outline/` | 17,072 개 `.md` | 아웃라인 예시 코퍼스 |
| `Final_outline_First/` | 14,376 개 `.md` | 아웃라인 예시 코퍼스 (1차) |
| `gte-large-en-v1.5/` | — | 임베딩 모델 (`Alibaba-NLP/gte-large-en-v1.5`) |

**지식 컷오프는 데이터에 박혀 있다.** 파일명의 `TO_240926` / `TO_2409`가 말해 주듯 논문 DB는
**2024-09-26까지**만 담고 있다. 즉 이 파이프라인이 인용할 수 있는 논문은 그 이전 것뿐이고,
모델이 아무리 최신이어도 참고문헌은 2024-09를 넘지 않는다. 재현 시 이 자산을 바꾸면
결과 비교가 성립하지 않는다.

### 1.3 파이썬 환경

`code/requirement.txt`(업스트림)는 **그대로는 설치되지 않는다** — `numpy==1.23.5` 핀이
`faiss-cpu 1.9.0`(numpy>=1.25 요구)과 충돌한다. `code/requirements-fixed.txt`를 쓴다.

```bash
python3 -m venv .venv
.venv/bin/pip install -r code/requirements-fixed.txt
```

실행 시점의 검증된 조합:

| | 버전 |
|---|---|
| Python | 3.10.12 |
| torch | 2.1.0 |
| transformers | 4.44.2 |
| sentence-transformers | 2.7.0 |
| huggingface_hub | 0.25.2 (transformers 4.44는 <1.0 요구) |
| faiss-cpu | 1.9.0 |
| numpy | 1.26.4 |
| openai | 1.52.0 |
| tiktoken | 0.7.0 |
| requests | 2.32.3 |
| OS / GPU | Linux 5.15.0 / NVIDIA L40S 46GB, 드라이버 550.120 |

GPU는 **임베딩과 FAISS 검색에만** 쓰인다. 생성은 전부 원격 API이므로 GPU 종류가 결과를 바꾸지 않는다.

### 1.4 `.env`

`.env.example`을 복사해 채운다. 파일은 gitignore 대상이며 **절대 커밋하지 않는다.**

```bash
cp .env.example .env
```

실행에 사용한 값 (키 제외 전문):

| 변수 | 값 | 비고 |
|---|---|---|
| `OPENROUTER_API_KEY` | *(비공개)* | argv로 넘기지 않는다 — `ps`에 노출되므로 |
| `SURVEYFORGE_MODEL` | `deepseek/deepseek-v4-pro` | id에 `deepseek`이 있으면 OpenAI SDK 분기를 탄다 |
| `SURVEYFORGE_API_URL` | `https://openrouter.ai/api/v1` | SDK 분기에서는 `base_url`이므로 **엔드포인트 경로를 붙이면 안 된다** |
| `SURVEYFORGE_PROVIDER` | `streamlake/fp8` | 아래 참조 |
| `SURVEYFORGE_QUANTIZATIONS` | *(빈 값)* | provider를 직접 지정했으므로 미사용 |
| `SURVEYFORGE_REASONING_EFFORT` | *(빈 값)* | provider 기본값 사용 |
| `SURVEYFORGE_REASONING_EXCLUDE` | *(빈 값)* | reasoning이 `content`를 오염시키지 않아 불필요 |
| `SURVEYFORGE_MAX_TOKENS` | `65536` | 길이 통제가 아니라 **잘림 방지용** |
| `SURVEYFORGE_MAX_THREADS` | `8` | |
| `SURVEYFORGE_MAX_SECTION_THREADS` | `2` | 최대 동시 요청 = 2 × 8 = **16** |
| `SURVEYFORGE_DATA` | `/data2/chanjoong/survey-agent/SurveyForge_data` | 1.2의 경로 |
| `SURVEYFORGE_EXPS` | `1` | 주제당 반복 횟수 |

**provider를 반드시 핀해야 한다.** OpenRouter는 요청마다 독립적으로 라우팅하는데,
이 모델의 18개 엔드포인트는 **서로 다른 quantization**(fp4 / fp8 / unknown)으로 같은 가중치를 서빙한다.
핀하지 않으면 서베이 한 편의 서브섹션들이 fp4와 fp8이 섞인 채 작성되어 통제된 실험이 아니게 된다.
`SURVEYFORGE_PROVIDER`를 설정하면 `allow_fallbacks=false`도 함께 켜지므로, 장애 시 조용히 다른
가중치로 넘어가지 않고 재시도한다.

1st-party `deepseek` 엔드포인트가 최저가($0.43/$0.87 per M)지만 이 계정에서는 막혀 있다
(`404 No endpoints available matching your guardrail restrictions and data policy`).
계정의 privacy/데이터 정책 설정 때문이며, 해제하려면 openrouter.ai/settings/privacy를 완화해야 한다.
그러지 않기로 하고 **서빙 가능한 것 중 최저가**인 `streamlake/fp8`($0.67/$1.34 per M)로 핀했다.
fp8은 DeepSeek이 실제로 배포하는 정밀도라 fp4 엔드포인트보다 원본 가중치에 가깝다.

`SURVEYFORGE_MAX_TOKENS=65536`은 **길이 조절 파라미터가 아니다.** 값을 생략해도 "무제한"이 아니라
provider별 상한(DeepInfra 16,384 ~ Parasail 1,048,576, 64배 차이)이 그때그때 적용되므로,
명시적으로 보내야 조건이 고정된다. 32,768에서 65,536으로 올린 이유는 StreamLake가 프로브에서
reasoning 오버헤드가 가장 컸고(같은 질문에 3,834자 vs Novita 318자) reasoning이 같은 예산에서
빠져나가기 때문이다. 서브섹션이 상한에 걸려 잘리면 **길이 측정 자체가 무의미**해진다.
쓰지 않은 토큰은 과금되지 않으므로 여유는 공짜다.

### 1.5 실행

```bash
cd code
../.venv/bin/python run_demo.py "Retrieval-Augmented Generation for Large Language Models"
```

- 인자를 주지 않으면 `code/topics_demo.txt`의 주제를 쓴다.
- 출력은 `code/output/res/<model-slug>/<topic>/exp_<n>/`에 쌓인다.
- **`run_demo.py`는 디렉터리가 이미 있으면 조용히 건너뛰고 성공으로 보고한다.**
  다시 돌리려면 기존 `exp_1/`을 옮기거나 지워야 한다.
- 주제 문자열은 `SurveyBench/ref_bench/<topic>_bench.json`과 **정확히 일치**해야 후속 정량 평가가 된다.
  벤치마크 토픽 10개는 `SurveyBench/topics.txt`에 있다.

### 1.6 LaTeX 변환 (선택)

`.md`의 참고문헌은 제목만 나열하고 arxiv id는 형제 `.json`에만 있다. 이 둘과 로컬 DB를 조인해
링크가 살아 있는 서지를 만든다.

```bash
../.venv/bin/python tools/md_to_tex.py \
  "output/res/deepseek_deepseek-v4-pro/Retrieval-Augmented Generation for Large Language Models/exp_1" \
  --compile
```

`<topic>.tex`, `<topic>.bib`, `<topic>.pdf`를 만든다. `.tex`는 `thebibliography`를 내장해
**원본 번호 체계를 그대로 보존**한다(BibTeX 스타일은 재번호를 매겨 원본 대조를 깨뜨린다).
외부 의존이 없어 `.tex` 하나만 Overleaf에 올려도 컴파일된다(pdfLaTeX, bibtex 패스 불필요).

---

## 2. 입력값 전체 목록

### 2.1 CLI 인자 (`run_demo.py` → `main.py`)

| 인자 | 사용값 | `main.py` 기본값 | 의미 |
|---|---|---|---|
| `--topic` | `Retrieval-Augmented Generation for Large Language Models` | `Multimodal Large Language Models` | |
| `--section_num` | **7** | 6 | **본문** 섹션 수. Introduction/Conclusion은 별도로 붙어 총 9가 된다 |
| `--subsection_len` | **500** | 500 | 서브섹션당 목표 단어 수 (프롬프트의 WORD NUM) |
| `--rag_num` | **100** | 100 | 서브섹션 작성 시 검색할 논문 수 |
| `--rag_max_out` | **60** | 60 | 리랭킹 후 프롬프트에 넣을 논문 수 |
| `--outline_reference_num` | **1500** | 1500 | 아웃라인 단계에서 검색할 논문 수 |
| `--debug` | **켬** | 끔 | 중간 산출물(청크 아웃라인, 검색 결과, RAG 덤프) 저장 |
| `--gpu` | `0` | `0` | 임베딩/FAISS용 |
| `--saving_path` | `./output/res/<slug>/<topic>/exp_1` | `./output/` | |
| `--model` / `--api_url` | `.env`에서 | — | |
| `--api_key` | **넘기지 않음** | `$OPENROUTER_API_KEY` | argv에 비밀을 두면 `ps`로 새어 나간다 |
| `--db_path` / `--survey_outline_path` / `--embedding_model` | `$SURVEYFORGE_DATA` 하위 | — | |
| `--ckpt` | *(빈 값)* | *(빈 값)* | 로컬 모델용, 미사용 |

`--section_num 7`이 9개 섹션을 만든 것은 오류가 아니다. 병합 프롬프트가
`Start with an Introduction section / Include approximately [SECTION NUM] main body sections / End with a Conclusion section`
라고 지시하므로 **7 + 2 = 9**가 정상이고, 실제 산출도 정확히 그렇다.

### 2.2 샘플링 파라미터

| 위치 | 호출 | temperature |
|---|---|---:|
| `outline_writer.py:199` | rough outline (batch) | 1 |
| `outline_writer.py:222` | outline 병합 | 1 |
| `outline_writer.py:285` | 서브섹션 아웃라인 (batch) | 1 |
| `outline_writer.py:302` | 서브아웃라인 병합 | 1 |
| `writer.py:230` | 서브섹션 본문 (batch) | 1 |
| `writer.py:244` | 인용 검증 (batch) | 1 |
| `writer.py:272` | LCE 정제 | 1 |

**`temperature=1`이 전부이고 seed는 어디에도 없다.** `top_p`, `frequency_penalty` 등은 보내지 않아
provider 기본값이 적용된다. 이것이 재현성의 가장 큰 제약이다 ([3장](#3-재현성의-한계)).

### 2.3 LLM을 쓰지 **않는** 단계

아래는 결정론적이므로 재현 시 동일하게 나와야 한다. 여기서 차이가 나면 데이터 자산이 다른 것이다.

- 논문/서베이 검색: 임베딩(gte-large) + FAISS + 인용수 정렬
- 아웃라인 예시 코퍼스 선택: 파일 읽기만 함
- 리랭킹: 임베딩 유사도
- 인용 번호 부여: `retrieve_id4citation`의 임베딩 최근접(top_k=1) 스냅

---

## 3. 재현성의 한계

**같은 값이 나오지 않는다.** 재현이란 여기서 "동일 텍스트"가 아니라 "동일 조건에서 통계적으로
같은 분포의 산출"을 뜻한다. 원인을 큰 것부터:

| # | 원인 | 영향 | 완화 |
|---|---|---|---|
| 1 | `temperature=1`, seed 없음 | 아웃라인 구조·서브섹션 수·문장 전부 달라짐 | 코드 수정 없이는 불가. `temperature=0`으로 바꿔도 provider가 완전 결정론을 보장하지 않음 |
| 2 | 서브섹션 수 S를 LLM이 자유롭게 정함 | **총 길이가 여기서 결정된다.** 저자 기준선의 2.5배 편차(13,242~32,938 words)도 대부분 이 탓 | 길이를 맞추려면 `--subsection_len`이 아니라 S를 고정해야 한다 |
| 3 | provider 측 비결정성 | 배치 크기·커널에 따라 같은 요청도 다른 출력 | 없음 |
| 4 | 스레드 인터리빙 (동시 16) | 배치 내 순서·재시도 타이밍 | `MAX_THREADS=1`로 줄이면 감소하나 매우 느려짐 |
| 5 | OpenRouter 모델/엔드포인트 드리프트 | 시간이 지나면 `streamlake/fp8`이 사라지거나 가중치가 갱신될 수 있음 | provider 핀 + 로그의 `[PROVIDER]` 줄로 사후 확인 |
| 6 | 데이터 자산 버전 | 참고문헌 후보 집합이 통째로 바뀜 | 1.2의 파일 크기로 대조 |

**고정되는 것**: 검색된 논문 1,500편, 선택된 예시 서베이, 리랭킹 결과, 인용 번호 스냅 로직 —
전부 LLM을 타지 않으므로 동일 자산이면 동일하다.

---

## 4. 결과 및 분석

### 4.1 산출 파일 (31개, 29MB)

| 파일 | 내용 |
|---|---|
| `<topic>.md` / `<topic>.json` | **최종 산출물.** json은 `{"survey":…, "reference":{"1":"2005.11401v4",…}}` |
| `<topic>.tex` / `.bib` / `.pdf` | `md_to_tex.py` 산출 (git 추적 대상) |
| `raw_survey.txt` / `refined_survey.txt` | LCE 정제 전/후 |
| `*_with_references.jsonl` | 인용 번호가 박힌 버전 |
| `1-Total_1500_papers*.txt` | 아웃라인용 검색 결과 |
| `1-Chunk_outlines.json`, `2-Merged_outlines*.txt`, `3-Merged_Sub_outline*` | 아웃라인 단계별 중간 산출 (`--debug`) |
| `Survey_titles_rough/high.txt` | 예시로 쓰인 서베이 목록 |
| `rag_docs_writer_*.jsonl`, `section_references_ids.json`, `total_ids.txt` | 본문 RAG 검색 결과 |
| `citations.txt`, `reference_metadata.json` | 인용 매핑, arxiv 메타데이터 캐시 |
| `time_cost.log`, `experiment_times.log` | 단계별 소요·토큰 |
| ~~`paper_texts.txt`~~ | 24MB 초록 덤프. 재생성 가능하므로 gitignore |

### 4.2 측정값

| 항목 | 값 | 측정 방법 |
|---|---|---|
| 본문 단어 수 | **18,788** | References 절 제거 → `[n]` 인용 마커 제거 → 공백 분리 |
| 섹션 | **9** (Introduction + 7 + Conclusion) | `^## ` |
| 서브섹션 **S** | **30** | `^### ` |
| 서브섹션당 평균 | **626 words** | 18,788 / 30, 목표 500 대비 **+25%** |
| 참고문헌 | **101편 등록 / 101편 전부 인용됨** | `.json`의 `reference` 키 수 |
| 인용 표기 등장 | 245회 | `[n]` 또는 `[n; m]` 브래킷 |
| PDF | 43쪽, `\cite` 245 / `\bibitem` 101 | undefined citation/reference 0 |

```python
# 단어 수 재현 스니펫
import re
t = open("<topic>.md").read()
b = t[:t.rfind("## References")]
print(len(re.sub(r"\[\d+(?:\s*;\s*\d+)*\]", " ", b).split()))   # 18788
```

> **`RESULT.md`의 "본문 인용 92개"는 과소 집계다.** 92는 `[12]` 형태의 단일 브래킷만 센 값이고,
> `[12; 45]` 같은 묶음 인용까지 세면 **101편 전부가 본문에 인용**된다. 즉 참고문헌에 등록되고
> 본문에서 쓰이지 않은 항목(고아 서지)은 없다.
> 단어 수도 `RESULT.md`는 18,807, 여기서는 18,788로 19단어(0.1%) 차이가 나는데,
> References 절 경계를 잡는 방식 차이일 뿐 결론에 영향이 없다. 위 스니펫이 재현 가능한 기준이다.

### 4.3 소요 시간 및 토큰

| 단계 | 소요 |
|---|---|
| DB / FAISS 로딩 | ~2분 |
| 아웃라인 (검색 → 청크 → 병합 → 서브아웃라인) | ~8.5분 |
| 본문 작성 + 인용 검증 + LCE 정제 | ~23.6분 |
| **총계** | **34분 11초** |

| | 입력 | 출력(가시) |
|---|---:|---:|
| OutlineWriter | 618,707 | 40,071 |
| SubsectionWriter | 1,623,049 | 87,777 |
| **합계** | **2,241,756** | **127,848** |

> **`experiment_times.log`의 아웃라인 입력 481,888은 틀린 값이다.** `run_demo.py`의
> `extract_token_usage`가 `re.search`로 **첫 매치만** 잡는데 `outline_writer.py:132`가
> 아웃라인 중간에 토큰 사용량을 한 번 더 출력하기 때문이다(136,819 누락).
> 위 표는 실제값을 쓴다.

### 4.4 비용

전부 OpenRouter `total_usage` 차이로 잰 **실청구액**이다. 토큰 카운터 추정이 아니다
(추정을 쓰면 아래 reasoning 항목이 통째로 누락된다).

| 구간 | 금액 |
|---|---:|
| 아웃라인 (검색 → 청크 → 병합 → 서브아웃라인) | $0.5115 |
| 본문 작성 + 인용 검증 + LCE 정제 | $1.4864 |
| **서베이 1편** | **$1.998** |
| 실패한 첫 실행 (`--debug`의 `UnboundLocalError`) | $0.4908 |
| **파일럿 총 지출** | **$2.4887** |

| 편수 | 비용 |
|---:|---:|
| 1 | $2.00 |
| 3 | $5.99 |
| 10 | $19.98 |

잔액 $187.55 기준 약 **94편**. 예산은 제약이 아니다.

**입력이 비용의 90%다.** 입력 2,241,756 × $0.67/M = $1.502, 가시 출력 127,848 × $1.34/M = $0.171.
참고문헌 초록을 단계마다 다시 전송하는 구조 때문이며, 따라서 비용을 줄이려면 출력이 아니라
`--rag_num` / `--outline_reference_num`을 건드려야 한다.

**숨은 비용: reasoning 토큰.** 위 두 항목의 합은 $1.673인데 실청구는 $1.998이다.
차액 **$0.325 ≈ 242k reasoning tokens**가 어느 토큰 카운터에도 잡히지 않은 채 출력 단가로
과금됐다 — 가시 출력(127,848)의 **1.9배**, 총액의 **16%**. V4 Pro가 reasoning 모델이고
StreamLake가 프로브에서 오버헤드가 가장 컸던 엔드포인트이기 때문이다.
줄이려면 `SURVEYFORGE_REASONING_EFFORT=low`를 주거나 오버헤드가 가장 작았던
`novita/fp8`(단가는 1.75배)로 옮기는 방법이 있으나, **둘 다 모델 거동을 바꾸므로
품질 확인 없이 적용하면 이 문서의 측정값과 비교할 수 없게 된다.**

reasoning은 `content`가 아닌 별도 필드로 오므로 아웃라인 파서(`'Title: '`로 split)를 오염시키지는 않는다.

### 4.5 무결성 검증

재현 실행이 유효한지 판단하는 기준. 로그에서 확인한다.

| 확인 항목 | 이번 실행 | 실패 시 의미 |
|---|---|---|
| `[PROVIDER] served by:` | **StreamLake 단일** | 여러 개면 quantization이 섞였다 → 통제 실험 아님 |
| `[TRUNCATED]` (finish_reason=length) | **0건** | 1건이라도 있으면 **길이 측정값을 신뢰할 수 없다** |
| `[EMPTY]` (content=None) | **0건** | reasoning이 예산을 다 씀 → `MAX_TOKENS` 상향 필요 |
| `[GIVE UP]` (재시도 소진) | **0건** | 해당 서브섹션이 통째로 비었다 |
| API 에러 | 4건, **전부 첫 재시도에서 복구** | 동시 요청 중 간헐 발생, 재시도 루프가 흡수 |
| 아웃라인 누락 경고 | 0건 | |

`[TRUNCATED]` 0건이 핵심이다. 이것이 확인되어야 **18,788이라는 값을 "모델의 자연스러운 출력 길이"로**
해석할 수 있다. 에러 4건의 내역은 `'NoneType' object is not subscriptable`
(OpenRouter가 HTTP 200 본문에 에러를 실어 보내 `completion.choices`가 None) 3건, JSON 파싱 실패 1건이다.

### 4.6 길이 통제에 대한 함의

논문 간 출력 길이를 맞추는 것이 목표라면, **어떤 레버가 실제로 듣는지**가 결론이다.

- `--subsection_len`은 **듣는다**. 목표 500 → 실측 626으로 수렴했고 섹션 2~7의 편차도 2,113~2,916으로 좁다.
- 총 길이를 실제로 지배하는 건 **서브섹션 수 S**이고, 이건 아웃라인 단계에서 LLM이 자유롭게 정한다.
- 저자 기준선(13,242~32,938 words) 안에는 들어가지만 중앙값 ~26,000의 **0.72배**다.
  중앙값에 맞추려면 **S≈41** 또는 `subsection_len≈700`이 필요하다.
- Introduction(516 words)과 Conclusion(685 words)은 서브섹션이 없어 짧게 나온다 — 계산에 넣을 것.

**→ 길이를 맞추려면 `subsection_len`이 아니라 S를 고정해야 한다.**

---

## 5. 검증 체크리스트

재현 실행이 끝났을 때 순서대로 확인한다.

- [ ] 로그에 `[PROVIDER] served by:` 가 **한 종류만** 등장하는가
- [ ] `[TRUNCATED]` / `[EMPTY]` / `[GIVE UP]` 이 0건인가
- [ ] `exp_1/`에 `<topic>.md`와 `<topic>.json`이 모두 있는가
- [ ] `.json`의 `reference` 개수와 `.md`의 References 항목 수가 일치하는가
- [ ] 본문 단어 수가 13,000~33,000 범위에 있는가 (저자 기준선)
- [ ] 섹션 수 = `--section_num` + 2 인가
- [ ] `md_to_tex.py --compile`이 undefined citation 0으로 통과하는가
- [ ] `experiment_times.log`의 아웃라인 입력 토큰은 **믿지 말 것** (4.3의 버그)

---

## 6. 업스트림 대비 코드 수정

`2d48aca` 기준, 이 실행을 위해 바꾼 것 전부:

| 파일 | 내용 | 왜 |
|---|---|---|
| `code/run_demo.py` | `sys.executable` 사용, `.env` 로딩, 모델별 출력 경로 분리, `--debug` 활성화, `--api_key` 미전달 | venv 인터프리터 사용 / 비밀 노출 차단 / 모델 간 결과 충돌 방지 |
| `code/main.py` | `print(args)`의 API 키 마스킹 | 로그에 평문 유출 |
| `code/src/model.py` | provider·quantization·reasoning 핀 지원, `MAX_TOKENS` 환경변수화, `[PROVIDER]`/`[TRUNCATED]`/`[EMPTY]` 로깅, `content=None` 재시도 가드 | 통제 실험 조건 확보 + reasoning 모델 대응 |
| `code/src/agents/outline_writer.py` | `filter_by_outline()` 추가, `--debug` 경로의 `UnboundLocalError` 수정 | 아래 |
| `code/requirements-fixed.txt` | 설치 가능한 의존성 목록 (신규) | 원본이 해석 불가 |
| `code/tools/md_to_tex.py` | Markdown → LaTeX 변환기 (신규) | `.md` 참고문헌이 제목뿐이라 링크가 없음 |
| `.env` / `.env.example` / `.gitignore` | 설정 외부화, 실행 산출물 추적 | |

### 발견한 업스트림 버그

**1. `outline_writer.py` — `--debug`에서만 터지는 `UnboundLocalError`**

```python
if self.args.debug:
    with open(f"{...}/3-Merged_Sub_outline_wo_process.txt", "w") as f:
        f.write(merged_outline + '\n\n')      # 아직 미할당

merged_outline = self.process_outlines_points(...)   # 여기서 최초 할당
```

디버그 블록이 두 줄 먼저 놓여 있다. 파일명이 `wo_process`인 걸 보면 의도는
`process_outlines_points()` **이전** 상태를 덤프하는 것이었으므로 `subsection_outlines`를
JSON으로 쓰도록 고쳤다. **`--debug` 없이는 발생하지 않는다.**

**2. `run_demo.py`의 `extract_token_usage`가 아웃라인 토큰을 과소 집계** — 4.3 참조.

**3. 아웃라인 코퍼스가 서베이 DB id를 전부 덮지 않는다** — `Final_outline` 90.7%,
`Final_outline_First` 76.4%. 현재는 `filter_by_outline()`이 누락분을 걸러내 안전하지만,
검색 결과가 전부 누락되는 주제에서는 `RuntimeError`가 난다.

---

## 7. 아직 하지 않은 것

- **`SurveyBench/ref_bench/`를 이용한 정량 평가 미실시.** 주제를 벤치마크 토픽으로 고른 이유가
  이것이므로(`ref_bench/Retrieval-Augmented Generation for Large Language Models_bench.json`이 존재),
  citation recall 등 대조 평가가 다음 단계다.
- **1편만 실행.** temperature=1에 seed가 없으므로 길이·구조의 분산을 알려면 같은 주제 n회 반복이 필요하다.
- **인용 정합성 미검증.** 인용 번호는 LLM이 쓴 자유 텍스트 제목을 임베딩 최근접(top_k=1)으로
  스냅한 결과이며 **임계값도 검증도 없다.** 존재하지 않는 논문 제목을 쓰더라도 가장 가까운 논문으로
  매핑되므로, "인용이 달려 있다"가 "옳게 인용했다"를 뜻하지 않는다.
- **API 키 교체.** `main.py`는 마스킹하도록 고쳤으나, 이 수정 이전 로그에는 키가 평문으로 남아 있다.
