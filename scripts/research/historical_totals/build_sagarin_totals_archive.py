#!/usr/bin/env python3

from __future__ import annotations

import csv
import gzip
import json
import re
import time
import zlib
from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]

CAPTURES = (
    ROOT
    / "research/historical_totals/sagarin/"
    / "wayback_all_captures_2021_2025.json"
)

CACHE = (
    ROOT
    / "research/historical_totals/sagarin/archive_html"
)

OUT = (
    ROOT
    / "data/research/historical_totals/sagarin/"
    / "sagarin_totals_all_snapshots_2021_2025.csv"
)

AUDIT = (
    ROOT
    / "data/research/historical_totals/sagarin/"
    / "sagarin_totals_archive_audit.json"
)


OLD_RE = re.compile(
    r"^\s*(?P<neutral>n\s+)?"
    r"(?P<favorite>.+?)\s{2,}"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s{2,}"
    r"(?P<underdog>.+?)\s{2,}"
    r"\d+\s+"
    r"\d+%\s+"
    r"(?P<total>\d+\.\d{2})\s*$"
)


RE_2024 = re.compile(
    r"^\s*"
    r"(?:(?P<neutral>[NC])\s+)?"
    r"(?P<favorite_loc>@\s+)?"
    r"(?P<favorite>.+?)\s{2,}"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"(?P<underdog>.+?)\s+"
    r"\d+\s+"
    r"\d+%\s+"
    r"(?P<regular_total>\d+\.\d{2})\s+"
    r"(?P<experimental_total>\d+\.\d{2})\s+"
    r"average=\s*(?P<average>\d+(?:\.\d+)?)\s*$"
)


RE_2025 = re.compile(
    r"^\s*\d+\s+"
    r"(?:(?P<neutral>[NC])\s+)?"
    r"(?P<favorite_loc>@\s+)?"
    r"(?P<favorite>.+?)\s{2,}"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"(?P<underdog>.+?)\s+"
    r"\d+\s+"
    r"\d+%\s+"
    r"(?P<home_points>\d+\.\d{2})\s+"
    r"(?P<away_points>\d+\.\d{2})\s+"
    r"(?P<total>\d+\.\d{2})\s*$"
)




# Early-2025 format used before Sagarin added displayed
# favorite/underdog projected-point columns.
#
# Example:
# @ Charlotte  0.69 0.05 0.80 0.22 -2.62  Rice  108 52% 41.67
#
# Keep only the published total. Do not manufacture team points.
RE_2025_EARLY = re.compile(
    r"^\s*"
    r"(?:(?P<neutral>[NC])\s+)?"
    r"(?P<favorite_loc>@\s+)?"
    r"(?P<favorite>.+?)\s{2,}"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"-?\d+\.\d{2}\s+"
    r"(?P<underdog>.+?)\s+"
    r"\d+\s+"
    r"\d+%\s+"
    r"(?P<total>\d+\.\d{2})\s*$"
)

def decode(raw: bytes) -> tuple[bytes, str]:
    head = raw[:1000].lower()

    if (
        b"<html" in head
        or b"<pre" in head
        or b"<!doctype" in head
    ):
        return raw, "plain"

    if raw[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(raw), "gzip"
        except Exception:
            pass

    for wbits, label in (
        (zlib.MAX_WBITS, "zlib"),
        (-zlib.MAX_WBITS, "raw-deflate"),
        (zlib.MAX_WBITS | 16, "gzip-zlib"),
    ):
        try:
            return zlib.decompress(raw, wbits), label
        except Exception:
            pass

    return raw, "unknown"


def fetch(ts: str, original: str) -> tuple[Path, str]:
    CACHE.mkdir(parents=True, exist_ok=True)

    out = CACHE / f"{ts}.html"

    if out.exists() and out.stat().st_size > 1000:
        return out, "cache"

    url = f"https://web.archive.org/web/{ts}id_/{original}"

    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Encoding": "gzip, deflate",
        },
    )

    last_exc = None

    for attempt in range(1, 7):
        try:
            with urlopen(req, timeout=90) as r:
                raw = r.read()

            decoded, encoding = decode(raw)
            out.write_bytes(decoded)

            # Be deliberately gentle with Wayback.
            time.sleep(2.0)

            return out, encoding

        except Exception as exc:
            last_exc = exc

            wait = min(60, 5 * attempt)

            print(
                f"    fetch attempt {attempt}/6 failed: "
                f"{type(exc).__name__}: {exc}; "
                f"sleeping {wait}s",
                flush=True,
            )

            time.sleep(wait)

    raise last_exc


def clean_team(name: str) -> str:
    return name.strip()


def parse_old(text: str, ts: str, source_url: str) -> list[dict]:
    marker = 'name="Predictions_with_Totals"'

    if marker not in text:
        return []

    start = text.index(marker)

    section = text[start:]

    if "EIGENVECTOR Analysis" in section:
        section = section[:section.index("EIGENVECTOR Analysis")]

    rows = []

    for line in section.splitlines():
        m = OLD_RE.match(line)

        if not m:
            continue

        rows.append({
            "season": ts[:4],
            "snapshot_timestamp": ts,
            "favorite_raw": clean_team(m["favorite"]),
            "underdog_raw": clean_team(m["underdog"]),
            "sagarin_total": float(m["total"]),
            "regular_total": float(m["total"]),
            "experimental_total": "",
            "published_average": "",
            "home_points": "",
            "away_points": "",
            "format": "regular_total_only",
            "source_url": source_url,
        })

    return rows


def parse_2024(text: str, ts: str, source_url: str) -> list[dict]:
    marker = 'name="Predictions_with_Totals_and_Moneylines"'

    if marker not in text:
        return []

    start = text.index(marker)
    section = text[start:]

    # Only parse the regular-method table.
    # Do NOT parse the duplicated experimental section below it.
    if "EXPERIMENTAL NUMBERS based on HOME-AWAY" in section:
        section = section[
            :section.index(
                "EXPERIMENTAL NUMBERS based on HOME-AWAY"
            )
        ]

    rows = []

    for line in section.splitlines():
        m = RE_2024.match(line)

        if not m:
            continue

        regular = float(m["regular_total"])
        experimental = float(m["experimental_total"])
        average = float(m["average"])

        rows.append({
            "season": ts[:4],
            "snapshot_timestamp": ts,
            "favorite_raw": clean_team(m["favorite"]),
            "underdog_raw": clean_team(m["underdog"]),
            # PRIMARY VALUE FOR HISTORICAL CONSENSUS:
            "sagarin_total": regular,
            "regular_total": regular,
            "experimental_total": experimental,
            "published_average": average,
            "home_points": "",
            "away_points": "",
            "format": "regular_plus_experimental",
            "source_url": source_url,
        })

    return rows


def parse_2025(text: str, ts: str, source_url: str) -> list[dict]:
    marker = 'name="Predictions_with_Totals_and_Moneylines"'

    if marker not in text:
        return []

    start = text.index(marker)
    section = text[start:]

    if "EIGENVECTOR Analysis" in section:
        section = section[:section.index("EIGENVECTOR Analysis")]

    rows = []

    for line in section.splitlines():
        # Newer 2025 format with displayed projected team points.
        m = RE_2025.match(line)

        if m:
            home = float(m["home_points"])
            away = float(m["away_points"])
            total = float(m["total"])

            rows.append({
                "season": ts[:4],
                "snapshot_timestamp": ts,
                "favorite_raw": clean_team(m["favorite"]),
                "underdog_raw": clean_team(m["underdog"]),
                "sagarin_total": total,
                "regular_total": total,
                "experimental_total": "",
                "published_average": "",
                "home_points": home,
                "away_points": away,
                "format": "home_away_total",
                "source_url": source_url,
            })
            continue

        # Earlier 2025 format:
        # published TOTAL exists, but no displayed fav/dog point columns.
        m = RE_2025_EARLY.match(line)

        if not m:
            continue

        total = float(m["total"])

        # Early 2025 included a blanket preseason/default total
        # of 52.12 across essentially the full board. Preserve it
        # in the archive, but flag it distinctly so downstream
        # research can exclude it from individualized projections.
        early_format = (
            "preseason_default_total_2025"
            if abs(total - 52.12) < 1e-9
            else "regular_total_only_2025"
        )

        rows.append({
            "season": ts[:4],
            "snapshot_timestamp": ts,
            "favorite_raw": clean_team(m["favorite"]),
            "underdog_raw": clean_team(m["underdog"]),
            "sagarin_total": total,
            "regular_total": total,
            "experimental_total": "",
            "published_average": "",
            "home_points": "",
            "away_points": "",
            "format": early_format,
            "source_url": source_url,
        })

    return rows

def parse_snapshot(path: Path, ts: str, original: str) -> list[dict]:
    text = path.read_text(errors="ignore")

    source_url = (
        f"https://web.archive.org/web/{ts}id_/{original}"
    )

    season = int(ts[:4])

    if season <= 2023:
        return parse_old(text, ts, source_url)

    if season == 2024:
        return parse_2024(text, ts, source_url)

    return parse_2025(text, ts, source_url)


def main():
    raw = json.loads(CAPTURES.read_text())
    captures = raw[1:]

    all_rows = []
    failures = []
    decode_counts = Counter()

    for i, capture in enumerate(captures, start=1):
        ts = capture[0]
        original = capture[1]

        print(
            f"[{i:3d}/{len(captures)}] {ts}",
            flush=True,
        )

        try:
            path, encoding = fetch(ts, original)
            decode_counts[encoding] += 1

            rows = parse_snapshot(path, ts, original)

            if not rows:
                failures.append({
                    "timestamp": ts,
                    "reason": "no_rows",
                })
                continue

            all_rows.extend(rows)

        except Exception as exc:
            failures.append({
                "timestamp": ts,
                "reason": f"{type(exc).__name__}: {exc}",
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "season",
        "snapshot_timestamp",
        "favorite_raw",
        "underdog_raw",
        "sagarin_total",
        "regular_total",
        "experimental_total",
        "published_average",
        "home_points",
        "away_points",
        "format",
        "source_url",
    ]

    with OUT.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fields,
        )
        writer.writeheader()
        writer.writerows(all_rows)

    # Validation audits
    validation_2024 = []
    validation_2025 = []

    for row in all_rows:
        if row["format"] == "regular_plus_experimental":
            expected = (
                float(row["regular_total"])
                + float(row["experimental_total"])
            ) / 2

            diff = abs(
                expected
                - float(row["published_average"])
            )

            if diff > 0.001:
                validation_2024.append({
                    "timestamp": row["snapshot_timestamp"],
                    "favorite": row["favorite_raw"],
                    "underdog": row["underdog_raw"],
                    "diff": diff,
                })

        if row["format"] == "home_away_total":
            expected = (
                float(row["home_points"])
                + float(row["away_points"])
            )

            diff = abs(
                expected
                - float(row["sagarin_total"])
            )

            # Sagarin can differ by .01 from displayed rounding.
            if diff > 0.011:
                validation_2025.append({
                    "timestamp": row["snapshot_timestamp"],
                    "favorite": row["favorite_raw"],
                    "underdog": row["underdog_raw"],
                    "diff": diff,
                })

    season_summary = {}

    for season in ["2021", "2022", "2023", "2024", "2025"]:
        rows = [
            r for r in all_rows
            if r["season"] == season
        ]

        season_summary[season] = {
            "rows": len(rows),
            "snapshots_with_rows": len({
                r["snapshot_timestamp"]
                for r in rows
            }),
            "min_total": (
                min(float(r["sagarin_total"]) for r in rows)
                if rows else None
            ),
            "max_total": (
                max(float(r["sagarin_total"]) for r in rows)
                if rows else None
            ),
        }

    audit = {
        "captures_attempted": len(captures),
        "rows_total": len(all_rows),
        "decode_counts": dict(decode_counts),
        "season_summary": season_summary,
        "2024_average_validation_failures": validation_2024,
        "2025_score_sum_validation_failures": validation_2025,
        "failures": failures,
    }

    AUDIT.write_text(
        json.dumps(audit, indent=2) + "\n"
    )

    print()
    print("===== SAGARIN TOTAL ARCHIVE =====")
    print("captures attempted:", len(captures))
    print("rows:", len(all_rows))
    print("decode counts:", dict(decode_counts))

    print()
    print("===== BY SEASON =====")

    for season, info in season_summary.items():
        print(season, info)

    print()
    print(
        "2024 average validation failures:",
        len(validation_2024),
    )
    print(
        "2025 home+away validation failures:",
        len(validation_2025),
    )

    print()
    print("captures with failures:", len(failures))

    for failure in failures[:20]:
        print(failure)

    print()
    print("wrote:", OUT)
    print("audit:", AUDIT)


if __name__ == "__main__":
    main()
