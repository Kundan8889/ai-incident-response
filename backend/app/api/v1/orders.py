from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.order import OrderCreateRequest, OrderListResponse, OrderResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    request: Request,
    order_in: OrderCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    return await OrderService.create_order(db, order_in, background_tasks, request)

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    return await OrderService.get_order_by_id(db, order_id, request)

@router.get("", response_model=OrderListResponse)
async def list_orders(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> OrderListResponse:
    orders = await OrderService.list_orders(db, limit, offset)
    return OrderListResponse(total=len(orders), orders=orders)
