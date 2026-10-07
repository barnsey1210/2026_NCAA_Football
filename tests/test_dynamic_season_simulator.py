from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("conference_sim", ROOT / "rerun_conference_sims_2026.py")
SIM = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SIM)


def fixture():
    teams = [
        {"team": "A", "conference": "Test", "combo": 10.0, "hfa": 0.0},
        {"team": "B", "conference": "Test", "combo": 5.0, "hfa": 0.0},
        {"team": "Bye", "conference": "Independent", "combo": 0.0, "hfa": 0.0},
    ]
    games = [
        {"game_id": "done", "week": 1, "away_team": "B", "home_team": "A", "away_conference": "Test", "home_conference": "Test", "is_conference_game": True, "completed": True, "away_score": 20, "home_score": 21},
        {"game_id": "future", "week": 2, "away_team": "B", "home_team": "A", "away_conference": "Test", "home_conference": "Test", "is_conference_game": True, "projected_margin_home": 3.0},
    ]
    return {"teams": teams, "games": games, "conferences": []}


class RecordingRng:
    def __init__(self):
        self.gauss_calls = []

    def gauss(self, mean, sd):
        self.gauss_calls.append((mean, sd))
        return mean + 1.0

    def random(self):
        return 0.25


class DynamicSeasonSimulatorTests(unittest.TestCase):
    def test_frozen_game_and_chronological_dynamic_update(self):
        prepared = SIM.prepare_dynamic_regular_season(deepcopy(fixture()))
        rng = RecordingRng()
        out = SIM.simulate_dynamic_regular_season_trial(prepared, rng)
        self.assertEqual(out["results"][("B", "A")], "A")
        self.assertEqual(out["margins"][("B", "A")], 4.0)
        self.assertAlmostEqual(out["latent"]["A"], 1.0 + SIM.UPDATE_BETA)
        self.assertAlmostEqual(out["latent"]["B"], 1.0 - SIM.UPDATE_BETA)

    def test_weekly_shock_includes_bye_teams(self):
        prepared = SIM.prepare_dynamic_regular_season(deepcopy(fixture()))
        rng = RecordingRng()
        SIM.simulate_dynamic_regular_season_trial(prepared, rng)
        shock_calls = [call for call in rng.gauss_calls if call[1] == SIM.WEEKLY_STRENGTH_SHOCK_SD]
        self.assertEqual(len(shock_calls), 3)

    def test_parameters_and_model_version_are_frozen(self):
        self.assertEqual(SIM.GAME_SIGMA, 15.7)
        self.assertEqual(SIM.UPDATE_BETA, 0.09)
        self.assertEqual(SIM.WEEKLY_STRENGTH_SHOCK_SD, 1.5)
        self.assertEqual(SIM.SURPRISE_CAP, 35.0)
        self.assertEqual(SIM.DYNAMIC_MODEL_VERSION, "dynamic_conference_season_v1")


if __name__ == "__main__":
    unittest.main()
