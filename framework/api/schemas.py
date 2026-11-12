"""JSON schemas for API responses.

A schema checks the shape of a response: required fields and their types.
Tests check the values separately.
"""

NAMED_ENTITY = {
    "type": "object",
    "required": ["id", "name"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
    },
}

PRODUCT = {
    "type": "object",
    "required": [
        "id",
        "name",
        "description",
        "price",
        "in_stock",
        "is_rental",
        "category",
        "brand",
        "product_image",
    ],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "price": {"type": "number", "exclusiveMinimum": 0},
        "in_stock": {"type": "boolean"},
        "is_rental": {"type": "boolean"},
        "category": NAMED_ENTITY,
        "brand": NAMED_ENTITY,
        "product_image": {
            "type": "object",
            "required": ["file_name"],
            "properties": {"file_name": {"type": "string", "minLength": 1}},
        },
    },
}

PRODUCT_PAGE = {
    "type": "object",
    "required": ["current_page", "last_page", "per_page", "total", "data"],
    "properties": {
        "current_page": {"type": "integer", "minimum": 1},
        "last_page": {"type": "integer", "minimum": 1},
        "per_page": {"type": "integer", "minimum": 1},
        "total": {"type": "integer", "minimum": 0},
        "data": {"type": "array", "items": PRODUCT},
    },
}
