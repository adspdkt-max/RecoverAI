# RecoverAI

**RecoverAI** is a professional, AI-powered revenue recovery and payment intelligence platform designed for modern subscription businesses, SaaS platforms, and digital merchants.

RecoverAI analyzes payment failures, evaluates financial risk with an explainable risk engine, determines bounded recovery strategies, executes safe recovery attempts, ingests payment provider webhooks with strict idempotency, and delivers real-time analytics and immutable audit trails.

---

## 1. Core Recovery Workflow

```
[ PAYMENT EVENT ]
       ↓
[ PAYMENT RECORD ]
       ↓
[ EXPLAINABLE RISK ENGINE ]  → (Evaluates failure code, amount tier, attempt velocity, recency)
       ↓
[ RECOVERY DECISION ENGINE ] → (Determines safe bounded strategy: RETRY, PAYMENT LINK, ESCALATE)
       ↓
[ BOUNDED RECOVERY ATTEMPT ] → (Status: PENDING; safety caps & human approval enforced)
       ↓
[ PROVIDER WEBHOOK EVENT ]  → (POST /api/webhooks/payment: Idempotent processing)
       ↓
[ RECOVERY CONFIRMED ]       → (Status: SUCCEEDED; recovered_amount updated)
       ↓
[ REAL-TIME ANALYTICS ]      → (Zero hardcoded metrics; pure DB aggregation)
       ↓
[ IMMUTABLE AUDIT TRAIL ]    → (Full lifecycle provenance)
```

---

## 2. Technology Stack

### Backend
- **Python 3.10+**
- **FastAPI**: Modern, asynchronous web framework with automatic OpenAPI/Swagger documentation.
- **SQLAlchemy 2.0**: Typed ORM for robust database querying and schema migrations.
- **Pydantic v2**: Declarative data validation and strict serialization.
- **SQLite**: Zero-configuration relational database for local development and testing.
- **Pytest**: Automated test suite with 100% pass rate across core lifecycle guardrails.

### Frontend
- **HTML5 & CSS3**: High-end fintech SaaS design system (inspired by Stripe, Linear, and Ramp).
- **Vanilla JavaScript (ES6+)**: Clean, lightweight single-page application (SPA) architecture without heavy framework overhead.
- **Chart.js (v4)**: Modern, responsive canvas charts for time-series and categorical analytics.
- **Inter & JetBrains Mono Fonts**: Crisp typography optimized for tabular financial figures.

---

## 3. Project Structure

```
RecoverAI/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint, middleware, static mounting
│   │   ├── config.py                  # Environment config & database URI resolution
│   │   ├── api/
│   │   │   ├── router.py              # Central API router (/api)
│   │   │   ├── health.py              # GET /api/health (System status & DB health)
│   │   │   ├── payments.py            # POST /api/payments/events, GET /api/payments, GET /api/payments/{id}
│   │   │   ├── risk.py                # POST /api/risk/analyze, GET /api/risk/factors
│   │   │   ├── recovery.py            # POST /api/recovery/decide, POST /api/recovery/execute, GET /api/recovery/attempts
│   │   │   ├── webhooks.py            # POST /api/webhooks/payment (Idempotent webhook gateway)
│   │   │   ├── dashboard.py           # GET /api/dashboard/summary (Real-time DB metrics)
│   │   │   ├── analytics.py           # GET /api/analytics/summary, /analytics/recovery, /analytics/risk
│   │   │   ├── customers.py           # GET /api/customers, GET /api/customers/{id}
│   │   │   ├── audit.py               # GET /api/audit (Paginated audit logs)
│   │   │   └── seed.py                # POST /api/seed, POST /api/seed/clear (Sandbox manager)
│   │   │
│   │   ├── models/
│   │   │   ├── base.py                # SQLAlchemy DeclarativeBase
│   │   │   ├── payment.py             # Payment entity
│   │   │   ├── recovery.py            # RecoveryAttempt entity
│   │   │   ├── webhook.py             # WebhookEvent entity (Idempotency ledger)
│   │   │   └── audit.py               # AuditLog entity
│   │   │
│   │   ├── schemas/                   # Pydantic validation schemas
│   │   ├── engines/
│   │   │   ├── risk_engine.py         # Explainable Risk Engine
│   │   │   └── recovery_engine.py     # Recovery Decision Engine
│   │   │
│   │   ├── services/
│   │   │   ├── payment_service.py     # Payment lifecycle & queries
│   │   │   ├── recovery_executor.py   # Bounded execution & approval guardrails
│   │   │   ├── webhook_service.py     # Webhook idempotency & recovery completion
│   │   │   ├── analytics_service.py   # Database aggregation engine
│   │   │   ├── audit_service.py       # Centralized immutable audit logger
│   │   │   └── seed_service.py        # Realistic multi-scenario demo dataset
│   │   │
│   │   └── db/
│   │       └── session.py             # Database session manager
│   │
│   ├── tests/                         # Pytest automated test suite (21 tests)
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── index.html                     # Semantic SPA structure & modal templates
│   ├── style.css                      # Modern fintech CSS design system
│   ├── script.js                      # Application controller & Chart.js integrations
│   └── assets/
│       └── logo.svg                   # RecoverAI brand SVG
│
└── README.md                          # Master documentation
```

---

## 4. Key Architectural Features

### A. Explainable Risk Engine
Unlike opaque black-box systems, RecoverAI computes deterministic, explainable risk scores (0 to 100) and provides clear justifications for each decision:
1. **Decline Mechanics**: Distinguishes transient issuer glitches (`TEMPORARY_ISSUER_DECLINE`) from invalid credentials (`CUSTOMER_CREDENTIALS_INVALID`) and security flags (`FRAUD_OR_SECURITY`).
2. **Exposure Tiering**: Differentiates micro-transactions (<₹1,000) from high-value enterprise tiers (≥₹25,000).
3. **Attempt Velocity & Fatigue**: Analyzes previous decline counts to prevent merchant chargeback risks.
4. **Aging Decay**: Factors in the elapsed time since the original payment failure.

### B. Recovery Decision Engine & Safety Guardrails
- **Bounded Retries**: Automated retries are hard-capped at 3 attempts. When the limit is reached, the system automatically escalates to `HUMAN_ESCALATION`.
- **High-Value Guardrail**: Transactions ≥ ₹25,000 or those flagged as `CRITICAL` require explicit supervisor approval before any automated charge can proceed.
- **Strict Prohibition of Direct Money Movement**: The Recovery Engine makes strategic decisions and creates bounded attempts in `PENDING` status. Recovery is confirmed only when a valid webhook is received.
- **Prohibition of `NO_ACTION` Execution**: Prevents unexecutable placeholder states from entering the processing pipeline.

### C. Webhook Ingestion & Cryptographic Idempotency
- All incoming webhooks (`POST /api/webhooks/payment`) are recorded in an idempotency ledger (`WebhookEvent`).
- Duplicate deliveries (identical `event_id`) are safely acknowledged without double-processing recovery amounts or altering state.

### D. Zero-Hardcoding Metric Integrity
- When the database is clean, all dashboard cards, charts, and tables display genuine zero/empty states (`—`, `No data available`).
- Real-time aggregation of INR (₹) transactions with authentic localized formatting (`en-IN`).

---

## 5. Getting Started & Installation

### Prerequisites
- Python 3.10 or higher
- Modern web browser (Chrome, Edge, Firefox, Safari)

### 1. Setup Backend
```bash
# Navigate to backend folder
cd backend

# Install dependencies
pip install -r requirements.txt

# Run automated tests
pytest -v
```

### 2. Start the Application
```bash
# Start FastAPI application on port 8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open RecoverAI
- **Frontend Dashboard**: Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
- **Interactive Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 6. End-to-End Demo Walkthrough

Follow these steps to demonstrate the complete revenue recovery workflow:

### Step 1: Clean State Verification
1. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).
2. If previous data exists, click **Settings** → **Wipe All Database Tables**.
3. Verify that the Dashboard displays clean empty states (`—` for KPIs and clear empty state indicators for charts).

### Step 2: Seed Realistic Multi-Scenario Data
1. Click **Seed Demo Data** in the topbar (or via Settings).
2. Observe 12 realistic payments populated across varied Indian Rupee amounts (₹499.00 to ₹78,500.00), realistic customers, and diverse decline categories.
3. Dashboard KPIs and Chart.js visuals immediately render live aggregated INR (₹) metrics.

### Step 3: Inspect a Failed Payment & Run Risk Analysis
1. Navigate to **Payments** in the sidebar.
2. Click **Inspect** on a failed payment (e.g. `pay_sec_991823` or `pay_aut_558291`).
3. View the slide-over drawer showing decline reasons, attempt velocity, and the full event timeline.
4. Open **Risk Intelligence** in the sidebar and enter `pay_sec_991823` → Click **Analyze**.
5. Observe the composite score (`95.0/100`), `CRITICAL` risk tier, `FRAUD_OR_SECURITY` category, and plain-English factor justifications.

### Step 4: Execute a Bounded Recovery Action
1. From the Payment Details drawer or **Recovery Center**, initiate a recovery action.
2. Review the confirmation modal showing the recommended strategy, probability, and enforced guardrails.
3. Click **Create Recovery Attempt**.
4. The attempt appears in the Recovery Center in `PENDING` (or `ESCALATED` if high value) status.

### Step 5: Simulate Payment Provider Webhook
1. Navigate to **Events (Webhooks)** in the sidebar.
2. Set Payment ID to your payment (e.g. `pay_aut_558291`), Status to `captured`, Amount to `14200.00`.
3. Click **Dispatch Webhook**.
4. Inspect the live 200 OK JSON response in the inspector.
5. Re-dispatch the same Event ID → observe the idempotency response: `duplicate: true`, preventing double counting.

### Step 6: Verify Recovery & Audit Trail
1. Return to the **Dashboard** → Observe **Recovered Revenue** and **Recovery Rate** have increased.
2. Navigate to **Audit Log** → Verify every step is recorded chronologically with timestamps, actors, and state transitions.

---

## 7. Security & Compliance

- **Zero Card Data Storage**: RecoverAI operates strictly on tokenized payment identifiers (`pay_xxx`), customer references (`cus_xxx`), and decline codes. No Primary Account Numbers (PAN), CVVs, or cardholder credentials are ever stored.
- **Server-Side Validation**: All bounds, limits, and approval rules are strictly validated on the FastAPI backend using Pydantic schemas.
- **Safe Error Handling**: Python internal stack traces are sanitized before sending responses to clients.

---

## 8. Future Enhancements

- **Machine Learning Transition**: Replace or augment the rule-based risk engine with an XGBoost/LightGBM model predicting payment recovery probabilities based on historical cardholder settlement patterns.
- **Multi-PSP Smart Routing**: Intelligently re-route retries across multiple payment gateways (Stripe, Adyen, Checkout.com, Razorpay) based on real-time authorization rates.
- **Automated Dunning Communications**: Webhook integrations with customer engagement platforms (Postmark, SendGrid, Twilio, WhatsApp Business) for interactive payment link delivery.
