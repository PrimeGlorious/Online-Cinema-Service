from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import stripe
import os

from starlette.responses import JSONResponse

from config import get_current_user
from config.dependencies import require_admin
from database import get_db, UserModel
from database.models.orders import OrderModel, OrderItem, OrderStatusEnum
from database.models.payments import Payment, PaymentStatusEnum
from schemas.payments import (
    StripePaymentResponseSchema,
    PaymentReadSchema,
    PaymentReadAdminSchema,
)

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@router.post("/create-session/{order_id}", response_model=StripePaymentResponseSchema)
async def create_payment_session(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> StripePaymentResponseSchema:
    result = await db.execute(
        select(OrderModel)
        .options(selectinload(OrderModel.items).selectinload(OrderItem.movie))
        .where(OrderModel.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can pay only for your orders")

    actual_total = sum(item.movie.price for item in order.items)
    if actual_total != order.total_amount:
        raise HTTPException(
            status_code=409, detail="Order total has changed. Please try again."
        )

    result = await db.execute(select(Payment).where(Payment.order_id == order_id))
    existing_payment = result.scalar_one_or_none()

    if existing_payment:
        session = stripe.checkout.Session.retrieve(
            existing_payment.stripe_payment_intent_id
        )
        return StripePaymentResponseSchema(
            payment_id=existing_payment.id,
            checkout_url=session.url,
            status=existing_payment.status,
        )

    payment = Payment(
        order_id=order.id,
        amount=order.total_amount,
        currency="usd",
        status=PaymentStatusEnum.PENDING,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": ", ".join([item.movie.name for item in order.items])
                    },
                    "unit_amount": int(order.total_amount * 100),
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        metadata={"payment_id": str(payment.id)},
        success_url="http://localhost:8000/payments/success",
        cancel_url="http://localhost:8000/payments/cancel",
    )

    payment.stripe_payment_intent_id = session.payment_intent
    await db.commit()

    return StripePaymentResponseSchema(
        payment_id=payment.id, checkout_url=session.url, status=payment.status
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, endpoint_secret
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        payment_id = int(session["metadata"]["payment_id"])

        result = await db.execute(
            select(Payment)
            .options(selectinload(Payment.order))
            .where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = PaymentStatusEnum.SUCCESSFUL
            payment.order.status = OrderStatusEnum.PAID
            await db.commit()

    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        payment_id = int(session["metadata"]["payment_id"])

        result = await db.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()

        if payment and payment.status == PaymentStatusEnum.PENDING:
            payment.status = PaymentStatusEnum.CANCELED
            await db.commit()

    return {"status": "success"}


@router.get(
    "/admin/payments/",
    response_model=List[PaymentReadSchema],
    summary="Admin: List all payments with filters",
)
async def list_all_orders(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
    status: Optional[PaymentStatusEnum] = Query(None),
    user_id: Optional[int] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
) -> List[PaymentReadAdminSchema]:
    stmt = select(Payment).options(selectinload(Payment.order))

    if status:
        stmt = stmt.where(Payment.status == status)
    if user_id:
        stmt = stmt.where(Payment.user_id == user_id)
    if from_date:
        stmt = stmt.where(Payment.created_at >= from_date)
    if to_date:
        stmt = stmt.where(Payment.created_at <= to_date)

    result = await db.execute(stmt)
    payments = result.scalars().all()
    return [PaymentReadAdminSchema.model_validate(payment) for payment in payments]


@router.get(
    "/payments/",
    response_model=List[PaymentReadSchema],
    summary="List user's own payments",
)
async def list_my_orders(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    status: Optional[PaymentStatusEnum] = None,
) -> List[PaymentReadSchema]:
    stmt = (
        select(Payment)
        .options(selectinload(Payment.order))
        .where(Payment.user_id == current_user.id)
    )

    if status:
        stmt = stmt.where(Payment.status == status)

    result = await db.execute(stmt)
    payments = result.scalars().all()
    return [PaymentReadSchema.model_validate(payment) for payment in payments]


@router.get("/payments/success", summary="Stripe success redirect")
async def payment_success():
    return JSONResponse(
        content={"status": "success", "message": "Payment completed successfully."}
    )


@router.get("/payments/cancel", summary="Stripe cancel redirect")
async def payment_cancel():
    return JSONResponse(
        content={"status": "cancelled", "message": "Payment was canceled or failed."}
    )
