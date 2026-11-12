"""Fixtures for all tests."""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from datetime import UTC, datetime

import httpx
import pytest

from framework.api import ToolshopApi
from framework.api.client import Product
from framework.config import Settings
from framework.demo_reset import time_until_safe_start
from framework.waits import wait_until

log = logging.getLogger(__name__)

# Demo data that the Toolshop app always has after a reset.
KNOWN_PRODUCT_NAME = "Combination Pliers"


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings.from_env()


@pytest.fixture(scope="session")
def api(settings: Settings, pytestconfig: pytest.Config) -> Iterator[ToolshopApi]:
    client = ToolshopApi(settings.api_url, timeout=settings.http_timeout)
    if settings.avoid_demo_reset:
        wait_for_demo_data(client, pytestconfig)
    yield client
    client.close()


def wait_for_demo_data(api: ToolshopApi, config: pytest.Config) -> None:
    """Do not start near the hourly reset of the demo database, see framework/demo_reset.py."""
    delay = time_until_safe_start(datetime.now(UTC))
    if delay:
        message = f"Demo database reset is near. Waiting {delay.seconds}s before the tests."
        log.warning(message)
        # pytest captures the output of tests. The terminal reporter shows the line at once.
        reporter = config.pluginmanager.get_plugin("terminalreporter")
        if reporter:
            reporter.write_line(message, yellow=True)
        time.sleep(delay.total_seconds())

    def demo_data_is_ready() -> bool:
        try:
            response = api.search_products(KNOWN_PRODUCT_NAME)
            return response.status_code == 200 and bool(response.json()["data"])
        except (httpx.HTTPError, ValueError, KeyError):
            return False

    wait_until(demo_data_is_ready, timeout=90, interval=3, description="demo data is ready")


@pytest.fixture
def cart_id(api: ToolshopApi) -> Iterator[str]:
    """An empty cart. It is deleted after the test, also when the test fails."""
    response = api.create_cart()
    assert response.status_code == 201, response.text
    cart_id = response.json()["id"]
    yield cart_id
    api.delete_cart(cart_id)


@pytest.fixture(scope="session")
def known_product(api: ToolshopApi) -> Product:
    """A product that is in stock. Its data comes from the API, not from the test code."""
    return api.find_product(
        KNOWN_PRODUCT_NAME,
        lambda p: p["name"] == KNOWN_PRODUCT_NAME and p["in_stock"],
    )


@pytest.fixture(scope="session")
def out_of_stock_product(api: ToolshopApi) -> Product:
    return api.find_product("pliers", lambda p: not p["in_stock"])
