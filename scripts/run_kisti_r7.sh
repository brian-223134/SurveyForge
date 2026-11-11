#!/usr/bin/env bash
# kisti-2608-r7 파일럿(CSUR 2026 게재 GT) 한 편: 점검 → run_demo(생성) → score_run(채점).
#
#   scripts/run_kisti_r7.sh <slug> <gpu> [--dry-run]
#
# - kisti_data docs/asg/AGENT-HANDOFF.md 「파일럿: CSUR 2026 게재 GT」 절차를 그대로 감싼다. run_pilot.sh 는
#   check_credits.py 가 OpenRouter 잔액을 조회하다 실패하면 생성 전에 멈추므로 쓰지 않는다.
# - 백본 qwen-plus-2025-12-01 @ DashScope intl. 응답에 비용이 없으니 단가(in $0.4 / out $1.2 per 1M)를 env 로
#   넘겨 run_manifest.json 의 llm_stats(청구 토큰·cost_usd)에 남긴다.
# - .env 는 고치지 않는다. 셸 export 가 .env 보다 우선한다(load_dotenv 는 덮지 않음).
# - 키는 AutoSurvey/.env 의 ALIBABA_CLOUD_API_KEY 를 env 로만 넘긴다(명령줄·로그에 남기지 않음).
# - 같은 산출물(exp_1)이 있으면 멈춘다. run_demo 는 기존 디렉터리를 조용히 건너뛰고 성공으로 보고하기 때문.
# - 계정 전체 120 RPM · 1M TPM 이라 한 번에 한 topic 씩 돌린다.
# - 생성은 setsid nohup 으로 분리한다. 로그: code/output/res/<model>__<db>/<title>/run_kisti_r7.log
set -euo pipefail

VIEW=kisti-2608-r7
K=/data2/chanjoong/kisti_data
A=/data2/chanjoong/survey-agent
SF=$A/SurveyForge
PY=$SF/.venv/bin/python
G=$K/candidates/csur2026_gt_refs.jsonl
T=$K/candidates/csur2026_topics.jsonl
POL=$A/AutoSurvey/data/topic_policy.$VIEW.jsonl
DATES=$K/data/views/$VIEW/paper_dates.json
DB_DIR=database_kisti-$VIEW
DB=$A/SurveyForge_data/$DB_DIR
MODEL=qwen-plus-2025-12-01
API_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
# 2026-11-11 판 (AGENT-HANDOFF). 네 agent 가 같은 파일로 돌려야 비교할 수 있다.
SHA_T=d3acc763d15c4be897b52c23702ec4e90e9ec925ec08d3dcc8cc990bc6ea021f
SHA_G=dae62edc46d1979c70931f6322f1f50676d97b6d664472dc43e9ea5a7ff56acc
SHA_POL=bae2d5a88102816ca1e7fd36445a54171d9d6b95a754b3c9b054515b3b5b826e

die() { echo "✗ $*" >&2; exit 1; }

# ---------- 내부 단계: setsid 로 분리된 쪽에서 돈다 ----------
if [[ "${1:-}" == "--_inner" ]]; then
  shift; SLUG=$1; EXP=$2
  echo "[r7] $(date -u +%FT%TZ) start slug=$SLUG gpu=$CUDA_VISIBLE_DEVICES pid=$$"
  t0=$(date +%s)
  rc=0; (cd "$SF/code" && "$PY" -u run_demo.py) || rc=$?
  echo "[r7] $(date -u +%FT%TZ) run_demo exit=$rc elapsed=$(( $(date +%s) - t0 ))s"
  if [[ -f "$EXP/run_manifest.json" ]]; then
    "$PY" - "$EXP/run_manifest.json" <<'EOF'
import json, sys
m = json.load(open(sys.argv[1])); s = m['llm_stats']; p = m.get('retrieval_policy') or {}
print(f"[r7/usage] in={s['prompt_tokens']:,} out={s['completion_tokens']:,} cached={s['cached_tokens']:,} "
      f"reasoning={s['reasoning_tokens']:,} max_prompt={s['max_prompt_tokens']:,} over_256k={s['calls_over_256k']} "
      f"cost=${s['cost_usd']:.4f} ({s['cost_source']})")
print(f"[r7/llm] completions={s['completions']} truncation_retries={s['truncation_retries']} "
      f"truncated_accepted={s['truncated_accepted']} error_retries={s['error_retries']} "
      f"data_inspection_failed={s['data_inspection_failed']}")
print(f"[r7/policy] cutoff={p.get('retrieval_cutoff_at')} allowed={p.get('allowed')} "
      f"violations={p.get('reference_violations')} refs={m['refs']} (doi {m['refs_doi']})")
EOF
  elif [[ -f "$EXP/llm_usage.partial.json" ]]; then
    echo "[r7] ⚠ 실패 — $EXP/llm_usage.partial.json"; cat "$EXP/llm_usage.partial.json"
  fi
  [[ -f "$EXP/refined_survey.txt" ]] && echo "[r7] refined words: $(wc -w < "$EXP/refined_survey.txt")"
  if [[ $rc == 0 ]]; then
    (cd "$SF" && KISTI_GT_REFS_FILE=$G KISTI_TOPICS_FILE=$T "$PY" scripts/score_run.py --run "$EXP" --topic_id "$SLUG") \
      || echo "[r7] ⚠ score_run 실패"
  fi
  echo "[r7] $(date -u +%FT%TZ) ALL DONE rc=$rc"
  exit 0
fi

# ---------- 외부 단계: 점검 후 띄운다 ----------
SLUG=${1:?usage: $0 <slug> <gpu> [--dry-run]}
GPU=${2:?usage: $0 <slug> <gpu> [--dry-run]}
DRY=${3:-}

# 입력 판: sha256 이 AGENT-HANDOFF 값과 같아야 한다
for pair in "$T:$SHA_T" "$G:$SHA_G" "$POL:$SHA_POL"; do
  f=${pair%:*}; want=${pair##*:}
  [[ -f "$f" ]] || die "$f 없음"
  got=$(sha256sum "$f" | cut -d' ' -f1)
  [[ "$got" == "$want" ]] || die "$f sha256 $got ≠ $want (판이 바뀌었으면 이 스크립트의 SHA_* 를 갱신)"
done
[[ -f "$DATES" ]] || die "$DATES 없음"

# topic: $T 의 title · pick, 정책 행의 topic 과 같아야 한다
read -r PICK TITLE < <("$PY" - "$T" "$POL" "$SLUG" <<'EOF'
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
pol = {r['topic_id']: r for r in (json.loads(l) for l in open(sys.argv[2]) if l.strip().startswith('{'))}
r = [x for x in rows if x['slug'] == sys.argv[3]]
if not r: print('MISSING -'); sys.exit()
p = pol.get(sys.argv[3])
if not p or p['topic'] != r[0]['title']: print('MISMATCH -'); sys.exit()
print((r[0].get('pick') or '-') + ' ' + r[0]['title'])
EOF
)
[[ "$PICK" == MISSING ]] && die "slug '$SLUG' 가 $T 에 없습니다"
[[ "$PICK" == MISMATCH ]] && die "'$SLUG' 의 \$T title 과 정책 topic 이 다릅니다"
[[ "$PICK" == pilot ]] || echo "⚠ '$SLUG' 는 pick=$PICK (파일럿 아님)"

# 판 짝: 정책 snapshot = view sha = 인덱스 build_manifest 의 view sha
VSHA=$(sha256sum "$K/data/views/$VIEW/papers.parquet" | cut -c1-8)
grep -q "\"topic_id\": \"$SLUG\".*$VSHA" "$POL" || die "정책의 $SLUG 행 snapshot 이 view sha $VSHA 와 다릅니다"
grep -q "\"papers.parquet\": \"$VSHA" "$DB/build_manifest.json" || die "$DB 가 view $VSHA 로 빌드되지 않았습니다"

# TinyDB 는 쓰기 모드로 열린다 — 본인 소유여야 한다
OWNER=$(stat -c %U "$DB/arxiv_paper_db_with_cc.json")
[[ "$OWNER" == "$(whoami)" ]] || die "$DB/arxiv_paper_db_with_cc.json 소유자 $OWNER ≠ $(whoami) — 본인 소유로 복사해 쓰세요"

# GPU: 이미 쓰이고 있으면 멈춘다(FORCE_GPU=1 로 무시)
USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i "$GPU" | tr -d ' ')
if (( USED > 2000 )) && [[ "${FORCE_GPU:-}" != 1 ]]; then
  nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
  die "GPU $GPU 사용 중(${USED} MiB). 빈 GPU 를 고르세요"
fi

# 산출 경로 (run_demo.py: output/res/<model_slug>__<db_slug>/<topic>/exp_N)
TOPIC_DIR="$SF/code/output/res/${MODEL}__${DB_DIR}/$TITLE"
EXP="$TOPIC_DIR/exp_1"
[[ -e "$EXP" ]] && die "$EXP 가 이미 있습니다 — 덮어쓰지 않습니다(run_demo 는 조용히 건너뛴다). 직접 옮겨 두세요"

# 백본 (키는 출력하지 않는다; AutoSurvey/.env 에서 그 변수 하나만 꺼낸다)
KEY=$(set -a; source "$A/AutoSurvey/.env" >/dev/null 2>&1; printf %s "${ALIBABA_CLOUD_API_KEY:-}")
[[ -n "$KEY" ]] || die "AutoSurvey/.env 에 ALIBABA_CLOUD_API_KEY 없음"
export OPENROUTER_API_KEY="$KEY" \
  SURVEYFORGE_MODEL=$MODEL SURVEYFORGE_API_URL=$API_URL \
  SURVEYFORGE_PROVIDER= SURVEYFORGE_QUANTIZATIONS= \
  SURVEYFORGE_REASONING_EFFORT= SURVEYFORGE_REASONING_EXCLUDE= \
  SURVEYFORGE_TEMPERATURE=0.6 SURVEYFORGE_MAX_TOKENS=8192 SURVEYFORGE_RETRY_TRUNCATED=1 \
  SURVEYFORGE_PRICE_INPUT=0.4 SURVEYFORGE_PRICE_OUTPUT=1.2 \
  SURVEYFORGE_DB_DIR=$DB_DIR SURVEYFORGE_TOPIC_POLICY=$POL SURVEYFORGE_PAPER_DATES=$DATES \
  SURVEYFORGE_TOPIC_ID=$SLUG SURVEYFORGE_EXPS=1 \
  CUDA_VISIBLE_DEVICES=$GPU
unset KEY

echo "view     $VIEW (papers sha $VSHA)  index $DB_DIR"
echo "topic    $SLUG — \"$TITLE\""
echo "gpu      $GPU (${USED} MiB 사용 중)"
echo "model    $MODEL @ $API_URL  temp 0.6 max_tokens 8192 retry_truncated 1"
echo "price    in \$0.4 / out \$1.2 per 1M (토큰으로 계산)"
echo "policy   $POL"
echo "dates    $DATES  (PAPER_ID_CUTOFF=$(grep '^SURVEYFORGE_PAPER_ID_CUTOFF=' "$SF/.env" | cut -d= -f2) .env 그대로)"
echo "out      $EXP"

if [[ "$DRY" == --dry-run ]]; then echo "(dry-run: 띄우지 않음)"; exit 0; fi

mkdir -p "$TOPIC_DIR"
LOG="$TOPIC_DIR/run_kisti_r7.log"
[[ -e "$LOG" ]] && mv "$LOG" "$LOG.$(date +%s)"
setsid nohup "$(readlink -f "$0")" --_inner "$SLUG" "$EXP" > "$LOG" 2>&1 < /dev/null &
PID=$!
sleep 2
echo "launched pid=$PID → tail -f \"$LOG\""
