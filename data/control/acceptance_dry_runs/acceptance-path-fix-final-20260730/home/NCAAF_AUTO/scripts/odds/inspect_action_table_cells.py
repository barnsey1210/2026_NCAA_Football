#!/usr/bin/env python3
import asyncio
import json
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

  function lines(s) {
    return (s || '').split('\n').map(x => x.trim()).filter(Boolean);
  }

  function imgs(el) {
    return Array.from(el.querySelectorAll('img')).map(img => ({
      alt: img.getAttribute('alt'),
      title: img.getAttribute('title'),
      src: img.getAttribute('src')
    }));
  }

  function cellInfo(cell, idx) {
    return {
      idx,
      tag: cell.tagName,
      cls: String(cell.className || ''),
      role: cell.getAttribute('role'),
      aria: cell.getAttribute('aria-label'),
      text_lines: lines(cell.innerText),
      imgs: imgs(cell)
    };
  }

  const out = {
    header_th: [],
    header_imgs_near_table: [],
    rows: {}
  };

  for (const team of teams) {
    const firstCells = Array.from(document.querySelectorAll('td.options-futures-row__first-cell'));
    const td = firstCells.find(x => lines(x.innerText).includes(team));

    if (!td) {
      out.rows[team] = {found: false};
      continue;
    }

    const tr = td.closest('tr');
    const table = td.closest('table');

    let headerCells = [];
    if (table) {
      headerCells = Array.from(table.querySelectorAll('thead th, thead td, th')).map((x, idx) => cellInfo(x, idx));
      out.header_th = headerCells;

      out.header_imgs_near_table = imgs(table).map((x, idx) => ({idx, ...x}));
    }

    const cells = tr ? Array.from(tr.children).map((x, idx) => cellInfo(x, idx)) : [];

    out.rows[team] = {
      found: true,
      tr_class: tr ? String(tr.className || '') : null,
      table_class: table ? String(table.className || '') : null,
      cell_count: cells.length,
      cells
    };
  }

  return out;
}
"""

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1700, "height": 1200})
        await page.goto("https://www.actionnetwork.com/ncaaf/futures", wait_until="domcontentloaded", timeout=60000)

        print("\nSelect 2026 Regular Season Wins in the Playwright Chrome window.")
        print("Wait until the win-total table is visible.")
        print("Cell inspection runs in 90 seconds.\n")

        await page.wait_for_timeout(90000)

        data = await page.evaluate(JS, {"teams": TEAMS})

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out = OUT / f"action_table_cells_{ts}.json"
        out.write_text(json.dumps(data, indent=2), errors="ignore")
        print("wrote:", out)

        print("\nHEADER TH:")
        for h in data.get("header_th", []):
            print("th", h["idx"], "text", h["text_lines"], "imgs", h["imgs"])

        print("\nHEADER IMGS NEAR TABLE:")
        for h in data.get("header_imgs_near_table", [])[:40]:
            print(h)

        for team, row in data["rows"].items():
            print("\n" + "="*100)
            print(team)
            print("="*100)
            print("found:", row.get("found"), "cell_count:", row.get("cell_count"), "tr_class:", row.get("tr_class"))
            for c in row.get("cells", []):
                print("cell", c["idx"], "tag", c["tag"], "class", c["cls"][:80], "text", c["text_lines"], "imgs", c["imgs"][:3])

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
