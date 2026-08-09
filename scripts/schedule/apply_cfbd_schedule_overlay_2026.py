#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, json, re
from datetime import datetime, timezone, date
from pathlib import Path

ROOT = Path.cwd()
DB = ROOT / "data/snapshots/preseason/preseason_db.json"
SCHEDULE = ROOT / "data/canonical/cfbd_schedule_2026.json"
AUDIT = ROOT / "data/audits/cfbd_schedule_overlay_audit.json"

ALIASES = {
    "houston christian": "hcu",
    "houston baptist": "hcu",
    "ucf": "central florida",
    "uconn": "connecticut",
    "ole miss": "mississippi",
    "app state": "appalachian state",
    "ul monroe": "ul monroe",
    "ul-monroe": "ul monroe",
}

def norm(x):
    s = re.sub(r"[^a-z0-9]+", " ", str(x or "").lower()).strip()
    return ALIASES.get(s, s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    db = json.loads(DB.read_text())
    sched = json.loads(SCHEDULE.read_text())
    games = db.get("games", [])
    cfbd = sched.get("games", [])

    by_id = {str(g.get("cfbd_game_id")): g for g in cfbd if g.get("cfbd_game_id") is not None}
    by_teams = {}
    for g in cfbd:
        by_teams.setdefault((norm(g.get("away_team")), norm(g.get("home_team"))), []).append(g)

    out = copy.deepcopy(db)
    changes, unmatched, ambiguous = [], [], []
    matched = 0

    fields = {
        "date": "date",
        "week": "week",
        "neutral_site": "neutral_site",
        "cfbd_completed": "completed",
        "cfbd_status": "status",
        "cfbd_last_updated": "cfbd_last_updated",
        "cfbd_start_date": "start_date",
        "cfbd_start_time_tbd": "start_time_tbd",
    }

    for g in out.get("games", []):
        cg = None
        method = None
        cid = g.get("cfbd_game_id")
        if cid is not None and str(cid) in by_id:
            cg = by_id[str(cid)]
            method = "cfbd_game_id"
        else:
            away_key = norm(g.get("away_team"))
            home_key = norm(g.get("home_team"))

            candidates = by_teams.get((away_key, home_key), [])
            if len(candidates) == 1:
                cg = candidates[0]
                method = "unique_team_pair"
            elif len(candidates) > 1:
                ambiguous.append({
                    "game_id": g.get("game_id"),
                    "match_type": "same_orientation",
                    "candidates": [x.get("cfbd_game_id") for x in candidates]
                })
            else:
                reversed_candidates = by_teams.get((home_key, away_key), [])

                # Reversed orientation is only safe when the authoritative game
                # occurs essentially on the same scheduled date. This prevents
                # future flex/TBD placeholders from matching an unrelated
                # earlier-season meeting between the same two teams.
                existing_date = None
                try:
                    existing_date = date.fromisoformat(str(g.get("date"))[:10])
                except Exception:
                    pass

                safe_reversed = []
                for candidate in reversed_candidates:
                    candidate_date = None
                    try:
                        candidate_date = date.fromisoformat(
                            str(candidate.get("date"))[:10]
                        )
                    except Exception:
                        pass

                    if existing_date and candidate_date:
                        if abs((candidate_date - existing_date).days) <= 2:
                            safe_reversed.append(candidate)

                if len(safe_reversed) == 1:
                    cg = safe_reversed[0]
                    method = "unique_reversed_team_pair"
                elif len(safe_reversed) > 1:
                    ambiguous.append({
                        "game_id": g.get("game_id"),
                        "match_type": "reversed_orientation",
                        "candidates": [
                            x.get("cfbd_game_id") for x in safe_reversed
                        ]
                    })

        if not cg:
            unmatched.append({"game_id": g.get("game_id"), "cfbd_game_id": g.get("cfbd_game_id"),
                              "date": g.get("date"), "away_team": g.get("away_team"), "home_team": g.get("home_team")})
            continue

        matched += 1
        rec = {
            "game_id": g.get("game_id"),
            "away_team": g.get("away_team"),
            "home_team": g.get("home_team"),
            "match_method": method,
            "field_changes": {}
        }

        if method == "unique_reversed_team_pair":
            old_away = g.get("away_team")
            old_home = g.get("home_team")
            new_away = cg.get("away_team")
            new_home = cg.get("home_team")

            rec["field_changes"]["away_team"] = {
                "old": old_away,
                "new": new_away
            }
            rec["field_changes"]["home_team"] = {
                "old": old_home,
                "new": new_home
            }

            g["away_team"] = new_away
            g["home_team"] = new_home
        for db_field, cfbd_field in fields.items():
            new = cg.get(cfbd_field)
            if new is None:
                continue
            old = g.get(db_field)
            if old != new:
                rec["field_changes"][db_field] = {"old": old, "new": new}
                g[db_field] = new

        if cg.get("cfbd_game_id") is not None and g.get("cfbd_game_id") != cg.get("cfbd_game_id"):
            rec["field_changes"]["cfbd_game_id"] = {"old": g.get("cfbd_game_id"), "new": cg.get("cfbd_game_id")}
            g["cfbd_game_id"] = cg.get("cfbd_game_id")

        if rec["field_changes"]:
            changes.append(rec)

    audit = {
        "schema_version": "cfbd-schedule-overlay-audit-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "APPLY" if args.apply else "DRY_RUN",
        "site_games": len(games),
        "cfbd_games": len(cfbd),
        "matched": matched,
        "changed_games": len(changes),
        "unmatched_games": len(unmatched),
        "ambiguous_games": len(ambiguous),
        "changes": changes,
        "unmatched": unmatched,
        "ambiguous": ambiguous,
    }
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n")

    if args.apply:
        tmp = DB.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(out, indent=2) + "\n")
        tmp.replace(DB)
        print(f"Applied overlay to {DB}")
    else:
        print("DRY RUN ONLY: preseason_db.json not modified")

    print(f"matched={matched}/{len(games)} changed={len(changes)} unmatched={len(unmatched)} ambiguous={len(ambiguous)}")
    for r in changes[:40]:
        imp = {k:v for k,v in r["field_changes"].items() if k in {"date","week","neutral_site","cfbd_start_date"}}
        if imp:
            print(f"{r['game_id']}: {r['away_team']} @ {r['home_team']} -> {imp}")

if __name__ == "__main__":
    main()
