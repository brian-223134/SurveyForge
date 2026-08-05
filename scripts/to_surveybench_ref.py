"""생성된 서베이의 참고문헌을 SurveyBench가 읽는 ref.json 형식으로 변환한다.

`main.py`는 `<topic>.json` 에 `{"survey": ..., "reference": {"1": "2005.11401v4", ...}}`
를 쓰는데, `SurveyBench/test.py` 는 `<dir>/<topic>/exp_N/ref.json` 에서
`{arxiv_id: {"arxivId": id}}` 형태를 읽는다. 그 사이를 잇는다.

**버전 접미사를 떼지 않는다.** test.py 가 `re.sub(r'v\\d+$', '', paper_id)` 로 직접
떼기 때문에 여기서 미리 떼면 이중 처리일 뿐이고, 원본 id 를 남겨 두는 편이 추적에 낫다.

**출력 디렉터리를 원본 벤치마크와 섞지 말 것.** 저장소에 딸려 온
`SurveyBench/generated_surveys_ref/` 는 저자들의 산출물이라 덮어쓰면 비교 기준이 사라진다.
`--out-root` 로 별도 위치를 준다.

사용법:
    python scripts/to_surveybench_ref.py \
        --survey-json "code/output/res/<slug>/<topic>/exp_1/<topic>.json" \
        --topic "Retrieval-Augmented Generation for Large Language Models" \
        --out-root SurveyBench/eval_runs/olddb --exp 1
"""

import argparse
import json
import os
import re
import sys

ARXIV = re.compile(r'^(?:\d{4}\.\d{4,5}|[a-zA-Z][\w.-]*/\d{7})(?:v\d+)?$')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--survey-json', required=True, help='main.py 가 쓴 <topic>.json')
    ap.add_argument('--topic', required=True)
    ap.add_argument('--out-root', required=True, help='test.py 의 --generated_surveys_ref_dir')
    ap.add_argument('--exp', type=int, default=1)
    args = ap.parse_args()

    with open(args.survey_json) as f:
        data = json.load(f)
    refs = data.get('reference')
    if not refs:
        raise SystemExit(f'{args.survey_json} 에 reference 가 없다 (키: {list(data)})')

    ids, bad = [], []
    for _, aid in sorted(refs.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0):
        (ids if ARXIV.match(aid) else bad).append(aid)
    if bad:
        print(f'경고: arXiv id 로 보이지 않는 항목 {len(bad)}건 제외: {bad[:5]}', file=sys.stderr)

    uniq = list(dict.fromkeys(ids))
    out_dir = os.path.join(args.out_root, args.topic, f'exp_{args.exp}')
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, 'ref.json')
    with open(out, 'w') as f:
        json.dump({i: {'arxivId': i} for i in uniq}, f, indent=1)

    print(f'{out}: 참고문헌 {len(refs)}건 -> 고유 arXiv id {len(uniq)}건'
          + (f' (중복 {len(ids) - len(uniq)}건 병합)' if len(ids) != len(uniq) else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
