#!/usr/bin/env python3
from pathlib import Path
import re
from datetime import datetime
from zoneinfo import ZoneInfo

LAST_UPDATED_LABEL = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d %I:%M %p ET")

FILES = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

STYLE = '''
<style id="sidebar-last-updated-style">
  .last-updated-sub {
    margin-top: 8px;
    color: #94a3b8;
    font-size: 12px;
    font-weight: 700;
    line-height: 1.25;
  }
  .last-updated-sub strong {
    color: #dbeafe;
    font-weight: 800;
  }
</style>
'''

SCRIPT = ''

for p in FILES:
    if not p.exists():
        continue

    txt = p.read_text(errors="ignore")

    # Remove old dynamic Last Updated script; timestamp is static after build.
    txt = re.sub(
        r'\n?<script id="sidebar-last-updated-script">.*?</script>\n?',
        '\n',
        txt,
        flags=re.S
    )

    # Remove old sidebar prototype text.
    txt = re.sub(
        r'\s*<div class="sub">\s*Workbook-powered prototype\s*</div>',
        '',
        txt,
        flags=re.I
    )
    txt = re.sub(r'Workbook-powered prototype', '', txt, flags=re.I)

    # Remove Season Schedule subtitle blocks.
    txt = re.sub(
        r'\s*<div class="page-sub">\s*Schedule and projections remain workbook-driven\..*?</div>',
        '',
        txt,
        flags=re.S | re.I
    )

    # Remove escaped JS-template version if present.
    txt = re.sub(
        r'\s*<div class=\\"page-sub\\">\s*Schedule and projections remain workbook-driven\..*?</div>',
        '',
        txt,
        flags=re.S | re.I
    )

    # Add Last Updated placeholder after brand.
    if 'id="last-updated-sub"' not in txt:
        txt = txt.replace(
            '<div class="brand">2026 NCAA<br/>Football</div>',
            f'<div class="brand">2026 NCAA<br/>Football</div>\n<div id="last-updated-sub" class="last-updated-sub">Last updated<br><strong>{LAST_UPDATED_LABEL}</strong></div>',
            1
        )

    # last-updated-sub static fill
    txt = re.sub(
        r'<div id="last-updated-sub" class="last-updated-sub">.*?</div>',
        f'<div id="last-updated-sub" class="last-updated-sub">Last updated<br><strong>{LAST_UPDATED_LABEL}</strong></div>',
        txt,
        count=1,
        flags=re.S
    )

    # Add CSS/script once.
    if 'id="sidebar-last-updated-style"' not in txt:
        txt = txt.replace("</head>", STYLE + "\n</head>", 1)

    p.write_text(txt)
    print(f"Cleaned {p}")
