import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from opentelemetry import trace

request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
service_name_ctx: ContextVar[str] = ContextVar("service_name", default="incident-platform")


def get_request_id() -> Optional[str]:
    return request_id_ctx.get()


def set_request_id(request_id: str) -> None:
    request_id_ctx.set(request_id)


def set_service_name(name: str) -> None:
    service_name_ctx.set(name)


class JSONFormatter(logging.Formatter):
    """Structured JSON Log Formatter with request context and OpenTelemetry trace correlation."""

    def format(self, record: logging.LogRecord) -> str:
        # Extract OpenTelemetry trace and span IDs if active
        trace_id = None
        span_id = None
        try:
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                span_ctx = current_span.get_span_context()
                if span_ctx.is_valid:
                    trace_id = format(span_ctx.trace_id, "032x")
                    span_id = format(span_ctx.span_id, "016x")
        except Exception:
            pass

        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id() or getattr(record, "request_id", None),
            "trace_id": trace_id,
            "span_id": span_id,
            "service": getattr(record, "service", service_name_ctx.get()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include custom extra fields if passed
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            log_obj["extra"] = extra

        # Include exception info if available
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False

    return logging.getLogger("app")


logger = setup_logging()
