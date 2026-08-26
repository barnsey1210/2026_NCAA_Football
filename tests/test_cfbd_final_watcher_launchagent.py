#!/usr/bin/env python3
import json
import plistlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CfbdFinalWatcherLaunchAgentTests(unittest.TestCase):
    def test_watcher_remains_disabled_by_default(self):
        config = json.loads(
            (ROOT / "config/cfbd_final_watcher.json").read_text(encoding="utf-8")
        )
        self.assertFalse(config["enabled"])

    def test_launchagent_is_dumb_five_minute_timer(self):
        with (ROOT / "deploy/launchagents/com.jim.ncaaf.cfbd-final-watcher.plist").open("rb") as handle:
            plist = plistlib.load(handle)
        self.assertEqual(plist["StartInterval"], 300)
        self.assertNotIn("StartCalendarInterval", plist)
        self.assertNotIn("RunAtLoad", plist)
        self.assertNotIn("KeepAlive", plist)
        self.assertEqual(
            plist["ProgramArguments"],
            [
                "/bin/zsh",
                "/Users/jameslindesmith/NCAAF_AUTO/scripts/war_room/start_cfbd_final_watcher.sh",
            ],
        )

    def test_wrapper_does_not_embed_secret_or_game_day_logic(self):
        wrapper = (ROOT / "scripts/war_room/start_cfbd_final_watcher.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("security find-generic-password", wrapper)
        self.assertIn("run_cfbd_final_watcher.py", wrapper)
        self.assertNotIn("Authorization:", wrapper)
        self.assertNotIn("Saturday", wrapper)
        self.assertNotIn("Sunday", wrapper)


if __name__ == "__main__":
    unittest.main()
