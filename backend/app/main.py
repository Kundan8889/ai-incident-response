from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from app.api.v1.incidents import router as incidents_router
from app.api.v1.orders import router as orders_router
from app.api.v1.payments import router as payments_router
from app.core.config import settings
from app.core.logging import logger
from app.core.middleware import RequestTracingMiddleware
from app.core.telemetry import setup_telemetry
from app.db.base import Base
from app.db.session import engine

# Custom Prometheus Incident Counters
incident_simulation_counter = Counter(
    "simulated_incidents_total",
    "Total count of simulated incident scenarios triggered",
    ["scenario"]
)

# Standard HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests processed by endpoint and status code",
    ["method", "path", "status_code"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)


class HealthResponse(BaseModel):
    status: str
    project: str
    environment: str
    observability: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database connection and tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema verified.")
    yield
    logger.info("Closing database engine connections...")
    await engine.dispose()
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# OpenTelemetry Tracing Setup
setup_telemetry(app, engine)

# Prometheus Instrumentator
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health"],
    inprogress_name="http_requests_inprogress",
)
instrumentator.instrument(app)

# Attach Request Tracing & Metrics Middleware
app.add_middleware(RequestTracingMiddleware)

# Attach CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach API Routers
app.include_router(orders_router, prefix="/api")
app.include_router(payments_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")

app.include_router(orders_router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(payments_router, prefix=f"{settings.API_V1_PREFIX}")
app.include_router(incidents_router, prefix=f"{settings.API_V1_PREFIX}")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        project=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        observability={
            "metrics": "/metrics",
            "tracing": "OpenTelemetry enabled",
            "database": "PostgreSQL (instrumented)"
        }
    )


@app.get("/metrics", tags=["Observability"])
def metrics() -> Response:
    """Exposes Prometheus metrics for scraping."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
