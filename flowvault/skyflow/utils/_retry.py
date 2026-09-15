import asyncio
import time
from random import randint

import httpx

RETRYABLE_STATUS_CODES = frozenset({408, 429})
MIN_SERVER_ERROR_STATUS = 500
JITTER_FACTOR = 0.2
MILLIS_PER_SECOND = 1000.0


def should_retry(status_code):
    return status_code in RETRYABLE_STATUS_CODES or status_code >= MIN_SERVER_ERROR_STATUS


def backoff_millis(attempt, initial_millis, max_millis):
    delay = initial_millis
    step = 1
    while step < attempt and delay < max_millis:
        delay = max_millis if delay > max_millis / 2 else delay * 2
        step += 1
    delay = min(delay, max_millis)
    jitter = int(delay * JITTER_FACTOR)
    if jitter <= 0:
        return delay
    return max(0, delay - jitter + randint(0, 2 * jitter))


class _RetryPolicy:
    def __init__(self, max_retries, initial_millis, max_millis, call_timeout):
        self.max_retries = max_retries
        self.initial_millis = initial_millis
        self.max_millis = max_millis
        self.call_timeout = call_timeout

    def deadline(self):
        return time.monotonic() + self.call_timeout if self.call_timeout else None

    def next_sleep_seconds(self, retry, deadline):
        if retry >= self.max_retries:
            return None
        if deadline is not None and time.monotonic() >= deadline:
            return None
        sleep_seconds = backoff_millis(retry + 1, self.initial_millis, self.max_millis) / MILLIS_PER_SECOND
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            sleep_seconds = min(sleep_seconds, remaining)
        return sleep_seconds


class RetryTransport(httpx.BaseTransport):
    def __init__(self, transport, max_retries, initial_millis, max_millis, call_timeout):
        self._transport = transport
        self._policy = _RetryPolicy(max_retries, initial_millis, max_millis, call_timeout)

    def handle_request(self, request):
        deadline = self._policy.deadline()
        response = self._transport.handle_request(request)
        retry = 0
        while should_retry(response.status_code):
            sleep_seconds = self._policy.next_sleep_seconds(retry, deadline)
            if sleep_seconds is None:
                break
            response.close()
            time.sleep(sleep_seconds)
            response = self._transport.handle_request(request)
            retry += 1
        return response

    def close(self):
        self._transport.close()


class AsyncRetryTransport(httpx.AsyncBaseTransport):
    def __init__(self, transport, max_retries, initial_millis, max_millis, call_timeout):
        self._transport = transport
        self._policy = _RetryPolicy(max_retries, initial_millis, max_millis, call_timeout)

    async def handle_async_request(self, request):
        deadline = self._policy.deadline()
        response = await self._transport.handle_async_request(request)
        retry = 0
        while should_retry(response.status_code):
            sleep_seconds = self._policy.next_sleep_seconds(retry, deadline)
            if sleep_seconds is None:
                break
            await response.aclose()
            await asyncio.sleep(sleep_seconds)
            response = await self._transport.handle_async_request(request)
            retry += 1
        return response

    async def aclose(self):
        await self._transport.aclose()
