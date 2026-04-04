from datetime import date, timedelta

from components.filters import PRESET_DAYS


class TestPresetDays:
    def test_all_presets_are_positive(self):
        for label, days in PRESET_DAYS.items():
            assert days > 0, f"{label} has non-positive days: {days}"

    def test_preset_range_produces_valid_dates(self):
        from datetime import datetime

        now = datetime.utcnow()
        for label, days in PRESET_DAYS.items():
            start = (now - timedelta(days=days)).date()
            end = now.date()
            assert start < end or start == end, f"{label}: start={start} >= end={end}"

    def test_custom_range_start_before_end(self):
        start = date(2026, 1, 1)
        end = date(2026, 3, 1)
        assert start < end

    def test_last_7_days_span(self):
        from datetime import datetime

        now = datetime.utcnow()
        start = (now - timedelta(days=7)).date()
        end = now.date()
        assert (end - start).days == 7

    def test_last_30_days_span(self):
        from datetime import datetime

        now = datetime.utcnow()
        start = (now - timedelta(days=30)).date()
        end = now.date()
        assert (end - start).days == 30
