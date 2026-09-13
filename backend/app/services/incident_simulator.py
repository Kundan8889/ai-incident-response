import asyncio
from typing import Optional
from fastapi import HTTPException, Request
from app.core.config import settings
from app.core.logging import logger
from app.schemas.incident import IncidentSimulationConfig


class IncidentSimulator:
    def __init__(self):
        self.state = IncidentSimulationConfig(
            simulate_db_timeout=settings.SIMULATE_DB_TIMEOUT,
            simulate_payment_failure=settings.SIMULATE_PAYMENT_FAILURE,
            simulate_slow_api=settings.SIMULATE_SLOW_API,
            simulate_slow_api_latency_ms=settings.SIMULATE_SLOW_API_LATENCY_MS,
            simulate_background_failure=settings.SIMULATE_BACKGROUND_FAILURE,
        )

    def get_state(self) -> IncidentSimulationConfig:
        return self.state

    def update_state(self, new_config: IncidentSimulationConfig) -> IncidentSimulationConfig:
        self.state = new_config
        logger.warning(
            f"Incident simulation state updated: {self.state.model_dump()}",
            extra={"extra": {"incident_config": self.state.model_dump()}}
        )
        return self.state

    def reset_state(self) -> IncidentSimulationConfig:
        self.state = IncidentSimulationConfig()
        logger.info("Incident simulation state reset to default normal operation.")
        return self.state

    async def check_slow_api(self, request: Optional[Request] = None):
        should_delay = self.state.simulate_slow_api
        delay_ms = self.state.simulate_slow_api_latency_ms

        if request:
            header_scenario = request.headers.get("X-Simulate-Incident")
            if header_scenario == "slow_api":
                should_delay = True
            header_delay = request.headers.get("X-Simulate-Latency-Ms")
            if header_delay and header_delay.isdigit():
                delay_ms = int(header_delay)
                should_delay = True

        if should_delay:
            logger.warning(
                f"[SIMULATION: slow_api] Injected artificial latency of {delay_ms}ms",
                extra={"extra": {"scenario": "slow_api", "latency_ms": delay_ms}}
            )
            await asyncio.sleep(delay_ms / 1000.0)

    async def check_db_timeout(self, request: Optional[Request] = None):
        should_timeout = self.state.simulate_db_timeout

        if request:
            header_scenario = request.headers.get("X-Simulate-Incident")
            if header_scenario in ("db_timeout", "database_timeout"):
                should_timeout = True

        if should_timeout:
            logger.error(
                "[SIMULATION: db_timeout] Database connection lock contention / Query execution timed out after 5000ms",
                extra={"extra": {
                    "scenario": "db_timeout",
                    "error_code": "DB_CONNECTION_TIMEOUT",
                    "driver_error": "asyncpg.exceptions.QueryCanceledError: canceling statement due to user request or lock timeout"
                }}
            )
            raise HTTPException(
                status_code=504,
                detail={
                    "error": "DatabaseTimeoutError",
                    "message": "Database query timed out waiting for connection pool lock.",
                    "code": "DB_504_TIMEOUT",
                    "simulation": True
                }
            )

    def is_payment_failure_active(self, request: Optional[Request] = None) -> bool:
        if request:
            header_scenario = request.headers.get("X-Simulate-Incident")
            if header_scenario in ("payment_failure", "payment_service_failure"):
                return True
        return self.state.simulate_payment_failure

    def is_background_failure_active(self, request: Optional[Request] = None) -> bool:
        if request:
            header_scenario = request.headers.get("X-Simulate-Incident")
            if header_scenario in ("background_failure", "job_failure"):
                return True
        return self.state.simulate_background_failure


simulator = IncidentSimulator()
