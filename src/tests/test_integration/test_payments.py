import pytest
import json
from decimal import Decimal
from unittest.mock import patch

from sqlalchemy import select

from database.models.orders import OrderModel, OrderItem, OrderStatusEnum
from database.models.payments import Payment, PaymentStatusEnum
from database.models.movies import MovieModel


async def create_order_without_payment(db_session, user, movie):
    order_total_amount = Decimal(str(movie.price))
    order = OrderModel(user_id=user.id, total_amount=order_total_amount, status=OrderStatusEnum.PENDING)
    db_session.add(order)
    await db_session.flush()

    order_item = OrderItem(order_id=order.id, movie_id=movie.id, price_at_order=order_total_amount)
    db_session.add(order_item)
    await db_session.commit()

    return order


async def create_order_with_payment(db_session, user, movie, payment_status=PaymentStatusEnum.PENDING):
    order = await create_order_without_payment(db_session, user, movie)
    order_total_amount = Decimal(str(movie.price))

    payment = Payment(
        order_id=order.id,
        user_id=user.id,
        amount=order_total_amount,
        status=payment_status,
        stripe_payment_intent_id="pi_test",
    )
    db_session.add(payment)
    await db_session.commit()

    return order, payment


@pytest.mark.asyncio
async def test_list_my_orders_unauthorized(client):
    response = await client.get("/api/v1/theater/payments/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authorization header is missing"


@pytest.mark.asyncio
async def test_create_payment_session_success(client, db_session, auth_headers, seed_user_movie_cart):
    user = seed_user_movie_cart
    movie = await db_session.scalar(select(MovieModel).where(MovieModel.id == 1))
    order = await create_order_without_payment(db_session, user, movie)

    response = await client.post(f"/api/v1/theater/create-session/{order.id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "payment_id" in data
    assert data["checkout_url"].rstrip("/") == "https://test-checkout-session.url"
    assert data["status"] == PaymentStatusEnum.PENDING.value

    payment = await db_session.scalar(select(Payment).where(Payment.order_id == order.id))
    assert Decimal(str(payment.amount)) == Decimal(str(movie.price))
    assert payment.stripe_payment_intent_id == "pi_test"


@pytest.mark.asyncio
async def test_create_payment_order_not_found(client, auth_headers):
    response = await client.post("/api/v1/theater/create-session/999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


@pytest.mark.asyncio
async def test_create_payment_session_already_exists(client, db_session, auth_headers, seed_user_movie_cart):
    user = seed_user_movie_cart
    movie = await db_session.scalar(select(MovieModel).where(MovieModel.id == 1))

    order, payment = await create_order_with_payment(db_session, user, movie)

    response = await client.post(f"/api/v1/theater/create-session/{order.id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["payment_id"] == payment.id


@pytest.mark.asyncio
async def test_create_payment_session_forbidden_for_other_user(client, db_session, auth_headers, another_user):
    movie = await db_session.scalar(select(MovieModel).where(MovieModel.id == 1))
    order = await create_order_without_payment(db_session, another_user, movie)

    response = await client.post(f"/api/v1/theater/create-session/{order.id}", headers=auth_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "You can pay only for your orders"


@pytest.mark.asyncio
async def test_create_payment_session_total_mismatch(client, db_session, auth_headers, seed_user_movie_cart):
    user = seed_user_movie_cart
    movie = await db_session.scalar(select(MovieModel).where(MovieModel.id == 1))
    order = await create_order_without_payment(db_session, user, movie)

    # симулюємо зміну ціни
    movie.price = float(Decimal(str(movie.price)) + Decimal("10.00"))
    db_session.add(movie)
    await db_session.commit()

    response = await client.post(f"/api/v1/theater/create-session/{order.id}", headers=auth_headers)
    assert response.status_code == 409
    assert response.json()["detail"] == "Order total has changed. Please try again."


@pytest.mark.asyncio
async def test_webhook_checkout_session_completed(client, db_session, seed_user_movie_cart):
    user = seed_user_movie_cart
    movie = await db_session.scalar(select(MovieModel).where(MovieModel.id == 1))
    order, payment = await create_order_with_payment(db_session, user, movie)

    event_payload = {
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"payment_id": str(payment.id)}}},
    }

    with patch("stripe.Webhook.construct_event", return_value=event_payload):
        response = await client.post(
            "/api/v1/theater/webhook",
            data=json.dumps(event_payload),
            headers={"stripe-signature": "dummy-signature"},
        )
        assert response.status_code == 200

        await db_session.refresh(payment)
        await db_session.refresh(order)

        assert payment.status == PaymentStatusEnum.SUCCESSFUL
        assert order.status == OrderStatusEnum.PAID


@pytest.mark.asyncio
async def test_webhook_checkout_session_expired(client, db_session, seed_user_movie_cart):
    user = seed_user_movie_cart
    movie = await db_session.scalar(select(MovieModel).where(MovieModel.id == 1))
    order, payment = await create_order_with_payment(db_session, user, movie)

    event_payload = {
        "type": "checkout.session.expired",
        "data": {"object": {"metadata": {"payment_id": str(payment.id)}}},
    }

    with patch("stripe.Webhook.construct_event", return_value=event_payload):
        response = await client.post(
            "/api/v1/theater/webhook",
            data=json.dumps(event_payload),
            headers={"stripe-signature": "dummy-signature"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"

        await db_session.refresh(payment)
        assert payment.status == PaymentStatusEnum.CANCELED


@pytest.mark.asyncio
async def test_webhook_completed_payment_not_found(client):
    fake_payment_id = 999

    event_payload = {
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"payment_id": str(fake_payment_id)}}},
    }

    with patch("stripe.Webhook.construct_event", return_value=event_payload):
        response = await client.post(
            "/api/v1/theater/webhook",
            data=json.dumps(event_payload),
            headers={"stripe-signature": "dummy-signature"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"


@pytest.mark.asyncio
async def test_webhook_invalid_signature(client):
    invalid_signature = "invalid-signature"

    with patch("stripe.Webhook.construct_event", side_effect=Exception("Invalid signature")):
        response = await client.post(
            "/api/v1/theater/webhook",
            data="{}",
            headers={"stripe-signature": invalid_signature},
        )

        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]
