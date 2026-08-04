#!/usr/bin/env python3
"""Fix the daily email game-line card renderer.

The prior patch called build_agent_cards(), but this version of the email
builder does not define that function. Cleaned game-line rows already use the
same category/title/reason schema supported by build_move_cards(), so this
installer switches only that one call.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import py_compile
import shutil
import sys


ROOT = Path.home() / "NCAAF_AUTO"
TARGET = ROOT / "scripts/agents/build_daily_betting_angles_html.py"
BACKUP_ROOT = ROOT / "backups/daily_email_game_line_renderer_fix"

OLD = """    if not angle_game_line_moves.empty:
        game_line_move_cards = build_agent_cards(
            angle_game_line_moves,
            limit=12,
        )
"""

NEW = """    if not angle_game_line_moves.empty:
        game_line_move_cards = build_move_cards(
            angle_game_line_moves,
            limit=12,
        )
"""


def main() -> None:
    if not TARGET.exists():
        raise FileNotFoundError(TARGET)

    original = TARGET.read_text(encoding="utf-8", errors="ignore")

    if OLD not in original:
        if NEW in original:
            print("Renderer fix already installed.")
            py_compile.compile(str(TARGET), doraise=True)
            return
        raise RuntimeError("Could not locate the build_agent_cards game-line block")

    updated = original.replace(OLD, NEW, 1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_ROOT / timestamp / TARGET.relative_to(ROOT)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TARGET, backup)

    TARGET.write_text(updated, encoding="utf-8")
    py_compile.compile(str(TARGET), doraise=True)

    print(f"patched: {TARGET}")
    print(f"backup:  {backup}")
    print()
    print("DAILY EMAIL GAME-LINE RENDERER FIX")
    print("=" * 100)
    print("Undefined build_agent_cards call removed: True")
    print("Existing build_move_cards renderer used: True")
    print("Maximum game-line move cards: 12")
    print("Python syntax validation passed: True")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
