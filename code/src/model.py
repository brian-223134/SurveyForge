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

# 전 호출 temperature 오버라이드. 호출부(outline_writer.py·writer.py 7곳)는
# temperature=1 을 하드코딩하는데, KISTI 비교 실험은 4개 agent 공통으로 0.6 을 쓴다
# (llama-3.3-70b 는 temp 0 에서 반복 루프에 빠져 금지). 비워 두면 호출자 값 그대로.
_t = os.environ.get("SURVEYFORGE_TEMPERATURE", "").strip()
TEMPERATURE_OVERRIDE = float(_t) if _t else None
# max_tokens 가드에 걸린 응답(finish_reason=length)은 정상 호출에서 나올 수 없다 --
# 가드(8,192)가 서브섹션 출력의 4~8배다. 반복 루프의 신호이므로 그 응답은 버리고
# 같은 temperature 로 새 샘플을 받는다. 재시도를 다 쓰면 마지막 잘린 내용을
# 받아들이고 truncated_accepted 로 센다. SURVEYFORGE_RETRY_TRUNCATED=0 이면 종전처럼
# 잘린 내용을 그대로 쓴다. OpenAI-SDK 분기(OpenRouter)에만 구현돼 있다.
_rt = os.environ.get("SURVEYFORGE_RETRY_TRUNCATED", "").strip().lower()
RETRY_TRUNCATED = (_rt not in ("0", "false", "off", "no")) if _rt else True

# 실행 단위 집계. APIModel 은 outline writer 와 subsection writer 가 따로 만들므로
# 모듈 수준에 둔다. main.py 가 run_manifest.json 에 기록한다.
_STATS_LOCK = threading.Lock()
LLM_STATS = {"completions": 0, "truncated_accepted": 0, "truncation_retries": 0,
             "empty_retries": 0, "error_retries": 0}


def _bump(key, n=1):
    with _STATS_LOCK:
        LLM_STATS[key] += n


def _csv_env(name):
    return [v.strip() for v in os.environ.get(name, "").split(",") if v.strip()]


def _openrouter_extra():
    """OpenRouter-specific request fields, assembled from the environment.

    Pinning the provider matters for reproducibility: OpenRouter routes each
    request independently across endpoints that serve *different quantizations*
    of the same weights (deepseek/deepseek-v4-pro is offered as fp4, fp8 and
    first-party), so an unpinned run mixes them within a single survey.
    """
    extra = {}

    providers, quants = _csv_env("SURVEYFORGE_PROVIDER"), _csv_env("SURVEYFORGE_QUANTIZATIONS")
    if providers or quants:
        # require_parameters drops endpoints that would silently ignore fields we
        # send (max_tokens, reasoning) rather than honouring them.
        provider = {"require_parameters": True}
        if providers:
            provider["only"] = providers
            # Pinning is pointless if a fallback can quietly serve a different
            # quantization; the retry loop in __req covers transient outages.
            provider["allow_fallbacks"] = False
        if quants:
            provider["quantizations"] = quants
        extra["provider"] = provider

    effort = os.environ.get("SURVEYFORGE_REASONING_EFFORT", "").strip()
    exclude = os.environ.get("SURVEYFORGE_REASONING_EXCLUDE", "").strip().lower() in ("1", "true", "yes")
    if effort or exclude:
        reasoning = {}
        if effort:
            # "none" disables it; otherwise low/medium/high/xhigh
            reasoning["effort"] = effort
        if exclude:
            # keep reasoning out of `content`, where it would break the outline
            # parser (extract_title_sections_descriptions splits on 'Title: ')
            reasoning["exclude"] = True
        extra["reasoning"] = reasoning

    return extra


OPENROUTER_EXTRA = _openrouter_extra()
_SEEN_PROVIDERS = set()
_PROFILE_LOGGED = False

# Retries used to fire back-to-back. Against an upstream 429 that is the worst
# possible response: MAX_THREADS * MAX_SECTION_THREADS workers each burn their
# whole budget within seconds of the limit appearing, so a rate limit that would
# have cleared in half a minute takes the run down instead. Back off with jitter
# -- jitter matters because the workers hit the limit together and would
# otherwise retry together too.
_RETRY_BASE = float(os.environ.get("SURVEYFORGE_RETRY_BASE", 4.0))
_RETRY_CAP = float(os.environ.get("SURVEYFORGE_RETRY_CAP", 60.0))
# Second line of defence, at the batch level: retry whatever the per-request
# loop gave up on, serially and after a longer pause.
_BATCH_RETRY_ROUNDS = int(os.environ.get("SURVEYFORGE_BATCH_RETRY_ROUNDS", 3))
_BATCH_RETRY_COOLDOWN = float(os.environ.get("SURVEYFORGE_BATCH_RETRY_COOLDOWN", 60.0))


def _retry_wait(attempt, max_try):
    """Seconds to wait before the next attempt; 0 when this was the last one."""
    if attempt >= max_try - 1:
        return 0.0
    import random
    return min(_RETRY_CAP, _RETRY_BASE * (2 ** attempt)) * (0.5 + random.random())


class APIModel:

    def __init__(self, model, api_key, api_url) -> None:
        self.__api_key = api_key
        self.__api_url = api_url
        self.model = model
        global _PROFILE_LOGGED
        if not _PROFILE_LOGGED:
            _PROFILE_LOGGED = True
            print(f"[DECODING] temperature="
                  f"{TEMPERATURE_OVERRIDE if TEMPERATURE_OVERRIDE is not None else 'caller default'}"
                  f" max_tokens={MAX_TOKENS} retry_truncated={RETRY_TRUNCATED}")
        
    def __openai_compatible(self):
        # OpenRouter처럼 base URL(…/v1)로 설정된 엔드포인트는 모델명과 무관하게
        # OpenAI SDK 분기를 태운다. 아래 raw requests 분기는 전체 경로
        # (…/chat/completions)를 기대하고, 백오프·PROVIDER/TRUNCATED/EMPTY 진단이
        # 없다 — 모델명 하드코딩(deepseek/claude)으로는 meta-llama 등 새 백본이
        # 그 약한 분기로 떨어진다.
        return bool(self.__api_url) and self.__api_url.rstrip('/').endswith('v1')

    def __req(self, text, temperature, max_try = 10):
        if TEMPERATURE_OVERRIDE is not None:
            temperature = TEMPERATURE_OVERRIDE
        if "deepseek" in self.model or \
                ("claude" not in self.model and self.__openai_compatible()):
            last_error = None
            for _ in range(max_try):
                try:
                    client = OpenAI(
                        api_key=self.__api_key,
                        base_url=self.__api_url,
                    )
                    completion = client.chat.completions.create(
                        model=self.model,  # e.g. meta-llama/llama-3.3-70b-instruct on OpenRouter
                        messages=[
                            {'role': 'user', 'content': f'{text}'}
                            ],
                        temperature=temperature,
                        max_tokens=MAX_TOKENS,
                        extra_body=OPENROUTER_EXTRA,
                    )
                    # OpenRouter reports which endpoint served the request; surface
                    # each distinct one so a run that silently spanned several
                    # providers (and quantizations) is visible in the log.
                    served_by = getattr(completion, 'provider', None)
                    if served_by and served_by not in _SEEN_PROVIDERS:
                        _SEEN_PROVIDERS.add(served_by)
                        print(f"[PROVIDER] served by: {served_by}")

                    choice = completion.choices[0]
                    _bump("completions")
                    if choice.finish_reason == 'length':
                        if RETRY_TRUNCATED and _ < max_try - 1:
                            _bump("truncation_retries")
                            last_error = ("truncated (finish_reason=length) -- "
                                          "suspected repetition loop")
                            print(f"[TRUNCATED->RETRY] finish_reason=length "
                                  f"max_tokens={MAX_TOKENS}; discarding and resampling "
                                  f"({_ + 1}/{max_try}), run total "
                                  f"{LLM_STATS['truncation_retries']}")
                            # 429 백오프가 아니라 새 샘플이 목적이므로 길게 기다리지 않는다.
                            time.sleep(min(_retry_wait(_, max_try), 5.0))
                            continue
                        _bump("truncated_accepted")
                        print(f"[TRUNCATED] finish_reason=length model={self.model} "
                              f"max_tokens={MAX_TOKENS} -- output was cut off"
                              + (" and kept (resample budget exhausted)"
                                 if RETRY_TRUNCATED else ""))
                    content = choice.message.content
                    if not content:
                        # A reasoning model can spend the whole budget thinking and
                        # come back with content=None (observed on baidu/fp8 at
                        # max_tokens=2000). Returning it here would surface as a
                        # TypeError in .replace() several call frames away, so treat
                        # it as a failed attempt and let the retry loop handle it.
                        last_error = (f"empty content, finish_reason="
                                      f"{choice.finish_reason}")
                        _bump("empty_retries")
                        print(f"[EMPTY] {last_error}\n Retrying...{_} Times")
                        time.sleep(_retry_wait(_, max_try))
                        continue
                    return content
                except Exception as e:
                    _bump("error_retries")
                    last_error = e
                    wait = _retry_wait(_, max_try)
                    print(f"API error: {e}\n Retrying...{_} Times "
                          f"(waiting {wait:.1f}s)")
                    time.sleep(wait)
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
                             **OPENROUTER_EXTRA,
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
        # Callers use the result directly (.replace(), token counting), so None
        # surfaces as an unrelated TypeError/AttributeError frames away from the
        # API error that caused it. Give the request the same cooldown-and-retry
        # the batch path gets -- this path serves the late, expensive stages
        # (outline merge, LCE refinement), where losing the run costs the most --
        # then fail with a message that names the real cause.
        for round_no in range(_BATCH_RETRY_ROUNDS):
            response = self.__req(text, temperature=temperature, max_try=5)
            if response is not None:
                return response
            if round_no == _BATCH_RETRY_ROUNDS - 1:
                break
            wait = _BATCH_RETRY_COOLDOWN * (round_no + 1)
            print(f"[CHAT RETRY] request failed; waiting {wait:.0f}s "
                  f"(round {round_no + 1}/{_BATCH_RETRY_ROUNDS})")
            time.sleep(wait)
        raise RuntimeError(
            f"chat: request failed after {_BATCH_RETRY_ROUNDS} rounds of retries. "
            f"See the [GIVE UP] lines above for the underlying API error.")

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

        # A slot that is still None means __req exhausted its retries. Left in
        # place it poisons the caller far downstream -- the 3DGS run died ten
        # minutes in with "TypeError: expected string or buffer" from tiktoken,
        # with nothing pointing back at the 429 that actually caused it.
        #
        # Retry the failed slots serially. The failure mode we keep hitting is a
        # shared-pool rate limit, so the useful move is to stop competing with
        # ourselves: one request at a time, after a cooldown. Then fail loudly
        # rather than returning a list with holes in it.
        for round_no in range(_BATCH_RETRY_ROUNDS):
            missing = [i for i, r in enumerate(res_l) if r is None]
            if not missing:
                break
            wait = _BATCH_RETRY_COOLDOWN * (round_no + 1)
            print(f"[BATCH RETRY] {len(missing)}/{len(res_l)} requests failed; "
                  f"waiting {wait:.0f}s then retrying them one at a time "
                  f"(round {round_no + 1}/{_BATCH_RETRY_ROUNDS})")
            time.sleep(wait)
            for i in missing:
                self.__chat(text_batch[i], temperature, res_l, i)

        missing = [i for i, r in enumerate(res_l) if r is None]
        if missing:
            raise RuntimeError(
                f"batch_chat: {len(missing)}/{len(res_l)} requests still failed "
                f"after {_BATCH_RETRY_ROUNDS} serial retry rounds (indices "
                f"{missing[:10]}{'...' if len(missing) > 10 else ''}). See the "
                f"[GIVE UP] lines above for the underlying API error.")
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
