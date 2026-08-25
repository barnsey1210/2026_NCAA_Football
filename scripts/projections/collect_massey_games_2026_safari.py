#!/usr/bin/env python3

import argparse
import json
import subprocess
import time
from pathlib import Path

import pandas as pd


ROOT = Path(".")
PRESEASON_DB = ROOT / "data/snapshots/preseason/preseason_db.json"

OUTDIR = (
    ROOT
    / "data/ratings/external_sources/massey/browser_raw_2026"
)

PROGRESS = (
    ROOT
    / "data/research/historical_totals/massey/"
    "massey_2026_safari_collection_progress.csv"
)

INVENTORY = (
    ROOT
    / "data/research/historical_totals/massey/"
)


def run_applescript(script: str, timeout: int = 45) -> str:
    result = subprocess.run(
        ["osascript", "-e", script], capture_output=True, text=True, timeout=timeout
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def create_safari_worker() -> int:
    """Create and identify one collector-owned Safari window."""
    script = '''
tell application "Safari"
    set priorIds to id of every window
    make new document with properties {URL:"about:blank"}
    repeat with candidate in every window
        if (id of candidate) is not in priorIds then return id of candidate
    end repeat
    error "unable to identify collector-owned Safari window"
end tell
'''
    return int(run_applescript(script))


def close_safari_worker(worker_id: int) -> None:
    """Best-effort cleanup restricted to the collector-owned window ID."""
    script = f'''
tell application "Safari"
    try
        close window id {int(worker_id)}
    end try
end tell
'''
    try:
        run_applescript(script, timeout=15)
    except Exception as exc:
        print(f"warning: Safari worker cleanup failed: {exc}")


def safari_capture(date_str: str, worker_id: int, wait_seconds: int = 6) -> str:
    url_date = date_str.replace("-", "")
    url = f"https://masseyratings.com/cf/fbs/games?dt={url_date}"

    applescript = f'''
tell application "Safari"
    set workerWindow to window id {int(worker_id)}
    set URL of current tab of workerWindow to "{url}"

    delay {wait_seconds}

    repeat 20 times
        try
            set rs to do JavaScript "document.readyState" in current tab of workerWindow
            if rs is "complete" then exit repeat
        end try
        delay 1
    end repeat

    delay 2

    return do JavaScript "document.body.innerText" in current tab of workerWindow
end tell
'''
    return run_applescript(applescript)


def valid_page(text: str) -> bool:
    required = ["Pred", "Pwin", "MOV", "Total"]

    return (
        len(text) > 500
        and all(x in text for x in required)
    )


def build_dates():
    with open(PRESEASON_DB, "r", encoding="utf-8") as f:
        db = json.load(f)

    return sorted({
        str(g.get("date"))
        for g in db.get("games", [])
        if g.get("date")
    })

def load_progress():
    if (
        PROGRESS.exists()
        and PROGRESS.stat().st_size > 0
    ):
        try:
            return pd.read_csv(
                PROGRESS,
                low_memory=False,
            ).to_dict("records")
        except Exception:
            pass

    return []


def save_progress(rows):
    PROGRESS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(rows).to_csv(
        PROGRESS,
        index=False,
    )


def main():
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--seasons",
        nargs="+",
        type=int,
        default=[2021, 2022, 2023, 2024, 2025],
    )

    ap.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    ap.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Only collect dates on or after YYYY-MM-DD",
    )

    ap.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="Only collect dates on or before YYYY-MM-DD",
    )

    ap.add_argument(
        "--sleep",
        type=float,
        default=2.5,
    )

    ap.add_argument(
        "--force",
        action="store_true",
    )

    args = ap.parse_args()

    OUTDIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dates = build_dates()

    if args.start_date:
        dates = [
            d for d in dates
            if d >= args.start_date
        ]

    if args.end_date:
        dates = [
            d for d in dates
            if d <= args.end_date
        ]

    if args.limit:
        dates = dates[:args.limit]

    progress = load_progress()

    completed = {
        str(r.get("date"))
        for r in progress
        if str(r.get("status")) == "OK"
    }

    print("=" * 100)
    print("MASSEY 2026 GAME SAFARI COLLECTOR")
    print("=" * 100)
    print("season: 2026")
    print("dates:", len(dates))
    print("already completed:", len(completed))
    print("output:", OUTDIR)



    worker_id = create_safari_worker()
    try:
      for n, date_str in enumerate(dates, 1):

        key = date_str

        outfile = OUTDIR / (
            f"massey_games_{date_str.replace('-', '')}.txt"
        )

        if (
            not args.force
            and key in completed
            and outfile.exists()
            and outfile.stat().st_size > 500
        ):
            print(
                f"[{n}/{len(dates)}] {date_str} SKIP existing"
            )
            continue

        print(
            f"[{n}/{len(dates)}] {date_str} loading...",
            flush=True,
        )

        status = "ERROR"
        chars = 0
        error = ""

        for attempt in range(
            1,
            4,
        ):
            try:
                text = safari_capture(date_str, worker_id)

                chars = len(text)

                if not valid_page(
                    text
                ):
                    raise RuntimeError(
                        f"page failed validation; chars={chars}"
                    )

                outfile.write_text(
                    text,
                    encoding="utf-8",
                )

                status = "OK"
                error = ""

                print(
                    f"    OK chars={chars} "
                    f"file={outfile.name}"
                )

                break

            except Exception as exc:
                error = str(exc)

                print(
                    f"    attempt {attempt} failed: "
                    f"{error[:200]}"
                )

                if attempt < 3:
                    time.sleep(5)

        progress.append({
            "date": date_str,
            "status": status,
            "chars": chars,
            "file": str(outfile)
                if status == "OK"
                else "",
            "error": error,
            "collected_at":
                pd.Timestamp.utcnow().isoformat(),
        })

        save_progress(
            progress
        )

        time.sleep(args.sleep)
    finally:
        close_safari_worker(worker_id)

    print()
    print("=" * 100)
    print("DONE")
    print("=" * 100)

    p = pd.DataFrame(
        progress
    )

    if len(p):
        latest = (
            p.sort_values(
                "collected_at"
            )
            .drop_duplicates(
                ["date"],
                keep="last",
            )
        )

        print(
            latest["status"]
            .value_counts(
                dropna=False
            )
            .to_string()
        )

        print()
        print("completed boards:", int(
            latest["status"]
            .eq("OK")
            .sum()
        ))

        print("expected dates:", len(dates))


if __name__ == "__main__":
    main()
