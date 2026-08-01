#!/usr/bin/env python3
import re
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

RAW_PATHS = [
    Path("data/injuries/cfbdepth_latest_injury_status_raw.csv"),
    Path("data/injuries/cfbdepth_injury_articles_raw.csv"),
]

PLAYER_PATH = Path("data/rosters/player_importance_2026_alert_ready.csv")
OUT_NORMALIZED = Path("data/injuries/injury_events_normalized.csv")
OUT_ALERTS = Path("data/injuries/injury_alerts.csv")

STATUS_PATTERNS = {
    "Out": r"\bout\b|\bwill miss\b|\bmisses\b|\bmissed\b|\bnot play\b|\bruled out\b",
    "Doubtful": r"\bdoubtful\b",
    "Questionable": r"\bquestionable\b|\buncertain\b|\bgame-time decision\b",
    "Probable": r"\bprobable\b|\bexpected to play\b",
    "Limited": r"\blimited\b|\bnot practicing\b|\bno practice\b|\bpractice\b|\bboot\b",
    "Suspended": r"\bsuspended\b|\bsuspension\b",
    "Status Change": r"\bstatus\b|\bavailability\b|\bavailable\b|\binjury\b|\binjured\b",
}

STATUS_MULT = {
    "Out": 1.00,
    "Doubtful": 0.85,
    "Questionable": 0.45,
    "Probable": 0.10,
    "Limited": 0.25,
    "Suspended": 0.90,
    "Status Change": 0.20,
    "Unknown": 0.10,
}

def detect_status(text):
    blob = str(text or "").lower()
    for status, pat in STATUS_PATTERNS.items():
        if re.search(pat, blob, flags=re.I):
            return status
    return "Unknown"

def tier(score):
    if score >= 7:
        return "Tier 1"
    if score >= 4:
        return "Tier 2"
    if score >= 2:
        return "Review"
    return "Log"

def load_raws():
    frames = []
    skipped_empty = []

    for p in RAW_PATHS:
        if not p.exists():
            continue

        try:
            df = pd.read_csv(p)
        except pd.errors.EmptyDataError:
            skipped_empty.append(str(p))
            continue

        if df.empty:
            skipped_empty.append(str(p))
            continue

        df["input_file"] = str(p)
        frames.append(df)

    if skipped_empty:
        print("empty injury inputs skipped:", ", ".join(skipped_empty))

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)

def main():
    built_at = datetime.now(timezone.utc).isoformat()
    raw = load_raws()

    if PLAYER_PATH.exists():
        players = pd.read_csv(PLAYER_PATH)
    else:
        players = pd.DataFrame()

    player_records = []
    if not players.empty and "player" in players.columns:
        for _, r in players.iterrows():
            name = str(r.get("player", "")).strip()
            if name:
                player_records.append(r)

    norm_rows = []

    for _, r in raw.iterrows():
        row_type = str(r.get("row_type", "") or "")
        title = str(r.get("item_title", "") or "")
        url = str(r.get("item_url", "") or "")
        text = str(r.get("raw_text", "") or title)

        generic_titles = {
            "PAGE_SNAPSHOT",
            "FETCH_ERROR",
            "Injury & Status",
            "Latest Injury & Status",
            "Injury & Status Report",
            "Injury Impact Report",
            "Latest Injury & Status Updates >",
            "Injury / Status Key",
        }

        generic_urls = [
            "latest-injury-status",
            "injury-report",
            "injury-impact-report",
        ]

        if row_type in ["page", "error"]:
            include_for_alerting = False
        elif title in generic_titles:
            include_for_alerting = False
        elif any(x in url for x in generic_urls) and row_type != "article_detail":
            include_for_alerting = False
        else:
            include_for_alerting = True

        generic_titles = {
            "PAGE_SNAPSHOT",
            "FETCH_ERROR",
            "Injury & Status",
            "Latest Injury & Status",
            "Injury & Status Report",
            "Injury Impact Report",
            "Latest Injury & Status Updates >",
            "Injury / Status Key",
        }

        generic_url_parts = [
            "latest-injury-status",
            "injury-report",
            "injury-impact-report",
        ]

        generic_page = (
            row_type in ["page", "error"]
            or title in generic_titles
            or (any(x in url for x in generic_url_parts) and row_type != "article_detail")
        )

        status = detect_status(f"{title} {text} {url}")

        matched = None
        for pr in player_records:
            player_name = str(pr.get("player", "")).strip()
            if player_name and player_name.lower() in f"{title} {text}".lower():
                matched = pr
                break

        team = ""
        player = ""
        position = ""
        importance = 0.0
        matched_depth = False

        if matched is not None:
            team = str(matched.get("team", "") or "")
            player = str(matched.get("player", "") or "")
            position = str(matched.get("position", "") or "")
            importance = float(matched.get("importance_score", 0) or 0)
            matched_depth = True

        keyword_score = float(r.get("relevance_score", 0) or 0)

        if not matched_depth:
            if row_type == "article" and include_for_alerting:
                importance = min(3.0, 0.75 * keyword_score)
            else:
                importance = 0.0

        impact_score = round(importance * STATUS_MULT.get(status, 0.10), 2)

        if generic_page and not matched_depth:
            impact_score = 0.0

        norm_rows.append({
            "built_at": built_at,
            "source": r.get("source", ""),
            "source_url": r.get("source_url", ""),
            "item_title": title,
            "item_url": url,
            "row_type": row_type,
            "team": team,
            "player": player,
            "position": position,
            "status": status,
            "matched_depth_chart_player": matched_depth,
            "importance_score": importance,
            "impact_score": impact_score,
            "alert_tier": tier(impact_score),
            "raw_text": text,
        })

    norm = pd.DataFrame(norm_rows)
    OUT_NORMALIZED.parent.mkdir(parents=True, exist_ok=True)

    if norm.empty:
        existing_columns = []

        for existing_path in (OUT_NORMALIZED, OUT_ALERTS):
            if existing_path.exists() and existing_path.stat().st_size:
                try:
                    existing_columns = list(pd.read_csv(existing_path, nrows=0).columns)
                except (pd.errors.EmptyDataError, OSError):
                    existing_columns = []
                if existing_columns:
                    break

        if not existing_columns:
            existing_columns = [
                "alert_tier",
                "impact_score",
                "status",
                "row_type",
                "team",
                "player",
                "position",
                "item_title",
                "item_url",
            ]

        empty = pd.DataFrame(columns=existing_columns)
        empty.to_csv(OUT_NORMALIZED, index=False)
        empty.to_csv(OUT_ALERTS, index=False)

        print("injury source status: UNAVAILABLE")
        print("normalized rows: 0")
        print("alert/review rows: 0")
        print("wrote:", OUT_NORMALIZED)
        print("wrote:", OUT_ALERTS)
        return

    norm.to_csv(OUT_NORMALIZED, index=False)

    alerts = norm[norm["alert_tier"].isin(["Tier 1", "Tier 2", "Review"])].copy()
    alerts = alerts.sort_values(["impact_score", "status"], ascending=[False, True])
    alerts.to_csv(OUT_ALERTS, index=False)

    print("normalized rows:", len(norm))
    print("alert/review rows:", len(alerts))
    print("wrote:", OUT_NORMALIZED)
    print("wrote:", OUT_ALERTS)

    if not alerts.empty:
        print(alerts[["alert_tier", "impact_score", "status", "row_type", "team", "player", "position", "item_title", "item_url"]].head(40).to_string(index=False))

if __name__ == "__main__":
    main()
