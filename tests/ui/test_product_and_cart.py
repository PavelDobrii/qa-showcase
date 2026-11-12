"""Product page and cart. Test data comes from the API, so the UI is checked
against the same data that the backend returns."""

from decimal import Decimal

import pytest
from playwright.sync_api import Page, expect

from framework.api.client import Product
from framework.pages import ProductPage

pytestmark = pytest.mark.ui


def money(value: Decimal) -> str:
    return f"${value:.2f}"


def test_product_page_shows_data_from_api(page: Page, known_product: Product) -> None:
    product_page = ProductPage(page).open(known_product["id"])

    expect(product_page.name).to_have_text(known_product["name"])
    expect(product_page.unit_price).to_have_text(f"{known_product['price']:.2f}")
    expect(product_page.description).to_have_text(known_product["description"])


@pytest.mark.smoke
def test_add_to_cart_updates_badge_and_total(page: Page, known_product: Product) -> None:
    unit_price = Decimal(str(known_product["price"]))
    product_page = ProductPage(page).open(known_product["id"])

    product_page.add_to_cart(quantity=2)

    expect(product_page.cart_badge).to_have_text("2")
    cart = product_page.open_cart()
    expect(cart.item_titles).to_have_count(1)
    expect(cart.item_titles.first).to_contain_text(known_product["name"])
    expect(cart.item_quantities.first).to_have_value("2")
    expect(cart.line_totals.first).to_have_text(money(unit_price * 2))
    expect(cart.total).to_have_text(money(unit_price * 2))


def test_out_of_stock_product_cannot_be_added(page: Page, out_of_stock_product: Product) -> None:
    product_page = ProductPage(page).open(out_of_stock_product["id"])

    expect(product_page.out_of_stock_label).to_be_visible()
    expect(product_page.add_to_cart_button).to_be_disabled()
