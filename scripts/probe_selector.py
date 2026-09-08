"""게이트 선택자 등가성·시간 프로브 — IDSelectorArray(현행) vs IDSelectorBatch(해시) vs 선택자 없음.

같은 질의·같은 허용 id 집합에서 top-1500 id 목록(순서 포함)이 같은지와 소요 시간을 잰다. LLM 0.
실측 2026-09-08 (KISTI v2, 1,651,487편, topic physical-adversarial): array 761.5s · batch 3.3s · none 1.3s, 세 목록 동일.

    CUDA_VISIBLE_DEVICES="" .venv/bin/python scripts/probe_selector.py <scratch_dir>
"""
import os, sys, time, json
os.environ['SURVEYFORGE_EMBED_DEVICE'] = 'cpu'
CODE = '/data2/chanjoong/survey-agent/SurveyForge/code'; sys.path.insert(0, CODE); os.chdir(CODE)
from dotenv import load_dotenv; load_dotenv('/data2/chanjoong/survey-agent/SurveyForge/.env')
import faiss, types
from src.rag import GeneralRAG_langchain
from src.utils import find_index, filter_arxivids_by_prefix
D = '/data2/chanjoong/survey-agent/SurveyForge_data/database_kisti-kisti-2512'
args = types.SimpleNamespace(paper_date_oldest='1922-01-01', paper_date_newest='2026-01-01', saving_path=sys.argv[1], debug=False)
os.makedirs(args.saving_path, exist_ok=True)
rag = GeneralRAG_langchain(args=args, retriever_type='vectorstore', index_db_path=find_index(D, 'faiss_paper_title_abs_embeddings'),
                           doc_db_path=f'{D}/arxiv_paper_db_with_cc.json', arxivid_to_index_path=f'{D}/arxivid_to_index_abs.json',
                           embedding_model='/data2/chanjoong/survey-agent/SurveyForge_data/gte-large-en-v1.5')
topic = 'Visual Adversarial Attacks and Defenses in the Physical World'
kept = filter_arxivids_by_prefix(list(rag.id_to_index.keys()), '2512')
idx = [rag.id_to_index[a] for a in kept]
out = {}
for name, sel in (('array', faiss.IDSelectorArray(idx)), ('batch', faiss.IDSelectorBatch(idx)), ('none', None)):
    t0 = time.time()
    kw = {'id_selector': sel} if sel is not None else {}
    ids = rag.retrieve_id([topic], top_k=1500, **kw)
    out[name] = {'secs': round(time.time() - t0, 1), 'ids': ids}
    print(f'[selector/{name}] {out[name]["secs"]}s  n={len(ids)}', flush=True)
print('array == batch (ordered):', out['array']['ids'] == out['batch']['ids'])
print('array == none  (ordered):', out['array']['ids'] == out['none']['ids'], '(게이트 212 제외분이 top-1500 에 없으면 같다)')
json.dump({k: {'secs': v['secs'], 'n': len(v['ids'])} for k, v in out.items()} | {'array_eq_batch': out['array']['ids'] == out['batch']['ids'], 'array_eq_none': out['array']['ids'] == out['none']['ids']}, open(f'{args.saving_path}/selector_eq.json', 'w'), indent=1)
print('SELECTOR_DONE', flush=True)
