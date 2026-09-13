# System Architecture & Observability

## 1. System Overview

The **AI Engineering Incident Response & Autonomous Debugging Platform** is designed with a realistic production backend, deterministic failure simulation mechanisms, and a full observability stack.

```
+-------------------------------------------------------------------------+
|                           Client Traffic                                |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                        FastAPI Backend Application                      |
|                                                                         |
|  +------------------------+      +-----------------------------------+  |
|  | Request Tracing (UUID) | <--> | OpenTelemetry TracerProvider       |  |
|  +------------------------+      +-----------------------------------+  |
|               |                                   |                     |
|               v                                   v                     |
|  +------------------------+      +-----------------------------------+  |
|  | Structured JSON Logger |      | Prometheus Instrumentator         |  |
|  | (request_id, trace_id, |      | (/metrics exposition endpoint)    |  |
|  |  span_id, duration_ms) |      +-----------------------------------+  |
|  +------------------------+                        |                    |
|               |                                    |                    |
|               v                                    |                    |
|  +------------------------+                        |                    |
|  | Order & Payment Logic  |                        |                    |
|  +------------------------+                        |                    |
|               |                                    |                    |
|               v                                    |                    |
|  +------------------------+                        |                    |
|  | SQLAlchemy (asyncpg)   |                        |                    |
|  +------------------------+                        |                    |
+----------------------------------------------------|--------------------+
               |                                     |
               v                                     v
+-----------------------------+      +-------------------------------+
|     PostgreSQL Database     |      |      Prometheus Scraper       |
|    (orders, payments)       |      |     (localhost:9090)          |
+-----------------------------+      +-------------------------------+
                                                     |
                                                     v
                                     +-------------------------------+
                                     |       Grafana Dashboard       |
                                     |     (localhost:3001)          |
                                     +-------------------------------+
```

---

## 2. Observability Architecture & Roles

### A. OpenTelemetry (Distributed Tracing)
- **Role**: Automatically captures trace context, spans, and metadata for every incoming HTTP request and database operation.
- **FastAPI Instrumentation**: Automatically creates root spans with HTTP method, route template, client address, and response status.
- **SQLAlchemy Instrumentation**: Attaches child spans for SQL statements, query execution timing, and transaction lifecycles.
- **Correlation**: Injects `http.request_id` into spans and injects active `trace_id` and `span_id` into all structured JSON logs.

### B. Prometheus (Metrics Collection)
- **Role**: Periodically scrapes numerical metrics exposed at `/metrics`.
- **Metrics Collected**:
  - `http_requests_total`: Request counts partitioned by `method`, `path`, and `status_code`.
  - `http_request_duration_seconds`: Histogram of request latencies partitioned across latency buckets.
  - `http_requests_inprogress`: Active in-flight requests.
  - `simulated_incidents_total`: Number of controlled incident scenarios triggered (`payment_failure`, `db_timeout`, `slow_api`, `background_failure`).
  - Python runtime & GC statistics.

### C. Grafana (Visualization & Dashboards)
- **Role**: Visualizes time-series metrics queried from Prometheus.
- **Pre-provisioned Dashboard**: `incident_response_overview.json` displaying:
  1. HTTP Request Rate (QPS)
  2. Latency Quantiles (p50, p95, p99)
  3. Error Rate (4xx / 5xx per second)
  4. HTTP Status Code Distribution
  5. Simulated Incident Scenario Triggers

---

## 3. URLs and Port Map

| Component | Host / Port | Description |
| :--- | :--- | :--- |
| **FastAPI Backend** | `http://localhost:8000` | Core API & business logic |
| **Backend Health** | `http://localhost:8000/health` | Health check with observability status |
| **Prometheus Metrics**| `http://localhost:8000/metrics` | Prometheus exposition endpoint |
| **Swagger UI Docs** | `http://localhost:8000/docs` | Interactive OpenAPI documentation |
| **PostgreSQL** | `localhost:5432` | Relational database (`incident_response_db`) |
| **Prometheus UI** | `http://localhost:9090` | Prometheus metric explorer |
| **Grafana UI** | `http://localhost:3001` | Pre-configured dashboard UI (admin / admin) |
| **Next.js Frontend** | `http://localhost:3000` | UI Dashboard |
