"""APIModel 의 청구 토큰·비용 집계와 400 data_inspection_failed 처리 (DashScope 백본, 2026-11-11).

- 응답에 usage.cost 가 없으면(DashScope) SURVEYFORGE_PRICE_INPUT/OUTPUT 단가로 계산하고, 있으면(OpenRouter) 그 값을 쓴다.
- data_inspection_failed 는 같은 입력을 다시 보내도 같은 판정이라 재시도하지 않고 DataInspectionFailed 로 멈춘다.

Network-free (OpenAI 클라이언트를 가짜로 바꾼다).

    cd code && ../.venv/bin/python -m pytest ../tests/test_model_usage.py -q
"""

import os
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'code'))

import src.model as M  # noqa: E402

URL = 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1'


def _completion(content='ok', usage=None, finish='stop'):
    msg = types.SimpleNamespace(content=content)
    choice = types.SimpleNamespace(message=msg, finish_reason=finish)
    return types.SimpleNamespace(choices=[choice], usage=usage)


class _FakeClient:
    def __init__(self, behaviour):
        self.calls = 0
        outer = self

        class _Completions:
            def create(self, **kw):
                outer.calls += 1
                outer.last_kwargs = kw
                return behaviour(outer.calls)

        self.chat = types.SimpleNamespace(completions=_Completions())


class _Base(unittest.TestCase):
    def setUp(self):
        self._stats = dict(M.LLM_STATS)
        self._events = list(M.DATA_INSPECTION_EVENTS)
        for k, v in M.LLM_STATS.items():
            M.LLM_STATS[k] = 0.0 if k == 'cost_usd' else (None if k == 'cost_source' else 0)
        M.DATA_INSPECTION_EVENTS.clear()
        self._sleep = mock.patch.object(M.time, 'sleep', lambda s: None)
        self._sleep.start()

    def tearDown(self):
        self._sleep.stop()
        M.LLM_STATS.clear(); M.LLM_STATS.update(self._stats)
        M.DATA_INSPECTION_EVENTS[:] = self._events

    def _model(self, behaviour):
        fake = _FakeClient(behaviour)
        patcher = mock.patch.object(M, 'OpenAI', lambda **kw: fake)
        patcher.start(); self.addCleanup(patcher.stop)
        return M.APIModel('qwen-plus-2025-12-01', 'k', URL), fake


class UsageAndCost(_Base):
    def test_price_fallback_when_no_cost_in_response(self):
        usage = {'prompt_tokens': 1_000_000, 'completion_tokens': 500_000,
                 'prompt_tokens_details': {'cached_tokens': 10}}
        with mock.patch.multiple(M, PRICE_INPUT=0.4, PRICE_OUTPUT=1.2):
            m, fake = self._model(lambda n: _completion(usage=usage))
            self.assertEqual(m.chat('x'), 'ok')
        self.assertEqual(M.LLM_STATS['prompt_tokens'], 1_000_000)
        self.assertEqual(M.LLM_STATS['completion_tokens'], 500_000)
        self.assertEqual(M.LLM_STATS['cached_tokens'], 10)
        self.assertEqual(M.LLM_STATS['calls_over_256k'], 1)
        self.assertAlmostEqual(M.LLM_STATS['cost_usd'], 0.4 + 0.6)
        self.assertTrue(M.LLM_STATS['cost_source'].startswith('tokens x price'))
        # thinking 관련 필드를 보내지 않는다 (DashScope 기본 꺼짐)
        self.assertEqual(fake.last_kwargs['extra_body'], {})
        self.assertEqual(fake.last_kwargs['max_tokens'], M.MAX_TOKENS)

    def test_reported_cost_wins(self):
        usage = {'prompt_tokens': 1000, 'completion_tokens': 10, 'cost': 0.25}
        with mock.patch.multiple(M, PRICE_INPUT=0.4, PRICE_OUTPUT=1.2):
            m, _ = self._model(lambda n: _completion(usage=usage))
            m.chat('x')
        self.assertAlmostEqual(M.LLM_STATS['cost_usd'], 0.25)

    def test_discarded_truncated_response_is_still_billed(self):
        usage = {'prompt_tokens': 100, 'completion_tokens': 8192}

        def beh(n):
            return _completion(usage=usage, finish='length' if n == 1 else 'stop')
        with mock.patch.object(M, 'RETRY_TRUNCATED', True):
            m, fake = self._model(beh)
            m.chat('x')
        self.assertEqual(fake.calls, 2)
        self.assertEqual(M.LLM_STATS['completion_tokens'], 2 * 8192)


class DataInspection(_Base):
    def _reject(self, n):
        raise Exception("Error code: 400 - {'error': {'code': 'data_inspection_failed', "
                        "'message': 'Input data may contain inappropriate content.'}}")

    def test_chat_stops_without_retry(self):
        m, fake = self._model(self._reject)
        with self.assertRaises(M.DataInspectionFailed):
            m.chat('some prompt')
        self.assertEqual(fake.calls, 1)
        self.assertEqual(M.LLM_STATS['data_inspection_failed'], 1)
        self.assertEqual(M.LLM_STATS['error_retries'], 0)
        ev = M.DATA_INSPECTION_EVENTS[0]
        self.assertEqual(ev['prompt_chars'], len('some prompt'))
        self.assertIn('data_inspection_failed', ev['error'])

    def test_batch_stops_before_serial_retry_rounds(self):
        def beh(n):
            if n == 2:
                self._reject(n)
            return _completion(usage={'prompt_tokens': 1, 'completion_tokens': 1})
        m, fake = self._model(beh)
        with self.assertRaises(M.DataInspectionFailed):
            m.batch_chat(['a', 'b', 'c'])
        self.assertEqual(fake.calls, 3)   # 첫 회차만, 직렬 재시도 없음

    def test_other_errors_still_retry(self):
        def beh(n):
            if n == 1:
                raise Exception('Error code: 429 - rate limit')
            return _completion(usage={'prompt_tokens': 1, 'completion_tokens': 1})
        m, fake = self._model(beh)
        self.assertEqual(m.chat('x'), 'ok')
        self.assertEqual(fake.calls, 2)
        self.assertEqual(M.LLM_STATS['error_retries'], 1)


if __name__ == '__main__':
    unittest.main()
