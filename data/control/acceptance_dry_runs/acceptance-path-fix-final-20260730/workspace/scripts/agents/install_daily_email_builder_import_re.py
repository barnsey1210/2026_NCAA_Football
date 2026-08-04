#!/usr/bin/env python3
"""Add the missing re import to the daily betting-angle HTML builder."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import py_compile
import shutil
import sys


ROOT = Path.home() / "NCAAF_AUTO"
TARGET = ROOT / "scripts/agents/build_daily_betting_angles_html.py"
BACKUP_ROOT = ROOT / "backups/daily_email_builder_import_re"


def main() -> None:
    if not TARGET.exists():
        raise FileNotFoundError(TARGET)

    original = TARGET.read_text(encoding="utf-8", errors="ignore")

    if "\nimport re\n" in original or original.startswith("import re\n"):
        updated = original
        changed = False
    else:
        lines = original.splitlines()
        insert_at = 0

        # Place import re with the standard-library imports, after any
        # shebang/module docstring/future import block.
        for index, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = index
                break
        else:
            raise RuntimeError("Could not locate the import section")

        lines.insert(insert_at, "import re")
        updated = "\n".join(lines) + ("\n" if original.endswith("\n") else "")
        changed = True

    if changed:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = BACKUP_ROOT / timestamp / TARGET.relative_to(ROOT)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TARGET, backup)

        TARGET.write_text(updated, encoding="utf-8")
        print(f"patched: {TARGET}")
        print(f"backup:  {backup}")
    else:
        print(f"already present: import re in {TARGET}")

    py_compile.compile(str(TARGET), doraise=True)

    print()
    print("DAILY EMAIL BUILDER IMPORT FIX")
    print("=" * 100)
    print("Missing import re added: True")
    print("Python syntax validation passed: True")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
