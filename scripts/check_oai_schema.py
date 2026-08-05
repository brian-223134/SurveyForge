#!/usr/bin/env python
"""OAI-PMH로 받은 레코드가 기존 DB의 표기 규약과 일치하는지 대조한다.

증분 적재의 전제는 '새 논문이 기존 논문과 구별되지 않는 형태로 들어가는 것'이다.
필드 표기가 어긋나면 에러 없이 코퍼스가 두 층으로 갈라진다.

**이 DB는 이미 두 층이다.** 제목의 문자 치환 여부로 정확히 갈린다 (2026-08-05 실측):

    치환됨 (':' -> ' ')   149,036편   2012-01-01 .. 2024-04-26
    ':' 보존              21,791편    2024-04-23 .. 2024-09-25
    양쪽 모두 해당        0편

경계 2024-04-26은 AutoSurvey 배포 DB의 컷오프와 같다. 즉 SurveyForge DB는
AutoSurvey 계열 베이스 위에 저자들이 2024-09까지 직접 증분한 것이고, **그 증분에서는
치환을 걸지 않았다.** 따라서 신규 논문이 따라야 할 것은 최신 층, 곧 raw arXiv 표기다.
AutoSurvey 쪽 harvest_arxiv.py의 TITLE_TRANS를 그대로 가져오면 안 된다.

--since로 대조 대상을 최신 층으로 좁혀 그 층이 실제로 raw OAI와 같은지 확인한다.

공백 비교에 대하여: title/abs의 하드 줄바꿈은 정규화해서 비교한다. gte-large-en-v1.5가
공백 차이에 **완전히** 불변임을 실측했기 때문이다 (40편 표본, 저장 텍스트 vs 공백
정규화본의 cos = 1.000000, 최솟값도 1.000000). 반면 구분자를 끼워 넣으면 0.990까지
떨어진다 — 인덱스는 title과 abs를 구분자 없이 이어 붙인 것이므로 그 규약이 진짜 불변식이다.

사용법:
    python scripts/check_oai_schema.py --n 30 --since 2024-04-27
"""
import argparse
import json
import os
import random
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

OAI_URL = 'https://oaipmh.arxiv.org/oai'
UA = 'surveyforge-harvester/0.1 (+https://github.com/brian-223134/SurveyForge)'

NS_RAW = {'oai': 'http://www.openarchives.org/OAI/2.0/',
          'r': 'http://arxiv.org/OAI/arXivRaw/'}
NS_ARX = {'oai': 'http://www.openarchives.org/OAI/2.0/',
          'a': 'http://arxiv.org/OAI/arXiv/'}

MONTHS = {m: i for i, m in enumerate(
    ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}

# FAISS 인덱스로 들어가는 필드. 여기가 어긋나면 신·구 논문이 다른 텍스트 분포로
# 임베딩돼 검색이 조용히 망가진다. 나머지는 표시용 메타데이터다.
EMBEDDED = ('title', 'abs')

DEFAULT_DATA = os.environ.get('SURVEYFORGE_DATA',
                              '/data2/chanjoong/survey-agent/SurveyForge_data')


def fetch(params, tries=6):
    url = f'{OAI_URL}?{urllib.parse.urlencode(params)}'
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read().decode('utf-8')
        except Exception as e:
            retry = getattr(e, 'headers', None) and e.headers.get('Retry-After')
            wait = int(retry) if retry else min(60, 5 * (attempt + 1))
            print(f'    재시도 {attempt + 1}/{tries} ({e}) — {wait}s', file=sys.stderr)
            time.sleep(wait)
    raise SystemExit('OAI 요청 실패')


def parse_version_date(text):
    """'Fri, 14 Aug 2020 20:46:38 GMT' -> '2020-08-14'"""
    m = re.search(r'(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})', text or '')
    if not m:
        return ''
    day, mon, year = int(m.group(1)), MONTHS.get(m.group(2), 0), m.group(3)
    return f'{year}-{mon:02d}-{day:02d}'


def from_oai(base_id):
    """기존 DB와 같은 표기로 레코드를 만든다.

    abs와 title/authors의 출처가 다르므로 두 형식을 모두 받는다.
    abs는 arXivRaw(TeX escape 보존), title/authors는 arXiv(유니코드 변환).
    """
    raw = ET.fromstring(fetch({'verb': 'GetRecord', 'metadataPrefix': 'arXivRaw',
                               'identifier': f'oai:arXiv.org:{base_id}'}))
    meta = raw.find('.//r:arXivRaw', NS_RAW)
    if meta is None:
        return None

    versions = meta.findall('r:version', NS_RAW)
    vnums = [int(v.get('version', 'v1').lstrip('v')) for v in versions] or [1]
    latest = max(vnums)
    # date는 **id에 적힌 버전의 날짜**다. v1이 아니다 (2026-08-05 실측):
    #   2407.16160v2  DB 2024-08-21 = v2   (v1은 2024-07-23)
    #   2405.09713v2  DB 2024-05-17 = v2   (v1은 2024-05-15)
    #   2407.00890v1  DB 2024-07-01 = v1
    # AutoSurvey는 반대로 v1을 쓴다. 그쪽 harvest_arxiv.py를 그대로 옮기면 개정본의
    # 날짜가 최대 수년 어긋나고, TRE의 시간창 배정이 조용히 틀어진다.
    vlatest = next((v for v in versions if v.get('version') == f'v{latest}'), None)

    def rtext(tag):
        el = meta.find(f'r:{tag}', NS_RAW)
        return (el.text or '').strip() if el is not None else ''

    arx = ET.fromstring(fetch({'verb': 'GetRecord', 'metadataPrefix': 'arXiv',
                               'identifier': f'oai:arXiv.org:{base_id}'}))
    ameta = arx.find('.//a:arXiv', NS_ARX)
    authors, atitle = [], ''
    if ameta is not None:
        for a in ameta.findall('a:authors/a:author', NS_ARX):
            key = a.find('a:keyname', NS_ARX)
            fore = a.find('a:forenames', NS_ARX)
            name = ' '.join(x.text.strip() for x in (fore, key)
                            if x is not None and x.text)
            if name:
                authors.append(name)
        t = ameta.find('a:title', NS_ARX)
        atitle = (t.text or '').strip() if t is not None else ''

    vid = f'{base_id}v{latest}'
    return {
        # 버전별 날짜 전체. 스냅샷 이후 개정된 논문을 DB가 기록한 버전 기준으로
        # 되돌려 대조하는 데 쓴다 (main 참조). 레코드 필드가 아니므로 '_' 접두사.
        '_versions': {v.get('version'): parse_version_date(
            (v.find('r:date', NS_RAW).text if v.find('r:date', NS_RAW) is not None else ''))
            for v in versions},
        'id': vid,
        # 치환하지 않는다. 최신 층(2024-04-27~)이 raw 표기다 — 모듈 docstring 참조.
        'title': atitle,
        'url': f'http://arxiv.org/pdf/{vid}',
        'date': parse_version_date(vlatest.find('r:date', NS_RAW).text
                                   if vlatest is not None else ''),
        'abs': rtext('abstract'),
        'cat': (rtext('categories').split() or [''])[0],
        'authors': authors,
    }


def version_of(vid):
    m = re.search(r'v(\d+)$', vid or '')
    return int(m.group(1)) if m else 0


def same(field, a, b):
    """title/abs는 공백 차이를 무시한다 — gte가 공백에 불변임을 실측했다 (docstring)."""
    if field in EMBEDDED:
        return ' '.join((a or '').split()) == ' '.join((b or '').split())
    return a == b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-root', default=DEFAULT_DATA)
    ap.add_argument('--n', type=int, default=20, help='대조할 논문 수')
    ap.add_argument('--since', default='',
                    help='이 날짜 이후 논문만 대조 (최신 층 확인용, 예: 2024-04-27)')
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--delay', type=float, default=3.0)
    args = ap.parse_args()

    db_json = f'{args.data_root}/database/arxiv_paper_db_with_cc.json'
    print(f'[1/2] DB 로딩 {db_json}', flush=True)
    with open(db_json) as f:
        docs = list(json.load(f)['cs_paper_info'].values())
    if args.since:
        docs = [d for d in docs if d.get('date', '') >= args.since]
        print(f'      --since {args.since} → 후보 {len(docs)}편', flush=True)
    if not docs:
        raise SystemExit('대조할 논문이 없다. --since 를 확인할 것.')
    picks = random.Random(args.seed).sample(docs, min(args.n, len(docs)))

    print(f'[2/2] OAI 대조 ({len(picks)}편 x 2요청)\n', flush=True)
    fields = ['id', 'title', 'url', 'date', 'abs', 'cat', 'authors']
    mismatch = {f: 0 for f in fields}
    checked = revised = 0

    for i, want in enumerate(picks, 1):
        base = want['id'].split('v')[0]
        got = from_oai(base)
        if got is None:
            print(f'  {i:>3}. {want["id"]:<18} 레코드 없음 (삭제된 논문?)')
            continue
        checked += 1

        # 스냅샷 이후 새 버전이 올라온 논문은 id/제목/초록/저자가 달라지는 게 정상이다.
        was_revised = version_of(got['id']) > version_of(want['id'])
        revised += was_revised

        if was_revised:
            # DB가 담은 버전으로 되돌려 대조한다. 그 버전의 제목·초록·저자는 OAI가
            # 더 이상 주지 않으므로 검사에서 빼되, date는 되돌릴 수 있으므로 검사한다
            # — 규약이 'id에 적힌 버전의 날짜'라는 주장을 실제로 시험하는 부분이다.
            vtag = f'v{version_of(want["id"])}'
            got = dict(got, id=want['id'], url=f'http://arxiv.org/pdf/{want["id"]}',
                       date=got['_versions'].get(vtag, ''))
            checkable = ['id', 'url', 'date']
        else:
            checkable = fields
        bad = [f for f in checkable if not same(f, got[f], want[f])]

        for f in bad:
            mismatch[f] += 1
        blocking = [f for f in bad if f in EMBEDDED]
        mark = '개정' if was_revised and not bad else ('OK  ' if not bad else
                                                      ('차단' if blocking else '경고'))
        print(f'  {i:>3}. {want["id"]:<18} {mark} {" ".join(bad)}')
        for f in bad:
            print(f'         DB  {want[f]!r}'[:160])
            print(f'         OAI {got[f]!r}'[:160])
        time.sleep(args.delay)

    print()
    print(f'대조 {checked}편 (그중 스냅샷 이후 개정 {revised}편 — id/제목/저자 변화는 정상)')
    hard = [f for f in EMBEDDED if mismatch[f]]
    soft = [f for f in fields if mismatch[f] and f not in EMBEDDED]
    for f in hard:
        print(f'  [차단] {f:<8} {mismatch[f]}/{checked} — 임베딩되는 필드다')
    for f in soft:
        print(f'  [경고] {f:<8} {mismatch[f]}/{checked} — 검색에 쓰이지 않는 메타데이터')

    print()
    if hard:
        print('=> 임베딩 대상 필드가 어긋난다. 고치기 전에는 append 하지 말 것.')
        return 1
    print('=> 임베딩 대상(title/abs) 규약 일치. 이 방식으로 수집해도 된다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
