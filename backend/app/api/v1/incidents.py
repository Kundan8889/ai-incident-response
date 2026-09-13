from fastapi import APIRouter
from app.schemas.incident import IncidentScenarioStatus, IncidentSimulationConfig
from app.services.incident_simulator import simulator

router = APIRouter(prefix="/incidents", tags=["Incident Simulation Controller"])

@router.get("/config", response_model=IncidentScenarioStatus)
async def get_incident_config() -> IncidentScenarioStatus:
    return IncidentScenarioStatus(active_scenarios=simulator.get_state())

@router.post("/config", response_model=IncidentScenarioStatus)
async def update_incident_config(config: IncidentSimulationConfig) -> IncidentScenarioStatus:
    updated = simulator.update_state(config)
    return IncidentScenarioStatus(active_scenarios=updated)

@router.post("/reset", response_model=IncidentScenarioStatus)
async def reset_incident_config() -> IncidentScenarioStatus:
    reset_state = simulator.reset_state()
    return IncidentScenarioStatus(active_scenarios=reset_state)
