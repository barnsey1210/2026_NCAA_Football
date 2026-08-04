#!/usr/bin/env python3
from pathlib import Path
import re
import sys

LIMITS = {"index.html": 11 * 1024 * 1024, "matchup.html": 8 * 1024 * 1024}


def blocks(html):
    found = []
    for match in re.finditer(r"<(script|style)([^>]*)>(.*?)</\1>", html, re.S | re.I):
        ident = re.search(r'id=["\']([^"\']+)', match.group(2), re.I)
        found.append((len(match.group(3).encode()), ident.group(1) if ident else f"anonymous-{match.group(1).lower()}"))
    return sorted(found, reverse=True)


failed = False
for name, limit in LIMITS.items():
    path = Path(name)
    if not path.exists():
        print(f"FAIL: missing {name}")
        failed = True
        continue
    size = path.stat().st_size
    state = "PASS" if size <= limit else "FAIL"
    print(f"{state}: {name} {size / 1024 / 1024:.2f} MiB (budget {limit / 1024 / 1024:.0f} MiB)")
    for block_size, ident in blocks(path.read_text(errors="ignore"))[:5]:
        print(f"  {ident}: {block_size / 1024 / 1024:.2f} MiB")
    failed = failed or size > limit

sys.exit(1 if failed else 0)
