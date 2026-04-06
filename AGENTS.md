# FRIDGEFRIEND — PROJECT KNOWLEDGE BASE

**Generated:** 2026-04-03
**Status:** Pre-implementation (spec phase). Source: `FridgeFriend_SPEC_filled.xlsx`

---

## OVERVIEW

FridgeFriend is a mobile app (Flutter/iOS+Android) that tracks kitchen inventory, surfaces items nearing expiry, and generates ranked recipe suggestions, weekly meal plans, and shopping lists to reduce food waste. Backend is Python/FastAPI on AWS.

---

## TECH STACK

| Layer | Technology |
|-------|-----------|
| Mobile | Flutter 3.24 (Dart), Riverpod (state), Drift/SQLite (offline cache), Dio (HTTP) |
| Optional web | Next.js 14 + TypeScript (admin/support only) |
| API | FastAPI (Python 3.12), Pydantic v2, SQLAlchemy 2.x |
| Auth | Firebase Authentication (email, Apple, Google) → JWT |
| DB | PostgreSQL 16 (RDS), Redis (ElastiCache, cache + Celery broker) |
| Async jobs | Celery + Redis |
| Search | OpenSearch (recipe candidate retrieval) |
| Storage | S3 (images), CloudFront (CDN) |
| Queues | Amazon SQS (async events), dead-letter queues for failures |
| Push | Firebase Cloud Messaging + APNs |
| AI / Vision | GPT-4.1-mini or Gemini 1.5 Flash (fridge photo parsing); Apple Vision (iOS) / ML Kit (Android) for on-device OCR |
| Barcode | Open Food Facts / UPC lookup |
| Recipe data | Spoonacular or Edamam + internal corpus |
| Infra-as-code | Terraform; all on AWS us-east-1 (ECS Fargate) |
| CI/CD | GitHub Actions |
| Observability | Sentry + CloudWatch + Crashlytics; Amplitude (product analytics) |
| ML (v2) | LightGBM learning-to-rank on click/save/cook labels |

---

## ARCHITECTURE

```
Mobile App (Flutter)
  └── API Gateway + Auth Service  ← Firebase JWT validation
        ├── Inventory Service       ← CRUD for InventoryItem, events
        ├── Catalog/Normalization   ← barcode → canonical ingredient
        ├── Expiry Service          ← shelf-life rules → urgency buckets
        ├── Recommendation Service  ← OpenSearch + Python ranker
        ├── Meal Planning Service   ← greedy optimizer + reservation
        ├── Notification Service    ← Celery scheduler → FCM/APNs
        ├── Household Sync Service  ← WebSocket/SSE + activity log
        └── Analytics Collector     ← SQS event stream → Amplitude
```

Async flow: API emits SQS jobs → Celery workers → Catalog → Expiry → Inventory persisted → Redis cached.  
Image pipeline: S3 upload → multimodal LLM → normalized draft → editable in UI.

---

## DATA MODEL (key entities)

```
User → HouseholdMember → Household
Household 1..* InventoryItem → CanonicalIngredient
CanonicalIngredient 1..* ShelfLifeRule (by storage type)
ProductBarcode *..1 CanonicalIngredient
Recipe *..* CanonicalIngredient (via RecipeIngredient)
MealPlan 1..* MealPlanDay; MealPlan *..* InventoryItem (via ReservedIngredient)
RecommendationSession → Household; references Recipes shown
NotificationPreference, DeviceToken per User
AnalyticsEvent (immutable log)
InventoryEvent (versioned, supports undo)
```

---

## API CONTRACT

Base: `https://api.fridgefriend.app/v1/`  
Auth: `Authorization: Bearer <firebase-jwt>`  
All writes use **idempotency keys**.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/items` | POST | Manual item add |
| `/v1/scan/barcode` | POST | Barcode lookup + add |
| `/v1/scan/photo` | POST | Fridge photo → draft items |
| `/v1/recommendations` | POST | Ranked recipe suggestions |
| `/v1/plans` | POST | Generate weekly meal plan |
| `/v1/shopping-list` | GET | Shopping gaps from plan |
| `/v1/households` | GET/POST/PATCH | Household CRUD |
| `/v1/notifications` | PATCH | Notification preferences |

**Key response shapes:**
- Item create `201`: `{itemId, canonicalIngredientId, displayName, quantity, unit, storageLocation, estimatedExpiryDate, confidence}`
- Recommendations `200`: `{recipes:[{id,title,useSoonScore,coveragePct,missingItems[],substitutions[],prepMinutes}]}`
- Meal plan `200`: `{plan:{days:[{date,recipeId,servings,reservedItems[]}], shoppingList:[...]}}`

---

## FUNCTIONAL REQUIREMENTS

| ID | Requirement |
|----|-------------|
| FR-1 | Manual entry, barcode scan, fridge photo for inventory capture |
| FR-2 | Normalize to canonical ingredient names/quantities/units |
| FR-3 | Assign estimated expiry + confidence score (shelf-life rules) |
| FR-4 | Rank recipes by expiry urgency, ingredient coverage, prep time, dietary fit |
| FR-5 | Show substitutions + minimum missing-ingredient list per recipe |
| FR-6 | Group items into urgency buckets (Today / This Week / Safe Later) |
| FR-7 | Configurable push reminders for expiring items |
| FR-8 | Mark items as used / discarded / frozen |
| FR-9 | Generate 3-7 day meal plans prioritizing on-hand / near-expiry |
| FR-10 | Reserve planned ingredients; shopping list = gaps only |
| FR-11 | Shared household: add/edit/consume with item-level granularity |
| FR-12 | Activity log with conflict handling and basic undo for recent changes |

---

## PERFORMANCE SLOs

| Operation | Target |
|-----------|--------|
| Item create (manual/barcode) | < 3s P95 |
| Recipe recommendations | < 5s P95 |
| Meal plan generation | < 8s P95 |
| Dashboard load (≤500 items) | < 2s P95 |
| Household sync | < 5s under normal network |
| Push reminder delivery | within 1 minute of target |
| API availability | 99.5% |

---

## USER STORIES → TASKS MAP

| Story | Task | Subtasks |
|-------|------|---------|
| US-1: Inventory capture | T-1 | ST-1 (CRUD API), ST-2 (barcode/manual), ST-3 (photo/OCR) |
| US-1: Recommendations | T-2 | ST-4 (recipe index), ST-5 (ranking + UI) |
| US-2: Expiry dashboard | T-3 | ST-6 (urgency/dashboard), ST-7 (notifications), ST-8 (state changes) |
| US-2: Meal planning | T-4 (dep: T-1,T-2,T-3) | ST-9 (planner algo), ST-10 (shopping list + UI) |
| US-3: Household sync | T-5 | ST-11 (auth/sync/events), ST-12 (analytics) |

---

## KEY SCREENS (Flutter)

Sign In → Home Inventory → Add Item → Barcode Scan → Photo Upload → OCR Review → Use Soon → Recipe Feed → Recipe Detail → Weekly Plan → Shopping List → Household → Settings

---

## CONVENTIONS

- **Backend language:** Python 3.12 strictly; FastAPI + Pydantic v2 for all services
- **Mobile:** Flutter/Dart; Riverpod for state, Drift (SQLite) for offline-first cache
- **Error handling:** Barcode/photo failures return *partial editable drafts*, never hard 500s; circuit breaker falls back to manual entry when model latency or confidence is poor
- **Idempotency:** All write endpoints require idempotency keys
- **Auth boundary:** Household-level authorization on all data; Firebase JWT on every request
- **Image privacy:** No training on user photos by default; S3 signed upload URLs

### Version Naming Policy

The app version lives in `mobile/pubspec.yaml` as `version: <MAJOR>.<MINOR>.<PATCH>+<BUILD>`.

**Version string (`MAJOR.MINOR.PATCH`)** — follows [Semantic Versioning](https://semver.org/):
- **MAJOR** — breaking changes, major redesigns, or backward-incompatible API changes (e.g., `1.0.0` for first public release)
- **MINOR** — new features, new screens, significant enhancements (e.g., `0.2.0` for adding meal planning)
- **PATCH** — bug fixes, small UI tweaks, copy changes (e.g., `0.1.1` for a crash fix)

**Build number (`+N`)** — auto-incremented by CI on every TestFlight upload. Never set manually. The Fastlane `beta` lane fetches the latest build number from TestFlight and increments it.

**When to bump the version string:**
- Before a release with new user-facing features → bump MINOR (e.g., `0.1.0` → `0.2.0`)
- Before a release with only bug fixes → bump PATCH (e.g., `0.2.0` → `0.2.1`)
- For the first App Store public release → set to `1.0.0`
- Multiple CI builds within the same version are fine — the build number distinguishes them

**Current version:** `0.1.0` (pre-release/pilot phase)

**Examples:**
| pubspec.yaml | TestFlight shows | Meaning |
|---|---|---|
| `0.1.0+N` | 0.1.0 (N) | Initial pilot builds |
| `0.2.0+N` | 0.2.0 (N) | Added meal planning feature |
| `0.2.1+N` | 0.2.1 (N) | Fixed crash in meal planner |
| `1.0.0+N` | 1.0.0 (N) | First public App Store release |

---

## ANTI-PATTERNS (DO NOT DO)

- Do NOT return hard errors for low-confidence barcode/photo parses — always return editable drafts
- Do NOT bypass household-level auth checks for any inventory operation
- Do NOT expose raw S3 URLs — always use signed URLs
- Do NOT train or log user photos without explicit opt-in
- Do NOT generate meal plans without reserving inventory quantities against them (causes double-use bugs)
- Do NOT call OpenSearch directly from the mobile client — always via Recommendation Service

---

## EXTERNAL DEPENDENCIES / INTEGRATIONS

- **Open Food Facts / UPC** — barcode → product metadata
- **Spoonacular or Edamam** — initial recipe corpus (internal corpus supplements)
- **Firebase Auth** — identity (email, Apple, Google sign-in)
- **Firebase Cloud Messaging + APNs** — push notifications
- **GPT-4.1-mini / Gemini 1.5 Flash** — multimodal fridge photo parsing
- **Apple Vision (iOS) / ML Kit (Android)** — on-device OCR
- **Amplitude** — product analytics
- **Sentry + Crashlytics** — error/crash monitoring

---

## WHERE TO LOOK (once code exists)

| Task | Expected Location |
|------|------------------|
| Inventory CRUD | `backend/inventory/` |
| Barcode/catalog normalization | `backend/catalog/` |
| Shelf-life rules | `backend/expiry/` |
| Recommendation ranking | `backend/recommendations/` |
| Meal planner algorithm | `backend/planning/` |
| Push notification jobs | `backend/notifications/` |
| Household sync / WebSocket | `backend/households/` |
| Flutter screens | `mobile/lib/screens/` |
| Riverpod providers | `mobile/lib/providers/` |
| Drift DB schema | `mobile/lib/database/` |
| Terraform infra | `infra/` |
| GitHub Actions CI | `.github/workflows/` |

---

## NOTES / GOTCHAS

- **Recommendation engine v1 is rules-based** (expiry urgency + ingredient coverage + dietary fit + prep time + missing-item penalty). LightGBM L2R is explicitly v2 scope.
- **Photo parsing confidence** drives whether to show full auto-fill or partial editable draft — always store the confidence score.
- **Household sync uses WebSocket/SSE** for real-time activity feed; REST for CRUD.
- **Celery jobs** handle: image normalization, expiry recalculation, push scheduling. Redis is both cache and Celery broker.
- **Meal plan reservation** must be transactional: plan generation and quantity reservation happen atomically or neither commits.
- **Offline-first:** Flutter uses Drift SQLite for local state; sync happens on reconnect. Conflict resolution strategy TBD at implementation time.
