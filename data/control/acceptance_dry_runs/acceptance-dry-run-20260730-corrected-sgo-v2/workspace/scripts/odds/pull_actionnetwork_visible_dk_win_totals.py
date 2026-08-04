#!/usr/bin/env python3
import asyncio
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
from playwright.async_api import async_playwright

OUT = Path("data/odds/actionnetwork_visible_dk_win_totals.csv")
AUDIT = Path("data/audit/actionnetwork_visible_dk_win_totals_audit.csv")
FAILED = Path("data/audit/actionnetwork_visible_dk_failed_body.txt")
URL = "https://www.actionnetwork.com/ncaaf/futures"
TARGET_MARKET = "2026 NCAAF Regular Season - Total Wins"
DK_CELL_INDEX = 7

def parse_price(x):
    s = str(x or "").strip().replace("−", "-")
    if not s or s.upper() == "N/A":
        return None
    try:
        return int(s.replace("+", ""))
    except Exception:
        return None

def parse_total_token(x):
    s = str(x or "").strip().lower()
    m = re.match(r"^[ou]([0-9]+(?:\.[0-9]+)?)$", s)
    if not m:
        return None
    return float(m.group(1))

def normalize_team(raw):
    raw = str(raw or "").strip()
    explicit = {
        "Alabama Crimson Tide": "Alabama",
        "LSU Tigers": "LSU",
        "Georgia Bulldogs": "Georgia",
        "UTEP Miners": "UTEP",
        "New Mexico Lobos": "New Mexico",
        "Wake Forest Demon Deacons": "Wake Forest",
        "Miami (FL) Hurricanes": "Miami-FL",
    }
    if raw in explicit:
        return explicit[raw]

    suffixes = [
        " Crimson Tide", " Bulldogs", " Tigers", " Miners", " Lobos", " Demon Deacons",
        " Yellow Jackets", " Red Raiders", " Hoosiers", " Hurricanes", " Cornhuskers",
        " Gamecocks", " Terrapins", " Seminoles", " Wolverines", " Cougars", " Badgers",
        " Scarlet Knights", " Mountaineers", " Orange", " Cowboys", " Golden Eagles",
        " Golden Gophers", " Panthers", " Roadrunners", " Flames", " Pirates",
        " Mean Green", " Sun Devils", " Bears", " Bearcats", " Eagles", " Buckeyes",
        " Ducks", " Volunteers", " Longhorns", " Aggies", " Gators", " Rebels",
        " Nittany Lions", " Fighting Irish", " Trojans", " Knights", " Spartans",
        " Wolfpack", " Tar Heels", " Cavaliers", " Hokies", " Mustangs", " Owls",
        " Green Wave", " Broncos", " Rams", " Aztecs", " Falcons", " Zips",
    ]

    out = raw
    for suf in suffixes:
        if out.endswith(suf):
            out = out[:-len(suf)]
            break

    if out == "Miami (FL)":
        return "Miami-FL"
    return out

async def force_select_market(page):
    attempts = []

    try:
        res = await page.evaluate(
            """
            (target) => {
              const clean = s => (s || '').replace(/\\s+/g, ' ').trim();
              const opts = Array.from(document.querySelectorAll('option'));
              const opt = opts.find(o => clean(o.textContent) === target);

              if (!opt) {
                return {selected:false, reason:'option_not_found', option_count:opts.length};
              }

              const sel = opt.closest('select');
              if (!sel) {
                return {selected:false, reason:'select_not_found', option_text:clean(opt.textContent)};
              }

              sel.value = opt.value;
              opt.selected = true;

              sel.dispatchEvent(new Event('input', {bubbles:true}));
              sel.dispatchEvent(new Event('change', {bubbles:true}));

              return {
                selected:true,
                value:opt.value,
                option_text:clean(opt.textContent),
                selected_text: sel.options && sel.selectedIndex >= 0 ? clean(sel.options[sel.selectedIndex].textContent) : ''
              };
            }
            """,
            TARGET_MARKET
        )
        attempts.append(f"select_option={res}")
        await page.wait_for_timeout(10000)

        if res and res.get("selected"):
            return True, attempts
    except Exception as e:
        attempts.append(f"select_option_failed={type(e).__name__}")

    try:
        n = await page.get_by_text(TARGET_MARKET, exact=True).count()
        attempts.append(f"exact_count={n}")
        for i in range(n):
            try:
                await page.get_by_text(TARGET_MARKET, exact=True).nth(i).scroll_into_view_if_needed(timeout=2000)
                await page.get_by_text(TARGET_MARKET, exact=True).nth(i).click(timeout=3000, force=True)
                await page.wait_for_timeout(3000)
                attempts.append(f"clicked_exact_index={i}")
                return True, attempts
            except Exception as e:
                attempts.append(f"exact_index_{i}_failed={type(e).__name__}")
    except Exception as e:
        attempts.append(f"exact_failed={type(e).__name__}")

    try:
        res = await page.evaluate(
            """
            (target) => {
              const clean = s => (s || '').replace(/\\s+/g, ' ').trim();
              const els = Array.from(document.querySelectorAll('body *'))
                .filter(el => clean(el.innerText || el.textContent) === target)
                .sort((a,b) => clean(a.innerText || a.textContent).length - clean(b.innerText || b.textContent).length);

              for (const el of els) {
                try {
                  el.scrollIntoView({block:'center', inline:'center'});
                  el.click();
                  return {clicked:true, tag:el.tagName, cls:String(el.className || ''), text:clean(el.innerText || el.textContent)};
                } catch (e) {}
              }
              return {clicked:false, count:els.length};
            }
            """,
            TARGET_MARKET
        )
        attempts.append(f"js_click={res}")
        await page.wait_for_timeout(5000)
        if res and res.get("clicked"):
            return True, attempts
    except Exception as e:
        attempts.append(f"js_click_failed={type(e).__name__}")

    try:
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(1000)
        await page.get_by_text("2026 NCAAF Championship - To Win", exact=True).first.click(timeout=3000, force=True)
        await page.wait_for_timeout(1000)
        await page.get_by_text(TARGET_MARKET, exact=True).first.click(timeout=3000, force=True)
        await page.wait_for_timeout(5000)
        attempts.append("clicked_dropdown_sequence")
        return True, attempts
    except Exception as e:
        attempts.append(f"dropdown_sequence_failed={type(e).__name__}")

    return False, attempts

async def scrape_rows(page):
    return await page.evaluate(
        r"""
        (dkIndex) => {
          function lines(s) {
            return (s || '').split('\n').map(x => x.trim()).filter(Boolean);
          }

          const rows = [];
          const trs = Array.from(document.querySelectorAll('tr'));

          for (const tr of trs) {
            const first = tr.querySelector('td.options-futures-row__first-cell');
            if (!first) continue;

            const cells = Array.from(tr.children);
            const teamRaw = lines(first.innerText)[0] || '';
            const dk = cells[dkIndex];
            const dkLines = dk ? lines(dk.innerText) : [];

            rows.push({
              team_raw: teamRaw,
              cell_count: cells.length,
              dk_cell_index: dkIndex,
              dk_text_lines: dkLines,
            });
          }

          const bodyText = document.body.innerText || '';
          return {rows, bodyText};
        }
        """,
        DK_CELL_INDEX
    )

async def main():
    headless = os.environ.get("ACTION_HEADLESS", "1") != "0"
    snapshot_date = datetime.now(timezone.utc).date().isoformat()
    pulled_at = datetime.now(timezone.utc).isoformat()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        page = await browser.new_page(viewport={"width": 1700, "height": 1200})
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        clicked, attempts = await force_select_market(page)

        data = await scrape_rows(page)
        rows = data["rows"]

        parsed = []

        for r in rows:
            team_raw = r["team_raw"]
            dk_lines = r["dk_text_lines"]

            if len(dk_lines) < 4:
                continue
            if any(str(x).upper() == "N/A" for x in dk_lines):
                continue

            over_total = parse_total_token(dk_lines[0])
            over_odds = parse_price(dk_lines[1])
            under_total = parse_total_token(dk_lines[2])
            under_odds = parse_price(dk_lines[3])

            if over_total is None or under_total is None or over_odds is None or under_odds is None:
                continue
            if abs(over_total - under_total) > 0.001:
                continue

            parsed.append({
                "snapshot_date": snapshot_date,
                "season": 2026,
                "team": normalize_team(team_raw),
                "conference": "",
                "book": "DraftKings",
                "win_total": over_total,
                "over_odds": over_odds,
                "under_odds": under_odds,
                "source_url": URL,
                "notes": f"Action rendered table; book=DK OH; cell_index={DK_CELL_INDEX}; pulled_at={pulled_at}; team_raw={team_raw}",
            })

        audit = pd.DataFrame([{
            "pulled_at": pulled_at,
            "headless": headless,
            "clicked": clicked,
            "attempts": json.dumps(attempts),
            "dom_rows_seen": len(rows),
            "parsed_rows": len(parsed),
            "body_has_regular_season": "Regular Season" in data["bodyText"],
            "body_has_total_wins": "Total Wins" in data["bodyText"],
            "body_has_alabama": "Alabama Crimson Tide" in data["bodyText"],
        }])

        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        audit.to_csv(AUDIT, index=False)

        df = pd.DataFrame(parsed)

        print("headless:", headless)
        print("clicked category:", clicked)
        print("attempts:", attempts)
        print("dom rows seen:", len(rows))
        print("rows parsed:", len(df))
        print("wrote audit:", AUDIT)

        if df.empty:
            FAILED.parent.mkdir(parents=True, exist_ok=True)
            FAILED.write_text(data["bodyText"], errors="ignore")
            print("No rows parsed. Did not overwrite existing DK CSV.")
            print("wrote failed body:", FAILED)
            await browser.close()
            raise SystemExit(2)

        OUT.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(OUT, index=False)

        print("wrote:", OUT)

        teams = ["Alabama", "LSU", "Georgia", "UTEP", "New Mexico", "Wake Forest"]
        print(df[df["team"].isin(teams)].to_string(index=False))

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
