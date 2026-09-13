import asyncio
import json
from app.core.logging import logger
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.order import Order
from app.models.payment import Payment
from sqlalchemy import select


async def init_and_seed_db():
    logger.info("Creating database tables if not present...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Order).limit(1))
        existing = res.scalar_one_or_none()

        if not existing:
            logger.info("Seeding initial sample orders and payments...")
            sample_order_1 = Order(
                id="ord_seed_101",
                customer_id="cust_enterprise_alpha",
                amount=299.97,
                currency="USD",
                status="PAID",
                items_json=json.dumps([
                    {"sku": "PROD-CLOUD-SVR", "name": "Dedicated Cloud Node", "quantity": 3, "price": 99.99}
                ]),
                error_message=None
            )
            sample_payment_1 = Payment(
                id="pay_seed_101",
                order_id="ord_seed_101",
                amount=299.97,
                currency="USD",
                status="SUCCESS",
                provider="mock_stripe",
                transaction_id="txn_seed_live_89102"
            )

            sample_order_2 = Order(
                id="ord_seed_102",
                customer_id="cust_retail_beta",
                amount=45.00,
                currency="USD",
                status="FAILED",
                items_json=json.dumps([
                    {"sku": "PROD-API-PACK", "name": "Monthly API Tier", "quantity": 1, "price": 45.00}
                ]),
                error_message="Downstream payment provider unreachable (502 Bad Gateway)"
            )
            sample_payment_2 = Payment(
                id="pay_seed_102",
                order_id="ord_seed_102",
                amount=45.00,
                currency="USD",
                status="FAILED",
                provider="mock_stripe",
                error_message="PaymentGatewayError: 502 Bad Gateway"
            )

            session.add_all([sample_order_1, sample_payment_1, sample_order_2, sample_payment_2])
            await session.commit()
            logger.info("Sample seed data committed successfully.")
        else:
            logger.info("Database already contains records. Skipping seed.")

    await engine.dispose()
    logger.info("Database initialization completed.")


if __name__ == "__main__":
    asyncio.run(init_and_seed_db())
