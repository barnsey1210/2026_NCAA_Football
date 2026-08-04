#!/usr/bin/env python3
import re
from pathlib import Path
from urllib.parse import unquote

import pandas as pd

INP = Path("data/rosters/ourlads_depth_chart_links.csv")
OUT = Path("data/rosters/ourlads_depth_chart_links_clean.csv")

BASE = "https://www.ourlads.com/ncaa-football-depth-charts/depth-chart"

DROP_TEAMS = {
    "Go Ad Free",
    "FCS & Small College NFL Prospects",
    "-- Select Colleges --",
    "",
}

def clean_text(x):
    return re.sub(r"\s+", " ", str(x or "")).strip()

def canonicalize(url):
    url = unquote(str(url or ""))

    m = re.search(r"s=([^&/]+)&id=(\d+)", url)
    if m:
        slug = m.group(1).strip()
        team_id = m.group(2).strip()
        slug = slug.replace(" ", "-")
        return f"{BASE}/{slug}/{team_id}"

    m = re.search(r"/depth-chart/([^/]+)/(\d+)", url)
    if m:
        return f"{BASE}/{m.group(1)}/{m.group(2)}"

    return url

def main():
    if not INP.exists():
        raise SystemExit(f"Missing {INP}")

    df = pd.read_csv(INP)
    df["team_guess"] = df["team_guess"].map(clean_text)
    df["url"] = df["url"].map(canonicalize)

    df = df[~df["team_guess"].isin(DROP_TEAMS)].copy()
    df = df[~df["url"].astype(str).str.contains("index.html", na=False)].copy()
    df = df[df["url"].astype(str).str.contains(r"/depth-chart/.+/\d+", regex=True, na=False)].copy()

    df = df.drop_duplicates(subset=["team_guess"], keep="last")
    df = df.sort_values("team_guess")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    print("input links:", len(pd.read_csv(INP)))
    print("clean links:", len(df))
    print("wrote:", OUT)
    print(df[["team_guess", "url"]].head(50).to_string(index=False))
    print("\nTAIL")
    print(df[["team_guess", "url"]].tail(30).to_string(index=False))

if __name__ == "__main__":
    main()
