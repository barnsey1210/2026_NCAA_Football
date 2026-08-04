#!/usr/bin/env python3
import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone
from playwright.async_api import async_playwright

OUT = Path("data/audit/action_futures_network")
OUT.mkdir(parents=True, exist_ok=True)

KEY_TERMS = [
    "futures",
    "regular_season_total_wins",
    "ncaaf",
    "DraftKings",
    "DK OH",
    "Georgia",
    "Georgia Bulldogs",
    "UTEP",
    "New Mexico",
    "Wake Forest",
    "Alabama",
    "LSU",
    "win total",
    "total wins",
]

def safe_name(i, url):
    keep = "".join(ch if ch.isalnum() else "_" for ch in url[:120])
    return f"{i:03d}_{keep}.txt"

async def main():
    rows = []
    saved = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page(
            viewport={"width": 1500, "height": 1000},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
        )

        async def on_response(resp):
            nonlocal saved
            url = resp.url
            low_url = url.lower()

            if not any(x in low_url for x in ["actionnetwork", "sprtactn", "api"]):
                return

            ct = resp.headers.get("content-type", "")
            status = resp.status

            body = ""
            try:
                body = await resp.text()
            except Exception:
                body = ""

            low_body = body.lower()
            score = sum(term.lower() in low_body or term.lower() in low_url for term in KEY_TERMS)

            if score <= 0:
                return

            item = {
                "saved_index": saved,
                "status": status,
                "content_type": ct,
                "url": url,
                "score": score,
                "body_len": len(body),
                "has_draftkings": "draftkings" in low_body or "dk oh" in low_body or "dk nj" in low_body,
                "has_georgia": "georgia" in low_body,
                "has_win_total_terms": "regular_season_total_wins" in low_body or "total wins" in low_body or "win total" in low_body,
            }
            rows.append(item)

            fn = OUT / safe_name(saved, url)
            fn.write_text(body, errors="ignore")
            saved += 1

        page.on("response", on_response)

        await page.goto("https://www.actionnetwork.com/ncaaf/futures", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(20000)

        await browser.close()

    summary_path = OUT / "network_summary.json"
    summary_path.write_text(json.dumps({
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "responses": rows
    }, indent=2), errors="ignore")

    print("Saved responses:", saved)
    print("Summary:", summary_path)

    for r in sorted(rows, key=lambda x: x["score"], reverse=True)[:40]:
        print("\nSCORE", r["score"], "LEN", r["body_len"], "STATUS", r["status"])
        print(r["url"])

if __name__ == "__main__":
    asyncio.run(main())
