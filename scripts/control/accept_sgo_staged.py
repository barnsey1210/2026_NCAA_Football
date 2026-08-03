#!/usr/bin/env python3
"""Promote a complete controller-normalized SGO staging run into accepted game lines.

This script fails closed unless canonical coverage is complete. It updates only
games present in the staged display artifact and preserves all other accepted rows.
"""
from __future__ import annotations
import argparse, csv, json, os, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "data/odds/season_game_lines_2026.csv"

def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as h:
        return list(csv.DictReader(h))

def atomic_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    os.close(fd)
    try:
        with open(tmp, "w", newline="", encoding="utf-8") as h:
            w=csv.DictWriter(h,fieldnames=fields,extrasaction="ignore")
            w.writeheader(); w.writerows(rows)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def set_first(row, names, value):
    for name in names:
        if name in row:
            row[name] = value
            return name
    row[names[0]] = value
    return names[0]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--stage-dir",type=Path,required=True)
    p.add_argument("--display",type=Path,required=True)
    p.add_argument("--coverage",type=Path,required=True)
    a=p.parse_args()
    stage=a.stage_dir if a.stage_dir.is_absolute() else ROOT/a.stage_dir
    display=a.display if a.display.is_absolute() else ROOT/a.display
    coverage_path=a.coverage if a.coverage.is_absolute() else ROOT/a.coverage
    coverage=json.loads(coverage_path.read_text())
    if not coverage.get("acceptance_eligibility"):
        raise SystemExit("SGO acceptance blocked: canonical coverage is not eligible")
    if coverage.get("next_cursor_remaining") or coverage.get("missing_canonical_games") or coverage.get("ambiguous_events"):
        raise SystemExit("SGO acceptance blocked: incomplete or ambiguous canonical coverage")
    normalized=read_csv(stage/"normalized.csv")
    cfbd_by_gid={str(r.get("canonical_game_id")):str(r.get("canonical_cfbd_game_id") or "") for r in normalized}
    accepted=read_csv(TARGET)
    if not accepted:
        raise SystemExit(f"Accepted target is empty: {TARGET}")
    fields=list(accepted[0].keys())
    by_id={str(r.get("game_id")):r for r in accepted}
    changed=[]
    missing_targets={}
    for d in read_csv(display):
        gid=str(d.get("canonical_game_id") or "")
        target_id=cfbd_by_gid.get(gid) or gid
        row=by_id.get(target_id)
        if row is None:
            item=missing_targets.setdefault(
                gid,
                {
                    "canonical_game_id":gid,
                    "target_game_id":target_id,
                    "week":d.get("canonical_site_week"),
                    "away_team":d.get("away_team"),
                    "home_team":d.get("home_team"),
                    "markets":[],
                },
            )
            market=str(d.get("market_type") or "")
            if market and market not in item["markets"]:
                item["markets"].append(market)
            continue
        market=d.get("market_type")
        book=d.get("selected_sportsbook")
        ts=d.get("source_updated_at")
        if market=="spread":
            set_first(row,["market_spread_home"],d.get("home_line"))
            set_first(row,["market_spread_book"],book)
            set_first(row,["market_spread_last_update"],ts)
            set_first(row,["market_spread_price_home","market_spread_price"],d.get("home_price"))
            set_first(row,["market_spread_price_away"],d.get("away_price"))
            home=float(d["home_line"])
            text=f"{row.get('home_team','Home')} {home:+g}"
            set_first(row,["market_spread_text"],text)
            if "market_formatted_spread" in row: row["market_formatted_spread"]=text
        elif market=="total":
            set_first(row,["market_total"],d.get("total_line"))
            set_first(row,["market_total_book"],book)
            set_first(row,["market_total_last_update"],ts)
            set_first(row,["market_total_over_price"],d.get("over_price"))
            set_first(row,["market_total_under_price"],d.get("under_price"))
        elif market=="moneyline":
            set_first(row,["away_moneyline","market_away_moneyline"],d.get("away_price"))
            set_first(row,["home_moneyline","market_home_moneyline"],d.get("home_price"))
            set_first(row,["market_moneyline_book"],book)
            set_first(row,["market_moneyline_last_update"],ts)
        changed.append({"canonical_game_id":gid,"target_game_id":target_id,"market":market,"book":book})
    missing_game_count=len(missing_targets)
    accepted_game_count=int(coverage.get("accepted_quote_games") or 0)
    missing_limit=max(3,int(accepted_game_count*0.05))

    if missing_game_count>missing_limit:
        raise SystemExit(
            "SGO acceptance blocked: "
            f"{missing_game_count} accepted games are absent from the target file "
            f"(limit {missing_limit})"
        )

    if missing_targets:
        print(
            "WARNING: skipped accepted display rows for "
            f"{missing_game_count} game(s) absent from the target file:",
            file=sys.stderr,
        )
        for item in missing_targets.values():
            print(
                " - "
                f"{item['canonical_game_id']} / {item['target_game_id']} "
                f"{item['away_team']} at {item['home_team']} "
                f"(week {item['week']}; markets={','.join(item['markets'])})",
                file=sys.stderr,
            )

    for row in accepted:
        for k in row:
            if k not in fields: fields.append(k)
    atomic_csv(TARGET,accepted,fields)
    report={
        "accepted":True,
        "accepted_with_warnings":bool(missing_targets),
        "changed_market_rows":len(changed),
        "changes":changed,
        "skipped_missing_target_games":list(missing_targets.values()),
        "skipped_missing_target_game_count":missing_game_count,
        "missing_target_failure_limit":missing_limit,
    }
    report_path=stage/"acceptance_report.json"
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
