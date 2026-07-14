#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

REMOVE_BLOCKS = [
    ("<!-- rename-home-dashboard-cleanup-start -->", "<!-- rename-home-dashboard-cleanup-end -->"),
    ("<!-- fix-home-command-center-toggle-start -->", "<!-- fix-home-command-center-toggle-end -->"),
    ("<!-- openers-navigation-guard-start -->", "<!-- openers-navigation-guard-end -->"),
]

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    # Remove known post-render wrappers/guards that cause flicker or navigation issues.
    for start, end in REMOVE_BLOCKS:
        if start in s and end in s:
            s = re.sub(re.escape(start) + r".*?" + re.escape(end), "", s, flags=re.S)

    # Native Dashboard nav label in the base nav render.
    s = re.sub(r"navBtn\('#home'\s*,\s*'Home'\)", "navBtn('#home','Dashboard')", s)
    s = s.replace(">Home</button>", ">Dashboard</button>")

    # Remove duplicate / old Openers guard from older daily runs.
    s = re.sub(
        r"<!-- openers-navigation-guard-start -->.*?<!-- openers-navigation-guard-end -->",
        "",
        s,
        flags=re.S
    )

    # Do not remove page-specific wrappers yet. Only remove the confirmed dashboard/toggle/guard blocks.
    path.write_text(s, encoding="utf-8")
    print(path, "cleaned render-wrapper flicker blocks")

