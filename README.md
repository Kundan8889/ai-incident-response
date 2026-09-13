# AI Engineering Incident Response & Autonomous Debugging Platform

An intelligent, autonomous platform for real-time engineering incident triage, root cause analysis, automated remediation workflows, and post-mortem generation.

---

## System Architecture (Phase 2: Observability Enabled)

```
ai-incident-response/
??? backend/
?   ??? app/
?   ?   ??? api/v1/
?   ?   ?   ??? orders.py              # POST /api/orders, GET /api/orders/{id}, GET /api/orders
?   ?   ?   ??? payments.py            # POST /api/payments, GET /api/payments/{id}
?   ?   ?   ??? incidents.py           # GET/POST /api/incidents/config, POST /api/incidents/reset
?   ?   ??? core/
?   ?   ?   ??? config.py              # Pydantic Settings & DB configuration
?   ?   ?   ??? logging.py             # Structured JSON logger with trace_id & request_id
?   ?   ?   ??? middleware.py          # RequestID tracing, span correlation & Prometheus metrics
?   ?   ?   ??? telemetry.py           # OpenTelemetry TracerProvider & instrumentation
?   ?   ??? db/
?   ?   ?   ??? base.py                # DeclarativeBase
?   ?   ?   ??? session.py             # SQLAlchemy 2.0 asyncpg engine with connection pooling
?   ?   ??? models/
?   ?   ?   ??? order.py               # Order table model (DateTime with timezone)
?   ?   ?   ??? payment.py             # Payment table model
?   ?   ??? schemas/
?   ?   ?   ??? order.py               # Pydantic models for Orders
?   ?   ?   ??? payment.py             # Pydantic models for Payments
?   ?   ?   ??? incident.py            # Pydantic models for Incident Simulation
?   ?   ??? services/
?   ?   ?   ??? order_service.py       # Order lifecycle management
?   ?   ?   ??? payment_service.py     # Payment processing & mock provider
?   ?   ?   ??? incident_simulator.py  # Controlled deterministic incident injectors
?   ?   ??? main.py                    # FastAPI application, lifespan & /metrics endpoint
?   ??? scripts/
?   ?   ??? init_db.py                 # DB schema initialization & seed data
?   ?   ??? simulate_scenarios.py      # End-to-end scenario & metrics test runner
?   ??? requirements.txt
?   ??? .env.example
??? infrastructure/
?   ??? docker-compose.yml             # Prometheus & Grafana stack
?   ??? prometheus/
?   ?   ??? prometheus.yml             # Scrape config for FastAPI backend
?   ??? grafana/
?       ??? provisioning/
?       ?   ??? datasources/           # Auto-provisioned Prometheus datasource
?       ?   ??? dashboards/            # Auto-provisioned dashboard loader
?       ??? dashboards/
?           ??? incident_response_overview.json
??? frontend/                          # Next.js App Router, Tailwind CSS, TypeScript
??? docs/
?   ??? architecture.md
??? .gitignore
??? README.md
```

---

## Observability Stack Overview

| Tool | Purpose | Port / URL |
| :--- | :--- | :--- |
| **OpenTelemetry** | Distributed tracing across FastAPI endpoints and SQLAlchemy database queries | In-process (`trace_id` in logs & spans) |
| **Prometheus** | Metrics scraper and time-series database | `http://localhost:9090` |
| **Grafana** | Visual dashboard for QPS, latency quantiles, error rate, and incident distribution | `http://localhost:3001` (admin / admin) |
| **FastAPI Metrics** | Prometheus metrics exposition endpoint | `http://localhost:8000/metrics` |

---

## Database Schema (PostgreSQL 18)

- **`orders` Table**: `id` (PK, `ord_...`), `customer_id` (Indexed), `amount`, `currency`, `status` (`PENDING`, `PAID`, `FAILED`), `items_json`, `error_message`, `created_at` (TIMESTAMPTZ), `updated_at` (TIMESTAMPTZ).
- **`payments` Table**: `id` (PK, `pay_...`), `order_id` (FK -> `orders.id`, Indexed), `amount`, `currency`, `status` (`SUCCESS`, `FAILED`), `provider`, `transaction_id`, `error_message`, `created_at` (TIMESTAMPTZ), `updated_at` (TIMESTAMPTZ).

---

## Controlled Incident Scenarios

All scenarios are **100% deterministic** and can be triggered via headers or `/api/incidents/config`:

| Scenario | Header Trigger | Status Code | Metrics & Trace Impact |
| :--- | :--- | :--- | :--- |
| **Normal Flow** | Default headers | `201 Created` | Increments `http_requests_total{status="201"}`, records latency. |
| **Payment Failure** | `X-Simulate-Incident: payment_failure` | `502 Bad Gateway` | Increments `http_requests_total{status="502"}`, records `simulated_incidents_total{scenario="payment_failure"}`. |
| **Database Timeout**| `X-Simulate-Incident: db_timeout` | `504 Gateway Timeout` | Increments `http_requests_total{status="504"}`, records `simulated_incidents_total{scenario="db_timeout"}`. |
| **Slow API Latency**| `X-Simulate-Incident: slow_api` | `201 Created` (Delayed) | Extends `http_request_duration_seconds` bucket observations. |
| **Background Failure**| `X-Simulate-Incident: background_failure` | `201 Created` | Order succeeds; async worker logs error with active `trace_id`. |

---

## How to Run Everything

### 1. Start the Observability Stack (Prometheus + Grafana)
```bash
cd infrastructure
docker compose up -d
```
- Prometheus: [http://localhost:9090](http://localhost:9090)
- Grafana: [http://localhost:3001](http://localhost:3001) (Credentials: `admin` / `admin`)

### 2. Start the FastAPI Backend
```bash
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
python -m scripts.init_db
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Run Automated Tests and Verify Observability
```bash
python -m scripts.simulate_scenarios
```

### 4. Verify Metrics and Telemetry
- Open [http://localhost:8000/metrics](http://localhost:8000/metrics) to inspect raw Prometheus metrics.
- Open [http://localhost:3001/d/incident-response-overview](http://localhost:3001/d/incident-response-overview) in Grafana to view live request rates, latency, and incident counters.
