import uuid
from typing import Optional
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models.payment import Payment
from app.schemas.payment import PaymentCreateRequest, PaymentResponse
from app.services.incident_simulator import simulator


class PaymentService:
    @staticmethod
    async def process_payment(
        db: AsyncSession,
        request_data: PaymentCreateRequest,
        http_request: Optional[Request] = None
    ) -> Payment:
        logger.info(
            f"[PaymentService] Initiating payment for order {request_data.order_id} of amount {request_data.amount} {request_data.currency}",
            extra={"service": "payment-service", "extra": {"order_id": request_data.order_id, "amount": request_data.amount}}
        )

        await simulator.check_slow_api(http_request)

        if simulator.is_payment_failure_active(http_request):
            logger.error(
                f"[SIMULATION: payment_failure] Upstream payment gateway error for order {request_data.order_id} (Provider: mock_stripe)",
                extra={"service": "payment-service", "extra": {
                    "scenario": "payment_failure",
                    "provider": "mock_stripe",
                    "http_status": 502,
                    "provider_error_code": "GATEWAY_TIMEOUT_UPSTREAM",
                    "message": "Upstream bank authorization endpoint unreachable"
                }}
            )

            failed_payment = Payment(
                order_id=request_data.order_id,
                amount=request_data.amount or 0.0,
                currency=request_data.currency,
                status="FAILED",
                provider="mock_stripe",
                error_message="Simulated payment failure: Upstream payment gateway unreachable (502 Bad Gateway)"
            )
            db.add(failed_payment)
            await db.commit()
            await db.refresh(failed_payment)

            raise HTTPException(
                status_code=502,
                detail={
                    "error": "PaymentGatewayError",
                    "message": "Downstream payment processor failed to authorize payment transaction.",
                    "payment_id": failed_payment.id,
                    "code": "PAYMENT_GATEWAY_502",
                    "simulation": True
                }
            )

        transaction_id = "txn_" + uuid.uuid4().hex[:16]
        payment = Payment(
            order_id=request_data.order_id,
            amount=request_data.amount or 0.0,
            currency=request_data.currency,
            status="SUCCESS",
            provider="mock_stripe",
            transaction_id=transaction_id,
            error_message=None
        )
        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        logger.info(
            f"[PaymentService] Payment successful: payment_id={payment.id}, transaction_id={transaction_id}",
            extra={"service": "payment-service", "extra": {"payment_id": payment.id, "transaction_id": transaction_id, "status": "SUCCESS"}}
        )

        return payment
