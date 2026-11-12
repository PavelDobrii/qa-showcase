"""Home page with the product list, search, sorting and filters."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Self

from playwright.sync_api import Page, Response, expect

from framework.pages.base_page import BasePage


def is_product_list_response(response: Response) -> bool:
    """True for the API call that loads the product list (GET or QUERY method)."""
    path = response.url.split("?", 1)[0]
    return path.endswith(("/products", "/products/search"))


class CatalogPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.search_input = page.get_by_test_id("search-query")
        self.search_button = page.get_by_test_id("search-submit")
        self.search_result_count = page.get_by_test_id("search-result-count")
        self.sort_select = page.get_by_test_id("sort")
        self.product_names = page.get_by_test_id("product-name")
        self.product_prices = page.get_by_test_id("product-price")

    def open(self) -> Self:
        return self.visit("/")

    def wait_until_loaded(self) -> None:
        expect(self.product_names.first).to_be_visible()

    def search(self, term: str) -> None:
        def submit() -> None:
            self.search_input.fill(term)
            self.search_button.click()

        self._reload_products(submit, done_marker="search_completed")

    def sort_by(self, option_label: str) -> None:
        self._reload_products(
            lambda: self.sort_select.select_option(label=option_label),
            done_marker="sorting_completed",
        )

    def filter_by_category(self, category_id: str) -> None:
        self._reload_products(
            lambda: self.page.get_by_test_id(f"category-{category_id}").check(),
            done_marker="filter_completed",
        )

    def names(self) -> list[str]:
        return [name.strip() for name in self.product_names.all_inner_texts()]

    def prices(self) -> list[Decimal]:
        texts = self.product_prices.all_inner_texts()
        return [Decimal(text.strip().lstrip("$")) for text in texts]

    def _reload_products(self, action: Callable[[], None], done_marker: str) -> None:
        """Do an action that reloads the product list and wait until the new list is shown.

        This is the stable wait pattern used in this project. No sleep():
        1. Start to listen for the API response before the action, so a fast
           response is not missed.
        2. Wait until the response body is fully received.
        3. Wait for the marker that the app sets when it has drawn the new list.
           Without this step the test can read the old list.
        """
        with self.page.expect_response(is_product_list_response) as response_info:
            action()
        response = response_info.value
        response.finished()
        assert response.ok, f"Product list request failed: {response.status} {response.url}"
        expect(self.page.get_by_test_id(done_marker)).to_be_visible()
