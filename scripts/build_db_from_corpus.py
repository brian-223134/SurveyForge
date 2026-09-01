"""공용 코퍼스 export(TinyDB JSON)에서 SurveyForge 논문 DB 스냅샷을 전체 빌드한다.

`append_snapshot.py`가 '기존 스냅샷 뒤에 이어 붙이기'라면, 이 스크립트는
asg-common-corpus의 `export-agent-db --format surveyforge` 산출물을 입력으로
빈 상태에서 인덱스까지 통째로 만든다. 불변식과 임베딩 규약은 append_snapshot.py
헤더에 실측으로 문서화된 것과 동일하다:

    TinyDB 키 == arxivid_to_index_abs.json 값 == IndexIDMap stored id (1-based 연속)
    faiss_paper_title_abs_* = encode(title + abs)  구분자 없는 단순 연결
    faiss_paper_title_*     = encode(title)
    IndexIDMap(IndexFlatIP), 1024-dim, L2 정규화, instruction prefix 없음

## 텍스트는 export 그대로 임베딩한다 (정규화 없음)

초록 표본 10%에 리터럴 '\\n' 이스케이프가, 6%에 개행 문자가 남아 있지만 치환하지
않는다. 이유 둘: (1) AutoSurvey가 같은 export를 바이트 그대로 복사해 임베딩했으므로
(asg-common-corpus/docs/autosurvey-usage.md §1) agent 간 텍스트 통일이 우선이고,
(2) 리터럴 '\\n' 블라인드 치환은 LaTeX 명령('\\nu', '\\nabla', …)을 오손한다.
그 결과 스냅샷의 JSON은 export 파일의 **바이트 동일 사본**이고, 사이드카 manifest의
content_sha256이 그대로 검증에 쓰인다. 논의: docs/common-corpus-integration.md 함정 7.

## 재시작 가능

임베딩은 청크(기본 25,600편) 단위로 `<out>/_emb_tmp/`에 저장한다. 8시간짜리 작업이
죽으면 같은 명령으로 다시 실행 — 완료된 청크는 건너뛴다. 성공적으로 인덱스를 쓰고
나면 tmp는 지운다.

## GPU를 고를 것 (append_snapshot.py와 동일)

    nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader
    CUDA_VISIBLE_DEVICES=5 .venv/bin/python scripts/build_db_from_corpus.py ...

사용법:
    CUDA_VISIBLE_DEVICES=5 .venv/bin/python scripts/build_db_from_corpus.py \
        --export ../asg-common-corpus/data/exports/surveyeval-2512.surveyforge.json \
        --out $SURVEYFORGE_DATA/database_cc-surveyeval-2512
    # 스모크: --limit 2000 --skip-survey-assets --out <scratch>
    # 다음: scripts/check_db.py --db <out> --verify-embeddings 20
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from append_snapshot import PAPER_DB, PAPER_MAP, ABS_STEM, TITLE_STEM, \
    check_consistency, md5  # noqa: E402

SURVEY_FILES = ('surveys_arxiv_paper_db.json', 'surveys_arxivid_to_index_abs.json')
SURVEY_STEMS = ('faiss_survey_title_abs_embeddings', 'faiss_survey_title_embeddings')


def sha256(path, chunk=1 << 24):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(chunk), b''):
            h.update(blk)
    return h.hexdigest()


def embed_chunked(model, texts, batch_size, chunk_size, tmp_dir, label):
    """청크별로 임베딩해 .npy로 저장하고, 이미 있는 청크는 건너뛴 뒤 전체를 잇는다."""
    os.makedirs(tmp_dir, exist_ok=True)
    n = len(texts)
    parts, t0, done_new = [], time.time(), 0
    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        # 파일명에 전체 건수를 박아 --limit 스모크와 본 빌드의 청크가 섞이지 않게 한다.
        path = os.path.join(tmp_dir, f'{label}_{n}_{start:07d}.npy')
        if os.path.exists(path):
            vec = np.load(path)
            if vec.shape[0] == end - start:
                parts.append(vec)
                continue
            os.remove(path)  # 죽다 만 청크
        # batch_size를 encode에 직접 준다. sentence-transformers는 청크를 길이순으로
        # 정렬해 배칭한 뒤 원래 순서로 복원하므로 (1) id 순서 불변식이 유지되고
        # (2) 장문 배치가 균질해진다. 코퍼스에는 구 DB(최대 567 tokens)와 달리
        # ~1,900 token짜리 초록이 있어, batch 64 × seq² 어텐션이 15 GiB를 요구하며
        # OOM 났다 (2026-08-31 실측) — 기본 batch를 16으로 내린 이유.
        vec = model.encode(texts[start:end], batch_size=batch_size,
                           show_progress_bar=False,
                           normalize_embeddings=True  # 저장 벡터 규약: norm 1.0
                           ).astype('float32')
        np.save(path + '.part.npy', vec)
        os.replace(path + '.part.npy', path)
        parts.append(vec)
        done_new += end - start
        rate = done_new / max(time.time() - t0, 1e-9)
        eta = (n - end) / max(rate, 1e-9)
        print(f'  [{label}] {end:,}/{n:,}  {rate:.0f}편/s  ETA {eta / 3600:.1f}h', flush=True)
    full = np.concatenate(parts)
    if full.shape[0] != n:
        raise SystemExit(f'[{label}] 청크 합계 {full.shape[0]:,} != {n:,}')
    return full


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--export', required=True,
                    help='export-agent-db --format surveyforge 산출물 json')
    ap.add_argument('--out', required=True, help='새 스냅샷 디렉터리 (기존 것과 섞지 말 것)')
    ap.add_argument('--survey-assets',
                    help='서베이 DB 4종을 복사해 올 기존 스냅샷 (기본: <out 부모>/database)')
    ap.add_argument('--embedding-model', default='',
                    help='기본: <out 부모>/gte-large-en-v1.5')
    # append_snapshot의 실측 최적은 64였지만 그건 최대 567 token 코퍼스 기준.
    # 공용 코퍼스의 장문 초록에서는 64가 OOM — embed_chunked 주석 참조.
    ap.add_argument('--batch-size', type=int, default=16)
    ap.add_argument('--chunk-size', type=int, default=25600, help='재시작 체크포인트 단위')
    ap.add_argument('--device', default='')
    ap.add_argument('--tag', default='', help='인덱스 파일명 접미사 (기본: manifest의 view명)')
    ap.add_argument('--limit', type=int, default=0, help='스모크용 상한 (앞에서 N편)')
    ap.add_argument('--skip-survey-assets', action='store_true')
    ap.add_argument('--validate-only', action='store_true', help='입력 검증까지만 하고 종료')
    args = ap.parse_args()

    data_root = os.path.dirname(os.path.abspath(args.out))
    model_path = args.embedding_model or os.path.join(data_root, 'gte-large-en-v1.5')
    survey_src = args.survey_assets or os.path.join(data_root, 'database')

    print(f'[1/6] export 로딩 {args.export}', flush=True)
    sidecar_path = args.export + '.manifest.json'
    with open(sidecar_path) as f:
        sidecar = json.load(f)
    with open(args.export) as f:
        table = json.load(f)['cs_paper_info']
    if len(table) != sidecar['records']:
        raise SystemExit(f"레코드 수 불일치: json {len(table):,} vs manifest {sidecar['records']:,}")

    if args.limit:
        table = {str(i): table[str(i)] for i in range(1, args.limit + 1)}
        print(f'      --limit {args.limit}: 앞 {len(table):,}편만 (스모크)')
    n = len(table)

    print(f'\n[2/6] 입력 검증', flush=True)
    keys = sorted(int(k) for k in table)
    if keys != list(range(1, n + 1)):
        raise SystemExit(f'키가 1..{n} 연속이 아니다 (min {keys[0]}, max {keys[-1]})')
    need = ('id', 'title', 'url', 'date', 'abs', 'cat', 'citation_count')  # authors는 코퍼스에 없다
    missing = {f for r in (table[str(i)] for i in (1, n // 2, n)) for f in need if f not in r}
    if missing:
        raise SystemExit(f'레코드에 없는 필드: {sorted(missing)}')
    mapping = {table[str(i)]['id']: i for i in range(1, n + 1)}
    if len(mapping) != n:
        raise SystemExit(f'arXiv id 중복: {n - len(mapping):,}건')
    dates = [r['date'] for r in table.values() if r.get('date')]
    print(f'      {n:,}편, id/키/필드 OK, 날짜 범위 {min(dates)} .. {max(dates)}')
    if args.validate_only:
        print('--validate-only: 여기서 종료한다.')
        return 0

    device = args.device or ('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'\n[3/6] 임베딩 {model_path} on {device} (batch {args.batch_size}, '
          f'chunk {args.chunk_size})', flush=True)
    model = SentenceTransformer(model_path, trust_remote_code=True)
    model.to(torch.device(device))
    tmp_dir = os.path.join(args.out, '_emb_tmp')
    recs = [table[str(i)] for i in range(1, n + 1)]
    # 구분자 없는 단순 연결. 공백 하나만 끼워도 cos가 0.99로 떨어진다 (append_snapshot 실측).
    abs_vec = embed_chunked(model, [r['title'] + r['abs'] for r in recs],
                            args.batch_size, args.chunk_size, tmp_dir, 'title+abs')
    title_vec = embed_chunked(model, [r['title'] for r in recs],
                              args.batch_size, args.chunk_size, tmp_dir, 'title')

    print(f'\n[4/6] 인덱스 구성', flush=True)
    dim = abs_vec.shape[1]
    ids = np.arange(1, n + 1, dtype='int64')  # 1-based 연속
    abs_idx = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
    title_idx = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
    abs_idx.add_with_ids(abs_vec, ids)
    title_idx.add_with_ids(title_vec, ids)
    check_consistency(table, mapping, {'abs': abs_idx, 'title': title_idx}, 'build')

    view = sidecar.get('view', {}).get('name', 'unknown')
    tag = args.tag or ('SMOKE_%d' % n if args.limit
                       else 'CC_' + view.upper().replace('-', '_'))
    os.makedirs(args.out, exist_ok=True)
    print(f'\n[5/6] 쓰기 {args.out}  (tag {tag})', flush=True)
    out_db = os.path.join(args.out, PAPER_DB)
    out_map = os.path.join(args.out, PAPER_MAP)
    out_abs = os.path.join(args.out, f'{ABS_STEM}_{tag}.bin')
    out_title = os.path.join(args.out, f'{TITLE_STEM}_{tag}.bin')
    if args.limit:
        with open(out_db, 'w') as f:
            json.dump({'cs_paper_info': table}, f, ensure_ascii=False)
    else:
        # 바이트 동일 사본. 주의: 사이드카의 content_sha256은 파일 전체가 아니라
        # 레코드 청크만 해시한 값이다 (JSON 껍데기 '{"cs_paper_info": {' / '}}' 제외
        # — exporter 구현 특성, 2026-08-31 밤 빌드가 여기서 헛되이 중단됐다).
        # 그래서 원본 파일을 직접 해시해 사본과 대조한다.
        src_sha = sha256(args.export)
        shutil.copy2(args.export, out_db)
        got = sha256(out_db)
        if got != src_sha:
            raise SystemExit(f'복사본 sha256 불일치: {got} != {src_sha}')
        print(f'      {PAPER_DB} = export 사본, 파일 sha256 {got[:12]}… 일치 확인')
    with open(out_map, 'w') as f:
        json.dump(mapping, f)
    faiss.write_index(abs_idx, out_abs)
    faiss.write_index(title_idx, out_title)
    shutil.copy2(sidecar_path, os.path.join(args.out, 'corpus_export_manifest.json'))

    if not args.skip_survey_assets:
        # database_survey도 같은 --db_path에서 읽으므로 서베이 자산이 함께 있어야 한다.
        # 논문 DB 쪽 파일(구 인덱스 포함)을 끌고 오면 find_index의 단일 glob이 깨지므로 제외.
        ban_stems = (ABS_STEM, TITLE_STEM)
        copied = []
        for name in sorted(os.listdir(survey_src)):
            src = os.path.join(survey_src, name)
            if not os.path.isfile(src) or name in (PAPER_DB, PAPER_MAP) \
                    or any(name.startswith(s + '_') for s in ban_stems):
                continue
            shutil.copy2(src, os.path.join(args.out, name))
            copied.append(name)
        print(f'      서베이 자산 {len(copied)}개 복사: {", ".join(copied)}')
        have = set(os.listdir(args.out))
        lack = [f for f in SURVEY_FILES if f not in have] + \
               [s for s in SURVEY_STEMS if not any(x.startswith(s + '_') for x in have)]
        if lack:
            raise SystemExit(f'서베이 자산 누락: {lack} (--survey-assets 확인)')

    build_manifest = {
        'built_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'export': os.path.abspath(args.export),
        # 파일 전체 지문. sidecar의 content_sha256(레코드 청크만)과 다르다 — 위 주석.
        'export_file_sha256': None if args.limit else src_sha,
        'export_manifest': sidecar,
        'records': n,
        'limit': args.limit or None,
        'tag': tag,
        'embedding_model': model_path,
        'batch_size': args.batch_size,
        'text_normalization': 'none — export 원문 그대로 (헤더 참조)',
        'date_range': [min(dates), max(dates)],
        'md5': {os.path.basename(p): md5(p) for p in (out_db, out_map, out_abs, out_title)},
    }
    with open(os.path.join(args.out, 'build_manifest.json'), 'w') as f:
        json.dump(build_manifest, f, ensure_ascii=False, indent=2)
    shutil.rmtree(tmp_dir)

    print(f'\n[6/6] 지문 — build_manifest.json에도 기록됨', flush=True)
    for name, h in build_manifest['md5'].items():
        print(f'  {name:<62} {h}')
    print(f'\n  총 {n:,}편, 날짜 범위 {min(dates)} .. {max(dates)}')
    print('\n다음: scripts/check_db.py --db', args.out, '--verify-embeddings 20')
    return 0


if __name__ == '__main__':
    sys.exit(main())
