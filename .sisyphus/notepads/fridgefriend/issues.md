# FridgeFriend — Issues

## 2026-04-03 — P0-2 blocker resolved
- `pip install -e .[dev]` initially failed because zsh expands `.[dev]`; quoting as `'.[dev]'` is required.
- Older pydantic combinations attempted a rust build of `pydantic-core` and failed on Python 3.14 compatibility; resolved by pinning to versions with compatible binary wheels.

## 2026-04-03 — P1-4/P1-5 verification limitation
- `python3 -m pytest tests/ -v` is currently blocked by previously added red tests in `tests/modules/catalog/` and `tests/modules/inventory/` that import modules not yet implemented. Expiry verification therefore used `tests/test_health.py tests/test_models.py tests/modules/expiry/` to keep the existing 8 passing tests plus the new expiry suite green.

## 2026-04-03 — P1-2 typing/tooling note
- basedpyright in this environment reported false-positive unresolved imports for newly added package modules; runtime imports and tests were valid, so file-local pyright directives were added only where needed to keep changed-file diagnostics clean.

## 2026-04-03 — P1-3 typing/tooling note
- basedpyright again reported unresolved absolute imports for newly added module files and tests; adding backend-level path config plus targeted relative imports/dynamic test symbol loading kept changed-file diagnostics clean without changing runtime behavior.
