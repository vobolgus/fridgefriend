from __future__ import annotations

import asyncio
import importlib
import json
import logging
import os
from collections.abc import Callable
from typing import Protocol, cast

from app.core.config import settings


class _FirebaseAdminModule(Protocol):
    def get_app(self) -> object: ...

    def initialize_app(self, credential: object) -> object: ...


class _CredentialsModule(Protocol):
    def Certificate(self, certificate_path: str) -> object: ...


class _MessagingModule(Protocol):
    UnregisteredError: type[Exception]
    Notification: Callable[..., object]
    Message: Callable[..., object]
    AndroidConfig: Callable[..., object]
    APNSConfig: Callable[..., object]
    APNSPayload: Callable[..., object]
    Aps: Callable[..., object]

    def send(self, message: object) -> str: ...


try:
    firebase_admin_module = cast(object, importlib.import_module("firebase_admin"))
    credentials_module = cast(object, importlib.import_module("firebase_admin.credentials"))
    messaging_module = cast(object, importlib.import_module("firebase_admin.messaging"))
    firebase_admin = cast(_FirebaseAdminModule | None, firebase_admin_module)
    credentials = cast(_CredentialsModule | None, credentials_module)
    messaging = cast(_MessagingModule | None, messaging_module)
    _firebase_import_error: ImportError | None = None
except ImportError as exc:
    firebase_admin = None
    credentials = None
    messaging = None
    _firebase_import_error = exc


logger = logging.getLogger(__name__)


class PushServiceInterface(Protocol):
    async def send(self, token: str, title: str, body: str) -> bool: ...


class MockPushService:
    async def send(self, token: str, title: str, body: str) -> bool:
        _ = (token, title, body)
        return True


_firebase_app_initialized = False


class FCMPushService:
    def _ensure_initialized(self) -> bool:
        global _firebase_app_initialized

        if _firebase_app_initialized:
            return True
        if firebase_admin is None or credentials is None or messaging is None:
            logger.warning("firebase_admin is unavailable; push notifications disabled")
            return False
        # Support JSON string credentials (ECS/Fargate) or file path (local dev).
        creds_json = os.environ.get("FIREBASE_CREDENTIALS_JSON", "")
        creds_path = settings.FIREBASE_CREDENTIALS_PATH
        if not creds_json and not creds_path:
            logger.warning("Firebase credentials missing; push notifications disabled")
            return False

        try:
            _ = firebase_admin.get_app()
        except ValueError:
            try:
                if creds_json:
                    credential = credentials.Certificate(json.loads(creds_json))
                else:
                    credential = credentials.Certificate(creds_path)
                _ = firebase_admin.initialize_app(credential)
            except Exception:
                logger.exception("Failed to initialize Firebase app")
                return False

        _firebase_app_initialized = True
        return True

    def _send_sync(self, token: str, title: str, body: str) -> bool:
        if not self._ensure_initialized():
            return False

        assert messaging is not None
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
            android=messaging.AndroidConfig(priority="high"),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(badge=1, sound="default"),
                ),
            ),
        )

        try:
            _ = messaging.send(message)
            return True
        except messaging.UnregisteredError:
            logger.info("FCM token is unregistered: %s", token)
            return False
        except Exception:
            logger.exception("Failed to send FCM push notification")
            return False

    async def send(self, token: str, title: str, body: str) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self._send_sync(token, title, body))
