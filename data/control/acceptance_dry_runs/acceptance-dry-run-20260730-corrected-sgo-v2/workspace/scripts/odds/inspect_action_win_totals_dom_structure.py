#!/usr/bin/env python3
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from playwright.async_api import async_playwright

OUT = Path("data/audit/action_visible_table")
OUT.mkdir(parents=True, exist_ok=True)

TEAMS = [
    "Alabama Crimson Tide",
    "LSU Tigers",
    "Georgia Bulldogs",
    "UTEP Miners",
    "New Mexico Lobos",
    "Wake Forest Demon Deacons",
]

JS = r"""
(args) => {
  const teams = args.teams;

  function clean(s) {
    return (s || '').replace(/\s+/g, ' ').trim();
  }

  function lines(s) {
    return (s || '').split('\n').map(x => x.trim()).filter(Boolean);
  }

  const result = {};

  for (const team of teams) {
    const els = Array.from(document.querySelectorAll('body *')).filter(el => {
      const t = el.innerText || '';
      return t.split('\n').map(x => x.trim()).includes(team);
    });

    result[team] = [];

    for (const el of els.slice(0, 5)) {
      let cur = el;
      const chain = [];
      for (let level = 0; cur && level < 8; level++, cur = cur.parentElement) {
        const childTexts = Array.from(cur.children || []).map((c, idx) => ({
          idx,
          tag: c.tagName,
          cls: c.className,
          text: lines(c.innerText).slice(0, 40),
          img_alts: Array.from(c.querySelectorAll('img')).map(img => ({
            alt: img.getAttribute('alt'),
            title: img.getAttribute('title'),
            src: img.getAttribute('src')
          })).slice(0, 20)
        }));

        chain.push({
          level,
          tag: cur.tagName,
          cls: cur.className,
          text_lines: lines(cur.innerText).slice(0, 80),
          child_count: cur.children ? cur.children.length : 0,
          children: childTexts.slice(0, 20),
          img_alts: Array.from(cur.querySelectorAll('img')).map(img => ({
            alt: img.getAttribute('alt'),
            title: img.getAttribute('title'),
            src: img.getAttribute('src')
          })).slice(0, 30)
        });
      }
      result[team].push(chain);
    }
  }

  const headerImgs = Array.from(document.querySelectorAll('img')).map((img, idx) => ({
    idx,
    alt: img.getAttribute('alt'),
    title: img.getAttribute('title'),
    src: img.getAttribute('src'),
    parent_text: clean(img.parentElement ? img.parentElement.innerText : '')
  })).filter(x => {
    const s = JSON.stringify(x).toLowerCase();
    return s.includes('draft') || s.includes('mgm') || s.includes('fanduel') || s.includes('caesars') || s.includes('365') || s.includes('consensus');
  });

  return {result, headerImgs};
}
"""

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1700, "height": 1200})
        await page.goto("https://www.actionnetwork.com/ncaaf/futures", wait_until="domcontentloaded", timeout=60000)

        print("\nSelect 2026 Regular Season Wins in the Playwright Chrome window.")
        print("Wait until the win-total table is visible.")
        print("DOM inspection will run in 90 seconds.\n")

        await page.wait_for_timeout(90000)

        data = await page.evaluate(JS, {"teams": TEAMS})

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out = OUT / f"action_win_totals_dom_structure_{ts}.json"

        import json
        out.write_text(json.dumps(data, indent=2), errors="ignore")

        print("wrote:", out)

        print("\nHeader image candidates:")
        for h in data["headerImgs"][:80]:
            print(h)

        for team, chains in data["result"].items():
            print("\n" + "="*100)
            print(team)
            print("="*100)
            if not chains:
                print("not found")
                continue

            chain = chains[0]
            for node in chain[:6]:
                print("\nLEVEL", node["level"], node["tag"], "children:", node["child_count"])
                print("class:", str(node["cls"])[:200])
                print("text_lines:", node["text_lines"][:40])
                print("img_alts:", node["img_alts"][:10])
                print("child summaries:")
                for ch in node["children"][:12]:
                    print(" child", ch["idx"], ch["tag"], "class", str(ch["cls"])[:80], "text", ch["text"][:12], "imgs", ch["img_alts"][:4])

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
