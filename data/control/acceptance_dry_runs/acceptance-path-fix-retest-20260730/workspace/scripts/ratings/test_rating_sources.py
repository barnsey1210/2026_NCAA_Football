#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import re
import json
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "ratings"
RAW = OUT / "raw"

URLS = {
    "teamrankings": "https://www.teamrankings.com/college-football/ranking/predictive-by-other",
    "kford": "https://kfordratings.com/power",
    "fpi": "https://www.espn.com/college-football/fpi",
    "spplus": "https://www.espn.com/college-football/story/_/id/48306284/2026-college-football-sp+-rankings-138-fbs-teams",
    "bradpowers": "https://nebula.wsimg.com/884a927043bff9994159619ba0ba890c?AccessKeyId=F4E5462B12CB60B63AD2&disposition=0&alloworigin=1",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def norm_col(c):
    s = str(c)
    if isinstance(c, tuple):
        s = " ".join(str(x) for x in c if str(x) != "nan")
    s = re.sub(r"\s+", " ", s).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s

def save_html(name, html):
    d = RAW / name
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    p.write_text(html, encoding="utf-8")
    return p

def fetch(name, url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=45)
        print(f"\n{name.upper()}")
        print("status:", r.status_code)
        print("content-type:", r.headers.get("content-type", ""))
        print("length:", len(r.content))
        print("final url:", r.url)

        raw_path = RAW / name
        raw_path.mkdir(parents=True, exist_ok=True)

        if "text" in r.headers.get("content-type", "") or "html" in r.headers.get("content-type", ""):
            saved = save_html(name, r.text)
            print("saved html:", saved.relative_to(ROOT))
            return r.text, r.content, r.headers.get("content-type", "")
        else:
            ext = ".bin"
            ct = r.headers.get("content-type", "").lower()
            if "pdf" in ct:
                ext = ".pdf"
            p = raw_path / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
            p.write_bytes(r.content)
            print("saved binary:", p.relative_to(ROOT))
            return "", r.content, r.headers.get("content-type", "")
    except Exception as e:
        print(f"\n{name.upper()}")
        print("ERROR fetching:", e)
        return "", b"", ""

def inspect_tables(name, html):
    if not html.strip():
        print("no html to inspect")
        return []

    try:
        tables = pd.read_html(html)
    except Exception as e:
        print("read_html error:", e)
        return []

    print("tables found:", len(tables))

    summaries = []
    for i, t in enumerate(tables):
        df = t.copy()
        df.columns = [norm_col(c) for c in df.columns]
        summaries.append({
            "table_index": i,
            "rows": len(df),
            "cols": len(df.columns),
            "columns": list(df.columns),
        })
        print(f"\nTable {i}: rows={len(df)} cols={len(df.columns)}")
        print("columns:", list(df.columns))
        print(df.head(8).to_string(index=False))

        out_dir = RAW / name
        out_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_dir / f"{name}_table_{i}.csv", index=False)

    return summaries

def main():
    overall = {}

    for name, url in URLS.items():
        html, content, content_type = fetch(name, url)
        summaries = inspect_tables(name, html)

        overall[name] = {
            "url": url,
            "content_type": content_type,
            "html_length": len(html),
            "binary_length": len(content),
            "tables_found": len(summaries),
            "tables": summaries,
        }

    out = OUT / "ratings_source_test_summary.json"
    out.write_text(json.dumps(overall, indent=2), encoding="utf-8")
    print("\nWrote", out.relative_to(ROOT))

if __name__ == "__main__":
    main()
