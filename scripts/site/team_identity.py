#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TEAM_DB = ROOT / "data/snapshots/preseason/preseason_db.json"
ALIASES_FILE = ROOT / "config/team_aliases.json"
LOGO_DIR = ROOT / "logos"


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


@lru_cache(maxsize=1)
def _context():
    db = json.loads(TEAM_DB.read_text())
    teams = db.get("teams", [])

    by_name = {}
    by_norm = {}
    by_slug = {}

    for row in teams:
        name = str(row.get("team") or "").strip()
        slug = str(row.get("slug") or "").strip()
        if not name or not slug:
            continue

        by_name[name] = row
        by_norm[_norm(name)] = row
        by_slug[slug] = row

    cfg = json.loads(ALIASES_FILE.read_text()) if ALIASES_FILE.exists() else {}
    aliases = cfg.get("aliases", {})

    alias_norm = {}
    for alias, target in aliases.items():
        target_row = by_name.get(target)
        if target_row:
            alias_norm[_norm(alias)] = target_row

    return {
        "teams": teams,
        "by_name": by_name,
        "by_norm": by_norm,
        "by_slug": by_slug,
        "alias_norm": alias_norm,
    }


def canonical_team(value: Any) -> dict | None:
    if isinstance(value, dict):
        # Prefer already-canonical metadata when supplied.
        slug = str(value.get("logo_slug") or value.get("slug") or "").strip()
        if slug:
            row = _context()["by_slug"].get(slug)
            if row:
                return row

        value = (
            value.get("team")
            or value.get("name")
            or value.get("team_name")
            or ""
        )

    raw = str(value or "").strip()
    if not raw:
        return None

    ctx = _context()

    if raw in ctx["by_name"]:
        return ctx["by_name"][raw]

    n = _norm(raw)

    if n in ctx["alias_norm"]:
        return ctx["alias_norm"][n]

    if n in ctx["by_norm"]:
        return ctx["by_norm"][n]

    return None


def canonical_team_name(value: Any) -> str | None:
    row = canonical_team(value)
    return str(row["team"]) if row else None


def canonical_team_slug(value: Any) -> str | None:
    row = canonical_team(value)
    return str(row["slug"]) if row else None


def team_logo_path(value: Any) -> str | None:
    slug = canonical_team_slug(value)
    if not slug:
        return None

    path = LOGO_DIR / f"{slug}.png"
    if not path.exists():
        return None

    return f"logos/{slug}.png"


def team_logo_slug_lookup() -> dict[str, str]:
    """Return canonical team names and configured aliases mapped to logo slugs."""
    ctx = _context()
    lookup: dict[str, str] = {}

    # Canonical 138-team universe.
    for row in ctx["teams"]:
        name = str(row.get("team") or "").strip()
        slug = str(row.get("slug") or "").strip()
        if name and slug:
            lookup[name] = slug

    # Exact configured aliases. Alias targets were validated against
    # the canonical team universe when _context() was built.
    cfg = json.loads(ALIASES_FILE.read_text()) if ALIASES_FILE.exists() else {}
    for alias, target in cfg.get("aliases", {}).items():
        row = ctx["by_name"].get(target)
        if row and row.get("slug"):
            lookup[str(alias)] = str(row["slug"])

    return lookup



def audit():
    ctx = _context()

    missing = []
    for row in ctx["teams"]:
        logo = LOGO_DIR / f"{row['slug']}.png"
        if not logo.exists():
            missing.append((row["team"], row["slug"]))

    return {
        "canonical_teams": len(ctx["teams"]),
        "aliases": len(ctx["alias_norm"]),
        "missing_logos": missing,
    }


if __name__ == "__main__":
    result = audit()
    print("canonical teams:", result["canonical_teams"])
    print("aliases:", result["aliases"])
    print("missing canonical logos:", len(result["missing_logos"]))
    for row in result["missing_logos"]:
        print(row)
