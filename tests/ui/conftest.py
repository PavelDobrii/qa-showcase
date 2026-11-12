"""Fixtures for browser tests. The `page` fixture comes from pytest-playwright."""

from __future__ import annotations

from typing import Any

import pytest
from playwright.sync_api import Page, Playwright, expect

from framework.api import ToolshopApi
from framework.config import Settings
from framework.pages import CatalogPage


@pytest.fixture(scope="session")
def base_url(settings: Settings, api: ToolshopApi) -> str:
    """Lets tests use short paths like page.goto("/").

    It uses the `api` fixture, so browser tests also wait until the demo data is ready.
    """
    return settings.ui_url


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    return {
        **browser_context_args,
        "locale": "en-US",
        "viewport": {"width": 1366, "height": 900},
    }


@pytest.fixture(scope="session", autouse=True)
def _use_data_test_attribute(playwright: Playwright) -> None:
    """The shop marks elements with data-test="...". get_by_test_id() will use it."""
    playwright.selectors.set_test_id_attribute("data-test")


@pytest.fixture(autouse=True)
def _timeouts(page: Page, settings: Settings) -> None:
    page.set_default_timeout(settings.ui_timeout_ms)
    expect.set_options(timeout=settings.ui_timeout_ms)


@pytest.fixture
def catalog(page: Page) -> CatalogPage:
    return CatalogPage(page).open()
