#!/usr/bin/env bash
# 파일럿 1편: 크레딧 스냅샷 → run_demo → 크레딧 스냅샷 → 산출물 요약.
#   scripts/run_pilot.sh <topic_id>        # topic_id = 정책 파일의 slug (예 physical-adversarial-attacks)
# 제목은 정책 행의 topic(= kisti_data/data/topics.kisti.jsonl 의 title)에서 푼다. 검색은 그 행의
# retrieval_cutoff_at(GT survey 최초 공개일) 이전 문헌으로 제한된다 (docs/retrieval-policy.md).
# 로그: eval_out/pilot_<slug>.log, 크레딧: eval_out/credits.log (check_credits.py 기본)
# 실행 조건(.env): SURVEYFORGE_DB_DIR · TEMPERATURE · MAX_TOKENS 등은 .env 가 정한다 — 여기서 덮지 않는다.
set -euo pipefail
SLUG=${1:?topic_id (정책 파일의 slug)}
SF=/data2/chanjoong/survey-agent/SurveyForge
PY=$SF/.venv/bin/python
TOPIC=$(cd "$SF/code" && "$PY" -c "import sys; from src.retrieval_policy import topic_title; print(topic_title(sys.argv[1]))" "$SLUG")
export SURVEYFORGE_TOPIC_ID=$SLUG
LOG=$SF/eval_out/pilot_$SLUG.log
mkdir -p "$SF/eval_out"
{
  echo "[pilot] topic_id=$SLUG topic=$TOPIC start=$(date -Is)"
  grep -E '^SURVEYFORGE_(DB_DIR|MODEL|PROVIDER|TEMPERATURE|MAX_TOKENS|RETRY_TRUNCATED|PAPER_|TOPIC_)' "$SF/.env" | sed 's|^|[pilot/env] |'
  "$PY" "$SF/scripts/check_credits.py" --label "before-$SLUG"
  cd "$SF/code"
  t0=$(date +%s)
  "$PY" run_demo.py
  rc=$?
  echo "[pilot] run_demo exit=$rc elapsed=$(( $(date +%s) - t0 ))s"
  "$PY" "$SF/scripts/check_credits.py" --label "after-$SLUG"
  OUT=$(ls -d "$SF/code/output/res/"*"__$(grep '^SURVEYFORGE_DB_DIR=' "$SF/.env" | cut -d= -f2)/$TOPIC/exp_"* 2>/dev/null | tail -1 || true)
  if [ -n "$OUT" ]; then
    echo "[pilot] output=$OUT"
    cat "$OUT/cutoff_report.log" 2>/dev/null | sed 's|^|[pilot/cutoff] |'
    [ -f "$OUT/run_manifest.json" ] && "$PY" -c "
import json,sys; m=json.load(open('$OUT/run_manifest.json')); p=m.get('retrieval_policy') or {}
print('[pilot/manifest] refs', m['refs'], 'doi', m['refs_doi'], '| llm', json.dumps(m['llm_stats']), '| temp', m['temperature'], 'max_tokens', m['max_tokens'])
print('[pilot/policy] topic_id', m.get('topic_id'), 'cutoff', p.get('retrieval_cutoff_at'), 'allowed', p.get('allowed'), '/', p.get('db_records'), 'sha', str(p.get('allowed_fingerprint_sha256'))[:16], 'violations', p.get('reference_violations'), 'view', p.get('view_sha256', '')[:8], p.get('view_created_at'))"
    [ -f "$OUT/refined_survey.txt" ] && echo "[pilot] refined words: $(wc -w < "$OUT/refined_survey.txt")"
  fi
  echo "[pilot] end=$(date -Is)"
  echo PILOT_DONE
} 2>&1 | tee "$LOG"
