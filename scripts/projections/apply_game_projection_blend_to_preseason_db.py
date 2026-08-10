#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json, math
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data/snapshots/preseason/preseason_db.json"
BLEND = ROOT / "data/projections/game_projection_blend_2026.csv"
AUDIT = ROOT / "data/projections/game_projection_site_overlay_audit.json"

def finite(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None

def main():
    if not DB.exists():
        raise SystemExit(f"Missing canonical preseason DB: {DB}")
    if not BLEND.exists():
        raise SystemExit(f"Missing canonical projection blend: {BLEND}")

    db = json.loads(DB.read_text())
    games = db.get("games")
    if not isinstance(games, list) or not games:
        raise SystemExit("Canonical preseason DB has no games")

    blend = pd.read_csv(BLEND)
    if "game_id" not in blend.columns:
        raise SystemExit("Projection blend missing game_id")

    by_id = {str(r["game_id"]): r for r in blend.to_dict("records")}

    updated = spread_updated = total_updated = missing_blend = 0
    coverage = {}

    for g in games:
        gid = str(g.get("game_id") or "")
        r = by_id.get(gid)
        if not r:
            missing_blend += 1
            continue

        spread = finite(r.get("blend_spread_home"))
        total = finite(r.get("blend_total"))
        spread_count = int(finite(r.get("source_count_spread")) or 0)
        total_count = int(finite(r.get("source_count_total")) or 0)

        spread_sources = [x for x in str(r.get("spread_sources_used") or "").split(",") if x]
        total_sources = [x for x in str(r.get("total_sources_used") or "").split(",") if x]

        if "projection_overlay_previous_margin_home" not in g:
            g["projection_overlay_previous_margin_home"] = g.get("projected_margin_home")
        if "projection_overlay_previous_total" not in g:
            g["projection_overlay_previous_total"] = g.get("projected_total")

        changed = False
        if spread is not None:
            g["projected_margin_home"] = round(spread, 4)
            g["blend_spread_home"] = round(spread, 4)
            spread_updated += 1
            changed = True
        if total is not None:
            g["projected_total"] = round(total, 4)
            g["blend_total"] = round(total, 4)
            total_updated += 1
            changed = True

        g["projection_model_family"] = "Game Projection Consensus"
        g["projection_spread_model_version"] = "spread_consensus_equal_available_v1"
        g["projection_total_model_version"] = "total_consensus_equal_available_v1"

        g["projection_spread_source_count"] = spread_count
        g["projection_spread_source_max"] = 5
        g["projection_spread_coverage"] = f"{spread_count}/5"
        g["projection_spread_sources"] = spread_sources
        g["projection_spread_source_label"] = ", ".join(spread_sources)

        g["projection_total_source_count"] = total_count
        g["projection_total_source_max"] = 4
        g["projection_total_coverage"] = f"{total_count}/4"
        g["projection_total_sources"] = total_sources
        g["projection_total_source_label"] = ", ".join(total_sources)

        if changed:
            updated += 1
            key = f"spread_{spread_count}of5_total_{total_count}of4"
            coverage[key] = coverage.get(key, 0) + 1

    db["projection_model_metadata"] = {
        "family": "Game Projection Consensus",

        "spread_version": "spread_consensus_equal_available_v1",
        "spread_max_sources": 5,
        "spread_sources": [
            "SP+",
            "FPI",
            "TeamRankings",
            "DRatings Predictions",
            "Sagarin Predictor Prediction",
        ],
        "spread_active_sources": [
            "SP+",
            "FPI",
            "TeamRankings",
            "DRatings Predictions",
        ],
        "spread_pending_sources": [
            "Sagarin Predictor Prediction",
        ],
        "spread_fallback": "equal weight across available eligible production sources",

        "total_version": "total_consensus_equal_available_v1",
        "total_max_sources": 4,
        "total_sources": [
            "SP+",
            "DRatings Predictions",
            "Massey Games",
            "Sagarin Predictor Prediction",
        ],
        "total_active_sources": [
            "SP+",
            "DRatings Predictions",
        ],
        "total_pending_sources": [
            "Massey Games",
            "Sagarin Predictor Prediction",
        ],
        "total_fallback": "equal weight across available eligible production sources",

        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    tmp = DB.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(db, indent=2) + "\n")
    tmp.replace(DB)

    audit = {
        "schema_version": "game-projection-site-overlay-audit-v1",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "games_in_db": len(games),
        "blend_rows": len(blend),
        "games_updated": updated,
        "spread_updated": spread_updated,
        "total_updated": total_updated,
        "missing_blend_rows": missing_blend,
        "coverage_buckets": coverage,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n")

    print(f"Applied projection blend to {updated}/{len(games)} games")
    print(f"Spread updated: {spread_updated}")
    print(f"Total updated: {total_updated}")
    print(f"Wrote {AUDIT}")
    for k, v in sorted(coverage.items()):
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
