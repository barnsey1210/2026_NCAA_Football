#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import json
import re

INDEX = Path("index.html")
MOVES = Path("daily_market_movement_report.csv")

if not INDEX.exists():
    raise SystemExit("index.html not found")
if not MOVES.exists():
    raise SystemExit("daily_market_movement_report.csv not found")

def clean_team(x):
    return str(x or "").strip()

def clean_book(x):
    return str(x or "").strip()

def fmt_num(x):
    try:
        n = float(x)
        if n.is_integer():
            return str(int(n))
        return str(n)
    except Exception:
        return str(x)

def fmt_odds(x):
    try:
        n = int(round(float(x)))
        return f"+{n}" if n > 0 else str(n)
    except Exception:
        return str(x)

def row_time_key(r):
    val = str(r.get("snapshot_latest") or r.get("move_date") or "")
    dt = pd.to_datetime(val, errors="coerce", utc=True)
    if pd.isna(dt):
        dt = pd.to_datetime(str(r.get("move_date") or ""), errors="coerce", utc=True)
    return dt

df = pd.read_csv(MOVES)

needed = ["market", "team", "book", "field", "previous", "latest", "snapshot_prev", "snapshot_latest", "move_date", "summary"]
for c in needed:
    if c not in df.columns:
        df[c] = ""

# Keep Win Total and futures/conference moves, but sort newest first.
df["team"] = df["team"].map(clean_team)
df["book"] = df["book"].map(clean_book)
df["sort_ts"] = df.apply(row_time_key, axis=1)

groups = []
group_cols = ["market", "team", "book", "snapshot_prev", "snapshot_latest", "move_date"]

for key, g in df.groupby(group_cols, dropna=False, sort=False):
    market, team, book, snapshot_prev, snapshot_latest, move_date = key
    market = str(market or "")
    team = str(team or "")
    book = str(book or "")
    if not team:
        continue

    fields = {str(r["field"]): r for _, r in g.iterrows()}

    if market == "Win Total":
        line_row = None
        over_row = None
        under_row = None

        for field, r in fields.items():
            f = str(field)
            if f == "Win Total":
                line_row = r
            elif f.lower().startswith("over"):
                over_row = r
            elif f.lower().startswith("under"):
                under_row = r

        latest_line = ""
        if line_row is not None:
            latest_line = fmt_num(line_row["latest"])
        elif over_row is not None:
            m = re.search(r"Over\s+([0-9.]+)", str(over_row["field"]))
            latest_line = m.group(1) if m else ""
        elif under_row is not None:
            m = re.search(r"Under\s+([0-9.]+)", str(under_row["field"]))
            latest_line = m.group(1) if m else ""

        title = f"{team} {latest_line} win total moved at {book}".replace("  ", " ").strip()

        parts = []
        if line_row is not None:
            parts.append(f"line {fmt_num(line_row['previous'])} → {fmt_num(line_row['latest'])}")

        if over_row is not None:
            parts.append(f"Over {latest_line}: {fmt_odds(over_row['previous'])} → {fmt_odds(over_row['latest'])}")

        if under_row is not None:
            parts.append(f"Under {latest_line}: {fmt_odds(under_row['previous'])} → {fmt_odds(under_row['latest'])}")

        when = str(snapshot_latest or move_date or "")
        reason = "; ".join(parts)
        if when:
            reason += f" on {when}."

        max_change = 0
        for _, r in g.iterrows():
            try:
                max_change = max(max_change, abs(float(r.get("change", 0))))
            except Exception:
                pass

        groups.append({
            "title": title,
            "team": team,
            "book": book,
            "reason": reason,
            "score": max_change,
            "_sort_ts": row_time_key(g.iloc[0]).isoformat() if pd.notna(row_time_key(g.iloc[0])) else "",
        })

    else:
        # Futures / title odds rows.
        r = g.iloc[0]
        title = str(r.get("summary") or f"{team} {market} moved").strip()
        groups.append({
            "title": title,
            "team": team,
            "book": book,
            "reason": str(r.get("summary") or ""),
            "score": r.get("change", ""),
            "_sort_ts": row_time_key(r).isoformat() if pd.notna(row_time_key(r)) else "",
        })

# Newest first, then bigger score.
def sort_key(r):
    return (str(r.get("_sort_ts") or ""), float(r.get("score") or 0) if str(r.get("score") or "").replace(".","",1).replace("-","",1).isdigit() else 0)

groups = sorted(groups, key=sort_key, reverse=True)

# Remove helper sort field before embedding.
for r in groups:
    r.pop("_sort_ts", None)

s = INDEX.read_text(errors="ignore")
key = '"top_market_moves":'
idx = s.find(key)
if idx == -1:
    raise SystemExit("top_market_moves not found in index.html")

start = s.find("[", idx)
if start == -1:
    raise SystemExit("top_market_moves array start not found")

depth = 0
end = None
for i in range(start, len(s)):
    if s[i] == "[":
        depth += 1
    elif s[i] == "]":
        depth -= 1
        if depth == 0:
            end = i + 1
            break

if end is None:
    raise SystemExit("top_market_moves array end not found")

new_json = json.dumps(groups, separators=(",", ":"))
s = s[:start] + new_json + s[end:]
INDEX.write_text(s)

print(f"embedded all top_market_moves: {len(groups)}")
print("first 10:")
for r in groups[:10]:
    print("-", r.get("team"), "|", r.get("title"), "|", r.get("reason"))
