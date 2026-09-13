from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from app.core.config import settings
from app.core.logging import logger

resource = Resource.create(
    attributes={
        "service.name": "ai-incident-response-backend",
        "service.version": "1.0.0",
        "deployment.environment": settings.ENVIRONMENT,
    }
)

tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer("ai-incident-response-tracer", "1.0.0")


def setup_telemetry(app, engine):
    """Instruments FastAPI and SQLAlchemy with OpenTelemetry."""
    logger.info("Configuring OpenTelemetry instrumentation...")
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        excluded_urls="health,metrics,docs,redoc,openapi.json"
    )

    # Instrument SQLAlchemy AsyncEngine
    if hasattr(engine, "sync_engine"):
        SQLAlchemyInstrumentor().instrument(
            engine=engine.sync_engine,
            tracer_provider=tracer_provider
        )

    logger.info("OpenTelemetry instrumentation active.")
