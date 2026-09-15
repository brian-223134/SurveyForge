import os
import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer,  AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer
import h5py
from src.utils import tokenCounter, find_index, EMBED_DEVICE
import json
from tqdm import tqdm
import faiss
from tinydb import TinyDB, Query

import logging

logging.basicConfig()
logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)
logging.getLogger("langchain.retrievers.re_phraser").setLevel(logging.INFO)


class database():

    def __init__(self, db_path, embedding_model, policy=None) -> None:
        
        self.embedding_model = SentenceTransformer(embedding_model, trust_remote_code=True)

        self.embedding_model.to(torch.device(EMBED_DEVICE))

        self.db = TinyDB(f'{db_path}/arxiv_paper_db_with_cc.json')
        self.table = self.db.table('cs_paper_info')

        self.User = Query()
        self.token_counter = tokenCounter()
        self.title_loaded_index = faiss.read_index(find_index(db_path, 'faiss_paper_title_embeddings'))

        self.abs_loaded_index = faiss.read_index(find_index(db_path, 'faiss_paper_title_abs_embeddings'))
        self.id_to_index, self.index_to_id = self.load_index_arxivid(db_path)
        # topic 정책 (src/retrieval_policy.RetrievalPolicy). 파이프라인은 이 객체를 id → 레코드 조회에만 쓰지만
        # (get_paper_info_from_ids), 직접 조회·자체 FAISS 검색도 같은 허용 집합으로 제한한다 -- 어떤 경로로도
        # 허용 밖 문헌이 프롬프트에 들어갈 수 없어야 한다 (docs/retrieval-policy.md).
        self.policy = policy
        self._allowed_db = None
        self._search_params = None
        self.lookup_dropped = 0
        if policy is not None:
            view = policy.db_view(self.id_to_index)
            self._allowed_db = set(view['kept'])
            # 선택자 객체는 살아 있어야 한다 (SearchParameters 는 참조만 든다)
            self._sel = faiss.IDSelectorBatch(np.asarray(view['index_ids'], dtype='int64'))
            self._search_params = faiss.SearchParameters(sel=self._sel)

    def load_index_arxivid(self, db_path):
        with open(f'{db_path}/arxivid_to_index_abs.json','r') as f:
            id_to_index = json.loads(f.read())
        id_to_index = {id: int(index) for id, index in id_to_index.items()}
        index_to_id = {int(index): id for id, index in id_to_index.items()}
        return id_to_index, index_to_id
    
    def get_embeddings(self, batch_text):
        # batch_text = ['search_query: ' + _ for _ in batch_text]
        embeddings = self.embedding_model.encode(batch_text)
        return embeddings

    def get_embeddings_documents(self, batch_text):
        # batch_text = ['search_document: ' + _ for _ in batch_text]
        embeddings = self.embedding_model.encode(batch_text)
        return embeddings
        
    def _search(self, index, query_vectors, top_k):
        """정책이 있으면 허용 집합 선택자 안에서 검색한다 (IndexIDMap 이 stored id 로 번역해 준다)."""
        if self._search_params is not None:
            return index.search(query_vectors, top_k, params=self._search_params)
        return index.search(query_vectors, top_k)

    def batch_search(self, query_vectors, top_k=1, title=False):
        query_vectors = np.array(query_vectors).astype('float32')
        distances, indices = self._search(self.title_loaded_index if title else self.abs_loaded_index,
                                          query_vectors, top_k)
        results = []
        for i, query in tqdm(enumerate(query_vectors)):
            result = [(self.index_to_id[idx], distances[i][j]) for j, idx in enumerate(indices[i]) if idx != -1]
            results.append([_[0] for _ in result])
        return results

    def search(self, query_vector, top_k=1, title=False):
        query_vector = np.array([query_vector]).astype('float32')
        distances, indices = self._search(self.title_loaded_index if title else self.abs_loaded_index,
                                          query_vector, top_k)
        results = [(self.index_to_id[idx], distances[0][i]) for i, idx in enumerate(indices[0]) if idx != -1]
        return [_[0] for _ in results]

    def get_ids_from_query(self, query, num,  shuffle = False):
        q = self.get_embeddings([query])[0]
        return self.search(q, top_k=num)

    def is_allowed(self, pid):
        return self._allowed_db is None or pid in self._allowed_db

    def get_paper_info_from_ids(self, ids):
        if self._allowed_db is not None:
            kept = [i for i in ids if i in self._allowed_db]
            dropped = len(ids) - len(kept)
            if dropped:
                # 검색 결과는 전부 선택자를 거치므로 여기 오면 안 된다 -- 왔다면 우회 경로가 있다는 뜻이라 찍어 둔다
                self.lookup_dropped += dropped
                print(f'[policy/lookup] 직접 조회에서 허용 밖 id {dropped}건 차단 (누적 {self.lookup_dropped})')
            ids = kept
        result = self.table.search(self.User.id.one_of(ids))
        return result


class database_survey():

    def __init__(self, db_path, embedding_model, policy=None) -> None:
        
        self.embedding_model = SentenceTransformer(embedding_model, trust_remote_code=True)

        self.embedding_model.to(torch.device(EMBED_DEVICE))

        self.db = TinyDB(f'{db_path}/surveys_arxiv_paper_db.json')
        self.table = self.db.table('survey_paper_info')

        self.User = Query()
        self.token_counter = tokenCounter()
        self.title_loaded_index = faiss.read_index(find_index(db_path, 'faiss_survey_title_embeddings'))

        self.abs_loaded_index = faiss.read_index(find_index(db_path, 'faiss_survey_title_abs_embeddings'))
        self.id_to_index, self.index_to_id = self.load_index_arxivid(db_path)
        # 아웃라인 예시 검색에서 제외할 arXiv base id (쉼표 구분). 논문 DB는 KISTI
        # view 단계에서 벤치마크 GT를 제외하지만, survey DB(human survey 18,816편)는
        # 코퍼스 범위 밖이라 GT 서베이가 그대로 남아 있다 — 여기서 거른다.
        # docs/kisti-integration.md §0 · docs/retrieval-policy.md.
        self.exclude_base_ids = {v.strip() for v in os.environ.get(
            'SURVEYFORGE_SURVEY_EXCLUDE_IDS', '').split(',') if v.strip()}
        # topic 정책: outline DB 는 sidecar 밖 자산(arXiv id 에 버전 접미사)이라 id 의 YYMM(v1 투고월)로
        # cutoff 를 판정하고, 정책 exclude_ids 도 base id 로 막는다. GT 이후에 나온 human survey 를 아웃라인
        # 예시로 보여 주는 것도 cutoff 이후 지식이다 (origin 문서 §5.2). 정책이 있으면 검색 자체를
        # 허용 집합 선택자 안에서 돌리고(사후 필터 아님), 없으면 종전 경로(과다 검색 후 env 제외).
        self.policy = policy
        self._search_params = None
        self.policy_report = None
        if policy is not None:
            self._apply_policy(policy)

    def load_index_arxivid(self, db_path):
        with open(f'{db_path}/surveys_arxivid_to_index_abs.json','r') as f:
            id_to_index = json.loads(f.read())
        id_to_index = {id: int(index) for id, index in id_to_index.items()}
        index_to_id = {int(index): id for id, index in id_to_index.items()}
        return id_to_index, index_to_id
    
    def get_embeddings(self, batch_text):
        # batch_text = ['search_query: ' + _ for _ in batch_text]
        embeddings = self.embedding_model.encode(batch_text)
        return embeddings

    def get_embeddings_documents(self, batch_text):
        # batch_text = ['search_document: ' + _ for _ in batch_text]
        embeddings = self.embedding_model.encode(batch_text)
        return embeddings
        
    def batch_search(self, query_vectors, top_k=1, title=False):
        query_vectors = np.array(query_vectors).astype('float32')
        distances, indices = self._search(self.title_loaded_index if title else self.abs_loaded_index,
                                          query_vectors, top_k)
        results = []
        for i, query in tqdm(enumerate(query_vectors)):
            result = [(self.index_to_id[idx], distances[i][j]) for j, idx in enumerate(indices[i]) if idx != -1]
            results.append([_[0] for _ in result])
        return results

    def search(self, query_vector, top_k=1, title=False):
        query_vector = np.array([query_vector]).astype('float32')
        distances, indices = self._search(self.title_loaded_index if title else self.abs_loaded_index,
                                          query_vector, top_k)
        results = [(self.index_to_id[idx], distances[0][i]) for i, idx in enumerate(indices[0]) if idx != -1]
        return [_[0] for _ in results]

    def _apply_policy(self, policy):
        allowed, n_after, n_excl, n_unparsed = [], 0, 0, 0
        for sid, idx in self.id_to_index.items():
            base = sid.split('v')[0]
            if base in self.exclude_base_ids or policy.is_excluded(base) or policy.is_excluded(sid):
                n_excl += 1
            elif policy.allows_arxiv_id(sid):
                allowed.append(int(idx))
            elif policy._rp.arxiv_yymm(sid) is None:
                n_unparsed += 1
            else:
                n_after += 1
        n = len(self.id_to_index)
        self.policy_report = {'allowed': len(allowed), 'total': n, 'excluded_after_cutoff': n_after,
                              'excluded_gt': n_excl, 'excluded_unparsed_id': n_unparsed, 'rule': 'arXiv id YYMM (month) < cutoff'}
        print(f"[policy/survey-db] cutoff<{policy.cutoff} outline DB(human survey) 허용 {len(allowed):,}/{n:,}편 -- "
              f"제외: cutoff 이후 {n_after:,} · GT 제외(env ∪ 정책) {n_excl} · id 형식 불명 {n_unparsed}")
        if not allowed:
            raise RuntimeError(f'정책 {policy.topic_id} 적용 후 outline DB 에 허용 서베이가 0편이다')
        self._sel = faiss.IDSelectorBatch(np.asarray(allowed, dtype='int64'))
        self._search_params = faiss.SearchParameters(sel=self._sel)

    def _search(self, index, query_vectors, top_k):
        if self._search_params is not None:
            return index.search(query_vectors, top_k, params=self._search_params)
        return index.search(query_vectors, top_k)

    def get_ids_from_query(self, query, num,  shuffle = False):
        q = self.get_embeddings([query])[0]
        if self._search_params is not None:
            # 선택자가 cutoff 이후·GT 제외분을 이미 뺐다 -- 허용 집합 안의 정확한 top-num
            return self.search(q, top_k=num)
        if not self.exclude_base_ids:
            return self.search(q, top_k=num)
        # 제외분만큼 더 뽑아 거른 뒤 num으로 자른다. 서베이 id는 버전 접미사가
        # 붙어 있으므로 base id로 비교한다.
        got = self.search(q, top_k=num + len(self.exclude_base_ids))
        kept = [i for i in got if i.split('v')[0] not in self.exclude_base_ids]
        if len(got) - len(kept):
            print(f'[survey-exclude] 예시 후보에서 GT 서베이 {len(got) - len(kept)}건 제외')
        return kept[:num]

    def get_paper_info_from_ids(self, ids):
        result = self.table.search(self.User.id.one_of(ids))
        return result
