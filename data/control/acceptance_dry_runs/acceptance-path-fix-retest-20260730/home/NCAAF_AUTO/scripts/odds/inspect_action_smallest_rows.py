#!/usr/bin/env python3
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from playwright.async_api import async_playwright
import json

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

  function lines(s) {
    return (s || '').split('\n').map(x => x.trim()).filter(Boolean);
  }

  function nodeInfo(el) {
    return {
      tag: el.tagName,
      cls: String(el.className || ''),
      role: el.getAttribute('role'),
      aria: el.getAttribute('aria-label'),
      text_len: (el.innerText || '').length,
      text_lines: lines(el.innerText).slice(0, 80),
      child_count: el.children ? el.children.length : 0,
      children: Array.from(el.children || []).map((c, idx) => ({
        idx,
        tag: c.tagName,
        cls: String(c.className || ''),
        role: c.getAttribute('role'),
        aria: c.getAttribute('aria-label'),
        text_len: (c.innerText || '').length,
        text_lines: lines(c.innerText).slice(0, 40),
        imgs: Array.from(c.querySelectorAll('img')).map(img => ({
          alt: img.getAttribute('alt'),
          title: img.getAttribute('title'),
          src: img.getAttribute('src')
        })).slice(0, 10)
      })).slice(0, 30),
      imgs: Array.from(el.querySelectorAll('img')).map(img => ({
        alt: img.getAttribute('alt'),
        title: img.getAttribute('title'),
        src: img.getAttribute('src')
      })).slice(0, 30)
    };
  }

  const results = {};
  const all = Array.from(document.querySelectorAll('body *'));

  for (const team of teams) {
    const matches = all
      .filter(el => {
        const ls = lines(el.innerText);
        return ls.includes(team);
      })
      .map(el => nodeInfo(el))
      .sort((a, b) => a.text_len - b.text_len);

    results[team] = matches.slice(0, 12);
  }

  const logoImgs = Array.from(document.querySelectorAll('img'))
    .map((img, idx) => ({
      idx,
      alt: img.getAttribute('alt'),
      title: img.getAttribute('title'),
      src: img.getAttribute('src'),
      parent_text: lines(img.parentElement ? img.parentElement.innerText : '').slice(0, 10)
    }))
    .filter(x => {
      const s = JSON.stringify(x).toLowerCase();
      return s.includes('oh logo') || s.includes('dk oh') || s.includes('draft') || s.includes('mgm') || s.includes('caesars') || s.includes('fanduel') || s.includes('365') || s.includes('fanatics') || s.includes('hardrock');
    });

  return {logoImgs, results};
}
"""

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1700, "height": 1200})
        await page.goto("https://www.actionnetwork.com/ncaaf/futures", wait_until="domcontentloaded", timeout=60000)

        print("\nSelect 2026 Regular Season Wins in the Playwright Chrome window.")
        print("Wait until Alabama/LSU win-total rows are visible.")
        print("Inspection runs in 90 seconds.\n")

        await page.wait_for_timeout(90000)

        data = await page.evaluate(JS, {"teams": TEAMS})

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out = OUT / f"action_smallest_rows_{ts}.json"
        out.write_text(json.dumps(data, indent=2), errors="ignore")
        print("wrote:", out)

        print("\nLogo/header image candidates:")
        for x in data["logoImgs"][:40]:
            print(x)

        for team, matches in data["results"].items():
            print("\n" + "="*100)
            print(team)
            print("="*100)
            for k, m in enumerate(matches[:5]):
                print("\nMATCH", k, m["tag"], "len", m["text_len"], "children", m["child_count"], "role", m["role"], "aria", m["aria"])
                print("class:", m["cls"][:200])
                print("text_lines:", m["text_lines"][:60])
                print("imgs:", m["imgs"][:10])
                print("children:")
                for ch in m["children"][:20]:
                    print(" child", ch["idx"], ch["tag"], "len", ch["text_len"], "role", ch["role"], "aria", ch["aria"], "text", ch["text_lines"][:20], "imgs", ch["imgs"][:4])

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
