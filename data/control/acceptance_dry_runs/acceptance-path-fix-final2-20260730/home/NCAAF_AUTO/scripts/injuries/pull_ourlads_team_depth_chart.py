#!/usr/bin/env python3
import hashlib
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd

OUT_RAW = Path("data/rosters/ourlads_depth_charts_raw.csv")
OUT_IMPORTANCE = Path("data/rosters/player_importance_2026.csv")
SNAPSHOT_DIR = Path("data/rosters/ourlads_team_snapshots")

POSITION_GROUPS = {
    "QB": "QB",
    "RB": "RB",
    "FB": "RB",
    "WR": "WR",
    "WR-X": "WR",
    "WR-Z": "WR",
    "WR-SL": "WR",
    "TE": "TE",
    "LT": "OL",
    "LG": "OL",
    "C": "OL",
    "RG": "OL",
    "RT": "OL",
    "LDE": "DL",
    "RDE": "DL",
    "DE": "DL",
    "EDGE": "DL",
    "NT": "DL",
    "DT": "DL",
    "WLB": "LB",
    "MLB": "LB",
    "SLB": "LB",
    "OLB": "LB",
    "ILB": "LB",
    "SAM": "LB",
    "MIKE": "LB",
    "WILL": "LB",
    "LB": "LB",
    "WOLF": "DL",
    "JACK": "DL",
    "BUCK": "DL",
    "BAN": "DL",
    "STING": "LB",
    "SPUR": "S",
    "HUSKY": "CB",
    "STAR": "CB",
    "NICKEL": "CB",
    "ROVER": "S",
    "LCB": "CB",
    "RCB": "CB",
    "CB": "CB",
    "NB": "CB",
    "SS": "S",
    "FS": "S",
    "S": "S",
    "PT": "ST",
    "PK": "ST",
    "KO": "ST",
    "LS": "ST",
    "H": "ST",
    "PR": "ST",
    "KR": "ST",
}

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 NCAAF depth chart monitor",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def clean_text(x):
    if pd.isna(x):
        return ""
    return re.sub(r"\s+", " ", str(x)).strip()

def parse_updated(html):
    m = re.search(r"Updated:\s*([^<\n]+)", html, flags=re.I)
    if m:
        return clean_text(m.group(1))
    text = re.sub(r"<[^>]+>", " ", html)
    m = re.search(r"Updated:\s*([A-Za-z0-9/: ,]+? ET)", text, flags=re.I)
    return clean_text(m.group(1)) if m else ""

def parse_player_class(player_raw):
    raw = clean_text(player_raw)
    if not raw:
        return "", "", False, False

    is_transfer = "/TR" in raw or " TR" in raw
    is_freshman = bool(re.search(r"\bFR\b", raw))

    class_match = re.search(r"\b((?:RS\s+)?(?:FR|SO|JR|SR|GR)(?:/TR)?)$", raw)
    player_class = class_match.group(1) if class_match else ""

    player = raw
    if player_class:
        player = raw[:class_match.start()].strip()

    return player, player_class, is_transfer, is_freshman

def position_group(pos):
    pos = clean_text(pos).upper()
    return POSITION_GROUPS.get(pos, pos)

def importance_score(pos, depth_rank):
    pos = clean_text(pos).upper()
    group = position_group(pos)

    if group == "QB":
        return {1: 10, 2: 4, 3: 2}.get(depth_rank, 1)

    if group in ["RB", "WR", "TE"]:
        return {1: 5, 2: 3, 3: 1.5}.get(depth_rank, 0.5)

    if group == "OL":
        return {1: 4, 2: 2}.get(depth_rank, 0.5)

    if group in ["DL", "LB", "CB", "S"]:
        return {1: 4, 2: 2, 3: 1}.get(depth_rank, 0.5)

    if group == "ST":
        return {1: 1.5, 2: 0.5}.get(depth_rank, 0.25)

    return {1: 2, 2: 1}.get(depth_rank, 0.25)

def flatten_columns(df):
    cols = []
    for c in df.columns:
        if isinstance(c, tuple):
            parts = [str(x) for x in c if "Unnamed" not in str(x)]
            cols.append(" ".join(parts).strip())
        else:
            cols.append(str(c).strip())
    df = df.copy()
    df.columns = cols
    return df

def table_section_name(df, fallback):
    txt = " ".join([str(c) for c in df.columns])
    if "Offense" in txt:
        return "Offense"
    if "Defense" in txt:
        return "Defense"
    if "Special" in txt:
        return "Special Teams"
    return fallback

def parse_tables(team, url, html):
    pulled_at = datetime.now(timezone.utc).isoformat()
    updated = parse_updated(html)
    rows = []

    try:
        tables = pd.read_html(StringIO(html))
    except Exception as e:
        raise SystemExit(f"pandas read_html failed: {e}")

    section_counter = 0

    for t in tables:
        df = flatten_columns(t)
        cols = list(df.columns)

        has_pos = any(str(c).lower() == "pos" for c in cols)
        has_player = any("player" in str(c).lower() for c in cols)

        if not has_pos or not has_player:
            continue

        section_counter += 1
        section = ["Offense", "Defense", "Special Teams"][section_counter - 1] if section_counter <= 3 else f"Section {section_counter}"

        pos_col = next(c for c in cols if str(c).lower() == "pos")

        for _, row in df.iterrows():
            pos = clean_text(row.get(pos_col, ""))
            if not pos or pos.lower() == "pos":
                continue

            for i, c in enumerate(cols):
                m = re.search(r"player\s*([1-5])", str(c), flags=re.I)
                if not m:
                    continue

                depth_rank = int(m.group(1))
                player_raw = clean_text(row.get(c, ""))
                if not player_raw:
                    continue

                no_col = cols[i - 1] if i > 0 else ""
                jersey = clean_text(row.get(no_col, "")) if no_col else ""

                player, player_class, is_transfer, is_freshman = parse_player_class(player_raw)
                if not player:
                    continue

                rows.append({
                    "pulled_at": pulled_at,
                    "source": "Ourlads",
                    "team": team,
                    "url": url,
                    "updated_text": updated,
                    "section": section,
                    "position": pos,
                    "position_group": position_group(pos),
                    "depth_rank": depth_rank,
                    "jersey": jersey,
                    "player": player,
                    "player_raw": player_raw,
                    "player_class": player_class,
                    "is_transfer": is_transfer,
                    "is_true_freshman": is_freshman,
                    "content_hash": hashlib.sha256(f"{team}|{pos}|{depth_rank}|{player_raw}|{updated}".encode()).hexdigest(),
                })

    return rows

def main():
    if len(sys.argv) < 3:
        raise SystemExit('Usage: python3 scripts/injuries/pull_ourlads_team_depth_chart.py "Ohio State" "https://..."')

    team = sys.argv[1]
    url = sys.argv[2]

    html = fetch(url)

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe_team = re.sub(r"[^a-zA-Z0-9]+", "_", team.lower()).strip("_")
    snapshot = SNAPSHOT_DIR / f"{safe_team}.html"
    snapshot.write_text(html, errors="ignore")

    rows = parse_tables(team, url, html)
    df = pd.DataFrame(rows)

    if df.empty:
        raise SystemExit("No depth chart rows parsed")

    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)

    if OUT_RAW.exists():
        old = pd.read_csv(OUT_RAW)
        old = old[~((old["team"].astype(str) == team) & (old["source"].astype(str) == "Ourlads"))]
        raw = pd.concat([old, df], ignore_index=True)
    else:
        raw = df.copy()

    raw.to_csv(OUT_RAW, index=False)

    imp = df.copy()
    imp["starter_flag"] = imp["depth_rank"].eq(1)
    imp["role"] = imp["position_group"] + imp["depth_rank"].astype(str)
    imp["snap_share"] = ""
    imp["usage_share"] = ""
    imp["returning_starter"] = ""
    imp["importance_score"] = imp.apply(lambda r: importance_score(r["position"], int(r["depth_rank"])), axis=1)
    imp["last_updated"] = imp["updated_text"]
    imp["notes"] = "Ourlads depth chart import"

    imp_out = imp[[
        "team",
        "player",
        "position",
        "depth_rank",
        "starter_flag",
        "role",
        "snap_share",
        "usage_share",
        "returning_starter",
        "importance_score",
        "source",
        "last_updated",
        "notes",
    ]].copy()

    if OUT_IMPORTANCE.exists():
        old_imp = pd.read_csv(OUT_IMPORTANCE)
        old_imp = old_imp[~((old_imp["team"].astype(str) == team) & (old_imp["source"].astype(str) == "Ourlads"))]
        merged = pd.concat([old_imp, imp_out], ignore_index=True)
    else:
        merged = imp_out.copy()

    merged.to_csv(OUT_IMPORTANCE, index=False)

    print("team:", team)
    print("rows parsed:", len(df))
    print("updated:", df["updated_text"].iloc[0] if "updated_text" in df.columns else "")
    print("wrote:", OUT_RAW)
    print("wrote:", OUT_IMPORTANCE)
    print("snapshot:", snapshot)

    if os.environ.get("OURLADS_QUIET", "0") != "1":
        show_cols = ["team", "section", "position", "depth_rank", "jersey", "player", "player_class", "importance_score"]
        print(df.assign(importance_score=df.apply(lambda r: importance_score(r["position"], int(r["depth_rank"])), axis=1))[show_cols].head(80).to_string(index=False))

if __name__ == "__main__":
    main()
