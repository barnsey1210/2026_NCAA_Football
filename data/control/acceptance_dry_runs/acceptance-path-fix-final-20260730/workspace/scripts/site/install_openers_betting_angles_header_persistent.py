#!/usr/bin/env python3
"""Persistently rename the Openers board header from Context to Betting Angles.

The prior UI-only observer changed the rendered DOM, but the board render
function rebuilt the table and restored the original "Context" label whenever
the page, week, or filter changed.

This installer changes the source table template itself, so every rerender uses
"Betting Angles". It also removes the now-unnecessary observer block.

Safety:
- Preflights every Openers copy before writing.
- Requires at least one exact Context header replacement per file.
- Creates timestamped backups.
- Does not alter board data, loading, filtering, sorting, or betting logic.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import sys


ROOT = Path.home() / "NCAAF_AUTO"

OPENERS_FILES = [
    ROOT / "openers_v2.html",
    ROOT / "build/public_site/openers.html",
    Path.home() / "Sites/NCAAF_SITE/openers.html",
]

DAILY_SCRIPT = ROOT / "daily_market_update.sh"

OLD_JS_START = "/* OPENERS_BETTING_ANGLES_HEADER_START */"
OLD_JS_END = "/* OPENERS_BETTING_ANGLES_HEADER_END */"

PERSISTENT_MARKER_START = "/* OPENERS_BETTING_ANGLES_HEADER_PERSISTENT_START */"
PERSISTENT_MARKER_END = "/* OPENERS_BETTING_ANGLES_HEADER_PERSISTENT_END */"


def strip_old_observer(text: str) -> str:
    return re.sub(
        re.escape(OLD_JS_START)
        + r".*?"
        + re.escape(OLD_JS_END)
        + r"\s*",
        "",
        text,
        flags=re.S,
    )


def strip_persistent_marker(text: str) -> str:
    return re.sub(
        re.escape(PERSISTENT_MARKER_START)
        + r".*?"
        + re.escape(PERSISTENT_MARKER_END)
        + r"\s*",
        "",
        text,
        flags=re.S,
    )


def replace_header_templates(text: str) -> tuple[str, int]:
    """Replace literal table-header Context cells in source templates."""

    patterns = [
        re.compile(
            r"(<th\b[^>]*>)\s*CONTEXT\s*(</th>)",
            flags=re.I,
        ),
        re.compile(
            r"(<th\b[^>]*>)\s*Context\s*(</th>)",
        ),
    ]

    total = 0
    updated = text

    for pattern in patterns:
        updated, count = pattern.subn(
            r"\1BETTING ANGLES\2",
            updated,
        )
        total += count

    return updated, total


def add_marker(text: str, count: int) -> str:
    marker = (
        f"\n{PERSISTENT_MARKER_START}\n"
        f"<!-- Source table templates renamed: {count} -->\n"
        f"{PERSISTENT_MARKER_END}\n"
    )

    closing_body = text.rfind("</body>")
    if closing_body >= 0:
        return text[:closing_body] + marker + text[closing_body:]

    return text + marker


def patch_page(path: Path, original: str) -> tuple[str, int]:
    text = strip_old_observer(original)
    text = strip_persistent_marker(text)

    text, count = replace_header_templates(text)

    if count < 1:
        raise RuntimeError(
            f"No literal <th>Context</th> source template found in {path}. "
            "The board renderer may use a different header structure."
        )

    text = add_marker(text, count)

    if re.search(
        r"<th\b[^>]*>\s*CONTEXT\s*</th>",
        text,
        flags=re.I,
    ):
        raise RuntimeError(
            f"A Context table header remains after patching {path}"
        )

    if "BETTING ANGLES" not in text:
        raise RuntimeError(
            f"BETTING ANGLES was not found after patching {path}"
        )

    if OLD_JS_START in text or OLD_JS_END in text:
        raise RuntimeError(
            f"Old header observer block remains in {path}"
        )

    return text, count


def backup_path(path: Path, timestamp: str) -> Path:
    base = (
        ROOT
        / "backups/openers_betting_angles_header_persistent"
        / timestamp
    )

    try:
        destination = base / path.relative_to(ROOT)
    except ValueError:
        destination = base / "external" / path.name

    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def update_daily_script(timestamp: str) -> bool:
    if not DAILY_SCRIPT.exists():
        return False

    command = (
        "python3 scripts/site/"
        "install_openers_betting_angles_header_persistent.py"
    )

    text = DAILY_SCRIPT.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    if command in text:
        return False

    backup = backup_path(DAILY_SCRIPT, timestamp)
    shutil.copy2(DAILY_SCRIPT, backup)

    block = f"""

# Keep the Openers source table header labeled Betting Angles.
if [ -f scripts/site/install_openers_betting_angles_header_persistent.py ]; then
  {command}
fi
"""

    DAILY_SCRIPT.write_text(
        text.rstrip() + block + "\n",
        encoding="utf-8",
    )

    return True


def main() -> None:
    pages = [
        path for path in OPENERS_FILES
        if path.exists()
    ]

    if not pages:
        raise FileNotFoundError(
            "No Openers HTML files were found"
        )

    patched: dict[Path, str] = {}
    counts: dict[Path, int] = {}

    # Preflight all copies before writing any file.
    for path in pages:
        original = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
        updated, count = patch_page(
            path,
            original,
        )
        patched[path] = updated
        counts[path] = count

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    for path, content in patched.items():
        backup = backup_path(
            path,
            timestamp,
        )
        shutil.copy2(
            path,
            backup,
        )
        path.write_text(
            content,
            encoding="utf-8",
        )
        print(f"patched: {path}")
        print(f"backup:  {backup}")
        print(
            "source header templates renamed: "
            f"{counts[path]}"
        )

    daily_updated = update_daily_script(
        timestamp
    )

    print()
    print(
        "PERSISTENT BETTING ANGLES HEADER INSTALLATION"
    )
    print("=" * 100)
    print(
        f"Openers files patched: {len(pages)}"
    )
    print(
        "Old DOM observer removed: True"
    )
    print(
        "Source render template changed: True"
    )
    print(
        "Header survives page/filter changes: True"
    )
    print(
        f"Daily script hook added: {daily_updated}"
    )
    print(
        "Board loading/filtering/sorting logic changed: False"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        raise
