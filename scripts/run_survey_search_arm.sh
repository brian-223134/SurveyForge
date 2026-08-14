#!/usr/bin/env bash
# survey-search arm — 검색만 갈아끼운 서베이 1편.
#
#   bash scripts/run_survey_search_arm.sh "3D Gaussian Splatting"
#
# 대조군은 이미 있습니다:
#   구 DB   code/output/res/deepseek_deepseek-v4-flash-0731/<T>/exp_1
#   신 DB   code/output/res/deepseek_deepseek-v4-flash-0731__database_2026-08/<T>/exp_1
# 이 arm 은 신 DB 와 **같은 코퍼스·같은 모델·같은 인자**이고 검색 레이어만 다릅니다.
# 인자는 run_demo.py 가 만드는 것과 동일하게 맞췄습니다 (그래야 통제 비교가 성립).
set -u
cd /data2/chanjoong/survey-agent/SurveyForge

set -a; . ./.env; set +a
export CUDA_VISIBLE_DEVICES="${SS_GPU:-6}"
export SURVEYFORGE_DB_DIR=database_2026-08
export SURVEYFORGE_PAPER_ID_CUTOFF=2608
export SURVEYFORGE_PAPER_DATE_NEWEST=2026-08-31

T="${1:-Retrieval-Augmented Generation for Large Language Models}"
OUT="output/res/deepseek_deepseek-v4-flash-0731/survey-search/$T/exp_1"

if [ -e "code/$OUT/$T.md" ]; then
    echo "!! 이미 있습니다: code/$OUT — 덮어쓰지 않고 멈춥니다"
    exit 1
fi

# main.py:318 은 os.mkdir 이라 부모를 안 만듭니다. 먼저 파 둡니다.
mkdir -p "code/$OUT"

cd code
echo "=== [$(date '+%F %T')] 생성 시작 — $T ==="
echo "=== 출력: code/$OUT  ·  GPU $CUDA_VISIBLE_DEVICES ==="

../.venv/bin/python main.py \
    --topic "$T" \
    --gpu 0 \
    --debug \
    --saving_path "$OUT" \
    --model "$SURVEYFORGE_MODEL" \
    --section_num 7 \
    --subsection_len 500 \
    --rag_num 100 \
    --rag_max_out 60 \
    --outline_reference_num 1500 \
    --survey_outline_path "$SURVEYFORGE_DATA" \
    --db_path "$SURVEYFORGE_DATA/$SURVEYFORGE_DB_DIR" \
    --embedding_model "$SURVEYFORGE_DATA/gte-large-en-v1.5" \
    --api_url "$SURVEYFORGE_API_URL"

echo "=== [$(date '+%F %T')] 종료 (exit $?) ==="
