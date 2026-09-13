from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class PaymentCreateRequest(BaseModel):
    order_id: str = Field(..., example='ord_123456')
    amount: Optional[float] = Field(None, gt=0, example=99.98)
    currency: str = Field(default='USD', example='USD')
    payment_method: str = Field(default='card', example='card')

class PaymentResponse(BaseModel):
    id: str
    order_id: str
    amount: float
    currency: str
    status: str
    provider: str
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
