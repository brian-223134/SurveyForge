"""harvest_arxiv.py가 만든 레코드에 citation_count를 채운다.

기존 DB는 589,123편 전부가 이 필드를 갖고 있다 (0인 것 121,654편, 최대 175,503).
비워 두면 안 되는 이유는 스키마가 아니라 랭킹이다 — `sort_by_citation_period`가
시간창 **안에서** 이 값으로 정렬하므로, 신규 논문이 전부 0이면 2024-25 창에서
기존 논문(실제 피인용수 보유)에 항상 밀린다. 2026 창은 신규뿐이라 영향이 없지만
경계 창이 오염된다.

Semantic Scholar `POST /graph/v1/paper/batch`를 쓴다. id 500개씩 보내고 응답은
**입력과 같은 순서**로 오며, 모르는 논문 자리에는 null이 온다 (자리가 밀리지 않는다).

API 키는 .env의 SEMANTIC_SCHOLAR_API_KEY에서 읽는다. argv로 넘기지 않는다 —
`ps`로 새어 나간다 (main.py:139-141이 세운 규칙과 같다).

조회 결과는 그때그때 <out-dir>/_citations.jsonl에 적어 두므로 중단해도 이어서 받는다.

사용법:
    python scripts/fetch_citations.py \
        --in  $SURVEYFORGE_DATA/database_2026-08/arxiv_paper_db_new.json \
        --out $SURVEYFORGE_DATA/database_2026-08/arxiv_paper_db_new_with_cc.json
"""

import argparse
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, '.env'))

S2_BATCH = 'https://api.semanticscholar.org/graph/v1/paper/batch'
# 문서상 한 요청에 500개가 상한이다.
BATCH = 500


def base_id(vid):
    """'2410.12341v4' -> '2410.12341'. S2는 버전 접미사를 받지 않는다."""
    return vid.split('v')[0]


def load_cache(path):
    cache = {}
    if not os.path.exists(path):
        return cache
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                cache[rec['id']] = rec['citation_count']
            except (json.JSONDecodeError, KeyError):
                continue
    return cache


def fetch_batch(ids, session, key, max_try=6):
    """{base_id: citationCount}. 실패한 배치는 예외를 올린다."""
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['x-api-key'] = key
    payload = {'ids': [f'ARXIV:{i}' for i in ids]}
    last = None
    for attempt in range(max_try):
        try:
            r = session.post(S2_BATCH, params={'fields': 'citationCount'},
                             headers=headers, json=payload, timeout=120)
            if r.status_code == 429:
                wait = int(r.headers.get('Retry-After', 5)) + 2
                print(f'  429 rate limited, {wait}s 대기', flush=True)
                time.sleep(wait)
                continue
            if r.status_code != 200:
                last = f'HTTP {r.status_code}: {r.text[:200]}'
            else:
                data = r.json()
                if len(data) != len(ids):
                    # 순서 정렬이 깨지면 엉뚱한 논문에 피인용수가 붙는다. 조용히
                    # 넘기지 않는다.
                    raise RuntimeError(
                        f'응답 길이 불일치: 요청 {len(ids)} / 응답 {len(data)}')
                return {pid: (d or {}).get('citationCount') or 0
                        for pid, d in zip(ids, data)}
        except requests.RequestException as e:
            last = repr(e)
        wait = min(2 ** attempt, 60)
        print(f'  요청 실패({last}), {wait}s 후 재시도', flush=True)
        time.sleep(wait)
    raise RuntimeError(f'S2 요청 {max_try}회 실패: {last}')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--in', dest='src', required=True, help='harvest 결과 json')
    ap.add_argument('--out', dest='dst', required=True, help='citation_count를 채운 json')
    ap.add_argument('--cache', default='', help='기본값: <out과 같은 디렉터리>/_citations.jsonl')
    # 키가 있어도 batch 엔드포인트는 1 RPS보다 빡빡하다 — 1.1초로는 429가 났다.
    # 429마다 Retry-After 7초를 물기 때문에 처음부터 여유를 두는 쪽이 빠르다.
    ap.add_argument('--delay', type=float, default=2.0, help='배치 사이 대기 초')
    ap.add_argument('--limit', type=int, default=0, help='배치 수 상한 (스모크용)')
    args = ap.parse_args()

    key = os.environ.get('SEMANTIC_SCHOLAR_API_KEY', '')
    if not key:
        print('경고: SEMANTIC_SCHOLAR_API_KEY가 없다. 공용 풀은 레이트리밋이 훨씬 빡빡하다.',
              file=sys.stderr)

    with open(args.src) as f:
        table = json.load(f)['cs_paper_info']
    records = list(table.values())
    print(f'레코드 {len(records):,}편')

    cache_path = args.cache or os.path.join(os.path.dirname(os.path.abspath(args.dst)),
                                            '_citations.jsonl')
    cache = load_cache(cache_path)
    if cache:
        print(f'캐시 {len(cache):,}건 발견, 이어서 조회')

    want = sorted({base_id(r['id']) for r in records} - set(cache))
    print(f'조회 대상 {len(want):,}건 ({(len(want) + BATCH - 1) // BATCH} 배치)')

    session = requests.Session()
    with open(cache_path, 'a') as cf:
        for n, start in enumerate(range(0, len(want), BATCH), 1):
            if args.limit and n > args.limit:
                print(f'--limit {args.limit} 도달, 중단')
                break
            chunk = want[start:start + BATCH]
            got = fetch_batch(chunk, session, key)
            for pid, cc in got.items():
                cache[pid] = cc
                cf.write(json.dumps({'id': pid, 'citation_count': cc}) + '\n')
            cf.flush()
            found = sum(1 for v in got.values() if v)
            print(f'  배치 {n}: {len(chunk)}건 조회, 피인용>0 {found}건 '
                  f'(누적 {len(cache):,})', flush=True)
            time.sleep(args.delay)

    missing = 0
    for r in records:
        cc = cache.get(base_id(r['id']))
        if cc is None:
            missing += 1
            cc = 0
        r['citation_count'] = cc

    with open(args.dst, 'w') as f:
        json.dump({'cs_paper_info': {str(i): r for i, r in enumerate(records)}},
                  f, ensure_ascii=False)

    nonzero = sum(1 for r in records if r['citation_count'])
    print(f'\n{args.dst} 작성 완료: {len(records):,}편')
    print(f'  피인용수 > 0 : {nonzero:,}편 ({100 * nonzero / len(records):.1f}%)')
    print(f'  조회 실패로 0 처리: {missing:,}편')
    if records:
        print(f'  최대 피인용수: {max(r["citation_count"] for r in records):,}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
