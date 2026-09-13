import time
import uuid
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.logging import logger, set_request_id


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Middleware for request correlation ID tracing, OpenTelemetry span correlation, Prometheus metrics, and structured access logging."""

    async def dispatch(self, request: Request, call_next) -> Response:
        from app.main import http_request_duration_seconds, http_requests_total, incident_simulation_counter

        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        set_request_id(request_id)

        incident_header = request.headers.get("X-Simulate-Incident")
        if incident_header:
            try:
                incident_simulation_counter.labels(scenario=incident_header).inc()
            except Exception:
                pass

        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            current_span.set_attribute("http.request_id", request_id)
            if incident_header:
                current_span.set_attribute("incident.simulation_scenario", incident_header)

        start_time = time.perf_counter()

        logger.info(
            f"Incoming {request.method} request to {request.url.path}",
            extra={"extra": {"method": request.method, "path": request.url.path, "client_ip": request.client.host if request.client else None}}
        )

        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            process_time = round((time.perf_counter() - start_time) * 1000, 2)
            duration_sec = time.perf_counter() - start_time
            response.headers["X-Request-ID"] = request_id

            if request.url.path not in ("/metrics", "/health"):
                try:
                    http_requests_total.labels(
                        method=request.method,
                        path=request.url.path,
                        status_code=str(status_code)
                    ).inc()
                    http_request_duration_seconds.labels(
                        method=request.method,
                        path=request.url.path
                    ).observe(duration_sec)
                except Exception:
                    pass

            logger.info(
                f"Completed {request.method} {request.url.path} with status {response.status_code} in {process_time}ms",
                extra={"extra": {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": process_time
                }}
            )
            return response
        except Exception as exc:
            duration_sec = time.perf_counter() - start_time
            process_time = round(duration_sec * 1000, 2)
            if request.url.path not in ("/metrics", "/health"):
                try:
                    http_requests_total.labels(
                        method=request.method,
                        path=request.url.path,
                        status_code="500"
                    ).inc()
                    http_request_duration_seconds.labels(
                        method=request.method,
                        path=request.url.path
                    ).observe(duration_sec)
                except Exception:
                    pass

            logger.error(
                f"Unhandled exception during {request.method} {request.url.path}: {str(exc)}",
                exc_info=True,
                extra={"extra": {"method": request.method, "path": request.url.path, "duration_ms": process_time}}
            )
            raise exc
