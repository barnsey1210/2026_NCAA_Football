#!/usr/bin/env python3
import hashlib
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

LINKS_PATH = Path("data/injuries/cfbdepth_latest_injury_status_raw.csv")
OUT = Path("data/injuries/cfbdepth_injury_articles_raw.csv")
SNAPSHOT_DIR = Path("data/injuries/cfbdepth_article_snapshots")

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

def clean_text(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()

def strip_html(html):
    article = re.search(r"(?is)<article[^>]*>(.*?)</article>", html)
    if article:
        html = article.group(1)

    html = re.sub(r"(?is)<script.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?</style>", " ", html)
    html = re.sub(r"(?is)<nav.*?</nav>", " ", html)
    html = re.sub(r"(?is)<header.*?</header>", " ", html)
    html = re.sub(r"(?is)<footer.*?</footer>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    return clean_text(text)

def relevance_score(title, url, body):
    blob = f"{title} {url} {body}".lower()
    hits = []
    for k in KEYWORDS:
        if k in blob:
            hits.append(k)
    return len(set(hits)), ",".join(sorted(set(hits)))

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 NCAAF injury article monitor",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def main():
    pulled_at = datetime.now(timezone.utc).isoformat()

    if not LINKS_PATH.exists():
        raise SystemExit(f"Missing {LINKS_PATH}")

    links = pd.read_csv(LINKS_PATH)
    links = links[links["row_type"].astype(str).eq("link")].copy()
    links = links[links["item_url"].astype(str).str.contains("injury|status|impact|report", case=False, na=False)].copy()

    rows = []
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    for _, r in links.iterrows():
        title = str(r.get("item_title", "") or "")
        url = str(r.get("item_url", "") or "")

        try:
            html = fetch(url)
            safe = re.sub(r"[^a-zA-Z0-9]+", "_", url.strip("/"))
            snap = SNAPSHOT_DIR / f"{safe}.html"
            snap.write_text(html, errors="ignore")

            body = strip_html(html)
            score, hits = relevance_score(title, url, body)

            rows.append({
                "pulled_at": pulled_at,
                "source": "CFBDepth Article Body",
                "source_url": str(r.get("source_url", "")),
                "item_title": title,
                "item_url": url,
                "raw_text": body[:8000],
                "content_hash": hashlib.sha256(f"{url}|{body}".encode("utf-8", errors="ignore")).hexdigest(),
                "relevance_score": score,
                "keyword_hits": hits,
                "row_type": "article",
            })
        except Exception as e:
            rows.append({
                "pulled_at": pulled_at,
                "source": "CFBDepth Article Body",
                "source_url": str(r.get("source_url", "")),
                "item_title": title,
                "item_url": url,
                "raw_text": str(e),
                "content_hash": hashlib.sha256(f"{url}|{e}".encode()).hexdigest(),
                "relevance_score": 0,
                "keyword_hits": "",
                "row_type": "error",
            })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    print("article rows:", len(df))
    print("relevant article rows:", int((df["relevance_score"] > 0).sum()) if not df.empty else 0)
    print("wrote:", OUT)

    if not df.empty:
        print(df[["row_type", "item_title", "item_url", "relevance_score", "keyword_hits"]].to_string(index=False))

if __name__ == "__main__":
    main()
