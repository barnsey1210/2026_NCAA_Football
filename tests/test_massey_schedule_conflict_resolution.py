import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "projection_sources",
    ROOT / "scripts/projections/build_game_projection_sources_2026.py",
)
projection_sources = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(projection_sources)


def write_massey(path: Path) -> None:
    pd.DataFrame([
        {
            "game_date": "2026-10-17",
            "away_team": "Kennesaw",
            "home_team": "Missouri St",
            "projected_spread_home": -3.5,
            "projected_total": 53.5,
            "away_projected_points": 24,
            "home_projected_points": 28,
            "away_win_prob": 0.39,
            "home_win_prob": 0.61,
            "pulled_at": "2026-10-04T10:54:47Z",
            "source_url": "https://masseyratings.com/",
            "neutral_site_hint": False,
        }
    ]).to_csv(path, index=False)


def test_unique_pair_resolves_three_day_provider_date_conflict(tmp_path, monkeypatch):
    source = tmp_path / "massey.csv"
    write_massey(source)
    monkeypatch.setattr(projection_sources, "MASSEY", source)
    game = {
        "game_id": "g451",
        "date": "2026-10-14",
        "week": 7,
        "away_team": "Kennesaw State",
        "home_team": "Missouri State",
        "neutral_site": False,
    }

    rows, audit = projection_sources.load_massey(
        projection_sources.site_game_index({"games": [game]})
    )

    assert len(rows) == 1
    assert rows[0]["game_id"] == "g451"
    assert audit[0]["match_method"] == "unique_team_pair_date_conflict"


def test_duplicate_pair_date_conflict_remains_unmatched(tmp_path, monkeypatch):
    source = tmp_path / "massey.csv"
    write_massey(source)
    monkeypatch.setattr(projection_sources, "MASSEY", source)
    games = [
        {
            "game_id": "g451",
            "date": "2026-10-14",
            "week": 7,
            "away_team": "Kennesaw State",
            "home_team": "Missouri State",
            "neutral_site": False,
        },
        {
            "game_id": "g999",
            "date": "2026-10-15",
            "week": 7,
            "away_team": "Kennesaw State",
            "home_team": "Missouri State",
            "neutral_site": False,
        },
    ]

    rows, audit = projection_sources.load_massey(
        projection_sources.site_game_index({"games": games})
    )

    assert rows == []
    assert audit[0]["match_method"] == "unmatched"
