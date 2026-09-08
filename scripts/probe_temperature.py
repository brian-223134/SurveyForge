"""temperature 검증 프로브 — SurveyForge 의 실제 서브섹션 프롬프트로 temperature 별 출력 특성을 잰다.

왜: 원 코드(upstream)는 모델과 무관하게 모든 호출에 temperature=1 을 고정한다. KISTI 비교 실험은
4 agent 공통 0.6 인데, 이것은 Meta 가 Llama 3.x Instruct 의 generation_config 로 배포하는 값
(temperature 0.6, top_p 0.9)이다. 이 프로브는 그 선택이 SurveyForge 의 프롬프트(초록 60편 + 아웃라인,
약 20K 토큰)에서도 타당한지 본다: temperature 0 / 0.6 / 1.0 에서 N회씩 같은 프롬프트를 보내
잘림(=반복 루프)율·출력 길이·중복 문장 비율·인용 수·소요를 비교한다. 비용 약 $0.1 (12회).

    SURVEYFORGE_TEMPERATURE= SURVEYFORGE_RETRY_TRUNCATED=0 CUDA_VISIBLE_DEVICES=4 \
    .venv/bin/python scripts/probe_temperature.py --db_path $SURVEYFORGE_DATA/database_cc-bench-2512 \
        --topic "Visual Adversarial Attacks and Defenses in the Physical World" --out eval_out/probe_temperature.json

재요청 가드는 끄고(RETRY_TRUNCATED=0) 잘림을 그대로 관찰한다. 전역 오버라이드도 비운다.
"""

import argparse
import collections
import json
import os
import re
import sys
import time

# .env 보다 먼저 박아야 한다 (load_dotenv 는 이미 있는 값을 덮지 않는다).
os.environ['SURVEYFORGE_TEMPERATURE'] = ''
os.environ['SURVEYFORGE_RETRY_TRUNCATED'] = '0'

CODE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'code')
sys.path.insert(0, CODE)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(CODE, os.pardir, '.env'))

from src.model import APIModel, LLM_STATS, MAX_TOKENS  # noqa: E402
from src.prompt import SUBSECTION_WRITING_PROMPT  # noqa: E402
from src.rag import GeneralRAG_langchain  # noqa: E402
from src.utils import find_index, get_index_filter, get_index_filter_by_id_prefix, tokenCounter  # noqa: E402

OUTLINE = """# Visual Adversarial Attacks and Defenses in the Physical World
## 1 Introduction
Description: Scope, threat model and why physical-world attacks differ from digital ones.
## 2 Physical Attacks on Image Classifiers
Description: Printed patches, stickers and 3D objects that fool classifiers under real viewing conditions.
## 3 Physical Attacks on Object Detectors
Description: Adversarial patches, clothing and camouflage that suppress or spoof detections; robustness to distance, angle and lighting.
## 4 Attacks on Other Perception Tasks
Description: Face recognition, semantic segmentation, depth estimation, LiDAR and multi-sensor fusion.
## 5 Defenses and Robustness Evaluation
Description: Adversarial training, input purification, certified defenses and benchmarks for the physical setting.
## 6 Open Problems and Future Directions
Description: Transferability, realism gaps, evaluation standards and safety implications.
## 7 Conclusion
Description: Summary of findings."""


def build_prompt(rag, topic, args):
    flt = get_index_filter_by_id_prefix(rag.id_to_index, args.paper_id_cutoff, stage='probe-temp',
                                        saving_path=args.saving_path)
    pool = rag.retrieve_id([topic], top_k=1500, **flt)                       # writer.write 와 동일
    lock = get_index_filter(rag.id_to_index, pool)
    ids = rag.retrieve_id([args.query], search_type='similarity', rerank='citation',
                          top_k=args.rag_num, max_out=args.rag_max_out, **lock)
    store = rag.rag_data['doc_store']._dict
    paper_texts = ''
    for i in ids:
        d = store[i]
        paper_texts += f"---\n\npaper_title: {d.metadata['title']}\n\npaper_content:\n\n{d.page_content}\n"
    paper_texts += '---\n'
    paras = {'OVERALL OUTLINE': OUTLINE, 'SUBSECTION NAME': args.subsection, 'DESCRIPTION': args.description,
             'TOPIC': topic, 'PAPER LIST': paper_texts, 'SECTION NAME': args.section,
             'WORD NUM': str(args.word_num), 'CITATION NUM': '8'}
    prompt = SUBSECTION_WRITING_PROMPT
    for k, v in paras.items():
        prompt = prompt.replace(f'[{k}]', v)
    return prompt, ids


def analyse(text):
    sents = [s.strip().lower() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 20]
    c = collections.Counter(sents)
    dup = sum(v - 1 for v in c.values())
    return {
        'words': len(text.split()),
        'sentences': len(sents),
        'dup_sentence_ratio': round(dup / max(len(sents), 1), 3),
        'max_sentence_repeat': max(c.values()) if c else 0,
        'citations': len(re.findall(r'\[[^\[\]]{3,}\]', text)),
    }


def main():
    data_root = os.environ.get('SURVEYFORGE_DATA', '/data2/chanjoong/survey-agent/SurveyForge_data')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--topic', required=True)
    ap.add_argument('--db_path', required=True)
    ap.add_argument('--embedding_model', default=os.path.join(data_root, 'gte-large-en-v1.5'))
    ap.add_argument('--section', default='Physical Attacks on Object Detectors')
    ap.add_argument('--subsection', default='Adversarial Patches and Camouflage against Detectors')
    ap.add_argument('--description', default='Printable patches, adversarial clothing and camouflage textures that '
                    'make detectors miss or misclassify objects, and how their effectiveness varies with distance, '
                    'viewing angle and lighting.')
    ap.add_argument('--query', default='Adversarial patches and camouflage against object detectors in the physical world')
    ap.add_argument('--rag_num', type=int, default=100)
    ap.add_argument('--rag_max_out', type=int, default=60)
    ap.add_argument('--word_num', type=int, default=500)
    ap.add_argument('--temps', default='0,0.6,1.0')
    ap.add_argument('--n', type=int, default=4)
    ap.add_argument('--paper_id_cutoff', default=os.environ.get('SURVEYFORGE_PAPER_ID_CUTOFF', '2612'))
    ap.add_argument('--paper_date_oldest', default=os.environ.get('SURVEYFORGE_PAPER_DATE_OLDEST', '1922-01-01'))
    ap.add_argument('--paper_date_newest', default=os.environ.get('SURVEYFORGE_PAPER_DATE_NEWEST', '2026-01-01'))
    ap.add_argument('--saving_path', default=os.path.join(os.environ.get('TMPDIR', '/tmp'), 'surveyforge_probe_temp'))
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    args.debug = False
    os.makedirs(args.saving_path, exist_ok=True)

    t0 = time.time()
    rag = GeneralRAG_langchain(args=args, retriever_type='vectorstore',
                               index_db_path=find_index(args.db_path, 'faiss_paper_title_abs_embeddings'),
                               doc_db_path=f'{args.db_path}/arxiv_paper_db_with_cc.json',
                               arxivid_to_index_path=f'{args.db_path}/arxivid_to_index_abs.json',
                               embedding_model=args.embedding_model)
    prompt, ids = build_prompt(rag, args.topic, args)
    counter = tokenCounter()
    n_prompt = counter.num_tokens_from_string(prompt)
    print(f'[probe-temp] prompt {n_prompt:,} tokens, {len(ids)} papers, built in {time.time() - t0:.0f}s; '
          f'max_tokens={MAX_TOKENS}, retry_truncated off', flush=True)

    model = APIModel(os.environ['SURVEYFORGE_MODEL'], os.environ['OPENROUTER_API_KEY'], os.environ['SURVEYFORGE_API_URL'])
    rows, samples = [], []
    for t in [float(x) for x in args.temps.split(',')]:
        for k in range(args.n):
            before = dict(LLM_STATS)
            t1 = time.time()
            text = model.chat(prompt, temperature=t)
            secs = time.time() - t1
            after = dict(LLM_STATS)
            row = {'temperature': t, 'run': k + 1, 'secs': round(secs),
                   'out_tokens': counter.num_tokens_from_string(text),
                   'truncated': after['truncated_accepted'] - before['truncated_accepted'],
                   'errors': after['error_retries'] - before['error_retries'], **analyse(text)}
            rows.append(row)
            samples.append({'temperature': t, 'run': k + 1, 'text': text})
            print(f"[probe-temp] T={t:<4} #{k + 1}  {row['secs']:>4}s  tokens {row['out_tokens']:>5}  words {row['words']:>5}  "
                  f"trunc {row['truncated']}  dup {row['dup_sentence_ratio']:.2f}  maxrep {row['max_sentence_repeat']}  "
                  f"cites {row['citations']}", flush=True)

    summary = {}
    for t in sorted({r['temperature'] for r in rows}):
        rs = [r for r in rows if r['temperature'] == t]
        summary[str(t)] = {
            'n': len(rs),
            'truncated': sum(r['truncated'] for r in rs),
            'mean_words': round(sum(r['words'] for r in rs) / len(rs)),
            'mean_out_tokens': round(sum(r['out_tokens'] for r in rs) / len(rs)),
            'mean_dup_ratio': round(sum(r['dup_sentence_ratio'] for r in rs) / len(rs), 3),
            'max_sentence_repeat': max(r['max_sentence_repeat'] for r in rs),
            'mean_citations': round(sum(r['citations'] for r in rs) / len(rs), 1),
            'mean_secs': round(sum(r['secs'] for r in rs) / len(rs)),
        }
    print('[probe-temp] summary:', json.dumps(summary), flush=True)
    with open(args.out, 'w') as f:
        json.dump({'topic': args.topic, 'db_path': os.path.abspath(args.db_path), 'prompt_tokens': n_prompt,
                   'papers': len(ids), 'max_tokens': MAX_TOKENS, 'model': os.environ['SURVEYFORGE_MODEL'],
                   'provider': os.environ.get('SURVEYFORGE_PROVIDER', ''), 'word_num': args.word_num,
                   'rows': rows, 'summary': summary, 'samples': samples}, f, ensure_ascii=False, indent=1)
    print(f'[probe-temp] wrote {args.out}\nPROBE_DONE', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
