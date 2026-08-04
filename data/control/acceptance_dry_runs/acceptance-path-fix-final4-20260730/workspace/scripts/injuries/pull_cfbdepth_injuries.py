#!/usr/bin/env python3
import hashlib
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import pandas as pd

SOURCE_NAME = "CFBDepth Injury Status"

SEED_URLS = [
    "https://www.cfbdepth.com/latest-injury-status/",
    "https://www.cfbdepth.com/injury-report/",
    "https://www.cfbdepth.com/injury-impact-report/",
]

RAW_CURRENT = Path("data/injuries/cfbdepth_latest_injury_status_raw.csv")
RAW_HISTORY = Path("data/injuries/injury_events_raw_history.csv")
SNAPSHOT_DIR = Path("data/injuries/cfbdepth_snapshots")

KEYWORDS = [
    "injury",
    "injuries",
    "injured",
    "status",
    "out",
    "questionable",
    "doubtful",
    "probable",
    "available",
    "availability",
    "miss",
    "missed",
    "will miss",
    "practice",
    "limited",
    "starter",
    "starting",
    "impact",
    "suspended",
    "suspension",
    "game-time",
    "not practicing",
    "ruled out",
    "day-to-day",
]

EXCLUDE_TITLES = {
    "skip to content",
    "cfb depth",
    "primary menu",
    "depth charts",
    "sec",
    "big ten",
    "big 12",
    "acc",
    "pac 12",
    "independents",
    "aac",
    "c-usa",
    "mac",
    "mountain west",
    "sun belt",
    "updates",
    "rankings",
    "projections",
    "content",
    "magazines",
    "advanced stats",
    "depth+",
    "about",
    "register",
    "log in",
    "home",
    "search for:",
}

EXCLUDE_URL_PARTS = [
    "/category/",
    "/depth-charts/",
    "/rankings/",
    "/projections/",
    "/advanced-stats/",
    "/about/",
    "/register/",
    "/log-in/",
    "javascript:",
    "#content",
]

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            attrs = dict(attrs)
            href = attrs.get("href", "")
            self.current = href
            self.current_text = []

    def handle_data(self, data):
        if self.current is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.current is not None:
            text = " ".join(x.strip() for x in self.current_text if x.strip())
            if text:
                self.links.append((self.current, clean_text(text)))
            self.current = None
            self.current_text = []

def clean_text(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()

def strip_html(html):
    text = re.sub(r"(?is)<script.*?</script>", " ", html)
    text = re.sub(r"(?is)<style.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return clean_text(text)

def relevance_score(title, url, body=""):
    blob = f"{title} {url} {body}".lower()
    hits = []
    for k in KEYWORDS:
        if k in blob:
            hits.append(k)
    return len(set(hits)), ",".join(sorted(set(hits)))

def is_excluded(title, url):
    t = clean_text(title).lower()
    u = str(url or "").lower()

    if t in EXCLUDE_TITLES:
        return True

    for part in EXCLUDE_URL_PARTS:
        if part in u:
            return True

    parsed = urlparse(u)
    path = parsed.path.strip("/")

    if path and path.count("/") == 0:
        team_like = re.match(r"^[a-z0-9-]+$", path)
        if team_like and not any(k.replace(" ", "-") in path for k in ["injury", "status", "impact", "report", "spring-intel"]):
            return True

    return False

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 NCAAF injury monitor",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def main():
    pulled_at = datetime.now(timezone.utc).isoformat()
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    seen = set()

    for seed_url in SEED_URLS:
        try:
            html = fetch(seed_url)
        except Exception as e:
            rows.append({
                "pulled_at": pulled_at,
                "source": SOURCE_NAME,
                "source_url": seed_url,
                "item_title": "FETCH_ERROR",
                "item_url": seed_url,
                "raw_text": str(e),
                "content_hash": hashlib.sha256(f"{seed_url}|{e}".encode()).hexdigest(),
                "relevance_score": 0,
                "keyword_hits": "",
                "row_type": "error",
            })
            continue

        safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", seed_url.strip("/"))
        snap = SNAPSHOT_DIR / f"{safe_name}.html"
        snap.write_text(html, errors="ignore")

        page_text = strip_html(html)
        page_score, page_hits = relevance_score(seed_url, seed_url, page_text[:5000])

        rows.append({
            "pulled_at": pulled_at,
            "source": SOURCE_NAME,
            "source_url": seed_url,
            "item_title": "PAGE_SNAPSHOT",
            "item_url": seed_url,
            "raw_text": page_text[:2000],
            "content_hash": hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest(),
            "relevance_score": page_score,
            "keyword_hits": page_hits,
            "row_type": "page",
        })

        parser = LinkParser()
        parser.feed(html)

        for href, title in parser.links:
            url = urljoin(seed_url, href)
            title = clean_text(title)

            if is_excluded(title, url):
                continue

            score, hits = relevance_score(title, url)

            if score <= 0:
                continue

            key = (url, title)
            if key in seen:
                continue
            seen.add(key)

            rows.append({
                "pulled_at": pulled_at,
                "source": SOURCE_NAME,
                "source_url": seed_url,
                "item_title": title,
                "item_url": url,
                "raw_text": title,
                "content_hash": hashlib.sha256(f"{url}|{title}".encode()).hexdigest(),
                "relevance_score": score,
                "keyword_hits": hits,
                "row_type": "link",
            })

    df = pd.DataFrame(rows)

    RAW_CURRENT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_CURRENT, index=False)

    if RAW_HISTORY.exists():
        hist = pd.read_csv(RAW_HISTORY)
        hist = pd.concat([hist, df], ignore_index=True)
        hist = hist.drop_duplicates(subset=["content_hash"], keep="last")
    else:
        hist = df.copy()

    hist.to_csv(RAW_HISTORY, index=False)

    print("pulled_at:", pulled_at)
    print("raw rows:", len(df))
    print("relevant rows:", int((df["relevance_score"] > 0).sum()))
    print("wrote:", RAW_CURRENT)
    print("wrote:", RAW_HISTORY)
    print("snapshots:", SNAPSHOT_DIR)

    show = df[df["relevance_score"] > 0].copy()
    if not show.empty:
        print(show[["row_type", "item_title", "item_url", "relevance_score", "keyword_hits"]].head(50).to_string(index=False))

if __name__ == "__main__":
    main()
