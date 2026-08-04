#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

LINKS = Path("data/rosters/ourlads_depth_chart_links_clean.csv")
AUDIT = Path("data/audit/ourlads_batch_import_audit.csv")

def main():
    if not LINKS.exists():
        raise SystemExit(f"Missing {LINKS}. Run clean_ourlads_depth_chart_links.py first.")

    limit = None
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])

    links = pd.read_csv(LINKS)

    links = links.dropna(subset=["team_guess", "url"]).copy()
    links = links[~links["team_guess"].astype(str).str.contains("FCS|Small College|Go Ad Free", case=False, na=False)].copy()
    links = links.drop_duplicates(subset=["team_guess"], keep="last").copy()

    if limit:
        links = links.head(limit).copy()

    rows = []
    start_all = time.time()

    for i, r in links.iterrows():
        team = str(r["team_guess"]).strip()
        url = str(r["url"]).strip()
        started = datetime.now(timezone.utc).isoformat()
        t0 = time.time()

        print("\n" + "=" * 90)
        print(f"{team} | {url}")

        env = os.environ.copy()
        env["OURLADS_QUIET"] = "1"

        proc = subprocess.run(
            [
                "python3",
                "scripts/injuries/pull_ourlads_team_depth_chart.py",
                team,
                url,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        seconds = round(time.time() - t0, 2)
        ok = proc.returncode == 0

        if ok:
            summary = "\n".join([x for x in proc.stdout.splitlines() if x.startswith(("team:", "rows parsed:", "updated:"))])
            print(summary)
        else:
            print("FAILED")
            print(proc.stdout[-1000:])
            print(proc.stderr[-1000:])

        rows.append({
            "started_at": started,
            "team": team,
            "url": url,
            "ok": ok,
            "returncode": proc.returncode,
            "seconds": seconds,
            "stdout_tail": proc.stdout[-1000:],
            "stderr_tail": proc.stderr[-1000:],
        })

        pd.DataFrame(rows).to_csv(AUDIT, index=False)
        time.sleep(0.4)

    elapsed = round(time.time() - start_all, 2)
    audit = pd.DataFrame(rows)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(AUDIT, index=False)

    print("\n" + "=" * 90)
    print("Batch complete")
    print("attempted:", len(audit))
    print("ok:", int(audit["ok"].sum()) if not audit.empty else 0)
    print("failed:", int((~audit["ok"]).sum()) if not audit.empty else 0)
    print("seconds:", elapsed)
    print("wrote:", AUDIT)

    if not audit.empty and (~audit["ok"]).any():
        print("\nFAILED TEAMS")
        print(audit[~audit["ok"]][["team", "url", "returncode"]].to_string(index=False))

if __name__ == "__main__":
    main()
