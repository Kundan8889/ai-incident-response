import asyncio
import json
from typing import List, Optional
from fastapi import BackgroundTasks, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.logging import logger
from app.models.order import Order
from app.schemas.order import OrderCreateRequest, OrderResponse
from app.schemas.payment import PaymentCreateRequest
from app.services.incident_simulator import simulator
from app.services.payment_service import PaymentService


async def process_background_tasks(order_id: str, is_failure_active: bool):
    await asyncio.sleep(0.1)
    if is_failure_active:
        logger.error(
            f"[SIMULATION: background_job_failure] Background worker crashed processing order {order_id}",
            extra={"service": "worker-service", "extra": {
                "scenario": "background_job_failure",
                "task": "dispatch_webhook_and_receipt",
                "order_id": order_id,
                "exception": "WorkerConnectionResetError: Worker lost Redis/Celery queue heartbeat",
            }}
        )
    else:
        logger.info(
            f"[BackgroundWorker] Successfully dispatched order confirmation receipt for order {order_id}",
            extra={"service": "worker-service", "extra": {"order_id": order_id, "status": "COMPLETED"}}
        )


class OrderService:
    @staticmethod
    async def create_order(
        db: AsyncSession,
        request_data: OrderCreateRequest,
        background_tasks: BackgroundTasks,
        http_request: Optional[Request] = None
    ) -> OrderResponse:
        logger.info(
            f"[OrderService] Creating order for customer {request_data.customer_id} with {len(request_data.items)} items",
            extra={"service": "order-service", "extra": {"customer_id": request_data.customer_id, "item_count": len(request_data.items)}}
        )

        await simulator.check_slow_api(http_request)
        await simulator.check_db_timeout(http_request)

        total_amount = sum(item.price * item.quantity for item in request_data.items)
        items_payload = [item.model_dump() for item in request_data.items]

        order = Order(
            customer_id=request_data.customer_id,
            amount=round(total_amount, 2),
            currency=request_data.currency,
            status="PENDING",
            items_json=json.dumps(items_payload),
            error_message=None
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)

        logger.info(f"[OrderService] Order created with ID {order.id}, total amount: {order.amount} {order.currency}")

        if request_data.auto_pay:
            try:
                payment_req = PaymentCreateRequest(
                    order_id=order.id,
                    amount=order.amount,
                    currency=order.currency
                )
                payment = await PaymentService.process_payment(db, payment_req, http_request)
                order.status = "PAID"
                order.error_message = None
                await db.commit()
                await db.refresh(order)

            except HTTPException as exc:
                order.status = "FAILED"
                order.error_message = str(exc.detail)
                await db.commit()
                await db.refresh(order)
                raise exc

        bg_failure_active = simulator.is_background_failure_active(http_request)
        background_tasks.add_task(process_background_tasks, order.id, bg_failure_active)

        return OrderResponse(
            id=order.id,
            customer_id=order.customer_id,
            amount=order.amount,
            currency=order.currency,
            status=order.status,
            items=json.loads(order.items_json),
            error_message=order.error_message,
            created_at=order.created_at,
            updated_at=order.updated_at
        )

    @staticmethod
    async def get_order_by_id(db: AsyncSession, order_id: str, http_request: Optional[Request] = None) -> OrderResponse:
        await simulator.check_slow_api(http_request)
        await simulator.check_db_timeout(http_request)

        stmt = select(Order).where(Order.id == order_id).options(selectinload(Order.payments))
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            logger.warning(f"[OrderService] Order with ID {order_id} not found", extra={"extra": {"order_id": order_id}})
            raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found")

        return OrderResponse(
            id=order.id,
            customer_id=order.customer_id,
            amount=order.amount,
            currency=order.currency,
            status=order.status,
            items=json.loads(order.items_json),
            error_message=order.error_message,
            created_at=order.created_at,
            updated_at=order.updated_at
        )

    @staticmethod
    async def list_orders(db: AsyncSession, limit: int = 50, offset: int = 0) -> List[OrderResponse]:
        stmt = select(Order).order_by(Order.created_at.desc()).offset(offset).limit(limit)
        result = await db.execute(stmt)
        orders = result.scalars().all()

        return [
            OrderResponse(
                id=o.id,
                customer_id=o.customer_id,
                amount=o.amount,
                currency=o.currency,
                status=o.status,
                items=json.loads(o.items_json),
                error_message=o.error_message,
                created_at=o.created_at,
                updated_at=o.updated_at
            )
            for o in orders
        ]
