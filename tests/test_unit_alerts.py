"""
Unit tests for pure business logic — no database, no HTTP.
These run fast and catch regressions in core domain logic.
"""
from datetime import datetime, timedelta, timezone
import pytest

from app.services.match_service import ALERT_WINDOWS
from app.models.models import AlertType


class TestAlertWindows:
    """Alert windows must cover the right time ranges without gaps or overlaps."""

    def _in_window(self, alert_type: AlertType, hours_before: float) -> bool:
        delta = timedelta(hours=hours_before)
        low, high = ALERT_WINDOWS[alert_type]
        return low <= delta <= high

    def test_one_week_window_contains_7_days(self):
        assert self._in_window(AlertType.ONE_WEEK, hours_before=7 * 24)

    def test_one_week_window_excludes_6_days(self):
        assert not self._in_window(AlertType.ONE_WEEK, hours_before=6 * 24)

    def test_one_week_window_excludes_8_days(self):
        assert not self._in_window(AlertType.ONE_WEEK, hours_before=8 * 24)

    def test_three_days_window_contains_72_hours(self):
        assert self._in_window(AlertType.THREE_DAYS, hours_before=72)

    def test_three_days_window_excludes_48_hours(self):
        assert not self._in_window(AlertType.THREE_DAYS, hours_before=48)

    def test_six_hours_window_contains_6_hours(self):
        assert self._in_window(AlertType.SIX_HOURS, hours_before=6)

    def test_six_hours_window_excludes_12_hours(self):
        assert not self._in_window(AlertType.SIX_HOURS, hours_before=12)

    def test_six_hours_window_excludes_1_hour(self):
        assert not self._in_window(AlertType.SIX_HOURS, hours_before=1)

    def test_all_alert_types_have_windows(self):
        for alert_type in AlertType:
            assert alert_type in ALERT_WINDOWS, f"Missing window for {alert_type}"


class TestAlertTypeValues:
    """Enum values must match what is stored in the database."""

    def test_alert_type_values(self):
        assert AlertType.ONE_WEEK.value == "1_week"
        assert AlertType.THREE_DAYS.value == "3_days"
        assert AlertType.SIX_HOURS.value == "6_hours"