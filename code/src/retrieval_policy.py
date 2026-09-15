"""topic 별 retrieval cutoff -- GT survey 의 최초 공개일 이전 문헌만 검색 후보로 허용한다 (2026-09-14 규약).

교수님 지시(2026-09-14): reference cutoff 를 2025-12-31 로 고정하지 않는다. corpus(view `kisti-2608`)는 시간 컷
없이 스냅샷 전체를 두고, **retrieval 이 topic 별 cutoff(= GT survey 최초 공개일) 이전 문헌만** 뽑는다.
판정 규칙·정책 파일·sidecar 로더는 4 agent 공통 모듈 `kisti_data/adapter/common/retrieval_policy.py` 에 있다
(AutoSurvey `src/retrieval_policy.py` 와 같은 규칙). 이 모듈은 그것을 SurveyForge 의 검색 경로에 붙이는 얇은 층이다:

    규칙   upper_bound(문헌 공개일) < retrieval_cutoff_at  (당일 제외, 날짜 없음 제외; 문자열 길이 = 정밀도)
    날짜   sidecar paper_dates.json 하나 ({id: "YYYY[-MM[-DD]]"}, view 전편) -- export 의 date(YYYY-01-01)는 쓰지 않는다
    제외   exclude_ids (GT 본체·선행판·사본) 는 날짜와 무관하게 차단
    적용   허용 집합 **안에서** 검색 (FAISS IDSelectorBatch) -- 전체 Top-K 뒤 사후 필터 금지

어디에 걸리는가 (docs/retrieval-policy.md):
    utils.get_retrieval_filter      아웃라인 풀·집필 풀 (id 게이트 ∩ 허용 집합 → IDSelectorBatch)
    outline_writer                  서브아웃라인 검색에도 같은 선택자 (원 코드는 여기에 게이트가 없었다)
    writer.replace_citations…       인용 정합의 잠금 집합을 허용 집합과 교집합
    database.database               직접 조회(get_paper_info_from_ids)·search 를 허용 집합으로 제한
    database.database_survey        outline DB(human survey, arXiv id)는 sidecar 밖이라 id 의 YYMM(v1 투고월)로 판정

topic 지정은 env 하나: SURVEYFORGE_TOPIC_ID=<slug> (정책 파일의 topic_id). 정책 파일·sidecar 경로는
SURVEYFORGE_TOPIC_POLICY / SURVEYFORGE_PAPER_DATES 로 바꿀 수 있고, 기본은 아래 상수.
"""
import hashlib
import json
import os
import re
import sys

KISTI_DATA_ROOT = os.environ.get('KISTI_DATA_ROOT', '/data2/chanjoong/kisti_data')
ADAPTER_ROOT = os.environ.get('KISTI_ADAPTER_ROOT', os.path.join(KISTI_DATA_ROOT, 'adapter'))
# 문헌 날짜는 이 파일 하나만 쓴다 (AGENT-HANDOFF.md §0, 2026-09-14). DB 디렉터리에 복사하지 않는다.
DEFAULT_PAPER_DATES = os.path.join(KISTI_DATA_ROOT, 'data', 'views', 'kisti-2608', 'paper_dates.json')
# 정책 파일 정본은 AutoSurvey 가 만든다 (cutoff 값은 view 무관). kisti-2608 용이 없으면 2512 정본으로.
_POLICY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, os.pardir,
                           'AutoSurvey', 'data')
DEFAULT_POLICY_CANDIDATES = [os.path.normpath(os.path.join(_POLICY_DIR, 'topic_policy.kisti-2608.jsonl')),
                             os.path.normpath(os.path.join(_POLICY_DIR, 'topic_policy.kisti-2512.jsonl'))]
# topic_id 에 이 값을 주면 정책 없이(원 코드 동작: id 게이트만) 돌린다. 실수로 비워 둔 것과 구분하려고 명시값을 요구한다.
NO_POLICY = 'none'


def _common():
    """kisti_data 공통 모듈. duckdb 불필요, 어느 env 에서든 import 된다."""
    if ADAPTER_ROOT not in sys.path:
        sys.path.insert(0, ADAPTER_ROOT)
    try:
        from common import retrieval_policy as rp  # noqa: WPS433
    except ImportError as e:
        raise RuntimeError(f'kisti_data 공통 정책 모듈을 import 할 수 없다 ({ADAPTER_ROOT}/common/retrieval_policy.py): {e}. '
                           f'KISTI_ADAPTER_ROOT 를 확인할 것') from e
    return rp


def default_policy_path():
    env = os.environ.get('SURVEYFORGE_TOPIC_POLICY', '').strip()
    if env:
        return env
    for p in DEFAULT_POLICY_CANDIDATES:
        if os.path.exists(p):
            return p
    return DEFAULT_POLICY_CANDIDATES[0]


def default_paper_dates_path():
    return os.environ.get('SURVEYFORGE_PAPER_DATES', '').strip() or DEFAULT_PAPER_DATES


def fingerprint(ids):
    """허용 집합의 지문 -- 정렬한 id 를 개행으로 이어 sha256. AutoSurvey `src/retrieval_policy.fingerprint` 와 같은 식이라
    같은 DB·같은 정책이면 두 agent 의 값이 같다 (physical-adversarial @ kisti-2608: 4bee99cd…)."""
    h = hashlib.sha256()
    for i in sorted(ids):
        h.update(str(i).encode())
        h.update(b'\n')
    return h.hexdigest()


def _sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for blk in iter(lambda: f.read(chunk), b''):
            h.update(blk)
    return h.hexdigest()


def load_policy_rows(path):
    return _common().load_topic_policy(path)


def topic_title(topic_id, policy_path=None):
    """정책 행의 topic 문자열 (= topics.kisti.jsonl 의 title). run_demo/run_pilot 이 slug 만 받고 제목을 여기서 푼다."""
    rows = load_policy_rows(policy_path or default_policy_path())
    if topic_id not in rows:
        raise KeyError(f'topic_id {topic_id!r} 가 정책 파일에 없다: {sorted(rows)}')
    return rows[topic_id]['topic']


class RetrievalPolicy:
    """한 topic 의 허용 집합. 무거운 것(허용 id 집합·선택자용 인덱스 id)은 한 번만 계산해 캐시한다."""

    def __init__(self, row, policy_path, dates, sidecar_meta, paper_dates_path):
        self.row = row
        self.policy_path = os.path.abspath(policy_path)
        self.paper_dates_path = os.path.abspath(paper_dates_path)
        self.topic_id = row['topic_id']
        self.topic = row.get('topic')
        self.cutoff = row['retrieval_cutoff_at']
        rp = _common()
        self._cutoff_date = rp.parse_day(self.cutoff)
        self.exclude_ids = [str(e).strip() for e in (row.get('exclude_ids') or []) if str(e).strip()]
        self._exclude_lower = {e.lower() for e in self.exclude_ids}
        self.dates = dates
        self.sidecar_meta = sidecar_meta or {}
        self._rp = rp
        self._allowed = None
        self._summary = None
        self._db_cache = {}

    # ---------------------------------------------------------------- 판정
    def is_excluded(self, pid):
        return str(pid).strip().lower() in self._exclude_lower

    def date_of(self, pid):
        """sidecar 의 공개일 문자열. 없으면 None (→ 불허)."""
        return self.dates.get(pid)

    def is_allowed(self, pid):
        """논문 DB id 하나에 대한 판정 -- sidecar 날짜만 본다 (export date 는 연 단위라 쓰지 않는다)."""
        if self.is_excluded(pid):
            return False
        d = self.dates.get(pid)
        return d is not None and self._rp.is_allowed(d, self._cutoff_date)

    def allows_arxiv_id(self, pid):
        """outline DB(human survey) 용: sidecar 밖 자산이라 arXiv id 의 YYMM(v1 투고월, month 정밀도)로 판정한다.
        arXiv 형식이 아니거나 base id 가 제외 목록에 있으면 불허."""
        base = _arxiv_base(pid)
        if base is None or base.lower() in self._exclude_lower:
            return False
        ym = self._rp.arxiv_yymm(pid)
        return ym is not None and self._rp.is_allowed(ym, self._cutoff_date)

    # ---------------------------------------------------------------- 집합
    def allowed_ids(self):
        """sidecar 전편 중 허용 id 집합 (view 기준). 검색은 이 안에서 돈다."""
        if self._allowed is None:
            self._allowed = self._rp.allowed_ids(self.dates, self._cutoff_date, self.exclude_ids)
        return self._allowed

    def summary(self):
        """허용/제외 사유별 편수 (sidecar 기준) -- AutoSurvey 의 retrieval_policy 블록과 같은 항목."""
        if self._summary is None:
            self._summary = self._rp.allowed_summary(self.dates, self._cutoff_date, self.exclude_ids)
        return self._summary

    def db_view(self, arxivid_to_index):
        """논문 DB(id → stored index) 위에서의 허용 목록. DB 순서를 보존한다 (선택자 인자 순서가 된다).

        반환: dict(kept=[id…], index_ids=[int…], n_db, n_allowed, n_excluded_id, n_no_date, n_after_cutoff,
                   excluded_present=[id…], fingerprint)
        같은 매핑 객체에 대해 한 번만 계산한다 (아웃라인·집필 두 단계가 같은 매핑을 쓴다).
        """
        key = id(arxivid_to_index)
        if key in self._db_cache:
            return self._db_cache[key]
        allowed = self.allowed_ids()
        kept, index_ids = [], []
        n_excluded_id = n_no_date = n_after = 0
        excluded_present = []
        for pid, idx in arxivid_to_index.items():
            if pid in allowed:
                kept.append(pid)
                index_ids.append(int(idx))
            elif self.is_excluded(pid):
                n_excluded_id += 1
                excluded_present.append(pid)
            elif pid not in self.dates:
                n_no_date += 1
            else:
                n_after += 1
        view = {'kept': kept, 'index_ids': index_ids, 'n_db': len(arxivid_to_index), 'n_allowed': len(kept),
                'n_excluded_id': n_excluded_id, 'n_no_date': n_no_date, 'n_after_cutoff': n_after,
                'excluded_present': excluded_present, 'fingerprint': fingerprint(kept)}
        self._db_cache[key] = view
        return view

    # ---------------------------------------------------------------- 기록
    def describe(self):
        return (f"topic_id={self.topic_id} cutoff<{self.cutoff} (근거: {self.row.get('gt_first_public_source')}) "
                f"제외 id {len(self.exclude_ids)}개 {self.exclude_ids}")

    def log_lines(self, db_view=None, stage=''):
        """[policy] 로그 두 줄 -- cutoff·허용 편수·제외 사유별 편수."""
        s = self.summary()
        ex = s['excluded']
        tag = f'[policy/{stage}]' if stage else '[policy]'
        lines = [f"{tag} {self.describe()}",
                 f"{tag} sidecar 허용 {s['allowed']:,}/{s['total']:,}편 -- 제외: exclude_id {ex.get('exclude_id', 0)} · "
                 f"no_date {ex.get('no_date', 0)} · after_cutoff day {ex.get('after_cutoff_day', 0):,} / "
                 f"month {ex.get('after_cutoff_month', 0):,} / year {ex.get('after_cutoff_year', 0):,}"]
        if db_view is not None:
            lines.append(f"{tag} DB 허용 {db_view['n_allowed']:,}/{db_view['n_db']:,}편 -- 제외: exclude_id "
                         f"{db_view['n_excluded_id']} · no_date {db_view['n_no_date']} · after_cutoff "
                         f"{db_view['n_after_cutoff']:,}; 허용 id 정렬 sha256 {db_view['fingerprint'][:16]}…")
            if db_view['excluded_present']:
                lines.append(f"{tag} WARNING: 제외 id 가 DB 인덱스에 있다(view 단계 누락) -- 선택자가 차단한다: "
                             f"{db_view['excluded_present']}")
        return lines

    def manifest(self, arxivid_to_index=None):
        """run_manifest.json 의 retrieval_policy 블록."""
        s = self.summary()
        meta = self.sidecar_meta
        block = {
            'topic_id': self.topic_id,
            'topic': self.topic,
            'retrieval_cutoff_at': self.cutoff,
            'gt_first_public_at': self.row.get('gt_first_public_at'),
            'gt_first_public_source': self.row.get('gt_first_public_source'),
            'exclude_ids': self.exclude_ids,
            'status': self.row.get('status'),
            'corpus_snapshot_id': self.row.get('corpus_snapshot_id'),
            'policy_file': self.policy_path,
            'policy_file_sha256': _sha256_file(self.policy_path) if os.path.exists(self.policy_path) else None,
            'rule': 'upper_bound(sidecar date) < cutoff; 당일·날짜 없음 제외; exclude_ids 는 날짜 무관 차단; '
                    '검색은 허용 집합 안에서 (IDSelectorBatch)',
            'sidecar': {'path': self.paper_dates_path,
                        'meta': {k: meta.get(k) for k in ('created_at', 'builder', 'view', 'view_papers_sha256',
                                                          'view_created_at', 'records', 'dated', 'by_precision',
                                                          'by_source', 'rule')}},
            'view_sha256': meta.get('view_papers_sha256'),
            'view_created_at': meta.get('view_created_at'),
            'sidecar_allowed': s['allowed'],
            'sidecar_total': s['total'],
            'sidecar_excluded': s['excluded'],
            'sidecar_dated_by_precision': s['dated_by_precision'],
        }
        if arxivid_to_index is not None:
            v = self.db_view(arxivid_to_index)
            block.update({'db_records': v['n_db'], 'allowed': v['n_allowed'],
                          'allowed_fingerprint_sha256': v['fingerprint'],
                          'db_excluded': {'exclude_id': v['n_excluded_id'], 'no_date': v['n_no_date'],
                                          'after_cutoff': v['n_after_cutoff']},
                          'excluded_ids_present_in_db': v['excluded_present']})
        return block


def _arxiv_base(pid):
    """'2308.10792v5' → '2308.10792', 'cs/0503039v2' → 'cs/0503039'. arXiv 형식이 아니면 None."""
    if _common().arxiv_yymm(pid) is None:
        return None
    return re.sub(r'v\d+$', '', str(pid).strip())


def load_retrieval_policy(topic_id, policy_path=None, paper_dates_path=None, topic=None):
    """topic_id 로 정책을 고르고 sidecar 를 읽는다. topic_id 가 비었거나 'none' 이면 None (정책 없음).

    거부하는 경우: 정책 파일에 없는 topic_id, status != ok (needs_review), --topic 문자열이 정책 행의 topic 과 다름
    (잘못된 cutoff 로 $ 를 쓰는 것을 막는다). 실패는 DB 로드(수 분) 전에 나야 하므로 main 은 이것을 가장 먼저 부른다.
    """
    topic_id = (topic_id or '').strip()
    if not topic_id or topic_id.lower() == NO_POLICY:
        return None
    policy_path = policy_path or default_policy_path()
    paper_dates_path = paper_dates_path or default_paper_dates_path()
    if not os.path.exists(policy_path):
        raise FileNotFoundError(f'topic 정책 파일이 없다: {policy_path} (SURVEYFORGE_TOPIC_POLICY)')
    if not os.path.exists(paper_dates_path):
        raise FileNotFoundError(f'문헌 날짜 sidecar 가 없다: {paper_dates_path} (SURVEYFORGE_PAPER_DATES)')
    rows = load_policy_rows(policy_path)
    if topic_id not in rows:
        raise KeyError(f'topic_id {topic_id!r} 가 {policy_path} 에 없다. 있는 값: {sorted(rows)}')
    row = rows[topic_id]
    if row.get('status') != 'ok':
        raise RuntimeError(f'정책 행 {topic_id} 의 status={row.get("status")!r} (ok 아님) -- '
                           f'review_notes: {row.get("review_notes")}. 검토 전에는 돌리지 않는다')
    if topic is not None and topic.strip() != (row.get('topic') or '').strip():
        raise RuntimeError(f'--topic {topic!r} 이 정책 행 {topic_id} 의 topic {row.get("topic")!r} 과 다르다. '
                           f'topic 문자열은 topics.kisti.jsonl 의 title 그대로여야 한다 (run_demo 는 slug 만 주면 제목을 푼다)')
    rp = _common()
    dates, meta = rp.load_paper_dates(paper_dates_path)
    if not dates:
        raise RuntimeError(f'sidecar 가 비어 있다: {paper_dates_path}')
    return RetrievalPolicy(row, policy_path, dates, meta, paper_dates_path)
