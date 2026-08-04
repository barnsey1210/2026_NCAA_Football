#!/usr/bin/env python3
"""Provider-free SGO accepted-data simulation in a run-scoped mirror."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPLAY_ID = "replay-20260730T035405Z-85165416-corrected"
COPY_DATA_DIRS = (
    "odds", "site", "history", "markets", "audits", "audit", "agents",
    "signals", "injuries", "ratings", "coach", "rosters", "import",
    "projections", "weather", "schedules", "logos",
)
ROOT_FILES = ("v1.html", "build_market_arbitrage_report.py")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(paths):
    out = {}
    for base in paths:
        if base.is_file():
            out[str(base.relative_to(ROOT))] = sha(base)
        elif base.exists():
            for path in sorted(p for p in base.rglob("*") if p.is_file()):
                out[str(path.relative_to(ROOT))] = sha(path)
    return out


def guarded(path: Path, mirror: Path) -> Path:
    resolved, boundary = path.resolve(), mirror.resolve()
    if resolved != boundary and boundary not in resolved.parents:
        raise RuntimeError(f"PATH ESCAPE BLOCKED: {resolved} is outside {boundary}")
    return path


def read_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields, mirror):
    guarded(path, mirror).parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def fnum(value):
    try: return float(value)
    except (TypeError, ValueError): return None


def changed(a, b):
    x, y = fnum(a), fnum(b)
    return x is not None and y is not None and abs(x-y) > 1e-9


def copy_tree(src: Path, dst: Path, mirror: Path):
    guarded(dst, mirror)
    if not src.exists(): return []
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return [str(p.relative_to(ROOT)) for p in src.rglob("*") if p.is_file()]


def apply_changes(work: Path, display_path: Path, mirror: Path):
    target = work / "data/odds/season_game_lines_2026.csv"
    rows = read_csv(target); fields = list(rows[0])
    by_id = {str(r["game_id"]): r for r in rows}
    display = read_csv(display_path)
    staged_games = {(r["canonical_game_id"],r["canonical_cfbd_game_id"]):r for r in read_csv(mirror/"corrected_replay/normalized.csv")}
    proposed, unchanged = [], []
    expected = Counter()
    touched=set()
    for d in display:
        match=next((s for (gid,_),s in staged_games.items() if gid==d["canonical_game_id"]),None)
        if not match or int(d["canonical_site_week"]) != 0 or d["game_classification"] != "FBS_vs_FBS":
            continue
        row = by_id.get(str(match["canonical_cfbd_game_id"]))
        if row is None: raise RuntimeError(f"canonical accepted row missing: {match['canonical_cfbd_game_id']}")
        market=d["market_type"];specs=[]
        if market=="spread":specs=[("spread","market_spread_home",d.get("home_line"),d.get("home_price"))]
        elif market=="total":specs=[("total","market_total",d.get("total_line"),d.get("over_price"))]
        elif market=="moneyline":specs=[("away_moneyline","away_moneyline",d.get("away_price"),d.get("away_price")),("home_moneyline","home_moneyline",d.get("home_price"),d.get("home_price"))]
        for label,field,newvalue,newprice in specs:
            family="moneyline" if "moneyline" in label else label
            if not changed(row.get(field),newvalue):
                continue
            previous = row.get(field)
            row[field] = newvalue
            if family == "spread":
                row["market_spread_text"] = f"{d['home_team']} {float(newvalue):+g}"
                row["market_formatted_spread"] = row["market_spread_text"]
            proposed.append({
                "canonical_game_id": d["canonical_game_id"], "canonical_cfbd_game_id": match["canonical_cfbd_game_id"],
                "game": f"{d['away_team']} at {d['home_team']}", "market": label,
                "sportsbook": d["selected_sportsbook"], "previous_line": previous,
                "previous_price": "", "new_line": newvalue, "new_price": newprice,
                "source_timestamp": d["source_updated_at"], "availability": d["available"]=="True", "stale_status": d["stale_flag"]=="True",
                "reason_accepted": "same accepted sportsbook; paired, available, fresh current quote; canonical Week 0",
                "target_file": "data/odds/season_game_lines_2026.csv", "target_field": field,
            })
            expected[family] += 1;touched.add(d["canonical_game_id"])
    for (_, _),s in staged_games.items():
        if s["canonical_game_id"] not in touched:unchanged.append({k:s.get(k) for k in ("canonical_game_id","canonical_cfbd_game_id","away_team","home_team","week")})
    if expected != Counter({"spread":5,"total":1,"moneyline":2}):
        raise RuntimeError(f"expected 5 spread, 1 total, and paired 2-side ML field changes; got {dict(expected)}")
    write_csv(target, rows, fields, mirror)
    return proposed, unchanged


def row_count(path):
    if not path.exists(): return 0
    with path.open(errors="ignore") as h: return max(sum(1 for _ in h)-1, 0)


def workspace_hashes(work: Path):
    return {str(p.relative_to(work)):sha(p) for p in work.rglob("*") if p.is_file()}


def run(cmd, work, home):
    env = os.environ.copy(); env.update({"HOME":str(home), "PYTHONPATH":str(work), "NCAAF_DRY_RUN":"1"})
    result = subprocess.run(cmd, cwd=work, env=env, text=True, capture_output=True)
    return {"command":" ".join(cmd),"returncode":result.returncode,"stdout":result.stdout[-4000:],"stderr":result.stderr[-4000:]}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--dry-run-id"); ap.add_argument("--replay-id",default=REPLAY_ID)
    args=ap.parse_args(); dry_id=args.dry_run_id or "acceptance-dry-run-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    mirror=ROOT/"data/control/acceptance_dry_runs"/dry_id
    if mirror.exists(): raise SystemExit(f"Refusing existing dry-run path: {mirror}")
    mirror.mkdir(parents=True); work=mirror/"workspace"; work.mkdir(); home=mirror/"home"; (home/"NCAAF_AUTO").parent.mkdir(parents=True)
    (home/"NCAAF_AUTO").symlink_to(work)
    protected=[ROOT/"data/odds",ROOT/"data/site",ROOT/"data/history",ROOT/"data/markets",ROOT/"build/public_site"]
    before=inventory(protected)
    copied=[]
    copied += copy_tree(ROOT/"scripts",work/"scripts",mirror)
    if (ROOT/"config").exists(): copied += copy_tree(ROOT/"config",work/"config",mirror)
    for name in COPY_DATA_DIRS: copied += copy_tree(ROOT/"data"/name,work/"data"/name,mirror)
    for name in ROOT_FILES:
        if (ROOT/name).exists(): shutil.copy2(ROOT/name,guarded(work/name,mirror)); copied.append(name)
    mirror_baseline = workspace_hashes(work)
    stage=ROOT/"data/control/staging"/args.replay_id
    shutil.copytree(stage,guarded(mirror/"corrected_replay",mirror))
    # Feed the archived response to the existing SGO history appender in the mirror only.
    raw=ROOT/"data/control/raw/sports_game_odds/20260730T035405Z-85165416/response.json"
    raw_dst=work/"data/markets/sgo/sgo_ncaaf_events_raw.json"; raw_dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(raw,raw_dst)
    canonical_dir=work/"data/markets/sgo";canonical_dir.mkdir(parents=True,exist_ok=True)
    artifact_cmd=[sys.executable,"scripts/markets/build_sgo_canonical_artifacts.py","--observations",str(mirror/"corrected_replay/quote_observations.csv"),"--manifest",str(mirror/"corrected_replay/manifest.json"),"--raw",str(raw_dst),"--quotes-out",str(canonical_dir/"sgo_accepted_quotes.csv"),"--display-out",str(canonical_dir/"sgo_canonical_display_lines.csv"),"--coverage-out",str(canonical_dir/"sgo_canonical_coverage.json"),"--exclusions-out",str(canonical_dir/"sgo_canonical_exclusions.csv")]
    artifact_log=run(artifact_cmd,work,home)
    if artifact_log["returncode"]:raise RuntimeError(artifact_log["stderr"])
    proposed,unchanged=apply_changes(work,canonical_dir/"sgo_canonical_display_lines.csv",mirror)
    proposal_fields=list(proposed[0]); write_csv(mirror/"proposed_changes.csv",proposed,proposal_fields,mirror)
    (mirror/"proposed_changes.json").write_text(json.dumps(proposed,indent=2)+"\n")
    (mirror/"unchanged_staged_games.json").write_text(json.dumps(unchanged,indent=2)+"\n")
    histories=[work/"data/odds/game_line_history.csv",work/"data/odds/game_book_line_history.csv"]
    counts0={str(p.relative_to(work)):row_count(p) for p in histories}
    appender_cmds=[
        [sys.executable,"scripts/odds/append_game_line_history.py"],
        [sys.executable,"scripts/odds/append_game_book_line_history.py"],
        [sys.executable,"scripts/odds/append_sgo_game_book_line_history.py","--accepted-quotes","data/markets/sgo/sgo_accepted_quotes.csv","--allow-blocked-dry-run"],
    ]
    logs=[artifact_log]
    for cmd in appender_cmds: logs.append(run(cmd,work,home))
    counts1={str(p.relative_to(work)):row_count(p) for p in histories}
    for cmd in appender_cmds: logs.append(run(cmd,work,home))
    counts2={str(p.relative_to(work)):row_count(p) for p in histories}
    builder_cmds=[
        [sys.executable,"scripts/odds/build_game_line_movement_report.py"],
        [sys.executable,"scripts/site/build_matchups_view.py"],
        [sys.executable,"scripts/history/build_matchup_line_history_clean.py"],
        [sys.executable,"scripts/site/inject_matchup_line_history.py","--asset-only"],
        [sys.executable,"scripts/site/build_odds_screen_v2.py"],
        [sys.executable,"scripts/site/build_schedule_live_enrichment.py"],
    ]
    for cmd in builder_cmds: logs.append(run(cmd,work,home))
    after=inventory(protected)
    if before != after: raise RuntimeError("PRODUCTION BYTE HASH CHANGED during dry run")
    final_hashes=workspace_hashes(work)
    mirror_changed=sorted(k for k,v in final_hashes.items() if mirror_baseline.get(k)!=v)
    mirror_added=sorted(k for k in final_hashes if k not in mirror_baseline)
    mirror_removed=sorted(k for k in mirror_baseline if k not in final_hashes)
    # Schema/basic integrity checks.
    accepted=read_csv(work/"data/odds/season_game_lines_2026.csv")
    prod_accepted=read_csv(ROOT/"data/odds/season_game_lines_2026.csv")
    if len(accepted)!=len(prod_accepted): raise RuntimeError("partial coverage changed accepted row count")
    if any(int(p["week"])!=0 for p in read_csv(stage/"normalized.csv")): raise RuntimeError("non-Week-0 staging row")
    failures=[x for x in logs if x["returncode"]]
    idempotent={k:counts2[k]-counts1[k] for k in counts1}
    daily_issues={
      "newest-book/FanDuel selection":"ALSO PRESENT IN DAILY PIPELINE (parse_sgo selects freshest book, not accepted display book)",
      "cross-book movement comparisons":"ALSO PRESENT IN DAILY PIPELINE (SGO normalized rows and CFBD-priority accepted/history rows use different selection rules)",
      "exact-name matching":"ALSO PRESENT IN DAILY PIPELINE (limited parser aliases and downstream date/team matching)",
      "silent unmatched games":"ALSO PRESENT IN DAILY PIPELINE (production parser has no canonical mapping threshold)",
      "canonical game_id mapping":"ALSO PRESENT IN DAILY PIPELINE (SGO CSV retains provider ID, not canonical game_id)",
      "Week 0 and Week 1 merging":"ALSO PRESENT IN DAILY PIPELINE (provider seasonWeek is trusted; canonical week is not resolved)",
      "pagination and partial coverage":"ALSO PRESENT IN DAILY PIPELINE (single limit=250 request; nextCursor is not followed or gated)",
      "neutral-site loss":"ALSO PRESENT IN DAILY PIPELINE (SGO normalized CSV does not preserve canonical neutral_site)",
      "unavailable-market fallback":"ALSO PRESENT IN DAILY PIPELINE (freshest selector falls back to unavailable quotes)",
      "stale-market fallback":"ALSO PRESENT IN DAILY PIPELINE (no explicit quote-age ceiling)",
      "independently paired total sides":"ALSO PRESENT IN DAILY PIPELINE",
      "independently paired moneyline sides":"ALSO PRESENT IN DAILY PIPELINE",
      "audit observation deduplication":"PREVIEW-ONLY (corrected quote ledger uses stable quote identity)",
      "canonical history deduplication":"ALSO PRESENT IN DAILY PIPELINE; general snapshot is state-idempotent, SGO per-book key includes snapshot timestamp",
    }
    report={
      "dry_run_id":dry_id,"mirror_path":str(mirror),"coverage":"PARTIAL","production_acceptance":"BLOCKED",
      "external_calls":0,"accepted_production_modified":False,"publication":"SKIPPED",
      "copied_source_file_count":len(copied),"copied_sources":sorted(copied),"proposed_changes":proposed,
      "unchanged_staged_games":unchanged,"history_rows_before":counts0,"history_rows_after_first":counts1,
      "history_rows_after_second":counts2,"second_run_rows_appended":idempotent,"commands":logs,
      "builder_failures":failures,"production_hashes_unchanged":before==after,"daily_pipeline_issue_classification":daily_issues,
      "mirror_files_changed":mirror_changed,"mirror_files_added":mirror_added,"mirror_files_removed":mirror_removed,
      "known_acceptance_path_gaps":[
        "season_game_lines_2026.csv has no spread/total price or provider quote timestamp fields",
        "generic per-book history appender does not consume SGO",
        "SGO per-book appender ingests all archived events and does not enforce canonical week, mapping, availability, staleness, or paired sides",
      ],
      "classification":"NEEDS ACCEPTANCE-PATH FIX" if failures or any(idempotent.values()) else "NEEDS ACCEPTANCE-PATH FIX",
      "v2_html_modified":False,"protected_production_hashes":before,
      "skipped_builders":["ratings","futures","simulations","Shadow","full-site publication","daily email"],
    }
    (mirror/"dry_run_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    lines=["# SGO accepted-data dry run", "", "**COVERAGE: PARTIAL**", "**PRODUCTION ACCEPTANCE: BLOCKED**", "**DRY-RUN VALIDATION ONLY**", "",
      f"- Dry-run ID: `{dry_id}`",f"- External calls: 0",f"- Proposed changed fields: {len(proposed)}",f"- Production hashes unchanged: {before==after}",
      f"- Canonical history second-run additions: `{idempotent}`",f"- Builder failures: {len(failures)}",f"- Classification: **{report['classification']}**","",
      "The mirror proves that validated same-book values can be applied without deleting accepted rows. It also proves the current acceptance/history schema is not ready for safe SGO promotion: spread/total prices and quote timestamps have no accepted target fields, and the SGO per-book appender bypasses the corrected canonical-week/mapping/freshness/paired-side policy."]
    (mirror/"dry_run_summary.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({k:report[k] for k in ("dry_run_id","mirror_path","external_calls","history_rows_before","history_rows_after_first","history_rows_after_second","second_run_rows_appended","builder_failures","classification")},indent=2))
    return 1 if failures else 0

if __name__ == "__main__": raise SystemExit(main())
