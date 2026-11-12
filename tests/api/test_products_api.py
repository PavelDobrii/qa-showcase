"""Product catalogue API: list, search, sorting, errors.

The demo API is public and other people add their own products to it. So the
tests never check exact totals. They check rules that stay true for any data.
"""

import jsonschema
import pytest

from framework.api import ToolshopApi
from framework.api.client import Product
from framework.api.schemas import PRODUCT, PRODUCT_PAGE

pytestmark = pytest.mark.api


@pytest.mark.smoke
def test_product_list_is_paginated(api: ToolshopApi) -> None:
    first = api.get_products(page=1)
    second = api.get_products(page=2)

    assert first.status_code == 200
    assert second.status_code == 200
    body = first.json()
    jsonschema.validate(body, PRODUCT_PAGE)
    assert body["current_page"] == 1
    assert len(body["data"]) == body["per_page"]
    first_ids = {p["id"] for p in body["data"]}
    second_ids = {p["id"] for p in second.json()["data"]}
    assert first_ids.isdisjoint(second_ids), "The same product is on page 1 and page 2"


def test_single_product_matches_schema(api: ToolshopApi, known_product: Product) -> None:
    response = api.get_product(known_product["id"])

    assert response.status_code == 200
    product = response.json()
    jsonschema.validate(product, PRODUCT)
    assert (product["id"], product["name"]) == (known_product["id"], known_product["name"])


@pytest.mark.parametrize("term", ["pliers", "drill"])
def test_search_returns_only_matching_products(api: ToolshopApi, term: str) -> None:
    response = api.search_products(term)

    assert response.status_code == 200
    names = [p["name"] for p in response.json()["data"]]
    assert names, f"No results for {term!r}"
    not_matching = [name for name in names if term not in name.lower()]
    assert not not_matching, f"Results without {term!r} in the name: {not_matching}"


@pytest.mark.parametrize(
    ("direction", "descending"),
    [("asc", False), ("desc", True)],
    ids=["price-ascending", "price-descending"],
)
def test_products_are_sorted_by_price(api: ToolshopApi, direction: str, descending: bool) -> None:
    response = api.get_products(sort=f"price,{direction}")

    assert response.status_code == 200
    prices = [p["price"] for p in response.json()["data"]]
    assert len(prices) > 1
    assert prices == sorted(prices, reverse=descending)


def test_unknown_product_returns_404(api: ToolshopApi) -> None:
    response = api.get_product("00000000000000000000000000")

    assert response.status_code == 404
    assert response.json()["message"] == "Requested item not found"
