import os
import numpy as np
import tiktoken
from tqdm import trange,tqdm
import time
import torch
from src.model import APIModel, LocalModel
from src.database import database
from src.utils import tokenCounter, get_index_filter_by_id_prefix
from src.prompt import ROUGH_OUTLINE_WITH_SURVEY_PROMPT, MERGING_OUTLINE_WITH_SURVEY_PROMPT, SUBSECTION_OUTLINE_WITH_SURVEY_PROMPT, EDIT_FINAL_OUTLINE_PROMPT_NEW
import random
import re
import json

class outlineWriter():
    
    def __init__(self, args, model:str, ckpt:str, api_key:str, api_url:str, database) -> None:
        self.args = args
        self.model, self.ckpt, self.api_key, self.api_url = model, ckpt, api_key, api_url 
        if self.model == 'local':
            self.api_model = LocalModel(self.ckpt)
        else:
            self.api_model = APIModel(self.model, self.api_key, self.api_url)

        self.db= database
        self.token_counter = tokenCounter()
        self.input_token_usage, self.output_token_usage = 0, 0

    def print_token_usage(self):
        print(f"OutlineWriter Input token usage: {self.input_token_usage}")
        print(f"OutlineWriter Output token usage: {self.output_token_usage}")

    def filter_by_outline(self, survey_infos, folders):
        """Keep only surveys that have a .md in every one of `folders`."""
        kept = [r for r in survey_infos
                if all(os.path.exists(f"{self.args.survey_outline_path}/{folder}/{r['id']}.md")
                       for folder in folders)]
        dropped = len(survey_infos) - len(kept)
        if dropped:
            print(f"Dropped {dropped}/{len(survey_infos)} surveys with no outline in {folders}")
        if not kept:
            raise RuntimeError(
                f"None of the {len(survey_infos)} retrieved surveys have outlines in {folders} "
                f"under {self.args.survey_outline_path}. Check --survey_outline_path.")
        return kept

    def draft_outline(self, topic, reference_num = 600, chunk_size = 30000, section_num = 6):
        # Get database
        # Time Filter
        rag_outline_subset_index_filter = get_index_filter_by_id_prefix(
            self.db["rag_outline"].id_to_index, self.args.paper_id_cutoff,
            stage='outline', saving_path=self.args.saving_path)
        rag_outline_subset_ids = self.db["rag_outline"].retrieve_id(topic, 
                                                                    top_k=reference_num,
                                                                    **rag_outline_subset_index_filter)
        references_infos = self.db["paper"].get_paper_info_from_ids(rag_outline_subset_ids)

        references_titles = [r['title'] for r in references_infos]
        references_date = [r['date'] for r in references_infos]
        references_abs = [r['abs'] for r in references_infos]

        references_survey_ids = self.db["survey"].get_ids_from_query(topic, num = 20, shuffle = False)
        references_survey_infos = self.db["survey"].get_paper_info_from_ids(references_survey_ids)

        # The heuristic outline corpus does not cover every id in the survey db
        # (Final_outline 90.7%, Final_outline_First 76.4%), and the reads below have no
        # fallback. Drop uncovered surveys here so the lists stay aligned downstream.
        references_survey_infos = self.filter_by_outline(references_survey_infos, ['Final_outline_First'])

        references_survey_titles = [r['title'] for r in references_survey_infos]
        references_survey_date = [r['date'].split(" ")[0] for r in references_survey_infos]
        references_survey_abs = [r['abs'] for r in references_survey_infos]
        references_survey_ids = [r['id'] for r in references_survey_infos]

        if self.args.debug:
            with open(f'{self.args.saving_path}/1-Total_1500_papers.txt', 'w') as f:
                for i in references_titles:
                    f.write(i + '\n\n')
            with open(f'{self.args.saving_path}/1-Total_1500_papers_ids.txt', 'w') as f:
                for i in references_survey_ids:
                    f.write(i + '\n\n')

        abs_chunks, titles_chunks, date_chunks = self.chunking(references_abs, references_titles, references_date, chunk_size=chunk_size)
        survey_abs_chunks, survey_titles_chunks, survey_date_chunks, survey_ids_chunks = self.survey_chunking(references_survey_ids, references_survey_abs, references_survey_titles, references_survey_date, chunk_num=len(abs_chunks), ref_num=5)
        
        if self.args.debug:
            with open(f"{self.args.saving_path}/Survey_titles_rough.txt", "w") as f:
                for i in references_survey_titles:
                    f.write(i + '\n\n')

        # generate rough section-level outline

        outlines = self.generate_rough_outlines_with_survey(topic=topic, papers_chunks = abs_chunks, titles_chunks = titles_chunks, date_chunks = date_chunks, survey_ids_chunks=survey_ids_chunks, survey_abs_chunks=survey_abs_chunks, survey_titles_chunks=survey_titles_chunks, survey_date_chunks=survey_date_chunks, section_num=section_num)
        
        if self.args.debug:
            with open(f'{self.args.saving_path}/1-Chunk_outlines.json', 'w') as f:
                json.dump(outlines, f)

        # merge outline
        references_survey_ids = self.db["survey"].get_ids_from_query(topic, num = 10, shuffle = False)
        references_survey_infos = self.db["survey"].get_paper_info_from_ids(references_survey_ids)

        # both outline levels are read for these ids (below and after merging)
        references_survey_infos = self.filter_by_outline(references_survey_infos,
                                                         ['Final_outline_First', 'Final_outline'])

        # choose the first 5 survey papers
        references_survey_infos = sorted(references_survey_infos, key=lambda x: x['date'].split(" ")[0], reverse=True)[:5]

        references_survey_titles = [r['title'] for r in references_survey_infos]
        references_survey_abs = [r['abs'] for r in references_survey_infos]
        references_survey_date = [r['date'].split(" ")[0] for r in references_survey_infos]
        references_survey_ids = [r['id'] for r in references_survey_infos]

        references_survey_outlines = []
        for id_tmp in references_survey_ids:
            with open(f"{self.args.survey_outline_path}/Final_outline_First/{id_tmp}.md", "r") as f:
                references_survey_outlines.append(f.read().strip())

        if self.args.debug:
            with open(f"{self.args.saving_path}/Survey_titles_high.txt", "w") as f:
                for i in references_survey_titles:
                    f.write(i + '\n\n')
                
        section_outline = self.merge_outlines_with_survey(topic=topic, outlines=outlines, references_survey_titles=references_survey_titles, references_survey_abs=references_survey_abs,references_survey_date=references_survey_date, references_survey_outlines=references_survey_outlines, section_num=section_num)
        
        if self.args.debug:
            with open(f"{self.args.saving_path}/2-Merged_outlines.txt", "w") as f:
                f.write(section_outline + '\n\n')
        
        # generate subsection-level outline
        self.print_token_usage()
        references_survey_outlines = []
        for id_tmp in references_survey_ids:
            with open(f"{self.args.survey_outline_path}/Final_outline/{id_tmp}.md", "r") as f:
                references_survey_outlines.append(f.read().strip())

        if self.args.debug:
            with open(f"{self.args.saving_path}/2-Merged_outlines.txt", "r") as f:
                section_outline = f.read().strip()

        subsection_outlines = self.generate_subsection_outlines_with_survey(topic=topic, section_outline= section_outline,rag_num= 50, references_survey_titles=references_survey_titles, references_survey_abs=references_survey_abs,references_survey_date=references_survey_date, references_survey_outlines=references_survey_outlines)
        
        # Process introduction and conclusion
        subsection_outlines.insert(0, [])
        subsection_outlines.append([])

        if self.args.debug:
            # Upstream wrote `merged_outline` here, but it is not assigned until
            # process_outlines_points() below -- an UnboundLocalError that only fires
            # under --debug. The filename says "wo_process", so what belongs here is
            # the subsection outlines as they stand before that processing. They are
            # a list of lists, so JSON rather than the original .txt.
            with open(f"{self.args.saving_path}/3-Merged_Sub_outline_wo_process.json", "w") as f:
                json.dump(subsection_outlines, f, indent=2)

        merged_outline = self.process_outlines_points(section_outline, subsection_outlines)

        if self.args.debug:
            with open(f"{self.args.saving_path}/3-Merged_Sub_outline.txt", "w") as f:
                f.write(merged_outline + '\n\n')

        final_outline = merged_outline

        return final_outline

    def compute_price(self):
        return self.token_counter.compute_price(input_tokens=self.input_token_usage, output_tokens=self.output_token_usage, model=self.model)

    def generate_rough_outlines_with_survey(self, topic, papers_chunks, titles_chunks, date_chunks, survey_ids_chunks, survey_abs_chunks, survey_titles_chunks, survey_date_chunks, section_num = 8):

        prompts = []
        for idx in trange(len(papers_chunks)):
            titles = titles_chunks[idx]
            papers = papers_chunks[idx]
            date = date_chunks[idx]
            paper_texts = '' 
            for i, t, p, d in zip(range(len(papers)), titles, papers, date):
                paper_texts += f'---\npaper_title: {t}\n\npublish_date: {d}\n\npaper_abstract:\n\n{p}\n'
            paper_texts+='---\n'

            survey_titles = survey_titles_chunks[idx]
            survey_papers = survey_abs_chunks[idx]
            survey_date = survey_date_chunks[idx]
            survey_ids = survey_ids_chunks[idx]
            
            survey_paper_texts = '' 
            for i, id, t, p, d in zip(range(len(survey_papers)), survey_ids, survey_titles, survey_papers, survey_date):
                with open(f"{self.args.survey_outline_path}/Final_outline_First/{id}.md", "r") as f:
                    first_o = f.read().strip()
                survey_paper_texts += f'---\npaper_title: {t}\n\npublish_date: {d}\n\npaper_abstract:\n\n{p}\n\npaper_first_outline:\n\n{first_o}\n'
            survey_paper_texts+='---\n'

            prompt = self.__generate_prompt(ROUGH_OUTLINE_WITH_SURVEY_PROMPT, paras={'SURVEY LIST': survey_paper_texts, 'PAPER LIST': paper_texts, 'TOPIC': topic, 'SECTION NUM': str(section_num)})
            prompts.append(prompt)
        self.input_token_usage += self.token_counter.num_tokens_from_list_string(prompts)
        print("rouge outline input token :%d" %self.token_counter.num_tokens_from_list_string(prompts))
        start = time.time()
        outlines = self.api_model.batch_chat(text_batch=prompts, temperature=1)
        end = time.time()
        period = end - start
        with open(f"{self.args.saving_path}/time_cost.log", "a") as f:
            f.write(f"Outline API: {period}\n")

        self.output_token_usage += self.token_counter.num_tokens_from_list_string(outlines)
        return outlines
    
    def merge_outlines_with_survey(self, topic, outlines, references_survey_titles, references_survey_abs,references_survey_date, references_survey_outlines, section_num):

        outline_texts = '' 
        for i, o in zip(range(len(outlines)), outlines):
            outline_texts += f'---\noutline_id: {i}\n\noutline_content:\n\n{o}\n'
        outline_texts+='---\n'

        survey_paper_texts = '' 
        for i, t, p, d, o in zip(range(len(references_survey_abs)), references_survey_titles, references_survey_abs, references_survey_date, references_survey_outlines):
            survey_paper_texts += f'---\npaper_title: {t}\n\npublish_date: {d}\n\npaper_abstract:\n\n{p}\n\npaper_first_outline:\n\n{o}\n'
        survey_paper_texts+='---\n'

        prompt = self.__generate_prompt(MERGING_OUTLINE_WITH_SURVEY_PROMPT, paras={'SURVEY LIST':survey_paper_texts, 'OUTLINE LIST': outline_texts, 'TOPIC':topic, 'SECTION NUM':str(section_num)})
        self.input_token_usage += self.token_counter.num_tokens_from_string(prompt)
        outline = self.api_model.chat(prompt, temperature=1)
        self.output_token_usage += self.token_counter.num_tokens_from_string(outline)
        if self.args.debug:
            with open(f"{self.args.saving_path}/2-Merged_outlines_Input.txt", "w") as f:
                f.write(prompt + '\n\n')
        return outline.replace('<format>\n','').replace('</format>','')

    def generate_subsection_outlines_with_survey(self, topic, section_outline, rag_num, references_survey_titles, references_survey_abs,references_survey_date, references_survey_outlines):

        survey_title, survey_sections, survey_section_descriptions = self.extract_title_sections_descriptions(section_outline)

        prompts = []

        for section_name, section_description in zip(survey_sections[1:-1], survey_section_descriptions[1:-1]):
            if isinstance(section_description, list):
                references_ids = []
                for des_tmp in section_description:
                    # print(f"{section_name}:" + des_tmp)
                    references_ids_tmp = self.db["rag_suboutline"].retrieve_id([f"{topic}:" + des_tmp], 
                                                                        search_type='similarity', 
                                                                        rerank='raw', 
                                                                        top_k=int(rag_num // len(section_description) * 5))
                    references_ids.extend(references_ids_tmp)
            else:
                section_description = [section_description]
                references_ids = self.db["rag_suboutline"].retrieve_id(section_description, 
                                                                    search_type='similarity', 
                                                                    rerank='raw', 
                                                                    top_k=rag_num)

            references_infos = self.db["paper"].get_paper_info_from_ids(references_ids)
            
            # remove "Survey" papers
            references_infos = [r for r in references_infos if 'survey' not in r['title'].lower()]
            if len(references_infos) > rag_num:
                references_infos = random.sample(references_infos, rag_num)

            references_titles = [r['title'] for r in references_infos]
            references_papers = [r['abs'] for r in references_infos]
            references_date = [r['date'] for r in references_infos]
            if self.args.debug:
                with open(f'{self.args.saving_path}/3-Total_subsection_papers.txt', 'a+') as f:
                    f.write(f'{section_name}\n{section_description}\n\n')
                    for i in references_titles:
                        f.write(i + '\n\n')

            paper_texts = '' 
            for i, t, p, d in zip(range(len(references_papers)), references_titles, references_papers, references_date):
                paper_texts += f'---\npaper_title: {t}\n\npublish_date: {d}\n\npaper_content:\n\n{p}\n'
            paper_texts+='---\n'

            survey_paper_texts = '' 
            for i, t, p, d, o in zip(range(len(references_survey_abs)), references_survey_titles, references_survey_abs, references_survey_date, references_survey_outlines):
                survey_paper_texts += f'---\npaper_title: {t}\n\npublish_date: {d}\n\npaper_abstract:\n\n{p}\n\npaper_outline:\n\n{o}\n'
            survey_paper_texts+='---\n'

            prompt = self.__generate_prompt(SUBSECTION_OUTLINE_WITH_SURVEY_PROMPT, paras={'RAG NUM':str(rag_num),  'OVERALL OUTLINE': section_outline, 'OVERALL OUTLINE': section_outline,'SECTION NAME': section_name,\
                                                                          'SECTION DESCRIPTION':'\n'.join(section_description),'TOPIC':topic,'PAPER LIST':paper_texts, 'SURVEY LIST':survey_paper_texts})
            prompts.append(prompt)

        self.input_token_usage += self.token_counter.num_tokens_from_list_string(prompts)

        start = time.time()
        sub_outlines = self.api_model.batch_chat(prompts, temperature=1)
        end = time.time()
        period = end - start
        with open(f"{self.args.saving_path}/time_cost.log", "a") as f:
            f.write(f"SubOutline API: {period}\n")
        # print(f"##########SubOutline API Time taken#########: {period}")

        self.output_token_usage += self.token_counter.num_tokens_from_list_string(sub_outlines)
        if self.args.debug:
            with open(f"{self.args.saving_path}/3-Merged_Sub_outline_Input.txt", "w") as f:
                f.write(prompt + '\n\n')
        return sub_outlines


    def edit_final_outline(self, outline):
        prompt = self.__generate_prompt(EDIT_FINAL_OUTLINE_PROMPT_NEW, paras={'OVERALL OUTLINE': outline})
        self.input_token_usage += self.token_counter.num_tokens_from_string(prompt)
        outline = self.api_model.chat(prompt, temperature=1)
        self.output_token_usage += self.token_counter.num_tokens_from_string(outline)
        return outline.replace('<format>\n','').replace('</format>','')
 
    def __generate_prompt(self, template, paras):
        prompt = template
        for k in paras.keys():
            prompt = prompt.replace(f'[{k}]', paras[k])
        return prompt
    
    def extract_title_sections_descriptions(self, outline):
        title = outline.split('Title: ')[1].split('\n')[0]
        sections, descriptions = [], []
        for i in range(100):
            if f'Section {i+1}' in outline:
                sections.append(outline.split(f'Section {i+1}: ')[1].split('\n')[0])
                # 서브섹션 파서와 같은 문제가 여기에도 있다 — 모델이 번호를 빼고
                # 'Description:' 으로 쓰면 IndexError 로 죽었다 (3D Gaussian Splatting
                # 에서 Section 7 하나가 그랬다, 2026-08-06).
                tail = self._description_tail(outline, i + 1, unit='Section')
                if tail is None:
                    descriptions.append([] if "1." in outline else '')
                    continue
                if f"1."  not in outline:
                    descriptions.append(tail.split('\n')[0])
                else:
                    tmp_context = tail
                    if f'Section {i+1+1}' in outline:
                        tmp_context = tmp_context.split(f'Section {i+1+1}: ')[0]
                    descriptions.append([item.strip() for item in tmp_context.split("\n") if item])
        return title, sections, descriptions
    
    def extract_subsections_subdescriptions_points(self, outline):
        subsections, subdescriptions = [], []
        for i in range(100):
            if f'Subsection {i+1}' in outline:
                subsections.append(outline.split(f'Subsection {i+1}: ')[1].split('\n')[0])
                tail = self._description_tail(outline, i + 1)
                if tail is None:
                    # 설명을 못 찾았어도 리스트 길이는 맞춰 둔다. 호출부가 서브섹션과
                    # 설명을 인덱스로 짝지으므로 건너뛰면 이후가 전부 밀린다.
                    subdescriptions.append([] if "1." in outline else '')
                    continue
                if "1." not in outline:
                    subdescriptions.append(tail.split('\n')[0])
                else:
                    tmp_context = tail
                    if f'Subsection {i+1+1}' in outline:
                        tmp_context = tmp_context.split(f'Subsection {i+1+1}: ')[0]
                    subdescriptions.append([item.strip() for item in tmp_context.split("\n") if item])
        return subsections, subdescriptions

    @staticmethod
    def _description_tail(outline, n, unit='Subsection'):
        """`<unit> n` 에 딸린 설명 이후의 텍스트. 못 찾으면 None.

        원래는 `Description {n}: ` 만 찾고 없으면 IndexError 로 죽었다. 모델이 첫
        항목에만 번호를 붙이고 이후는 `Description:` 으로 쓰는 경우가 있다 —
        deepseek-v4-flash-0731 이 7개 섹션 중 하나에서 그렇게 내놓아 아웃라인
        단계에서 실행 전체가 죽었다 (2026-08-05).

        번호가 붙은 형태를 먼저 그대로 찾으므로, 규격을 지킨 출력에서는 동작이
        이전과 완전히 같다.
        """
        marker = f'Description {n}: '
        if marker in outline:
            return outline.split(marker)[1]
        # 번호 없는 형태: 해당 구간 안에서만 찾는다. 밖에서 찾으면 다른 절의 설명을
        # 가져온다.
        parts = outline.split(f'{unit} {n}: ')
        if len(parts) < 2:
            return None
        m = re.search(r'Description\s*:\s*', parts[1])
        return parts[1][m.end():] if m else None
    
    def chunking(self, papers, titles, dates, chunk_size = 14000):
        paper_chunks, title_chunks, date_chunks = [], [], []
        total_length = self.token_counter.num_tokens_from_list_string(papers)
        num_of_chunks = int(total_length / chunk_size) + 1
        avg_len = int(total_length / num_of_chunks) + 1
        split_points = []
        l = 0
        for j in range(len(papers)):
            l += self.token_counter.num_tokens_from_string(papers[j])
            if l > avg_len:
                l = 0
                split_points.append(j)
                continue
        start = 0
        for point in split_points:
            paper_chunks.append(papers[start:point])
            title_chunks.append(titles[start:point])
            date_chunks.append(dates[start:point])
            start = point
        paper_chunks.append(papers[start:])
        title_chunks.append(titles[start:])
        date_chunks.append(dates[start:])
        return paper_chunks, title_chunks, date_chunks

    def survey_chunking(self, ids, papers, titles, dates, chunk_num=10, ref_num=10):
        assert len(papers) == len(titles), "papers and titles must have the same length"
        
        paper_chunks, title_chunks, date_chunks, id_chunks = [], [], [], []
        total_papers = len(papers)
        
        all_indices = list(range(total_papers))
        
        for i in range(chunk_num):
            chunk_indices = []
            if all_indices:
                # the pool shrinks each round and may hold fewer than ref_num left
                num_to_select = min(ref_num, len(all_indices))
                selected = random.sample(all_indices, num_to_select)
                chunk_indices.extend(selected)
                for idx in selected:
                    all_indices.remove(idx)
            
            # random select
            while len(chunk_indices) < ref_num:
                chunk_indices.append(random.randint(0, total_papers - 1))
            
            # make chunk of paper and title
            paper_chunk = [papers[idx] for idx in chunk_indices]
            title_chunk = [titles[idx] for idx in chunk_indices]
            date_chunk = [dates[idx] for idx in chunk_indices]
            id_chunk = [ids[idx] for idx in chunk_indices]
            
            paper_chunks.append(paper_chunk)
            title_chunks.append(title_chunk)
            date_chunks.append(date_chunk)
            id_chunks.append(id_chunk)
        
        return paper_chunks, title_chunks, date_chunks, id_chunks
    
    def process_outlines_points(self, section_outline, sub_outlines):
        res = ''
        survey_title, survey_sections, survey_section_descriptions = self.extract_title_sections_descriptions(outline=section_outline)
        res += f'# {survey_title}\n\n'
        for i in range(len(survey_sections)):
            section = survey_sections[i]
            description = "\n".join(survey_section_descriptions[i])
            res += f'## {i+1} {section}\nDescription: {description}\n\n'
            subsections, subsection_descriptions = self.extract_subsections_subdescriptions_points(sub_outlines[i])
            for j in range(len(subsections)):
                subsection = subsections[j]
                sub_description = "\n".join(subsection_descriptions[j])
                res += f'### {i+1}.{j+1} {subsection}\nDescription: {sub_description}\n\n'
        return res

