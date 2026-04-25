## Prerequisites

- AWS account with ECS, RDS, ElastiCache, S3, ECR, Secrets Manager configured
- Firebase project with credentials JSON file
- Spoonacular API key
- Sentry DSN (optional but recommended)
- Amplitude API key (optional)
- Docker + AWS CLI installed locally

> **Cost notes:** Production stack runs at **~$78/mo** of pre-credit AWS usage (post-2026-04-25 optimizations: Container Insights off, backend right-sized to 256/512, dashboard stopped, log retention 7d). An AWS Budget named `fridgefriend-monthly` is configured at $30/mo with email alerts at 80/100/120% — alerts fire on real usage even while promotional credits absorb the bill. See [`docs/aws-cost-analysis.md`](docs/aws-cost-analysis.md) for the full breakdown and remaining optimization opportunities.

## Pre-flight Checklist

- [ ] All environment variables in `.env.production` are set with real values
- [ ] Firebase credentials JSON uploaded to AWS Secrets Manager
- [ ] RDS PostgreSQL 16 instance is running and accessible
- [ ] ElastiCache Redis cluster is running and accessible
- [ ] S3 bucket created with CORS policy for signed URLs
- [ ] ECR repositories created: `fridgefriend-backend`, `fridgefriend-dashboard`
- [ ] ECS cluster created with Fargate capacity provider
- [ ] ALB configured with target groups for backend (8000) and dashboard (8501)
- [ ] Security groups: backend → RDS (5432), backend → Redis (6379), ALB → backend (8000)
- [ ] All 261 backend tests pass locally
- [ ] All 44 Flutter tests pass locally

## Database Migrations (Alembic)

Schema changes ship via [Alembic](https://alembic.sqlalchemy.org/). The application no longer creates tables on startup against PostgreSQL — `alembic upgrade head` is the only supported way to evolve production schema.

### Local workflow

Generate a new revision after editing `app/models/`:

```bash
cd backend
docker compose -f ../docker-compose.yml up -d db
source .venv/bin/activate

# Autogenerate against an empty database to capture only your changes.
docker exec ailab_project-db-1 psql -U fridgefriend -d postgres \
  -c "DROP DATABASE IF EXISTS alembic_scratch;" \
  -c "CREATE DATABASE alembic_scratch OWNER fridgefriend;"

DATABASE_URL="postgresql+asyncpg://fridgefriend:fridgefriend@localhost:5432/alembic_scratch" \
  alembic upgrade head

DATABASE_URL="postgresql+asyncpg://fridgefriend:fridgefriend@localhost:5432/alembic_scratch" \
  alembic revision --autogenerate -m "<short slug>"
```

Inspect the generated `alembic/versions/<timestamp>_<slug>.py`. Autogenerate has known blind spots — most notably it does **not** drop PostgreSQL `ENUM` types when their owning tables are dropped. Patch the `downgrade()` with explicit `DROP TYPE IF EXISTS <name>` calls when tables containing `sa.Enum(...)` are removed (see `20260425_0943-9c891418bc24_initial_schema.py` for the pattern).

Verify the round-trip before committing:

```bash
DATABASE_URL="postgresql+asyncpg://fridgefriend:fridgefriend@localhost:5432/alembic_scratch" \
  alembic downgrade base

DATABASE_URL="postgresql+asyncpg://fridgefriend:fridgefriend@localhost:5432/alembic_scratch" \
  alembic upgrade head

DATABASE_URL="postgresql+asyncpg://fridgefriend:fridgefriend@localhost:5432/alembic_scratch" \
  alembic check          # must report "No new upgrade operations detected."
```

### Tests

Tests use SQLite in-memory and bootstrap the schema via `Base.metadata.create_all()` — Alembic is intentionally **not** in the test path. The lifespan in `app/main.py` only invokes `create_all()` when `DATABASE_URL` contains `sqlite`; PostgreSQL deployments rely entirely on Alembic.

### First-time bootstrap of an existing database

The production database was originally created via `Base.metadata.create_all()`, so its schema already matches the initial Alembic revision but `alembic_version` is empty. After deploying the first version of the backend that ships Alembic, mark the initial revision as applied without re-running it:

```bash
# One-shot, run by an operator with RDS access. NEVER run alembic upgrade head
# against a database that was created with create_all() and has not been stamped.
aws ecs run-task \
  --cluster fridgefriend-production-cluster \
  --launch-type FARGATE \
  --task-definition fridgefriend-production-backend \
  --overrides '{"containerOverrides":[{"name":"backend","command":["alembic","stamp","head"]}]}' \
  --network-configuration "$(aws ecs describe-services \
      --cluster fridgefriend-production-cluster \
      --services fridgefriend-production-backend \
      --query 'services[0].networkConfiguration')"
```

After the stamp completes, every subsequent push to `main` runs `alembic upgrade head` automatically (see below).

### CI/CD

`.github/workflows/deploy.yml` runs migrations as a dedicated `migrate` job between `build-and-push` and `deploy-backend`/`deploy-worker`. The job:

1. Clones the latest `fridgefriend-production-backend` task definition.
2. Overrides the container command to `["alembic","upgrade","head"]` and registers it under family `fridgefriend-production-migrate`.
3. Reuses the backend service's VPC/subnet/security-group config so the task can reach RDS over the private network.
4. Runs the task with `aws ecs run-task`, waits for `tasks-stopped`, and fails the build on a non-zero container exit code.

Migration logs land in the `/ecs/fridgefriend/production/backend` log group (the cloned task inherits the backend service's `awslogs` config) — search for the migration task ARN to find them.

If a migration fails, `deploy-backend` and `deploy-worker` are not started, leaving the previous image serving traffic. Fix the migration on a branch, push to `main`, and the deploy retries from the migrate step.

## Deployment Steps

1. Build and push Docker images to ECR.
2. Run `alembic upgrade head` as a one-shot ECS task (handled automatically by `migrate` job in `deploy.yml`).
3. Update ECS task definitions with new image tags.
4. Deploy ECS services using a rolling update strategy (`maximumPercent=200`, `minimumHealthyPercent=100`).
5. Verify health checks pass for `/health` and `/health/ready`.
6. Run smoke tests against the production ALB or service DNS.
7. Monitor Sentry and CloudWatch for errors, latency regressions, and failed background jobs.

## Rollback Procedure

1. Update each ECS service to the previous task definition revision.
2. If the rolled-back image predates a recent migration, run `alembic downgrade -1` against production via a one-shot task before flipping traffic. Be cautious — destructive downgrades (dropped columns/tables) lose data; prefer rolling forward with a fix.
3. Verify health checks and smoke tests return to normal.
4. Investigate the root cause before attempting another deployment.

## Environment Variable Reference

| Name | Required | Description | Example value |
| --- | --- | --- | --- |
| `APP_NAME` | Required | API/application name exposed in logs and health metadata. | `FridgeFriend` |
| `VERSION` | Required | Release version string for the deployed build. | `0.1.0` |
| `DEBUG` | Required | Must remain disabled in production. | `false` |
| `APP_ENV` | Required | Logical environment label for runtime/configuration grouping. | `production` |
| `DB_USER` | Required | PostgreSQL username for the production database. | `fridgefriend` |
| `DB_PASSWORD` | Required | PostgreSQL password loaded from Secrets Manager. | `${DB_PASSWORD}` |
| `DB_NAME` | Required | PostgreSQL database name. | `fridgefriend` |
| `DB_PORT` | Required | PostgreSQL port number. | `5432` |
| `RDS_ENDPOINT` | Required | RDS writer endpoint hostname. | `fridgefriend-prod.cluster-xxxx.us-east-1.rds.amazonaws.com` |
| `DATABASE_URL` | Required | Async SQLAlchemy connection string consumed by backend services. | `postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/fridgefriend` |
| `ELASTICACHE_ENDPOINT` | Required | Redis primary endpoint for ElastiCache. | `fridgefriend-prod.xxxxxx.use1.cache.amazonaws.com` |
| `REDIS_URL` | Required | Shared Redis URL used by cache and workers. | `redis://${ELASTICACHE_ENDPOINT}:6379/0` |
| `CELERY_BROKER_URL` | Optional | Explicit broker URL if Celery should not infer it from `REDIS_URL`. | `${REDIS_URL}` |
| `CELERY_RESULT_BACKEND` | Optional | Explicit Celery result backend URL. | `${REDIS_URL}` |
| `IDEMPOTENCY_BACKEND` | Required | Backend used to persist idempotency keys. | `redis` |
| `IDEMPOTENCY_TTL_SECONDS` | Required | Time-to-live for idempotency entries. | `86400` |
| `AUTH_MOCK` | Required | Must stay disabled for real auth validation. | `false` |
| `FIREBASE_PROJECT_ID` | Required | Firebase project used for JWT verification. | `fridgefriend-prod` |
| `FIREBASE_CREDENTIALS_PATH` | Required | Mounted path to the Firebase credentials JSON file. | `/run/secrets/firebase-credentials.json` |
| `FCM_ENABLED` | Required | Enables push notification delivery via FCM/APNs. | `true` |
| `STORAGE_BACKEND` | Required | Selects Amazon S3 storage implementation. | `s3` |
| `S3_ENDPOINT_URL` | Required | AWS S3 regional endpoint URL. | `https://s3.us-east-1.amazonaws.com` |
| `S3_BUCKET` | Required | Bucket for uploaded fridge photos and generated assets. | `fridgefriend-uploads-prod` |
| `AWS_REGION` | Required | AWS region hosting FridgeFriend production resources. | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | Optional | Access key for local production-like docker-compose runs only. | `${AWS_ACCESS_KEY_ID}` |
| `AWS_SECRET_ACCESS_KEY` | Optional | Secret key for local production-like docker-compose runs only. | `${AWS_SECRET_ACCESS_KEY}` |
| `PHOTO_PARSER_BACKEND` | Required | Enables LLM-driven photo parsing. | `llm` |
| `LLM_API_URL` | Required | Base URL for the LiteLLM or model gateway. | `https://litellm.labs.jb.gg` |
| `LLM_MODEL` | Required | Model name used for fridge photo parsing. | `gpt-4.1-mini` |
| `LLM_API_KEY` | Optional | API key if the LLM endpoint requires explicit authentication. | `${LLM_API_KEY}` |
| `RECIPE_SOURCE` | Required | Recipe provider used for recommendations. | `spoonacular` |
| `SPOONACULAR_API_KEY` | Required | API key for Spoonacular requests. | `${SPOONACULAR_API_KEY}` |
| `BARCODE_API_SOURCE` | Required | Barcode catalog provider. | `openfoodfacts` |
| `SENTRY_DSN` | Optional | Sentry DSN for errors and distributed tracing. | `${SENTRY_DSN}` |
| `SENTRY_ENVIRONMENT` | Required | Environment label attached to Sentry events. | `production` |
| `SENTRY_TRACES_SAMPLE_RATE` | Required | Tracing sample rate for production traffic. | `0.1` |
| `AMPLITUDE_API_KEY` | Optional | API key for analytics event ingestion. | `${AMPLITUDE_API_KEY}` |
| `LLM_INPUT_COST_PER_1M` | Required | Input token unit-cost estimate for economics reporting. | `0.40` |
| `LLM_OUTPUT_COST_PER_1M` | Required | Output token unit-cost estimate for economics reporting. | `1.60` |
| `SPOONACULAR_POINT_COST` | Required | Estimated cost of one Spoonacular billing point. | `0.005` |
| `ECR_REGISTRY` | Required | Fully qualified ECR registry that stores deployable images. | `123456789012.dkr.ecr.us-east-1.amazonaws.com` |
| `IMAGE_TAG` | Required | Image tag promoted to ECS and docker-compose deployments. | `latest` |
| `ECS_CLUSTER` | Required | Target ECS cluster name. | `fridgefriend-prod` |
| `ECS_BACKEND_SERVICE` | Required | ECS service name for the backend/API task set. | `fridgefriend-backend` |
| `ECS_DASHBOARD_SERVICE` | Required | ECS service name for the dashboard task set. | `fridgefriend-dashboard` |
| `ECS_BACKEND_TASK_FAMILY` | Required | ECS task definition family for backend services. | `fridgefriend-backend` |
| `ECS_DASHBOARD_TASK_FAMILY` | Required | ECS task definition family for dashboard services. | `fridgefriend-dashboard` |
| `DASHBOARD_BASE_URL` | Optional | Public dashboard URL used in smoke tests and operator docs. | `https://dashboard.fridgefriend.app` |

## Smoke Tests

Export a temporary token and base URL before running smoke tests:

```bash
export BASE_URL="https://api.fridgefriend.app"
export AUTH_TOKEN="replace-with-valid-firebase-jwt"
```

### Health endpoint

```bash
curl -f "$BASE_URL/health"
```

### Inventory list

```bash
curl -f "$BASE_URL/v1/items" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

### Barcode draft lookup

```bash
curl -f -X POST "$BASE_URL/v1/scan/barcode" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: smoke-barcode-001" \
  -d '{"barcode":"012345678905","quantity":1,"unit":"item"}'
```

### Recommendations

```bash
curl -f -X POST "$BASE_URL/v1/recommendations" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"servings":2,"dietaryPreferences":[]}'
```

### Notification preferences

```bash
curl -f -X PATCH "$BASE_URL/v1/notifications" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: smoke-notifications-001" \
  -d '{"expiringSoonEnabled":true,"dailyDigestEnabled":true}'
```
