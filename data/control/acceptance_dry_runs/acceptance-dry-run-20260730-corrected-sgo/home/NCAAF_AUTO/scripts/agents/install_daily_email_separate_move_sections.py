#!/usr/bin/env python3
"""Separate Game Line Moves from Market Moves in the daily email."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import py_compile
import shutil
import sys

ROOT = Path.home() / "NCAAF_AUTO"
TARGET = ROOT / "scripts/agents/build_daily_betting_angles_html.py"
BACKUP_ROOT = ROOT / "backups/daily_email_separate_move_sections"

OLD_COMBINE = '''    if game_line_move_cards:
        move_cards = move_cards + "\\n" + game_line_move_cards
    game_cards = build_game_line_cards(angles, limit=18)
'''

NEW_COMBINE = '''    game_cards = build_game_line_cards(angles, limit=18)
'''

OLD_DOC = '''    <div class="summary">
      Daily market moves are listed first so you can quickly see what changed since the previous snapshot.
      Game line edges and current arbitrage opportunities are included after the move section.
    </div>
    <div class="subline">
      Market moves in this report: {move_count} · Game line moves: {game_move_count} · Game line edges: {game_count} · Arbitrage opportunities: {arb_count}
    </div>

    <h2>Daily Market Moves</h2>
    <p class="muted">Top win total and conference futures moves from the latest daily report. Cards include the move date and snapshot window.</p>
    {move_cards}

    <h2>Game Line Edges</h2>
'''

NEW_DOC = '''    <div class="summary">
      Game line moves are listed first so you can quickly see the largest spread and total changes.
      Futures market moves, game line edges, and current arbitrage opportunities follow.
    </div>
    <div class="subline">
      Game line moves in this report: {game_move_count} · Market moves: {move_count} · Game line edges: {game_count} · Arbitrage opportunities: {arb_count}
    </div>

    <h2>Game Line Moves</h2>
    <p class="muted">Largest actual spread and total changes from the latest daily snapshot. Juice-only changes are excluded.</p>
    {game_line_move_cards}

    <h2>Daily Market Moves</h2>
    <p class="muted">Top win total, conference futures, and playoff price moves from the latest daily report.</p>
    {move_cards}

    <h2>Game Line Edges</h2>
'''


def main() -> None:
    if not TARGET.exists():
        raise FileNotFoundError(TARGET)

    original = TARGET.read_text(encoding="utf-8", errors="ignore")
    updated = original

    if OLD_COMBINE in updated:
        updated = updated.replace(OLD_COMBINE, NEW_COMBINE, 1)
    elif NEW_COMBINE not in updated:
        raise RuntimeError("Could not locate the move-card combination block")

    if OLD_DOC in updated:
        updated = updated.replace(OLD_DOC, NEW_DOC, 1)
    elif "<h2>Game Line Moves</h2>" not in updated:
        raise RuntimeError("Could not locate the email move-section HTML block")

    if 'move_cards = move_cards + "\\n" + game_line_move_cards' in updated:
        raise RuntimeError("Game-line cards are still merged into market cards")

    game_line_pos = updated.find("<h2>Game Line Moves</h2>")
    market_pos = updated.find("<h2>Daily Market Moves</h2>")
    edges_pos = updated.find("<h2>Game Line Edges</h2>")

    if not (0 <= game_line_pos < market_pos < edges_pos):
        raise RuntimeError("Email section order validation failed")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_ROOT / timestamp / TARGET.relative_to(ROOT)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TARGET, backup)

    TARGET.write_text(updated, encoding="utf-8")
    py_compile.compile(str(TARGET), doraise=True)

    print(f"patched: {TARGET}")
    print(f"backup:  {backup}")
    print()
    print("DAILY EMAIL MOVE SECTION SEPARATION")
    print("=" * 100)
    print("Game Line Moves separate section: True")
    print("Game Line Moves displayed first: True")
    print("Daily Market Moves displayed second: True")
    print("Game Line Edges/arbitrage unchanged: True")
    print("Python syntax validation passed: True")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
