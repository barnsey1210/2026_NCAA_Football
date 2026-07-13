#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re
import pandas as pd

DB_RE = re.compile(r'(<script id="db" type="application/json">)(.*?)(</script>)', re.S)

def clean(v):
    if pd.isna(v):
        return None
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", default="index.html")
    ap.add_argument("--results", default="data/results/game_results_2026.csv")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    src = Path(args.index)
    results_path = Path(args.results)
    out = Path(args.out or args.index)

    html = src.read_text(errors="ignore")
    m = DB_RE.search(html)
    if not m:
        raise SystemExit("DB script tag not found")

    db = json.loads(m.group(2))
    res = pd.read_csv(results_path)

    by_gid = {str(r["game_id"]): r for _, r in res.iterrows() if str(r.get("game_id", "")).strip()}

    updated = 0
    for g in db.get("games", []):
        r = by_gid.get(str(g.get("game_id")))
        if r is None:
            continue

        away_score = clean(r.get("away_score"))
        home_score = clean(r.get("home_score"))

        g["cfbd_status"] = clean(r.get("status")) or "final"
        g["cfbd_completed"] = bool(r.get("completed", True))
        g["cfbd_away_score"] = away_score
        g["cfbd_home_score"] = home_score
        g["away_score"] = away_score
        g["home_score"] = home_score
        g["completed"] = True
        g["result_source"] = clean(r.get("source")) or "results_csv"
        g["result_updated_at"] = clean(r.get("updated_at"))

        try:
            ascore = float(away_score)
            hscore = float(home_score)
            total = ascore + hscore
            home_margin = hscore - ascore

            g["home_margin_actual"] = home_margin
            g["total_points_actual"] = total
            g["winner"] = g.get("home_team") if hscore > ascore else g.get("away_team") if ascore > hscore else "Tie"

            spread = g.get("market_spread_home")
            total_line = g.get("market_total")

            if spread not in [None, ""]:
                cover = home_margin + float(spread)
                g["home_cover_margin"] = cover
                g["ats_team"] = g.get("home_team") if cover > 0 else g.get("away_team") if cover < 0 else "Push"
                g["ats_result"] = "home" if cover > 0 else "away" if cover < 0 else "push"

            if total_line not in [None, ""]:
                total_margin = total - float(total_line)
                g["total_margin"] = total_margin
                g["total_result"] = "over" if total_margin > 0 else "under" if total_margin < 0 else "push"
        except Exception:
            pass

        updated += 1

    new_json = json.dumps(db, separators=(",", ":"))
    html = html[:m.start(2)] + new_json + html[m.end(2):]
    out.write_text(html, encoding="utf-8")

    print(f"updated games: {updated}")
    print(f"wrote {out}")

if __name__ == "__main__":
    main()
