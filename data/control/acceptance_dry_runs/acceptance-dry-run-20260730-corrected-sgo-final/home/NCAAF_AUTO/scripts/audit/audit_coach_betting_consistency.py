#!/usr/bin/env python3
"""Report-only consistency audit for canonical V1 and V2 coach betting data."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "v1.html"
MATCHUPS = ROOT / "data/site/matchups_view.json"
OUT_DIR = ROOT / "data/qa"
OUT_JSON = OUT_DIR / "coach_betting_consistency.json"
OUT_CSV = OUT_DIR / "coach_betting_consistency.csv"
CONSUMERS = ("Team", "Matchup", "Coach Trends")
CATEGORIES = (
    "full_game_ats",
    "full_game_totals",
    "favorite_ats",
    "favorite_totals",
    "underdog_ats",
    "underdog_totals",
    "first_half_ats",
    "first_half_totals",
    "second_half_ats",
    "second_half_totals",
)


def norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def integer(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def parse_ats(value):
    nums = [int(x) for x in re.findall(r"\d+", str(value or ""))]
    if len(nums) < 2:
        return None
    return {"wins": nums[0], "losses": nums[1], "pushes": nums[2] if len(nums) > 2 else 0}


def parse_totals(value):
    text = str(value or "")
    over = re.search(r"(\d+)\s*O\b", text, re.I)
    under = re.search(r"(\d+)\s*U\b", text, re.I)
    push = re.search(r"(\d+)\s*P\b", text, re.I)
    if over and under:
        return {"wins": int(over.group(1)), "losses": int(under.group(1)), "pushes": int(push.group(1)) if push else 0}
    return parse_ats(text)


def record(values, declared_sample=None, source=None):
    if not values:
        return None
    result = {
        "wins": integer(values.get("wins")) or 0,
        "losses": integer(values.get("losses")) or 0,
        "pushes": integer(values.get("pushes")) or 0,
        "declared_sample": integer(declared_sample),
        "source": source,
    }
    result["sample"] = result["wins"] + result["losses"] + result["pushes"]
    return result


def extract_index():
    html = INDEX.read_text(errors="ignore")
    match = re.search(r'<script id="db" type="application/json">(.*?)</script>', html, re.S)
    if not match:
        raise RuntimeError("v1.html is missing embedded DB")
    db = json.loads(match.group(1))
    role_match = re.search(r"window\.COACH_FAV_DOG_TRENDS_PAGE_ROWS\s*=\s*(\[.*?\]);", html, re.S)
    role_rows = json.loads(role_match.group(1)) if role_match else []
    return db, role_rows


def overall_categories(row, period):
    if not row:
        return {}
    if period == "full_game":
        ats = record(
            {"wins": row.get("ats_w"), "losses": row.get("ats_l"), "pushes": row.get("ats_push")},
            (integer(row.get("ats_w")) or 0) + (integer(row.get("ats_l")) or 0) + (integer(row.get("ats_push")) or 0),
        )
        totals = record(
            {"wins": row.get("over_w"), "losses": row.get("under_w"), "pushes": row.get("ou_push")},
            (integer(row.get("over_w")) or 0) + (integer(row.get("under_w")) or 0) + (integer(row.get("ou_push")) or 0),
        )
    else:
        ats = record(
            {"wins": row.get("ats_w"), "losses": row.get("ats_l"), "pushes": row.get("ats_push")},
            row.get("ats_games", row.get("games")),
        )
        totals = record(
            {"wins": row.get("overs"), "losses": row.get("unders"), "pushes": row.get("total_push")},
            row.get("over_games", row.get("games")),
        )
    return {f"{period}_ats": ats, f"{period}_totals": totals}


def payload_period_categories(periods):
    result = {}
    names = {"full_game": "full_game", "first_half": "first_half", "second_half": "second_half"}
    for row in periods or []:
        if not row:
            continue
        period = names.get(row.get("period"))
        if not period:
            continue
        result[f"{period}_ats"] = record(
            parse_ats(row.get("ats_record")), row.get("ats_sample", row.get("sample"))
        )
        result[f"{period}_totals"] = record(
            parse_totals(row.get("ou_record")), row.get("total_sample")
        )
    return result


def role_categories(rows, page_shape=False):
    result = {}
    for row in rows or []:
        if not row:
            continue
        period = str(row.get("period") or "")
        period_key = str(row.get("period_key") or "")
        if period not in {"Full Game", "full_game"} and period_key != "game":
            continue
        role = str(row.get("role") or row.get("fav_dog") or row.get("role_key") or "").lower()
        if role not in {"favorite", "underdog"}:
            continue
        ats_value = row.get("ats_record")
        totals_value = row.get("ou_record")
        declared = row.get("games")
        result[f"{role}_ats"] = record(parse_ats(ats_value), declared)
        result[f"{role}_totals"] = record(parse_totals(totals_value))
    return result


def canonical_sources(db, role_rows):
    coaches = {}
    for row in db.get("coach_betting", []):
        coach = row.get("head_coach") or row.get("coach")
        if not coach:
            continue
        entry = coaches.setdefault(norm(coach), {"coach": coach, "team": row.get("team"), "categories": {}})
        entry["categories"].update(overall_categories(row, "full_game"))
    for key, period in (("coach_1h_betting", "first_half"), ("coach_2h_betting", "second_half")):
        for row in db.get(key, []):
            coach = row.get("current_coach") or row.get("head_coach") or row.get("coach")
            if not coach:
                continue
            entry = coaches.setdefault(norm(coach), {"coach": coach, "team": row.get("current_team") or row.get("team"), "categories": {}})
            entry["categories"].update(overall_categories(row, period))
    for row in role_rows:
        coach = row.get("head_coach") or row.get("coach")
        if not coach:
            continue
        entry = coaches.setdefault(norm(coach), {"coach": coach, "team": row.get("team"), "categories": {}})
        entry["categories"].update(role_categories([row]))
    for entry in coaches.values():
        for category, value in entry["categories"].items():
            if value:
                value["source"] = (
                    "data/coach/coach_fav_dog_splits_hybrid.csv"
                    if category.startswith(("favorite_", "underdog_"))
                    else "v1.html embedded canonical V1 coach arrays"
                )
    return coaches


def coach_trends_consumer(db, role_rows):
    return canonical_sources(db, role_rows)


def matchup_consumers(payload):
    coaches = {}
    for game in payload.get("games", []):
        for row in game.get("matchup", {}).get("coaches", []):
            if not row or not row.get("coach"):
                continue
            entry = coaches.setdefault(norm(row["coach"]), {"coach": row["coach"], "team": row.get("team"), "categories": {}})
            entry["categories"].update(payload_period_categories(row.get("periods")))
            entry["categories"].update(role_categories(row.get("role_splits"), page_shape=True))
    return coaches


def same_counts(a, b, *, allow_missing_zero=False):
    if allow_missing_zero and a and a["sample"] == 0 and not b:
        return True
    return bool(a and b) and all(a[key] == b[key] for key in ("wins", "losses", "pushes", "sample"))


def render_record(value, totals=False):
    if not value:
        return "—"
    labels = ("O", "U", "P") if totals else ("W", "L", "P")
    return f"{value['wins']}{labels[0]}-{value['losses']}{labels[1]}-{value['pushes']}{labels[2]} (N={value['sample']})"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="exit nonzero when mismatches exist")
    args = parser.parse_args()
    db, role_rows = extract_index()
    canonical = canonical_sources(db, role_rows)
    trends = coach_trends_consumer(db, role_rows)
    payload = json.loads(MATCHUPS.read_text())
    shared = matchup_consumers(payload)
    consumers = {"Team": shared, "Matchup": shared, "Coach Trends": trends}

    rows = []
    page_mismatches = {page: 0 for page in CONSUMERS}
    page_coaches = {page: set() for page in CONSUMERS}
    largest_losses = []
    integrity_issues = []

    for coach_key, canon_entry in sorted(canonical.items(), key=lambda item: item[1]["coach"]):
        for category in CATEGORIES:
            expected = canon_entry["categories"].get(category)
            if not expected:
                continue
            totals = category.endswith("_totals")
            for page in CONSUMERS:
                actual = consumers[page].get(coach_key, {}).get("categories", {}).get(category)
                match = same_counts(expected, actual, allow_missing_zero=page in {"Team", "Matchup"})
                loss = None if not actual or expected["sample"] == 0 else (expected["sample"] - actual["sample"]) / expected["sample"]
                below_10 = expected["sample"] > 0 and (actual is None or (loss is not None and loss > 0.10))
                status = "equivalent_zero" if match and not actual else ("match" if match else ("missing" if not actual else "mismatch"))
                if not match:
                    page_mismatches[page] += 1
                    page_coaches[page].add(coach_key)
                if loss is not None and loss > 0:
                    largest_losses.append({"coach": canon_entry["coach"], "page": page, "category": category, "canonical_sample": expected["sample"], "consumer_sample": actual["sample"], "loss_pct": round(loss * 100, 2)})
                declared_ok = actual is None or actual.get("declared_sample") is None or actual["declared_sample"] == actual["sample"]
                if not declared_ok:
                    integrity_issues.append({"coach": canon_entry["coach"], "page": page, "category": category, "issue": "record sum does not equal displayed sample", "record_sample": actual["sample"], "displayed_sample": actual["declared_sample"]})
                rows.append({
                    "coach": canon_entry["coach"], "team": canon_entry.get("team"), "category": category, "consumer": page,
                    "canonical_wins": expected["wins"], "canonical_losses": expected["losses"], "canonical_pushes": expected["pushes"], "canonical_sample": expected["sample"],
                    "consumer_wins": actual["wins"] if actual else None, "consumer_losses": actual["losses"] if actual else None,
                    "consumer_pushes": actual["pushes"] if actual else None, "consumer_sample": actual["sample"] if actual else None,
                    "displayed_sample": actual.get("declared_sample") if actual else None, "record_sum_matches_displayed_sample": declared_ok,
                    "sample_loss_pct": round(loss * 100, 2) if loss is not None else None, "more_than_10_pct_below_canonical": below_10,
                    "status": status, "canonical_source": expected.get("source"),
                })

    # Favorite and underdog samples cannot individually exceed full-game samples.
    for source_name, source in [("Canonical", canonical), *consumers.items()]:
        for entry in source.values():
            cats = entry.get("categories", {})
            for metric in ("ats", "totals"):
                full = cats.get(f"full_game_{metric}")
                for role in ("favorite", "underdog"):
                    split = cats.get(f"{role}_{metric}")
                    if full and split and split["sample"] > full["sample"]:
                        integrity_issues.append({"coach": entry["coach"], "page": source_name, "category": f"{role}_{metric}", "issue": "role sample exceeds full-game sample", "role_sample": split["sample"], "full_game_sample": full["sample"]})

    cross_consumer = []
    for coach_key, canon_entry in canonical.items():
        for category in CATEGORIES:
            values = {page: consumers[page].get(coach_key, {}).get("categories", {}).get(category) for page in CONSUMERS}
            available = [(page, value) for page, value in values.items() if value]
            if len(available) > 1 and any(not same_counts(available[0][1], value) for _, value in available[1:]):
                cross_consumer.append({"coach": canon_entry["coach"], "category": category, "consumers": {page: value for page, value in available}})

    largest_losses.sort(key=lambda row: (row["loss_pct"], row["canonical_sample"]), reverse=True)
    lane_key = norm("Lane Kiffin")
    lane = {
        "canonical": canonical.get(lane_key),
        "consumers": {page: consumers[page].get(lane_key) for page in CONSUMERS},
    }
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "report-only" if not args.strict else "strict",
        "canonical_sources": [
            {"categories": ["full_game_ats", "full_game_totals", "first_half_ats", "first_half_totals", "second_half_ats", "second_half_totals"], "artifact": "v1.html embedded canonical V1 coach arrays", "upstream": "Coach_betting_data/2026_NCAA_Season_updated_coach_betting_summary.xlsm plus data/import/coach_1h_betting_current_2026.csv and data/import/coach_2h_betting_current_2026.csv"},
            {"categories": ["favorite_ats", "favorite_totals", "underdog_ats", "underdog_totals"], "artifact": "data/coach/coach_fav_dog_splits_hybrid.csv", "upstream": "data/coach/coach_full_game_fav_dog_cfbd_splits.csv remapped to active 2026 coach/team pairs"},
        ],
        "v2_consumers": {
            "Team": "team_coach_card.js -> data/site/matchups_view.json",
            "Matchup": "matchups_v2.html -> data/site/matchups_view.json",
            "Coach Trends": "v1.html coach-betting route -> embedded canonical arrays and COACH_FAV_DOG_TRENDS_PAGE_ROWS",
        },
        "summary": {
            "coaches_checked": len(canonical),
            "comparison_rows": len(rows),
            "mismatch_count_by_page": page_mismatches,
            "coaches_with_mismatch_by_page": {page: len(keys) for page, keys in page_coaches.items()},
            "cross_consumer_mismatches": len(cross_consumer),
            "integrity_issues": len(integrity_issues),
            "more_than_10_pct_below_canonical": sum(1 for row in rows if row["more_than_10_pct_below_canonical"]),
        },
        "largest_sample_size_losses": largest_losses[:25],
        "lane_kiffin": lane,
        "cross_consumer_mismatches": cross_consumer,
        "integrity_issues": integrity_issues,
        "comparisons": rows,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["coach"])
        writer.writeheader()
        writer.writerows(rows)

    print("COACH BETTING CONSISTENCY AUDIT (REPORT ONLY)" if not args.strict else "COACH BETTING CONSISTENCY AUDIT (STRICT)")
    print("Canonical source: V1 embedded coach arrays; full-game role splits from coach_fav_dog_splits_hybrid.csv")
    for page, path in report["v2_consumers"].items():
        print(f"V2 consumer: {page}: {path}")
    print(f"Coaches checked: {len(canonical)}")
    print("Mismatch comparisons by page: " + ", ".join(f"{page}={page_mismatches[page]}" for page in CONSUMERS))
    print("Largest sample-size losses:")
    for item in largest_losses[:8]:
        print(f"  {item['coach']} | {item['page']} | {item['category']} | {item['canonical_sample']} -> {item['consumer_sample']} ({item['loss_pct']:.1f}% loss)")
    print("Lane Kiffin:")
    lane_cats = canonical.get(lane_key, {}).get("categories", {})
    for category in CATEGORIES:
        expected = lane_cats.get(category)
        if not expected:
            continue
        actuals = []
        for page in CONSUMERS:
            actual = consumers[page].get(lane_key, {}).get("categories", {}).get(category)
            actuals.append(f"{page}={render_record(actual, category.endswith('_totals'))}")
        print(f"  {category}: canonical={render_record(expected, category.endswith('_totals'))}; " + "; ".join(actuals))
    print(f"Wrote: {OUT_JSON.relative_to(ROOT)}")
    print(f"Wrote: {OUT_CSV.relative_to(ROOT)}")
    mismatch_total = sum(page_mismatches.values()) + len(integrity_issues) + len(cross_consumer)
    if mismatch_total:
        print(f"WARNING: {mismatch_total} coach-betting consistency findings (report-only; publishing is not blocked)")
    else:
        print("PASS: all audited coach-betting records are consistent")
    if args.strict and mismatch_total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
