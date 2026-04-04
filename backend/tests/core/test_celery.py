from __future__ import annotations

from app.core.celery_app import EXPIRY_REMINDER_TASK_NAME, celery_app
from app.core.config import settings
from app.modules.notifications import tasks as notification_tasks


def test_celery_app_configured() -> None:
    if celery_app is None:
        assert celery_app is None
        return

    assert celery_app.main == "fridgefriend"
    assert celery_app.conf.broker_url == settings.REDIS_URL


def test_task_registration() -> None:
    _ = notification_tasks
    if celery_app is None:
        assert celery_app is None
        return

    registered_task_names = set(celery_app.tasks.keys())
    assert EXPIRY_REMINDER_TASK_NAME in registered_task_names
