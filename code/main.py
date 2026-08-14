import os
import json
import argparse

from dotenv import load_dotenv

# main.py is also an entry point (run_demo.py spawns it, but it can be run
# directly), so load the repo-root .env here too. Existing env vars take priority.
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, ".env"))

from src.agents.outline_writer import outlineWriter
from src.agents.writer import subsectionWriter
from src.database import database, database_survey
from src.utils import arxiv_month, cutoff_log, find_index

# --- survey-search arm -------------------------------------------------------
# `from src.rag import GeneralRAG_langchain` 를 대체합니다. 검색만 갈아끼우고
# 생성 로직·프롬프트·평가는 그대로 둡니다. 원본으로 되돌리려면 위 한 줄을 복구하세요.
#
# 259 행(초록 인덱스)과 270 행(제목 인덱스)은 성격이 다르므로 config 를 가릅니다 —
# 인용 검증 쿼리는 논문 제목이라 facet 분해가 의미 없고, 켜면 인용 1건마다 LLM 40초가
# 붙습니다. 근거는 ../SURVEY-SEARCH.md §6.
from functools import partial

from survey_search.adapters.surveyforge import SurveySearchRAG
from survey_search.backends.faiss_duckdb import FaissDuckDBBackend
from survey_search.core.facets import load_dotenv as _load_survey_search_env
from survey_search.types import SearchConfig

_load_survey_search_env("/data2/chanjoong/survey-agent/survey-search/.env")  # facet 용 OpenRouter 키

_BACKEND = None

#: 서브섹션 검색의 `rerank` 인자를 강제로 바꿉니다. 비우면 호스트 인자를 그대로 씁니다.
#: `raw` 로 주면 freshness 랭킹이 꺼지고 RRF 순서만 남습니다 — 정전 문헌 손실이
#: freshness 치환에서 오는지 가리는 실험용 스위치입니다.
_SUB_RERANK = os.environ.get("SURVEY_SEARCH_SUBSECTION_RERANK", "").strip()


class _ForceRerank:
    """`retrieve_id` 의 `rerank` 만 바꿔 넘기는 얇은 위임 래퍼.

    설정을 조용히 바꾸면 A/B 가 무의미해지므로 **첫 호출에서 한 번 로그로 남깁니다.**
    나머지 속성(`id_to_index`, `rag_data`, `last_stats`, `report_window_drops` …)은
    그대로 통과시킵니다.
    """

    def __init__(self, inner, rerank):
        self._inner = inner
        self._rerank = rerank
        self._announced = False

    def retrieve_id(self, query, *a, **kw):
        # 호스트는 query 만 위치 인자로 주고 나머지는 전부 키워드입니다
        # (writer.py:76, outline_writer.py:240·247). 위치 인자가 오면 rerank 를
        # 중복 전달하게 되므로 조용히 통과시키지 않고 여기서 멈춥니다.
        if a:
            raise TypeError(
                f"_ForceRerank 는 위치 인자를 받지 못합니다({len(a)}개 왔습니다). "
                "호스트 호출부가 바뀌었다면 이 래퍼를 같이 고치세요.")
        if not self._announced:
            print(f"[survey-search] 서브섹션 rerank {kw.get('rerank', 'raw')!r}"
                  f" -> {self._rerank!r} 강제 (SURVEY_SEARCH_SUBSECTION_RERANK). "
                  f"freshness 랭킹이 꺼집니다.")
            self._announced = True
        kw['rerank'] = self._rerank
        return self._inner.retrieve_id(query, **kw)

    def __getattr__(self, name):
        return getattr(self._inner, name)


def _backend():
    """FAISS 인덱스를 **한 번만** 올립니다 (로드 16초 + 메모리). 두 인스턴스가 공유합니다."""
    global _BACKEND
    if _BACKEND is None:
        _BACKEND = FaissDuckDBBackend()
    return _BACKEND


def GeneralRAG_langchain(*args, **kwargs):
    """아웃라인용 — 토픽 수준 쿼리. facet 이 +18%p 를 내는 곳이고, 여기서만 냅니다."""
    return SurveySearchRAG(*args, backend=_backend(),
                           config=SearchConfig(facets=True, freshness=True, lexical=False),
                           **kwargs)


def GeneralRAG_langchain_subsection(*args, **kwargs):
    """서브아웃라인·서브섹션용 — 같은 초록 인덱스, **facet 만 끕니다.**

    끄는 근거는 취향이 아니라 호스트의 자료 흐름입니다. `writer.py:41` 이 토픽 하나로
    1,500편을 뽑고 `writer.py:50` 이 그 집합을 `id_selector` 로 만들어 이후 모든 서브섹션
    검색에 겁니다. **후보 풀은 토픽 수준 검색이 이미 정했고**, 서브섹션 검색은 그 안에서
    순서만 바꿉니다. facet 을 여기서 또 돌려도 풀이 넓어지지 않습니다.

    대가는 큽니다. 서브섹션 쿼리 30~40개는 전부 처음 보는 문자열이라 캐시가 안 듣고,
    호출마다 LLM 40초가 붙습니다. 2026-08-13 실행에서 50분 중 대부분이 여기서 나갔고,
    OpenRouter 가 밀리면서 facet 분해가 3회 재시도 끝에 실패해 **규칙 기반 fallback 으로
    내려간 것이 2건** 있었습니다 — survey-search 의 170토픽 평가가 품질 조건으로 건
    "fallback 0회"를 못 맞춘 실행이 됐습니다.

    **freshness 는 config 로 못 끕니다.** 어댑터가 `adapters/surveyforge.py:170` 에서
    `freshness = rerank in ("citation","citation_period")` 로 호스트 인자를 우선합니다.
    서브아웃라인은 `rerank='raw'` 라 원래 꺼져 있고, 서브섹션은 `writer.py:76` 이
    `rerank='citation'` 을 넘겨 켜집니다. 그래서 아래 config 의 freshness 값은
    서브섹션 경로에서 **아무 효과가 없습니다** — 끄려면 인자를 가로채야 하고,
    그게 `SURVEY_SEARCH_SUBSECTION_RERANK=raw` 입니다(`_ForceRerank`).
    """
    rag = SurveySearchRAG(*args, backend=_backend(),
                          config=SearchConfig(facets=False, freshness=True, lexical=False),
                          **kwargs)
    return _ForceRerank(rag, _SUB_RERANK) if _SUB_RERANK else rag


def GeneralRAG_langchain_citation(*args, **kwargs):
    """인용 검증용 — 쿼리가 논문 제목. facet 은 무의미하고 제목 인덱스가 맞습니다."""
    return SurveySearchRAG(*args, backend=_backend(),
                           config=SearchConfig(facets=False, lexical=False,
                                               dense_field="title"),
                           **kwargs)
# --- /survey-search arm ------------------------------------------------------
from tqdm import tqdm
import time
import re
from datetime import datetime


def remove_descriptions_subquery(text):
    lines = text.split('\n')
    
    filtered_lines = [line for line in lines if line.strip().startswith("#")]
    
    result = '\n'.join(filtered_lines)
    
    return result

def write(topic, model, section_num, subsection_len, rag_num, refinement):
    outline, outline_wo_description = write_outline(topic, model, section_num)

    if refinement:
        raw_survey, raw_survey_with_references, raw_references, refined_survey, refined_survey_with_references, refined_references = write_subsection(topic, model, outline, subsection_len = subsection_len, rag_num = rag_num, refinement = True)
        return refined_survey_with_references
    else:
        raw_survey, raw_survey_with_references, raw_references = write_subsection(topic, model, outline, subsection_len = subsection_len, rag_num = rag_num, refinement = False)
        return raw_survey_with_references

def write_outline(args, topic, model, ckpt, section_num, outline_reference_num, db, api_key, api_url):
    outline_writer = outlineWriter(args=args, model=model, ckpt=ckpt, api_key=api_key, api_url = api_url, database=db)
    print(outline_writer.api_model.chat('hello'))
    outline = outline_writer.draft_outline(topic, outline_reference_num, 30000, section_num)
    outline_writer.print_token_usage()
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_1 = f"{args.saving_path}/outlines_with_des_{timestamp}.txt"
    with open(filename_1, "w") as f:
        f.write(outline + '\n\n')
    filename_2 = f"{args.saving_path}/outlines_without_des_{timestamp}.txt"
    with open(filename_2, "w") as f:
        f.write(remove_descriptions_subquery(outline) + '\n\n')
        
    outline_writer.print_token_usage()
    
    print(outline)

    def duplicate_first_last_sections(markdown_content):

        pattern = r'(## \d+\.?\s*.*?(?=\n##|\Z))'
        sections = re.findall(pattern, markdown_content, re.DOTALL)
        
        if len(sections) < 2:
            return markdown_content  
        
        first_section = sections[0]
        last_section = sections[-1]
        

        first_section_number = re.search(r'## (\d+)', first_section).group(1)
        first_title = first_section.split('\n')[0].strip()
        first_content = '\n'.join(first_section.split('\n')[1:]).strip()
        new_first_section = (f"{first_title}\n{first_content}\n\n"
                            f"### {first_section_number}.1 {first_title.split(maxsplit=2)[-1]}\n"
                            f"Description: {first_content}\n\n")
        

        last_section_number = re.search(r'## (\d+)', last_section).group(1)
        last_title = last_section.split('\n')[0].strip()
        last_content = '\n'.join(last_section.split('\n')[1:]).strip()
        new_last_section = (f"{last_title}\n{last_content}\n\n"
                            f"### {last_section_number}.1 {last_title.split(maxsplit=2)[-1]}\n"
                            f"Description: {last_content}\n")
        

        markdown_content = markdown_content.replace(first_section, new_first_section)
        markdown_content = markdown_content.replace(last_section, new_last_section)
        
        return markdown_content

    outline = duplicate_first_last_sections(outline)

    return outline, remove_descriptions_subquery(outline)

def write_subsection(args, topic, model, ckpt, outline, subsection_len, rag_num, rag_max_out, db, api_key, api_url, refinement = True):
    def remove_first_last_subsection_titles(markdown_content):
        subsection_pattern = r'\n(### \d+\.\d+[^\n]*)\n'
        subsections = re.findall(subsection_pattern, markdown_content)
        
        if len(subsections) < 2:
            return markdown_content
        
        first_subsection = subsections[0]
        last_subsection = subsections[-1]

        new_content = re.sub(r'\n' + re.escape(first_subsection) + r'\n', '\n', markdown_content)

        new_content = re.sub(r'\n' + re.escape(last_subsection) + r'\n', '\n', new_content)

        new_content = re.sub(r'\n\n\n+', '\n\n', new_content)
        
        return new_content
    
    subsection_writer = subsectionWriter(args=args, model=model, ckpt=ckpt, api_key=api_key, api_url = api_url, database=db)
    if refinement:
        raw_survey, raw_survey_with_references, raw_references, refined_survey, refined_survey_with_references, refined_references = subsection_writer.write(topic, outline, subsection_len = subsection_len, rag_num = rag_num, rag_max_out=rag_max_out, refining = True)
        subsection_writer.print_token_usage()
        return raw_survey, raw_survey_with_references, raw_references, remove_first_last_subsection_titles(refined_survey), remove_first_last_subsection_titles(refined_survey_with_references), refined_references
    else:
        raw_survey, raw_survey_with_references, raw_references = subsection_writer.write(topic, outline, subsection_len = subsection_len, rag_num = rag_num, rag_max_out=rag_max_out, refining = False)
        subsection_writer.print_token_usage()
        return remove_first_last_subsection_titles(raw_survey), remove_first_last_subsection_titles(raw_survey_with_references), raw_references
    

def paras_args():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--gpu',default='0', type=str, help='Specify the GPU to use')
    parser.add_argument('--saving_path',default='./output/', type=str, help='Directory to save the output survey')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--model',default='gpt-4o-mini-2024-07-18', type=str, help='Model to use')
    parser.add_argument('--ckpt',default='', type=str, help='Checkpoint to use')
    parser.add_argument('--topic',default='Multimodal Large Language Models', type=str, help='Topic to generate survey for')
    parser.add_argument('--section_num',default=6, type=int, help='Number of sections in the outline')
    parser.add_argument('--subsection_len',default=500, type=int, help='Length of each subsection')
    parser.add_argument('--outline_reference_num',default=1500, type=int, help='Number of references for outline generation')
    parser.add_argument('--rag_num',default=100, type=int, help='Number of references to use for RAG')
    parser.add_argument('--rag_max_out',default=60, type=int, help='Number of references to use for RAG')
    parser.add_argument('--api_url',default=os.environ.get('SURVEYFORGE_API_URL', 'https://api.openai.com/v1/chat/completions'), type=str, help='url for API request')
    # Defaults to the environment (see .env) so the key never appears in argv,
    # where `ps` would expose it to every other user on the machine.
    parser.add_argument('--api_key',default=os.environ.get('OPENROUTER_API_KEY', ''), type=str, help='API key for the model')
    parser.add_argument('--db_path',default='./database', type=str, help='Directory of the database.')
    parser.add_argument('--survey_outline_path',default='', type=str, help='Directory of the outline database of survey.')
    parser.add_argument('--embedding_model',default='./gte-large-en-v1.5', type=str, help='Embedding model for retrieval.')
    # Which papers the pipeline is allowed to see. The defaults are the values that
    # were hardcoded in the retrieval path, so omitting all three reproduces the
    # published behaviour exactly -- and, after a database update, silently hides
    # everything newer. main() compares them against the database and warns.
    #
    # Three knobs rather than one: '2412' (December) and '2024-09-26' (September) are
    # not the same instant, so no single value reproduces both. They are also not the
    # same quantity -- arXiv assigns the id's YYMM by announcement month while `date`
    # is the submission date, so deriving one from the other would drop papers at
    # every month boundary.
    parser.add_argument('--paper_id_cutoff',
                        default=os.environ.get('SURVEYFORGE_PAPER_ID_CUTOFF', '2412'), type=str,
                        help='Papers whose arXiv id prefix (YYMM) is above this are not '
                             'retrievable in the outline or the writing stage.')
    parser.add_argument('--paper_date_oldest',
                        default=os.environ.get('SURVEYFORGE_PAPER_DATE_OLDEST', '2012-01-01'), type=str,
                        help='Oldest publication date the citation reranker considers.')
    parser.add_argument('--paper_date_newest',
                        default=os.environ.get('SURVEYFORGE_PAPER_DATE_NEWEST', '2024-09-26'), type=str,
                        help='Newest publication date the citation reranker considers. Retrieved '
                             'papers outside [oldest, newest] are discarded before ranking and '
                             'can never be cited.')
    args = parser.parse_args()
    validate_cutoffs(args)
    return args


def validate_cutoffs(args):
    """Reject malformed cutoffs before the ~2 minute database load, not after."""
    if not re.fullmatch(r'\d{4}', args.paper_id_cutoff):
        raise SystemExit(
            f"--paper_id_cutoff must be a 4-digit YYMM string, got {args.paper_id_cutoff!r}. "
            "It is compared as a string against the part of the arXiv id before the dot, "
            "so '2412' works while '2412.0' or '24-12' silently match nothing.")
    for name in ('paper_date_oldest', 'paper_date_newest'):
        try:
            datetime.strptime(getattr(args, name), '%Y-%m-%d')
        except ValueError:
            raise SystemExit(f"--{name} must be YYYY-MM-DD, got {getattr(args, name)!r}")
    if args.paper_date_oldest >= args.paper_date_newest:
        raise SystemExit(
            f"--paper_date_oldest ({args.paper_date_oldest}) must be strictly before "
            f"--paper_date_newest ({args.paper_date_newest}); otherwise get_time_windows() "
            "returns an empty list, every retrieved paper is discarded, and the run "
            "produces a survey with no citations and no error.")

def report_cutoffs_vs_database(args, rag):
    """Compare the configured cutoffs against what is actually in the database.

    Costs no I/O -- id_to_index and doc_list are already resident from the RAG load.
    Warns rather than exits: a cutoff deliberately behind the database is a legitimate
    temporal-holdout setup, and dying here would throw away the two-minute load.
    """
    ids = list(rag.id_to_index)
    dates = [d.metadata['date'] for d in rag.rag_data['doc_list']]  # ISO, sorts lexicographically
    db_min_date, db_max_date = min(dates), max(dates)

    # Report the newest id by publication month, not by string order. A lexical max over
    # mixed id formats returns things like 'quant-ph/0412073v1' -- a 2004 paper named as
    # the newest -- and then warns that everything past it is unreachable while the gate
    # is in fact excluding nothing.
    months = [(m, i) for i in ids for m in (arxiv_month(i),) if m]
    db_max_month, db_max_id = max(months)
    cutoff_month = arxiv_month(f'{args.paper_id_cutoff}.00000')
    n_excluded = sum(1 for m, _ in months if m > cutoff_month)
    n_unparsed = len(ids) - len(months)

    cutoff_log(f"[cutoff/db] {len(ids)} papers, newest id {db_max_id} "
               f"({db_max_month[0]}-{db_max_month[1]:02d}), dates {db_min_date}..{db_max_date}"
               + (f", {n_unparsed} ids in no known format" if n_unparsed else ""),
               args.saving_path)
    cutoff_log(f"[cutoff/cfg] --paper_id_cutoff={args.paper_id_cutoff} "
               f"--paper_date_oldest={args.paper_date_oldest} "
               f"--paper_date_newest={args.paper_date_newest}", args.saving_path)

    if len(dates) != len(ids):
        cutoff_log(f"[cutoff/db] WARNING: arxivid_to_index_abs.json has {len(ids)} entries "
                   f"but the paper db has {len(dates)}; the two are out of step.",
                   args.saving_path)
    if n_excluded:
        cutoff_log(f"[cutoff/cfg] WARNING: {n_excluded} papers are newer than "
                   f"--paper_id_cutoff={args.paper_id_cutoff} and are unreachable in both "
                   f"the outline and the writing stage. Set SURVEYFORGE_PAPER_ID_CUTOFF="
                   f"{db_max_month[0] % 100:02d}{db_max_month[1]:02d} to use the whole "
                   f"database.", args.saving_path)
    if db_max_date > args.paper_date_newest:
        cutoff_log(f"[cutoff/cfg] WARNING: database has papers dated up to {db_max_date} but "
                   f"--paper_date_newest is {args.paper_date_newest}. The citation reranker "
                   f"discards retrieved papers after that date. Set "
                   f"SURVEYFORGE_PAPER_DATE_NEWEST to {db_max_date} or later.", args.saving_path)
    if db_min_date < args.paper_date_oldest:
        cutoff_log(f"[cutoff/cfg] WARNING: database has papers dated back to {db_min_date} but "
                   f"--paper_date_oldest is {args.paper_date_oldest}; older papers are "
                   f"discarded by the citation reranker.", args.saving_path)


def main(args):
    # Namespace's repr would print api_key in full. run_demo.py keeps the key out
    # of argv so `ps` cannot see it; without this the run log gives it away anyway.
    print(argparse.Namespace(**{**vars(args),
                               'api_key': f'<set, {len(args.api_key)} chars>' if args.api_key else '<empty>'}))
    print("########### Loading database and RAG Index... ###########")
    db_paper = database(db_path = args.db_path, embedding_model = args.embedding_model)
    db_survey = database_survey(db_path = args.db_path, embedding_model = args.embedding_model)

    # 파일명에 코퍼스 컷오프가 박혀 있으므로 글롭으로 찾는다 — 스냅샷을 갈아탈 때
    # --db_path 만 바꾸면 되고, 파일명은 계속 컷오프를 말해 준다.
    abs_index_db_path = find_index(args.db_path, 'faiss_paper_title_abs_embeddings')
    title_index_db_path = find_index(args.db_path, 'faiss_paper_title_embeddings')
    doc_db_path = f'{args.db_path}/arxiv_paper_db_with_cc.json'
    arxivid_to_index_path = f'{args.db_path}/arxivid_to_index_abs.json'
    
    rag_abstract4outline = GeneralRAG_langchain(args=args,
                                                retriever_type='vectorstore',
                                                index_db_path=abs_index_db_path,
                                                doc_db_path=doc_db_path,
                                                arxivid_to_index_path=arxivid_to_index_path,
                                                embedding_model=args.embedding_model)

    # 원본은 여기서 rag_abstract4outline 을 **별칭으로 공유**합니다. survey-search arm 은
    # 별칭을 끊습니다 — 셋의 쿼리 성격이 다르기 때문입니다. 토픽 하나로 후보 풀(1,500편)을
    # 정하는 것은 아웃라인 인스턴스이고(writer.py:41·50), 아래 둘은 그 풀 안에서 순서만
    # 바꿉니다. 같은 초록 인덱스·같은 freshness 를 쓰되 facet 만 끕니다. 자세한 근거는
    # GeneralRAG_langchain_subsection 의 독스트링.
    rag_abstract4suboutline = GeneralRAG_langchain_subsection(
        args=args, retriever_type='vectorstore', index_db_path=abs_index_db_path,
        doc_db_path=doc_db_path, arxivid_to_index_path=arxivid_to_index_path,
        embedding_model=args.embedding_model)

    rag_abstract4subsection = rag_abstract4suboutline

    rag_title4citation = GeneralRAG_langchain_citation(args=args,
                                              retriever_type='vectorstore',
                                              index_db_path=title_index_db_path,
                                              doc_db_path=doc_db_path,
                                              arxivid_to_index_path=arxivid_to_index_path,
                                              embedding_model=args.embedding_model)

    if not os.path.exists(args.saving_path):
        os.mkdir(args.saving_path)

    report_cutoffs_vs_database(args, rag_abstract4outline)

    db = {
        "paper": db_paper, 
        "survey": db_survey,
        "rag_outline": rag_abstract4outline, 
        "rag_suboutline": rag_abstract4suboutline,
        "rag_subsection": rag_abstract4subsection,
        "rag_title4citation": rag_title4citation
    }
    
    print("########### Writing outline... ###########")
    
    outline_with_description, outline_wo_description = \
        write_outline(args, args.topic, args.model, args.ckpt, args.section_num, args.outline_reference_num, db, args.api_key, args.api_url)
    
    print("########### Writing content... ###########")

    raw_survey, raw_survey_with_references, raw_references, refined_survey, refined_survey_with_references, refined_references = \
        write_subsection(args, args.topic, args.model, args.ckpt, outline_with_description, args.subsection_len, args.rag_num, args.rag_max_out, db, args.api_key, args.api_url)

    # rag_suboutline and rag_subsection alias this object, and rag_title4citation never
    # reaches _rerank, so one accumulator covers every citation-reranked call in the run.
    rag_abstract4outline.report_window_drops()

    with open(f'{args.saving_path}/{args.topic}.md', 'a+') as f:
        f.write(refined_survey_with_references)
    with open(f'{args.saving_path}/{args.topic}.json', 'a+') as f:
        save_dic = {}
        save_dic['survey'] = refined_survey_with_references
        save_dic['reference'] = refined_references
        f.write(json.dumps(save_dic, indent=4))

if __name__ == '__main__':

    args = paras_args()

    main(args)
