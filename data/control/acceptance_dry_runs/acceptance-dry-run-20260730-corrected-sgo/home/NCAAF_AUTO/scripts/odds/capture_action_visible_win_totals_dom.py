#!/usr/bin/env python3
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from playwright.async_api import async_playwright

OUT = Path("data/audit/action_visible_table")
OUT.mkdir(parents=True, exist_ok=True)

TEAMS = ["Georgia", "UTEP", "New Mexico", "Wake Forest", "Alabama", "LSU"]

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1700, "height": 1200})

        await page.goto("https://www.actionnetwork.com/ncaaf/futures", wait_until="domcontentloaded", timeout=60000)

        print("\nIMPORTANT:")
        print("Use the Playwright Chrome window that just opened.")
        print("Select: 2026 Regular Season Wins")
        print("Do not use your normal Chrome window.")
        print("The captured table should show win totals like 9.5, 8.5, 5.5, not +800 title odds.")
        print("You have 90 seconds.\n")

        await page.wait_for_timeout(90000)

        body_text = await page.locator("body").inner_text()
        html = await page.content()

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        txt_path = OUT / f"action_visible_body_text_{ts}.txt"
        html_path = OUT / f"action_visible_page_{ts}.html"
        png_path = OUT / f"action_visible_page_{ts}.png"

        txt_path.write_text(body_text, errors="ignore")
        html_path.write_text(html, errors="ignore")
        await page.screenshot(path=str(png_path), full_page=True)

        print("wrote:", txt_path)
        print("wrote:", html_path)
        print("wrote:", png_path)

        lines = [x.strip() for x in body_text.splitlines() if x.strip()]

        print("\nVerification terms:")
        for term in ["Regular Season", "Total Wins", "National Championship", "Georgia", "Alabama", "DraftKings"]:
            print(term, term.lower() in body_text.lower())

        for team in TEAMS:
            print("\n" + "="*90)
            print(team)
            print("="*90)
            found = False
            for i, line in enumerate(lines):
                if team.lower() in line.lower():
                    found = True
                    for j in range(max(0, i-8), min(len(lines), i+35)):
                        print(f"{j:04d}: {lines[j]}")
                    break
            if not found:
                print("not found")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
