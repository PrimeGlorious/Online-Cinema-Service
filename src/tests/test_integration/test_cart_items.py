import pytest
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.models.carts import CartItemModel, CartModel


@pytest.mark.asyncio
async def test_get_cart_items_empty_database(client):
    """
    Test that the `/cart_items/` endpoint returns a 404 error when the database is empty.
    """
    response = await client.get("/api/v1/cart/cart_items/")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    expected_detail = {"detail": "Not Found"}
    assert response.json() == expected_detail, f"Expected {expected_detail}, got {response.json()}"


async def test_cart_items_fields_match_schema(client, db_session, seed_database):
    """
    Test that each cart_item in the response matches the fields defined in `CartItemListResponseSchema`.
    """
    response = await client.get("/api/v1/cart_items")

    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"

    response_data = response.json()

    assert "cart_items" in response_data, "Response missing 'cart_items' field."

    expected_fields = {"id", "name", "year", "price", "genres"}

    for cart_item in response_data["cart_items"]:
        assert set(cart_item.keys()) == expected_fields, (
            f"Cart_item fields do not match schema. "
            f"Expected: {expected_fields}, but got: {set(cart_item.keys())}"
        )


@pytest.mark.asyncio
async def test_get_cart_items_by_id_not_found(client):
    """
    Test that the `/cart_items/{cart_item_id}` endpoint returns a 404 error
    when a cart item with the given ID does not exist.
    """
    cart_item_id = 1

    response = await client.get(f"/api/v1/carts/cart_items/{cart_item_id}/")
    assert response.status_code == 404, f"Expected status code 404, but got {response.status_code}"

    response_data = response.json()
    assert response_data == {"detail": "Not Found"}, (
        f"Expected error message not found. Got: {response_data}"
    )


@pytest.mark.asyncio
async def test_get_cart_item_by_id_fields_match_database(client, db_session, seed_database):
    """
    Test that the `/cart_items/{cart_item_id}` endpoint returns all fields matching the database data.
    """
    stmt = (
        select(CartItemModel)
        .options(
            joinedload(CartItemModel.movie.name),
            joinedload(CartItemModel.movie.genres),
            joinedload(CartItemModel.movie.price),
            joinedload(CartItemModel.movie.year),
        )
        .limit(1)
    )
    result = await db_session.execute(stmt)
    random_cart_item = result.scalars().first()
    assert random_cart_item is not None, "No cart items found in the database."

    response = await client.get(f"/api/v1/cart/cart_items/{random_cart_item.id}/")
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"

    response_data = response.json()

    assert response_data["id"] == random_cart_item.id, "ID does not match."
    assert response_data["name"] == random_cart_item.movie.name, "Name does not match."
    assert response_data["price"] == random_cart_item.movie.price, "Price does not match."
    assert response_data["year"] == random_cart_item.movie.year, "Year does not match."

    actual_genres = sorted(response_data["genres"], key=lambda x: x["id"])
    expected_genres = sorted(
        [{"id": genre.id, "name": genre.name} for genre in random_cart_item.movie.genres],
        key=lambda x: x["id"]
    )
    assert actual_genres == expected_genres, "Genres do not match."
