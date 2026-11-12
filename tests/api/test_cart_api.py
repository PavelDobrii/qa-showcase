"""Cart API. Every test gets its own new cart from the `cart_id` fixture."""

import pytest

from framework.api import ToolshopApi
from framework.api.client import Product

pytestmark = pytest.mark.api


def cart_items(api: ToolshopApi, cart_id: str) -> list[dict]:
    response = api.get_cart(cart_id)
    assert response.status_code == 200, response.text
    return response.json()["cart_items"]


@pytest.mark.smoke
def test_cart_item_can_be_added_changed_and_removed(
    api: ToolshopApi, cart_id: str, known_product: Product
) -> None:
    product_id = known_product["id"]

    added = api.add_to_cart(cart_id, product_id, quantity=2)
    assert added.status_code == 200, added.text
    items = cart_items(api, cart_id)
    assert [(i["product_id"], i["quantity"]) for i in items] == [(product_id, 2)]
    assert items[0]["product"]["name"] == known_product["name"]

    updated = api.update_cart_quantity(cart_id, product_id, quantity=5)
    assert updated.status_code == 200, updated.text
    assert cart_items(api, cart_id)[0]["quantity"] == 5

    removed = api.remove_from_cart(cart_id, product_id)
    assert removed.status_code == 204
    assert cart_items(api, cart_id) == []


def test_unknown_product_cannot_be_added_to_cart(api: ToolshopApi, cart_id: str) -> None:
    response = api.add_to_cart(cart_id, "unknown-product", quantity=1)

    assert response.status_code == 422
    assert "product_id" in response.json()["errors"]
    assert cart_items(api, cart_id) == []
