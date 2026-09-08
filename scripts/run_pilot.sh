#!/usr/bin/env bash
# 파일럿 1편: 크레딧 스냅샷 → run_demo → 크레딧 스냅샷 → 산출물 요약.
#   scripts/run_pilot.sh "<topic title from kisti_data/data/topics.kisti.jsonl>" [slug]
# 로그: eval_out/pilot_<slug>.log, 크레딧: eval_out/credits.log (check_credits.py 기본)
# 실행 조건(.env): SURVEYFORGE_DB_DIR · TEMPERATURE · MAX_TOKENS 등은 .env 가 정한다 — 여기서 덮지 않는다.
set -euo pipefail
TOPIC=${1:?topic}
SLUG=${2:-$(echo "$TOPIC" | tr -cs 'A-Za-z0-9' '-' | tr 'A-Z' 'a-z' | sed 's/^-//;s/-$//' | cut -c1-40)}
SF=/data2/chanjoong/survey-agent/SurveyForge
PY=$SF/.venv/bin/python
LOG=$SF/eval_out/pilot_$SLUG.log
mkdir -p "$SF/eval_out"
{
  echo "[pilot] topic=$TOPIC slug=$SLUG start=$(date -Is)"
  grep -E '^SURVEYFORGE_(DB_DIR|MODEL|PROVIDER|TEMPERATURE|MAX_TOKENS|RETRY_TRUNCATED|PAPER_)' "$SF/.env" | sed 's|^|[pilot/env] |'
  "$PY" "$SF/scripts/check_credits.py" --label "before-$SLUG"
  cd "$SF/code"
  t0=$(date +%s)
  "$PY" run_demo.py --topic "$TOPIC"
  rc=$?
  echo "[pilot] run_demo exit=$rc elapsed=$(( $(date +%s) - t0 ))s"
  "$PY" "$SF/scripts/check_credits.py" --label "after-$SLUG"
  OUT=$(ls -d "$SF/code/output/res/"*"__$(grep '^SURVEYFORGE_DB_DIR=' "$SF/.env" | cut -d= -f2)/$TOPIC/exp_"* 2>/dev/null | tail -1 || true)
  if [ -n "$OUT" ]; then
    echo "[pilot] output=$OUT"
    cat "$OUT/cutoff_report.log" 2>/dev/null | sed 's|^|[pilot/cutoff] |'
    [ -f "$OUT/run_manifest.json" ] && "$PY" -c "
import json,sys; m=json.load(open('$OUT/run_manifest.json'))
print('[pilot/manifest] refs', m['refs'], 'doi', m['refs_doi'], '| llm', json.dumps(m['llm_stats']), '| temp', m['temperature'], 'max_tokens', m['max_tokens'])"
    [ -f "$OUT/refined_survey.txt" ] && echo "[pilot] refined words: $(wc -w < "$OUT/refined_survey.txt")"
  fi
  echo "[pilot] end=$(date -Is)"
  echo PILOT_DONE
} 2>&1 | tee "$LOG"
