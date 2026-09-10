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
        {"team": "A", "conference": "Test", "combo": 50, "hfa": 0},
        {"team": "B", "conference": "Test", "combo": 90, "hfa": 0},
    ]
    games = [
        {"game_id": "g1", "week": 1, "away_team": "B", "home_team": "A", "away_conference": "Test", "home_conference": "Test", "is_conference_game": True, "projected_margin_home": -40},
        {"game_id": "g2", "week": 2, "away_team": "A", "home_team": "B", "away_conference": "Test", "home_conference": "Test", "is_conference_game": True, "projected_margin_home": 40},
    ]
    return {"teams": teams, "games": games, "conferences": [{"conference": "Test", "teams": deepcopy(teams), "championship_game": {"neutral_site": True}}]}


class CompletedGameFreezingTests(unittest.TestCase):
    def test_canonical_final_is_frozen_in_every_trial(self):
        db = fixture()
        applied = SIM.apply_canonical_results(db, [{"game_id": "g1", "completed": True, "away_score": 7, "home_score": 10}])
        self.assertEqual(applied, 1)
        self.assertEqual(SIM.completed_game_winner(db["games"][0]), "A")
        out = SIM.rerun_sims(db, sims=100, seed=7, sigma=14, title_sigma=14)
        by_team = {x["team"]: x for x in out["teams"]}
        self.assertGreaterEqual(by_team["A"]["avg_total_wins"], 1.0)
        self.assertGreaterEqual(by_team["A"]["avg_conference_wins"], 1.0)
        self.assertEqual(by_team["A"]["win_distribution"], [{"wins": 1, "probability": 1.0}])

    def test_completed_results_are_seed_independent(self):
        winners = []
        for seed in (1, 2, 999):
            db = fixture()
            SIM.apply_canonical_results(db, [{"game_id": "g1", "completed": True, "away_score": 7, "home_score": 10}])
            winners.append(SIM.completed_game_winner(db["games"][0]))
            SIM.rerun_sims(db, sims=5, seed=seed, sigma=14, title_sigma=14)
        self.assertEqual(winners, ["A", "A", "A"])


if __name__ == "__main__":
    unittest.main()
