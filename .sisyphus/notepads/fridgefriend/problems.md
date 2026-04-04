# FridgeFriend — Problems

## 2026-04-03 — P0-2 none
- No unresolved backend scaffold issues after health endpoint verification.

## 2026-04-03 — P1-4/P1-5 pending external blocker
- Full backend test sweep remains unresolved until the separately scoped catalog and inventory modules are implemented; no open problems remain inside the expiry domain itself.

## 2026-04-03 — P1-2 none
- No unresolved inventory API issues after green test run and push.

## 2026-04-03 — P1-3 none
- No unresolved catalog service issues after green test run and push.

## 2026-04-04 — Verification blockers
- Barcode idempotency is not actually functional because the cache write is unreachable in `backend/app/modules/catalog/router.py`; repeated requests with the same key will recompute instead of replaying a cached response.
- Idempotency regression coverage is incomplete: there is cross-endpoint isolation coverage, but no test proving same-key requests from different users stay isolated.
