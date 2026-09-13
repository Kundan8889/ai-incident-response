from typing import Optional
from pydantic import BaseModel, Field

class IncidentSimulationConfig(BaseModel):
    simulate_db_timeout: bool = Field(default=False, description='Simulate database timeout/lock contention')
    simulate_payment_failure: bool = Field(default=False, description='Simulate downstream payment service 502/503 error')
    simulate_slow_api: bool = Field(default=False, description='Inject latency in order/payment endpoints')
    simulate_slow_api_latency_ms: int = Field(default=3000, description='Injected latency in milliseconds')
    simulate_background_failure: bool = Field(default=False, description='Simulate unhandled background job crash')

class IncidentScenarioStatus(BaseModel):
    active_scenarios: IncidentSimulationConfig
    description: str = 'Controlled deterministic incident simulation controller'
