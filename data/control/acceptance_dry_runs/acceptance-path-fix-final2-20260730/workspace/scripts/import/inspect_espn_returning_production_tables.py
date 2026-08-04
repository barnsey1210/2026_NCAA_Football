#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import requests

OUT_DIR = Path("data/import/sp_plus/raw_espn_returning_production")
OUT_DIR.mkdir(parents=True, exist_ok=True)

URLS = {
    2023: "https://www.espn.com/college-football/insider/story/_/id/35577489/college-football-teams-returning-production-2023-season",
    2024: "https://www.espn.com/college-football/insider/story/_/id/39436455/college-football-2024-returning-production-rankings-134-teams",
    2025: "https://www.espn.com/college-football/insider/story/_/id/43952974/2025-college-football-returning-production-rankings-136-teams",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

for season, url in URLS.items():
    print("\n" + "=" * 100)
    print("season:", season)
    print("url:", url)

    html_path = OUT_DIR / f"espn_returning_production_{season}.html"
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        print("status:", r.status_code, "len:", len(r.text))
        html_path.write_text(r.text, encoding="utf-8")
    except Exception as e:
        print("download error:", e)
        continue

    try:
        tables = pd.read_html(r.text)
    except Exception as e:
        print("read_html error:", e)
        tables = []

    print("tables found:", len(tables))

    for i, df in enumerate(tables):
        csv_path = OUT_DIR / f"espn_returning_production_{season}_table_{i}.csv"
        df.to_csv(csv_path, index=False)

        print("\n--- table", i, "---")
        print("shape:", df.shape)
        print("columns:", list(df.columns))
        print(df.head(10).to_string(index=False))
        print("wrote:", csv_path)
