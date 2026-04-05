"""Celery worker entrypoint.

Used by the ECS worker and beat services:
    celery -A app.worker worker --loglevel=INFO
    celery -A app.worker beat --loglevel=INFO
"""

from app.core.celery_app import celery_app  # noqa: F401

# Import task modules so Celery autodiscovers them.
import app.modules.notifications.tasks  # noqa: F401
