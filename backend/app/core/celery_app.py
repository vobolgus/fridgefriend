# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false

from __future__ import annotations

try:
    from celery import Celery
    from celery.schedules import crontab
except ImportError:
    Celery = None  # type: ignore[assignment,misc]
    crontab = None  # type: ignore[assignment,misc]

from app.core.config import settings

EXPIRY_REMINDER_TASK_NAME = "app.modules.notifications.tasks.send_expiry_reminders_task"


def create_celery_app() -> object | None:
    if Celery is None:
        return None

    app = Celery("fridgefriend", broker=settings.REDIS_URL)
    app.conf.task_always_eager = settings.DATABASE_URL.startswith("sqlite")
    app.conf.task_eager_propagates = settings.DATABASE_URL.startswith("sqlite")
    app.conf.beat_schedule = {
        "expiry-reminders-daily": {
            "task": EXPIRY_REMINDER_TASK_NAME,
            "schedule": crontab(hour=9, minute=0) if crontab is not None else 86400,
        },
    }
    return app


celery_app = create_celery_app()
