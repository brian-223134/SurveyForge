"""두 실행을 나란히 놓고 비교 표를 만든다. DB 증분 전후 회귀 검사용.

SurveyBench coverage 하나만으로는 부족하다. 벤치마크의 기준일이 토픽마다
2023-10 ~ 2024-07이라 **2024-08 이후 인용은 분자에서도 분모에서도 빠진다** —
증분이 가져온 최신 논문은 이 지표에 아예 보이지 않는다. 그래서 세 가지를 같이 낸다.

  coverage  기존 정전(canonical) 문헌을 여전히 잘 집어내는가 (희석 여부)
  최신성    인용 중 스냅샷 컷오프 이후 비율 (증분이 출력까지 닿았는가)
  분량·무결성  같은 조건에서 산출물이 망가지지 않았는가

사용법:
    python scripts/compare_runs.py \
        --topic "Retrieval-Augmented Generation for Large Language Models" \
        --run "구 DB=code/output/res/<slug>/<topic>/exp_1" \
        --run "신 DB=code/output/res/<slug2>/<topic>/exp_1" \
        --out eval_summary.md
"""

import argparse
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH = os.path.join(REPO, 'SurveyBench')
# 증분 스냅샷의 컷오프. 이 날짜 이후 인용을 '신규'로 센다.
BASE_CUTOFF = '2024-09-25'


def load_refs(run_dir, topic):
    p = os.path.join(run_dir, f'{topic}.json')
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f).get('reference') or {}


def paper_dates(db_path):
    with open(db_path) as f:
        table = json.load(f)['cs_paper_info']
    return {v['id']: v.get('date', '') for v in table.values()}


def survey_stats(run_dir, topic):
    """분량과 구조. .tex 가 있으면 그쪽을 센다 (md 헤딩은 부풀려진 전례가 있다)."""
    tex = os.path.join(run_dir, f'{topic}.tex')
    md = os.path.join(run_dir, f'{topic}.md')
    if os.path.exists(tex):
        body = open(tex, encoding='utf-8').read().split(r'\begin{document}')[-1]
        body = re.split(r'\\begin\{thebibliography\}|\\section\*?\{References\}', body)[0]
        secs = len(re.findall(r'^\\section\{', body, re.M))
        subs = len(re.findall(r'^\\subsection\{', body, re.M))
        words = len(re.findall(r"[A-Za-z][A-Za-z'-]*",
                               re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?', ' ', body)))
        src = '.tex'
    elif os.path.exists(md):
        t = open(md, encoding='utf-8').read().split('## References')[0]
        secs = len(re.findall(r'^## ', t, re.M))
        subs = len(re.findall(r'^### ', t, re.M))
        words = len(t.split())
        src = '.md'
    else:
        return None
    return {'words': words, 'sections': secs, 'subsections': subs, 'src': src}


def integrity(run_dir):
    """생성이 온전했는지. 마커는 src/model.py 가 남긴다."""
    marks = {'[TRUNCATED]': 0, '[EMPTY]': 0, '[GIVE UP]': 0}
    for name in os.listdir(run_dir):
        if not name.endswith('.log'):
            continue
        try:
            text = open(os.path.join(run_dir, name), encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        for m in marks:
            marks[m] += text.count(m)
    return marks


def run_coverage(topic, out_root, exp=1):
    topics_file = os.path.join(out_root, '_topic.txt')
    os.makedirs(out_root, exist_ok=True)
    with open(topics_file, 'w') as f:
        f.write(topic + '\n')
    r = subprocess.run([sys.executable, 'test.py',
                        '--generated_surveys_ref_dir', os.path.abspath(out_root),
                        '--topic_list_path', os.path.abspath(topics_file),
                        '--num_generations', str(exp)],
                       cwd=BENCH, capture_output=True, text=True)
    if r.returncode != 0:
        return None, (r.stdout + r.stderr)[-400:]
    m = re.search(r'citation coverage:\s*([\d.]+)', r.stdout)
    return (float(m.group(1)) if m else None), r.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--topic', required=True)
    ap.add_argument('--run', action='append', required=True,
                    help='"라벨=경로" 형식, 여러 번 줄 수 있다')
    ap.add_argument('--db', default=os.path.join(
        os.environ.get('SURVEYFORGE_DATA', '/data2/chanjoong/survey-agent/SurveyForge_data'),
        'database_2026-08', 'arxiv_paper_db_with_cc.json'),
        help='인용 날짜 조회용 DB (증분본이어야 최신 논문 날짜를 안다)')
    ap.add_argument('--out', default='eval_summary.md')
    args = ap.parse_args()

    print('논문 날짜 로딩...', flush=True)
    dates = paper_dates(args.db)

    rows = []
    for spec in args.run:
        label, _, path = spec.partition('=')
        if not os.path.isdir(path):
            print(f'!! {label}: 경로 없음 {path}', file=sys.stderr)
            continue
        refs = load_refs(path, args.topic)
        if refs is None:
            print(f'!! {label}: <topic>.json 없음 (생성이 끝나지 않았을 수 있다)', file=sys.stderr)
            continue

        ids = list(dict.fromkeys(refs.values()))
        known = [dates[i] for i in ids if i in dates]
        recent = sum(1 for d in known if d > BASE_CUTOFF)

        out_root = os.path.join(BENCH, 'eval_runs', re.sub(r'\W+', '_', label))
        subprocess.run([sys.executable, os.path.join(REPO, 'scripts', 'to_surveybench_ref.py'),
                        '--survey-json', os.path.join(path, f'{args.topic}.json'),
                        '--topic', args.topic, '--out-root', out_root],
                       check=True, capture_output=True)
        cov, raw = run_coverage(args.topic, out_root)

        rows.append({'label': label, 'path': path, 'refs': len(ids),
                     'dated': len(known), 'recent': recent,
                     'recent_pct': 100 * recent / len(known) if known else 0,
                     'newest': max(known) if known else '-',
                     'coverage': cov, 'raw': raw,
                     'stats': survey_stats(path, args.topic),
                     'integrity': integrity(path)})

    lines = [f'# 회귀 검사 — {args.topic}', '',
             f'인용 날짜 기준 DB: `{os.path.basename(os.path.dirname(args.db))}`  '
             f'/ 최신 판정 기준: {BASE_CUTOFF} 이후', '',
             '| 실행 | 참고문헌 | coverage | 최신 인용 | 최신 비율 | 최신 인용일 | 단어 | 섹션/서브 | 무결성 |',
             '|---|---:|---:|---:|---:|---|---:|---:|---|']
    for r in rows:
        s = r['stats'] or {}
        ig = r['integrity']
        ok = 'OK' if not any(ig.values()) else ', '.join(f'{k}{v}' for k, v in ig.items() if v)
        cov = f"{r['coverage']:.3f}" if r['coverage'] is not None else '실패'
        lines.append(
            f"| {r['label']} | {r['refs']} | {cov} | {r['recent']}/{r['dated']} | "
            f"{r['recent_pct']:.1f}% | {r['newest']} | {s.get('words', '-')} | "
            f"{s.get('sections', '-')}/{s.get('subsections', '-')} | {ok} |")

    if len(rows) == 2:
        a, b = rows
        if a['coverage'] is not None and b['coverage'] is not None:
            d = b['coverage'] - a['coverage']
            lines += ['', f"**coverage 변화: {a['coverage']:.3f} -> {b['coverage']:.3f} "
                          f"({d:+.3f})** — 음수면 후보가 늘면서 정전 문헌이 밀려난 것"
                          f"(희석), 양수면 개선.",
                      '', f"**최신성: {a['recent_pct']:.1f}% -> {b['recent_pct']:.1f}%** — "
                          f"벤치마크는 이 축을 보지 못하므로 coverage와 별도로 읽을 것."]

    lines += ['', '---', '', '원본 출력:', '']
    for r in rows:
        lines += [f"- **{r['label']}** `{r['path']}`", f"  - {r['raw']}"]

    text = '\n'.join(lines) + '\n'
    with open(args.out, 'w') as f:
        f.write(text)
    print('\n' + text)
    print(f'-> {args.out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
