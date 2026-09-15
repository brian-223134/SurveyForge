"""topic 별 retrieval cutoff 가 SurveyForge 의 검색 경로에 제대로 걸리는지 (2026-09-14 규약, docs/retrieval-policy.md).

판정 규칙 자체는 kisti_data 공통 모듈(adapter/common/retrieval_policy.py)의 몫이고 AutoSurvey 쪽 테스트가 경계를 덮는다.
여기서 보는 것은 SurveyForge 가 그 규칙을 **어디에, 어떻게** 붙였는가:

  1. 판정 위임 -- sidecar 날짜(day/month/year/없음)·exclude_ids 가 is_allowed 로 그대로 통한다
  2. db_view -- DB 매핑 순서 보존, 인덱스 id 변환, 제외 사유 집계, 지문(AutoSurvey fingerprint 와 같은 식)
  3. 선택자 검색 -- IndexIDMap(IndexFlatIP) + IDSelectorBatch 로 k > 허용 편수여도 허용분만 돌아온다 (사후 필터가 아니라는 증거)
     · utils.get_index_filter_by_policy(게이트 ∩ 허용) · database 방식의 SearchParameters(sel=…) 둘 다
  4. outline DB 규칙 -- arXiv id 의 YYMM(월 상한) < cutoff, base id 제외, DOI/형식 불명 불허
  5. 실제 정책 파일·sidecar -- physical-adversarial-attacks 허용 1,186,466 / kv-cache-serving 1,663,704 (AutoSurvey 와 동일),
     topic 문자열 불일치·needs_review·미지 slug 거부, 'none' 은 정책 없음
  6. main.validate_cutoffs 가 topic_id 없는 실행을 DB 로드 전에 거부한다

    cd code && ../.venv/bin/python ../tests/test_retrieval_policy.py
    cd code && ../.venv/bin/python -m pytest ../tests/test_retrieval_policy.py -q
"""
import argparse
import os
import sys
import types

import faiss
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
sys.path.insert(0, os.path.join(ROOT, 'code'))

from src import retrieval_policy as sfp          # noqa: E402
from src.utils import get_index_filter_by_policy, get_retrieval_filter, filter_arxivids_by_prefix  # noqa: E402


class Skip(Exception):
    pass


def _policy(cutoff='2022-11-03', exclude=('10.1145/3793659', '2211.01671'), dates=None):
    row = {'topic_id': 't', 'topic': 'T', 'retrieval_cutoff_at': cutoff, 'exclude_ids': list(exclude),
           'status': 'ok', 'gt_first_public_source': 'test'}
    dates = dates if dates is not None else {
        '2210.17140': '2022-10',            # month, 상한 10-31 < cutoff → 허용
        '2211.00001': '2022-11',            # month, 상한 11-30 ≥ cutoff → 제외
        '10.1/a': '2022-11-02',             # day, 전날 → 허용
        '10.1/b': '2022-11-03',             # day, 당일 → 제외
        '10.1/c': '2021',                   # year, 12-31 < cutoff → 허용
        '10.1/d': '2022',                   # year, 12-31 ≥ cutoff → 제외
        '10.1145/3793659': '2020-01-01',    # 제외 id (날짜는 허용 범위)
        '2211.01671': '2022-11',            # 제외 id
        'cs/0503039': '2005-03',            # 구형 arXiv
    }
    return sfp.RetrievalPolicy(row, os.path.join(HERE, 'nonexistent.jsonl'), dates, {'view': 'fake'}, '/dev/null')


# ------------------------------------------------------------------ 1. 판정 위임
def test_1_is_allowed_delegates_upper_bound_rule():
    p = _policy()
    assert p.is_allowed('2210.17140') and p.is_allowed('10.1/a') and p.is_allowed('10.1/c') and p.is_allowed('cs/0503039')
    assert not p.is_allowed('2211.00001') and not p.is_allowed('10.1/b') and not p.is_allowed('10.1/d')
    assert not p.is_allowed('10.1145/3793659') and not p.is_allowed('2211.01671'), '제외 id 는 날짜와 무관하게 차단'
    assert not p.is_allowed('no-such-id'), '날짜 없음은 제외'
    assert p.allowed_ids() == {'2210.17140', '10.1/a', '10.1/c', 'cs/0503039'}
    s = p.summary()
    assert s['allowed'] == 4 and s['excluded']['exclude_id'] == 2
    assert s['excluded']['after_cutoff_month'] == 1 and s['excluded']['after_cutoff_day'] == 1 and s['excluded']['after_cutoff_year'] == 1
    print(f"    허용 {s['allowed']}/{s['total']} 제외 {s['excluded']}")


# ------------------------------------------------------------------ 2. db_view
def test_2_db_view_preserves_order_and_counts():
    p = _policy()
    mapping = {'10.1/d': 1, '2210.17140': 2, 'unknown-id': 3, '10.1145/3793659': 4, '10.1/a': 5, 'cs/0503039': 6}
    v = p.db_view(mapping)
    assert v['kept'] == ['2210.17140', '10.1/a', 'cs/0503039'], v['kept']          # DB 순서 그대로
    assert v['index_ids'] == [2, 5, 6]
    assert v['n_db'] == 6 and v['n_allowed'] == 3 and v['n_excluded_id'] == 1 and v['n_no_date'] == 1 and v['n_after_cutoff'] == 1
    assert v['excluded_present'] == ['10.1145/3793659']
    assert v['fingerprint'] == sfp.fingerprint(['10.1/a', '2210.17140', 'cs/0503039'])
    assert p.db_view(mapping) is v, '같은 매핑은 한 번만 계산'
    m = p.manifest(mapping)
    assert m['allowed'] == 3 and m['allowed_fingerprint_sha256'] == v['fingerprint'] and m['retrieval_cutoff_at'] == '2022-11-03'
    assert m['exclude_ids'] == ['10.1145/3793659', '2211.01671'] and m['excluded_ids_present_in_db'] == ['10.1145/3793659']
    print(f"    kept {v['kept']} idx {v['index_ids']} sha {v['fingerprint'][:12]}")


def test_2b_fingerprint_matches_autosurvey_formula():
    p = os.path.join(ROOT, os.pardir, 'AutoSurvey', 'src')
    if not os.path.exists(os.path.join(p, 'retrieval_policy.py')):
        raise Skip('AutoSurvey/src/retrieval_policy.py 없음')
    import importlib.util
    spec = importlib.util.spec_from_file_location('as_rp', os.path.join(p, 'retrieval_policy.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ids = ['2210.17140', '10.1/a', 'cs/0503039', '10.1145/x']
    assert sfp.fingerprint(ids) == mod.fingerprint(ids) == sfp.fingerprint(reversed(ids))
    print('    fingerprint == AutoSurvey.fingerprint')


# ------------------------------------------------------------------ 3. 선택자 검색
def _fake_index(n=120, dim=8, seed=0):
    rng = np.random.default_rng(seed)
    vec = rng.standard_normal((n, dim)).astype('float32')
    faiss.normalize_L2(vec)
    idx = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
    idx.add_with_ids(vec, np.arange(1, n + 1, dtype='int64'))     # 1-based stored id (스냅샷 불변식)
    return idx, vec


def test_3_selector_search_returns_only_allowed_even_when_k_exceeds():
    idx, vec = _fake_index()
    n = idx.ntotal
    # id: 절반 arXiv(2019~2023 월), 절반 DOI(연/일). cutoff 2021-06-15
    ids, dates = [], {}
    for i in range(1, n + 1):
        if i % 2:
            yymm = f'{19 + (i % 5):02d}{1 + (i % 12):02d}'
            pid = f'{yymm}.{i:05d}'
            dates[pid] = f'20{yymm[:2]}-{yymm[2:]}'
        else:
            pid = f'10.9/{i}'
            dates[pid] = '2020' if i % 4 else '2021-06-15'
        ids.append(pid)
    mapping = {pid: i for i, pid in enumerate(ids, start=1)}
    p = _policy(cutoff='2021-06-15', exclude=(ids[0],), dates=dates)
    v = p.db_view(mapping)
    allowed_idx = set(v['index_ids'])
    assert 0 < len(allowed_idx) < n

    # (a) utils 경로 -- 게이트 ∩ 허용 → IDSelectorBatch. k = 전체보다 크게 줘도 허용분만
    flt = get_index_filter_by_policy(mapping, p, '2612', stage='test', saving_path=None)
    q = vec[:1]
    from src.faiss_param import FAISS_param  # 파이프라인이 쓰는 검색 경로와 같은 호출
    D, I = idx.search(q, n + 10, params=faiss.SearchParametersIVF(sel=flt['id_selector']))
    got = [int(i) for i in I[0] if i != -1]
    assert got and set(got) <= allowed_idx and len(got) == len(allowed_idx), (len(got), len(allowed_idx))
    # 사후 필터였다면: 전체 top-k 의 허용분은 선택자 결과의 접두어. 여기서는 선택자 결과가 허용 집합 안의 정확한 순위여야 한다
    D0, I0 = idx.search(q, n)
    ref = [int(i) for i in I0[0] if int(i) in allowed_idx]
    assert got == ref, '선택자 검색은 허용 집합 안의 정확한 top-k 순서'

    # (b) database.py 경로 -- SearchParameters(sel=IDSelectorBatch) on IndexIDMap
    sel = faiss.IDSelectorBatch(np.asarray(v['index_ids'], dtype='int64'))
    D, I = idx.search(q, 30, params=faiss.SearchParameters(sel=sel))
    got = [int(i) for i in I[0] if i != -1]
    assert got == ref[:30]

    # (c) id 게이트 교집합: 게이트를 2001 로 두면 arXiv 20xx 중 2001 초과는 빠지고 DOI 는 통과
    flt2 = get_index_filter_by_policy(mapping, p, '2001', stage='test-gate', saving_path=None)
    D, I = idx.search(q, n, params=faiss.SearchParametersIVF(sel=flt2['id_selector']))
    got2 = {ids[int(i) - 1] for i in I[0] if i != -1}
    assert all(not g[:4].isdigit() or g[:4] <= '2001' for g in got2)
    assert got2 == set(filter_arxivids_by_prefix(v['kept'], '2001'))
    print(f'    허용 {len(allowed_idx)}/{n}, 선택자 top-k == 허용 집합 안의 정확한 순위 (k={n + 10}), 게이트 교집합 {len(got2)}')


def test_3b_get_retrieval_filter_dispatches_on_policy():
    mapping = {'2210.17140': 1, '2211.00001': 2, '10.1/a': 3}
    args = types.SimpleNamespace(paper_id_cutoff='2612', saving_path=None, retrieval_policy=None)
    flt = get_retrieval_filter(mapping, args, stage='t')
    assert 'id_selector' in flt and flt['id_selector'].is_member(2), '정책 없음: 게이트만 (2211 ≤ 2612 통과)'
    args.retrieval_policy = _policy()
    flt = get_retrieval_filter(mapping, args, stage='t')
    assert flt['id_selector'].is_member(1) and flt['id_selector'].is_member(3) and not flt['id_selector'].is_member(2)
    print('    정책 없음 → 게이트, 정책 있음 → 허용 집합')


# ------------------------------------------------------------------ 4. outline DB 규칙
def test_4_outline_db_rule_uses_arxiv_month_and_base_id():
    p = _policy(cutoff='2023-08-21', exclude=('2308.10792',))
    assert p.allows_arxiv_id('2307.01234v3'), '2023-07 상한 07-31 < 08-21'
    assert not p.allows_arxiv_id('2308.00001v1'), '2023-08 상한 08-31 ≥ 08-21 (당월 제외)'
    assert not p.allows_arxiv_id('2308.10792v5'), 'base id 가 제외 목록'
    assert p.allows_arxiv_id('cs/0503039v2') and not p.allows_arxiv_id('10.1145/3777411') and not p.allows_arxiv_id('junk')
    print('    월 상한·base id 제외·비-arXiv 불허 OK')


# ------------------------------------------------------------------ 5. 실제 정책 파일 + sidecar
def test_5_real_policy_file_and_sidecar():
    path = sfp.default_policy_path()
    if not os.path.exists(path) or not os.path.exists(sfp.default_paper_dates_path()):
        raise Skip(f'정책 파일/sidecar 없음: {path} / {sfp.default_paper_dates_path()}')
    assert sfp.load_retrieval_policy('') is None and sfp.load_retrieval_policy('none') is None
    p = sfp.load_retrieval_policy('physical-adversarial-attacks')
    assert p.cutoff == '2022-11-03' and p.topic == 'Visual Adversarial Attacks and Defenses in the Physical World'
    s = p.summary()
    assert s['allowed'] == 1186466, s      # AutoSurvey docs/retrieval-policy.md §8-2 와 동일해야 한다
    assert s['total'] == 1663704 and s['excluded'].get('no_date', 0) == 0
    assert p.sidecar_meta.get('view') == 'kisti-2608' and str(p.sidecar_meta.get('view_papers_sha256')).startswith('c1a0c6b3')
    k = sfp.load_retrieval_policy('kv-cache-serving')
    assert k.summary()['allowed'] == 1663704 and k.cutoff == '2026-07-01'
    assert sfp.topic_title('kv-cache-serving') == k.topic
    for bad, exc in ((dict(topic_id='no-such-topic'), KeyError),
                     (dict(topic_id='physical-adversarial-attacks', topic='Wrong Title'), RuntimeError)):
        try:
            sfp.load_retrieval_policy(**bad)
        except exc:
            pass
        else:
            raise AssertionError(f'{bad} 가 거부되지 않았다')
    print(f"    physical-adversarial 허용 {s['allowed']:,}/{s['total']:,} · kv-cache 허용 {k.summary()['allowed']:,} · 불일치 거부 OK")


# ------------------------------------------------------------------ 6. main 이 topic_id 없는 실행을 거부
def test_6_main_refuses_run_without_topic_id():
    import main as sf_main
    base = dict(paper_id_cutoff='2612', paper_date_oldest='1922-01-01', paper_date_newest='2026-12-31')
    try:
        sf_main.validate_cutoffs(argparse.Namespace(topic_id='', **base))
    except SystemExit as e:
        assert 'topic_id' in str(e)
    else:
        raise AssertionError('topic_id 없이 통과했다')
    sf_main.validate_cutoffs(argparse.Namespace(topic_id='none', **base))
    sf_main.validate_cutoffs(argparse.Namespace(topic_id='physical-adversarial-attacks', **base))
    print("    빈 topic_id 거부, 'none'·slug 통과")


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
        except Exception as e:  # noqa: BLE001
            failures += 1
            import traceback; traceback.print_exc()
            print(f'ERROR {name}: {type(e).__name__}: {e}')
    print(f'\n{failures} failure(s)')
    sys.exit(1 if failures else 0)
