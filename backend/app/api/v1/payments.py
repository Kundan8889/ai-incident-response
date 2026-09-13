from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.payment import Payment
from app.schemas.payment import PaymentCreateRequest, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("", response_model=PaymentResponse, status_code=201)
async def process_payment(
    request: Request,
    payment_in: PaymentCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> PaymentResponse:
    payment = await PaymentService.process_payment(db, payment_in, request)
    return PaymentResponse.model_validate(payment)

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db)
) -> PaymentResponse:
    stmt = select(Payment).where(Payment.id == payment_id)
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail=f"Payment '{payment_id}' not found")
    return PaymentResponse.model_validate(payment)
