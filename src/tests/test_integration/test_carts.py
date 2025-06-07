import pytest
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.models.carts import CartItemModel, CartModel


@pytest.mark.asyncio
async def test_get_carts_empty_database(client):
    """
    Test that the `/cart/` endpoint returns a 404 error when the database is empty.
    """
    response = await client.get("/api/v1/cart/")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    expected_detail = {"detail": "Not Found"}
    assert response.json() == expected_detail, f"Expected {expected_detail}, got {response.json()}"


@pytest.mark.asyncio
async def test_get_carts(client, seed_database):
    """
    Test the `/carts/` endpoint with not empty table.
    """
    response = await client.get("/api/v1/cart/")
    assert response.status_code == 200, "Expected status code 200, but got a different value"


@pytest.mark.asyncio
async def test_create_cart_duplicate_error(client, db_session, seed_database):
    """
    Test that trying to create another shopping cart for the same user.
    """
    stmt = select(CartModel).limit(1)
    result = await db_session.execute(stmt)
    existing_cart = result.scalars().first()
    assert existing_cart is not None, "No existing carts found in the database."

    cart_data = {
        "user_id": existing_cart.user_id,
    }

    response = await client.post("/api/v1/cart/create/", json=cart_data)
    assert response.status_code == 409, f"Expected status code 409, but got {response.status_code}"

    response_data = response.json()
    expected_detail = (
        f"A cart for the user with ID '{cart_data['user_id']}' already exists."
    )
    assert response_data["detail"] == expected_detail, (
        f"Expected detail message: {expected_detail}, but got: {response_data['detail']}"
    )


@pytest.mark.asyncio
async def test_get_cart_by_id_not_found(client):
    """
    Test that the `/carts/{cart_id}` endpoint returns a 404 error
    when a cart with the given ID does not exist.
    """
    cart_id = 1

    response = await client.get(f"/api/v1/carts/{cart_id}/")
    assert response.status_code == 404, f"Expected status code 404, but got {response.status_code}"

    response_data = response.json()
    assert response_data == {"detail": "Not Found"}, (
        f"Expected error message not found. Got: {response_data}"
    )
