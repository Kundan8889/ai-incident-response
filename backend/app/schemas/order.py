from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class OrderItem(BaseModel):
    sku: str = Field(..., example='ITEM-A100')
    name: str = Field(..., example='Cloud Compute Unit')
    quantity: int = Field(..., gt=0, example=2)
    price: float = Field(..., gt=0, example=49.99)

class OrderCreateRequest(BaseModel):
    customer_id: str = Field(..., example='cust_1001')
    items: List[OrderItem] = Field(..., min_length=1)
    currency: str = Field(default='USD', example='USD')
    auto_pay: bool = Field(default=True, description='Automatically process payment after order creation')

class OrderResponse(BaseModel):
    id: str
    customer_id: str
    amount: float
    currency: str
    status: str
    items: List[Dict[str, Any]]
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    total: int
    orders: List[OrderResponse]
