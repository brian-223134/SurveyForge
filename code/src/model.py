import os
import time
import requests
import json
from tqdm import tqdm
import threading
import anthropic
import torch
import transformers
import concurrent.futures
from openai import OpenAI
import time

# Output cap per request. This is a truncation guard, not a length control -- the
# survey length is set by --subsection_len and the number of subsections. Without
# it the provider default applies silently, which biases length measurements.
MAX_TOKENS = int(os.environ.get("SURVEYFORGE_MAX_TOKENS", 8192))
# Concurrent requests to the model API. The original 100 trips most hosted rate
# limits. Note the writer fans out sections on top of this, so peak concurrency is
# MAX_SECTION_THREADS * MAX_THREADS -- keep that product in mind when raising either.
MAX_THREADS = int(os.environ.get("SURVEYFORGE_MAX_THREADS", 8))
MAX_SECTION_THREADS = int(os.environ.get("SURVEYFORGE_MAX_SECTION_THREADS", 2))


class APIModel:

    def __init__(self, model, api_key, api_url) -> None:
        self.__api_key = api_key
        self.__api_url = api_url
        self.model = model
        
    def __req(self, text, temperature, max_try = 10):
        if "deepseek" in self.model:
            last_error = None
            for _ in range(max_try):
                try:
                    client = OpenAI(
                        api_key=self.__api_key,
                        base_url=self.__api_url,
                    )
                    completion = client.chat.completions.create(
                        model=self.model,  # e.g. deepseek/deepseek-v4-pro on OpenRouter
                        messages=[
                            {'role': 'user', 'content': f'{text}'}
                            ],
                        max_tokens=MAX_TOKENS,
                    )
                    choice = completion.choices[0]
                    if choice.finish_reason == 'length':
                        print(f"[TRUNCATED] finish_reason=length model={self.model} "
                              f"max_tokens={MAX_TOKENS} -- output was cut off")
                    return choice.message.content
                except Exception as e:
                    last_error = e
                    print(f"API error: {e}\n Retrying...{_} Times")
                    continue
            # Falling out of the loop used to return None implicitly, which blew up
            # far away in .replace() / token counting. Be explicit and loud instead.
            print(f"[GIVE UP] {max_try} attempts failed, last error: {last_error}")
            return None
        elif "claude"  not in self.model:
            url = f"{self.__api_url}"
            # temperature and max_tokens belong at the top level of the payload; they
            # were nested inside the message object, where the API ignores them.
            pay_load_dict = {"model": f"{self.model}",
                             "temperature": temperature,
                             "max_tokens": MAX_TOKENS,
                             "messages": [{
                    "role": "user",
                    "content": f"{text}"}]}

            payload = json.dumps(pay_load_dict)
            headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.__api_key}',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
            }
            try:
                response = requests.request("POST", url, headers=headers, data=payload)
                return json.loads(response.text)['choices'][0]['message']['content']
            except Exception as e:
                print(e)
                time.sleep(5)
                for _ in range(max_try):
                    try:
                        response = requests.request("POST", url, headers=headers, data=payload)
                        print(json.loads(response.text))
                        return json.loads(response.text)['choices'][0]['message']['content']
                    except Exception as e:
                        print(e)
                        pass
                    time.sleep(0.2)
                print(e)
                return None
        else:
            try:
                client = anthropic.Anthropic(api_key=self.__api_key)
                message = client.messages.create(
                    model=self.model,
                    max_tokens=MAX_TOKENS,
                    temperature=temperature,
                    messages=[
                        {"role": "user", "content": text}
                    ]
                )
                return message.content[0].text
            except Exception as e:
                print(f"Error occurred with Claude API: {e}")
                return None
    
    def chat(self, text, temperature=1):
        response = self.__req(text, temperature=temperature, max_try=5)
        return response

    def __chat(self, text, temperature, res_l, idx):
        
        response = self.__req(text, temperature=temperature)
        res_l[idx] = response
        return response

    def batch_chat(self, text_batch, temperature=0):
        max_threads = MAX_THREADS  # limit max concurrent threads using model API
        res_l = ['No response'] * len(text_batch)

        def chat_wrapper(text, temp, res_list, idx):
            self.__chat(text, temp, res_list, idx)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = []
            for i, text in enumerate(text_batch):
                future = executor.submit(chat_wrapper, text, temperature, res_l, i)
                futures.append(future)
                
                while len(futures) >= max_threads:
                    done, not_done = concurrent.futures.wait(futures, timeout=60, return_when=concurrent.futures.FIRST_COMPLETED)
                    futures = list(not_done)
                    time.sleep(10)  # Short delay to avoid busy-waiting

            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing remaining"):
                future.result()

        return res_l

class LocalModel:

    def __init__(self, ckpt) -> None:
        self.ckpt = ckpt
        
        self._init_client()
        
    def _init_client(self):
        model_name =  self.ckpt.split('/')[-1]
        self.client = transformers.pipeline('text-generation',
                                             model=self.ckpt, 
                                             #model_kwargs={"torch_dtype": torch.bfloat16},
                                             device_map="auto")
        print(f"Model {model_name} loaded successfully")

    def _req(self, text, temperature, max_try = 5):
        message = [{"role": "user", "content": text}]
        response = self.client(message,
                            max_new_tokens=4096,
                            temperature=temperature,
                            pad_token_id=self.client.tokenizer.eos_token_id)
        return response[0]['generated_text'][-1]['content']
        # try:
        #     response = self.client(message,
        #                         max_new_tokens=256,
        #                         temperature=temperature)
        #     return response[0]['generated_text'][-1]['content']
        # except:
        #     for _ in range(max_try):
        #         try:
        #             response = self.client(message,
        #                                 max_new_tokens=256,
        #                                 temperature=temperature)
        #             return response[0]['generated_text'][-1]['content']
        #         except:
        #             pass
        #         time.sleep(0.2)
        #     return None

    def chat(self, text, temperature=1.0):
        response = self._req(text, temperature=temperature, max_try=5)
        return response
    
    def _batch_chat_i(self, text, temperature, res_l, idx):
        response = self._req(text, temperature=temperature)
        res_l[idx] = response
        return response
        
    def batch_chat(self, text_batch, temperature=1.0):
        max_threads=1
        res_l = ['No response'] * len(text_batch)
        thread_l = []
        for i, text in zip(range(len(text_batch)), text_batch):
            thread = threading.Thread(target=self._batch_chat_i, args=(text, temperature, res_l, i))
            thread_l.append(thread)
            thread.start()
            while len(thread_l) >= max_threads: 
                for t in thread_l:
                    if not t .is_alive():
                        thread_l.remove(t)
                time.sleep(0.3)
        
        for thread in tqdm(thread_l):
            thread.join()
        return res_l
