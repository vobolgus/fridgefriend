# FridgeFriend Prototype — Work Plan

**Created:** 2026-04-03  
**Scope:** Single-user backend API (FastAPI/Python 3.14) + Flutter scaffold with full TDD  
**Methodology:** TDD (Red → Green → Refactor, tests committed BEFORE implementation)  
**Repository:** https://github.com/vobolgus/fridgefriend (to be created)

---

## Prototype Scope Decision

**IN SCOPE:**
- Backend: FastAPI monolith with modules: inventory, catalog, expiry, recommendations, planning
- All external services mocked via DI interfaces (Firebase, Spoonacular, Open Food Facts, GPT)
- PostgreSQL via Docker for dev; SQLite in-memory for tests
- Flutter project scaffold: all features stubbed with passing widget tests
- GitHub Actions CI (backend tests + Flutter tests)
- GitHub repo: `vobolgus/fridgefriend`

**OUT OF SCOPE (prototype deferral):**
- Household sharing / multi-user sync / WebSocket
- Real push notifications (Celery/FCM/APNs)
- Real photo/OCR pipeline (S3 + GPT)
- Real analytics (SQS/Amplitude)
- AWS/Terraform infrastructure
- LightGBM ML ranking (rules-based only)
- Flutter app running on device (scaffold + tests only, Flutter not installed)

---

## TODOs

### Phase 0: Project Scaffolding

- [ ] **P0-1**: Initialize GitHub repo `vobolgus/fridgefriend` as public monorepo with MIT license, .gitignore, and README
- [ ] **P0-2**: Scaffold backend Python project structure (`backend/`) with pyproject.toml, FastAPI app, health endpoint, and pytest config — TDD: health test first
- [ ] **P0-3**: Scaffold Flutter project (`mobile/`) with pubspec.yaml, Riverpod, Drift, Dio, and navigation shell — with passing widget tests
- [ ] **P0-4**: Add GitHub Actions CI for backend (`pytest`) and Flutter (`flutter test`) 

### Phase 1: Backend Core

- [ ] **P1-1**: Add SQLAlchemy 2.x models and database configuration (Alembic migrations, test DB setup)
- [ ] **P1-2**: Implement Inventory CRUD API — TDD first: tests for create/read/update/delete/mark-used/discard/freeze
- [ ] **P1-3**: Implement Catalog/Normalization service — TDD first: barcode→canonical ingredient with mocked Open Food Facts interface
- [ ] **P1-4**: Implement Expiry rules engine — TDD first: shelf-life calculation for known ingredients, confidence scoring
- [ ] **P1-5**: Implement urgency bucketing — TDD first: Today/This Week/Safe Later assignment logic
- [ ] **P1-6**: Implement Recipe Recommendation engine — TDD first: rules-based ranking with known inventory + canned recipe data
- [ ] **P1-7**: Implement Meal Planning algorithm — TDD first: greedy planner prioritizing expiring items, inventory reservation
- [ ] **P1-8**: Implement Shopping List derivation — TDD first: gap calculation between plan requirements and inventory

### Phase 2: Flutter Scaffold (tests-first)

- [ ] **P2-1**: Add Drift database schema and DAOs for inventory items — TDD first: insert/read/update/delete tests
- [ ] **P2-2**: Add Riverpod providers for inventory state — TDD first: loading/data/error states
- [ ] **P2-3**: Add Inventory List and Add Item screens with widget tests
- [ ] **P2-4**: Add API client layer (Dio) with mock backend and tests
- [ ] **P2-5**: Add Expiry urgency display screens with widget tests
- [ ] **P2-6**: Add Recipe Recommendation screen with provider and widget tests
- [ ] **P2-7**: Add Meal Plan and Shopping List screens with widget tests

### Phase 3: Integration & Polish

- [ ] **P3-1**: Add backend integration tests (full flow: add item → recommendations → generate plan → shopping list)
- [ ] **P3-2**: Add Docker Compose for local backend dev (PostgreSQL + Redis)
- [ ] **P3-3**: Final commit: comprehensive README with quickstart, architecture, API docs

---

## Final Verification Wave

- [ ] **F1**: All backend tests pass (`cd backend && python -m pytest tests/ -v` → 0 failures)
- [ ] **F2**: All Flutter tests pass (`cd mobile && flutter test` → 0 failures, via CI)
- [ ] **F3**: GitHub Actions CI green on all workflows
- [ ] **F4**: Backend API functional verification (curl all 8 endpoints, verify response shapes match spec)
