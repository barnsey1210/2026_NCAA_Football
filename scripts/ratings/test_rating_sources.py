#!/usr/bin/env python3

from pathlib import Path
from io import StringIO
import argparse
from datetime import datetime
import re
import json
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "ratings"
RAW = OUT / "raw"

SPPLUS_FALLBACK_URL = (
    "https://www.espn.com/college-football/story/_/id/49868647/"
    "2026-college-football-sp+-rankings-all-138-fbs-teams"
)

ESPN_SEARCH_URL = "https://site.web.api.espn.com/apis/search/v2"

URLS = {
    "teamrankings": "https://www.teamrankings.com/college-football/ranking/predictive-by-other",
    "kford": "https://kfordratings.com/power",
    "fpi": "https://www.espn.com/college-football/fpi",
    "spplus": SPPLUS_FALLBACK_URL,
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

def discover_spplus_candidates():
    candidates = []

    try:
        response = requests.get(
            ESPN_SEARCH_URL,
            params={
                "query": "2026 college football SP+ rankings",
                "limit": 20,
            },
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        for result in data.get("results") or []:
            for item in result.get("contents") or []:
                title = str(item.get("displayName") or "")
                url = str((item.get("link") or {}).get("web") or "")
                date = str(item.get("date") or "")

                title_lower = title.lower()
                url_lower = url.lower()

                if item.get("type") != "story":
                    continue
                if "espn.com/college-football/story/" not in url_lower:
                    continue
                if "2026" not in title_lower:
                    continue
                if "sp+" not in title_lower and "sp+" not in url_lower:
                    continue

                candidates.append(
                    {
                        "title": title,
                        "url": url,
                        "date": date,
                    }
                )

    except Exception as exc:
        print("\nSPPLUS DISCOVERY")
        print("discovery error:", exc)

    candidates.sort(
        key=lambda row: row.get("date") or "",
        reverse=True,
    )

    seen = set()
    unique = []

    for row in candidates:
        url = row["url"]
        if url in seen:
            continue
        seen.add(url)
        unique.append(row)

    if SPPLUS_FALLBACK_URL not in seen:
        unique.append(
            {
                "title": "Known-good manual fallback",
                "url": SPPLUS_FALLBACK_URL,
                "date": "",
            }
        )

    return unique


def valid_spplus_html(html):
    if not html.strip():
        return False

    try:
        tables = pd.read_html(StringIO(html))
    except Exception:
        return False

    for table in tables:
        df = table.copy()
        df.columns = [norm_col(c) for c in df.columns]

        columns = set(df.columns)

        rating_ok = bool(
            {"rating", "sp", "sp_rk"} & columns
        )
        offense_ok = bool(
            {"offense", "off_sp", "off"} & columns
        )
        defense_ok = bool(
            {"defense", "def_sp", "def"} & columns
        )

        if (
            len(df) == 138
            and "team" in columns
            and rating_ok
            and offense_ok
            and defense_ok
        ):
            return True

    return False


def fetch_spplus():
    candidates = discover_spplus_candidates()

    print("\nSPPLUS DISCOVERY")
    print("candidate URLs:", len(candidates))

    for index, candidate in enumerate(candidates, start=1):
        url = candidate["url"]
        title = candidate["title"]
        date = candidate["date"]

        print(
            f"candidate {index}: "
            f"{date or 'NO_DATE'} | {title}"
        )

        html, content, content_type = fetch("spplus", url)

        if not valid_spplus_html(html):
            print("SPPLUS VALIDATION: REJECTED")
            continue

        mode = (
            "FALLBACK"
            if title == "Known-good manual fallback"
            else "DISCOVERED"
        )

        print("SPPLUS VALIDATION: PASSED")
        print("SPPLUS URL MODE:", mode)
        print("SPPLUS SELECTED URL:", url)

        return url, html, content, content_type, mode

    raise SystemExit(
        "SP+: no discovered or fallback ESPN article "
        "contained a valid 138-team SP+ table"
    )


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
        tables = pd.read_html(StringIO(html))
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

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sources",
        default=",".join(URLS.keys()),
        help="Comma-separated source keys to fetch",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    requested = [x.strip() for x in args.sources.split(",") if x.strip()]
    unknown = [x for x in requested if x not in URLS]
    if unknown:
        raise SystemExit(f"Unknown rating sources: {unknown}")

    overall = {}

    for name in requested:
        raw_dir = RAW / name
        raw_dir.mkdir(parents=True, exist_ok=True)

        for stale_table in raw_dir.glob(f"{name}_table_*.csv"):
            stale_table.unlink()

        if name == "spplus":
            (
                url,
                html,
                content,
                content_type,
                discovery_mode,
            ) = fetch_spplus()
        else:
            url = URLS[name]
            html, content, content_type = fetch(name, url)
            discovery_mode = None

        summaries = inspect_tables(name, html)

        overall[name] = {
            "url": url,
            "discovery_mode": discovery_mode,
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
