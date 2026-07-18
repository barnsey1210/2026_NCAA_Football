#!/usr/bin/env python3
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd

OUT = Path("data/rosters/ourlads_depth_chart_links.csv")
SNAPSHOT = Path("data/rosters/ourlads_team_page_for_link_discovery.html")

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.options = []
        self.current_a = None
        self.current_option = None
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "a":
            self.current_a = attrs.get("href", "")
            self.text = []
        elif tag.lower() == "option":
            self.current_option = attrs.get("value", "")
            self.text = []

    def handle_data(self, data):
        if self.current_a is not None or self.current_option is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.current_a is not None:
            txt = re.sub(r"\s+", " ", " ".join(self.text)).strip()
            self.links.append((self.current_a, txt))
            self.current_a = None
            self.text = []
        elif tag.lower() == "option" and self.current_option is not None:
            txt = re.sub(r"\s+", " ", " ".join(self.text)).strip()
            self.options.append((self.current_option, txt))
            self.current_option = None
            self.text = []

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

def clean_team(url, text):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    text = re.sub(r"\s+Depth Chart$", "", text, flags=re.I).strip()
    if text and text.lower() not in ["select", "-- select colleges --", "depth chart"]:
        return text

    m = re.search(r"/depth-chart/([^/]+)/", url)
    if m:
        return m.group(1).replace("-", " ").title()

    return text

def is_depth_url(url):
    return "/ncaa-football-depth-charts/depth-chart/" in url

def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python3 scripts/injuries/discover_ourlads_links_from_team_page.py "https://..."')

    source_url = sys.argv[1]
    pulled_at = datetime.now(timezone.utc).isoformat()

    html = fetch(source_url)
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(html, errors="ignore")

    parser = Parser()
    parser.feed(html)

    rows = []
    seen = set()

    for href, text in parser.links:
        url = urljoin(source_url, href)
        if not is_depth_url(url):
            continue
        if url in seen:
            continue
        seen.add(url)
        rows.append({
            "pulled_at": pulled_at,
            "source": "Ourlads",
            "source_type": "anchor",
            "team_guess": clean_team(url, text),
            "link_text": text,
            "url": url,
        })

    for value, text in parser.options:
        url = urljoin(source_url, value)
        if not is_depth_url(url):
            continue
        if url in seen:
            continue
        seen.add(url)
        rows.append({
            "pulled_at": pulled_at,
            "source": "Ourlads",
            "source_type": "option",
            "team_guess": clean_team(url, text),
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
        print(df.head(80).to_string(index=False))
    else:
        print("No links found. Running regex diagnostics:")
        for pat in [
            r'/ncaa-football-depth-charts/depth-chart/[^"\']+',
            r'depth-chart/[^"\']+',
            r'91533',
        ]:
            hits = re.findall(pat, html)
            print(pat, len(hits), hits[:10])

if __name__ == "__main__":
    main()
