# FridgeFriend — Remaining Work

## ✅ Completed

- [x] **CI/CD pipeline**: deploy.yml fully wired, AWS credentials configured, deploys green.
- [x] **Cost optimization**: ~$120 → ~$51/mo (fck-nat, Fargate Spot, beat merged, S3 endpoint).
- [x] **Flutter iPhone fixes**: BoxConstraints infinite width, setState during build.
- [x] **GitHub Actions AWS credentials**: Configured and verified.
- [x] **Firebase Auth — live in production**: `AUTH_MOCK=false`, `FIREBASE_PROJECT_ID` set, service account in Secrets Manager. Real sign-in (email/Google/Apple) working end-to-end.
- [x] **Recipe seeding**: Fixture recipes seeded to DB on startup — meal plan generation works.
- [x] **User creation race condition**: Fixed retry-after-rollback in `_firebase_auth`.

## Blocked / Needs User Action

- [ ] **Apple Developer Program**: Purchased, pending activation (24-48h). Blocks: App Store submission.

## Production Hardening (remaining)

- [ ] **DB migrations (Alembic)**: `create_all()` only creates new tables, can't alter existing. Need Alembic before any schema changes.
- [ ] **Recipe data source**: `RECIPE_SOURCE=mock` in production. Plug in Spoonacular/Edamam API key or seed internal corpus.
- [ ] **Photo parser**: `PHOTO_PARSER_BACKEND=mock`. Wire GPT-4.1-mini or Gemini 1.5 Flash for real fridge photo parsing.
- [ ] **OpenSearch**: Not provisioned (URL empty). Needed for recipe candidate retrieval at scale.
- [ ] **Populate remaining secrets**: `spoonacular-api-key`, `sentry-dsn`, `amplitude-api-key`.
- [ ] **Flutter production build**: Publish to App Store / Play Store (needs ADP).
- [ ] **GitHub OIDC for CI/CD**: Replace access keys with OIDC for better security (deferred).

## Dev Workflow Note

- **Xcode 26.4 + Flutter CLI bug**: `flutter run` crashes on physical iOS with `EXC_BAD_ACCESS (code=50)`. Workaround: launch from Xcode (`Runner.xcworkspace` → Cmd+R). See [flutter#184254](https://github.com/flutter/flutter/issues/184254).
