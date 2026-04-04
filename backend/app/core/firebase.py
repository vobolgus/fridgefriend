from __future__ import annotations

import importlib
from typing import Protocol, cast


class FirebaseAuthInterface(Protocol):
    async def verify_token(self, token: str) -> dict[str, object]: ...


class _FirebaseAuthModule(Protocol):
    def verify_id_token(self, token: str) -> object: ...


class MockFirebaseAuth:
    async def verify_token(self, token: str) -> dict[str, object]:
        if token == "expired":
            raise ValueError("Token expired")
        return {"uid": "firebase-test-uid", "email": "test@fridgefriend.app"}


class FirebaseAuthService:
    def __init__(self, project_id: str) -> None:
        self._project_id: str = project_id

    async def verify_token(self, token: str) -> dict[str, object]:
        try:
            firebase_auth = cast(
                _FirebaseAuthModule,
                cast(object, importlib.import_module("firebase_admin.auth")),
            )
            decoded = firebase_auth.verify_id_token(token)
            if not isinstance(decoded, dict):
                raise ValueError("Invalid token payload")
            return cast(dict[str, object], decoded)
        except Exception as exc:
            raise ValueError(f"Invalid token: {exc}") from exc
