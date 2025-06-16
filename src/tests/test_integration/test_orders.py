from datetime import datetime, timedelta
import pytest
from sqlalchemy import insert, text
from main import app
from config.dependencies.custom import get_current_user, require_admin
from database.models.orders import OrderStatusEnum, OrderModel, OrderItem


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides = {}


@pytest.fixture
def admin_override():
    admin_user = type("User", (), {"id": 999, "email": "admin@test.com"})
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    return admin_user


async def create_order(db_session, user_id, status, amount, movie_id=1, created_at=None):
    insert_data = {
        "user_id": user_id,
        "status": status,
        "total_amount": amount,
    }
    if created_at:
        insert_data["created_at"] = created_at

    result = await db_session.execute(
        insert(OrderModel).values(**insert_data).returning(OrderModel.id)
    )
    order_id = result.scalar_one()

    await db_session.execute(
        insert(OrderItem).values(order_id=order_id, movie_id=movie_id, price_at_order=amount)
    )
    await db_session.commit()
    return order_id


@pytest.mark.asyncio
async def test_create_order_success(client, seed_user_movie_cart):
    app.dependency_overrides[get_current_user] = lambda: seed_user_movie_cart
    response = await client.post("/api/v1/theater/orders/", json={"movie_ids": [1]})
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == OrderStatusEnum.PENDING.value
    assert data["total_amount"] == "9.99"


@pytest.mark.asyncio
async def test_create_order_cart_not_found(client):
    ghost_user = type("User", (), {"id": 999, "email": "ghost@test.com"})
    app.dependency_overrides[get_current_user] = lambda: ghost_user
    response = await client.post("/api/v1/theater/orders/", json={"movie_ids": [1]})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_order_empty_cart(client, db_session, seed_user_movie_cart):
    app.dependency_overrides[get_current_user] = lambda: seed_user_movie_cart
    await db_session.execute(text("DELETE FROM cart_items;"))
    await db_session.commit()
    response = await client.post("/api/v1/theater/orders/", json={"movie_ids": [1]})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_order_movie_not_in_cart(client, seed_user_movie_cart):
    app.dependency_overrides[get_current_user] = lambda: seed_user_movie_cart
    response = await client.post("/api/v1/theater/orders/", json={"movie_ids": [999]})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_order_already_purchased(client, db_session, seed_user_movie_cart):
    app.dependency_overrides[get_current_user] = lambda: seed_user_movie_cart
    await create_order(db_session, seed_user_movie_cart.id, OrderStatusEnum.PAID, 9.99)
    response = await client.post("/api/v1/theater/orders/", json={"movie_ids": [1]})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_order_conflict_pending(client, db_session, seed_user_movie_cart):
    app.dependency_overrides[get_current_user] = lambda: seed_user_movie_cart
    await create_order(db_session, seed_user_movie_cart.id, OrderStatusEnum.PENDING, 9.99)
    response = await client.post("/api/v1/theater/orders/", json={"movie_ids": [1]})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_my_orders(client, db_session, seed_user_movie_cart):
    app.dependency_overrides[get_current_user] = lambda: seed_user_movie_cart
    order_id = await create_order(db_session, seed_user_movie_cart.id, OrderStatusEnum.PAID, 19.99)

    response = await client.get("/api/v1/theater/orders/")
    assert response.status_code == 200
    data = response.json()
    assert any(order["id"] == order_id for order in data)


@pytest.mark.asyncio
async def test_get_my_order(client, db_session, seed_user_movie_cart):
    app.dependency_overrides[get_current_user] = lambda: seed_user_movie_cart
    order_id = await create_order(db_session, seed_user_movie_cart.id, OrderStatusEnum.PAID, 29.99)

    response = await client.get(f"/api/v1/theater/orders/{order_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id
    assert data["status"] == OrderStatusEnum.PAID.value


@pytest.mark.asyncio
async def test_get_my_order_not_found(client, seed_user_movie_cart):
    app.dependency_overrides[get_current_user] = lambda: seed_user_movie_cart
    response = await client.get("/api/v1/theater/orders/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_my_order_forbidden(client, db_session, seed_user_movie_cart):
    app.dependency_overrides[get_current_user] = lambda: seed_user_movie_cart
    other_user_id = seed_user_movie_cart.id + 1
    order_id = await create_order(db_session, other_user_id, OrderStatusEnum.PAID, 49.99)

    response = await client.get(f"/api/v1/theater/orders/{order_id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_orders_with_filters(client, db_session, seed_user_movie_cart, admin_override):
    now = datetime.utcnow()
    old_date = now - timedelta(days=10)

    await create_order(db_session, seed_user_movie_cart.id, OrderStatusEnum.PAID, 9.99, created_at=now)
    await create_order(db_session, seed_user_movie_cart.id, OrderStatusEnum.PENDING, 5.99, created_at=old_date)

    response = await client.get(f"/api/v1/theater/admin/orders/?status={OrderStatusEnum.PAID.value}")
    assert response.status_code == 200
    assert all(order["status"] == OrderStatusEnum.PAID.value for order in response.json())

    response = await client.get(f"/api/v1/theater/admin/orders/?user_id={seed_user_movie_cart.id}")
    assert response.status_code == 200

    response = await client.get(f"/api/v1/theater/admin/orders/?from_date={now.date().isoformat()}")
    assert response.status_code == 200

    response = await client.get(
        f"/api/v1/theater/admin/orders/?to_date={(now + timedelta(days=1)).date().isoformat()}"
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_orders_with_invalid_status(client, admin_override):
    response = await client.get("/api/v1/theater/admin/orders/?status=INVALID")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_orders_filter_from_date_only(client, db_session, seed_user_movie_cart, admin_override):
    now = datetime.utcnow()
    await create_order(db_session, seed_user_movie_cart.id, OrderStatusEnum.PAID, 99.99, created_at=now)

    response = await client.get(f"/api/v1/theater/admin/orders/?from_date={now.date().isoformat()}")
    assert response.status_code == 200
    assert len(response.json()) >= 1
