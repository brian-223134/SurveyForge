#!/usr/bin/env bash
# 스냅샷 증분 전 과정을 순서대로 돌린다. 어느 단계든 실패하면 즉시 멈춘다.
#
#   1. harvest_arxiv.py     OAI-PMH 수집        (~2시간, 네트워크만)
#   2. fetch_citations.py   citation_count      (~20분, 네트워크만)
#   3. append_snapshot.py   임베딩 + append     (~90분, GPU)
#   4. check_db.py          재임베딩 검증       (~2분, GPU)
#
# 1단계가 이미 돌고 있으면 --wait-pid 로 그 PID가 끝나기를 기다렸다가 2단계로 간다.
# 각 스크립트가 중간 산출물을 남기므로 중단 후 다시 실행하면 이어서 진행된다.
#
# 사용법:
#   scripts/update_snapshot.sh                     # 1단계부터
#   scripts/update_snapshot.sh --wait-pid 805784   # 돌고 있는 harvest를 기다렸다가
#   scripts/update_snapshot.sh --skip-harvest      # 수집은 끝났다고 보고 2단계부터

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA="${SURVEYFORGE_DATA:-/data2/chanjoong/survey-agent/SurveyForge_data}"
PY="$REPO/.venv/bin/python"
BASE="$DATA/database"
OUT="$DATA/database_2026-08"
WAIT_PID=""
SKIP_HARVEST=0

while [ $# -gt 0 ]; do
  case "$1" in
    --wait-pid) WAIT_PID="$2"; shift 2 ;;
    --skip-harvest) SKIP_HARVEST=1; shift ;;
    *) echo "모르는 인자: $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$OUT"
log() { echo -e "\n=== [$(date '+%H:%M:%S')] $* ===" ; }

# GPU는 공유 자원이다. 남의 학습에 얹으면 임베딩이 반토막 난다(68 -> 32편/s).
pick_gpu() {
  nvidia-smi --query-gpu=index,memory.used --format=csv,noheader,nounits \
    | sort -t, -k2 -n | head -1 | cut -d, -f1 | tr -d ' '
}

if [ -n "$WAIT_PID" ]; then
  log "harvest PID $WAIT_PID 대기"
  while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 60; done
  echo "harvest 종료됨"
elif [ "$SKIP_HARVEST" = 0 ]; then
  log "1/4 harvest"
  "$PY" "$REPO/scripts/harvest_arxiv.py" --sets cs --oai-from 2024-09-25 \
    --exclude-db "$BASE/arxiv_paper_db_with_cc.json" --out-dir "$OUT" --delay 3
fi

[ -s "$OUT/arxiv_paper_db_new.json" ] || { echo "수집 결과가 없다: $OUT/arxiv_paper_db_new.json" >&2; exit 1; }

log "2/4 citation_count"
"$PY" "$REPO/scripts/fetch_citations.py" \
  --in "$OUT/arxiv_paper_db_new.json" \
  --out "$OUT/arxiv_paper_db_new_with_cc.json"

GPU="$(pick_gpu)"
log "3/4 append (GPU $GPU)"
CUDA_VISIBLE_DEVICES="$GPU" "$PY" "$REPO/scripts/append_snapshot.py" \
  --base "$BASE" --new "$OUT/arxiv_paper_db_new_with_cc.json" --out "$OUT"

log "4/4 검증 (GPU $GPU)"
CUDA_VISIBLE_DEVICES="$GPU" "$PY" "$REPO/scripts/check_db.py" \
  --db "$OUT" --verify-embeddings 40 --fingerprint

log "완료 — 새 스냅샷: $OUT"
echo "실행할 때:"
echo "  --db_path $OUT"
echo "  SURVEYFORGE_PAPER_ID_CUTOFF / SURVEYFORGE_PAPER_DATE_NEWEST 를 위 출력값 이상으로"
