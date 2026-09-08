"""게이트 선택자 등가성·시간 프로브 — IDSelectorArray(현행) vs IDSelectorBatch(해시) vs 선택자 없음.

같은 질의·같은 허용 id 집합에서 top-1500 id 목록(순서 포함)이 같은지와 소요 시간을 잰다. LLM 0.
실측 2026-09-08 (KISTI v2, 1,651,487편, topic physical-adversarial): array 761.5s · batch 3.3s · none 1.3s, 세 목록 동일.
'pipeline' 케이스는 utils.get_index_filter_by_id_prefix 가 실제로 만드는 선택자(교체 후 IDSelectorBatch)를 그대로 쓴다.

    CUDA_VISIBLE_DEVICES="" .venv/bin/python scripts/probe_selector.py <scratch_dir>
"""
import os, sys, time, json
os.environ['SURVEYFORGE_EMBED_DEVICE'] = 'cpu'
CODE = '/data2/chanjoong/survey-agent/SurveyForge/code'; sys.path.insert(0, CODE); os.chdir(CODE)
from dotenv import load_dotenv; load_dotenv('/data2/chanjoong/survey-agent/SurveyForge/.env')
import faiss, types
from src.rag import GeneralRAG_langchain
from src.utils import find_index, filter_arxivids_by_prefix, get_index_filter_by_id_prefix
D = '/data2/chanjoong/survey-agent/SurveyForge_data/database_kisti-kisti-2512'
args = types.SimpleNamespace(paper_date_oldest='1922-01-01', paper_date_newest='2026-01-01', saving_path=sys.argv[1], debug=False)
os.makedirs(args.saving_path, exist_ok=True)
rag = GeneralRAG_langchain(args=args, retriever_type='vectorstore', index_db_path=find_index(D, 'faiss_paper_title_abs_embeddings'),
                           doc_db_path=f'{D}/arxiv_paper_db_with_cc.json', arxivid_to_index_path=f'{D}/arxivid_to_index_abs.json',
                           embedding_model='/data2/chanjoong/survey-agent/SurveyForge_data/gte-large-en-v1.5')
topic = 'Visual Adversarial Attacks and Defenses in the Physical World'
kept = filter_arxivids_by_prefix(list(rag.id_to_index.keys()), '2512')
idx = [rag.id_to_index[a] for a in kept]
import numpy as np
cases = [('array', {'id_selector': faiss.IDSelectorArray(idx)}),
         ('batch', {'id_selector': faiss.IDSelectorBatch(np.asarray(idx, dtype='int64'))}),
         ('none', {}),
         # 실제 파이프라인 함수 경로 (outline_writer / writer 가 쓰는 것) -- 코드가 만드는 선택자 그대로
         ('pipeline', get_index_filter_by_id_prefix(rag.id_to_index, '2512', stage='probe-selector', saving_path=args.saving_path))]
out = {}
for name, kw in cases:
    t0 = time.time()
    ids = rag.retrieve_id([topic], top_k=1500, **kw)
    out[name] = {'secs': round(time.time() - t0, 1), 'ids': ids}
    print(f'[selector/{name}] {out[name]["secs"]}s  n={len(ids)}  selector={type(kw.get("id_selector")).__name__}', flush=True)
ref = out['array']['ids']
for name in ('batch', 'none', 'pipeline'):
    print(f'array == {name:<8} (ordered): {ref == out[name]["ids"]}', flush=True)
json.dump({k: {'secs': v['secs'], 'n': len(v['ids']), 'eq_array': ref == v['ids']} for k, v in out.items()}
          | {'ids': {k: v['ids'] for k, v in out.items()}}, open(f'{args.saving_path}/selector_eq.json', 'w'), indent=1)
print('SELECTOR_DONE', flush=True)
