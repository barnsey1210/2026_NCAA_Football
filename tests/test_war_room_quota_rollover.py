import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.war_room import build_war_room_health as health


class QuotaRolloverTest(unittest.TestCase):
    def write_quota(self, directory, **overrides):
        payload = {
            "response_received_at": "2026-08-31T19:45:49+00:00",
            "x_requests_used": "19763",
            "x_requests_remaining": "237",
            "x_requests_last": "2",
        }
        payload.update(overrides)
        path = Path(directory) / "quota.json"
        path.write_text(json.dumps(payload))
        return path

    def test_prior_utc_month_opens_one_guarded_reconciliation(self):
        with tempfile.TemporaryDirectory() as directory:
            quota = self.write_quota(directory)
            with patch.object(health, "QUOTA", quota):
                result = health.build_api_quota_health(
                    datetime(2026, 9, 1, 1, 0, tzinfo=timezone.utc)
                )
        self.assertEqual(result["calendar_month"], "2026-09")
        self.assertEqual(result["quota_observed_period"], "2026-08")
        self.assertTrue(result["rollover_reconciliation_required"])
        self.assertTrue(result["scheduled_refresh_allowed"])
        self.assertEqual(result["prior_period_credits_remaining"], 237)
        self.assertEqual(result["reset_at_utc"], "2026-10-01T00:00:00+00:00")

    def test_current_period_still_enforces_reserve(self):
        with tempfile.TemporaryDirectory() as directory:
            quota = self.write_quota(
                directory, response_received_at="2026-09-01T00:05:00+00:00"
            )
            with patch.object(health, "QUOTA", quota):
                result = health.build_api_quota_health(
                    datetime(2026, 9, 1, 1, 0, tzinfo=timezone.utc)
                )
        self.assertFalse(result["rollover_reconciliation_required"])
        self.assertFalse(result["scheduled_refresh_allowed"])
        self.assertEqual(result["status"], "RESERVE_ONLY")


if __name__ == "__main__":
    unittest.main()
