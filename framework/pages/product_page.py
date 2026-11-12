"""Product details page."""

from __future__ import annotations

from typing import Self

from playwright.sync_api import Page, expect

from framework.pages.base_page import BasePage
from framework.pages.cart_page import CartPage


class ProductPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.name = page.get_by_test_id("product-name")
        self.unit_price = page.get_by_test_id("unit-price")
        self.description = page.get_by_test_id("product-description")
        self.quantity_input = page.get_by_test_id("quantity")
        self.add_to_cart_button = page.get_by_test_id("add-to-cart")
        self.out_of_stock_label = page.get_by_test_id("out-of-stock")

    def open(self, product_id: str) -> Self:
        return self.visit(f"/product/{product_id}")

    def wait_until_loaded(self) -> None:
        expect(self.name).to_be_visible()

    def add_to_cart(self, quantity: int = 1) -> None:
        self.quantity_input.fill(str(quantity))
        # The cart is saved on the server. Wait for that call, not for a fixed time.
        with self.page.expect_response(
            lambda r: "/carts/" in r.url and r.request.method == "POST"
        ) as response_info:
            self.add_to_cart_button.click()
        assert response_info.value.ok, f"Add to cart failed: {response_info.value.status}"

    def open_cart(self) -> CartPage:
        self.cart_link.click()
        cart = CartPage(self.page)
        cart.wait_until_loaded()
        return cart
