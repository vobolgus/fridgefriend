from __future__ import annotations

from typing import Protocol, cast

import google.auth.transport.requests
import google.oauth2.id_token


class FirebaseAuthInterface(Protocol):
    async def verify_token(self, token: str) -> dict[str, object]: ...


class MockFirebaseAuth:
    async def verify_token(self, token: str) -> dict[str, object]:
        if token == "expired":
            raise ValueError("Token expired")
        return {"uid": "firebase-test-uid", "email": "test@fridgefriend.app"}


_GOOGLE_TRANSPORT = google.auth.transport.requests.Request()

# Firebase ID tokens are signed by Google — verify against Google's public certs.
_FIREBASE_CERT_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"


class FirebaseAuthService:
    def __init__(self, project_id: str) -> None:
        self._project_id = project_id

    async def verify_token(self, token: str) -> dict[str, object]:
        try:
            decoded = google.oauth2.id_token.verify_firebase_token(
                token,
                _GOOGLE_TRANSPORT,
                audience=self._project_id,
            )
            if not isinstance(decoded, dict):
                raise ValueError("Invalid token payload")

            result = cast(dict[str, object], decoded)

            # Normalize: google.oauth2 uses "sub" for user ID, Firebase uses "uid"
            if "uid" not in result and "sub" in result:
                result["uid"] = result["sub"]

            return result
        except Exception as exc:
            raise ValueError(f"Invalid token: {exc}") from exc
