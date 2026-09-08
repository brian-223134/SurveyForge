"""KISTI corpus → SurveyForge 스냅샷: corpus 를 실제로 쿼리해 올 수 있는지 검사한다.

검사 층위 (아래로 갈수록 무겁다):
  1. view/export 정합  — kisti_data 의 view 파일·manifest 와 export manifest 가 서로 맞는가 (sha256 포함)
  2. 스냅샷 정합      — 빌드된 DB 의 build_manifest·id map·FAISS 파일·outline DB 자산이 export 와 맞는가
  3. 제외 키 누수      — GT/twin 38키가 DB id map 에 없고, twin arXiv id 가 outline DB 제외 목록(.env)에 있는가
  4. id → DOI → 원문   — DB id 를 kisti_data 어댑터로 DOI·원문(body_store)까지 되짚을 수 있는가 (env 독립)
  5. 임베딩 질의       — gte 로 질의를 인코딩해 FAISS 를 직접 검색: 제목 자기-검색 rank 1, 주제 질의에서
                        DOI/arXiv 혼합 결과, 연도 ≤ 2025

2 · 3(앞부분) · 5 는 `SurveyForge_data/database_kisti-<view>/build_manifest.json` 이 있어야 돌고, 없으면 SKIP.
5 는 FAISS 인덱스 2종(약 13GB)을 읽고 gte 를 올리므로 1~3분 걸린다. KISTI_TEST_FAST=1 이면 5 와
2.38GB export 해시를 건너뛴다. LLM 호출은 없다.

    cd code && ../.venv/bin/python ../tests/test_kisti_corpus.py
    cd code && ../.venv/bin/python -m pytest ../tests/test_kisti_corpus.py -q     # pytest 가 있으면

환경변수: KISTI_DATA_ROOT(기본 /data2/chanjoong/kisti_data) · KISTI_VIEW(기본 kisti-2512) ·
SURVEYFORGE_DATA · SURVEYFORGE_DB_DIR(기본 database_kisti-<view>)
"""

import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
CODE = os.path.join(ROOT, 'code')
sys.path.insert(0, CODE)

KISTI = os.environ.get('KISTI_DATA_ROOT', '/data2/chanjoong/kisti_data')
VIEW = os.environ.get('KISTI_VIEW', 'kisti-2512')
DATA = os.environ.get('SURVEYFORGE_DATA', '/data2/chanjoong/survey-agent/SurveyForge_data')
DB = os.path.join(DATA, os.environ.get('SURVEYFORGE_DB_DIR', f'database_kisti-{VIEW}'))
VIEW_DIR = os.path.join(KISTI, 'data', 'views', VIEW)
EXPORT = os.path.join(KISTI, 'data', 'exports', f'{VIEW}.surveyforge.json')
EXPORT_MANIFEST = EXPORT + '.manifest.json'
FAST = os.environ.get('KISTI_TEST_FAST') == '1'

_ARXIV = re.compile(r'^(\d{4}\.\d{4,5}|[a-z\-]+(\.[A-Z]{2})?/\d{7})$')


class Skip(Exception):
    """전제 자산이 없어 검사할 수 없음 (실패가 아니다)."""


def _is_doi(i):
    return str(i).startswith('10.')


def _sha256(path, chunk=1 << 24):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(chunk), b''):
            h.update(blk)
    return h.hexdigest()


def _json(path):
    with open(path) as f:
        return json.load(f)


def _db_built():
    return os.path.exists(os.path.join(DB, 'build_manifest.json'))


def _id_formats_from_map(idmap):
    """build_manifest 에 id_formats 가 없을 때(view 차분 적용본) id map 에서 직접 센다."""
    f = {'arxiv': 0, 'doi': 0, 'other': 0}
    for i in idmap:
        f['doi' if _is_doi(i) else 'arxiv' if _ARXIV.match(str(i)) else 'other'] += 1
    return f


def _view_diff():
    """view 차분(v2 이후)이 적용된 스냅샷의 view_diff_manifest.json, 없으면 None."""
    p = os.path.join(DB, 'view_diff_manifest.json')
    return _json(p) if os.path.exists(p) else None


def _require_db():
    if not _db_built():
        raise Skip(f'{DB}/build_manifest.json 없음 — 스냅샷 빌드 전')


def _view_manifest():
    return _json(os.path.join(VIEW_DIR, 'view_manifest.json'))


def _export_manifest():
    return _json(EXPORT_MANIFEST)


def _paper_ids_table():
    import pyarrow.parquet as pq
    return pq.read_table(os.path.join(VIEW_DIR, 'paper_ids.parquet'))


# ------------------------------------------------------------------ 1. view / export
def test_1_view_files_present_and_manifests_consistent():
    for name in ('papers.parquet', 'paper_ids.parquet', 'authors.parquet', 'venue.parquet',
                 'exclude_ids.txt', 'exclude_keys.txt', 'view_manifest.json'):
        assert os.path.exists(os.path.join(VIEW_DIR, name)), f'view 파일 없음: {name}'
    assert os.path.exists(EXPORT), f'export 없음: {EXPORT}'
    assert os.path.exists(EXPORT_MANIFEST), f'export manifest 없음: {EXPORT_MANIFEST}'

    vm, em = _view_manifest(), _export_manifest()
    assert vm['view_name'] == VIEW == em['view']['name']
    assert em['format'] == 'surveyforge'
    assert em['records'] == vm['counts']['view_papers'], \
        f"export {em['records']:,} != view {vm['counts']['view_papers']:,}"
    assert 'arXiv base id' in em['id_convention'], em['id_convention']
    assert em['citation_count_source'].startswith('KISTI'), em['citation_count_source']

    # export manifest 가 가리키는 view 파일 지문과 실제 파일이 같아야 한다 (4개 합쳐 약 800MB)
    for name, want in em['view']['files_sha256'].items():
        got = _sha256(os.path.join(VIEW_DIR, name))
        assert got == want, f'{name} sha256 불일치: {got[:12]} != {want[:12]}'

    t = _paper_ids_table()
    assert t.num_rows == vm['counts']['view_papers']
    ids = t.column('id').to_pylist()
    n_doi = sum(1 for i in ids if _is_doi(i))
    n_arxiv = sum(1 for i in ids if _ARXIV.match(str(i)))
    assert n_arxiv == vm['counts']['arxiv_id_papers'], (n_arxiv, vm['counts']['arxiv_id_papers'])
    assert n_doi + n_arxiv == t.num_rows, f'형식 불명 id {t.num_rows - n_doi - n_arxiv}건'
    assert len(set(ids)) == len(ids), 'view 안에 중복 id'
    print(f'    view {t.num_rows:,}편: arXiv {n_arxiv:,} · DOI {n_doi:,}; 4개 parquet sha256 일치')


def test_1b_export_file_sha256_matches_manifest():
    if FAST:
        raise Skip('KISTI_TEST_FAST=1 — 2.38GB export 해시 생략')
    em = _export_manifest()
    got = _sha256(EXPORT)
    assert got == em['file_sha256'], f'export file_sha256 불일치: {got[:12]} != {em["file_sha256"][:12]}'
    print(f'    export file_sha256 {got[:12]}… 일치')


# ------------------------------------------------------------------ 2. snapshot
def test_2_build_manifest_matches_export_and_view():
    _require_db()
    bm, em, vm = _json(os.path.join(DB, 'build_manifest.json')), _export_manifest(), _view_manifest()
    assert bm['records'] == em['records'], (bm['records'], em['records'])
    assert bm['export_file_sha256'] == em['file_sha256'], '빌드에 쓴 export 가 현재 export 와 다르다'
    # 차분 적용본(index_diff.py)은 export 를 상대경로로 적는다 -- 파일명만 대조한다
    assert os.path.basename(bm['export']) == os.path.basename(EXPORT), bm['export']
    # id_formats 는 원 빌더만 쓴다. 없으면 id map 에서 직접 센다 (불변식은 같다)
    f = bm.get('id_formats') or _id_formats_from_map(_json(os.path.join(DB, 'arxivid_to_index_abs.json')))
    assert f['arxiv'] == vm['counts']['arxiv_id_papers'], (f, vm['counts']['arxiv_id_papers'])
    assert f['doi'] == vm['counts']['view_papers'] - vm['counts']['arxiv_id_papers'], f
    assert f['other'] == 0, f
    copy = _json(os.path.join(DB, 'corpus_export_manifest.json'))
    assert copy == em, 'DB 옆에 복사된 export manifest 가 원본과 다르다'
    assert bm.get('text_normalization', 'none').startswith('none'), bm['text_normalization']
    vd = _view_diff()
    if vd:
        assert vd['v2_records'] == bm['records'] == vd['v1_records'] - vd['removed_count'] + vd['added_count'], vd
        print(f"    view diff 적용본: {vd['created_at']} v1 {vd['v1_records']:,} → v2 {vd['v2_records']:,} (-{vd['removed_count']} +{vd['added_count']})")
    print(f"    build {bm['built_at']} tag {bm['tag']} records {bm['records']:,} id_formats {f}")


def test_2b_db_files_and_id_map():
    _require_db()
    from src.utils import find_index
    abs_idx = find_index(DB, 'faiss_paper_title_abs_embeddings')   # glob 이 정확히 1개일 때만 통과
    title_idx = find_index(DB, 'faiss_paper_title_embeddings')
    for name in ('arxiv_paper_db_with_cc.json', 'arxivid_to_index_abs.json',
                 'surveys_arxiv_paper_db.json', 'surveys_arxivid_to_index_abs.json'):
        assert os.path.exists(os.path.join(DB, name)), f'DB 파일 없음: {name}'
    assert find_index(DB, 'faiss_survey_title_abs_embeddings') and find_index(DB, 'faiss_survey_title_embeddings')

    bm = _json(os.path.join(DB, 'build_manifest.json'))
    n = bm['records']
    idmap = _json(os.path.join(DB, 'arxivid_to_index_abs.json'))
    assert len(idmap) == n, (len(idmap), n)
    vals = idmap.values()
    assert min(vals) == 1 and max(vals) == n and len(set(vals)) == n, 'id map 값이 1..n 전단사가 아니다'
    n_doi = sum(1 for i in idmap if _is_doi(i))
    vm = _view_manifest()
    assert n_doi == vm['counts']['view_papers'] - vm['counts']['arxiv_id_papers'], (n_doi, vm['counts'])
    # export 사본이어야 한다 (파일 지문 = export)
    if not FAST:
        assert _sha256(os.path.join(DB, 'arxiv_paper_db_with_cc.json')) == bm['export_file_sha256']
    print(f'    id map {n:,} (DOI {n_doi:,}), 인덱스 {os.path.basename(abs_idx)} / {os.path.basename(title_idx)}')


# ------------------------------------------------------------------ 3. leak
def _exclude_ids():
    with open(os.path.join(VIEW_DIR, 'exclude_ids.txt')) as f:
        return [l.split('\t')[0].strip() for l in f if l.strip()]


def test_3_excluded_keys_absent_from_snapshot():
    _require_db()
    ex = _exclude_ids()
    assert len(ex) >= 30, f'exclude_ids.txt 가 너무 짧다: {len(ex)}'
    idmap = _json(os.path.join(DB, 'arxivid_to_index_abs.json'))
    leaked = [i for i in ex if i in idmap]
    assert not leaked, f'GT/twin id 가 DB 에 있다: {leaked}'
    vd = _view_diff()
    if vd:
        # 차분으로 뺀 id 도 DB 에 남아 있으면 안 된다
        still = [i for i in vd.get('removed_ids', []) if i in idmap]
        assert not still, f'view diff 가 뺀 id 가 DB 에 남아 있다: {still[:5]}'
        print(f"    view diff 제거 {len(vd.get('removed_ids', []))}개 DB 부재 확인")
    print(f'    제외 키 {len(ex)}개 모두 DB 에 없음')


def test_3b_twin_arxiv_ids_in_outline_db_exclude_list():
    """outline DB(human survey, arXiv 키)는 view 밖 자산이라 .env 의 제외 목록이 유일한 방어선이다."""
    twins = [i for i in _exclude_ids() if not _is_doi(i)]
    env_path = os.path.join(ROOT, '.env')
    if not os.path.exists(env_path):
        raise Skip('.env 없음')
    listed = set()
    for line in open(env_path):
        if line.startswith('SURVEYFORGE_SURVEY_EXCLUDE_IDS='):
            listed = {v.strip().split('v')[0] for v in line.split('=', 1)[1].split(',') if v.strip()}
    missing = [t for t in twins if t.split('v')[0] not in listed]
    assert not missing, f'twin arXiv id 가 SURVEYFORGE_SURVEY_EXCLUDE_IDS 에 없다: {missing}'
    print(f'    twin arXiv id {len(twins)}개 모두 .env 제외 목록({len(listed)}개)에 있음')


# ------------------------------------------------------------------ 4. id → DOI → full text
def test_4_ids_resolve_to_doi_and_fulltext_via_kisti_adapter():
    sys.path.insert(0, os.path.join(KISTI, 'adapter'))
    from common.fulltext import FullText  # env 독립: sqlite3 + zlib 만 쓴다
    t = _paper_ids_table().to_pandas()
    arxiv_row = t[~t['id'].str.startswith('10.')].iloc[0]
    doi_row = t[t['id'].str.startswith('10.')].iloc[0]
    assert doi_row['doi'] == doi_row['id'], 'DOI id 는 doi 컬럼과 같아야 한다'
    assert arxiv_row['doi'] == f"10.48550/arxiv.{arxiv_row['id']}", arxiv_row.to_dict()
    ft = FullText()
    for row in (arxiv_row, doi_row):
        text = ft.get(row['id'])
        assert isinstance(text, str) and len(text) > 500, f"원문 없음/짧음: {row['id']} -> {None if text is None else len(text)}"
    assert ft.get('no-such-id-000') is None
    print(f"    {arxiv_row['id']} → {arxiv_row['doi']} 원문 {len(ft.get(arxiv_row['id'])):,}자; "
          f"{doi_row['id']} 원문 {len(ft.get(doi_row['id'])):,}자")


# ------------------------------------------------------------------ 5. embedding query
def test_5_query_corpus_with_gte_and_faiss():
    _require_db()
    if FAST:
        raise Skip('KISTI_TEST_FAST=1 — 인덱스 13GB 읽기·gte 로드 생략')
    import faiss
    import numpy as np
    import torch
    import pyarrow.parquet as pq
    from sentence_transformers import SentenceTransformer
    from src.utils import find_index

    idmap = _json(os.path.join(DB, 'arxivid_to_index_abs.json'))
    pos2id = {v: k for k, v in idmap.items()}
    model = SentenceTransformer(os.path.join(DATA, 'gte-large-en-v1.5'), trust_remote_code=True)
    model.to(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))

    papers = pq.read_table(os.path.join(VIEW_DIR, 'papers.parquet'), columns=['id', 'title', 'year']).to_pandas()
    papers = papers.set_index('id')
    pick_arxiv = next(i for i in idmap if not _is_doi(i))
    pick_doi = next(i for i in idmap if _is_doi(i))

    # (a) 제목 인덱스: 제목으로 자기 자신이 1위 (인용 정합 단계가 기대하는 성질)
    title_index = faiss.read_index(find_index(DB, 'faiss_paper_title_embeddings'))
    assert title_index.ntotal == len(idmap)
    q = model.encode([papers.loc[pick_arxiv, 'title'], papers.loc[pick_doi, 'title']],
                     normalize_embeddings=True).astype('float32')
    scores, ids = title_index.search(q, 1)
    got = [pos2id[int(i)] for i in ids[:, 0]]
    assert got == [pick_arxiv, pick_doi], f'제목 자기-검색 실패: {got} (cos {scores[:, 0]})'
    assert scores.min() > 0.99, scores
    del title_index

    # (b) 초록 인덱스: 주제 질의 → DOI·arXiv 가 섞여 나오고 연도 ≤ 2025
    abs_index = faiss.read_index(find_index(DB, 'faiss_paper_title_abs_embeddings'))
    assert abs_index.ntotal == len(idmap)
    q = model.encode(['adversarial patches and physical-world attacks on object detectors',
                      'instruction tuning of large language models with human feedback'],
                     normalize_embeddings=True).astype('float32')
    _, ids = abs_index.search(q, 50)
    for row, query in zip(ids, ('adversarial', 'instruction')):
        hits = [pos2id[int(i)] for i in row]
        n_doi = sum(1 for h in hits if _is_doi(h))
        assert 0 < n_doi < len(hits), f'{query}: top-50 이 한 형식뿐이다 (DOI {n_doi}/{len(hits)})'
        years = [int(papers.loc[h, 'year']) for h in hits]
        assert max(years) <= 2025 and min(years) >= 1922, (min(years), max(years))
        print(f'    "{query}…" top-50: DOI {n_doi} · arXiv {len(hits) - n_doi}, 연도 {min(years)}..{max(years)}')


if __name__ == '__main__':
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith('test_') or not callable(fn):
            continue
        try:
            fn()
            print(f'PASS  {name}')
        except Skip as e:
            print(f'SKIP  {name}: {e}')
        except AssertionError as e:
            failures += 1
            print(f'FAIL  {name}: {e}')
        except Exception as e:  # noqa: BLE001 — 예외도 실패로 센다
            failures += 1
            print(f'ERROR {name}: {type(e).__name__}: {e}')
    print(f'\n{failures} failure(s)')
    sys.exit(1 if failures else 0)
