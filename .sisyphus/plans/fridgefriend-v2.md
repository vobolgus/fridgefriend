# FridgeFriend v2 — Full Spec Compliance Work Plan

**Created:** 2026-04-04
**Predecessor:** fridgefriend.md (prototype, completed 2026-04-03)
**Scope:** Take prototype (99 backend tests, 5 Flutter screens) to full AGENTS.md spec compliance
**Methodology:** TDD (Red -> Green -> Refactor). Tests committed BEFORE implementation.
**Repository:** https://github.com/vobolgus/fridgefriend

---

## User Decisions (Locked)

1. **Infrastructure**: Local Docker + LocalStack (S3, SQS emulation), PostgreSQL, Redis. $0 cost.
2. **Firebase Auth**: Real architecture with toggleable mock via `AUTH_MOCK=true` env var.
3. **API Keys**: LiteLLM proxy at `https://litellm.labs.jb.gg` (OpenAI-compatible). Spoonacular, Amplitude, Sentry to be configured.
4. **Conflict Resolution**: Optimistic concurrency with `version` fields.
5. **Meal Plan Reservation**: `ReservedIngredient` model (separate records, transactional).
6. **Recipe Data**: Spoonacular API (free tier).
7. **Household Sync**: SSE for v1 (not WebSocket).

---

## Existing Codebase Snapshot

| Area | State | Count |
|------|-------|-------|
| Backend tests | Passing | 99 |
| Backend modules | inventory, catalog, recommendations, planning, expiry | 5 |
| Backend endpoints | items CRUD(6), barcode(1), recommendations(1), plans(1), shopping-list(1), health(1) | 11 |
| SQLAlchemy models | User, InventoryItem, Recipe, MealPlan, MealPlanDay | 5 |
| Flutter screens | Inventory, AddItem, Recommendations, MealPlan, ShoppingList | 5 |
| Flutter tests | Widget(3), Router(5), DAO(4), Smoke(1) | ~13 |
| Docker services | PostgreSQL 16, Redis 7 (not wired to app) | 2 |
| CI | GitHub Actions (backend + mobile) | 2 workflows |

---

## Phase 1: Foundation (Cross-Cutting Infrastructure)

> **Goal**: Make DB configurable, add real auth architecture, add optimistic concurrency, wire Docker services.
> **Dependency**: None — this is the base layer everything else builds on.

### Wave 1A: Database & Configuration (sequential)

- [ ] **1A-1**: Make database URL configurable via Settings
- [ ] **1A-2**: Add `version` column for optimistic concurrency
- [ ] **1A-3**: Add Redis configuration to Settings

### Wave 1B: Auth Architecture (sequential)

- [ ] **1B-1**: Extract auth to shared module with toggleable mock
- [ ] **1B-2**: Implement Firebase JWT validation (behind AUTH_MOCK=false)

### Wave 1C: Infrastructure Docker (parallelizable)

- [ ] **1C-1**: Create backend Dockerfile and wire docker-compose
- [ ] **1C-2**: Add LocalStack for S3 and SQS emulation

---

## Phase 2: Data Model Expansion

> **Goal**: Add all missing SQLAlchemy models required by the spec.
> **Dependency**: Phase 1A.

### Wave 2A: Household & Member models (sequential)

- [ ] **2A-1**: Add Household and HouseholdMember models
- [ ] **2A-2**: Add default household auto-creation to auth flow

### Wave 2B: Remaining models (parallelizable)

- [ ] **2B-1**: Add CanonicalIngredient and ProductBarcode models
- [ ] **2B-2**: Add notification and device token models
- [ ] **2B-3**: Add event tracking models (InventoryEvent, AnalyticsEvent, RecommendationSession, ReservedIngredient)

---

## Phase 3: Household Module (Backend)

> **Goal**: Full household CRUD + member management + household-scoped queries.
> **Dependency**: Phase 2A.

### Wave 3A: Household CRUD API

- [ ] **3A-1**: Create household module with CRUD endpoints

### Wave 3B: Household scoping (sequential)

- [ ] **3B-1**: Scope inventory queries by household
- [ ] **3B-2**: Scope recommendations and planning by household
- [ ] **3B-3**: Add InventoryEvent logging on all inventory mutations

---

## Phase 4: Enhanced Backend Services

> **Goal**: Upgrade existing services to full spec.
> **Dependency**: Phase 3.

### Wave 4A: Catalog & Expiry upgrades (parallelizable)

- [ ] **4A-1**: Migrate shelf-life rules from Python dict to database
- [ ] **4A-2**: Integrate CanonicalIngredient into catalog normalization
- [ ] **4A-3**: Add Spoonacular recipe API interface

### Wave 4B: Photo scan endpoint

- [ ] **4B-1**: Add photo scan endpoint with LLM interface

### Wave 4C: Transactional meal plan reservation

- [ ] **4C-1**: Implement ReservedIngredient transactional reservation

### Wave 4D: Enhanced recommendation scoring

- [ ] **4D-1**: Add substitutions and dietary fit to recommendation engine

---

## Phase 5: Notification & Async Jobs (Backend)

> **Goal**: Celery worker + push notification scheduling.
> **Dependency**: Phase 3, Phase 2B.

### Wave 5A: Celery setup

- [ ] **5A-1**: Add Celery worker configuration with Redis broker

### Wave 5B: Notification module

- [ ] **5B-1**: Create notification preferences API
- [ ] **5B-2**: Add expiry reminder Celery task
- [ ] **5B-3**: Add Celery Beat schedule for periodic reminders

---

## Phase 6: SSE Household Sync (Backend)

> **Goal**: SSE endpoint for real-time household activity stream.
> **Dependency**: Phase 3.

- [ ] **6A-1**: Add SSE endpoint for household activity stream
- [ ] **6A-2**: Add activity log endpoint

---

## Phase 7: Idempotency & Analytics Upgrades (Backend)

> **Goal**: Move idempotency to Redis, add analytics collection.
> **Dependency**: Phase 1C, Phase 2B.

- [ ] **7A-1**: Migrate idempotency cache to Redis
- [ ] **7A-2**: Add analytics event collection endpoint

---

## Phase 8: Flutter — Auth & Navigation

> **Goal**: Add Firebase auth flow, sign-in screen, household screen, settings screen.
> **Dependency**: Backend Phase 1B, Phase 3.

### Wave 8A: Auth infrastructure

- [ ] **8A-1**: Add Firebase Auth package and auth service
- [ ] **8A-2**: Add Sign In screen

### Wave 8B: New screens (parallelizable after auth)

- [ ] **8B-1**: Add Household management screen
- [ ] **8B-2**: Add Settings screen
- [ ] **8B-3**: Add Barcode Scan screen (camera integration)

---

## Phase 9: Flutter — Enhanced Features

> **Goal**: Photo upload, OCR review, Use Soon screen, Recipe Detail.
> **Dependency**: Phase 8.

### Wave 9A: Photo and OCR flow

- [ ] **9A-1**: Add Photo Upload screen
- [ ] **9A-2**: Add OCR Review screen

### Wave 9B: Enhanced screens (parallelizable)

- [ ] **9B-1**: Add Use Soon screen (expiry urgency dashboard)
- [ ] **9B-2**: Add Recipe Detail screen
- [ ] **9B-3**: Enhance Recipe Feed screen
- [ ] **9B-4**: Enhance Weekly Plan screen with reservation indicators

---

## Phase 10: Flutter — Offline & Sync

> **Goal**: Wire Drift as local cache, implement offline-first with sync.
> **Dependency**: Phase 9.

- [ ] **10A-1**: Wire Drift database as local cache for inventory
- [ ] **10A-2**: Add Drift tables for recipes and meal plans
- [ ] **10A-3**: Add SSE listener for household sync

---

## Phase 11: CI/CD & Infrastructure Hardening

> **Goal**: Enhanced CI, Sentry/Amplitude integration, production-ready Docker.
> **Dependency**: All previous phases.

- [ ] **11A-1**: Enhance GitHub Actions with Docker integration tests
- [ ] **11A-2**: Add Sentry error tracking
- [ ] **11A-3**: Add Amplitude analytics integration
- [ ] **11A-4**: Production Docker Compose with all services

---

## Phase 12: Final Integration & Polish

> **Goal**: End-to-end integration tests, API contract verification, documentation.
> **Dependency**: All previous phases.

- [ ] **12A-1**: Add comprehensive backend integration tests
- [ ] **12A-2**: API contract verification script
- [ ] **12A-3**: Update documentation

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total Phases | 12 |
| Total Tasks | 47 |
| New backend modules | 3 (households, notifications, analytics) |
| New SQLAlchemy models | 11 |
| New API endpoints | ~12 |
| New Flutter screens | 8 |
| New Flutter features | 3 (auth, households, settings) |

---

## Critical Path

```
Phase 1 (Foundation)
  |-- 1A: DB config
  |-- 1B: Auth architecture
  |-- 1C: Docker/LocalStack
  v
Phase 2 (Data Models)
  v
Phase 3 (Households)
  v
Phase 4 (Services) | Phase 5 (Notif) | Phase 6 (SSE)
  v
Phase 7 (Redis/Analytics)
  v
Phase 8 (Flutter Auth+Nav)
  v
Phase 9 (Flutter Features)
  v
Phase 10 (Offline+Sync)
  v
Phase 11 (CI/Infra) | Phase 12 (Integration)
```
