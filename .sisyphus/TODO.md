# FridgeFriend — Remaining Work

## Production Hardening

- [ ] **Firebase Auth — real auth**: Switch `AUTH_MOCK=false`, configure Firebase project, populate `firebase-credentials` secret. Currently all API calls use a test token.
- [ ] **DB migrations (Alembic)**: `create_all()` only creates new tables, can't alter existing. Need Alembic before any schema changes.
- [ ] **Recipe data source**: `RECIPE_SOURCE=mock` in production. Plug in Spoonacular/Edamam API key or seed internal corpus.
- [ ] **Photo parser**: `PHOTO_PARSER_BACKEND=mock`. Wire GPT-4.1-mini or Gemini 1.5 Flash for real fridge photo parsing.
- [ ] **OpenSearch**: Not provisioned (URL empty). Needed for recipe candidate retrieval at scale.
- [ ] **Populate remaining secrets**: `firebase-credentials`, `spoonacular-api-key`, `sentry-dsn`, `amplitude-api-key`.
- [ ] **CI/CD pipeline**: GitHub Actions template exists but not fully wired for automated ECR push + ECS deploy on merge.
- [ ] **Flutter production build**: Build with production API URL, publish to App Store / Play Store.
- [ ] **Cost optimization**: 4 Fargate services + NAT + RDS + Redis ≈ $100-150/mo. Scale worker/beat to 0 when idle.
