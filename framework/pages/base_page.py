"""Parts that every page of the shop has."""

from __future__ import annotations

from typing import Self

from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.cart_link = page.get_by_test_id("nav-cart")
        self.cart_badge = page.get_by_test_id("cart-quantity")

    def visit(self, path: str) -> Self:
        self.page.goto(path)
        self.wait_until_loaded()
        return self

    def wait_until_loaded(self) -> None:
        """Wait until the page is ready to use. Each page defines its own signal."""
