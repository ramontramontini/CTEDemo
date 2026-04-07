# L2 Project Stack — CTEDemo (Auto-Loaded)

---

## Identity
**CTEDemo** = Sistema Gerador e Gerenciador de CT-e
**Stack:** Vite/React 19/TypeScript | FastAPI/SQLAlchemy/PostgreSQL | Playwright/Vitest/pytest
**UI:** Tailwind CSS utility classes + custom components

---

## Test Commands
| Type | Command |
|------|---------|
| Frontend | `cd frontend && npx vitest run` |
| Backend | `cd backend && DATA_MODE=memory poetry run python -m pytest ../tests/backend -v --no-cov` |
| API | `cd backend && DATA_MODE=memory poetry run python -m pytest ../tests/api -v --no-cov` |
| E2E | `npm run e2e` |

ALL suites must pass before commit.

---

## Domain Aggregates

```
backend/src/domain/
    cte/              # CT-e aggregate (main domain)
    remetente/        # Sender (shipper)
    destinatario/     # Recipient
    transportadora/   # Carrier
    shared/           # Cross-aggregate types (Money, CNPJ, etc.)
    services/         # Cross-aggregate orchestration
```

---

## Environment

```bash
# Development
cd backend && DATA_MODE=memory uvicorn src.main:app --reload --port 8000
cd frontend && npm run dev

# Production
DATA_MODE=db  # PostgreSQL
```
