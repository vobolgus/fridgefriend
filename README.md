# FridgeFriend

> Reduce food waste by tracking what's in your kitchen and getting meal suggestions before ingredients expire.

## Status
🟢 Working prototype — backend fully operational with TDD coverage  
🟡 Mobile app — scaffold with tests, requires Flutter 3.24+ to run

## Quick Start

### Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
python3 -m pytest tests/ -v   # 90+ tests should pass
uvicorn app.main:app --reload  # Start dev server on :8000
```

### With Docker (PostgreSQL + Redis)
```bash
docker-compose up -d
cd backend && uvicorn app.main:app --reload
```

### Mobile
```bash
cd mobile && flutter pub get && flutter test
```

## Architecture
```
Mobile App (Flutter)
  └── FastAPI Backend
        ├── /v1/items           — Inventory CRUD
        ├── /v1/scan/barcode    — Barcode lookup
        ├── /v1/recommendations — Recipe suggestions
        ├── /v1/plans           — Meal plan generation
        ├── /v1/shopping-list   — Shopping gaps
        └── /health             — Health check
```

## API Examples
```bash
# Add item
curl -X POST http://localhost:8000/v1/items \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Milk","quantity":1,"unit":"gallon","storage_location":"fridge"}'

# Get recommendations
curl -X POST http://localhost:8000/v1/recommendations \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"servings":2}'

# Generate meal plan
curl -X POST http://localhost:8000/v1/plans \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"days":7}'
```

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.x |
| Database | PostgreSQL 16 (dev), SQLite (tests) |
| Cache/Broker | Redis 7 |
| Mobile | Flutter 3.24, Riverpod, Drift, GoRouter |
| Auth | Firebase JWT (test: Bearer test-token) |
| CI | GitHub Actions |

## Tests
```
90+ tests covering:
  ✅ Health endpoint
  ✅ Database models (User, InventoryItem, Recipe, MealPlan)
  ✅ Inventory CRUD API
  ✅ Catalog/barcode service
  ✅ Expiry rules engine
  ✅ Recipe recommendation engine
  ✅ Meal planning algorithm
  ✅ Integration (full user journey)
```

## Local Development Commands
```bash
# backend tests
cd backend
source .venv/bin/activate
python3 -m pytest tests/ -v

# backend dev server
uvicorn app.main:app --reload

# docker services only
docker-compose up -d
docker-compose down
```

## Repository Layout
```
backend/
  app/
    core/
    models/
    modules/
  tests/
mobile/
.github/workflows/
docker-compose.yml
```

## GitHub
https://github.com/vobolgus/fridgefriend
