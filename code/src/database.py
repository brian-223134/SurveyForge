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

    def __init__(self, db_path, embedding_model) -> None:
        
        self.embedding_model = SentenceTransformer(embedding_model, trust_remote_code=True)

        self.embedding_model.to(torch.device(EMBED_DEVICE))

        self.db = TinyDB(f'{db_path}/arxiv_paper_db_with_cc.json')
        self.table = self.db.table('cs_paper_info')

        self.User = Query()
        self.token_counter = tokenCounter()
        self.title_loaded_index = faiss.read_index(find_index(db_path, 'faiss_paper_title_embeddings'))

        self.abs_loaded_index = faiss.read_index(find_index(db_path, 'faiss_paper_title_abs_embeddings'))
        self.id_to_index, self.index_to_id = self.load_index_arxivid(db_path)

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
        
    def batch_search(self, query_vectors, top_k=1, title=False):
        query_vectors = np.array(query_vectors).astype('float32')
        if title:
            distances, indices = self.title_loaded_index.search(query_vectors, top_k)
        else:
            distances, indices = self.abs_loaded_index.search(query_vectors, top_k)
        results = []
        for i, query in tqdm(enumerate(query_vectors)):
            result = [(self.index_to_id[idx], distances[i][j]) for j, idx in enumerate(indices[i]) if idx != -1]
            results.append([_[0] for _ in result])
        return results

    def search(self, query_vector, top_k=1, title=False):
        query_vector = np.array([query_vector]).astype('float32')
        if title:
            distances, indices = self.title_loaded_index.search(query_vector, top_k)
        else:
            distances, indices = self.abs_loaded_index.search(query_vector, top_k)
        results = [(self.index_to_id[idx], distances[0][i]) for i, idx in enumerate(indices[0]) if idx != -1]
        return [_[0] for _ in results]

    def get_ids_from_query(self, query, num,  shuffle = False):
        q = self.get_embeddings([query])[0]
        return self.search(q, top_k=num)

    def get_paper_info_from_ids(self, ids):
        result = self.table.search(self.User.id.one_of(ids))
        return result


class database_survey():

    def __init__(self, db_path, embedding_model) -> None:
        
        self.embedding_model = SentenceTransformer(embedding_model, trust_remote_code=True)

        self.embedding_model.to(torch.device(EMBED_DEVICE))

        self.db = TinyDB(f'{db_path}/surveys_arxiv_paper_db.json')
        self.table = self.db.table('survey_paper_info')

        self.User = Query()
        self.token_counter = tokenCounter()
        self.title_loaded_index = faiss.read_index(find_index(db_path, 'faiss_survey_title_embeddings'))

        self.abs_loaded_index = faiss.read_index(find_index(db_path, 'faiss_survey_title_abs_embeddings'))
        self.id_to_index, self.index_to_id = self.load_index_arxivid(db_path)
        # 아웃라인 예시 검색에서 제외할 arXiv base id (쉼표 구분). 논문 DB는 공용
        # 코퍼스 view 단계에서 벤치마크 GT를 제외하지만, survey DB는 코퍼스 범위
        # 밖이라 GT 서베이 17편이 그대로 남아 있다 — 여기서 거른다.
        # docs/common-corpus-integration.md §7.
        self.exclude_base_ids = {v.strip() for v in os.environ.get(
            'SURVEYFORGE_SURVEY_EXCLUDE_IDS', '').split(',') if v.strip()}

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
        if title:
            distances, indices = self.title_loaded_index.search(query_vectors, top_k)
        else:
            distances, indices = self.abs_loaded_index.search(query_vectors, top_k)
        results = []
        for i, query in tqdm(enumerate(query_vectors)):
            result = [(self.index_to_id[idx], distances[i][j]) for j, idx in enumerate(indices[i]) if idx != -1]
            results.append([_[0] for _ in result])
        return results

    def search(self, query_vector, top_k=1, title=False):
        query_vector = np.array([query_vector]).astype('float32')
        if title:
            distances, indices = self.title_loaded_index.search(query_vector, top_k)
        else:
            distances, indices = self.abs_loaded_index.search(query_vector, top_k)
        results = [(self.index_to_id[idx], distances[0][i]) for i, idx in enumerate(indices[0]) if idx != -1]
        return [_[0] for _ in results]

    def get_ids_from_query(self, query, num,  shuffle = False):
        q = self.get_embeddings([query])[0]
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
