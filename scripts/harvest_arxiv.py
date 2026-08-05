"""arXiv OAI-PMH로 논문 메타데이터를 수집해 기존 DB와 같은 형식으로 만든다.

배포 DB는 수록 논문이 2024-09-25에서 끝난다. `--exclude-db`로 기존 DB에 없는 논문만
골라 받아 `scripts/append_snapshot.py`가 쓸 재료를 만든다.

## 기존 DB의 표기 규약 (2026-08-05, `scripts/check_oai_schema.py`로 25편 대조 확정)

  id      base + '최신' 버전 접미사      2407.16160v2
  date    **id에 적힌 버전의 날짜**      v1이 아니다. 개정본은 v1과 몇 달~몇 년 어긋난다
  url     http://arxiv.org/pdf/{id}      https 아님, /pdf/, 버전 포함
  abs     TeX escape 보존                arXivRaw <abstract>. arXiv 형식은 유니코드로
                                         변환돼 있어 기존 코퍼스와 다르다
  title   유니코드, **치환 없음**        arXiv <title> 그대로
  cat     <categories> 첫 번째           primary category
  authors 유니코드 'forenames keyname'   arXiv 형식의 구조화 저자

**abs와 title/authors의 출처가 서로 달라 두 형식을 모두 받는다.** 페이지 수가 두 배가
되지만 임베딩 대상 필드를 정확히 맞추는 값이 크다.

## AutoSurvey의 같은 스크립트와 다른 점 (그대로 가져오면 조용히 깨지는 것들)

  1. **제목을 치환하지 않는다.** AutoSurvey DB는 제목에서 '<>:"/|?*#'를 공백으로
     바꿔 놨고 그쪽 스크립트도 그렇게 한다. 이 DB는 두 층인데 —
        치환됨   149,036편  2012-01-01 .. 2024-04-26   (AutoSurvey 계열 베이스)
        ':' 보존  21,791편  2024-04-23 .. 2024-09-25   (저자들의 자체 증분)
     — 최신 층이 raw 표기다. 신규 논문은 최신 층을 따른다.
  2. **date를 v1이 아니라 최신 버전에서 딴다.** AutoSurvey는 의도적으로 v1을 쓴다.
     그대로 옮기면 개정본의 날짜가 어긋나 리랭커의 시간창 배정이 조용히 틀어진다.
  3. citation_count는 여기서 만들지 않는다. `scripts/fetch_citations.py`가 채운다.

## 출력

  <out-dir>/_harvest/records_arXivRaw.jsonl   중간 산출물 (재개용)
  <out-dir>/_harvest/records_arXiv.jsonl
  <out-dir>/arxiv_paper_db_new.json           {"cs_paper_info": {"0": {...7필드}, ...}}

resumptionToken이 state.json에 저장되므로 중단 후 같은 명령을 다시 실행하면 이어서 받는다.

예)
    python scripts/harvest_arxiv.py --sets cs --oai-from 2024-09-25 \
        --exclude-db $SURVEYFORGE_DATA/database/arxiv_paper_db_with_cc.json \
        --out-dir $SURVEYFORGE_DATA/database_2026-08

    # 스모크 — 한 페이지만
    python scripts/harvest_arxiv.py --sets cs:cs:CL --oai-from 2026-07-01 \
        --max-pages 1 --out-dir /tmp/harvest-smoke
"""

import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

import requests

# 2026-08 기준 export.arxiv.org/oai2 는 이곳으로 301 리다이렉트된다.
OAI_URL = 'https://oaipmh.arxiv.org/oai'

NS = {
    'oai': 'http://www.openarchives.org/OAI/2.0/',
    'arxiv': 'http://arxiv.org/OAI/arXiv/',
    'raw': 'http://arxiv.org/OAI/arXivRaw/',
}
WS = re.compile(r'\s+')
MONTHS = {m: i for i, m in enumerate(
    ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}


def norm(text):
    """OAI 응답의 title/abstract에 섞인 줄바꿈·들여쓰기를 공백으로 정규화한다.

    기존 DB는 원문의 하드 줄바꿈을 보존하고 있다. 그래도 정규화하는 이유는
    gte-large-en-v1.5가 공백 차이에 **완전히** 불변이기 때문이다 — 40편 표본에서
    저장 텍스트 대 공백 정규화본의 cos가 최솟값까지 1.000000이었다. 오히려 참고문헌
    목록 출력이 깔끔해진다 (writer.py가 제목의 '\\n'을 지울 때 이중 공백이 남는다).
    """
    return WS.sub(' ', (text or '')).strip()


def parse_version_date(text):
    """'Fri, 14 Aug 2020 20:46:38 GMT' -> '2020-08-14'"""
    m = re.search(r'(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})', text or '')
    if not m:
        return ''
    return f'{m.group(3)}-{MONTHS.get(m.group(2), 0):02d}-{int(m.group(1)):02d}'


def oai_request(params, session, max_try=8):
    """503 + Retry-After(arXiv의 레이트리밋 신호)를 존중하며 한 번 요청한다."""
    last_err = None
    for attempt in range(max_try):
        try:
            r = session.get(OAI_URL, params=params, timeout=180)
            if r.status_code == 503:
                wait = int(r.headers.get('Retry-After', 20))
                print(f'  503 rate limited, {wait}s 대기', flush=True)
                time.sleep(wait)
                continue
            if r.status_code != 200:
                last_err = f'HTTP {r.status_code}: {r.text[:200]}'
            else:
                # arXiv는 Content-Type에 charset을 안 붙인다. 그러면 requests가
                # text/*를 ISO-8859-1로 디코드해 'Schölkopf'가 'SchÃ¶lkopf'가 된다.
                # XML 선언이 UTF-8이므로 명시한다.
                r.encoding = 'utf-8'
                return r.text
        except Exception as e:  # 네트워크 순단
            last_err = repr(e)
        wait = min(2 ** attempt, 60)
        print(f'  요청 실패({last_err}), {wait}s 후 재시도', flush=True)
        time.sleep(wait)
    raise RuntimeError(f'OAI 요청 {max_try}회 실패: {last_err}')


def parse_page(xml_text, prefix):
    """(records, resumption_token). prefix에 따라 뽑는 필드가 다르다."""
    root = ET.fromstring(xml_text)

    error = root.find('oai:error', NS)
    if error is not None:
        code = error.get('code')
        # 지정한 윈도에 레코드가 없으면 정상 종료로 취급한다.
        if code == 'noRecordsMatch':
            return [], None
        raise RuntimeError(f'OAI error [{code}]: {error.text}')

    list_records = root.find('oai:ListRecords', NS)
    if list_records is None:
        return [], None

    records = []
    for rec in list_records.findall('oai:record', NS):
        header = rec.find('oai:header', NS)
        # 철회/삭제된 논문은 metadata가 없다.
        if header is not None and header.get('status') == 'deleted':
            continue
        parsed = (_parse_raw(rec) if prefix == 'arXivRaw' else _parse_arxiv(rec))
        if parsed:
            records.append(parsed)

    token_node = list_records.find('oai:resumptionToken', NS)
    token = token_node.text.strip() if token_node is not None and token_node.text else None
    return records, token


def _parse_raw(rec):
    """arXivRaw: 버전 목록 / 최신 버전 날짜 / TeX 보존 초록 / 카테고리"""
    meta = rec.find('oai:metadata/raw:arXivRaw', NS)
    if meta is None:
        return None

    def text(tag):
        node = meta.find(f'raw:{tag}', NS)
        return norm(node.text) if node is not None else ''

    paper_id = text('id')
    abstract = text('abstract')
    if not paper_id or not abstract:
        return None

    versions = meta.findall('raw:version', NS)
    vnums = [int(v.get('version', 'v1').lstrip('v')) for v in versions] or [1]
    latest = max(vnums)
    # date는 id에 적힌 버전, 곧 최신 버전의 날짜다 (모듈 docstring의 규약 참조).
    vlatest = next((v for v in versions if v.get('version') == f'v{latest}'), None)
    vdate = vlatest.find('raw:date', NS) if vlatest is not None else None

    return {
        'id': paper_id,
        'v': latest,
        'abs': abstract,
        'date': parse_version_date(vdate.text if vdate is not None else ''),
        'cat': (text('categories').split() or [''])[0],
    }


def _parse_arxiv(rec):
    """arXiv: 유니코드 제목 / 구조화 저자"""
    meta = rec.find('oai:metadata/arxiv:arXiv', NS)
    if meta is None:
        return None

    node = meta.find('arxiv:id', NS)
    paper_id = norm(node.text) if node is not None else ''
    node = meta.find('arxiv:title', NS)
    title = norm(node.text) if node is not None else ''
    if not paper_id or not title:
        return None

    authors = []
    for a in meta.findall('arxiv:authors/arxiv:author', NS):
        key = a.find('arxiv:keyname', NS)
        fore = a.find('arxiv:forenames', NS)
        name = ' '.join(x.text.strip() for x in (fore, key)
                        if x is not None and x.text)
        if name:
            authors.append(name)

    # 제목은 치환하지 않는다 — 최신 층이 raw 표기다 (모듈 docstring 참조).
    return {'id': paper_id, 'title': title, 'authors': authors}


def sweep(prefix, set_spec, state, out_f, session, args, seen):
    """한 세트를 한 형식으로 끝까지 수집한다."""
    key = f'{prefix}/{set_spec}'
    st = state.get(key, {})
    if st.get('done'):
        print(f'[{key}] 이미 완료됨, 건너뜀')
        return 0

    token, page, added = st.get('token'), st.get('page', 0), 0
    while True:
        if token:
            # resumptionToken을 쓸 때는 다른 인자를 함께 보내면 badArgument가 된다.
            params = {'verb': 'ListRecords', 'resumptionToken': token}
        else:
            params = {'verb': 'ListRecords', 'set': set_spec, 'metadataPrefix': prefix}
            if args.oai_from:
                params['from'] = args.oai_from
            if args.oai_until:
                params['until'] = args.oai_until

        records, token = parse_page(oai_request(params, session), prefix)
        page += 1

        for rec in records:
            if rec['id'] in seen:
                continue
            seen.add(rec['id'])
            out_f.write(json.dumps(rec, ensure_ascii=False) + '\n')
            added += 1

        out_f.flush()
        state[key] = {'token': token, 'page': page, 'done': token is None}
        save_state(args.out_dir, state)
        print(f'[{key}] page {page}: +{len(records)}건 (누적 {len(seen):,}) '
              f'{"완료" if token is None else ""}', flush=True)

        if token is None:
            return added
        if args.max_pages and page >= args.max_pages:
            print(f'[{key}] --max-pages {args.max_pages} 도달, 중단')
            return added
        time.sleep(args.delay)


def state_path(out_dir):
    return os.path.join(out_dir, '_harvest', 'state.json')


def save_state(out_dir, state):
    with open(state_path(out_dir), 'w') as f:
        json.dump(state, f, indent=2)


def load_state(out_dir):
    if os.path.exists(state_path(out_dir)):
        with open(state_path(out_dir)) as f:
            return json.load(f)
    return {}


def load_jsonl(path):
    """중단 후 재개 시 이미 받은 레코드를 복원한다. {id: rec}"""
    out = {}
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                out[rec['id']] = rec
            except (json.JSONDecodeError, KeyError):
                continue
    return out


def load_existing_ids(db_json):
    """기존 DB의 id를 버전 접미사를 뗀 형태로 모은다."""
    with open(db_json) as f:
        table = json.load(f)['cs_paper_info']
    return {v['id'].split('v')[0] for v in table.values()}


def finalize(work_dir, args):
    """두 형식을 id로 조인해 기존 DB와 같은 7필드 레코드를 만든다."""
    raw = load_jsonl(os.path.join(work_dir, 'records_arXivRaw.jsonl'))
    arx = load_jsonl(os.path.join(work_dir, 'records_arXiv.jsonl'))
    print(f'\narXivRaw {len(raw):,}건 / arXiv {len(arx):,}건')

    exclude = set()
    if args.exclude_db:
        exclude = load_existing_ids(args.exclude_db)
        print(f'기존 DB {len(exclude):,}편 — 여기 있는 논문은 건너뛴다')

    papers, idx = {}, 0
    missing, skipped = 0, 0
    for pid, r in raw.items():
        a = arx.get(pid)
        if a is None:          # 한쪽 형식에만 있는 레코드는 버린다
            missing += 1
            continue
        if pid in exclude:     # 기존 논문의 v2/v3 갱신 — 이번 대상이 아니다
            skipped += 1
            continue
        vid = f'{pid}v{r["v"]}'
        papers[str(idx)] = {
            'id': vid,
            'title': a['title'],
            'url': f'http://arxiv.org/pdf/{vid}',
            'date': r['date'],
            'abs': r['abs'],
            'cat': r['cat'],
            'authors': a['authors'],
        }
        idx += 1
        if args.max_records and idx >= args.max_records:
            break

    if missing:
        print(f'  한쪽 형식에만 있어 제외: {missing:,}건')
    if skipped:
        print(f'  기존 DB에 이미 있어 제외: {skipped:,}건')

    db_path = os.path.join(args.out_dir, 'arxiv_paper_db_new.json')
    with open(db_path, 'w') as f:
        json.dump({'cs_paper_info': papers}, f, ensure_ascii=False)
    print(f'\n{db_path} 작성 완료: {idx:,}편')
    print('다음: scripts/fetch_citations.py 로 citation_count 를 채운다')
    return idx


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--sets', nargs='+', default=['cs'],
                        help="OAI setSpec 목록. 전체 CS는 'cs' 하나면 된다. "
                             "하위 분류는 'cs:cs:CL' 형식")
    parser.add_argument('--out-dir', required=True, help='출력 디렉터리')
    parser.add_argument('--oai-from', default=None,
                        help='OAI from (최종 수정일 기준, YYYY-MM-DD)')
    parser.add_argument('--oai-until', default=None, help='OAI until (YYYY-MM-DD)')
    parser.add_argument('--exclude-db', default=None,
                        help='기존 arxiv_paper_db_with_cc.json 경로. 여기 있는 논문은 '
                             '제외한다 (OAI from은 수정일 기준이라 옛 논문의 개정본이 딸려온다)')
    parser.add_argument('--max-records', type=int, default=0,
                        help='최종 DB 상한 (0이면 무제한)')
    parser.add_argument('--max-pages', type=int, default=0,
                        help='형식·세트당 페이지 상한 (스모크용, 0이면 무제한)')
    parser.add_argument('--delay', type=float, default=3.0,
                        help='페이지 사이 대기 초 (arXiv 권장 간격)')
    parser.add_argument('--finalize-only', action='store_true',
                        help='수집은 건너뛰고 기존 jsonl 만 DB로 변환')
    args = parser.parse_args()

    work_dir = os.path.join(args.out_dir, '_harvest')
    os.makedirs(work_dir, exist_ok=True)

    if not args.finalize_only:
        state = load_state(args.out_dir)
        session = requests.Session()
        session.headers['User-Agent'] = (
            'surveyforge-harvester/0.1 (+https://github.com/brian-223134/SurveyForge)')

        # 초록은 arXivRaw, 제목·저자는 arXiv에서 온다. 두 번 훑는다.
        for prefix in ('arXivRaw', 'arXiv'):
            path = os.path.join(work_dir, f'records_{prefix}.jsonl')
            seen = set(load_jsonl(path))
            if seen:
                print(f'[{prefix}] 기존 {len(seen):,}건 발견, 이어서 수집')
            with open(path, 'a') as out_f:
                for set_spec in args.sets:
                    print(f'\n=== {prefix} / {set_spec} ===')
                    sweep(prefix, set_spec, state, out_f, session, args, seen)

    total = finalize(work_dir, args)
    if total == 0:
        print('경고: 수집된 논문이 0편입니다. --sets / 날짜 필터를 확인하세요', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
