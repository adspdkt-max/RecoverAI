# RecoverAI — Backend Service

The backend of RecoverAI is a high-performance Python FastAPI service providing explainable risk analysis, deterministic recovery strategy recommendation, bounded recovery attempt execution, idempotent payment webhook handling, and real-time database-driven analytics.

## Tech Stack
- **Python 3.10+**
- **FastAPI**: Modern, high-performance async REST API framework.
- **SQLAlchemy 2.0**: Robust ORM with type annotations and relation mapping.
- **Pydantic v2**: Strict schema validation and data serialization.
- **SQLite**: Zero-configuration embedded database for local execution.
- **Pytest & HTTPX**: Automated test suite for unit, integration, and guardrail validation.

## Directory Structure
```
backend/
├── app/
│   ├── main.py                    # FastAPI app initialization, middleware, lifespan, static mounting
│   ├── config.py                  # Environment config and database path resolution
│   ├── api/
│   │   ├── router.py              # Central API router mounting all sub-routes
│   │   ├── health.py              # GET /api/health (System status)
│   │   ├── payments.py            # POST /api/payments/events, GET /api/payments, GET /api/payments/{id}
│   │   ├── risk.py                # POST /api/risk/analyze, GET /api/risk/factors
│   │   ├── recovery.py            # POST /api/recovery/decide, POST /api/recovery/execute, GET /api/recovery/attempts
│   │   ├── webhooks.py            # POST /api/webhooks/payment (Idempotent provider webhook handler)
│   │   ├── dashboard.py           # GET /api/dashboard/summary (Real-time DB-calculated KPIs)
│   │   ├── analytics.py           # GET /api/analytics/summary, /analytics/recovery, /analytics/risk
│   │   ├── customers.py           # GET /api/customers, GET /api/customers/{id}
│   │   ├── audit.py               # GET /api/audit (Chronological immutable audit log)
│   │   └── seed.py                # POST /api/seed, POST /api/seed/clear
│   │
│   ├── models/
│   │   ├── base.py                # DeclarativeBase definition
│   │   ├── payment.py             # Payment transaction entity & statuses
│   │   ├── recovery.py            # RecoveryAttempt entity & intervention types
│   │   ├── webhook.py             # WebhookEvent entity (idempotency ledger)
│   │   └── audit.py               # AuditLog entity
│   │
│   ├── schemas/                   # Pydantic v2 validation models
│   ├── engines/
│   │   ├── risk_engine.py         # Explainable Risk Engine (Rule-based, factor scoring)
│   │   └── recovery_engine.py     # Recovery Decision Engine (Safety bounds, retry limits)
│   │
│   ├── services/
│   │   ├── payment_service.py     # Payment query & ingestion operations
│   │   ├── recovery_executor.py   # Bounded execution & supervisor approval logic
│   │   ├── webhook_service.py     # Idempotent webhook event processor
│   │   ├── analytics_service.py   # Real-time database metrics aggregator
│   │   ├── audit_service.py       # Centralized audit logger
│   │   └── seed_service.py        # Realistic multi-scenario demo data generator
│   │
│   └── db/
│       └── session.py             # Database engine, SessionLocal, get_db dependency
│
├── tests/                         # Comprehensive automated test suite
├── requirements.txt
└── README.md
```

## Running the Backend
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run with Uvicorn
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Running Tests
```bash
pytest -v
```
