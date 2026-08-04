#!/usr/bin/env python3
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd

INDEX_URL = "https://www.ourlads.com/ncaa-football-depth-charts/"
OUT = Path("data/rosters/ourlads_depth_chart_links.csv")
SNAPSHOT = Path("data/rosters/ourlads_depth_chart_index.html")

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            attrs = dict(attrs)
            self.current = attrs.get("href", "")
            self.current_text = []

    def handle_data(self, data):
        if self.current is not None:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.current is not None:
            text = " ".join(x.strip() for x in self.current_text if x.strip())
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                self.links.append((self.current, text))
            self.current = None
            self.current_text = []

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

def clean_team_from_url(url, text):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    text = re.sub(r"\s+Depth Chart$", "", text, flags=re.I).strip()
    if text and len(text) > 2 and not text.lower().startswith("depth"):
        return text

    m = re.search(r"/depth-chart/([^/]+)/", url)
    if m:
        return m.group(1).replace("-", " ").title()

    return text

def main():
    pulled_at = datetime.now(timezone.utc).isoformat()
    html = fetch(INDEX_URL)

    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(html, errors="ignore")

    parser = LinkParser()
    parser.feed(html)

    rows = []
    seen = set()

    for href, text in parser.links:
        url = urljoin(INDEX_URL, href)

        if "/ncaa-football-depth-charts/depth-chart/" not in url:
            continue

        if url in seen:
            continue
        seen.add(url)

        rows.append({
            "pulled_at": pulled_at,
            "source": "Ourlads",
            "team_guess": clean_team_from_url(url, text),
            "link_text": text,
            "url": url,
        })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    print("pulled_at:", pulled_at)
    print("depth chart links:", len(df))
    print("wrote:", OUT)
    print("snapshot:", SNAPSHOT)

    if not df.empty:
        print(df.head(40).to_string(index=False))

if __name__ == "__main__":
    main()
