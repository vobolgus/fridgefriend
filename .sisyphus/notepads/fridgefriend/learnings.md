# FridgeFriend — Learnings

## 2026-04-03 — Metis Pre-Analysis

### Environment
- Python 3.14 available (spec said 3.12 — 3.14 is acceptable, newer)
- Flutter NOT installed locally — Flutter scaffold + tests must be runnable via CI
- Docker available — use for PostgreSQL in dev
- GitHub CLI authenticated as `vobolgus`
- No `uv` installed — use `pip` + `venv` or `python -m pip`

### Architecture Decisions
- Backend: modular monolith (NOT separate microservices) — single FastAPI app with `app/modules/{inventory,catalog,expiry,recommendations,planning}/`
- Each module: `router.py`, `schemas.py`, `service.py`, `repository.py`, `models.py`
- Flutter: feature-first clean architecture — `lib/features/{inventory,recommendations,meal_planning}/` with `data/`, `domain/`, `presentation/`
- Test DB: SQLite in-memory (`:memory:`) for all tests; PostgreSQL only for dev via docker-compose

### Key Conventions
- Pydantic v2 ONLY: `model_validator`, `field_validator`, `ConfigDict` — never v1 patterns
- SQLAlchemy 2.x ONLY: `Mapped[str]`, `mapped_column()` — never `Column(String)`
- FastAPI DI for ALL external boundaries (auth, DB, redis, recipe API, barcode API)
- Tests override via `app.dependency_overrides`
- Riverpod providers for ALL Flutter external dependencies
- `dart run build_runner build --delete-conflicting-outputs` after ANY Drift/Riverpod codegen change

### Mocking Strategy
| Service | Approach |
|---------|----------|
| Firebase Auth | Fake JWT middleware that accepts `Bearer test-token` in tests |
| Open Food Facts | Interface + in-memory dict mock |
| Spoonacular/Edamam | Canned JSON fixture files |
| GPT-4.1-mini photo | Returns hardcoded items, never called |
| AWS S3/SQS | Not implemented in prototype |
| Redis | `fakeredis` in tests |
| PostgreSQL | SQLite `:memory:` in tests |

### TDD Discipline
- Write failing test FIRST, commit it, then implement, commit implementation
- Every test must assert business logic outcomes (specific field values) not just HTTP status
- Minimum per service function: happy path + invalid input + not-found + unauthorized

### Prototype Scope (OUT)
- Household sharing / WebSocket
- Push notifications (Celery/FCM)
- Photo/OCR pipeline (S3/GPT)  
- Analytics (SQS/Amplitude)
- AWS/Terraform
- LightGBM ML ranking
- Flutter app running on real device
