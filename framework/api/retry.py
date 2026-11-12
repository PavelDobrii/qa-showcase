"""Retry for short network problems.

A public demo API is shared by many people. Sometimes it is slow, returns
429 (too many requests) or a 5xx error for a moment. Such a failure says
nothing about the feature under test, so the client tries again.

Rules:
- Retry only temporary problems: connection errors, timeouts, 429, 502, 503, 504.
- Never retry other statuses. A 404 or 422 is a real answer, and the test must see it.
- Retry a 5xx or a timeout only for idempotent methods (GET, PUT, DELETE...).
  A POST may already be done on the server, so a second POST can create a duplicate.
- Wait a bit longer before each new attempt (exponential backoff).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

import httpx

log = logging.getLogger(__name__)

IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})
RETRY_FOR_ALL_METHODS = frozenset({429})
RETRY_FOR_IDEMPOTENT_METHODS = frozenset({502, 503, 504})
MAX_RETRY_AFTER_SECONDS = 10.0


class RetryTransport(httpx.BaseTransport):
    """An httpx transport that retries temporary failures."""

    def __init__(
        self,
        wrapped: httpx.BaseTransport | None = None,
        *,
        attempts: int = 3,
        backoff: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if attempts < 1:
            raise ValueError("attempts must be at least 1")
        self._wrapped = wrapped or httpx.HTTPTransport()
        self._attempts = attempts
        self._backoff = backoff
        self._sleep = sleep

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        idempotent = request.method in IDEMPOTENT_METHODS
        for attempt in range(1, self._attempts + 1):
            last_attempt = attempt == self._attempts
            try:
                response = self._wrapped.handle_request(request)
            except httpx.ConnectError:
                # The request did not reach the server, so it is safe to send it again.
                if last_attempt:
                    raise
                reason, delay = "connection error", self._delay(attempt)
            except httpx.TransportError as error:
                # Timeout or broken response: the server may have done the work already.
                if last_attempt or not idempotent:
                    raise
                reason, delay = type(error).__name__, self._delay(attempt)
            else:
                if last_attempt or not self._should_retry(response.status_code, idempotent):
                    return response
                reason, delay = f"status {response.status_code}", self._delay(attempt, response)
                response.close()

            log.warning(
                "%s %s: %s, attempt %d of %d, next try in %.1fs",
                request.method,
                request.url,
                reason,
                attempt,
                self._attempts,
                delay,
            )
            self._sleep(delay)

        raise AssertionError("unreachable: the loop always returns or raises")

    def close(self) -> None:
        self._wrapped.close()

    @staticmethod
    def _should_retry(status_code: int, idempotent: bool) -> bool:
        if status_code in RETRY_FOR_ALL_METHODS:
            return True
        return idempotent and status_code in RETRY_FOR_IDEMPOTENT_METHODS

    def _delay(self, attempt: int, response: httpx.Response | None = None) -> float:
        if response is not None:
            retry_after = response.headers.get("Retry-After", "")
            if retry_after.isdigit():
                return min(float(retry_after), MAX_RETRY_AFTER_SECONDS)
        return self._backoff * 2 ** (attempt - 1)
