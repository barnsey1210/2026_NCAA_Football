#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

NATIVE_NAV = """function buildNav() {
  byId('nav').innerHTML = [
    navBtn('#/','Dashboard'),
    navBtn('#schedule','Season Schedule'),
    navBtn('#line-history','Line History'),
    navBtn('#openers','Openers'),
    navBtn('#results-center','Results Center'),
    navBtn('#rankings','Rankings'),
    navBtn('#market-edges','Futures Market'),
    navBtn('#simulations','Simulations'),
    navBtn('#conferences','Conferences'),
    navBtn('#coach-betting','Coach Trends'),
    navBtn('#betting','Betting')
  ].join('');
}"""

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    # Replace the native left-nav builder with the accepted menu.
    s, n = re.subn(
        r"function buildNav\(\) \{\s*byId\('nav'\)\.innerHTML = \[[\s\S]*?\]\.join\(''\);\s*\}",
        NATIVE_NAV,
        s,
        count=1
    )
    if n != 1:
        raise SystemExit(f"buildNav replacement failed for {path}")

    # Disable old post-render Openers nav insertion. Openers is now native.
    s = re.sub(
        r"window\.installOpenersNav = function\(\)\{[\s\S]*?\n\s*\};\s*"
        r"document\.addEventListener\('DOMContentLoaded', \(\) => setTimeout\(window\.installOpenersNav, 50\)\);\s*"
        r"window\.addEventListener\('hashchange', \(\) => setTimeout\(window\.installOpenersNav, 50\)\);",
        "window.installOpenersNav = function(){};",
        s,
        flags=re.S
    )

    # Extra safety: any remaining direct Home labels in nav button calls.
    s = s.replace("navBtn('#/','Home')", "navBtn('#/','Dashboard')")
    s = s.replace("navBtn('#home','Home')", "navBtn('#home','Dashboard')")

    path.write_text(s, encoding="utf-8")
    print(path, "native left nav cleaned")
