"""LLM 호출 없이 검색 스택만 띄워 스냅샷이 실행 경로에서 제대로 읽히는지 본다.

KISTI view(id 규칙 B)로 옮기면서 확인할 것 세 가지 -- 전부 비용 0:
  1. 기동: main.py 와 같은 방식으로 RAG 2종을 올리고 [cutoff/db] 보고를 찍는다
     (DOI id 수, 형식 불명 id 수, 날짜 범위).
  2. 아웃라인 단계 검색: topic 으로 top_k 편을 뽑아 arXiv/DOI 비율과 연도 분포를 본다.
  3. 집필 단계 리랭크: citation 리랭크(TRE 창)를 한 번 태워 창 밖 폐기가 0인지 본다.
     KISTI 는 날짜가 YYYY-01-01 이라 창 경계 동작을 실제로 확인해야 한다.

사용:
    cd code && CUDA_VISIBLE_DEVICES=4 ../.venv/bin/python ../scripts/probe_retrieval.py \
        --topic "Instruction Tuning for Large Language Models" [--db_path ...] [--top_k 1500]
    # .env 의 SURVEYFORGE_DB_DIR / 컷오프 3종을 그대로 읽는다.
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
from src.utils import find_index, get_index_filter_by_id_prefix  # noqa: E402


def main():
    data_root = os.environ.get('SURVEYFORGE_DATA', '/data2/chanjoong/survey-agent/SurveyForge_data')
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--topic', required=True)
    ap.add_argument('--db_path', default=os.path.join(
        data_root, os.environ.get('SURVEYFORGE_DB_DIR', 'database')))
    ap.add_argument('--embedding_model', default=os.path.join(data_root, 'gte-large-en-v1.5'))
    ap.add_argument('--top_k', type=int, default=1500, help='아웃라인 단계 풀 크기')
    ap.add_argument('--rag_num', type=int, default=100)
    ap.add_argument('--rag_max_out', type=int, default=60)
    ap.add_argument('--paper_id_cutoff', default=os.environ.get('SURVEYFORGE_PAPER_ID_CUTOFF', '2612'))
    ap.add_argument('--paper_date_oldest', default=os.environ.get('SURVEYFORGE_PAPER_DATE_OLDEST', '1991-01-01'))
    ap.add_argument('--paper_date_newest', default=os.environ.get('SURVEYFORGE_PAPER_DATE_NEWEST', '2026-01-01'))
    ap.add_argument('--saving_path', default='', help='기본: 스크래치 디렉터리에 probe 로그')
    ap.add_argument('--out', default='', help='결과 JSON 경로 (선택)')
    args = ap.parse_args()
    args.debug = False
    if not args.saving_path:
        args.saving_path = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'surveyforge_probe')
    os.makedirs(args.saving_path, exist_ok=True)

    print(f'[probe] db_path={args.db_path}')
    t0 = time.time()
    abs_index = find_index(args.db_path, 'faiss_paper_title_abs_embeddings')
    doc_db = f'{args.db_path}/arxiv_paper_db_with_cc.json'
    id_map = f'{args.db_path}/arxivid_to_index_abs.json'
    rag = GeneralRAG_langchain(args=args, retriever_type='vectorstore', index_db_path=abs_index,
                               doc_db_path=doc_db, arxivid_to_index_path=id_map,
                               embedding_model=args.embedding_model)
    print(f'[probe] RAG loaded in {time.time() - t0:.0f}s')

    report_cutoffs_vs_database(args, rag)
    meta = {d.metadata['id']: d.metadata for d in rag.rag_data['doc_list']}

    def describe(ids, label):
        doi = [i for i in ids if str(i).startswith('10.')]
        years = collections.Counter(str(meta[i]['date'])[:4] for i in ids if i in meta)
        top = sorted(years.items())
        print(f'[probe/{label}] {len(ids)} ids: DOI {len(doi)} · arXiv/other {len(ids) - len(doi)}; '
              f'years {top[0][0] if top else "-"}..{top[-1][0] if top else "-"}')
        print(f'[probe/{label}] year histogram (2018+): '
              + ' '.join(f'{y}:{c}' for y, c in top if y >= '2018'))
        for i in ids[:5]:
            m = meta.get(i, {})
            print(f'    {i:<28} {str(m.get("date"))[:10]}  cc={m.get("citation_count")}  '
                  f'{" ".join(str(m.get("title", "")).split())[:70]}')
        return {'n': len(ids), 'doi': len(doi), 'years': dict(top)}

    # 1. 아웃라인 단계: main.py/outline_writer.draft_outline 과 같은 호출
    t1 = time.time()
    flt = get_index_filter_by_id_prefix(rag.id_to_index, args.paper_id_cutoff,
                                        stage='probe-outline', saving_path=args.saving_path)
    pool = rag.retrieve_id(args.topic, top_k=args.top_k, **flt)
    print(f'[probe] outline retrieval {time.time() - t1:.0f}s')
    res = {'topic': args.topic, 'db_path': os.path.abspath(args.db_path),
           'outline_pool': describe(pool, 'outline')}

    # 2. 집필 단계 리랭크: citation 리랭크(TRE 창) -- writer.py 는 1500 풀에 잠그지만
    #    여기서는 창 동작만 본다.
    t2 = time.time()
    top = rag.retrieve_id(args.topic, rerank='citation', top_k=args.rag_num,
                          max_out=args.rag_max_out, **flt)
    print(f'[probe] citation rerank {time.time() - t2:.0f}s')
    res['rerank'] = describe(top, 'rerank')
    rag.report_window_drops()
    res['window_drops'] = rag.window_drops
    res['window_docs'] = rag.window_docs

    if args.out:
        with open(args.out, 'w') as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print(f'[probe] wrote {args.out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
