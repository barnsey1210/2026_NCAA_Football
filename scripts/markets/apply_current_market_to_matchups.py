#!/usr/bin/env python3
"""Apply the canonical current-market contract to Matchups/Openers/Home payload.

This is a transitional adapter. It removes page-facing stale fallback values
and maps the canonical contract into the existing matchups_view market schema.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/site/current_market_contract.json"
MATCHUPS = ROOT / "data/site/matchups_view.json"


def atomic_json(path: Path, value: dict) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def quote_view(q):
    if not q:
        return None
    return {
        "line": q.get("line"),
        "price": q.get("price"),
        "book": q.get("sportsbook"),
        "source": q.get("source"),
        "updated_at": q.get("source_updated_at"),
        "freshness_status": q.get("freshness_status"),
    }


def main() -> None:
    contract = json.loads(CONTRACT.read_text())
    payload = json.loads(MATCHUPS.read_text())
    by_id = {str(g["game_id"]): g for g in contract.get("games", [])}

    applied = 0
    missing = 0
    for row in payload.get("games", []):
        gid = str(row.get("game", {}).get("game_id") or "")
        current = by_id.get(gid)
        if not current:
            continue

        market = row.setdefault("market", {})
        status = current.get("availability_status", "MISSING")
        ref_spread = current.get("reference", {}).get("spread")
        ref_total = current.get("reference", {}).get("total")
        best = current.get("best", {})

        if status == "MISSING":
            missing += 1
            market["spread"] = {
                "home_line": None, "price": None, "book": None, "updated_at": None,
                "availability_status": "MISSING",
                "availability_reason": current.get("availability_reason"),
                "best_home": None, "best_away": None,
            }
            market["total"] = {
                "line": None, "over_price": None, "under_price": None,
                "book": None, "updated_at": None,
                "availability_status": "MISSING",
                "availability_reason": current.get("availability_reason"),
                "best_over": None, "best_under": None,
            }
            market["moneyline"] = {
                "away_price": None, "home_price": None, "book": None,
                "updated_at": None, "availability_status": "MISSING",
                "availability_reason": current.get("availability_reason"),
            }
            continue

        spread_home = (ref_spread or {}).get("home")
        total_over = (ref_total or {}).get("over")
        total_under = (ref_total or {}).get("under")
        ml_away = (current.get("reference", {}).get("moneyline") or {}).get("away")
        ml_home = (current.get("reference", {}).get("moneyline") or {}).get("home")

        best_home = quote_view(best.get("home_spread"))
        best_away = quote_view(best.get("away_spread"))
        if best_home:
            best_home["home_line"] = best_home.pop("line")
        if best_away:
            # Existing Openers/Matchups schema stores the home-perspective line.
            best_away["home_line"] = -best_away.pop("line")

        market["spread"] = {
            "home_line": spread_home.get("line") if spread_home else None,
            "price": spread_home.get("price") if spread_home else None,
            "book": (ref_spread or {}).get("sportsbook"),
            "updated_at": spread_home.get("source_updated_at") if spread_home else None,
            "availability_status": status,
            "availability_reason": current.get("availability_reason"),
            "best_home": best_home,
            "best_away": best_away,
        }
        market["total"] = {
            "line": total_over.get("line") if total_over else None,
            "over_price": total_over.get("price") if total_over else None,
            "under_price": total_under.get("price") if total_under else None,
            "book": (ref_total or {}).get("sportsbook"),
            "updated_at": total_over.get("source_updated_at") if total_over else None,
            "availability_status": status,
            "availability_reason": current.get("availability_reason"),
            "best_over": quote_view(best.get("over")),
            "best_under": quote_view(best.get("under")),
        }
        market["moneyline"] = {
            "away_price": ml_away.get("price") if ml_away else None,
            "home_price": ml_home.get("price") if ml_home else None,
            "book": (current.get("reference", {}).get("moneyline") or {}).get("sportsbook"),
            "updated_at": ml_away.get("source_updated_at") if ml_away else None,
            "availability_status": status,
            "availability_reason": current.get("availability_reason"),
        }
        applied += 1

    payload["current_market_contract"] = {
        "schema_version": contract.get("schema_version"),
        "built_at": contract.get("built_at"),
        "source": "data/site/current_market_contract.json",
        "stale_data_policy": contract.get("stale_data_policy"),
    }
    atomic_json(MATCHUPS, payload)
    print(json.dumps({"games_applied": applied, "games_missing_current": missing}, indent=2))


if __name__ == "__main__":
    main()
