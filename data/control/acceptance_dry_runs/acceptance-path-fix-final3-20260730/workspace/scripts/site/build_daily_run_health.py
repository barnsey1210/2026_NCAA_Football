#!/usr/bin/env python3
"""Build a lightweight Daily Run Health page for the 2026 NCAAF site.

Run from project root: ~/NCAAF_AUTO
Outputs:
  data/health/daily_run_health.json
  data/health/daily_run_health.csv
  health.html
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path.cwd()
OUT_DIR = ROOT / "data" / "health"
OUT_JSON = OUT_DIR / "daily_run_health.json"
OUT_CSV = OUT_DIR / "daily_run_health.csv"
OUT_HTML = ROOT / "health.html"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def mtime(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")


def file_size(path: Path) -> Optional[int]:
    return path.stat().st_size if path.exists() else None


def read_metric_csv(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    out: Dict[str, Any] = {}
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                k = str(row.get("metric", "")).strip()
                v = str(row.get("value", "")).strip()
                if not k:
                    continue
                try:
                    if re.fullmatch(r"-?\d+", v):
                        out[k] = int(v)
                    elif re.fullmatch(r"-?\d+\.\d+", v):
                        out[k] = float(v)
                    else:
                        out[k] = v
                except Exception:
                    out[k] = v
    except Exception as e:
        out["read_error"] = str(e)
    return out


def read_rows(path: Path, limit: Optional[int] = None) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    rows: List[Dict[str, str]] = []
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if limit is not None and i >= limit:
                    break
                rows.append({k: (v if v is not None else "") for k, v in row.items()})
    except Exception:
        return []
    return rows


def count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        return 0


def status_from_audit(summary: Dict[str, Any], kind: str) -> str:
    if not summary:
        return "missing"
    major = int(summary.get("major", 0) or 0)
    bad = int(summary.get("bad", 0) or 0)
    warn = int(summary.get("warn", 0) or 0)
    if kind == "spread":
        if major or bad:
            return "bad"
        if warn:
            return "warn"
        return "ok"
    if major or warn:
        return "warn"
    return "ok"


def status_label(status: str) -> str:
    return {"ok": "OK", "warn": "WATCH", "bad": "FAIL", "missing": "MISSING"}.get(status, status.upper())


def collect_weather() -> Dict[str, Any]:
    loc_path = ROOT / "data" / "weather" / "game_weather_locations.csv"
    latest_path = ROOT / "data" / "weather" / "game_weather_latest.csv"
    hist_path = ROOT / "data" / "weather" / "game_weather_history.csv"

    loc_rows = read_rows(loc_path)
    missing_loc = 0
    placeholders = 0
    for r in loc_rows:
        venue = f"{r.get('venue','')} {r.get('home_team','')}"
        lat = str(r.get("latitude", "")).strip()
        lon = str(r.get("longitude", "")).strip()
        missing = not lat or lat.lower() == "nan" or not lon or lon.lower() == "nan"
        if missing:
            if re.search(r"No\. 1|TBD|Champion|Sun Belt West", venue, re.I):
                placeholders += 1
            else:
                missing_loc += 1

    latest_rows = read_rows(latest_path)
    status_counts = Counter()
    flag_counts = Counter()
    for r in latest_rows:
        status = (r.get("weather_status") or r.get("status") or r.get("forecast_status") or "unknown").strip() or "unknown"
        status_counts[status] += 1
        flags = (r.get("weather_flags") or r.get("flags") or "").strip()
        for part in re.split(r"[|,;]", flags):
            part = part.strip()
            if part:
                flag_counts[part] += 1

    return {
        "locations_file": str(loc_path),
        "locations_total": len(loc_rows),
        "locations_missing_real": missing_loc,
        "locations_missing_placeholder": placeholders,
        "latest_rows": len(latest_rows),
        "latest_status_counts": dict(status_counts.most_common()),
        "weather_flag_counts": dict(flag_counts.most_common(12)),
        "latest_mtime": mtime(latest_path),
        "history_rows": count_rows(hist_path),
        "history_mtime": mtime(hist_path),
    }


def collect_line_history() -> Dict[str, Any]:
    p = ROOT / "data" / "history" / "game_line_model_history.csv"
    rows = read_rows(p)
    games = set()
    snapshots = set()
    latest = ""
    for r in rows:
        gid = r.get("game_id") or r.get("cfbd_game_id") or ""
        if gid:
            games.add(gid)
        snap = r.get("snapshot_label") or r.get("snapshot_date") or r.get("run_date") or ""
        if snap:
            snapshots.add(snap)
            latest = max(latest, snap)
    return {
        "file": str(p),
        "rows": len(rows),
        "unique_games": len(games),
        "unique_snapshots": len(snapshots),
        "latest_snapshot": latest,
        "mtime": mtime(p),
    }


def collect_injuries() -> Dict[str, Any]:
    alerts = ROOT / "data" / "injuries" / "injury_alerts.csv"
    team_scores = ROOT / "data" / "injuries" / "team_injury_scores.csv"
    game_alerts = ROOT / "data" / "injuries" / "game_injury_alerts.csv"
    team_rows = read_rows(team_scores)
    game_rows = read_rows(game_alerts)

    def nonzero(rows: List[Dict[str, str]], fields: List[str]) -> int:
        n = 0
        for r in rows:
            for f in fields:
                try:
                    if abs(float(r.get(f, "") or 0)) > 0:
                        n += 1
                        break
                except Exception:
                    pass
        return n

    return {
        "alerts_rows": count_rows(alerts),
        "alerts_mtime": mtime(alerts),
        "team_score_rows": len(team_rows),
        "teams_with_nonzero_score": nonzero(team_rows, ["injury_score", "team_injury_score", "total_injury_score"]),
        "game_alert_rows": len(game_rows),
        "games_with_nonzero_score": nonzero(game_rows, ["away_injury_score", "home_injury_score", "injury_edge_home"]),
        "game_alerts_mtime": mtime(game_alerts),
    }


def collect_site() -> Dict[str, Any]:
    index = ROOT / "index.html"
    matchup = ROOT / "matchup.html"
    html = index.read_text(errors="ignore") if index.exists() else ""
    matchup_html = matchup.read_text(errors="ignore") if matchup.exists() else ""
    bad_markers = [
        "inject_game_injury_scores.py",
        "patch_schedule_injury_ui.py",
        "patch_schedule_injury_inline_badge.py",
    ]
    return {
        "index_exists": index.exists(),
        "index_mtime": mtime(index),
        "index_size": file_size(index),
        "matchup_exists": matchup.exists(),
        "matchup_mtime": mtime(matchup),
        "matchup_size": file_size(matchup),
        "matchup_links": html.count("matchup.html?game_id"),
        "injury_overlay_data_blocks": html.count('id="game-injury-overlay-data"'),
        "injury_overlay_script_blocks": html.count('id="game-injury-overlay-script"'),
        "bad_old_injury_markers": {m: (m in html or m in matchup_html) for m in bad_markers},
        "weather_card_present": "Weather" in matchup_html and ("weather" in matchup_html.lower()),
        "betting_edge_snapshot_present": "Betting Edge Snapshot" in matchup_html or "BETTING EDGE SNAPSHOT" in matchup_html,
    }


def pill(status: str) -> str:
    cls = {"ok": "ok", "warn": "warn", "bad": "bad", "missing": "missing"}.get(status, "missing")
    return f'<span class="pill {cls}">{escape(status_label(status))}</span>'


def fmt(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "Yes" if v else "No"
    return escape(str(v))


def metric_card(title: str, status: str, rows: List[tuple[str, Any]]) -> str:
    body = "".join(f"<div class='kv'><span>{escape(k)}</span><strong>{fmt(v)}</strong></div>" for k, v in rows)
    return f"""
    <section class="card">
      <div class="card-head"><h2>{escape(title)}</h2>{pill(status)}</div>
      <div class="kv-wrap">{body}</div>
    </section>
    """


def build_html(payload: Dict[str, Any]) -> str:
    spread = payload["audits"]["spread"]
    total = payload["audits"]["total"]
    weather = payload["weather"]
    hist = payload["line_history"]
    inj = payload["injuries"]
    site = payload["site"]

    overall = "ok"
    if payload["statuses"]["spread"] == "bad":
        overall = "bad"
    elif any(v in ("warn", "missing") for v in payload["statuses"].values()):
        overall = "warn"

    weather_counts = weather.get("latest_status_counts", {})
    weather_counts_html = "".join(f"<span class='mini'>{escape(str(k))}: {escape(str(v))}</span>" for k, v in list(weather_counts.items())[:10]) or "<span class='muted'>No weather rows yet</span>"

    bad_markers = site.get("bad_old_injury_markers", {})
    bad_marker_html = "".join(f"<span class='mini {'badtxt' if v else ''}'>{escape(k)}: {fmt(v)}</span>" for k, v in bad_markers.items())

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NCAAF Daily Run Health</title>
<style>
:root{{--bg:#071225;--card:#101b31;--card2:#0b1426;--line:#263852;--text:#e9eef8;--muted:#9aa9bf;--green:#1fbf75;--yellow:#d6ad25;--red:#ff5f57;}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at top,#10213f,#071225 48%,#050b17);color:var(--text);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;padding:24px}}
.wrap{{max-width:1280px;margin:0 auto}} .hero{{border:1px solid var(--line);background:linear-gradient(180deg,#14213a,#0b1426);border-radius:20px;padding:22px 24px;display:flex;justify-content:space-between;gap:16px;align-items:center;box-shadow:0 18px 50px rgba(0,0,0,.25)}}
h1{{margin:0;font-size:30px;letter-spacing:-.03em}} .sub{{color:var(--muted);margin-top:6px;font-weight:700}} .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:16px}} .card{{border:1px solid var(--line);background:linear-gradient(180deg,rgba(16,27,49,.96),rgba(8,17,34,.96));border-radius:18px;padding:16px;min-height:190px}} .wide{{grid-column:span 3}}
.card-head{{display:flex;justify-content:space-between;align-items:center;gap:10px;border-bottom:1px solid #22324a;padding-bottom:10px;margin-bottom:12px}} h2{{font-size:15px;letter-spacing:.11em;text-transform:uppercase;margin:0;color:#dbe6f7}} .pill{{border-radius:999px;padding:6px 10px;font-size:12px;font-weight:950;border:1px solid #344762;background:#17233a;color:#cfd9e8}} .pill.ok{{background:#0d3b2a;color:#c7ffdc;border-color:#1c8a55}} .pill.warn{{background:#463912;color:#ffe596;border-color:#937522}} .pill.bad{{background:#4b1518;color:#ffd0d0;border-color:#b23b3f}} .pill.missing{{background:#263044;color:#cdd6e5}}
.kv-wrap{{display:grid;gap:8px}} .kv{{display:flex;justify-content:space-between;gap:10px;border-bottom:1px solid rgba(38,56,82,.45);padding:5px 0;color:var(--muted);font-size:13px}} .kv strong{{color:var(--text);text-align:right}} .mini-row{{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}} .mini{{display:inline-flex;align-items:center;border:1px solid #2b3d58;background:#111d32;color:#cbd5e5;border-radius:999px;padding:6px 9px;font-size:12px;font-weight:800}} .badtxt{{border-color:#994148;color:#ffd0d0;background:#3b1519}} .muted{{color:var(--muted)}}
.table{{width:100%;border-collapse:collapse;margin-top:8px}} .table th,.table td{{border-bottom:1px solid #253750;padding:9px;text-align:left;font-size:13px}} .table th{{color:#9fb0c9;text-transform:uppercase;letter-spacing:.12em;font-size:11px}} code{{background:#101b31;border:1px solid #263852;border-radius:6px;padding:2px 5px}}
@media(max-width:900px){{.hero{{display:block}}.grid{{grid-template-columns:1fr}}.wide{{grid-column:span 1}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <div><h1>Daily Run Health</h1><div class="sub">Generated {escape(payload['generated_at'])}</div></div>
    <div>{pill(overall)}</div>
  </div>
  <div class="grid">
    {metric_card('Projection spread audit', payload['statuses']['spread'], [('Games', spread.get('games','—')), ('OK', spread.get('ok','—')), ('Warn', spread.get('warn','—')), ('Bad', spread.get('bad','—')), ('Major', spread.get('major','—')), ('Missing team / skipped', spread.get('missing_team','—')), ('Updated', mtime(ROOT / 'data/audits/game_projection_spread_audit_summary.csv'))])}
    {metric_card('Projection total audit', payload['statuses']['total'], [('Games', total.get('games','—')), ('OK', total.get('ok','—')), ('Info', total.get('info','—')), ('Warn', total.get('warn','—')), ('Major', total.get('major','—')), ('Market totals', total.get('has_market_total','—')), ('Massey totals', total.get('has_massey_total','—'))])}
    {metric_card('Weather', payload['statuses']['weather'], [('Venue rows', weather.get('locations_total','—')), ('Missing real venues', weather.get('locations_missing_real','—')), ('Placeholder venues', weather.get('locations_missing_placeholder','—')), ('Latest rows', weather.get('latest_rows','—')), ('History rows', weather.get('history_rows','—')), ('Updated', weather.get('latest_mtime','—'))])}
    <section class="card wide"><div class="card-head"><h2>Weather status breakdown</h2>{pill(payload['statuses']['weather'])}</div><div class="mini-row">{weather_counts_html}</div></section>
    {metric_card('Line / model history', payload['statuses']['history'], [('Rows', hist.get('rows','—')), ('Unique games', hist.get('unique_games','—')), ('Unique snapshots', hist.get('unique_snapshots','—')), ('Latest snapshot', hist.get('latest_snapshot','—')), ('Updated', hist.get('mtime','—'))])}
    {metric_card('Injuries', payload['statuses']['injuries'], [('Injury alerts', inj.get('alerts_rows','—')), ('Team score rows', inj.get('team_score_rows','—')), ('Teams nonzero', inj.get('teams_with_nonzero_score','—')), ('Game rows', inj.get('game_alert_rows','—')), ('Games nonzero', inj.get('games_with_nonzero_score','—')), ('Updated', inj.get('game_alerts_mtime','—'))])}
    {metric_card('Site output', payload['statuses']['site'], [('Index exists', site.get('index_exists')), ('Matchup exists', site.get('matchup_exists')), ('Matchup links', site.get('matchup_links')), ('Injury overlay data blocks', site.get('injury_overlay_data_blocks')), ('Injury overlay script blocks', site.get('injury_overlay_script_blocks')), ('Weather card present', site.get('weather_card_present')), ('Edge snapshot present', site.get('betting_edge_snapshot_present')), ('Matchup updated', site.get('matchup_mtime'))])}
    <section class="card wide"><div class="card-head"><h2>Unsafe marker check</h2>{pill('ok' if not any(bad_markers.values()) else 'bad')}</div><div class="mini-row">{bad_marker_html}</div></section>
  </div>
</div>
</body>
</html>"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    spread = read_metric_csv(ROOT / "data" / "audits" / "game_projection_spread_audit_summary.csv")
    total = read_metric_csv(ROOT / "data" / "audits" / "game_projection_total_audit_summary.csv")
    weather = collect_weather()
    hist = collect_line_history()
    injuries = collect_injuries()
    site = collect_site()

    statuses = {
        "spread": status_from_audit(spread, "spread"),
        "total": status_from_audit(total, "total"),
        "weather": "ok" if weather.get("locations_missing_real", 9999) == 0 else "warn",
        "history": "ok" if hist.get("rows", 0) > 0 else "missing",
        "injuries": "ok" if injuries.get("game_alert_rows", 0) > 0 else "warn",
        "site": "ok" if site.get("matchup_exists") and site.get("matchup_links", 0) > 0 and site.get("injury_overlay_data_blocks", 0) == 1 else "warn",
    }

    payload = {
        "generated_at": now_iso(),
        "statuses": statuses,
        "audits": {"spread": spread, "total": total},
        "weather": weather,
        "line_history": hist,
        "injuries": injuries,
        "site": site,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["section", "metric", "value"])
        for section, data in [
            ("status", statuses),
            ("spread_audit", spread),
            ("total_audit", total),
            ("weather", weather),
            ("line_history", hist),
            ("injuries", injuries),
            ("site", site),
        ]:
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    v = json.dumps(v)
                w.writerow([section, k, v])

    OUT_HTML.write_text(build_html(payload), encoding="utf-8")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_CSV}")
    print(f"wrote: {OUT_HTML}")
    print("statuses:", statuses)


if __name__ == "__main__":
    main()
