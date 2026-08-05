"""스냅샷이 실제로 쓸 수 있는 상태인지 검증한다.

append_snapshot.py의 자체 정합성 검사는 '세 자료구조의 id 체계가 맞는가'만 본다.
그것만으로는 **벡터 내용이 맞는지** 알 수 없다. 텍스트 형식을 틀리거나(구분자 삽입,
instruction prefix) 정규화를 빼먹으면 예외 없이 검색 품질만 조용히 나빠진다.

그래서 저장된 벡터를 꺼내 같은 텍스트로 다시 임베딩해 코사인을 비교한다.
**이 검사가 그 오류를 잡는 유일한 관문이다.**

기존 논문과 신규 논문을 모두 표본으로 뽑는 이유: 기존만 보면 append 코드가 틀려도
통과하고, 신규만 보면 규약 자체를 잘못 읽었을 때 나란히 틀려서 통과한다.

사용법:
    CUDA_VISIBLE_DEVICES=2 python scripts/check_db.py \
        --db $SURVEYFORGE_DATA/database_2026-08 --verify-embeddings 20
"""

import argparse
import hashlib
import json
import os
import random
import sys

import faiss
import numpy as np

PAPER_DB = 'arxiv_paper_db_with_cc.json'
PAPER_MAP = 'arxivid_to_index_abs.json'
ABS_STEM = 'faiss_paper_title_abs_embeddings'
TITLE_STEM = 'faiss_paper_title_embeddings'


def find_one(db_path, stem):
    hits = sorted(f for f in os.listdir(db_path)
                  if f.startswith(stem + '_') and f.endswith('.bin'))
    if len(hits) != 1:
        raise SystemExit(f'{db_path}/{stem}_*.bin 이 {len(hits)}개다: {hits}')
    return os.path.join(db_path, hits[0])


def md5(path, chunk=1 << 24):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(chunk), b''):
            h.update(blk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', required=True, help='검증할 스냅샷 디렉터리')
    ap.add_argument('--verify-embeddings', type=int, default=0,
                    help='재임베딩으로 대조할 표본 수 (0이면 생략, GPU 필요)')
    ap.add_argument('--embedding-model', default='')
    ap.add_argument('--min-cos', type=float, default=0.999)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--fingerprint', action='store_true', help='md5까지 계산 (느리다)')
    args = ap.parse_args()

    fail = []
    print(f'[1/4] 파일 로딩 {args.db}', flush=True)
    with open(os.path.join(args.db, PAPER_DB)) as f:
        table = json.load(f)['cs_paper_info']
    with open(os.path.join(args.db, PAPER_MAP)) as f:
        mapping = {k: int(v) for k, v in json.load(f).items()}
    abs_path, title_path = find_one(args.db, ABS_STEM), find_one(args.db, TITLE_STEM)
    # 부모 IndexIDMap의 레퍼런스를 반드시 살려 둘 것. downcast로 얻은 내부 인덱스는
    # 부모가 사라지면 dangling pointer가 되어 조용히 segfault 한다 (실측).
    abs_parent, title_parent = faiss.read_index(abs_path), faiss.read_index(title_path)
    n = len(table)

    print(f'\n[2/4] 건수 일치')
    counts = {'TinyDB': n, '매핑': len(mapping),
              'abs index': abs_parent.ntotal, 'title index': title_parent.ntotal}
    for k, v in counts.items():
        print(f'  {k:<12} {v:,}')
    if len(set(counts.values())) != 1:
        fail.append(f'건수 불일치: {counts}')

    print(f'\n[3/4] id 체계 (1-based 1..{n} 연속)')
    keys = sorted(int(k) for k in table)
    if keys != list(range(1, n + 1)):
        fail.append(f'TinyDB 키가 1..{n} 연속이 아니다 (min {keys[0]} max {keys[-1]})')
    else:
        print(f'  TinyDB 키      1..{n} 연속 OK')
    vals = sorted(mapping.values())
    if vals != list(range(1, n + 1)):
        fail.append(f'매핑 값이 1..{n} 연속이 아니다 (min {vals[0]} max {vals[-1]})')
    else:
        print(f'  매핑 값        1..{n} 연속 OK')
    for name, parent in (('abs', abs_parent), ('title', title_parent)):
        ids = faiss.vector_to_array(parent.id_map)
        if sorted(ids.tolist()) != list(range(1, n + 1)):
            fail.append(f'{name} index stored id가 1..{n} 전단사가 아니다')
        else:
            print(f'  {name} stored id  1..{n} 전단사 OK')
    bad = [i for i in random.Random(args.seed).sample(range(1, n + 1), min(2000, n))
           if mapping.get(table[str(i)]['id']) != i]
    if bad:
        fail.append(f'키 != 매핑값 표본 {len(bad)}건 (예: {bad[:5]})')
    else:
        print(f'  키 == 매핑값   2,000건 표본 OK')

    if args.verify_embeddings:
        print(f'\n[4/4] 재임베딩 대조 {args.verify_embeddings}건 x 2필드', flush=True)
        import torch
        from sentence_transformers import SentenceTransformer
        model_path = args.embedding_model or os.path.join(
            os.path.dirname(os.path.abspath(args.db)), 'gte-large-en-v1.5')
        model = SentenceTransformer(model_path, trust_remote_code=True)
        model.to(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))

        # 기존 구간과 신규 구간을 반씩 뽑는다. 한쪽만 보면 놓치는 오류가 있다.
        rng = random.Random(args.seed)
        half = max(1, args.verify_embeddings // 2)
        # 배포본 589,123편이 기존 구간이다. 그보다 작으면 전체를 기존으로 본다.
        split = min(589123, n)
        picks = (rng.sample(range(1, split + 1), min(half, split))
                 + (rng.sample(range(split + 1, n + 1), min(half, n - split))
                    if n > split else []))

        abs_inner = faiss.downcast_index(abs_parent.index)
        title_inner = faiss.downcast_index(title_parent.index)
        abs_pos = {int(v): i for i, v in enumerate(faiss.vector_to_array(abs_parent.id_map))}
        title_pos = {int(v): i for i, v in enumerate(faiss.vector_to_array(title_parent.id_map))}

        recs = [table[str(i)] for i in picks]
        # 규약: 구분자 없는 단순 연결 / 정규화 / prefix 없음
        ev = model.encode([r['title'] + r['abs'] for r in recs],
                          show_progress_bar=False, normalize_embeddings=True)
        tv = model.encode([r['title'] for r in recs],
                          show_progress_bar=False, normalize_embeddings=True)

        worst_abs = worst_title = 1.0
        for sid, r, ea, et in zip(picks, recs, ev, tv):
            sa = abs_inner.reconstruct(abs_pos[sid])
            st = title_inner.reconstruct(title_pos[sid])
            ca = float(np.dot(sa, ea) / (np.linalg.norm(sa) * np.linalg.norm(ea)))
            ct = float(np.dot(st, et) / (np.linalg.norm(st) * np.linalg.norm(et)))
            worst_abs, worst_title = min(worst_abs, ca), min(worst_title, ct)
            if min(ca, ct) < args.min_cos:
                print(f'  낮음 id={sid} {r["id"]}  title+abs {ca:.6f}  title {ct:.6f}')
        newest = 'n/a' if n <= split else f'{len(picks) - min(half, split)}건'
        print(f'  표본 {len(picks)}건 (신규 구간 {newest})')
        print(f'  최저 cos  title+abs {worst_abs:.6f}   title {worst_title:.6f}')
        if min(worst_abs, worst_title) < args.min_cos:
            fail.append(f'재임베딩 cos가 {args.min_cos} 미만 — 텍스트 형식이나 '
                        f'정규화가 저장 당시와 다르다')
    else:
        print('\n[4/4] 재임베딩 대조 생략 (--verify-embeddings N 으로 켠다)')

    dates = [r['date'] for r in table.values() if r.get('date')]
    print(f'\n코퍼스: {n:,}편, 날짜 {min(dates)} .. {max(dates)}')
    ids = [r['id'].split('.')[0] for r in table.values()]
    print(f'        arXiv id 접두사 {min(ids)} .. {max(ids)}')
    print(f'        실행 시 SURVEYFORGE_PAPER_ID_CUTOFF={max(ids)} '
          f'/ SURVEYFORGE_PAPER_DATE_NEWEST={max(dates)} 이상으로 둘 것')

    if args.fingerprint:
        print('\n지문 (REPRODUCTION.md에 기록):')
        for p in (os.path.join(args.db, PAPER_DB), os.path.join(args.db, PAPER_MAP),
                  abs_path, title_path):
            print(f'  {os.path.basename(p):<62} {os.path.getsize(p):>14,}  {md5(p)}')

    print()
    if fail:
        print('=== 결과: 실패 ===')
        for f_ in fail:
            print(f'  - {f_}')
        return 1
    print('=== 결과: 통과 ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
