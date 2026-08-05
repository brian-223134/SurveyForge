"""Characterization tests for the paper-cutoff parameterization.

The retrieval path used to carry three hardcoded cutoffs -- an arXiv id prefix
(`<= '2412'`) in both agents and a `[2012-01-01, 2024-09-26]` window in the citation
reranker. They are now flags. The defaults are the old literals, so **the defaults must
keep reproducing the old behaviour exactly**; that is what makes the published pilot run
reproducible, and it is what these tests pin down.

The pre-change implementations are copied in below rather than fetched from git. Once
the change is committed `git show HEAD:code/src/utils.py` returns the *new* code and a
differential test against it becomes vacuous. Pinning them here keeps the comparison
meaningful for as long as the file survives.

Network-free. The one test that touches the database skips itself when it is absent.

    cd code && ../.venv/bin/python ../tests/test_cutoffs.py
    cd code && ../.venv/bin/python -m pytest ../tests/test_cutoffs.py -q
"""

import json
import math
import os
import random
import sys
from datetime import timedelta

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'code'))

from langchain_core.documents import Document          # noqa: E402
from src.utils import (arxiv_month, filter_arxivids_by_prefix,   # noqa: E402
                       sort_by_citation_period)

DB_MAP = os.path.join(
    os.environ.get('SURVEYFORGE_DATA', '/data2/chanjoong/survey-agent/SurveyForge_data'),
    'database', 'arxivid_to_index_abs.json')


# --------------------------------------------------------------------------- reference
# Verbatim copies of the implementations being replaced. Do not "fix" them.

def _ref_sort_by_citation(documents, top_k=3):
    documents = sorted(documents, key=lambda x: x.metadata['citation_count'], reverse=True)
    if top_k > len(documents):
        top_k = len(documents)
    return documents[:top_k]


def _ref_get_time_windows(time_oldest, time_newest, period):
    time_oldest = pd.to_datetime(time_oldest)
    time_newest = pd.to_datetime(time_newest)
    time_windows = []
    current_start = time_oldest
    while current_start < time_newest:
        current_end = current_start + pd.DateOffset(years=period) - timedelta(days=1)
        if current_end > time_newest:
            current_end = time_newest
        time_windows.append((current_start, current_end))
        current_start += pd.DateOffset(years=period)
    return time_windows


def _ref_sort_by_citation_period(documents, top_k=10, period=2):
    time_oldest = '2012-01-01'
    time_newest = '2024-09-26'
    time_windows = _ref_get_time_windows(time_oldest, time_newest, period)
    total_doc = len(documents)
    ratio = top_k / total_doc
    top_docs = []
    for start, end in time_windows:
        docs_in_period = []
        for doc in documents:
            doc_date = pd.to_datetime(doc.metadata['date'])
            if doc_date >= start and doc_date <= end:
                docs_in_period.append(doc)
        if len(docs_in_period) == 0:
            continue
        top_k_period = math.ceil(ratio * len(docs_in_period))
        top_docs.extend(_ref_sort_by_citation(docs_in_period, top_k_period))
    return top_docs


# ---------------------------------------------------------------------------- fixtures

def mk(n, lo, hi, off=0, seed=None):
    """Documents with dates uniform over [lo, hi], day 15 to stay clear of month ends.

    Keep `hi` at 2023 for "in range" fixtures: the stock window ends 2024-09-26, so
    2024-10..12 would be dropped legitimately and look like a regression.
    """
    rng = random.Random(seed)
    return [Document(page_content='', metadata={
        'id': f'd{i + off}', 'title': f't{i + off}',
        'date': f'{rng.randint(lo, hi)}-{rng.randint(1, 12):02d}-15',
        'citation_count': rng.randint(0, 500)}) for i in range(n)]


def ids_of(docs):
    return [d.metadata['id'] for d in docs]


# ------------------------------------------------------------------------------- tests

def test_defaults_match_the_replaced_implementation():
    """With no keywords, output must be element-for-element what the old code produced."""
    docs = mk(1500, 2012, 2023, seed=0)
    expected = _ref_sort_by_citation_period(docs, 60)
    got, dropped = sort_by_citation_period(docs, 60)
    assert ids_of(got) == ids_of(expected)
    assert dropped == 0


def test_defaults_match_even_when_input_falls_outside_the_window():
    """The old code discarded out-of-window docs silently; the new code counts them.

    The kept set must still be identical -- only the reporting is new.
    """
    docs = mk(1500, 2012, 2023, seed=0) + mk(28, 2024, 2024, off=8000, seed=1)
    expected = _ref_sort_by_citation_period(docs, 60)
    got, dropped = sort_by_citation_period(docs, 60)
    assert ids_of(got) == ids_of(expected)
    assert dropped > 0, "fixture should contain dates after 2024-09-26"


def test_future_papers_are_reported_then_recovered_by_moving_the_cutoff():
    """The case today's database cannot exercise: papers newer than the cutoff.

    This is the whole point of the change. With a stale cutoff they vanish -- that must
    be *visible*; with the cutoff moved forward they must come back.
    """
    docs = mk(1500, 2012, 2023, seed=0)
    future = docs + mk(50, 2025, 2026, off=9000, seed=2)

    kept_stale, dropped_stale = sort_by_citation_period(future, 60)
    assert dropped_stale == 50

    kept_wide, dropped_wide = sort_by_citation_period(future, 60, time_newest='2026-12-31')
    assert dropped_wide == 0
    assert len(kept_wide) > len(kept_stale)


def test_date_exactly_on_a_window_boundary_is_not_dropped():
    """2012-01-01 + 7*2y = 2026-01-01 lands exactly where the window loop used to stop.

    `while current_start < time_newest` emitted no window for that instant, so a paper
    dated on it was discarded however wide the cutoff was set.
    """
    doc = [Document(page_content='', metadata={
        'id': 'edge', 'title': 'edge', 'date': '2026-01-01', 'citation_count': 1})]
    kept, dropped = sort_by_citation_period(doc, 1, time_newest='2026-01-01')
    assert dropped == 0
    assert ids_of(kept) == ['edge']


def test_empty_input_returns_empty_instead_of_dividing_by_zero():
    assert sort_by_citation_period([], 60) == ([], 0)


def test_filter_arxivids_by_prefix_matches_the_replaced_comprehension():
    ids = ['2409.00001v1', '2412.00001v1', '2501.00001v1', '1201.00001v1']
    for cutoff in ('2412', '1512', '2608'):
        assert (filter_arxivids_by_prefix(ids, cutoff)
                == [a for a in ids if a.split('.')[0] <= cutoff])


def test_arxiv_month_reads_both_id_formats():
    assert arxiv_month('2608.12345v1') == (2026, 8)
    assert arxiv_month('0704.0009v1') == (2007, 4)
    assert arxiv_month('cs/0503039v25') == (2005, 3)
    assert arxiv_month('quant-ph/0412073v1') == (2004, 12)
    assert arxiv_month('math.GT/0309136v1') == (2003, 9)
    # old-style years wrap: 91-99 are the 1990s, 00-07 the 2000s
    assert arxiv_month('cs/9203001v1') == (1992, 3)
    assert arxiv_month('nonsense') is None


def test_old_style_ids_are_not_dropped_by_a_modern_cutoff():
    """992 of these arrived with the 2026-08 increment and every one was excluded.

    `'cs/0503039v25'.split('.')[0]` is the whole id, and 'c' sorts above any digit,
    so the plain string compare rejected all of them -- silently, which is exactly
    the failure the cutoff machinery is supposed to prevent.
    """
    ids = ['2608.00001v1', '2409.00001v1', 'cs/0503039v25',
           'cs/9203001v1', 'quant-ph/0412073v1']
    kept = filter_arxivids_by_prefix(ids, '2608')
    assert kept == ids, 'a 2026 cutoff must keep every pre-2007 paper'

    # and a genuinely old cutoff still excludes the ones published after it
    assert filter_arxivids_by_prefix(ids, '0501') == ['cs/9203001v1', 'quant-ph/0412073v1']


def test_unparseable_ids_are_kept_rather_than_silently_dropped():
    assert filter_arxivids_by_prefix(['whatever', '2409.00001v1'], '2412') == \
        ['whatever', '2409.00001v1']


def test_filter_arxivids_by_prefix_on_the_real_id_map():
    """Optional: the stock cutoff must exclude nothing from the shipped database."""
    if not os.path.exists(DB_MAP):
        print(f'  (skipped: {DB_MAP} not present)')
        return
    ids = list(json.load(open(DB_MAP)).keys())
    kept = filter_arxivids_by_prefix(ids, '2412')
    assert kept == [a for a in ids if a.split('.')[0] <= '2412']
    assert len(kept) == len(ids), 'the stock cutoff must be a no-op on the shipped DB'
    assert len(filter_arxivids_by_prefix(ids, '1512')) < len(ids)


if __name__ == '__main__':
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith('test_') or not callable(fn):
            continue
        try:
            fn()
            print(f'PASS  {name}')
        except AssertionError as e:
            failures += 1
            print(f'FAIL  {name}: {e}')
    print(f'\n{failures} failure(s)')
    sys.exit(1 if failures else 0)
