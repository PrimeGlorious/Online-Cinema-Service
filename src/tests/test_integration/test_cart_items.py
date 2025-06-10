import pytest
from sqlalchemy import select
from database.models.carts import CartItemModel


@pytest.mark.asyncio
async def test_get_cart_items_empty_database(client):
    """
    Test that the `/cart_items/` endpoint returns a 404 error when the database is empty.
    """
    response = await client.get("/api/v1/theater/cart_items/")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    expected_detail = {"detail": "Not Found"}
    assert response.json() == expected_detail, f"Expected {expected_detail}, got {response.json()}"


@pytest.mark.asyncio
async def test_get_cart_items_by_id_not_found(client):
    """
    Test that the `/cart_items/{cart_item_id}` endpoint returns a 404 error
    when a cart item with the given ID does not exist.
    """
    cart_item_id = 1

    response = await client.get(f"/api/v1/theater/cart_items/{cart_item_id}/")
    assert response.status_code == 404, f"Expected status code 404, but got {response.status_code}"

    response_data = response.json()
    assert response_data == {"detail": "Not Found"}, (
        f"Expected error message not found. Got: {response_data}"
    )


@pytest.mark.asyncio
async def test_create_cart_item_already_exists(client, db_session):
    try:
        stmt = select(CartItemModel).limit(1)
        result = await db_session.execute(stmt)
        cart_item = result.scalars().first()
        cart_id = cart_item.cart_id
        movie_id = cart_item.movie_id

        assert cart_item is not None
        response = await client.post(
            "/api/v1/theater/carts/add/",
            json={"cart_id": cart_id,
                  "movie_id": movie_id,}
        )
        assert response.status_code == 409
        assert "was already added to the shopping card ID" in response.json()["detail"]
    finally:
        await db_session.rollback()
