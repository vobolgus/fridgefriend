# FridgeFriend Specification

Source workbook: `FridgeFriend_SPEC_filled.xlsx`.
This Markdown version is the editable product spec for agents and code review.

Regenerate from the workbook with `python scripts/export_spec_markdown.py`.

## 1. Feature Context

| Section | Fill In |
| --- | --- |
| Feature | FridgeFriend |
| Description (Goal / Scope) | Mobile app that suggests meals from ingredients already in the fridge and pantry, prioritizing items that will expire soon and recommending substitutions, alerts, and weekly plans to reduce food waste. |
| Client | Busy households, young professionals, couples, students, and families who cook at home a few times per week and want to save money while wasting less food. |
| Problem | People forget what food they already have, let ingredients expire, buy duplicates, and fall back to takeout because existing recipe apps start from ideal recipes instead of real inventory on hand. |
| Solution | Users add items by photo, barcode, or manual entry. FridgeFriend tracks estimated expiry dates, highlights use-soon items, and generates recipes and meal plans that maximize on-hand ingredients before they go bad. |
| Metrics | % of expiring items used before expiry<br>Weekly active users<br>Recipes opened / saved / cooked<br>Reported food waste reduction<br>Average grocery savings<br>D30 retention |

## 2. User Stories and Use Cases

### User Story 1

| Field | Value |
| --- | --- |
| Role | Home cook / primary grocery shopper |
| User Story ID | US-1 |
| User Story | As a home cook, I want FridgeFriend to understand what is already in my kitchen, so that I can make meals without wasting food or buying duplicates. |
| UX / User Flow | Open app -> add groceries by barcode / photo / manual entry -> review normalized inventory -> receive use-soon meal suggestions -> cook / mark items used |

#### Use Case (+ Edges) BDD 1

| Field | Value |
| --- | --- |
| Use Case ID | UC-1.1 |
| Given | The user has groceries at home and opens the app after shopping or before cooking. |
| When | The user scans a barcode, uploads a fridge photo, or adds an item manually. |
| Then | FridgeFriend creates normalized inventory items with quantity, storage location, and estimated expiry date. |
| Input | Barcode, photo, or item name; quantity; unit; storage location; optional brand |
| Output | Updated inventory list with standardized ingredient names, quantities, and expiry estimates |
| State | Item status = Active; source tagged as barcode / photo / manual; confidence score stored |

#### Functional Requirements

| Req ID | Requirement |
| --- | --- |
| FR-1 | Support manual entry, barcode scan, and fridge-photo ingestion for inventory capture. |
| FR-2 | Normalize products to canonical ingredient names, quantities, and storage units. |
| FR-3 | Assign estimated expiry dates and confidence scores using shelf-life rules. |

#### Non-Functional Requirements

| Req ID | Requirement |
| --- | --- |
| NFR-1 | Manual and barcode item creation completes in under 3 seconds on supported devices. |
| NFR-2 | Photo parsing returns editable results with graceful fallback when confidence is low. |
| NFR-3 | Inventory data is stored securely and synced across sessions. |

#### Use Case (+ Edges) BDD 2

| Field | Value |
| --- | --- |
| Field | Recommendation flow |
| Use Case ID | UC-1.2 |
| Given | The user has an inventory with at least one item nearing expiry. |
| When | The user requests meal suggestions or taps a use-soon alert. |
| Then | FridgeFriend returns ranked meals that maximize use of expiring ingredients and explain any missing items or substitutions. |
| Input | Inventory items; dietary preferences; servings; available cooking time |
| Output | Ranked recipe cards with use-soon score, substitution suggestions, and missing-ingredient list |
| State | Recommendation session saved for analytics and later reopening |

#### Functional Requirements

| Req ID | Requirement |
| --- | --- |
| FR-4 | Rank meals by expiry urgency, ingredient coverage, prep time, and dietary fit. |
| FR-5 | Show substitutions and the minimum missing-ingredient list for each recipe. |

#### Non-Functional Requirements

| Req ID | Requirement |
| --- | --- |
| NFR-4 | Recipe recommendations are generated in under 5 seconds for a normal household inventory. |
| NFR-5 | Recommendation service maintains 99.5% availability with monitored fallback behavior. |

### User Story 2

| Field | Value |
| --- | --- |
| Role | Budget-conscious planner |
| User Story ID | US-2 |
| User Story | As a budget-conscious cook, I want to see what will expire soon and generate a weekly plan, so that I can reduce waste and avoid unnecessary grocery trips. |
| UX / User Flow | Daily reminder -> expiry dashboard -> inspect use-today / use-this-week groups -> choose plan length -> generate weekly plan -> review shopping gaps |

#### Use Case BDD 1

| Field | Value |
| --- | --- |
| Use Case ID | UC-2.1 |
| Given | Inventory items already have estimated expiry dates and notification preferences are configured. |
| When | The user opens the expiry dashboard or receives a scheduled reminder. |
| Then | The app groups items by urgency and recommends what to use today versus later in the week. |
| Input | Inventory, expiry dates, notification settings, and recent usage history |
| Output | Dashboard sections for Use Today, Use This Week, and Safe Later with recommended next actions |
| State | Alert history updated; item urgency state recalculated |

#### Functional Requirements

| Req ID | Requirement |
| --- | --- |
| FR-6 | Group items into urgency buckets based on time-to-expiry and storage type. |
| FR-7 | Send configurable push reminders for expiring items. |
| FR-8 | Allow users to mark items as used, discarded, or frozen. |

#### Non-Functional Requirements

| Req ID | Requirement |
| --- | --- |
| NFR-6 | Scheduled reminders are delivered within one minute of the target time. |
| NFR-7 | Dashboard loads in under 2 seconds for households with up to 500 tracked items. |

#### Use Case (+ Edges) BDD 2

| Field | Value |
| --- | --- |
| Field | Planning flow |
| Use Case ID | UC-2.2 |
| Given | The user has a current inventory, serving preferences, and a target number of meals for the week. |
| When | The user requests a 3-7 day meal plan. |
| Then | FridgeFriend creates a weekly plan that uses on-hand food first and produces a minimal shopping list for gaps. |
| Input | Inventory; servings; dietary preferences; time budget; excluded ingredients; planning horizon |
| Output | Meal plan by day; reserved ingredients; shopping list; estimated waste reduction |
| State | Plan saved and linked to reserved inventory quantities |

#### Functional Requirements

| Req ID | Requirement |
| --- | --- |
| FR-9 | Generate 3-7 day meal plans that prioritize on-hand and near-expiry ingredients. |
| FR-10 | Reserve planned ingredients and create a shopping list for missing items only. |

#### Non-Functional Requirements

| Req ID | Requirement |
| --- | --- |
| NFR-8 | Meal plan generation completes in under 8 seconds for a standard household. |
| NFR-9 | Users can edit servings or swap meals and regenerate without losing saved data. |

### User Story 3

| Field | Value |
| --- | --- |
| User Story ID | US-3 |
| User Story | As a roommate or family member, I want a shared inventory that updates when someone uses an item, so that we coordinate meals and purchases without confusion. |
| UX / User Flow | Invite household member -> join shared kitchen -> update quantity / mark item used -> sync to all devices -> view activity log |

#### Use Case (+ Edges) BDD 1

| Field | Value |
| --- | --- |
| Use Case ID | UC-3.1 |
| Given | Multiple household members share the same kitchen inventory. |
| When | One member edits quantity, marks an item used, or adds a new item. |
| Then | All household members see the updated inventory and a short activity log. |
| Input | Item update event; user ID; household ID; device timestamp |
| Output | Synced inventory, change confirmation, and activity feed entry |
| State | Versioned inventory event recorded; household sync timestamp updated |

#### Functional Requirements

| Req ID | Requirement |
| --- | --- |
| FR-11 | Support shared household accounts with item-level add, edit, and consume actions. |
| FR-12 | Maintain an activity log with conflict handling and basic undo for recent changes. |

#### Non-Functional Requirements

| Req ID | Requirement |
| --- | --- |
| NFR-10 | Changes sync across devices within 5 seconds under normal network conditions. |
| NFR-11 | Authentication and authorization protect household data and member roles. |

## 3. Architecture / Solution

### 3.1 Client Side

| Field | Value |
| --- | --- |
| Area | Mobile experience and interaction layer |
| Client Type | Mobile app built with Flutter 3.24 (Dart) for iOS and Android; optional lightweight admin/support web app in Next.js 14 + TypeScript. |
| User Entry Points | Onboarding; inventory capture; expiry dashboard; use-soon alerts; recipe suggestions; weekly plan; shopping list; household sharing. |
| Main Screens / Commands | Screens: Sign in, Home Inventory, Add Item, Barcode Scan, Photo Upload, OCR Review, Use Soon, Recipe Feed, Recipe Detail, Weekly Plan, Shopping List, Household, Settings. Client state via Riverpod; offline-first local cache with Drift (SQLite). |
| Input / Output Format | Input: text, barcode, photo, quantity, preferences, time budget.<br>Output: normalized inventory, expiry alerts, ranked recipes, meal plan, shopping list. |

### 3.2 Backend Services

| Field | Value |
| --- | --- |
| Area | Core application services |
| Service Name | API Gateway + Auth Service, Inventory Service, Catalog/Normalization Service, Expiry Service, Recommendation Service, Meal Planning Service, Notification Service, Household Sync Service, Analytics Event Collector. |
| Responsibility | Inventory Service stores item state and quantities. Catalog Service maps barcode/photo/manual input to canonical ingredients. Expiry Service estimates shelf life from storage rules. Recommendation Service ranks recipes and substitutions. Meal Planning Service reserves ingredients and creates shopping lists. Notification Service schedules push alerts. Household Sync handles shared edits and activity feed. |
| Business Logic | Auth: Firebase Authentication (email, Apple, Google) issuing JWTs. API layer: FastAPI (Python 3.12) behind API Gateway. Inventory + household domain persisted in PostgreSQL 16 via SQLAlchemy. Background jobs via Celery + Redis. Image pipeline: upload photo to S3, run OCR/object detection, normalize candidates, return editable draft. Recommendation engine uses hybrid retrieval + rules scoring: OpenSearch candidate retrieval, then Python ranker scoring expiry urgency, ingredient coverage, dietary fit, prep time, and missing-item penalty. Meal plans built by greedy optimizer with constraint checks. |
| API / Contract | Primary API: REST/JSON over HTTPS. Internal async events over Amazon SQS. WebSocket/SSE channel for household activity updates. Versioned endpoints: /v1/items, /v1/scan/barcode, /v1/scan/photo, /v1/recommendations, /v1/plans, /v1/shopping-list, /v1/households, /v1/notifications. |
| Request Schema | POST /v1/items {householdId, source:"manual", itemName, quantity, unit, storageLocation}<br>POST /v1/scan/barcode {householdId, barcode, quantity, storageLocation}<br>POST /v1/scan/photo {householdId, imageUrl, locale}<br>POST /v1/recommendations {householdId, servings, dietaryTags[], maxPrepMinutes, excludedIngredients[]}<br>POST /v1/plans {householdId, days, servings, dietaryTags[], maxPrepMinutes} |
| Response Schema | 201 Created {itemId, canonicalIngredientId, displayName, quantity, unit, storageLocation, estimatedExpiryDate, confidence}<br>200 OK {draftItems:[...]}<br>200 OK {recipes:[{id,title,useSoonScore,coveragePct,missingItems[],substitutions[],prepMinutes}]}<br>200 OK {plan:{days:[{date,recipeId,servings,reservedItems[]}], shoppingList:[...]}} |
| Error Handling | FastAPI validates request schema with Pydantic. Barcode/photo parse failures return partial editable drafts instead of hard failures. All write endpoints use idempotency keys. Errors are logged to Sentry with correlation IDs. Dead-letter queues catch failed async jobs. Circuit breaker falls back to text-only/manual entry when image model latency or confidence is poor. |

### 3.3 Data Architecture and Flows

| Field | Value |
| --- | --- |
| Area | Canonical food inventory and recommendation model |
| Main Entities (ER) | User, Household, HouseholdMember, InventoryItem, InventoryEvent, CanonicalIngredient, ProductBarcode, ShelfLifeRule, Recipe, RecipeIngredient, RecommendationSession, MealPlan, MealPlanDay, ReservedIngredient, ShoppingListItem, NotificationPreference, DeviceToken, AnalyticsEvent. |
| Relationships (ER) | Household 1..* HouseholdMembers and InventoryItems. InventoryItem *..1 CanonicalIngredient. ProductBarcode *..1 CanonicalIngredient. CanonicalIngredient 1..* ShelfLifeRule by storage type. Recipe *..* CanonicalIngredient via RecipeIngredient. MealPlan 1..* MealPlanDay and *..* InventoryItem via ReservedIngredient. RecommendationSession belongs to Household and references Recipes shown. |
| Data Flow (DFD) | 1) Capture input in app (manual/barcode/photo). 2) API stores raw request and emits normalization job. 3) Catalog/Normalization maps to canonical ingredients. 4) Expiry Service computes estimated expiry + urgency bucket. 5) Inventory persisted to PostgreSQL and cached in Redis. 6) Recommendation request retrieves candidate recipes from OpenSearch, ranks them in Recommendation Service, and returns cards. 7) Meal planner reserves quantities and generates shopping gaps. 8) Notification jobs read urgency bucket and send push via Firebase Cloud Messaging/APNs. |
| Input Sources | Open Food Facts / UPC item metadata for barcode lookup; curated recipe corpus from Spoonacular or Edamam plus internally stored recipes; shelf-life rule table maintained by ops/nutrition advisor; user-uploaded photos; manual entries; Firebase push tokens; optional grocery receipt import from email/photo in later phase. |

### 3.4 Infrastructure

| Field | Value |
| --- | --- |
| Required Hardware / Resources | AWS us-east-1. ECS Fargate for FastAPI services, Celery workers for async jobs, RDS PostgreSQL 16, ElastiCache Redis, S3 for image/object storage, OpenSearch for recipe retrieval, Amazon SQS for job queues, CloudFront CDN, Firebase Cloud Messaging/APNs for push, Amplitude for product analytics, Sentry + CloudWatch for observability. |
| ML / Models | Photo ingestion: GPT-4.1-mini or Google Gemini 1.5 Flash for multimodal item extraction from fridge photos; barcode fallback via Open Food Facts lookup; OCR with Apple Vision (on-device iOS) / ML Kit (Android) where available. Recommendation ranking starts rules-based; v2 can add LightGBM learning-to-rank using click/save/cook labels. |
| Frameworks / Libraries | Flutter 3.24, Riverpod, Drift, Dio; FastAPI, Pydantic v2, SQLAlchemy 2.x, Celery, Redis, OpenSearch Python client; Terraform for infra-as-code; GitHub Actions for CI/CD. |
| Security / Privacy | JWT-based auth via Firebase Auth, HTTPS everywhere, encrypted S3 buckets, RDS encryption at rest, least-privilege IAM, household-level authorization checks, signed upload URLs, GDPR/CCPA deletion workflow, and no training on user photos by default. |
| Monitoring / SLOs | 99.5% API availability target. P95 latency goals: item create < 3s, recommendation < 5s, meal plan < 8s. Monitor queue depth, model latency, parse confidence, push delivery success, and crash-free sessions via Sentry/Crashlytics/CloudWatch dashboards. |

## 4. Work Plan

### Mapping: Use Case → Tasks

| Use Case | Task ID | Task | Dependencies | DoD | Subtasks |
| --- | --- | --- | --- | --- | --- |
| UC-1.1 | T-1 | Build inventory capture and normalization flow | - | Users can add items manually, by barcode, or by photo and see normalized inventory with expiry dates. | ST-1, ST-2, ST-3 |
| UC-1.2 | T-2 | Build use-soon recipe recommendation engine | T-1 | Ranked recipe suggestions are returned from on-hand inventory with substitutions and missing-item guidance. | ST-4, ST-5 |
| UC-2.1 | T-3 | Build expiry dashboard and reminder system | T-1 | Dashboard shows urgency buckets and notifications fire on schedule. | ST-6, ST-7, ST-8 |
| UC-2.2 | T-4 | Build weekly meal planner and shopping list | T-1, T-2, T-3 | Users can generate and edit a 3-7 day plan plus a minimal grocery list for missing items. | ST-9, ST-10 |
| UC-3.1 | T-5 | Build shared household sync and analytics | T-1 | Shared inventory updates sync across devices and key adoption / waste metrics are tracked. | ST-11, ST-12 |

## 5. Detailed Task Breakdown

### Task 1

| Field | Value |
| --- | --- |
| Field | Task details |
| Task ID | T-1 |
| Related Use Case | UC-1.1 |
| Task Description | Implement item capture via manual entry, barcode scan, and fridge photo; normalize names and units; estimate expiry. |
| Dependencies | - |
| DoD | Inventory item can be created from all three input methods with canonical ingredient, quantity, storage location, expiry date, and confidence score. |
| Acceptance Criteria | Users can save common items successfully; duplicate items can be merged; edited items persist across app restart and account sync. |

#### Subtasks

| Subtask ID | Description | Dependencies | Acceptance Criteria |
| --- | --- | --- | --- |
| ST-1 | Build item schema and inventory CRUD API | - | API supports create, update, consume, discard, and archive actions. |
| ST-2 | Integrate barcode/manual entry and validation | ST-1 | User can add common groceries in under 30 seconds and correct parsed fields. |
| ST-3 | Integrate image ingestion and normalization / expiry estimation | ST-1 | Photo flow returns parsed items with confidence and editable fields. |

### Task 2

| Field | Value |
| --- | --- |
| Field | Task details |
| Task ID | T-2 |
| Related Use Case | UC-1.2 |
| Task Description | Generate ranked recipe suggestions that prioritize expiring items while respecting dietary and time preferences. |
| Dependencies | T-1 |
| DoD | Recommendation API returns at least 10 ranked meal ideas with use-soon score, substitutions, and missing-item list. |
| Acceptance Criteria | Suggestions return in under 5 seconds for standard inventories, with acceptable pilot-user relevance and graceful fallback when matches are weak. |

#### Subtasks

| Subtask ID | Description | Dependencies | Acceptance Criteria |
| --- | --- | --- | --- |
| ST-4 | Build recipe ingest/index and ingredient matching | T-1 | Recipes are searchable by ingredient, dietary tags, prep time, and cuisine. |
| ST-5 | Implement ranking, substitutions, and recommendation UI | ST-4 | Top recommendations use expiring items and show missing ingredients clearly. |

### Task 3

| Field | Value |
| --- | --- |
| Field | Task details |
| Task ID | T-3 |
| Related Use Case | UC-2.1 |
| Task Description | Create expiry dashboard and notification jobs for items nearing expiration. |
| Dependencies | T-1 |
| DoD | Dashboard groups items by urgency and scheduled push reminders are sent based on user settings. |
| Acceptance Criteria | Users can mark items used, discarded, or frozen; reminder timing is configurable; dashboard loads quickly for normal accounts. |

#### Subtasks

| Subtask ID | Description | Dependencies | Acceptance Criteria |
| --- | --- | --- | --- |
| ST-6 | Build urgency scoring and dashboard API | T-1 | Items are bucketed into Today, This Week, and Safe Later based on shelf-life rules. |
| ST-7 | Implement push notification preferences and scheduler | ST-6 | Test reminders are delivered correctly and can be turned on/off per household. |
| ST-8 | Add item state changes for used / discarded / frozen | ST-6 | Inventory, dashboard, and analytics update correctly after status changes. |

### Task 4

| Field | Value |
| --- | --- |
| Field | Task details |
| Task ID | T-4 |
| Related Use Case | UC-2.2 |
| Task Description | Generate weekly meal plans and minimal shopping lists from current inventory. |
| Dependencies | T-1, T-2, T-3 |
| DoD | User can generate, edit, and save a 3-7 day plan plus a missing-ingredient list. |
| Acceptance Criteria | Plan favors use-soon items; shopping list contains only required gaps; changing servings regenerates results correctly. |

#### Subtasks

| Subtask ID | Description | Dependencies | Acceptance Criteria |
| --- | --- | --- | --- |
| ST-9 | Build meal-planning algorithm and inventory reservation logic | T-2, T-3 | Generated plans use on-hand items first and reserve quantities against future meals. |
| ST-10 | Build shopping-list generation and editable plan UI | ST-9 | Users can swap meals, adjust servings, and export or share the list. |

### Task 5

| Field | Value |
| --- | --- |
| Field | Task details |
| Task ID | T-5 |
| Related Use Case | UC-3.1 |
| Task Description | Enable shared household inventory, conflict handling, and analytics instrumentation. |
| Dependencies | T-1 |
| DoD | Multiple users can share a household inventory with near-real-time sync and an activity log. |
| Acceptance Criteria | Changes sync within 5 seconds, users can see who changed what, and product metrics for activation and waste reduction are captured. |

#### Subtasks

| Subtask ID | Description | Dependencies | Acceptance Criteria |
| --- | --- | --- | --- |
| ST-11 | Build household membership, auth roles, and sync/event model | T-1 | Invited users can join a household, update inventory, and see recent activity. |
| ST-12 | Instrument analytics dashboards for activation, saves, and waste-reduction proxy metrics | ST-11 | Core funnel and outcome events are available in the BI tool. |

## Current API Contract

This Markdown table is the source used by backend contract tests.

<!-- api-contract:start -->
| Method | Path | Purpose |
| --- | --- | --- |
| POST | /v1/items | Create an inventory item |
| GET | /v1/items | List inventory items |
| GET | /v1/items/{item_id} | Read an inventory item |
| PATCH | /v1/items/{item_id} | Partially update an inventory item |
| PUT | /v1/items/{item_id} | Replace an inventory item |
| DELETE | /v1/items/{item_id} | Delete an inventory item |
| POST | /v1/items/{item_id}/status | Mark item used, discarded, frozen, or active |
| POST | /v1/items/{item_id}/undo | Undo a recent inventory change |
| POST | /v1/scan/barcode | Resolve barcode input into an editable product draft |
| POST | /v1/scan/photo | Parse a fridge photo into editable draft items |
| POST | /v1/scan/photo/upload | Create a signed upload target for photo scanning |
| POST | /v1/recommendations | Return ranked recipe recommendations |
| GET | /v1/recipes/{recipe_id} | Read recipe details |
| POST | /v1/plans | Generate a meal plan and reserve ingredients |
| GET | /v1/plans/latest | Read the latest saved meal plan |
| GET | /v1/shopping-list | Compute shopping gaps from the active plan |
| DELETE | /v1/plans/{plan_id} | Delete a saved meal plan |
| GET | /v1/households | List households for the authenticated user |
| POST | /v1/households | Create a household |
| GET | /v1/households/{household_id} | Read household details |
| PATCH | /v1/households/{household_id} | Update household details |
| POST | /v1/households/join | Join a household by invite code |
| POST | /v1/households/{household_id}/leave | Leave a household |
| DELETE | /v1/households/{household_id}/members/{user_id} | Remove a household member |
| GET | /v1/households/{household_id}/events | Stream household events |
| GET | /v1/households/{household_id}/activity | Read household activity log |
| GET | /v1/notifications | Read notification preferences |
| PATCH | /v1/notifications | Update notification preferences |
| POST | /v1/notifications/devices | Register a push notification device token |
| DELETE | /v1/notifications/devices/{token_id} | Unregister a push notification device token |
| POST | /v1/analytics/events | Collect product analytics events |
| GET | /health | Service health check |
<!-- api-contract:end -->
