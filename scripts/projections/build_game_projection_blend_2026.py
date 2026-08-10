#!/usr/bin/env python3
from pathlib import Path
import json
import re
import pandas as pd
from pandas.errors import EmptyDataError

PRESEASON_DB = Path("data/snapshots/preseason/preseason_db.json")
SOURCES = Path("data/projections/game_projection_sources_2026.csv")
CONFIG = Path("data/projections/game_projection_blend_config.json")
OUT = Path("data/projections/game_projection_blend_2026.csv")
AUDIT = Path("data/projections/game_projection_blend_audit_2026.csv")

DEFAULT_CONFIG = {
    "blend_mode": "equal_available",
    "spread_sources": {
        "SP+": True,
        "FPI": True,
        "TeamRankings": True,
        "DRatings Predictions": True,
        "Sagarin Predictor Prediction": False,
    },
    "total_sources": {
        "SP+": True,
        "DRatings Predictions": True,
        "Massey Games": False,
        "Sagarin Predictor Prediction": False,
    },
}

def load_config():
    if CONFIG.exists():
        try:
            cfg = json.loads(CONFIG.read_text())
        except Exception as e:
            raise SystemExit(f"Could not parse {CONFIG}: {e}")
    else:
        cfg = DEFAULT_CONFIG
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps(cfg, indent=2) + "\n")

    spread_sources = dict(DEFAULT_CONFIG["spread_sources"])
    spread_sources.update(cfg.get("spread_sources", {}))

    total_sources = dict(DEFAULT_CONFIG["total_sources"])
    total_sources.update(cfg.get("total_sources", {}))

    return spread_sources, total_sources


def equal_available_weights(values, eligibility):
    available = [
        source
        for source, enabled in eligibility.items()
        if enabled and values.get(source) is not None
    ]

    if not available:
        return {}

    weight = 1.0 / len(available)
    return {source: weight for source in available}

def load_db():
    if not PRESEASON_DB.exists():
        raise SystemExit(f"Missing canonical preseason DB: {PRESEASON_DB}")

    try:
        db = json.loads(PRESEASON_DB.read_text())
    except Exception as exc:
        raise SystemExit(f"Could not parse {PRESEASON_DB}: {exc}") from exc

    if not isinstance(db, dict):
        raise SystemExit(f"{PRESEASON_DB} must contain a JSON object")

    games = db.get("games")
    if not isinstance(games, list) or not games:
        raise SystemExit(f"{PRESEASON_DB} does not contain a non-empty games list")

    return db

def read_sources():
    if not SOURCES.exists() or SOURCES.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(SOURCES)
    except EmptyDataError:
        return pd.DataFrame()

def num(x):
    try:
        if x is None or x == "":
            return None
        v = float(x)
        if pd.isna(v):
            return None
        return v
    except Exception:
        return None

def weighted_avg(values, weights):
    total_w = 0.0
    total_v = 0.0
    used = []
    used_detail = []
    for source, value in values.items():
        v = num(value)
        w = float(weights.get(source, 0) or 0)
        if v is None or w <= 0:
            continue
        total_w += w
        total_v += v * w
        used.append(source)
        used_detail.append(f"{source}:{w:g}")
    if total_w <= 0:
        return None, [], []
    return total_v / total_w, used, used_detail

def spread_text(home, away, spread_home):
    v = num(spread_home)
    if v is None:
        return ""
    if abs(v) < 0.05:
        return "Pick"
    if v > 0:
        return f"{home} -{abs(v):.1f}"
    return f"{away} -{abs(v):.1f}"

def source_key(source):
    s = str(source or "")
    if s == "Sagarin Predictor Home/Away Experimental":
        return "sagarin_homeaway"
    if s == "Sagarin Predictor Prediction":
        return "sagarin_predictor"
    if s == "DRatings Predictions":
        return "dratings"
    if s == "Massey Games":
        return "massey"
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

NON_FBS_CONFS_FOR_GAME_PROJECTION = {"fcs", "non-fbs", "non fbs", "unknown", ""}

def is_non_fbs_game(g) -> bool:
    away_conf = str(g.get("away_conference") or "").strip().lower()
    home_conf = str(g.get("home_conference") or "").strip().lower()
    return away_conf in NON_FBS_CONFS_FOR_GAME_PROJECTION or home_conf in NON_FBS_CONFS_FOR_GAME_PROJECTION

def main():
    spread_eligibility, total_eligibility = load_config()
    db = load_db()
    games = pd.DataFrame(db.get("games", []))
    src = read_sources()

    rows = []
    audit = []

    if not src.empty:
        for col in ["spread_home", "total"]:
            if col in src.columns:
                src[col] = pd.to_numeric(src[col], errors="coerce")

    source_names = sorted(set(src["source"].dropna().astype(str))) if not src.empty and "source" in src.columns else []
    configured_sources = sorted(
        set(spread_eligibility) | set(total_eligibility) | set(source_names)
    )

    for _, g in games.iterrows():
        game_id = g.get("game_id")
        # Projection sources must be explicit provider observations.
        # Do not feed the prior blended DB projection back into the blender.
        source_values_spread = {}
        source_values_total = {}

        # Preserve the original preseason SP+ total as an explicit source.
        # apply_game_projection_blend_to_preseason_db.py stores this once before
        # replacing projected_total with the production consensus.
        if not is_non_fbs_game(g):
            spplus_total = num(g.get("projection_overlay_previous_total"))
            if spplus_total is None:
                spplus_total = num(g.get("projected_total"))
            source_values_total["SP+"] = spplus_total

        if not src.empty and "game_id" in src.columns:
            sg = src[src["game_id"].astype(str) == str(game_id)]
            for _, r in sg.iterrows():
                source = str(r.get("source"))

                spread_value = num(r.get("spread_home"))
                total_value = num(r.get("total"))

                # Never let a blank provider field erase an already-established
                # value for that source (notably the canonical SP+ total).
                if spread_value is not None:
                    source_values_spread[source] = spread_value
                if total_value is not None:
                    source_values_total[source] = total_value

        spread_weights = equal_available_weights(
            source_values_spread, spread_eligibility
        )
        total_weights = equal_available_weights(
            source_values_total, total_eligibility
        )

        blend_spread, used_spread, used_spread_detail = weighted_avg(
            source_values_spread, spread_weights
        )
        blend_total, used_total, used_total_detail = weighted_avg(
            source_values_total, total_weights
        )

        row = {
            "game_id": game_id,
            "week": g.get("week"),
            "date": g.get("date"),
            "away_team": g.get("away_team"),
            "home_team": g.get("home_team"),
            "neutral_site": g.get("neutral_site"),
            "site_spread_home": source_values_spread.get("SP+"),
            "site_spread_text": spread_text(g.get("home_team"), g.get("away_team"), source_values_spread.get("SP+")),
            "site_total": source_values_total.get("SP+"),
            "blend_spread_home": round(blend_spread, 3) if blend_spread is not None else "",
            "blend_spread_text": spread_text(g.get("home_team"), g.get("away_team"), blend_spread),
            "blend_total": round(blend_total, 3) if blend_total is not None else "",
            "spread_sources_used": ",".join(used_spread),
            "total_sources_used": ",".join(used_total),
            "spread_weight_detail": ";".join(used_spread_detail),
            "total_weight_detail": ";".join(used_total_detail),
            "source_count_spread": len(used_spread),
            "source_count_total": len(used_total),
        }

        # Keep explicit columns for known and newly active projection sources.
        for source in configured_sources:
            if source == "Site Projection":
                continue
            key = source_key(source)
            spread_v = source_values_spread.get(source)
            total_v = source_values_total.get(source)
            row[f"{key}_spread_home"] = spread_v
            row[f"{key}_spread_text"] = spread_text(g.get("home_team"), g.get("away_team"), spread_v)
            row[f"{key}_total"] = total_v
            row[f"spread_disagreement_{key}"] = round(abs(source_values_spread.get("SP+") - spread_v), 3) if source_values_spread.get("SP+") is not None and spread_v is not None else ""
            row[f"total_disagreement_{key}"] = round(abs(source_values_total.get("SP+") - total_v), 3) if source_values_total.get("SP+") is not None and total_v is not None else ""
            row[f"spread_weight_{key}"] = spread_weights.get(source, 0)
            row[f"total_weight_{key}"] = total_weights.get(source, 0)

        # Backward-compatible aliases used by the first draft.
        row["massey_spread_home"] = row.get("massey_games_spread_home", row.get("massey_spread_home", ""))
        row["massey_spread_text"] = row.get("massey_games_spread_text", row.get("massey_spread_text", ""))
        row["massey_total"] = row.get("massey_games_total", row.get("massey_total", ""))
        row["spread_disagreement"] = row.get("spread_disagreement_massey_games", "")
        row["total_disagreement"] = row.get("total_disagreement_massey_games", "")

        rows.append(row)

        aud = {
            "game_id": game_id,
            "away_team": g.get("away_team"),
            "home_team": g.get("home_team"),
            "has_site_spread": source_values_spread.get("SP+") is not None,
            "has_site_total": source_values_total.get("SP+") is not None,
        }
        for source in configured_sources:
            if source == "Site Projection":
                continue
            key = source_key(source)
            aud[f"has_{key}_spread"] = source_values_spread.get(source) is not None
            aud[f"has_{key}_total"] = source_values_total.get(source) is not None
        audit.append(aud)

    out = pd.DataFrame(rows)
    aud = pd.DataFrame(audit)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    aud.to_csv(AUDIT, index=False)

    print(f"Wrote {OUT}: {len(out)} rows")
    print(f"Wrote {AUDIT}: {len(aud)} rows")
    print(f"Blend config: {CONFIG}")

    coverage_cols = [c for c in aud.columns if c.startswith("has_")]
    if coverage_cols:
        print("\nCoverage:")
        print(aud[coverage_cols].sum().to_string())

    disagreement_cols = [c for c in out.columns if c.startswith("spread_disagreement_")]
    populated = [c for c in disagreement_cols if c in out and pd.to_numeric(out[c], errors="coerce").notna().any()]
    if populated:
        best_col = populated[0]
        show_cols = ["week", "date", "away_team", "home_team", "site_spread_text", "blend_spread_text", "site_total", "blend_total", best_col]
        print("\nLargest spread disagreements:")

        # Diagnostic only: force disagreement column numeric so blanks/strings do not crash automation.
        diag = out.copy()
        diag[best_col] = pd.to_numeric(diag[best_col], errors="coerce")
        diag = diag[diag[best_col].notna()]
        if diag.empty:
            print("No numeric disagreement rows available.")
        else:
            print(diag.sort_values(best_col, ascending=False).head(30)[show_cols].to_string(index=False))

if __name__ == "__main__":
    main()
