"""Product list in the browser: search, sorting, category filter."""

import pytest
from playwright.sync_api import expect

from framework.api import ToolshopApi
from framework.pages import CatalogPage

pytestmark = pytest.mark.ui


@pytest.mark.smoke
def test_search_shows_only_matching_products(catalog: CatalogPage) -> None:
    catalog.search("pliers")

    names = catalog.names()
    assert names
    assert all("pliers" in name.lower() for name in names), names
    expect(catalog.search_result_count).to_contain_text(f"{len(names)} products found")


@pytest.mark.parametrize(
    ("option", "descending"),
    [("Price (Low - High)", False), ("Price (High - Low)", True)],
    ids=["low-to-high", "high-to-low"],
)
def test_sort_by_price(catalog: CatalogPage, option: str, descending: bool) -> None:
    catalog.sort_by(option)

    prices = catalog.prices()
    assert len(prices) > 1
    assert prices == sorted(prices, reverse=descending)


def test_category_filter_matches_api(catalog: CatalogPage, api: ToolshopApi) -> None:
    category = api.category_by_slug("hammer")
    names_in_api = {p["name"] for p in api.iter_products(by_category=category["id"])}

    catalog.filter_by_category(category["id"])

    names_in_ui = catalog.names()
    assert names_in_ui
    assert set(names_in_ui) <= names_in_api, set(names_in_ui) - names_in_api
