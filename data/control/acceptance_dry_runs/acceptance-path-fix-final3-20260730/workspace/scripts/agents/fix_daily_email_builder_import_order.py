#!/usr/bin/env python3
"""Repair import ordering in build_daily_betting_angles_html.py.

Removes any misplaced standalone `import re` lines and reinserts `import re`
after all `from __future__ import ...` lines, which preserves Python's required
future-import ordering.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import py_compile
import shutil
import sys


ROOT = Path.home() / "NCAAF_AUTO"
TARGET = ROOT / "scripts/agents/build_daily_betting_angles_html.py"
BACKUP_ROOT = ROOT / "backups/daily_email_builder_import_order_fix"


def main() -> None:
    if not TARGET.exists():
        raise FileNotFoundError(TARGET)

    original = TARGET.read_text(encoding="utf-8", errors="ignore")
    lines = original.splitlines()

    # Remove every standalone import re first.
    lines = [line for line in lines if line.strip() != "import re"]

    # Locate the last future import. If none exists, insert after shebang/docstring area.
    future_indexes = [
        i for i, line in enumerate(lines)
        if line.startswith("from __future__ import ")
    ]

    if future_indexes:
        insert_at = max(future_indexes) + 1
    else:
        insert_at = 0
        if lines and lines[0].startswith("#!"):
            insert_at = 1

    lines.insert(insert_at, "import re")

    updated = "\n".join(lines)
    if original.endswith("\n"):
        updated += "\n"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_ROOT / timestamp / TARGET.relative_to(ROOT)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TARGET, backup)

    TARGET.write_text(updated, encoding="utf-8")
    py_compile.compile(str(TARGET), doraise=True)

    print(f"patched: {TARGET}")
    print(f"backup:  {backup}")
    print()
    print("DAILY EMAIL BUILDER IMPORT ORDER FIX")
    print("=" * 100)
    print("Misplaced import re removed: True")
    print("import re placed after future imports: True")
    print("Python syntax validation passed: True")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
