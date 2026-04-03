from __future__ import annotations

from datetime import date
from enum import StrEnum


class UrgencyBucket(StrEnum):
    TODAY = "today"
    THIS_WEEK = "this_week"
    SAFE_LATER = "safe_later"
    EXPIRED = "expired"


def get_urgency_bucket(expiry_date: date, today: date) -> UrgencyBucket:
    days_left = (expiry_date - today).days

    if days_left < 0:
        return UrgencyBucket.EXPIRED
    if days_left <= 1:
        return UrgencyBucket.TODAY
    if days_left <= 7:
        return UrgencyBucket.THIS_WEEK
    return UrgencyBucket.SAFE_LATER
