from __future__ import annotations

FIXTURE_RECIPES: list[dict[str, object]] = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "title": "Scrambled Eggs",
        "prep_minutes": 10,
        "dietary_tags": [],
        "ingredients": [
            {"canonical_name": "eggs", "quantity": 2.0, "unit": "unit"},
            {"canonical_name": "butter", "quantity": 1.0, "unit": "tbsp"},
        ],
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "title": "Chicken Stir Fry",
        "prep_minutes": 20,
        "dietary_tags": [],
        "ingredients": [
            {"canonical_name": "chicken", "quantity": 500.0, "unit": "g"},
            {"canonical_name": "carrots", "quantity": 2.0, "unit": "piece"},
            {"canonical_name": "spinach", "quantity": 100.0, "unit": "g"},
        ],
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "title": "Pasta Bolognese",
        "prep_minutes": 40,
        "dietary_tags": [],
        "ingredients": [
            {"canonical_name": "pasta", "quantity": 200.0, "unit": "g"},
            {"canonical_name": "beef", "quantity": 300.0, "unit": "g"},
            {"canonical_name": "tomatoes", "quantity": 3.0, "unit": "piece"},
        ],
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "title": "Banana Smoothie",
        "prep_minutes": 5,
        "dietary_tags": ["vegetarian"],
        "ingredients": [
            {"canonical_name": "bananas", "quantity": 2.0, "unit": "piece"},
            {"canonical_name": "milk", "quantity": 200.0, "unit": "ml"},
        ],
    },
    {
        "id": "55555555-5555-5555-5555-555555555555",
        "title": "French Toast",
        "prep_minutes": 15,
        "dietary_tags": ["vegetarian"],
        "ingredients": [
            {"canonical_name": "bread", "quantity": 2.0, "unit": "slice"},
            {"canonical_name": "eggs", "quantity": 2.0, "unit": "unit"},
            {"canonical_name": "milk", "quantity": 50.0, "unit": "ml"},
            {"canonical_name": "butter", "quantity": 1.0, "unit": "tbsp"},
        ],
    },
    {
        "id": "66666666-6666-6666-6666-666666666666",
        "title": "Apple Salad",
        "prep_minutes": 10,
        "dietary_tags": ["vegan", "vegetarian", "gluten-free"],
        "ingredients": [
            {"canonical_name": "apples", "quantity": 2.0, "unit": "piece"},
            {"canonical_name": "lettuce", "quantity": 1.0, "unit": "head"},
        ],
    },
    {
        "id": "77777777-7777-7777-7777-777777777777",
        "title": "Beef Stew",
        "prep_minutes": 90,
        "dietary_tags": [],
        "ingredients": [
            {"canonical_name": "beef", "quantity": 400.0, "unit": "g"},
            {"canonical_name": "potatoes", "quantity": 3.0, "unit": "piece"},
            {"canonical_name": "carrots", "quantity": 2.0, "unit": "piece"},
            {"canonical_name": "onions", "quantity": 1.0, "unit": "piece"},
        ],
    },
    {
        "id": "88888888-8888-8888-8888-888888888888",
        "title": "Vegetable Rice",
        "prep_minutes": 30,
        "dietary_tags": ["vegetarian"],
        "ingredients": [
            {"canonical_name": "rice", "quantity": 200.0, "unit": "g"},
            {"canonical_name": "carrots", "quantity": 1.0, "unit": "piece"},
            {"canonical_name": "onions", "quantity": 1.0, "unit": "piece"},
        ],
    },
    {
        "id": "99999999-9999-9999-9999-999999999999",
        "title": "Greek Yogurt Bowl",
        "prep_minutes": 5,
        "dietary_tags": ["vegetarian", "gluten-free"],
        "ingredients": [
            {"canonical_name": "yogurt", "quantity": 200.0, "unit": "g"},
            {"canonical_name": "bananas", "quantity": 1.0, "unit": "piece"},
        ],
    },
    {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "title": "Tomato Soup",
        "prep_minutes": 25,
        "dietary_tags": ["vegan", "vegetarian"],
        "ingredients": [
            {"canonical_name": "tomatoes", "quantity": 5.0, "unit": "piece"},
            {"canonical_name": "onions", "quantity": 1.0, "unit": "piece"},
        ],
    },
    {
        "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "title": "Oatmeal Bowl",
        "prep_minutes": 8,
        "dietary_tags": ["vegetarian"],
        "ingredients": [
            {"canonical_name": "oats", "quantity": 80.0, "unit": "g"},
            {"canonical_name": "milk", "quantity": 200.0, "unit": "ml"},
            {"canonical_name": "bananas", "quantity": 1.0, "unit": "piece"},
        ],
    },
]
