import unittest

from scripts.simulations.run_playoff_model_2026 import (
    SELECTOR_RECORD_FIRST,
    select_field_candidate,
)


class CandidateCSelectorTests(unittest.TestCase):
    def setUp(self):
        self.champs = {
            "ACC": "ACC Auto",
            "B1G": "B1G Auto",
            "B12": "B12 Auto",
            "SEC": "SEC Auto",
            "American": "G6 Auto",
        }
        names = list(self.champs.values()) + [
            "Zero Loss",
            "One Loss Elite",
            "One Loss Weak",
            "Two Loss Elite",
            "Two Loss Mid",
            "Two Loss Weak",
            "Two Loss Last",
            "Two Loss Extra",
            "Three Loss Elite",
            "Four Loss Elite",
        ]
        self.teams = {
            name: {"conference": "American" if name == "G6 Auto" else "Independent", "rating": 0.0}
            for name in names
        }
        self.metrics = {
            name: {"resume_score": float(100 - index)}
            for index, name in enumerate(names)
        }

    def select(self, ranked, losses):
        return select_field_candidate(
            ranked,
            self.champs,
            self.teams,
            self.metrics,
            SELECTOR_RECORD_FIRST,
            losses,
        )

    def test_exhausts_zero_through_two_loss_teams_before_three_loss_team(self):
        ranked = [
            "Three Loss Elite",
            "Four Loss Elite",
            "ACC Auto",
            "B1G Auto",
            "B12 Auto",
            "SEC Auto",
            "G6 Auto",
            "Zero Loss",
            "One Loss Elite",
            "One Loss Weak",
            "Two Loss Elite",
            "Two Loss Mid",
            "Two Loss Weak",
            "Two Loss Last",
            "Two Loss Extra",
        ]
        losses = {
            "Zero Loss": 0,
            "One Loss Elite": 1,
            "One Loss Weak": 1,
            "Two Loss Elite": 2,
            "Two Loss Mid": 2,
            "Two Loss Weak": 2,
            "Two Loss Last": 2,
            "Two Loss Extra": 2,
            "Three Loss Elite": 3,
            "Four Loss Elite": 4,
        }
        field, auto = self.select(ranked, losses)
        at_large = set(field) - auto
        self.assertEqual(
            at_large,
            {
                "Zero Loss",
                "One Loss Elite",
                "One Loss Weak",
                "Two Loss Elite",
                "Two Loss Mid",
                "Two Loss Weak",
                "Two Loss Last",
            },
        )
        self.assertNotIn("Two Loss Extra", at_large)
        self.assertEqual(len(field), 12)
        self.assertEqual(field[-1], "G6 Auto")
        self.assertEqual(
            auto,
            {"ACC Auto", "B1G Auto", "B12 Auto", "SEC Auto", "G6 Auto"},
        )

    def test_uses_three_then_four_plus_only_for_emergency_fill(self):
        ranked = [
            "Four Loss Elite",
            "Three Loss Elite",
            "ACC Auto",
            "B1G Auto",
            "B12 Auto",
            "SEC Auto",
            "G6 Auto",
            "Zero Loss",
            "One Loss Elite",
            "One Loss Weak",
            "Two Loss Elite",
            "Two Loss Mid",
            "Two Loss Weak",
        ]
        losses = {
            "Zero Loss": 0,
            "One Loss Elite": 1,
            "One Loss Weak": 1,
            "Two Loss Elite": 2,
            "Two Loss Mid": 2,
            "Two Loss Weak": 2,
            "Three Loss Elite": 3,
            "Four Loss Elite": 4,
        }
        field, auto = self.select(ranked, losses)
        at_large = set(field) - auto
        self.assertIn("Three Loss Elite", at_large)
        self.assertNotIn("Four Loss Elite", at_large)


if __name__ == "__main__":
    unittest.main()
