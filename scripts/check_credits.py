"""OpenRouter 크레딧 사용량 스냅샷 스크립트.

    python scripts/check_credits.py [--label before-run] [--log eval_out/credits.log]

두 줄을 출력한다:
- account: 계정 전체의 구매/사용/잔여 크레딧 (USD)
- key:     이 키 자체의 한도·사용량(오늘 포함)·잔여 — 키 단위 한도가 걸려
           있을 때 실제 제약이 되는 값

파이프라인 실행 전후로 한 번씩 돌려 차이로 실 사용액을 측정한다. 실패한 실행에도
비용은 발생하므로 (surveyforge-llm-plan) 실행이 죽었을 때도 after 스냅샷을 찍을 것.
OpenRouter가 서버에서 집계한 실측값이라, run 로그의 토큰 수 기반 추정과 달리
provider별 단가 차이·재시도 비용까지 전부 포함된다.

키는 OPENROUTER_API_KEY 환경변수에서 읽고, 없으면 저장소 루트의 .env 를
직접 파싱한다 (source 불필요).

참고: ../SurveyX/scripts/check_credits.py (원류는 ../LLMxMapReduce-v2 의 동명 스크립트)
"""

import argparse
import datetime
import json
import os
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_key_from_dotenv(dotenv_path: Path) -> str | None:
    """`.env`에서 OPENROUTER_API_KEY 값을 읽는다. `export KEY=val`, 따옴표 허용."""
    if not dotenv_path.exists():
        return None
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export "):]
        if line.startswith("OPENROUTER_API_KEY="):
            value = line.split("=", 1)[1].strip().strip("'\"")
            return value or None
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Snapshot OpenRouter credit usage (account + key)."
    )
    parser.add_argument("--label", default="", help="스냅샷에 함께 찍을 태그")
    # eval_out/ 은 gitignore 대상이라 실행 기록이 저장소를 더럽히지 않는다.
    parser.add_argument("--log", default="eval_out/credits.log",
                        help="출력을 덧붙여 기록할 파일 경로 ('' 이면 기록 안 함)")
    args = parser.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY") or load_key_from_dotenv(
        REPO_ROOT / ".env"
    )
    if not key:
        sys.exit("OPENROUTER_API_KEY not set and no key found in .env")

    def get(url):
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["data"]

    acct = get("https://openrouter.ai/api/v1/credits")
    keyinfo = get("https://openrouter.ai/api/v1/key")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    label = f" [{args.label}]" if args.label else ""

    total, used = acct["total_credits"], acct["total_usage"]
    lines = [
        f"{now}{label}  account: purchased=${total:.4f}  used=${used:.4f}  "
        f"remaining=${total - used:.4f}"
    ]

    limit = keyinfo.get("limit")
    k_used = keyinfo.get("usage", 0.0)
    k_daily = keyinfo.get("usage_daily", 0.0)
    k_label = keyinfo.get("label", "?")
    if limit is None:
        lines.append(
            f"{now}{label}  key({k_label}): limit=none  used=${k_used:.4f}  "
            f"today=${k_daily:.4f}"
        )
    else:
        remaining = keyinfo.get("limit_remaining", limit - k_used)
        lines.append(
            f"{now}{label}  key({k_label}): limit=${limit:.2f}  used=${k_used:.4f}  "
            f"today=${k_daily:.4f}  remaining=${remaining:.4f}"
        )

    output = "\n".join(lines)
    print(output)

    if args.log:
        log_path = REPO_ROOT / args.log if not Path(args.log).is_absolute() \
            else Path(args.log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fw:
            fw.write(output + "\n")


if __name__ == "__main__":
    main()
