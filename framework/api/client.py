"""Client for the Toolshop REST API.

Request methods return the raw `httpx.Response`, so a test can check the
status code and the body itself. Helper methods at the end prepare test data
and raise an error if the API does not answer as expected.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

import httpx

from framework.api.retry import RetryTransport

Product = dict[str, Any]


class ToolshopApi:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._http = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            transport=transport or RetryTransport(),
            headers={"Accept": "application/json"},
        )

    def close(self) -> None:
        self._http.close()

    # Products

    def get_products(self, **params: Any) -> httpx.Response:
        return self._http.get("/products", params=params)

    def search_products(self, query: str, **params: Any) -> httpx.Response:
        return self._http.get("/products/search", params={"q": query, **params})

    def get_product(self, product_id: str) -> httpx.Response:
        return self._http.get(f"/products/{product_id}")

    def get_categories(self) -> httpx.Response:
        return self._http.get("/categories")

    # Carts

    def create_cart(self) -> httpx.Response:
        return self._http.post("/carts")

    def get_cart(self, cart_id: str) -> httpx.Response:
        return self._http.get(f"/carts/{cart_id}")

    def add_to_cart(self, cart_id: str, product_id: str, quantity: int) -> httpx.Response:
        return self._http.post(
            f"/carts/{cart_id}",
            json={"product_id": product_id, "quantity": quantity},
        )

    def update_cart_quantity(self, cart_id: str, product_id: str, quantity: int) -> httpx.Response:
        return self._http.put(
            f"/carts/{cart_id}/product/quantity",
            json={"product_id": product_id, "quantity": quantity},
        )

    def remove_from_cart(self, cart_id: str, product_id: str) -> httpx.Response:
        return self._http.delete(f"/carts/{cart_id}/product/{product_id}")

    def delete_cart(self, cart_id: str) -> httpx.Response:
        return self._http.delete(f"/carts/{cart_id}")

    # Helpers for test data

    def iter_products(self, **params: Any) -> Iterator[Product]:
        """Yield products from all pages, not only from the first one."""
        page = 1
        while True:
            body = self.get_products(page=page, **params).raise_for_status().json()
            yield from body["data"]
            if body["current_page"] >= body["last_page"]:
                return
            page += 1

    def find_product(self, query: str, condition: Callable[[Product], bool]) -> Product:
        """Return the first search result for `query` that matches `condition`."""
        results = self.search_products(query).raise_for_status().json()["data"]
        for product in results:
            if condition(product):
                return product
        raise LookupError(f"No product for search {query!r} matches the condition")

    def category_by_slug(self, slug: str) -> dict[str, Any]:
        for category in self.get_categories().raise_for_status().json():
            if category["slug"] == slug:
                return category
        raise LookupError(f"Category {slug!r} not found")
