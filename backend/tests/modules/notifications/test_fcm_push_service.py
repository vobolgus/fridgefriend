from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.household import Household, HouseholdMember, HouseholdRole
from app.models.inventory_item import InventoryItem, InventorySource, InventoryStatus
from app.models.notification import DeviceToken, NotificationPreference
from app.models.user import User
from app.modules.notifications import push as push_module
from app.modules.notifications import tasks as tasks_module


async def _seed_user_with_due_item(db_session: AsyncSession, email: str) -> None:
    user = User(email=email)
    db_session.add(user)
    await db_session.flush()

    household = Household(name=f"{email} household", invite_code=email.replace("@", "-")[:20])
    db_session.add(household)
    await db_session.flush()

    db_session.add(HouseholdMember(household_id=household.id, user_id=user.id, role=HouseholdRole.OWNER))
    db_session.add(
        NotificationPreference(
            user_id=user.id,
            expiry_reminder_enabled=True,
            reminder_days_before=1,
        ),
    )
    db_session.add(DeviceToken(user_id=user.id, token=f"token-{email}", platform="ios"))
    db_session.add(
        InventoryItem(
            user_id=user.id,
            household_id=household.id,
            display_name="Milk",
            quantity=1.0,
            unit="liter",
            storage_location="fridge",
            estimated_expiry_date=datetime(2026, 4, 5, tzinfo=UTC).date(),
            confidence=0.9,
            status=InventoryStatus.ACTIVE,
            source=InventorySource.MANUAL,
            canonical_name="milk",
        ),
    )
    await db_session.commit()


class FakeUnregisteredError(Exception):
    pass


class FakeFirebaseAdmin:
    def __init__(self) -> None:
        self._initialized: bool = False
        self.initialized_with: list[object] = []

    def get_app(self) -> object:
        if not self._initialized:
            raise ValueError("No app")
        return object()

    def initialize_app(self, credential: object) -> object:
        self._initialized = True
        self.initialized_with.append(credential)
        return object()


class FakeCredentials:
    def __init__(self) -> None:
        self.certificate_paths: list[str] = []

    def Certificate(self, certificate_path: str) -> object:
        self.certificate_paths.append(certificate_path)
        return {"certificate_path": certificate_path}


class FakeMessaging:
    UnregisteredError: type[Exception] = FakeUnregisteredError

    def __init__(self, *, send_side_effect: Exception | None = None) -> None:
        self.send_side_effect: Exception | None = send_side_effect
        self.last_notification: dict[str, str] | None = None
        self.last_android_config: dict[str, str] | None = None
        self.last_aps: dict[str, int | str] | None = None
        self.last_message: dict[str, object] | None = None
        self.sent_messages: list[object] = []

    def Notification(self, *, title: str, body: str) -> object:
        self.last_notification = {"title": title, "body": body}
        return self.last_notification

    def AndroidConfig(self, *, priority: str) -> object:
        self.last_android_config = {"priority": priority}
        return self.last_android_config

    def Aps(self, *, badge: int, sound: str) -> object:
        self.last_aps = {"badge": badge, "sound": sound}
        return self.last_aps

    def APNSPayload(self, *, aps: object) -> object:
        return {"aps": aps}

    def APNSConfig(self, *, payload: object) -> object:
        return {"payload": payload}

    def Message(
        self,
        *,
        notification: object,
        token: str,
        android: object,
        apns: object,
    ) -> object:
        self.last_message = {
            "notification": notification,
            "token": token,
            "android": android,
            "apns": apns,
        }
        return self.last_message

    def send(self, message: object) -> str:
        self.sent_messages.append(message)
        if self.send_side_effect is not None:
            raise self.send_side_effect
        return "message-id"


@pytest.mark.asyncio
async def test_fcm_send_success() -> None:
    firebase_admin = FakeFirebaseAdmin()
    credentials = FakeCredentials()
    messaging = FakeMessaging()

    with (
        patch.object(push_module, "firebase_admin", firebase_admin),
        patch.object(push_module, "credentials", credentials),
        patch.object(push_module, "messaging", messaging),
        patch.object(push_module, "_firebase_import_error", None),
        patch.object(push_module, "_firebase_app_initialized", False),
        patch.object(settings, "FIREBASE_CREDENTIALS_PATH", "/tmp/firebase.json"),
    ):
        result = await push_module.FCMPushService().send("device-token", "Use Soon", "Milk expires tomorrow")

    assert result is True
    assert credentials.certificate_paths == ["/tmp/firebase.json"]
    assert firebase_admin.initialized_with == [{"certificate_path": "/tmp/firebase.json"}]
    assert messaging.last_notification == {"title": "Use Soon", "body": "Milk expires tomorrow"}
    assert messaging.last_android_config == {"priority": "high"}
    assert messaging.last_aps == {"badge": 1, "sound": "default"}
    assert messaging.last_message is not None
    assert messaging.last_message["token"] == "device-token"
    assert len(messaging.sent_messages) == 1


@pytest.mark.asyncio
async def test_fcm_send_unregistered() -> None:
    firebase_admin = FakeFirebaseAdmin()
    credentials = FakeCredentials()
    messaging = FakeMessaging(send_side_effect=FakeUnregisteredError("stale token"))

    with (
        patch.object(push_module, "firebase_admin", firebase_admin),
        patch.object(push_module, "credentials", credentials),
        patch.object(push_module, "messaging", messaging),
        patch.object(push_module, "_firebase_import_error", None),
        patch.object(push_module, "_firebase_app_initialized", False),
        patch.object(settings, "FIREBASE_CREDENTIALS_PATH", "/tmp/firebase.json"),
    ):
        result = await push_module.FCMPushService().send("device-token", "Use Soon", "Milk expires tomorrow")

    assert result is False
    assert len(messaging.sent_messages) == 1


@pytest.mark.asyncio
async def test_fcm_send_generic_error() -> None:
    firebase_admin = FakeFirebaseAdmin()
    credentials = FakeCredentials()
    messaging = FakeMessaging(send_side_effect=RuntimeError("FCM unavailable"))

    with (
        patch.object(push_module, "firebase_admin", firebase_admin),
        patch.object(push_module, "credentials", credentials),
        patch.object(push_module, "messaging", messaging),
        patch.object(push_module, "_firebase_import_error", None),
        patch.object(push_module, "_firebase_app_initialized", False),
        patch.object(settings, "FIREBASE_CREDENTIALS_PATH", "/tmp/firebase.json"),
    ):
        result = await push_module.FCMPushService().send("device-token", "Use Soon", "Milk expires tomorrow")

    assert result is False
    assert len(messaging.sent_messages) == 1


@pytest.mark.asyncio
async def test_fcm_graceful_degradation_no_firebase() -> None:
    with (
        patch.object(push_module, "firebase_admin", None),
        patch.object(push_module, "credentials", None),
        patch.object(push_module, "messaging", None),
        patch.object(push_module, "_firebase_import_error", ImportError("firebase_admin missing")),
        patch.object(push_module, "_firebase_app_initialized", False),
    ):
        result = await push_module.FCMPushService().send("device-token", "Use Soon", "Milk expires tomorrow")

    assert result is False


@pytest.mark.asyncio
async def test_task_uses_mock_when_fcm_disabled(db_session: AsyncSession) -> None:
    await _seed_user_with_due_item(db_session, "mock-push@example.com")

    class RecordingService:
        def __init__(self) -> None:
            self.calls: int = 0

        async def send(self, token: str, title: str, body: str) -> bool:
            _ = (token, title, body)
            self.calls += 1
            return True

    class ServiceFactory:
        def __init__(self, service: RecordingService) -> None:
            self.service: RecordingService = service
            self.calls: int = 0

        def __call__(self) -> RecordingService:
            self.calls += 1
            return self.service

    mock_service = RecordingService()
    fcm_service = RecordingService()
    mock_push_service_factory = ServiceFactory(mock_service)
    fcm_push_service_factory = ServiceFactory(fcm_service)

    with (
        patch.object(settings, "FCM_ENABLED", False),
        patch.object(tasks_module, "MockPushService", mock_push_service_factory),
        patch.object(tasks_module, "FCMPushService", fcm_push_service_factory),
    ):
        sent_count = await tasks_module.send_expiry_reminders(
            session=db_session,
            now=datetime(2026, 4, 4, 9, 0, tzinfo=UTC),
        )

    assert sent_count == 1
    assert mock_push_service_factory.calls == 1
    assert fcm_push_service_factory.calls == 0
    assert mock_service.calls == 1
