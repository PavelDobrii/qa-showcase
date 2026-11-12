"""Unit tests for the retry logic. They use a fake server (httpx.MockTransport),
so they need no network and run in milliseconds."""

from collections.abc import Iterator

import httpx
import pytest

from framework.api import RetryTransport

pytestmark = pytest.mark.unit


class FakeServer:
    """Answers with the given status codes, one per request, and counts requests."""

    def __init__(self, statuses: list[int]) -> None:
        self._statuses: Iterator[int] = iter(statuses)
        self.requests = 0

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests += 1
        return httpx.Response(next(self._statuses))


def make_client(server: FakeServer, delays: list[float], attempts: int = 3) -> httpx.Client:
    transport = RetryTransport(
        httpx.MockTransport(server), attempts=attempts, backoff=0.5, sleep=delays.append
    )
    return httpx.Client(base_url="https://api.test", transport=transport)


def test_get_is_retried_until_success() -> None:
    server, delays = FakeServer([503, 502, 200]), []

    response = make_client(server, delays).get("/products")

    assert response.status_code == 200
    assert server.requests == 3
    assert delays == [0.5, 1.0], "Each new wait must be longer (exponential backoff)"


def test_retry_stops_after_last_attempt() -> None:
    server, delays = FakeServer([503, 503, 503, 200]), []

    response = make_client(server, delays, attempts=3).get("/products")

    assert response.status_code == 503, "After the last attempt the test must see the error"
    assert server.requests == 3


def test_post_is_not_retried_after_server_error() -> None:
    # A POST may be done on the server already. A second POST could create a duplicate.
    server, delays = FakeServer([503, 201]), []

    response = make_client(server, delays).post("/carts")

    assert response.status_code == 503
    assert server.requests == 1
    assert delays == []


def test_client_error_is_not_retried() -> None:
    # A 404 is a real answer from the API. The test must see it at once.
    server, delays = FakeServer([404, 200]), []

    response = make_client(server, delays).get("/products/unknown")

    assert response.status_code == 404
    assert server.requests == 1
