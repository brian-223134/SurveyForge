"""생성 결과 1편의 잠정 recall·precision·누수·시간 범위 위반을 낸다 (2026-09-14 규약 분모).

    분모  = kisti_data/data/topics.kisti.jsonl 의 n_gt_refs_cutoff
          = candidates/gap_to_80_refs.jsonl 의 tier == in_view (같은 slug) -- 두 값이 같아야 한다
    매칭  = 생성 refs 의 DB id 와 GT ref 의 view_id 를 대소문자 무시로 비교 (arXiv base id 또는 소문자 DOI)
    누수  = 정책 exclude_ids(GT 본체·선행판)가 refs·본문에 0회
    위반  = refs 중 sidecar 공개일 상한 ≥ cutoff (정책이 맞다면 0)

공용 채점기가 아니라 이 저장소 문서용 즉석 계산이다 (docs/kisti-integration.md §5.2 와 같은 방식, 분모만 새 규약).

    .venv/bin/python scripts/score_run.py --run "code/output/res/<slug>/<topic>/exp_1" --topic_id physical-adversarial-attacks
"""
import argparse
import glob
import json
import os
import sys

CODE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'code')
sys.path.insert(0, CODE)
from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(CODE, os.pardir, '.env'))
from src.retrieval_policy import load_retrieval_policy  # noqa: E402

KISTI = os.environ.get('KISTI_DATA_ROOT', '/data2/chanjoong/kisti_data')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', required=True, help='exp_N 디렉터리')
    ap.add_argument('--topic_id', required=True)
    ap.add_argument('--out', default='', help='결과 JSON (선택)')
    args = ap.parse_args()

    topics = {r['slug']: r for r in (json.loads(l) for l in open(os.path.join(KISTI, 'data', 'topics.kisti.jsonl')))}
    t = topics[args.topic_id]
    gt = [json.loads(l) for l in open(os.path.join(KISTI, 'candidates', 'gap_to_80_refs.jsonl'))]
    gt = [r for r in gt if r['slug'] == args.topic_id]
    in_view = {str(r['view_id']).lower(): r for r in gt if r['tier'] == 'in_view'}
    assert len(in_view) == t['n_gt_refs_cutoff'], (len(in_view), t['n_gt_refs_cutoff'])

    jpath = [p for p in glob.glob(os.path.join(args.run, '*.json'))
             if os.path.basename(p) not in ('run_manifest.json', 'section_references_ids.json', 'reference_metadata.json',
                                            '1-Chunk_outlines.json', '3-Merged_Sub_outline_wo_process.json')]
    assert len(jpath) == 1, jpath
    out = json.load(open(jpath[0]))
    refs = {str(v) for v in out['reference'].values()}
    refs_l = {r.lower() for r in refs}
    hits = sorted(r for r in refs_l if r in in_view)
    body = out['survey']
    manifest_p = os.path.join(args.run, 'run_manifest.json')
    manifest = json.load(open(manifest_p)) if os.path.exists(manifest_p) else {}
    policy = load_retrieval_policy(args.topic_id)
    rp = policy._rp
    cutoff = rp.parse_day(policy.cutoff)
    late = sorted(r for r in refs if (lambda ub: ub is None or ub >= cutoff)(rp.upper_bound(policy.date_of(r))))
    leaks = sorted(e for e in policy.exclude_ids if e.lower() in refs_l or e.lower() in body.lower())
    twin_titles = [s['title'] for s in policy.row.get('date_sources', []) if s.get('title')]
    # 생성 서베이의 제목 줄(첫 '# ')은 제외한다 -- topic 문자열이 GT 제목과 같으면 모델이 같은 제목을 붙이기 마련이고
    # (mllm-adversarial-attacks: '…: A Comprehensive Survey'), 그것은 검색 누수가 아니다. 본문·참고문헌에서만 찾는다.
    lines = body.split('\n')
    gen_title = next((l[2:].strip() for l in lines if l.startswith('# ')), '')
    body_wo_title = '\n'.join(l for l in lines if not l.startswith('# '))
    title_leaks = [x for x in twin_titles if x.lower() in body_wo_title.lower()]
    gen_title_equals_gt = [x for x in twin_titles if x.lower() == gen_title.lower()]

    res = {
        'run': os.path.abspath(args.run), 'topic_id': args.topic_id, 'topic': t['title'], 'cutoff': policy.cutoff,
        'refs': len(refs), 'refs_doi': sum(1 for r in refs if r.startswith('10.')),
        'denominator_n_gt_refs_cutoff': t['n_gt_refs_cutoff'], 'gt_pool': t.get('n_gt_refs_cutoff_pool'),
        'hits': len(hits), 'recall': round(len(hits) / t['n_gt_refs_cutoff'], 4), 'precision': round(len(hits) / max(len(refs), 1), 4),
        'hit_ids': hits,
        'refs_after_cutoff': late, 'gt_id_leaks': leaks, 'gt_title_leaks': title_leaks,
        'generated_title': gen_title, 'generated_title_equals_gt_title': gen_title_equals_gt,
        'words_refined': len(body.split()),
        'manifest': {k: manifest.get(k) for k in ('llm_stats', 'temperature', 'max_tokens', 'provider', 'finished_at')},
        'retrieval_policy': {k: (manifest.get('retrieval_policy') or {}).get(k) for k in
                             ('allowed', 'db_records', 'allowed_fingerprint_sha256', 'reference_violations', 'view_sha256', 'view_created_at')},
    }
    print(f"[score] {args.topic_id} cutoff<{policy.cutoff}: refs {res['refs']} (DOI {res['refs_doi']}) · hits {res['hits']}/{t['n_gt_refs_cutoff']} "
          f"→ recall {res['recall']:.1%} · precision {res['precision']:.1%} · after-cutoff refs {len(late)} · GT id 누수 {len(leaks)} · "
          f"GT 제목 누수 {len(title_leaks)}{' (생성 제목 == GT 제목)' if gen_title_equals_gt else ''} · words {res['words_refined']:,}")
    if args.out:
        with open(args.out, 'w') as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == '__main__':
    sys.exit(main())
