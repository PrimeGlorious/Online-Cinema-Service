import pytest


@pytest.mark.asyncio
async def test_get_cart_by_id_not_found(client):
    """
    Test that the `/carts/{cart_id}` endpoint returns a 404 error
    when a cart with the given ID does not exist.
    """
    cart_id = 1

    response = await client.get(f"/api/v1/theater/cart/{cart_id}/")
    assert response.status_code == 404, f"Expected status code 404, but got {response.status_code}"

    response_data = response.json()
    assert response_data == {"detail": "Not Found"}, (
        f"Expected error message not found. Got: {response_data}"
    )
