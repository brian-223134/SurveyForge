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

사용법:
    python scripts/append_snapshot.py \
        --base $SURVEYFORGE_DATA/database \
        --new  $SURVEYFORGE_DATA/database_2026-08/arxiv_paper_db_new_with_cc.json \
        --out  $SURVEYFORGE_DATA/database_2026-08 \
        --check-only          # 쓰지 않고 점검만
"""

import argparse
import hashlib
import json
import os
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
# 서베이 쪽 자산은 이번 증분 대상이 아니다. --db_path 하나로 완전히 전환되도록
# 새 디렉터리에 그대로 복사한다.
SURVEY_FILES = ('surveys_arxiv_paper_db.json', 'surveys_arxivid_to_index_abs.json',
                'faiss_survey_title_abs_embeddings_FROM_1501_TO_2409_gte.bin',
                'faiss_survey_title_embeddings_FROM_1501_TO_2409_gte.bin')


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
    ap.add_argument('--tag', default='', help="파일명 접미사, 예 FROM_2012_0101_TO_260803")
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
    have = {r['id'].split('v')[0] for r in table.values()}
    fresh = [r for r in fresh if r['id'].split('v')[0] not in have]
    # 같은 논문이 두 번 들어오면 매핑이 덮어써져 벡터 하나가 미아가 된다.
    seen, dedup = set(), []
    for r in fresh:
        b = r['id'].split('v')[0]
        if b not in seen:
            seen.add(b)
            dedup.append(r)
    fresh = dedup
    need = ('id', 'title', 'url', 'date', 'abs', 'cat', 'authors', 'citation_count')
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
    for name in SURVEY_FILES:
        src = os.path.join(args.base, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(args.out, name))
    print('      서베이 자산은 그대로 복사 (이번 증분 대상 아님)')

    print(f'\n[6/6] 지문 — REPRODUCTION.md 에 기록할 값', flush=True)
    for p in (out_db, out_map, out_abs, out_title):
        print(f'  {os.path.basename(p):<62} {os.path.getsize(p):>14,}  {md5(p)}')
    print(f'\n  총 {len(table):,}편 (기존 {n_base:,} + 신규 {len(fresh):,})')
    print(f'  코퍼스 최신일 {max(r["date"] for r in table.values() if r.get("date"))}')
    print('\n다음: scripts/check_db.py 로 재임베딩 검증')
    return 0


if __name__ == '__main__':
    sys.exit(main())
