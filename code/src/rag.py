import json
import jsonlines
import faiss
import time
import logging
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.runnables import RunnableLambda

from src.faiss_param import FAISS_param as FAISS
from .utils import (autosurvey_db_json2doc_langchain, postprocess_results_langchain2id,
                    sort_by_citation_period, cutoff_log)

logging.basicConfig()
logging.getLogger("langchain.retrievers.multi_query").setLevel(logging.INFO)
logging.getLogger("langchain.retrievers.re_phraser").setLevel(logging.INFO)

class GeneralRAG_langchain():
    def __init__(self, 
                 args,
                 retriever_type: str = 'vectorstore',
                 retriever_name: str = 'FAISS',
                 index_db_path: str = None,
                 doc_db_path: str = None,
                 arxivid_to_index_path = None,
                 embedding_model: str = None,
                 ):
        self.args = args
        self.retriever_type = retriever_type
        self.retriever_name = retriever_name

        # How much the citation window threw away over the whole run. _rerank runs once
        # per subsection query, so it warns on the first drop and only counts after that.
        self.window_drops = 0
        self.window_docs = 0
        
        self.index_db_path = index_db_path
        self.doc_db_path = doc_db_path
        self.arxivid_to_index_path = arxivid_to_index_path
        
        self.embedding_model = embedding_model

        # load embedding fucntion
        self.embedding_function = HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            model_kwargs={'device': 'cuda', 'trust_remote_code': True},
        )
     
        # load local rag database
        self.rag_data = self._load_data()
        
        print(f"RAG initialized with {self.retriever_type}: {self.retriever_name} based on {self.index_db_path.split('/')[-1]}.")
    
    def _load_data(self):
        # load embedded text as index
        if self.index_db_path is not None:
            if 'faiss' in self.index_db_path:
                index_db = faiss.read_index(self.index_db_path)
            else:
                # NOTE: elif other vectorstore
                index_db = None
        else:
            index_db = None
        
        # load doc database and get index2id
        doc_list, doc_store, _ = autosurvey_db_json2doc_langchain(self.doc_db_path)
        # load arxiv_id to index mapping
        self.id_to_index, self.index_to_id = self.load_index_arxivid(self.arxivid_to_index_path)

        rag_data = {
            'index_db': index_db, # embeddings for similarity calculation
            'doc_list': doc_list, # docs: list of Document, for building Retriever
            'doc_store': doc_store, # docs: docstore dict, for building Vectorstore
            'index2id': self.index_to_id, # mapping embeddings-id to docs-id
        }
        return rag_data
    
    def load_index_arxivid(self, arxivid_to_index_path):
        with open(arxivid_to_index_path,'r') as f:
            id_to_index = json.loads(f.read())
        id_to_index = {id: int(index) for id, index in id_to_index.items()}
        index_to_id = {int(index): id for id, index in id_to_index.items()}
        return id_to_index, index_to_id
    
    def _init_RAG(self, retriever_cfg=None):
        # Initialize RAG with Retriever or Vectorstore
        if self.retriever_type == 'vectorstore':
            self._init_vectorstore()
            self.retriever = RunnableLambda(self.vectorstore.search).bind(search_type=retriever_cfg['search_type'],
                                                                          **retriever_cfg['search_kwargs'])      
        elif self.retriever_type == 'retriver':
            self._init_retriever(retriever_cfg) 
        else:
            raise ValueError(f"Retriever type {self.retriever_type} is not supported.")
    
    def _init_retriever(self, retriever_cfg=None):
        if self.retriever_name == 'selfquery':
            raise NotImplementedError(f"Retriever {self.retriever} is not implemented.")
        elif self.retriever_name == 'multiquery':
            raise NotImplementedError(f"Retriever {self.retriever} is not implemented.")
        elif self.retriever_name == 'rephraser':
            raise NotImplementedError(f"Retriever {self.retriever} is not implemented.")
        elif self.retriever_name == 'BM25':
            raise NotImplementedError(f"Retriever {self.retriever} is not implemented.")
        else:
            raise NotImplementedError(f"Retriever {self.retriever} is not implemented.")         
    
    def _init_vectorstore(self):
        # initialize vectorstore
        if self.retriever_name == 'FAISS':
            self.vectorstore = FAISS(
                embedding_function=self.embedding_function ,
                index=self.rag_data['index_db'],
                docstore=self.rag_data['doc_store'],
                index_to_docstore_id=self.rag_data['index2id'],
            )
        elif self.retriever_name == 'OTHER':
            self.vectorstore = InMemoryDocstore()
        else:
            raise NotImplementedError(f"Vectorstore {self.retriever_cfg['name']} is not implemented.")   
    
    def _rerank(self, results, method='citation', top_k=10):
        """
            Rerank the results based on the method
            Args:
                method: str, method for reranking
                results: list of retrieved documents for each query
            Returns:
                results: list of reranked documents for each query
        """
        # if results list has 2dim (multiquery)
        if not results[0]:
            cutoff_log("[cutoff/rerank] WARNING: retrieval returned 0 documents for this "
                       "query; the subsection will be written with no references.",
                       self.args.saving_path)
            return results
        if len(results[0]) < top_k:
            top_k = len(results[0])

        if method == 'raw':
            results[0] = results[0][:top_k]
        elif method == 'citation':
            n_in = len(results[0])
            results[0], n_outside = sort_by_citation_period(
                results[0], top_k,
                time_oldest=self.args.paper_date_oldest,
                time_newest=self.args.paper_date_newest)
            self._note_window_drops(n_in, n_outside)
        elif method == 'hybrid':
            # TODO: implement hybrid rerank
            results[0] = results[0][:top_k]
        else: 
            raise NotImplementedError(f"Rerank method {method} is not implemented.")
        
        return results

    def _note_window_drops(self, n_in, n_outside):
        """Aggregate what the citation window discarded, warning loudly the first time."""
        self.window_docs += n_in
        if not n_outside:
            return
        if self.window_drops == 0:
            cutoff_log(
                f"[cutoff/rerank] WARNING: discarded {n_outside} of {n_in} retrieved papers "
                f"whose date falls outside the citation windows spanning "
                f"[{self.args.paper_date_oldest}, {self.args.paper_date_newest}]. Papers "
                f"outside that span can never be cited, however well they match. Set "
                f"SURVEYFORGE_PAPER_DATE_NEWEST to cover the database.", self.args.saving_path)
        self.window_drops += n_outside

    def report_window_drops(self):
        cutoff_log(f"[cutoff/rerank] total: {self.window_drops}/{self.window_docs} retrieved "
                   f"documents discarded by the citation window "
                   f"[{self.args.paper_date_oldest}, {self.args.paper_date_newest}]",
                   self.args.saving_path)

    def _unite(self, results, method='union'):
        """
            Unite the results based on the method
            Args:
                results: [[q1_docs], [q2_docs] ...]list of retrieved documents for each query
                method: str, method for uniting
            Returns:
                results: list of united documents
        """
        results_list = []
        for i in range(len(results)):
            results_list.extend(results[i])
            
        if method == 'union':
            unite_results = [doc for i, doc in enumerate(results_list) if doc not in results_list[:i]]
        elif method == 'intersection':
            ...
            # results = self.unique_intersection(results)
        elif method == 'hybrid':
            ...
        elif method == 'raw':
            unite_results = results_list
        return [unite_results]
        
    
    def retrieve(self, query, search_type='similarity', top_k=10, filter=None, fetch_k=20, **kwargs):
        """
            RAG for retrieving the top-k documents based on the query
            Args:
                query: str or list[str], query text
                types: types of the input (query, document)
            Returns:
                results: list[list[Document]], list of retrieved documents for each query
        """
        start = time.time()
        self._init_RAG(retriever_cfg={'search_type':search_type, 
                                      'search_kwargs':{'k': top_k}})
        
        if not isinstance(query, list):
            query = [query]
        
        results = self.retriever.batch(inputs=query, filter=filter, fetch_k=fetch_k, **kwargs)
        end = time.time()
        period = end - start
        with open(f"{self.args.saving_path}/time_cost.log", "a") as f:
            f.write(f"RAG API: {period}\n")
        # print(f"##########RAG API Time taken#########: {period}")
        
        return results
    
    def retrieve_id(self, query, search_type='similarity', rerank='raw', top_k=10, max_out=10000, filter=None, fetch_k=20, **kwargs):
        
        results = self.retrieve(query, search_type=search_type, top_k=top_k, filter=filter, fetch_k=fetch_k, **kwargs)
        # print(f"RAG retrieve number: {top_k * len(query)}")

        results = self._unite(results, method='union')
        # print(f"RAG unique number: {len(results[0])}")
        
        if self.args.debug and rerank=='citation':
            with open(f"{self.args.saving_path}/rag_docs_writer_unique.jsonl", 'a') as f:
                writer = jsonlines.Writer(f)
                line = {
                    "total_docs": [{doc.metadata['id']: {'title': doc.metadata['title']}} for doc in results[0]],
                }
                writer.write(line)
        
        results = self._rerank(results, method=rerank, top_k=max_out)
        
        references_ids = postprocess_results_langchain2id(results)
        # print(f"RAG out number: {len(references_ids)}")
        
        if self.args.debug and rerank=='citation':
            with open(f"{self.args.saving_path}/rag_docs_writer_rerank.jsonl", 'a') as f:
                writer = jsonlines.Writer(f)
                line = {
                    "total_docs": [{doc.metadata['id']: {'title': doc.metadata['title'], 'citation': doc.metadata['citation_count']}} for doc in results[0]],
                }
                writer.write(line)
        
        return references_ids

    def retrieve_id4citation(self, query, search_type='similarity', rerank='raw', top_k=10, max_out=10000, filter=None, fetch_k=20, **kwargs):
        
        results = self.retrieve(query, search_type=search_type, top_k=top_k, filter=filter, fetch_k=fetch_k, **kwargs)
        # print(f"RAG retrieve number: {top_k * len(query)}")
        
        references_ids = postprocess_results_langchain2id(results)
        # print(f"RAG out number: {len(references_ids)}")
        
        return references_ids
