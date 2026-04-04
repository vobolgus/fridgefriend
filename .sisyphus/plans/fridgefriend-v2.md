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

- [x] **1A-1**: Make database URL configurable via Settings
- [x] **1A-2**: Add `version` column for optimistic concurrency
- [x] **1A-3**: Add Redis configuration to Settings

### Wave 1B: Auth Architecture (sequential)

- [x] **1B-1**: Extract auth to shared module with toggleable mock
- [x] **1B-2**: Implement Firebase JWT validation (behind AUTH_MOCK=false)

### Wave 1C: Infrastructure Docker (parallelizable)

- [x] **1C-1**: Create backend Dockerfile and wire docker-compose
- [x] **1C-2**: Add LocalStack for S3 and SQS emulation

---

## Phase 2: Data Model Expansion

> **Goal**: Add all missing SQLAlchemy models required by the spec.
> **Dependency**: Phase 1A.

### Wave 2A: Household & Member models (sequential)

- [x] **2A-1**: Add Household and HouseholdMember models
- [x] **2A-2**: Add default household auto-creation to auth flow

### Wave 2B: Remaining models (parallelizable)

- [x] **2B-1**: Add CanonicalIngredient and ProductBarcode models
- [x] **2B-2**: Add notification and device token models
- [x] **2B-3**: Add event tracking models (InventoryEvent, AnalyticsEvent, RecommendationSession, ReservedIngredient)

---

## Phase 3: Household Module (Backend)

> **Goal**: Full household CRUD + member management + household-scoped queries.
> **Dependency**: Phase 2A.

### Wave 3A: Household CRUD API

- [x] **3A-1**: Create household module with CRUD endpoints

### Wave 3B: Household scoping (sequential)

- [x] **3B-1**: Scope inventory queries by household
- [x] **3B-2**: Scope recommendations and planning by household
- [x] **3B-3**: Add InventoryEvent logging on all inventory mutations

---

## Phase 4: Enhanced Backend Services

> **Goal**: Upgrade existing services to full spec.
> **Dependency**: Phase 3.

### Wave 4A: Catalog & Expiry upgrades (parallelizable)

- [x] **4A-1**: Migrate shelf-life rules from Python dict to database
- [x] **4A-2**: Integrate CanonicalIngredient into catalog normalization
- [x] **4A-3**: Add Spoonacular recipe API interface

### Wave 4B: Photo scan endpoint

- [x] **4B-1**: Add photo scan endpoint with LLM interface

### Wave 4C: Transactional meal plan reservation

- [x] **4C-1**: Implement ReservedIngredient transactional reservation

### Wave 4D: Enhanced recommendation scoring

- [x] **4D-1**: Add substitutions and dietary fit to recommendation engine

---

## Phase 5: Notification & Async Jobs (Backend)

> **Goal**: Celery worker + push notification scheduling.
> **Dependency**: Phase 3, Phase 2B.

### Wave 5A: Celery setup

- [x] **5A-1**: Add Celery worker configuration with Redis broker

### Wave 5B: Notification module

- [x] **5B-1**: Create notification preferences API
- [x] **5B-2**: Add expiry reminder Celery task
- [x] **5B-3**: Add Celery Beat schedule for periodic reminders

---

## Phase 6: SSE Household Sync (Backend)

> **Goal**: SSE endpoint for real-time household activity stream.
> **Dependency**: Phase 3.

- [x] **6A-1**: Add SSE endpoint for household activity stream
- [x] **6A-2**: Add activity log endpoint

---

## Phase 7: Idempotency & Analytics Upgrades (Backend)

> **Goal**: Move idempotency to Redis, add analytics collection.
> **Dependency**: Phase 1C, Phase 2B.

- [x] **7A-1**: Migrate idempotency cache to Redis
- [x] **7A-2**: Add analytics event collection endpoint

---

## Phase 8: Flutter — Auth & Navigation

> **Goal**: Add Firebase auth flow, sign-in screen, household screen, settings screen.
> **Dependency**: Backend Phase 1B, Phase 3.

### Wave 8A: Auth infrastructure

- [x] **8A-1**: Add Firebase Auth package and auth service
- [x] **8A-2**: Add Sign In screen

### Wave 8B: New screens (parallelizable after auth)

- [x] **8B-1**: Add Household management screen
- [x] **8B-2**: Add Settings screen
- [x] **8B-3**: Add Barcode Scan screen (camera integration)

---

## Phase 9: Flutter — Enhanced Features

> **Goal**: Photo upload, OCR review, Use Soon screen, Recipe Detail.
> **Dependency**: Phase 8.

### Wave 9A: Photo and OCR flow

- [x] **9A-1**: Add Photo Upload screen
- [x] **9A-2**: Add OCR Review screen

### Wave 9B: Enhanced screens (parallelizable)

- [x] **9B-1**: Add Use Soon screen (expiry urgency dashboard)
- [x] **9B-2**: Add Recipe Detail screen
- [x] **9B-3**: Enhance Recipe Feed screen
- [x] **9B-4**: Enhance Weekly Plan screen with reservation indicators

---

## Phase 10: Flutter — Offline & Sync

> **Goal**: Wire Drift as local cache, implement offline-first with sync.
> **Dependency**: Phase 9.

- [x] **10A-1**: Wire Drift database as local cache for inventory
- [x] **10A-2**: Add Drift tables for recipes and meal plans
- [x] **10A-3**: Add SSE listener for household sync

---

## Phase 11: CI/CD & Infrastructure Hardening

> **Goal**: Enhanced CI, Sentry/Amplitude integration, production-ready Docker.
> **Dependency**: All previous phases.

- [x] **11A-1**: Enhance GitHub Actions with Docker integration tests
- [x] **11A-2**: Add Sentry error tracking
- [x] **11A-3**: Add Amplitude analytics integration
- [x] **11A-4**: Production Docker Compose with all services

---

## Phase 12: Final Integration & Polish

> **Goal**: End-to-end integration tests, API contract verification, documentation.
> **Dependency**: All previous phases.

- [x] **12A-1**: Add comprehensive backend integration tests
- [x] **12A-2**: API contract verification script
- [x] **12A-3**: Update documentation

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
