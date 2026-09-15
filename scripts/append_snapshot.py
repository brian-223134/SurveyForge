"""신규 논문을 임베딩해 기존 스냅샷 뒤에 이어 붙이고, 새 스냅샷 디렉터리를 만든다.

기존 `database/`는 **읽기만 한다.** 결과는 새 디렉터리에 쓰므로 파일럿 실행의 A/B
대조가 계속 가능하다.

## 반드시 지켜야 하는 불변식 (2026-08-05 실측)

    TinyDB 키 == arxivid_to_index_abs.json 의 값 == IndexIDMap 의 stored id

셋 다 **1-based**이고 1..589123으로 연속이다. AutoSurvey의 같은 스크립트는
'리스트 위치 == FAISS 행 번호 == 매핑 값'이라는 **0-based** 불변식을 가정하므로
그대로 옮기면 전부 한 칸씩 어긋난다. 그래서 코드를 새로 썼다.

## 임베딩 규약 (추측 금지 — 저장 벡터를 복원해 실측한 값이다)

    faiss_paper_title_abs_* = encode(title + abs)   구분자 없는 단순 연결, cos 1.000000
    faiss_paper_title_*     = encode(title)                              cos 1.000000
    인덱스                  = IndexIDMap(IndexFlatIP), 1024-dim
    저장 벡터               = **L2 정규화됨** (norm 1.0000)
    instruction prefix      = 없음

정규화를 빼먹으면 예외 없이 랭킹만 망가진다. nomic의 'search_document: ' 같은
prefix를 붙이면 cos가 0.9x로 그럴듯하게 틀린다. 둘 다 조용한 실패라
`scripts/check_db.py`의 재임베딩 검증이 유일한 관문이다.

## GPU를 고를 것

이 박스는 GPU가 공유된다. 남이 쓰는 카드에 얹으면 임베딩 처리량이 그대로 반토막난다
(실측: 유휴 68편/s vs 다른 학습과 공유 32편/s). 먼저 확인하고 빈 카드를 지정한다.

    nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
    CUDA_VISIBLE_DEVICES=2 python scripts/append_snapshot.py ...

## id 는 불투명 키다 (KISTI view, 2026-09-15)

KISTI export(id 규칙 B)는 arXiv base id 와 DOI 가 섞여 있고 `authors` 필드가 없다.
중복 판정은 `base_key()` 로 한다 -- arXiv 형식이면 버전 접미사만 떼고, 그 밖의 id(DOI)는
그대로 비교한다. 종전의 `id.split('v')[0]` 은 DOI 를 'v' 에서 잘라(`10.1002/advs.2025…`
→ `10.1002/ad`) 서로 다른 논문을 같은 것으로 묶었다. 제목+저자 중복 제거는 `authors`
가 있는 레코드에서만 돈다 (없으면 건너뛰고 그 사실을 찍는다 -- 제목만으로 지우면
별개 논문 244건을 잃는다, 아래 주석).

`<new>.manifest.json` 이 옆에 있으면 (kisti_data exporter 산출) `append_manifest.json`
에 담고, `build_manifest.json` 은 병합 후 상태(편수·태그·md5·id 형식·derived_from)로
다시 쓴다. `--corpus-export-manifest` 로 전체 export 의 manifest 를 주면 그것이
`corpus_export_manifest.json` 이 된다 (run_manifest 가 view sha 를 여기서 읽는다).

사용법:
    python scripts/append_snapshot.py \
        --base $SURVEYFORGE_DATA/database \
        --new  $SURVEYFORGE_DATA/database_2026-08/arxiv_paper_db_new_with_cc.json \
        --out  $SURVEYFORGE_DATA/database_2026-08 \
        --check-only          # 쓰지 않고 점검만

    # KISTI view 증분 (kisti-2512 v2 → kisti-2608, 2026-09-15)
    CUDA_VISIBLE_DEVICES=3 .venv/bin/python scripts/append_snapshot.py \
        --base $SURVEYFORGE_DATA/database_kisti-kisti-2512 \
        --new  /data2/chanjoong/kisti_data/data/exports/kisti-2608.surveyforge.minus-kisti-2512.json \
        --corpus-export-manifest /data2/chanjoong/kisti_data/data/exports/kisti-2608.surveyforge.json.manifest.json \
        --out  $SURVEYFORGE_DATA/database_kisti-kisti-2608 --tag KISTI_2608
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time

import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

PAPER_DB = 'arxiv_paper_db_with_cc.json'
PAPER_MAP = 'arxivid_to_index_abs.json'
ABS_STEM = 'faiss_paper_title_abs_embeddings'
TITLE_STEM = 'faiss_paper_title_embeddings'


# build_db_from_corpus.py 와 같은 규칙: arXiv 신형 YYMM.NNNNN / 구형 archive/YYMMNNN (버전 접미사 허용).
_ARXIV_ID = re.compile(r'^(\d{4}\.\d{4,5}|[a-zA-Z\-]+(\.[a-zA-Z]{2})?/\d{7})(v\d+)?$')


def base_key(pid):
    """중복 판정 키. arXiv 형식이면 버전 접미사를 뗀 base id, 그 밖(DOI)은 그대로.

    DOI 에는 'v' 가 흔히 들어간다 (`10.1002/advs.…`, `10.1109/tvt.…`). 그것을 'v' 에서
    자르면 서로 다른 논문이 한 키로 뭉친다 -- KISTI 추가분 12,217편 중 1,374편이 그렇다.
    """
    pid = str(pid)
    m = _ARXIV_ID.match(pid)
    return pid[:m.start(3)] if m and m.group(3) else pid


def id_formats_of(ids):
    f = {'arxiv': 0, 'doi': 0, 'other': 0}
    for i in ids:
        i = str(i)
        f['doi' if i.startswith('10.') else 'arxiv' if _ARXIV_ID.match(i) else 'other'] += 1
    return f


def title_author_key(rec):
    """제목+저자로 만든 동일 논문 판별 키.

    제목만으로는 안 된다 — 기존 DB의 제목 충돌 742건 중 244건은 저자가 다른 별개
    논문이었다 ('A Duality Based 2-Approximation Algorithm...'처럼). 저자까지 맞아야
    같은 논문으로 본다.
    """
    title = re.sub(r'[^a-z0-9]', '', (rec.get('title') or '').lower())
    authors = tuple(a.strip().lower() for a in (rec.get('authors') or []))
    return (title, authors)


def find_one(db_path, stem):
    """<stem>_*.bin 이 정확히 하나 있어야 한다."""
    hits = sorted(f for f in os.listdir(db_path)
                  if f.startswith(stem + '_') and f.endswith('.bin'))
    if len(hits) != 1:
        raise SystemExit(f'{db_path}/{stem}_*.bin 이 {len(hits)}개다 (1개여야 한다): {hits}')
    return os.path.join(db_path, hits[0])


def md5(path, chunk=1 << 24):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(chunk), b''):
            h.update(blk)
    return h.hexdigest()


def check_consistency(table, mapping, indexes, label):
    """세 자료구조가 같은 1-based id 체계를 공유하는지 확인한다.

    어긋난 채로 쓰면 검색은 계속 되지만 엉뚱한 논문이 돌아온다. 그래서 base와
    병합 결과 양쪽에서 부르고, 실패하면 아무것도 쓰지 않는다.
    """
    n = len(table)
    problems = []
    if len(mapping) != n:
        problems.append(f'TinyDB {n}건 vs 매핑 {len(mapping)}건')
    for name, idx in indexes.items():
        if idx.ntotal != n:
            problems.append(f'TinyDB {n}건 vs {name} ntotal {idx.ntotal}')

    keys = sorted(int(k) for k in table)
    if keys != list(range(1, n + 1)):
        problems.append(f'TinyDB 키가 1..{n} 연속이 아니다 (min {keys[0]}, max {keys[-1]})')

    # 표본으로 키 == 매핑값을 확인한다. 전수는 느리고, 어긋남은 보통 구간 단위다.
    for i in [1, n // 3, n // 2, n]:
        rec = table.get(str(i))
        if rec is None:
            problems.append(f'TinyDB 키 {i} 없음')
            continue
        if mapping.get(rec['id']) != i:
            problems.append(f"매핑 불일치 키 {i}: {rec['id']} -> {mapping.get(rec['id'])}")

    for name, idx in indexes.items():
        ids = faiss.vector_to_array(idx.id_map)
        if ids.min() != 1 or ids.max() != n or len(np.unique(ids)) != n:
            problems.append(f'{name} stored id가 1..{n} 전단사가 아니다 '
                            f'(min {ids.min()}, max {ids.max()}, unique {len(np.unique(ids))})')

    if problems:
        print(f'[정합성/{label}] 실패:', file=sys.stderr)
        for p in problems:
            print(f'  - {p}', file=sys.stderr)
        raise SystemExit('정합성 검사 실패 — 아무것도 쓰지 않았다.')
    print(f'[정합성/{label}] OK  {n:,}편, 키/매핑/두 인덱스 모두 1..{n} 일치')


def embed(model, texts, batch_size, label):
    out, t0 = [], time.time()
    for i in range(0, len(texts), batch_size):
        out.append(model.encode(texts[i:i + batch_size], show_progress_bar=False,
                                normalize_embeddings=True))   # 저장 벡터가 norm 1.0이다
        done = min(i + batch_size, len(texts))
        if done % (batch_size * 20) == 0 or done == len(texts):
            rate = done / max(time.time() - t0, 1e-9)
            print(f'  [{label}] {done:,}/{len(texts):,}  {rate:.0f}편/s', flush=True)
    return np.concatenate(out).astype('float32')


def _json_or_none(path):
    if path and os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def write_manifests(args, table, mapping, fresh, n_base, n_in_file, tag, md5s, base_files,
                    model_path, device):
    """append_manifest.json(이번 증분의 기록) + build_manifest.json(병합 후 상태) + corpus_export_manifest.json.

    main.py 의 run_manifest 는 build_manifest 의 records/tag/export/export_file_sha256/built_at/id_formats 와
    corpus_export_manifest 의 view sha 를 읽는다 -- 병합 후 값이어야 결과 기록이 새 view 를 가리킨다.
    """
    now = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    base_build = _json_or_none(os.path.join(args.base, 'build_manifest.json')) or {}
    base_export = _json_or_none(os.path.join(args.base, 'corpus_export_manifest.json'))
    base_diff = _json_or_none(os.path.join(args.base, 'view_diff_manifest.json'))
    new_manifest = _json_or_none(args.new + '.manifest.json')
    full_manifest = _json_or_none(args.corpus_export_manifest) if args.corpus_export_manifest else None
    if args.corpus_export_manifest and full_manifest is None:
        raise SystemExit(f'--corpus-export-manifest 없음: {args.corpus_export_manifest}')
    n = len(table)
    dates = [r['date'] for r in table.values() if r.get('date')]
    new_ids = [r['id'] for r in fresh]

    append_manifest = {
        'created_at': now,
        'builder': 'scripts/append_snapshot.py',
        'base': {'dir': os.path.abspath(args.base), 'records': n_base,
                 'built_at': base_build.get('built_at'), 'tag': base_build.get('tag'),
                 'md5': base_build.get('md5'),
                 'view': (base_export or {}).get('view'),
                 'view_diff': ({k: base_diff.get(k) for k in ('created_at', 'v1_records', 'v2_records',
                                                             'removed_count', 'added_count')}
                               if base_diff else None)},
        'new': {'path': os.path.abspath(args.new), 'records_in_file': n_in_file, 'added': len(fresh),
                'skipped_duplicate': n_in_file - len(fresh), 'manifest': new_manifest,
                'file_sha256': _sha256(args.new), 'stored_ids': [n_base + 1, n],
                'id_formats': id_formats_of(new_ids),
                'date_range': [min(r['date'] for r in fresh), max(r['date'] for r in fresh)]},
        'embedding': {'model': model_path, 'device': device, 'batch_size': args.batch_size,
                      'text': 'title + abs (구분자 없음) / title, L2 정규화, prefix 없음'},
        'merged': {'records': n, 'tag': tag, 'index_type': 'IndexIDMap(IndexFlatIP)',
                   'stored_ids': '1-based 연속: base 1..%d 그대로 + 신규 %d..%d' % (n_base, n_base + 1, n),
                   'md5': md5s, 'date_range': [min(dates), max(dates)]},
        'corpus_export_manifest': ('--corpus-export-manifest 사본' if full_manifest else 'base 사본'),
    }
    with open(os.path.join(args.out, 'append_manifest.json'), 'w') as f:
        json.dump(append_manifest, f, ensure_ascii=False, indent=2)

    export_manifest = full_manifest or base_export
    if export_manifest is not None:
        with open(os.path.join(args.out, 'corpus_export_manifest.json'), 'w') as f:
            json.dump(export_manifest, f, ensure_ascii=False, indent=2)

    build_manifest = {
        'built_at': now,
        'builder': 'scripts/append_snapshot.py',
        'derived_from': {'dir': os.path.abspath(args.base), 'built_at': base_build.get('built_at'),
                         'records': n_base, 'md5': base_build.get('md5'), 'view_diff': base_diff,
                         'method': f'append: 신규 {len(fresh):,}편을 gte 로 임베딩해 stored id '
                                   f'{n_base + 1}..{n} 으로 뒤에 붙임, base 벡터·레코드는 바이트 그대로'},
        # 병합 결과의 id 집합은 전체 export 와 같다 (base ∪ 차분). 순서는 base 접두 + 추가분이라
        # JSON 이 export 의 바이트 사본은 아니다 -- export_file_sha256 는 그 전체 export 의 지문.
        'export': (os.path.abspath(args.corpus_export_manifest)[:-len('.manifest.json')]
                   if args.corpus_export_manifest and args.corpus_export_manifest.endswith('.manifest.json')
                   else base_build.get('export')),
        'export_file_sha256': (full_manifest or {}).get('file_sha256', base_build.get('export_file_sha256')),
        'export_equivalence': 'id 집합 == export (순서 다름: base 접두 + 추가분)' if full_manifest else 'base 의 기록',
        'export_manifest': export_manifest,
        'append': {'new': os.path.abspath(args.new), 'added': len(fresh),
                   'skipped_duplicate': n_in_file - len(fresh), 'stored_ids': [n_base + 1, n]},
        'records': n,
        'id_formats': id_formats_of(r['id'] for r in table.values()),
        'tag': tag,
        'embedding_model': model_path,
        'batch_size': args.batch_size,
        'text_normalization': base_build.get('text_normalization', 'none — export 원문 그대로'),
        'date_range': [min(dates), max(dates)],
        'md5': md5s,
    }
    with open(os.path.join(args.out, 'build_manifest.json'), 'w') as f:
        json.dump(build_manifest, f, ensure_ascii=False, indent=2)
    print('      append_manifest.json · build_manifest.json · corpus_export_manifest.json 기록')


def _sha256(path, chunk=1 << 24):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(chunk), b''):
            h.update(blk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base', required=True, help='기존 database/ (읽기 전용)')
    ap.add_argument('--new', required=True, help='citation_count까지 채운 신규 레코드 json')
    ap.add_argument('--out', required=True, help='새 스냅샷 디렉터리')
    ap.add_argument('--embedding-model', default='')
    # 64가 실측 최적이다 (L40S 유휴 기준 68 / 64 / 58 편/s at 64 / 128 / 256).
    # 토큰 길이가 중앙값 291, 최대 567이라 배치를 키워도 이득이 없고, gte의 커스텀
    # 어텐션이 seq^2로 메모리를 잡아 512에서는 OOM이 난다.
    ap.add_argument('--batch-size', type=int, default=64)
    ap.add_argument('--device', default='')
    ap.add_argument('--tag', default='', help="파일명 접미사, 예 FROM_2012_0101_TO_260803 / KISTI_2608")
    ap.add_argument('--corpus-export-manifest', default='',
                    help='병합 결과와 id 집합이 같은 전체 export 의 manifest -- 새 스냅샷의 '
                         'corpus_export_manifest.json 이 된다 (비우면 base 것을 복사)')
    ap.add_argument('--keep-title-dups', action='store_true',
                    help='제목+저자가 같은 논문도 그대로 넣는다 (기본은 제거)')
    ap.add_argument('--check-only', action='store_true', help='쓰지 않고 점검만')
    args = ap.parse_args()

    data_root = os.path.dirname(os.path.abspath(args.base))
    model_path = args.embedding_model or os.path.join(data_root, 'gte-large-en-v1.5')

    print(f'[1/6] base 로딩 {args.base}', flush=True)
    with open(os.path.join(args.base, PAPER_DB)) as f:
        table = json.load(f)['cs_paper_info']
    with open(os.path.join(args.base, PAPER_MAP)) as f:
        mapping = {k: int(v) for k, v in json.load(f).items()}
    abs_path, title_path = find_one(args.base, ABS_STEM), find_one(args.base, TITLE_STEM)
    abs_idx, title_idx = faiss.read_index(abs_path), faiss.read_index(title_path)
    check_consistency(table, mapping, {'abs': abs_idx, 'title': title_idx}, 'base')

    n_base = len(table)
    print(f'\n[2/6] 신규 레코드 로딩 {args.new}', flush=True)
    with open(args.new) as f:
        fresh = list(json.load(f)['cs_paper_info'].values())
    n_in_file = len(fresh)
    have = {base_key(r['id']) for r in table.values()}
    fresh = [r for r in fresh if base_key(r['id']) not in have]
    n_dup_base = n_in_file - len(fresh)
    # 같은 논문이 두 번 들어오면 매핑이 덮어써져 벡터 하나가 미아가 된다.
    seen, dedup = set(), []
    for r in fresh:
        b = base_key(r['id'])
        if b not in seen:
            seen.add(b)
            dedup.append(r)
    n_dup_self = len(fresh) - len(dedup)
    fresh = dedup
    if n_dup_base or n_dup_self:
        print(f'      id 중복 제외: 기존과 겹침 {n_dup_base:,}편, 신규끼리 겹침 {n_dup_self:,}편')

    has_authors = bool(fresh) and all('authors' in r for r in fresh[:1000])
    if not args.keep_title_dups and not has_authors:
        # 저자 없이 제목만으로 지우면 별개 논문을 잃는다 (아래 실측). KISTI export 가 이 경우다.
        print('      authors 필드 없음 (KISTI export) -- 제목+저자 중복 제거는 건너뛰고 id 로만 판정')
    if not args.keep_title_dups and has_authors:
        # 같은 논문이 arXiv에 다른 id로 두 번 올라오는 경우가 있다. id 기준 중복 제거로는
        # 안 잡힌다. 기존 DB에서 실측하면 제목 충돌 742건 중 498건이 저자까지 같았고
        # (진짜 중복), 244건은 제목만 같은 별개 논문이었다 — 그래서 제목만으로 지우면
        # 안 되고 저자까지 일치할 때만 지운다.
        n_before = len(fresh)
        base_keys = {title_author_key(r) for r in table.values()}
        kept, seen_fresh, dropped_base, dropped_self = [], set(), 0, 0
        for r in fresh:
            k = title_author_key(r)
            if k in base_keys:
                # 기존 스냅샷 쪽을 남긴다. base를 얼려 둬야 A/B 대조가 유지된다.
                dropped_base += 1
                continue
            if k in seen_fresh:
                dropped_self += 1
                continue
            seen_fresh.add(k)
            kept.append(r)
        fresh = kept
        if n_before != len(fresh):
            print(f'      제목+저자 중복 제거: 기존과 겹침 {dropped_base:,}편, '
                  f'신규끼리 겹침 {dropped_self:,}편 (--keep-title-dups로 끌 수 있다)')
    need = ('id', 'title', 'url', 'date', 'abs', 'cat', 'citation_count')   # authors 는 선택
    missing = {f for r in fresh[:1000] for f in need if f not in r}
    if missing:
        raise SystemExit(f'신규 레코드에 없는 필드: {sorted(missing)}')
    print(f'      기존에 없는 신규 {len(fresh):,}편')
    if not fresh:
        raise SystemExit('추가할 논문이 없다.')

    dates = [r['date'] for r in fresh if r.get('date')]
    print(f'      날짜 범위 {min(dates)} .. {max(dates)}')

    device = args.device or ('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'\n[3/6] 임베딩 {model_path} on {device} (batch {args.batch_size})', flush=True)
    model = SentenceTransformer(model_path, trust_remote_code=True)
    model.to(torch.device(device))
    # 구분자 없는 단순 연결이다. 공백 하나만 끼워도 cos가 0.99로 떨어진다.
    abs_vec = embed(model, [r['title'] + r['abs'] for r in fresh], args.batch_size, 'title+abs')
    title_vec = embed(model, [r['title'] for r in fresh], args.batch_size, 'title')

    print(f'\n[4/6] 병합', flush=True)
    new_ids = np.arange(n_base + 1, n_base + 1 + len(fresh), dtype='int64')  # 1-based 연속
    for r, i in zip(fresh, new_ids):
        table[str(int(i))] = r
        mapping[r['id']] = int(i)
    # IndexIDMap 은 add() 를 거부한다. stored id 를 직접 준다.
    abs_idx.add_with_ids(abs_vec, new_ids)
    title_idx.add_with_ids(title_vec, new_ids)
    check_consistency(table, mapping, {'abs': abs_idx, 'title': title_idx}, 'merged')

    if args.check_only:
        print('\n--check-only: 쓰지 않고 종료한다.')
        return 0

    tag = args.tag or f"FROM_2012_0101_TO_{max(dates).replace('-', '')[2:]}"
    os.makedirs(args.out, exist_ok=True)
    print(f'\n[5/6] 쓰기 {args.out}  (tag {tag})', flush=True)
    out_db = os.path.join(args.out, PAPER_DB)
    out_map = os.path.join(args.out, PAPER_MAP)
    out_abs = os.path.join(args.out, f'{ABS_STEM}_{tag}.bin')
    out_title = os.path.join(args.out, f'{TITLE_STEM}_{tag}.bin')
    with open(out_db, 'w') as f:
        json.dump({'cs_paper_info': table}, f, ensure_ascii=False)
    with open(out_map, 'w') as f:
        json.dump(mapping, f)
    faiss.write_index(abs_idx, out_abs)
    faiss.write_index(title_idx, out_title)
    # 우리가 다시 만든 4개를 뺀 나머지를 전부 복사한다. 서베이 자산을 이름으로 나열하면
    # 파일명이 바뀌었을 때 조용히 빠지고, 그 스냅샷은 실행 시점에야 죽는다.
    # base 의 빌드 기록 3종은 병합 후 상태를 말하지 않으므로 복사하지 않고 아래에서 다시 쓴다
    # (build_manifest 는 derived_from 으로, view_diff 는 그 안에 접어 넣는다).
    regenerated = {os.path.basename(p) for p in (out_db, out_map, out_abs, out_title)}
    regenerated |= {os.path.basename(abs_path), os.path.basename(title_path)}
    regenerated |= {'build_manifest.json', 'corpus_export_manifest.json', 'view_diff_manifest.json'}
    copied = []
    for name in sorted(os.listdir(args.base)):
        if name in regenerated:
            continue
        src = os.path.join(args.base, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(args.out, name))
            copied.append(name)
    print(f'      나머지 자산 {len(copied)}개 복사 (서베이 DB 등): {", ".join(copied)}')
    missing = ({f for f in os.listdir(args.base) if os.path.isfile(os.path.join(args.base, f))}
               - set(os.listdir(args.out)) - regenerated)
    if missing:
        raise SystemExit(f'새 스냅샷에 빠진 파일: {sorted(missing)}')

    print(f'\n[6/6] 지문 — REPRODUCTION.md 에 기록할 값', flush=True)
    md5s = {}
    for p in (out_db, out_map, out_abs, out_title):
        md5s[os.path.basename(p)] = md5(p)
        print(f'  {os.path.basename(p):<62} {os.path.getsize(p):>14,}  {md5s[os.path.basename(p)]}')
    write_manifests(args, table, mapping, fresh, n_base, n_in_file, tag, md5s,
                    base_files=(abs_path, title_path), model_path=model_path, device=device)
    print(f'\n  총 {len(table):,}편 (기존 {n_base:,} + 신규 {len(fresh):,})')
    print(f'  코퍼스 최신일 {max(r["date"] for r in table.values() if r.get("date"))}')
    print('\n다음: scripts/check_db.py 로 재임베딩 검증')
    return 0


if __name__ == '__main__':
    sys.exit(main())
