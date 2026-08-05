import glob
import re
import math
import os
from typing import List
import tiktoken
import json
import pandas as pd
from datetime import timedelta
import faiss

from langchain_core.documents import Document
from langchain_community.docstore.in_memory import InMemoryDocstore


def find_index(db_path, stem):
    """`<db_path>/<stem>_*.bin` 을 찾는다. 정확히 하나여야 한다.

    인덱스 파일명에는 코퍼스 컷오프가 박혀 있다 (`..._FROM_2012_0101_TO_240926.bin`).
    경로를 하드코딩하면 DB를 갱신할 때마다 코드를 고쳐야 하고, 그렇다고 파일명을
    고정해 버리면 이름이 실제 컷오프를 속이게 된다. 글롭으로 찾으면 파일명이 계속
    컷오프를 말해 주면서 `--db_path` 하나로 스냅샷을 갈아탈 수 있다.

    stem 은 서로의 접두사가 아니다 — `faiss_paper_title_embeddings_*` 는
    `faiss_paper_title_abs_embeddings_...` 를 잡지 않는다 (`_` 다음이 다르다).
    """
    hits = sorted(glob.glob(os.path.join(db_path, f'{stem}_*.bin')))
    if len(hits) != 1:
        raise RuntimeError(
            f'{db_path}/{stem}_*.bin 이 {len(hits)}개다 (정확히 1개여야 한다): '
            f'{[os.path.basename(h) for h in hits]}')
    return hits[0]


def cutoff_log(message, saving_path=None):
    """Print a cutoff/coverage message and, when given a run directory, persist it.

    run_demo.py echoes the child's stdout to the console but only greps token counts
    out of it (run_demo.py:129,138), so a printed warning does not survive the run.
    cutoff_report.log lives next to the survey it describes. It is deliberately not
    time_cost.log -- that file gets one line per RAG call and is scanned for timings.
    """
    print(message)
    if saving_path:
        with open(f"{saving_path}/cutoff_report.log", "a") as f:
            f.write(message + "\n")


class tokenCounter():

    def __init__(self) -> None:
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.model_price = {}
        
    def num_tokens_from_string(self, string:str) -> int:
        return len(self.encoding.encode(string))

    def num_tokens_from_list_string(self, list_of_string:List[str]) -> int:
        num = 0
        for s in list_of_string:
            num += len(self.encoding.encode(s))
        return num
    
    def compute_price(self, input_tokens, output_tokens, model):
        return (input_tokens/1000) * self.model_price[model][0] + (output_tokens/1000) * self.model_price[model][1]

    def text_truncation(self,text, max_len = 1000):
        encoded_id = self.encoding.encode(text, disallowed_special=())
        return self.encoding.decode(encoded_id[:min(max_len,len(encoded_id))])

def autosurvey_db_json2doc_langchain(json_path):
    """
        origion json file: {'cs_paper_info':{'1':{}, '2':{}, ...}}
        step 1: transfer each paper's value to Document class 
                {'cs_paper_info':{'1': Document(), '2': Document(), ...}}
        step 2: store all Document in InMemoryDocstore
    
        Args:
            json_path: path to the json file
        Returns:
            doc_list: list of Document, for Retriever
            doc_store: InMemoryDocstore(dict of Document), for Vectorstore
            index2id: dict of index to id {0: '1', 1: '2', ...}
    """
    doc_list = []
    with open(json_path, 'r') as f:
        doc_db = json.load(f)
    doc_dict_db = {}
    for doc_id, doc_dict in doc_db['cs_paper_info'].items():
        content = doc_dict['abs']
        doc_dict.pop('abs', None)
        doc_dict_db[doc_dict['id']] = Document(
            page_content=content,
            metadata=doc_dict,
        )
        doc_list.append(
            Document(
                page_content=content, 
                metadata=doc_dict
            )
        )
    
    number_of_docs = len(doc_db['cs_paper_info'])
    index2id = {int(index): str(index+1) for index in range(number_of_docs)}
    
    doc_store = InMemoryDocstore(doc_dict_db)
    return doc_list, doc_store, index2id

def postprocess_results_langchain2id(results):
        """
            Args:
                results: list[list[Document]], list of retrieved documents for each query
            Returns:
                references_titles:
                references_abs:
        """
        references_ids = []
        for result in results:
            references_ids.extend([doc.metadata['id'] for doc in result])
        
        return references_ids


def sort_by_citation(documents, top_k=3):
    # sort the documents by citation_count
    documents = sorted(documents, key=lambda x: x.metadata['citation_count'], reverse=True)
    if top_k > len(documents):
        top_k = len(documents)
        print(f"Only {top_k} documents available.")
    # get the top 3 documents
    top_docs = documents[:top_k]
    return top_docs

def get_time_windows(time_oldest, time_newest, period):
    # Convert strings to Timestamps
    time_oldest = pd.to_datetime(time_oldest)
    time_newest = pd.to_datetime(time_newest)
    
    # List to hold the time windows
    time_windows = []
    
    # Generate the time windows
    current_start = time_oldest
    # `<=`, not `<`: when time_newest lands exactly on a window boundary
    # (time_oldest + k*period years) the loop used to stop one window short, so papers
    # dated on that day matched no window and were discarded. Inert at the stock
    # cutoffs -- after the 2024-01-01 window current_start is 2026-01-01, which is
    # past 2024-09-26 under either comparison.
    while current_start <= time_newest:
        current_end = current_start + pd.DateOffset(years=period) - timedelta(days=1)
        if current_end > time_newest:
            current_end = time_newest
      
        time_windows.append((current_start, current_end))
        
        # Advance start for the next window
        current_start += pd.DateOffset(years=period)
    
    return time_windows

def sort_by_citation_period(documents, top_k=10, period=2,
                            time_oldest='2012-01-01', time_newest='2024-09-26'):
    """Citation-rank documents within contiguous `period`-year windows.

    The windows cover exactly [time_oldest, time_newest]; a document whose date falls
    in none of them is dropped. That is the whole hazard: a time_newest left behind the
    database makes every newer paper uncitable with no error and no other symptom. So
    the count of dropped documents is returned rather than discarded.

    The defaults are the values that used to be hardcoded here, so a caller that passes
    neither keyword behaves exactly as before.

    Returns:
        (top_docs, n_outside_window)
    """
    time_windows = get_time_windows(time_oldest, time_newest, period)
    # ratio = top_k/total_doc, for each period, get top_k*period documents
    total_doc = len(documents)
    if total_doc == 0:
        # ratio below would raise ZeroDivisionError. Unreachable at the stock retrieval
        # settings, but a mis-set cutoff makes it reachable.
        return [], 0
    ratio = top_k / total_doc
    # Hoisted out of the window loop: it used to re-parse every date once per window.
    doc_dates = [pd.to_datetime(doc.metadata['date']) for doc in documents]
    covered = [False] * total_doc
    top_docs = []
    for start, end in time_windows:
        docs_in_period = []
        for i, doc in enumerate(documents):
            if doc_dates[i] >= start and doc_dates[i] <= end:
                docs_in_period.append(doc)
                covered[i] = True

        if len(docs_in_period) == 0:
            continue
        top_k_period = math.ceil(ratio*len(docs_in_period))

        selected_docs = sort_by_citation(docs_in_period, top_k_period)
        top_docs.extend(selected_docs)

    # Actual window membership, not an [oldest, newest] range check: get_time_windows
    # can stop one window short of time_newest, and a range check would miss that.
    return top_docs, covered.count(False)

def get_index_filter(arxivid_to_index, results_arxivid):
    # transfer arxivid to index in outline_rag_results
    results_index = [0] * len(results_arxivid)
    for i in range(len(results_arxivid)):
        results_index[i] = arxivid_to_index[results_arxivid[i]]

    id_selector = faiss.IDSelectorArray(results_index)
    index_filter = {
        'id_selector': id_selector,
    }
    return index_filter


_NEW_ID = re.compile(r'^(\d{2})(\d{2})\.\d{4,5}')          # 2608.12345v1
_OLD_ID = re.compile(r'^[a-zA-Z][\w.-]*/(\d{2})(\d{2})\d+')  # cs/0503039v25, quant-ph/0412073v1


def arxiv_month(arxivid):
    """arXiv id -> (year, month). Returns None if the id is in neither known format.

    Two things make a plain string compare on the prefix wrong:

      - Old-style ids ('cs/0503039') carry no dot before the archive name, so
        `split('.')[0]` yields the whole id and 'c' > '2' sorts every one of them
        above any YYMM cutoff. They then vanish from retrieval with no signal --
        992 of them arrived with the 2026-08 increment.
      - Old-style years wrap: 9107 (1991) through 0703 (2007). Lexically '9203'
        sorts above '2608', so 1992 papers would be dropped as "too new".

    Returning a real (year, month) makes both cases order correctly.
    """
    m = _NEW_ID.match(arxivid)
    if m:                                    # new style began 0704 and has not wrapped
        return (2000 + int(m.group(1)), int(m.group(2)))
    m = _OLD_ID.match(arxivid)
    if m:
        yy = int(m.group(1))
        return (1900 + yy if yy >= 91 else 2000 + yy, int(m.group(2)))
    return None


def filter_arxivids_by_prefix(arxivid_list, id_cutoff):
    """Ids published on or before `id_cutoff` (a YYMM string), in the order given.

    Kept pure and separate from the IDSelectorArray it feeds so it can be diffed
    against the expression it replaces -- IDSelectorArray does not expose its contents.
    Order matters: it becomes the selector's argument order.

    Unparseable ids are kept rather than dropped: silently losing papers is the
    failure this whole mechanism exists to prevent.
    """
    cutoff = arxiv_month(f'{id_cutoff}.00000')
    if cutoff is None:
        raise ValueError(f'id_cutoff must be a 4-digit YYMM string, got {id_cutoff!r}')
    kept = []
    for aid in arxivid_list:
        month = arxiv_month(aid)
        if month is None or month <= cutoff:
            kept.append(aid)
    return kept


def get_index_filter_by_id_prefix(arxivid_to_index, id_cutoff, stage='', saving_path=None):
    """get_index_filter() restricted to papers at or before `id_cutoff` (YYMM prefix).

    Reports how many papers the cutoff excluded. After a database update with the
    cutoff left at its default that number is the count of papers made unreachable,
    and it is otherwise invisible anywhere in the output.
    """
    arxivid_list = list(arxivid_to_index.keys())
    kept = filter_arxivids_by_prefix(arxivid_list, id_cutoff)
    dropped = len(arxivid_list) - len(kept)
    msg = (f"[cutoff/{stage}] arXiv id prefix <= {id_cutoff}: "
           f"{len(kept)}/{len(arxivid_list)} papers retrievable, {dropped} excluded")
    if dropped:
        msg += (f". WARNING: those {dropped} papers cannot appear in the survey at any "
                f"stage; raise SURVEYFORGE_PAPER_ID_CUTOFF if that is not intended")
    cutoff_log(msg, saving_path)
    if not kept:
        raise RuntimeError(
            f"--paper_id_cutoff={id_cutoff} excludes every paper in the database "
            f"(ids run to {max(a.split('.')[0] for a in arxivid_list)}); nothing can be retrieved.")
    return get_index_filter(arxivid_to_index, kept)
