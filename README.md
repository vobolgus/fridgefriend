# FridgeFriend

Reduce food waste by tracking kitchen inventory, surfacing expiring items, generating recipe recommendations, building meal plans, and syncing household activity.

## Status

- Backend: FastAPI prototype with household scoping, inventory events, notifications, analytics, planning, and integration coverage.
- Mobile: Flutter scaffold with Riverpod, Drift offline cache, SSE household listener, and test coverage for core flows.
- Product spec: [SPEC.md](SPEC.md), converted from `FridgeFriend_SPEC_filled.xlsx` for agent-friendly edits.

## Feature Summary

### Inventory
- Manual item add
- Barcode lookup draft flow
- Photo scan draft flow
- Expiry confidence + urgency support
- Inventory lifecycle: active, used, discarded, frozen
- Optimistic concurrency and undo event support

### Recommendations and Planning
- Rules-based recipe recommendations
- Expiry-aware ranking
- Meal plan generation for 3-7 days
- Transactional ingredient reservation
- Shopping list gap detection

### Household and Sync
- Household CRUD + invite join flow
- Shared household inventory boundaries
- Activity log endpoint
- SSE event stream endpoint
- Flutter offline mutation queue and cache-first reads

### Platform / Infra
- PostgreSQL-backed CI workflow
- Docker Compose production stack
- Sentry initialization stubs for backend + Flutter
- Amplitude analytics stubs for backend + Flutter

## Architecture

```text
Flutter Mobile App
  ├── Riverpod providers
  ├── Drift local cache
  ├── SyncManager offline queue
  └── SSE household listener

FastAPI Backend
  ├── /v1/items
  ├── /v1/scan/barcode
  ├── /v1/scan/photo
  ├── /v1/recommendations
  ├── /v1/plans
  ├── /v1/shopping-list
  ├── /v1/households
  ├── /v1/notifications
  └── /v1/analytics/events

Supporting Services
  ├── PostgreSQL
  ├── Redis
  ├── Celery worker + beat
  └── LocalStack (S3/SQS)
```

## Quick Start

### Backend local

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m pytest tests/ -v --tb=short
uvicorn app.main:app --reload
```

### Flutter local

```bash
cd mobile
flutter pub get
flutter test --reporter expanded
```

### Docker quickstart

Development services:

```bash
docker-compose up -d
```

Production-like stack:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
python scripts/seed_data.py
```

Stop stack:

```bash
docker-compose -f docker-compose.prod.yml down
```

## API Endpoints

Base URL: `http://localhost:8000`

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Service health |
| `/v1/items` | GET/POST | List and create inventory items |
| `/v1/items/{item_id}` | GET/PATCH/PUT/DELETE | Read, update, replace, delete item |
| `/v1/items/{item_id}/status` | POST | Update inventory status |
| `/v1/scan/barcode` | POST | Resolve barcode into product draft |
| `/v1/scan/photo` | POST | Parse photo into editable draft items |
| `/v1/recommendations` | POST | Get ranked recipes |
| `/v1/plans` | POST | Generate meal plan |
| `/v1/plans/{plan_id}` | DELETE | Delete a saved meal plan |
| `/v1/shopping-list` | GET | Compute current shopping gaps |
| `/v1/households` | GET/POST | List and create households |
| `/v1/households/{household_id}` | GET/PATCH | Household detail and update |
| `/v1/households/join` | POST | Join by invite code |
| `/v1/households/{household_id}/leave` | POST | Leave household |
| `/v1/households/{household_id}/members/{user_id}` | DELETE | Remove member |
| `/v1/households/{household_id}/events` | GET | SSE event stream |
| `/v1/households/{household_id}/activity` | GET | Household activity log |
| `/v1/notifications` | GET/PATCH | Notification preferences |
| `/v1/notifications/devices` | POST | Register device token |
| `/v1/notifications/devices/{token_id}` | DELETE | Unregister device token |
| `/v1/analytics/events` | POST | Collect analytics event |

## Example Requests

```bash
curl -X POST http://localhost:8000/v1/items \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: add-milk-1" \
  -d '{"display_name":"Milk","quantity":1,"unit":"liter","storage_location":"fridge"}'

curl -X POST http://localhost:8000/v1/recommendations \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"servings":2}'

curl -X POST http://localhost:8000/v1/plans \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: plan-7-days" \
  -d '{"days":7,"servings":2}'
```

## Verification Scripts and Test Commands

### Backend tests

```bash
cd backend
source .venv/bin/activate
python -m pytest tests/ -v --tb=short
```

### Flutter tests

```bash
cd mobile
flutter test --reporter expanded
```

### API contract verification

```bash
source backend/.venv/bin/activate
python scripts/verify_api_contract.py --base-url http://localhost:8000 --token test-token
```

### Product spec export

```bash
python scripts/export_spec_markdown.py
cd backend
python -m pytest tests/test_spec_markdown.py tests/test_api_contract.py -v --tb=short
```

## Observability Stubs

- Backend Sentry initializes when `SENTRY_DSN` is set.
- Flutter Sentry initializes when compiled with `--dart-define=SENTRY_DSN=...`.
- Backend analytics uses a pluggable `AnalyticsInterface` with `AmplitudeClient` and `NoopAnalytics` stubs.
- Flutter includes a minimal analytics service abstraction with Amplitude stub wiring.

## Repository Layout

```text
backend/
  app/
    core/
    models/
    modules/
  tests/
mobile/
  lib/
  test/
scripts/
docs/
.github/workflows/
docker-compose.yml
docker-compose.prod.yml
```

## GitHub

https://github.com/vobolgus/fridgefriend
