#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import py_compile
import re
import shutil
import sys

ROOT = Path.home() / "NCAAF_AUTO"
TARGET = ROOT / "scripts/agents/build_daily_betting_angles_html.py"
BACKUP_ROOT = ROOT / "backups/daily_email_game_line_moves"

HELPER_CODE = r"""
def prepare_agent_game_line_moves(angle_rows, limit=12):
    # Prepare cleaned agent game-line rows for concise email display.
    if angle_rows is None or angle_rows.empty:
        return pd.DataFrame()

    df = angle_rows.copy()
    for column in ["category", "title", "reason", "score", "source"]:
        if column not in df.columns:
            df[column] = ""

    df = df[
        df["category"].fillna("").astype(str).str.casefold().eq("game line move")
    ].copy()

    if df.empty:
        return df

    price_only = df["title"].fillna("").astype(str).str.contains(
        r"\b(?:Spread|Total)\b.*\b(?:Price|Over Price|Under Price)\b",
        case=False,
        regex=True,
    )
    df = df.loc[~price_only].copy()

    extracted = df["title"].fillna("").astype(str).str.extract(
        r"\b(?:Spread|Total)\s+"
        r"(?P<previous>[+-]?\d+(?:\.\d+)?)\s*"
        r"(?:→|->|=>|to)\s*"
        r"(?P<latest>[+-]?\d+(?:\.\d+)?)",
        flags=re.IGNORECASE,
    )

    df["_previous_line"] = pd.to_numeric(extracted["previous"], errors="coerce")
    df["_latest_line"] = pd.to_numeric(extracted["latest"], errors="coerce")
    df = df[
        df["_previous_line"].notna()
        & df["_latest_line"].notna()
        & (df["_latest_line"] - df["_previous_line"]).abs().gt(0)
    ].copy()

    if df.empty:
        return df

    df["_move_size"] = (
        df["_latest_line"] - df["_previous_line"]
    ).abs()

    def clean_reason(value):
        text = "" if pd.isna(value) else str(value)
        text = re.sub(
            r"\s*·\s*price\s*[^·]*",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"\bnan\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s{2,}", " ", text)
        return text.strip(" ·|")

    df["reason"] = df["reason"].map(clean_reason)
    df["_title_key"] = (
        df["title"].fillna("").astype(str).str.casefold()
        .str.replace(r"\s+", " ", regex=True).str.strip()
    )
    df = df.drop_duplicates("_title_key", keep="first")
    df = df.sort_values(["_move_size", "title"], ascending=[False, True]).head(limit)
    df["score"] = df["_move_size"]

    return df.drop(
        columns=["_previous_line", "_latest_line", "_move_size", "_title_key"],
        errors="ignore",
    )
"""

OLD_SELECTION = """    # Prefer the cleaned daily betting angles Market move rows.
    # These already normalize price/odds moves to implied-probability percentage-point changes.
    angle_market_moves = pd.DataFrame()
    if not angles.empty and "category" in angles.columns:
        angle_market_moves = angles[angles["category"].astype(str).str.lower().eq("market move")].copy()

    if not angle_market_moves.empty:
        moves = angle_market_moves.copy()
        game_line_moves = pd.DataFrame()
        move_count = len(moves)
        game_move_count = 0
    else:
        move_count = len(moves)
        game_move_count = len(game_line_moves)
"""

NEW_SELECTION = """    # CLEANED_GAME_LINE_EMAIL_START
    angle_market_moves = pd.DataFrame()
    angle_game_line_moves = pd.DataFrame()

    if not angles.empty and "category" in angles.columns:
        normalized_category = (
            angles["category"].fillna("").astype(str).str.casefold()
        )
        angle_market_moves = angles[
            normalized_category.eq("market move")
        ].copy()
        angle_game_line_moves = prepare_agent_game_line_moves(
            angles,
            limit=12,
        )

    if not angle_market_moves.empty:
        moves = angle_market_moves.copy()

    if not angle_game_line_moves.empty:
        game_line_moves = angle_game_line_moves.copy()

    move_count = len(moves)
    game_move_count = len(game_line_moves)
    # CLEANED_GAME_LINE_EMAIL_END
"""

OLD_RENDER = """    game_line_move_cards = build_game_line_move_cards(game_line_moves, limit=20)
    if game_line_move_cards:
        move_cards = move_cards + "\\n" + game_line_move_cards
"""

NEW_RENDER = """    if not angle_game_line_moves.empty:
        game_line_move_cards = build_agent_cards(
            angle_game_line_moves,
            limit=12,
        )
    else:
        game_line_move_cards = build_game_line_move_cards(
            game_line_moves,
            limit=12,
        )

    if game_line_move_cards:
        move_cards = move_cards + "\\n" + game_line_move_cards
"""

def main() -> None:
    if not TARGET.exists():
        raise FileNotFoundError(TARGET)

    original = TARGET.read_text(encoding="utf-8", errors="ignore")
    updated = original

    if "def prepare_agent_game_line_moves(" not in updated:
        match = re.search(r"(?m)^def main\(\)", updated)
        if not match:
            raise RuntimeError("Could not locate def main()")
        updated = (
            updated[:match.start()]
            + HELPER_CODE.strip()
            + "\n\n\n"
            + updated[match.start():]
        )

    if "# CLEANED_GAME_LINE_EMAIL_START" in updated:
        updated = re.sub(
            r"(?ms)^    # CLEANED_GAME_LINE_EMAIL_START.*?^    # CLEANED_GAME_LINE_EMAIL_END",
            NEW_SELECTION.rstrip(),
            updated,
            count=1,
        )
    elif OLD_SELECTION in updated:
        updated = updated.replace(OLD_SELECTION, NEW_SELECTION, 1)
    else:
        raise RuntimeError("Could not locate selection block")

    if OLD_RENDER in updated:
        updated = updated.replace(OLD_RENDER, NEW_RENDER, 1)
    elif "game_line_move_cards = build_agent_cards(" not in updated:
        raise RuntimeError("Could not locate render block")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_ROOT / timestamp / TARGET.relative_to(ROOT)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TARGET, backup)

    TARGET.write_text(updated, encoding="utf-8")
    py_compile.compile(str(TARGET), doraise=True)

    print(f"patched: {TARGET}")
    print(f"backup:  {backup}")
    print()
    print("DAILY EMAIL GAME-LINE MOVE PATCH")
    print("=" * 100)
    print("Reads cleaned Game line move rows: True")
    print("Actual spread/total moves only: True")
    print("Juice text removed from displayed reasons: True")
    print("Ranks by absolute point movement: True")
    print("Maximum game-line move cards: 12")
    print("Python syntax validation passed: True")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
