from __future__ import annotations

from app.core.celery_app import EXPIRY_REMINDER_TASK_NAME, celery_app


def test_beat_schedule_includes_expiry_reminders() -> None:
    if celery_app is None:
        assert celery_app is None
        return

    schedule = celery_app.conf.beat_schedule
    assert "expiry-reminders-daily" in schedule
    assert schedule["expiry-reminders-daily"]["task"] == EXPIRY_REMINDER_TASK_NAME
