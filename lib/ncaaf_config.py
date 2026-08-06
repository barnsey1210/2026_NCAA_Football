#!/usr/bin/env python3
from pathlib import Path
import json

def _find_repo_root() -> Path:
    """Support both lib/ and scripts/lib/ repository layouts."""
    current = Path(__file__).resolve()

    for candidate in current.parents:
        if (
            (candidate / "config/team_aliases.json").is_file()
            and (candidate / "data/ratings/ratings_config.json").is_file()
        ):
            return candidate

    raise FileNotFoundError(
        "Unable to locate repository root containing "
        "config/team_aliases.json and data/ratings/ratings_config.json"
    )


ROOT = _find_repo_root()
TEAM_CONFIG = ROOT / "config/team_aliases.json"
RATINGS_CONFIG = ROOT / "data/ratings/ratings_config.json"
RATINGS_MASTER = ROOT / "data/ratings/ratings_master_latest.csv"

SOURCE_LABELS = {"bradpowers": "Brad Powers", "spplus": "SP+", "fpi": "FPI", "teamrankings": "TeamRankings", "kford": "KFord"}
SOURCE_SHORT_LABELS = {"bradpowers": "BP", "spplus": "SP+", "fpi": "FPI", "teamrankings": "TR", "kford": "KFord"}
SOURCE_ORDER = ("bradpowers", "spplus", "fpi", "teamrankings", "kford")


def _load_json(path):
    return json.loads(Path(path).read_text())


def team_config():
    return _load_json(TEAM_CONFIG)


def canonical_team(name):
    value = str(name or "").strip()
    return team_config().get("aliases", {}).get(value, value)


def canonical_conference(team, current=None):
    return team_config().get("conference_overrides", {}).get(canonical_team(team), current)


def boolish(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def is_neutral_site(game):
    """Curated schedule value wins; CFBD is used only when canonical data is absent."""
    for key in ("neutral_site", "neutral", "is_neutral", "Neutral Site?"):
        if key in game and game.get(key) not in (None, ""):
            return boolish(game.get(key))
    return boolish(game.get("cfbd_neutral_site"))


def ratings_updated_date():
    if not RATINGS_MASTER.exists():
        return "unknown"
    import pandas as pd
    df = pd.read_csv(RATINGS_MASTER)
    for col in ("rating_date", "snapshot_date", "date"):
        if col in df and df[col].notna().any():
            return str(df[col].dropna().max())[:10]
    return "unknown"


def production_model():
    cfg = _load_json(RATINGS_CONFIG)
    weights, active = cfg.get("weights", {}), cfg.get("active_systems", {})
    sources = []
    for key in SOURCE_ORDER:
        weight = float(weights.get(key, 0) or 0)
        if active.get(key, weight > 0) and weight > 0:
            sources.append({"key": key, "label": SOURCE_LABELS.get(key, key), "short_label": SOURCE_SHORT_LABELS.get(key, key), "weight": weight})
    return {"season": cfg.get("season"), "sources": sources, "updated": ratings_updated_date()}


def model_summary(short=False):
    label_key = "short_label" if short else "label"
    return " · ".join(f"{s[label_key]} {s['weight'] * 100:g}%" for s in production_model()["sources"])
