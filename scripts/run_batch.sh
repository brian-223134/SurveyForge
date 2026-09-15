#!/usr/bin/env bash
# 여러 topic 을 순서대로 run_pilot.sh 로 생성한다. 편마다 시작 전에 OpenRouter 키 잔여 크레딧을 확인해
# SURVEYFORGE_MIN_CREDIT(기본 $0.55, 편당 실측 $0.40 + 여유) 미만이면 멈춘다 -- 한도에 걸려 중간에 죽는
# 실행은 비용만 쓰고 산출물이 없다. 한 편이 실패해도 멈춘다(원인을 보고 이어서 돌린다).
#   scripts/run_batch.sh <slug> [<slug> ...]      # 로그: eval_out/batch_<시각>.log + 편별 pilot_<slug>.log
set -uo pipefail
SF=/data2/chanjoong/survey-agent/SurveyForge
PY=$SF/.venv/bin/python
MIN=${SURVEYFORGE_MIN_CREDIT:-0.55}
LOG=$SF/eval_out/batch_$(date +%Y%m%d_%H%M%S).log
mkdir -p "$SF/eval_out"
remaining() { "$PY" "$SF/scripts/check_credits.py" --label "batch-check" | grep 'key(' | sed -E 's/.*remaining=\$([0-9.]+).*/\1/'; }
{
  echo "[batch] topics=$* min_credit=$MIN start=$(date -Is)"
  for SLUG in "$@"; do
    REM=$(remaining)
    echo "[batch] $SLUG: key remaining \$$REM (min \$$MIN) at $(date -Is)"
    if [ -z "$REM" ] || [ "$(echo "$REM < $MIN" | bc -l)" = 1 ]; then
      echo "[batch] STOP: 잔여 크레딧 \$$REM < \$$MIN -- $SLUG 부터 미실행"; break
    fi
    t0=$(date +%s)
    if "$SF/scripts/run_pilot.sh" "$SLUG" > /dev/null 2>&1; then
      echo "[batch] $SLUG DONE elapsed=$(( $(date +%s) - t0 ))s  $(grep -E '^\[pilot/policy\]|^\[pilot\] refined' "$SF/eval_out/pilot_$SLUG.log" | tr '\n' ' ' | cut -c1-300)"
    else
      echo "[batch] $SLUG FAILED elapsed=$(( $(date +%s) - t0 ))s -- 배치 중단 (로그 eval_out/pilot_$SLUG.log)"; break
    fi
  done
  echo "[batch] key remaining \$$(remaining) end=$(date -Is)"
  echo BATCH_DONE
} 2>&1 | tee "$LOG"
