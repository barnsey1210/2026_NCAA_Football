#!/usr/bin/env python3
"""Download official CFP week-by-week ranking tables for historical validation."""
from __future__ import annotations

import argparse
from io import StringIO
from pathlib import Path
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
URLS = {
    2021: "https://collegefootballplayoff.com/sports/2021/11/3/wk-x-wk-rankings-2021.aspx",
    2022: "https://collegefootballplayoff.com/sports/2022/11/2/wk-x-wk-rankings-2022.aspx",
    2023: "https://collegefootballplayoff.com/sports/2023/11/1/wk-x-wk-rankings-2023.aspx",
    2024: "https://collegefootballplayoff.com/sports/2024/11/6/wk-x-wk-rankings-2024.aspx",
}


def clean_team(value):
    text = str(value).replace("\xa0", " ").strip()
    # The accessible table sometimes repeats the logo alt text/team name.
    parts = text.split()
    half = len(parts) // 2
    if len(parts) % 2 == 0 and parts[:half] == parts[half:]:
        text = " ".join(parts[:half])
    return {"Southern California": "USC", "Mississippi": "Ole Miss", "Miami (FL)": "Miami-FL"}.get(text, text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "data/models/cfp_weekly_rankings_official_2021_2024.csv")
    args = parser.parse_args()
    rows = []
    for season, url in URLS.items():
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 NCAAF-CFP-validation/1.0"}, timeout=45)
        response.raise_for_status()
        tables = pd.read_html(StringIO(response.text))
        table = max(tables, key=lambda frame: frame.shape[0] * frame.shape[1])
        table.columns = [str(c).replace("\n", " ").strip() for c in table.columns]
        team_col = table.columns[0]
        for _, record in table.iterrows():
            team = clean_team(record[team_col])
            for release_index, column in enumerate(table.columns[1:], 1):
                value = pd.to_numeric(record[column], errors="coerce")
                if pd.notna(value):
                    rows.append({"season": season, "release_index": release_index, "ranking_date": column, "team": team, "actual_cfp_rank": int(value), "source_url": url})
    output = pd.DataFrame(rows).sort_values(["season", "release_index", "actual_cfp_rank"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    print(f"Wrote {len(output)} official CFP ranking rows to {args.output}")


if __name__ == "__main__":
    main()
