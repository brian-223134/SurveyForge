"""LLM 호출 없이 검색 스택을 띄워 스냅샷과 **topic 정책**이 실행 경로에서 제대로 걸리는지 본다. 비용 0.

확인하는 것 (docs/retrieval-policy.md §검증):
  1. 기동: main.py 와 같은 방식으로 RAG(abs·title)·TinyDB·outline DB 를 올리고 [cutoff/db] 보고를 찍는다.
  2. 정책: SURVEYFORGE_TOPIC_ID 와 같은 경로(src/retrieval_policy)로 허용 집합을 만든다 -- sidecar 허용 편수가
     AutoSurvey 와 같은지(--expect_allowed slug=N), DB 허용 편수·지문.
  3. 검색 경로 전부에서 반환 id 가 허용 집합 안인지: 아웃라인 풀(top_k) · 서브아웃라인식 검색(50) · 집필 풀 잠금 +
     citation 리랭크(TRE) · 인용 정합(title 인덱스, 풀 잠금 ∩ 허용) · outline DB(human survey, YYMM 규칙) ·
     TinyDB 직접 조회(허용 밖 id 차단). 각 id 의 sidecar 날짜 상한 < cutoff, 제외 id 0건.
  4. 2026년 cutoff topic(예: kv-cache-serving)에서는 2026년 문헌이 실제로 검색되는지 (--expect_2026 slug).

사용 (.env 의 SURVEYFORGE_DB_DIR · 컷오프 3종을 그대로 읽는다; 정책 없이 보려면 --topic_id 를 빼고 --topic 을 준다):
    cd code && CUDA_VISIBLE_DEVICES=6 ../.venv/bin/python ../scripts/probe_retrieval.py \
        --topic_id physical-adversarial-attacks --expect_allowed physical-adversarial-attacks=1186466 \
        --topic_id kv-cache-serving --expect_allowed kv-cache-serving=1663704 --expect_2026 kv-cache-serving \
        --out ../eval_out/probe_policy.json
"""

import argparse
import collections
import json
import os
import sys
import time

CODE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'code')
sys.path.insert(0, CODE)
os.chdir(CODE)

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(CODE, os.pardir, '.env'))

from main import report_cutoffs_vs_database  # noqa: E402
from src.rag import GeneralRAG_langchain  # noqa: E402
from src.database import database, database_survey  # noqa: E402
from src.retrieval_policy import load_retrieval_policy  # noqa: E402
from src.utils import find_index, get_index_filter, get_retrieval_filter  # noqa: E402


def main():
    data_root = os.environ.get('SURVEYFORGE_DATA', '/data2/chanjoong/survey-agent/SurveyForge_data')
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--topic_id', action='append', default=[],
                    help='정책 파일의 slug (반복 가능). 제목은 정책 행에서 푼다')
    ap.add_argument('--topic', default='', help='정책 없이 볼 때의 topic 문자열')
    ap.add_argument('--expect_allowed', action='append', default=[], metavar='SLUG=N',
                    help='sidecar 허용 편수 기대값 (AutoSurvey docs/retrieval-policy.md §8-2)')
    ap.add_argument('--expect_2026', action='append', default=[], metavar='SLUG',
                    help='아웃라인 풀에 2026년 문헌이 1편 이상 있어야 하는 topic')
    ap.add_argument('--db_path', default=os.path.join(
        data_root, os.environ.get('SURVEYFORGE_DB_DIR', 'database')))
    ap.add_argument('--embedding_model', default=os.path.join(data_root, 'gte-large-en-v1.5'))
    ap.add_argument('--top_k', type=int, default=1500, help='아웃라인 단계 풀 크기')
    ap.add_argument('--rag_num', type=int, default=100)
    ap.add_argument('--rag_max_out', type=int, default=60)
    ap.add_argument('--paper_id_cutoff', default=os.environ.get('SURVEYFORGE_PAPER_ID_CUTOFF', '2612'))
    ap.add_argument('--paper_date_oldest', default=os.environ.get('SURVEYFORGE_PAPER_DATE_OLDEST', '1922-01-01'))
    ap.add_argument('--paper_date_newest', default=os.environ.get('SURVEYFORGE_PAPER_DATE_NEWEST', '2026-12-31'))
    ap.add_argument('--topic_policy', default=os.environ.get('SURVEYFORGE_TOPIC_POLICY', ''))
    ap.add_argument('--paper_dates', default=os.environ.get('SURVEYFORGE_PAPER_DATES', ''))
    ap.add_argument('--skip_paper_db', action='store_true', help='TinyDB(직접 조회)·자체 인덱스 로드 생략')
    ap.add_argument('--skip_title_index', action='store_true', help='인용 정합용 title 인덱스 로드 생략')
    ap.add_argument('--saving_path', default='', help='기본: 스크래치 디렉터리에 probe 로그')
    ap.add_argument('--out', default='', help='결과 JSON 경로 (선택)')
    args = ap.parse_args()
    args.debug = False
    args.retrieval_policy = None
    if not args.saving_path:
        args.saving_path = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'surveyforge_probe')
    os.makedirs(args.saving_path, exist_ok=True)
    if not args.topic_id and not args.topic:
        ap.error('--topic_id 또는 --topic 이 필요하다')
    expect_allowed = {}
    for kv in args.expect_allowed:
        k, v = kv.split('=', 1)
        expect_allowed[k] = int(v.replace(',', ''))

    print(f'[probe] db_path={args.db_path}')
    t0 = time.time()
    abs_index = find_index(args.db_path, 'faiss_paper_title_abs_embeddings')
    doc_db = f'{args.db_path}/arxiv_paper_db_with_cc.json'
    id_map = f'{args.db_path}/arxivid_to_index_abs.json'
    rag = GeneralRAG_langchain(args=args, retriever_type='vectorstore', index_db_path=abs_index,
                               doc_db_path=doc_db, arxivid_to_index_path=id_map,
                               embedding_model=args.embedding_model)
    rag_title = None
    if not args.skip_title_index:
        rag_title = GeneralRAG_langchain(args=args, retriever_type='vectorstore',
                                         index_db_path=find_index(args.db_path, 'faiss_paper_title_embeddings'),
                                         doc_db_path=doc_db, arxivid_to_index_path=id_map,
                                         embedding_model=args.embedding_model)
    print(f'[probe] RAG loaded in {time.time() - t0:.0f}s')
    report_cutoffs_vs_database(args, rag)
    meta = {d.metadata['id']: d.metadata for d in rag.rag_data['doc_list']}

    def describe(ids, label, policy=None):
        doi = [i for i in ids if str(i).startswith('10.')]
        years = collections.Counter(str(meta[i]['date'])[:4] for i in ids if i in meta)
        top = sorted(years.items())
        print(f'[probe/{label}] {len(ids)} ids: DOI {len(doi)} · arXiv/other {len(ids) - len(doi)}; '
              f'years {top[0][0] if top else "-"}..{top[-1][0] if top else "-"}')
        print(f'[probe/{label}] year histogram (2018+): '
              + ' '.join(f'{y}:{c}' for y, c in top if y >= '2018'))
        for i in ids[:5]:
            m = meta.get(i, {})
            d = policy.date_of(i) if policy else str(m.get('date'))[:10]
            print(f'    {i:<28} {d!s:<10}  cc={m.get("citation_count")}  '
                  f'{" ".join(str(m.get("title", "")).split())[:70]}')
        return {'n': len(ids), 'doi': len(doi), 'years': dict(top)}

    def check_ids(ids, label, policy, res, fails):
        """정책 위반(허용 밖·제외 id·날짜 상한 ≥ cutoff) 개수와 2026년 문헌 수를 res 에 적고 위반이면 fails 에 넣는다."""
        rp = policy._rp
        cutoff = rp.parse_day(policy.cutoff)
        bad_allowed = [i for i in ids if not policy.is_allowed(i)]
        bad_excl = [i for i in ids if policy.is_excluded(i)]
        bad_date = [i for i in ids if (lambda ub: ub is None or ub >= cutoff)(rp.upper_bound(policy.date_of(i)))]
        latest = max((policy.date_of(i) for i in ids if policy.date_of(i)), default=None)
        n2026 = sum(1 for i in ids if str(policy.date_of(i)).startswith('2026'))
        res[label] = {'n': len(ids), 'violations_not_allowed': len(bad_allowed), 'violations_exclude_id': len(bad_excl),
                      'violations_date_upper_bound': len(bad_date), 'latest_allowed_date': latest, 'n_2026': n2026}
        print(f'[probe/{label}] 정책 검사: 허용 밖 {len(bad_allowed)} · 제외 id {len(bad_excl)} · 날짜 상한 위반 {len(bad_date)} '
              f'· 가장 늦은 날짜 {latest} · 2026년 {n2026}편')
        if bad_allowed or bad_excl or bad_date:
            fails.append(f'{label}: not_allowed {bad_allowed[:5]} exclude {bad_excl[:5]} date {bad_date[:5]}')

    results, fails = {'db_path': os.path.abspath(args.db_path), 'topics': {}}, []
    topics = [(tid, None) for tid in args.topic_id] or [(None, args.topic)]
    paper_db = survey_db = None
    for topic_id, topic in topics:
        policy = load_retrieval_policy(topic_id, args.topic_policy or None, args.paper_dates or None) if topic_id else None
        args.retrieval_policy = policy
        rag.window_drops = rag.window_docs = 0
        if policy is not None:
            topic = policy.topic
            for line in policy.log_lines(policy.db_view(rag.id_to_index)):
                print(line)
        print(f'\n[probe] ===== topic_id={topic_id} topic={topic!r} =====')
        res = {'topic': topic, 'checks': {}}
        results['topics'][topic_id or topic] = res
        if policy is not None:
            s = policy.summary()
            res['policy'] = {'cutoff': policy.cutoff, 'sidecar_allowed': s['allowed'], 'sidecar_total': s['total'],
                             'sidecar_excluded': s['excluded'], 'db_allowed': policy.db_view(rag.id_to_index)['n_allowed'],
                             'db_records': policy.db_view(rag.id_to_index)['n_db'],
                             'allowed_fingerprint_sha256': policy.db_view(rag.id_to_index)['fingerprint'],
                             'exclude_ids': policy.exclude_ids}
            want = expect_allowed.get(topic_id)
            if want is not None and want != s['allowed']:
                fails.append(f'{topic_id}: sidecar 허용 {s["allowed"]:,} != 기대 {want:,}')
            print(f"[probe/policy] sidecar 허용 {s['allowed']:,} (기대 {want}) · DB 허용 {res['policy']['db_allowed']:,}/"
                  f"{res['policy']['db_records']:,} · sha256 {res['policy']['allowed_fingerprint_sha256'][:16]}…")

        # 1. 아웃라인 풀 -- outline_writer.draft_outline 과 같은 호출 (정책이 있으면 허용 집합 ∩ 게이트, 없으면 게이트)
        t1 = time.time()
        flt = get_retrieval_filter(rag.id_to_index, args, stage='probe-outline')
        pool = rag.retrieve_id(topic, top_k=args.top_k, **flt)
        print(f'[probe] outline retrieval {time.time() - t1:.0f}s')
        res['outline_pool'] = describe(pool, 'outline', policy)
        if policy is not None:
            check_ids(pool, 'outline', policy, res['checks'], fails)
            if topic_id in args.expect_2026 and res['checks']['outline']['n_2026'] == 0:
                fails.append(f'{topic_id}: 아웃라인 풀에 2026년 문헌이 없다')

        # 2. 서브아웃라인식 검색 -- generate_subsection_outlines_with_survey 와 같은 호출 (정책이 있을 때만 선택자)
        sub_flt = flt if policy is not None else {}
        sub = rag.retrieve_id([f'{topic}: recent methods, benchmarks and open problems'],
                              search_type='similarity', rerank='raw', top_k=50, **sub_flt)
        res['suboutline'] = describe(sub, 'suboutline', policy)
        if policy is not None:
            check_ids(sub, 'suboutline', policy, res['checks'], fails)

        # 3. 집필 단계 -- 1,500 풀에 잠근 뒤 citation 리랭크(TRE 창)
        lock = get_index_filter(rag.id_to_index, pool)
        t2 = time.time()
        top = rag.retrieve_id(topic, rerank='citation', top_k=args.rag_num, max_out=args.rag_max_out, **lock)
        print(f'[probe] citation rerank {time.time() - t2:.0f}s')
        res['rerank'] = describe(top, 'rerank', policy)
        rag.report_window_drops()
        res['window_drops'], res['window_docs'] = rag.window_drops, rag.window_docs
        if policy is not None:
            check_ids(top, 'rerank', policy, res['checks'], fails)

        # 4. 인용 정합 -- writer.replace_citations_with_numbers 와 같은 잠금(집필 id ∩ 허용) + title 인덱스 top-1
        if rag_title is not None:
            lock_ids = [i for i in top if policy.is_allowed(i)] if policy is not None else top
            titles = [' '.join(str(meta[i]['title']).split()) for i in top[:5]]
            cited = rag_title.retrieve_id4citation(titles, search_type='similarity', top_k=1,
                                                   **get_index_filter(rag_title.id_to_index, lock_ids))
            res['citation_map'] = {'queries': len(titles), 'self_hits': sum(1 for a, b in zip(top[:5], cited) if a == b)}
            print(f"[probe/citation] 제목 {len(titles)}건 → id {len(cited)}건, 자기 자신 적중 {res['citation_map']['self_hits']}")
            if policy is not None:
                check_ids(cited, 'citation', policy, res['checks'], fails)

        # 5. outline DB(human survey) -- database_survey 의 YYMM 규칙 + GT 제외
        if survey_db is None or policy is not None:
            survey_db = database_survey(db_path=args.db_path, embedding_model=args.embedding_model, policy=policy)
        sids = survey_db.get_ids_from_query(topic, num=20)
        info = {r['id']: r for r in survey_db.get_paper_info_from_ids(sids)}
        res['survey_db'] = {'n': len(sids), 'policy_report': survey_db.policy_report,
                            'dates': sorted(str(info[i]['date'])[:7] for i in sids if i in info)}
        print(f"[probe/survey-db] {len(sids)} surveys, 날짜(월) {res['survey_db']['dates'][:3]} .. {res['survey_db']['dates'][-3:]}")
        if policy is not None:
            bad = [i for i in sids if not policy.allows_arxiv_id(i)]
            envx = [i for i in sids if i.split('v')[0] in survey_db.exclude_base_ids]
            res['checks']['survey_db'] = {'n': len(sids), 'violations': len(bad), 'env_excluded_present': len(envx)}
            print(f'[probe/survey-db] 정책 검사: 위반 {len(bad)} · env 제외 id 출현 {len(envx)}')
            if bad or envx:
                fails.append(f'survey-db: {bad[:5]} env {envx[:5]}')

        # 6. TinyDB 직접 조회 -- database.get_paper_info_from_ids 가 허용 밖 id 를 차단하는지
        if not args.skip_paper_db and policy is not None:
            if paper_db is None or paper_db.policy is not policy:
                t3 = time.time()
                paper_db = database(db_path=args.db_path, embedding_model=args.embedding_model, policy=policy)
                print(f'[probe] paper database (TinyDB + 자체 인덱스) loaded in {time.time() - t3:.0f}s')
            v = policy.db_view(rag.id_to_index)
            after = next((i for i in rag.id_to_index if i in policy.dates and not policy.is_allowed(i)
                          and not policy.is_excluded(i)), None)
            probe_ids = [pool[0]] + ([after] if after else []) + policy.exclude_ids
            got = paper_db.get_paper_info_from_ids(probe_ids)
            got_ids = {r['id'] for r in got}
            own = paper_db.get_ids_from_query(topic, num=20)
            res['checks']['direct_lookup'] = {'asked': probe_ids, 'returned': sorted(got_ids),
                                              'own_search_violations': sum(1 for i in own if not policy.is_allowed(i))}
            print(f'[probe/lookup] 조회 {probe_ids} → 반환 {sorted(got_ids)} · 자체 검색 20건 위반 '
                  f"{res['checks']['direct_lookup']['own_search_violations']}")
            if got_ids != {pool[0]} or res['checks']['direct_lookup']['own_search_violations']:
                fails.append(f'direct lookup: returned {sorted(got_ids)} (expected only {pool[0]})')
            if v['excluded_present']:
                fails.append(f'exclude id present in DB index: {v["excluded_present"]}')

    results['fails'] = fails
    results['status'] = 'FAIL' if fails else 'PASS'
    print(f'\n[probe] ===== {results["status"]} =====')
    for f_ in fails:
        print(f'  - {f_}')
    if args.out:
        with open(args.out, 'w') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f'[probe] wrote {args.out}')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
