#!/usr/bin/env bash
# survey-search arm 후처리 — 생성이 끝나기를 기다렸다가 무결성 검사 · PDF · 회귀 비교까지.
#
# SSH 가 끊겨도 돌게 setsid 로 띄웁니다. 생성 프로세스는 이 스크립트의 자식이 아니므로
# `wait` 가 아니라 `kill -0` 폴링으로 기다립니다.
#
# 사용: SS_PID=<생성 PID> setsid nohup bash scripts/post_survey_search_arm.sh &
set -u
cd /data2/chanjoong/survey-agent/SurveyForge

DATA=/data2/chanjoong/survey-agent/SurveyForge_data
DB="$DATA/database_2026-08/arxiv_paper_db_with_cc.json"
T="Retrieval-Augmented Generation for Large Language Models"
RUN="code/output/res/deepseek_deepseek-v4-flash-0731/survey-search/$T/exp_1"
HUMAN="SurveyBench/human_written_ref/Retrieval-augmented generation for large language models: A survey.json"
SS_PID="${SS_PID:-0}"

say() { echo "=== [$(date '+%F %T')] $*"; }

# ---------------------------------------------------------------- 1. 대기
say "생성(PID $SS_PID) 종료 대기"
while kill -0 "$SS_PID" 2>/dev/null; do sleep 60; done
say "생성 종료 감지"
sleep 5

# ---------------------------------------------------------------- 2. 무결성
say "무결성 검사"
MD="$RUN/$T.md"
if [ ! -s "$MD" ]; then
    say "!! 본문 .md 가 없습니다 — 생성이 실패했습니다. 여기서 멈춥니다"
    ls -la "$RUN" || true
    exit 1
fi
# 본문 단어 수. References 이후를 잘라 RESULT.md 와 같은 기준으로 셉니다.
WORDS=$(sed '/^#\+ *References/,$d' "$MD" | sed 's/\[[0-9, ]*\]//g' | wc -w)
say "본문 $WORDS words / .md $(stat -c%s "$MD") bytes"
say "TRUNCATED $(grep -c 'TRUNCATED' eval_out/survey_search_arm.log) · EMPTY $(grep -c 'EMPTY' eval_out/survey_search_arm.log) · 429 $(grep -c 'code.: 429' eval_out/survey_search_arm.log) · facet fallback $(grep -c 'fallback 사용' eval_out/survey_search_arm.log)"

# ---------------------------------------------------------------- 3. PDF
# **--db 를 반드시 명시합니다.** md_to_tex 의 db_for_run() 은 경로의 `<model>__<db_dir>`
# 접미사로 스냅샷을 되짚는데, 이 arm 의 출력 경로에는 그 접미사가 없어 배포본(2024-09)
# 으로 조용히 폴백합니다. 그러면 최신 논문의 제목·저자가 통째로 빠집니다.
say "PDF 변환"
.venv/bin/python code/tools/md_to_tex.py "$RUN" --compile --db "$DB" \
    && say "PDF 완료: $(ls -la "$RUN/$T.pdf" 2>/dev/null || echo '없음')" \
    || say "!! PDF 변환 실패 (본문은 무사합니다)"

# ---------------------------------------------------------------- 4. 회귀 비교
say "회귀 비교 (구 DB · 신 DB · survey-search · 인간)"
.venv/bin/python scripts/compare_runs.py --topic "$T" \
    --run "구 DB=code/output/res/deepseek_deepseek-v4-flash-0731/$T/exp_1" \
    --run "신 DB=code/output/res/deepseek_deepseek-v4-flash-0731__database_2026-08/$T/exp_1" \
    --run "survey-search=$RUN" \
    --human "$HUMAN" \
    --out eval_out/eval_survey_search_arm.md \
    && say "비교표: eval_out/eval_survey_search_arm.md" \
    || say "!! 비교 실패"

say "후처리 완료"
