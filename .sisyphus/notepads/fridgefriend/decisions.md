# FridgeFriend — Architectural Decisions

## 2026-04-03

### ADR-001: Modular Monolith over Microservices
**Decision**: Single FastAPI app with module-based structure  
**Reason**: Prototype scope; microservices require network overhead, service discovery, distributed tracing all of which are out of scope  
**Consequence**: All modules share one DB connection, one Redis, one process

### ADR-002: SQLite in Tests, PostgreSQL in Dev
**Decision**: Tests use SQLite `:memory:`, docker-compose provides PostgreSQL for dev server  
**Reason**: Fast test execution, no docker dependency in CI for unit tests  
**Risk**: SQLite dialect differences (no ARRAY type, different JSON support) — mitigated by avoiding PostgreSQL-specific SQLAlchemy features in core logic

### ADR-003: Rules-Based Recipe Ranking Only (No ML)
**Decision**: Score = expiry_urgency_weight * 0.5 + coverage_pct * 0.3 + (1/(prep_min+1)) * 0.1 + dietary_match * 0.1  
**Reason**: LightGBM is explicitly v2 scope per spec  
**Consequence**: Less personalized recommendations but fully testable with known weights

### ADR-004: Flutter Scaffold in CI, Not Local
**Decision**: Flutter project created and tested in GitHub Actions CI only (flutter not installed locally)  
**Reason**: Flutter not available on dev machine  
**Consequence**: Cannot run `flutter run` locally; all Flutter verification via `flutter test` in CI

### ADR-005: Single-User Model for Prototype
**Decision**: No Household entity in prototype; every item belongs to a User directly  
**Reason**: Household sync is explicitly out of prototype scope  
**Consequence**: Simple FK `user_id` on InventoryItem; no HouseholdMember join table needed

### ADR-006: Auth in Tests via Fake JWT
**Decision**: Test auth middleware accepts `Authorization: Bearer test-token` and returns a fixed test user  
**Reason**: No Firebase SDK in test environment  
**Consequence**: Never call Firebase SDK in tests; `get_current_user` dependency overridden

### ADR-007: Python 3.14 (not 3.12 as spec states)
**Decision**: Use Python 3.14 (what's available)  
**Reason**: Python 3.12 not installed; 3.14 is a superset  
**Risk**: Minor — some 3.12-only packages may behave differently; negligible for this stack

## 2026-04-03 — P0-2 Dependency pinning for Python 3.14
- Chose FastAPI 0.135.3 / Uvicorn 0.43.0 / Pydantic 2.12.5 / pydantic-settings 2.13.1 because older requested minimums triggered `pydantic-core` source builds incompatible with the local Python 3.14 environment.

## 2026-04-03 — P1-4/P1-5 expiry implementation shape
- Kept expiry logic as three small pure modules: rules lookup, expiry-date calculation service, and urgency bucketing enum/helper.
- Used `StrEnum` for urgency buckets so downstream API/schema layers can serialize enum values directly without extra conversion.
