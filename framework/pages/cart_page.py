"""Cart: the first step of the checkout."""

from __future__ import annotations

from playwright.sync_api import Page, expect

from framework.pages.base_page import BasePage


class CartPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.item_titles = page.get_by_test_id("product-title")
        self.item_quantities = page.get_by_test_id("product-quantity")
        self.item_prices = page.get_by_test_id("product-price")
        self.line_totals = page.get_by_test_id("line-price")
        self.total = page.get_by_test_id("cart-total")

    def wait_until_loaded(self) -> None:
        expect(self.total).to_be_visible()
