import time
import unittest
from unittest.mock import patch

import httpx

from skyflow_flowvault.utils import _retry
from skyflow_flowvault.utils._retry import (
    should_retry,
    backoff_millis,
    RetryTransport,
    AsyncRetryTransport,
    _RetryPolicy,
)


class FakeTransport(httpx.BaseTransport):
    def __init__(self, statuses):
        self._statuses = list(statuses)
        self.calls = 0
        self.closed = False

    def handle_request(self, request):
        status = self._statuses[min(self.calls, len(self._statuses) - 1)]
        self.calls += 1
        return httpx.Response(status, request=request)

    def close(self):
        self.closed = True


class FakeAsyncTransport(httpx.AsyncBaseTransport):
    def __init__(self, statuses):
        self._statuses = list(statuses)
        self.calls = 0
        self.closed = False

    async def handle_async_request(self, request):
        status = self._statuses[min(self.calls, len(self._statuses) - 1)]
        self.calls += 1
        return httpx.Response(status, request=request)

    async def aclose(self):
        self.closed = True


def _request():
    return httpx.Request("POST", "https://vault.example.com/records")


class TestShouldRetry(unittest.TestCase):
    def test_retryable_statuses(self):
        for code in (408, 429, 500, 502, 503, 599):
            self.assertTrue(should_retry(code))

    def test_non_retryable_statuses(self):
        for code in (200, 201, 400, 401, 404, 409, 422):
            self.assertFalse(should_retry(code))


class TestBackoffMillis(unittest.TestCase):
    def test_exponential_growth_capped_at_max(self):
        # jitter is int(delay*0.2), which is 0 for every delay here (max 4 -> 0.8 -> 0), so exact.
        self.assertEqual(backoff_millis(1, 1, 4), 1)
        self.assertEqual(backoff_millis(2, 1, 4), 2)
        self.assertEqual(backoff_millis(3, 1, 4), 4)
        self.assertEqual(backoff_millis(4, 1, 4), 4)  # capped
        self.assertEqual(backoff_millis(5, 1, 4), 4)

    def test_jitter_within_bounds(self):
        for _ in range(50):
            value = backoff_millis(1, 500, 2000)
            self.assertGreaterEqual(value, 400)   # 500 - 20%
            self.assertLessEqual(value, 600)       # 500 + 20%


class TestRetryPolicy(unittest.TestCase):
    def test_no_deadline_when_call_timeout_falsy(self):
        self.assertIsNone(_RetryPolicy(3, 500, 2000, 0).deadline())
        self.assertIsNone(_RetryPolicy(3, 500, 2000, None).deadline())

    def test_next_sleep_none_when_retries_exhausted(self):
        policy = _RetryPolicy(2, 1, 1, None)
        self.assertIsNone(policy.next_sleep_seconds(2, None))

    def test_next_sleep_none_when_deadline_passed(self):
        policy = _RetryPolicy(3, 1, 1, 60)
        self.assertIsNone(policy.next_sleep_seconds(0, time.monotonic() - 1))

    def test_next_sleep_capped_to_remaining_budget(self):
        policy = _RetryPolicy(3, 100000, 100000, 60)
        remaining = policy.next_sleep_seconds(0, time.monotonic() + 0.05)
        self.assertIsNotNone(remaining)
        self.assertLessEqual(remaining, 0.05)

    def test_next_sleep_none_when_budget_exhausted_after_check(self):
        policy = _RetryPolicy(3, 1, 1, 60)
        with patch.object(_retry.time, "monotonic", side_effect=[99, 100]):
            self.assertIsNone(policy.next_sleep_seconds(0, 100))


class TestRetryTransport(unittest.TestCase):
    def setUp(self):
        self._real_sleep = _retry.time.sleep
        _retry.time.sleep = lambda s: None

    def tearDown(self):
        _retry.time.sleep = self._real_sleep

    def test_retries_until_success(self):
        inner = FakeTransport([503, 503, 200])
        transport = RetryTransport(inner, max_retries=3, initial_millis=1, max_millis=1, call_timeout=None)
        response = transport.handle_request(_request())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(inner.calls, 3)

    def test_stops_after_max_retries(self):
        inner = FakeTransport([503])
        transport = RetryTransport(inner, max_retries=2, initial_millis=1, max_millis=1, call_timeout=None)
        response = transport.handle_request(_request())
        self.assertEqual(response.status_code, 503)
        self.assertEqual(inner.calls, 3)  # 1 initial + 2 retries

    def test_no_retry_on_success(self):
        inner = FakeTransport([200])
        transport = RetryTransport(inner, max_retries=3, initial_millis=1, max_millis=1, call_timeout=None)
        transport.handle_request(_request())
        self.assertEqual(inner.calls, 1)

    def test_no_retry_when_max_retries_zero(self):
        inner = FakeTransport([503])
        transport = RetryTransport(inner, max_retries=0, initial_millis=1, max_millis=1, call_timeout=None)
        response = transport.handle_request(_request())
        self.assertEqual(response.status_code, 503)
        self.assertEqual(inner.calls, 1)

    def test_close_delegates(self):
        inner = FakeTransport([200])
        RetryTransport(inner, 1, 1, 1, None).close()
        self.assertTrue(inner.closed)


class TestAsyncRetryTransport(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._real_sleep = _retry.asyncio.sleep

        async def _no_sleep(_):
            return None

        _retry.asyncio.sleep = _no_sleep

    def tearDown(self):
        _retry.asyncio.sleep = self._real_sleep

    async def test_retries_until_success(self):
        inner = FakeAsyncTransport([503, 200])
        transport = AsyncRetryTransport(inner, max_retries=3, initial_millis=1, max_millis=1, call_timeout=None)
        response = await transport.handle_async_request(_request())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(inner.calls, 2)

    async def test_stops_after_max_retries(self):
        inner = FakeAsyncTransport([500])
        transport = AsyncRetryTransport(inner, max_retries=1, initial_millis=1, max_millis=1, call_timeout=None)
        response = await transport.handle_async_request(_request())
        self.assertEqual(response.status_code, 500)
        self.assertEqual(inner.calls, 2)

    async def test_aclose_delegates(self):
        inner = FakeAsyncTransport([200])
        await AsyncRetryTransport(inner, 1, 1, 1, None).aclose()
        self.assertTrue(inner.closed)


if __name__ == "__main__":
    unittest.main()
