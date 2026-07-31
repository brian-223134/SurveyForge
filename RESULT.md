# SurveyForge 파일럿 실행 결과

open-weight 모델로 SurveyForge를 재현했을 때의 **출력 길이**와 **편당 비용**을 확정하기 위한
1편 규모 파일럿. 측정된 값은 전부 실측이며, 비용은 토큰 카운터가 아니라 OpenRouter 실청구액 기준이다.

- 실행일: 2026-07-31
- 결과물: `code/output/res/deepseek_deepseek-v4-pro/Retrieval-Augmented Generation for Large Language Models/exp_1/`
- 코드 기준 커밋: `88c3fde` + 이 실행을 위한 로컬 수정 (아래 "코드 수정 사항")

---

## 1. 모델 및 실행 구성

| 항목 | 값 |
|---|---|
| 모델 | `deepseek/deepseek-v4-pro` (**open weight**) |
| 경유 | OpenRouter (`https://openrouter.ai/api/v1`) |
| 엔드포인트 (핀) | **StreamLake, fp8** (`SURVEYFORGE_PROVIDER=streamlake/fp8`) |
| 단가 | 입력 $0.67/M · 출력 $1.34/M |
| `max_tokens` | 65,536 |
| reasoning 설정 | 미지정 (provider 기본값) |
| 동시 요청 | `MAX_SECTION_THREADS`(2) × `MAX_THREADS`(8) = 최대 16 |
| GPU | L40S 1장 (`CUDA_VISIBLE_DEVICES=0`, 임베딩·FAISS 용도) |

### 왜 first-party DeepSeek이 아닌가

`deepseek` 1st-party 엔드포인트가 가장 저렴하지만($0.43/$0.87 per M) 이 계정에서는 막혀 있다:

```
404 No endpoints available matching your guardrail restrictions and data policy.
```

계정의 privacy/데이터 정책 설정 때문이며, 해제하려면 openrouter.ai/settings/privacy에서
데이터 정책을 완화해야 한다. 이를 건드리지 않기로 하고, **서빙 가능한 엔드포인트 중 최저가**인
StreamLake로 핀했다. fp8은 DeepSeek이 실제로 배포하는 정밀도라 fp4 엔드포인트보다 원본에 가깝다.

### 엔드포인트 실측 비교 (동일 프롬프트 프로브)

| tag | 상태 | quant | in $/M | out $/M | max_out |
|---|---|---|---|---|---|
| `deepseek` (1st-party) | **404 차단** | unknown | 0.43 | 0.87 | 384k |
| **`streamlake/fp8`** | **채택** | fp8 | **0.67** | **1.34** | 384k |
| `novita/fp8` | OK | fp8 | 1.17 | 2.34 | 393k |
| `alibaba/fp8` | OK | fp8 | 1.42 | 2.83 | 393k |
| `baidu/fp8` | OK이나 `content=None` 반환 | fp8 | 1.69 | 3.38 | 393k |
| `parasail/fp8` | OK | fp8 | 1.74 | 3.48 | 1M |
| `coreweave/fp8`, `fireworks` | 429 | — | — | — | — |

**엔드포인트를 핀해야 하는 이유:** OpenRouter는 요청마다 독립적으로 라우팅하는데, 이 모델의
엔드포인트들은 **서로 다른 quantization**(fp4/fp8/unknown)으로 같은 가중치를 서빙한다.
핀하지 않으면 서베이 한 편의 서브섹션들이 fp4와 fp8이 섞인 채로 작성되어 통제된 실험이 아니게 된다.
`allow_fallbacks=false`도 함께 설정되므로 장애 시 조용히 다른 가중치로 넘어가지 않고 재시도한다.

---

## 2. 생성 방식

주제: **`Retrieval-Augmented Generation for Large Language Models`**
(SurveyBench의 10개 벤치마크 토픽 중 하나. `SurveyBench/ref_bench/`와 문자열이 정확히 일치해야
후속 정량 평가가 가능하므로 그대로 사용했다.)

### 파라미터

```
--section_num 7  --subsection_len 500  --rag_num 100
--rag_max_out 60 --outline_reference_num 1500  --debug
```

### 파이프라인

| 단계 | LLM 호출 | 소요 |
|---|---|---|
| DB / FAISS / RAG 인덱스 로딩 | 없음 | ~2분 |
| ① 논문 1,500편 검색 → 13개 청크로 rough outline | 있음 (batch) | |
| ② rough outline 병합 → 섹션 아웃라인 | 있음 | ~8.5분 (①~③ 합) |
| ③ 서브섹션 아웃라인 전개 | 있음 (batch) | |
| ④ 서브섹션 본문 작성 + 인용 검증 | 있음 (batch, 섹션 9개) | ~23.6분 (④~⑤ 합) |
| ⑤ LCE 정제 (parity 0 / 1) | 있음 | |
| **총계** | | **34분 11초** |

**heuristic outline DB는 LLM을 쓰지 않는다.** 사전 구축된 `.md` 코퍼스를 파일로 읽어
아웃라인 프롬프트에 예시로 끼워 넣을 뿐이다. 검색·리랭킹도 임베딩 + FAISS + 인용수 정렬이라
LLM이 개입하지 않는다. 이번 실행에서 예시로 선택된 서베이 5편은 다음과 같아 주제 적합성이 높았다:

- Large Language Models for Information Retrieval: A Survey
- A Survey on Retrieval-Augmented Text Generation for Large Language Models
- Graph Retrieval-Augmented Generation: A Survey
- Retrieval-Augmented Generation for Natural Language Processing: A Survey
- Evaluation of Retrieval-Augmented Generation: A Survey

---

## 3. 출력

| 항목 | 값 |
|---|---|
| **본문 단어 수** | **18,807 words** |
| 저자 기준선 대비 | 13,242~32,938 **범위 내**, 중앙값(~26,000)의 **0.72배** |
| 섹션 수 | 9 (Introduction + 7 + Conclusion) |
| 서브섹션 수 **S** | **30** |
| 서브섹션당 평균 | **627 words** (목표 500 대비 +25%) |
| 참고문헌 | 101개 등록 / 본문 인용 92개 |
| 파일 크기 | `.md` 156KB, `.json` 162KB |

단어 수는 저자들의 `demo_papers/` 29편과 동일한 기준으로 측정했다 — References 섹션 제거,
인라인 `[n]` 인용 마커 제거 후 공백 분리.

### 섹션별 분포

| 섹션 | 단어 | 서브섹션 |
|---|---:|---:|
| 1 Introduction | 516 | 0 |
| 2 Foundations and Taxonomy of RAG | 2,916 | 4 |
| 3 Retrieval Mechanisms and Knowledge Source Construction | 2,113 | 4 |
| 4 Integration Strategies for Augmented Generation | 2,380 | 4 |
| 5 Training and Optimization of Retrieval-Augmented Systems | 2,188 | 4 |
| 6 Evaluation, Benchmarking, and Trustworthiness Assessment | 2,189 | 4 |
| 7 Applications and Domain-Specific Adaptations | 2,214 | 4 |
| 8 Open Challenges and Future Research Directions | 3,532 | 6 |
| 9 Conclusion | 685 | 0 |

### 길이 통제에 대한 함의

논문 간 출력 길이를 맞추려면 **어떤 레버가 실제로 작동하는지**가 중요하다.

- `--subsection_len`(프롬프트의 WORD NUM)은 **잘 작동한다**. 목표 500에 실측 627로 수렴했고
  섹션 2~7의 편차도 2,113~2,916으로 좁다.
- 전체 길이를 실제로 좌우하는 건 **서브섹션 수 S**이고, 이건 아웃라인 단계에서 LLM이 자유롭게 정한다.
  이번엔 S=30이 나왔지만 주제에 따라 크게 흔들릴 수 있다. 저자 기준선의 2.5배 편차
  (13,242~32,938)도 대부분 여기서 온다.
- 중앙값 26,000에 맞추려면 S≈41 또는 `subsection_len`≈700이 필요하다.
- **결론: 논문 간 길이를 맞추려면 `subsection_len`이 아니라 S를 고정해야 한다.**
  Introduction/Conclusion은 서브섹션이 없어 각 500~700 words로 짧게 나오는 점도 감안할 것.

---

## 4. 비용

### 실측 (OpenRouter `total_usage` 차이)

| 구간 | 금액 |
|---|---:|
| 아웃라인 (①~③) | $0.5115 |
| 본문 (④~⑤) | $1.4864 |
| **서베이 1편 총액** | **$1.998** |

### 토큰

| | 입력 | 출력 |
|---|---:|---:|
| OutlineWriter | 618,707 | 40,071 |
| SubsectionWriter | 1,623,049 | 87,777 |
| **합계** | **2,241,756** | **127,848** |

**입력이 비용의 90%**를 차지한다. 참고문헌 초록을 단계마다 다시 전송하는 구조 때문이며,
비용을 줄이려면 출력이 아니라 `--rag_num` / `--outline_reference_num`을 건드려야 한다.

### reasoning 토큰 (숨은 비용)

카운트된 토큰의 정가 환산은 $1.673인데 실제 청구는 $1.998이다. 차액 **$0.325**는
`reasoning` 필드로 반환되는 토큰이며, 출력 단가로 과금되지만 어느 토큰 카운터에도 잡히지 않는다.

- 약 **242k reasoning tokens** = visible output(127,848)의 **1.9배**
- **총액의 16%**

DeepSeek V4 Pro가 reasoning 모델이기 때문이며, StreamLake는 프로브에서 reasoning 오버헤드가
가장 컸던 엔드포인트다. 줄이려면 `SURVEYFORGE_REASONING_EFFORT=low`를 주거나
오버헤드가 가장 작았던 `novita/fp8`(단가는 1.75배)로 옮기는 방법이 있으나, 둘 다 모델 거동을
바꾸므로 품질 확인 없이 적용하지 말 것.

reasoning은 `content`가 아닌 **별도 필드**로 오므로 아웃라인 파서
(`extract_title_sections_descriptions`가 `'Title: '`로 split)를 오염시키지는 않는다.

### 규모 환산

| 편수 | 비용 |
|---:|---:|
| 1 | $2.00 |
| 3 | $5.99 |
| 10 | $19.98 |

잔액 $187.55 기준 **약 94편** 가능. 예산은 제약이 아니다.
(참고: 실패한 첫 실행에 $0.4908이 별도로 소요되어 파일럿 총 지출은 $2.4887.)

---

## 5. 무결성 검증

| 항목 | 결과 |
|---|---|
| `[TRUNCATED]` (finish_reason=length) | **0건** |
| `[EMPTY]` (content=None) | **0건** |
| `[GIVE UP]` (재시도 소진) | **0건** |
| API 에러 | 4건 — **전부 첫 재시도에서 복구** |
| `[PROVIDER] served by:` | **StreamLake 단일** |

`[TRUNCATED]` 0건이 중요하다. 출력이 상한에 걸려 잘렸다면 길이 측정 자체가 무의미해지는데,
`max_tokens`를 65,536으로 올린 덕에 **18,807이라는 값은 모델의 자연스러운 출력 길이**로 신뢰할 수 있다.

`[PROVIDER]` 단일 확인은 quantization 혼입이 없었다는 뜻이므로, 이 실행은 재현 가능한 통제 조건을 만족한다.

API 에러 4건의 내역은 `'NoneType' object is not subscriptable`(OpenRouter가 HTTP 200에 에러
바디를 실어 보내 `completion.choices`가 None) 3건과 응답 JSON 파싱 실패 1건이다. 동시 요청 중
간헐적으로 발생하며 기존 재시도 루프가 흡수한다.

---

## 6. 코드 수정 사항

이 실행을 위해 수정한 파일 (`88c3fde` 기준):

| 파일 | 내용 |
|---|---|
| `.env` | provider `deepseek` → `streamlake/fp8`, `MAX_TOKENS` 32,768 → 65,536 |
| `code/src/model.py` | `content`가 비어 있으면 반환하지 않고 재시도하도록 가드 추가 |
| `code/src/agents/outline_writer.py` | `--debug` 경로의 `UnboundLocalError` 수정 (아래) |
| `code/run_demo.py` | `--debug` 활성화 |
| `code/main.py` | `print(args)`가 API 키를 평문 출력하던 것을 마스킹 |

### 발견한 업스트림 버그

**`outline_writer.py:148-150` — `--debug`에서만 터지는 `UnboundLocalError`**

```python
if self.args.debug:
    with open(f"{...}/3-Merged_Sub_outline_wo_process.txt", "w") as f:
        f.write(merged_outline + '\n\n')      # merged_outline은 아직 미할당

merged_outline = self.process_outlines_points(...)   # 여기서 최초 할당
```

디버그 블록이 두 줄 먼저 놓여 있다. 파일명이 "wo_process"인 것으로 보아 의도는
`process_outlines_points()` **이전** 상태를 덤프하는 것이었으므로, `subsection_outlines`를
JSON으로 쓰도록 고쳤다. **`--debug` 없이 돌리면 발생하지 않는다.**

**`run_demo.py`의 `extract_token_usage`가 아웃라인 토큰을 과소 집계**

`re.search`는 첫 매치만 잡는데, `outline_writer.py:132`가 아웃라인 **중간** 시점에
토큰 사용량을 한 번 출력한다. 그래서 `experiment_times.log`에는 481,888이 기록되지만
실제 아웃라인 단계 입력은 **618,707**이다 (136,819 누락). 이 파일의 표는 실제값을 쓴다.

---

## 7. 남은 조치

- [ ] **API 키 교체** — `main.py`는 고쳤으나, 이번 실행 이전의 로그에는 키가 평문으로 남아 있다.
- [ ] `SurveyBench/ref_bench/`를 이용한 정량 평가 (citation recall 등) 미실시.
- [ ] README의 데이터셋 링크가 옛 org(`U4R/`)를 가리킨다. 실제로는 `InternScience/SurveyForge_database`이며,
      README에 설명이 없는 `Final_outline.zip` / `Final_outline_First.zip` 2개가 필수다.
- [ ] outline 코퍼스가 survey DB id를 전부 덮지 않는다 (`Final_outline` 90.7%, `Final_outline_First` 76.4%).
      현재는 `filter_by_outline()`이 누락분을 걸러내므로 안전하나, 검색 결과가 전부 누락되는
      주제에서는 `RuntimeError`가 난다.
