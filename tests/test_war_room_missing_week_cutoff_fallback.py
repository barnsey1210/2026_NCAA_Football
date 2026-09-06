import importlib.util
import unittest
from pathlib import Path

SCRIPT=Path("scripts/war_room/build_war_room_market_matrix.py")

spec=importlib.util.spec_from_file_location(
    "war_room_matrix",
    SCRIPT,
)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class MissingWeekCutoffFallbackTest(unittest.TestCase):

    def test_later_accepted_date_qualifies_without_exact_cutoff(self):
        meta={
            "latest_accepted_update_at":
                "2026-09-06T08:39:45Z"
        }

        self.assertTrue(
            mod.has_accepted_source_update(
                meta,
                None,
                "2026-09-05",
            )
        )

    def test_same_day_does_not_qualify_without_exact_cutoff(self):
        meta={
            "latest_accepted_update_at":
                "2026-09-05T23:59:00Z"
        }

        self.assertFalse(
            mod.has_accepted_source_update(
                meta,
                None,
                "2026-09-05",
            )
        )

    def test_exact_cutoff_remains_authoritative_when_available(self):
        meta={
            "latest_accepted_update_at":
                "2026-09-06T05:00:00Z"
        }

        self.assertFalse(
            mod.has_accepted_source_update(
                meta,
                "2026-09-06T06:24:22Z",
                "2026-09-05",
            )
        )


if __name__ == "__main__":
    unittest.main()
