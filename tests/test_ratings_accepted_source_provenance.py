import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts/ratings/build_all_ratings_latest.py"

spec = importlib.util.spec_from_file_location(
    "build_all_ratings_latest",
    MODULE,
)
ratings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ratings)


def test_accepted_source_pulled_at_uses_live_change_status(tmp_path):
    status = tmp_path / "live_rating_change_status.json"
    status.write_text(
        json.dumps(
            {
                "sources": {
                    "SP+": {
                        "latest_pull_at": "2026-09-02T12:01:28Z",
                    },
                    "FPI": {
                        "latest_pull_at": "2026-09-02T12:01:29Z",
                    },
                    "TeamRankings": {
                        "latest_pull_at": "2026-09-02T12:01:31Z",
                    },
                }
            }
        )
    )

    assert ratings.accepted_source_pulled_at(
        "SP+", status
    ) == "2026-09-02T12:01:28Z"

    assert ratings.accepted_source_pulled_at(
        "FPI", status
    ) == "2026-09-02T12:01:29Z"

    assert ratings.accepted_source_pulled_at(
        "TeamRankings", status
    ) == "2026-09-02T12:01:31Z"


def test_accepted_source_pulled_at_fails_closed(tmp_path):
    missing = tmp_path / "missing.json"
    assert ratings.accepted_source_pulled_at("SP+", missing) == ""

    broken = tmp_path / "broken.json"
    broken.write_text("{not-json")
    assert ratings.accepted_source_pulled_at("SP+", broken) == ""

    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"sources": {"SP+": {}}}))
    assert ratings.accepted_source_pulled_at("SP+", empty) == ""
