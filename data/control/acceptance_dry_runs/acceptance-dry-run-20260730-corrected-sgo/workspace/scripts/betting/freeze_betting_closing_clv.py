#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import pandas as pd

ROOT = Path.cwd()
BETS = ROOT / "data" / "bets" / "bets_enriched.csv"
DASH = ROOT / "data" / "bets" / "betting_dashboard.json"
FREEZE = ROOT / "data" / "bets" / "bet_closing_clv.csv"
AUDIT = ROOT / "data" / "bets" / "bet_closing_clv_audit.csv"

GAME_LINE_FILES = [
    ROOT / "data" / "odds" / "actionnetwork_ncaaf_game_lines_2026.csv",
    ROOT / "data" / "odds" / "action_ncaaf_game_lines_2026.csv",
    ROOT / "data" / "odds" / "theodds_ncaaf_lines_2026.csv",
]

if not BETS.exists():
    raise SystemExit("Missing data/bets/bets_enriched.csv")
if not DASH.exists():
    raise SystemExit("Missing data/bets/betting_dashboard.json")

def clean_key(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    s = str(x).strip().lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

TEAM_ALIASES = {
    "miami oh": "miami oh",
    "miami ohio": "miami oh",
    "miami o": "miami oh",
    "miami oh redhawks": "miami oh",
    "duke blue devils": "duke",
    "duke": "duke",
}

def team_key(x):
    k = clean_key(x)
    return TEAM_ALIASES.get(k, k)

def parse_dt(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    s = str(x).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def parse_num(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    try:
        n = float(x)
        if not math.isfinite(n):
            return None
        return n
    except Exception:
        return None

def bet_id(row):
    parts = [
        row.get("Date"),
        row.get("Account"),
        row.get("Bet Description"),
        row.get("Sportsbook"),
        row.get("Bet"),
        row.get("Bet Type"),
        row.get("bet_line"),
        row.get("bet_price"),
        row.get("stake"),
    ]
    raw = "|".join("" if pd.isna(x) else str(x).strip().lower() for x in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

def is_game_bet(row):
    desc = clean_key(row.get("Bet Description"))
    typ = clean_key(row.get("Bet Type"))
    if "win total" in desc or "conf title" in desc or typ == "future":
        return False
    if "week" in desc:
        return True
    if typ in {"side", "spread", "game total"}:
        return True
    return False

def load_game_kickoffs():
    rows = []
    for path in GAME_LINE_FILES:
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        for _, r in df.iterrows():
            dt = parse_dt(r.get("commence_time") or r.get("date"))
            if not dt:
                continue
            away = r.get("away_team")
            home = r.get("home_team")
            rows.append({
                "source": str(path.relative_to(ROOT)),
                "game_id": r.get("game_id"),
                "away_team": away,
                "home_team": home,
                "away_key": team_key(away),
                "home_key": team_key(home),
                "week": parse_num(r.get("week")),
                "kickoff_utc": dt.isoformat(),
            })
    # de-dupe
    seen = set()
    out = []
    for r in rows:
        key = (r["source"], r["game_id"], r["away_key"], r["home_key"], r["kickoff_utc"])
        if key not in seen:
            out.append(r)
            seen.add(key)
    return out

def find_kickoff(row, game_rows):
    tk = team_key(row.get("team_guess"))
    desc = clean_key(row.get("Bet Description"))

    preferred_week = None
    m = re.search(r"week\s+(\d+)", desc)
    if m:
        preferred_week = float(m.group(1))

    candidates = [g for g in game_rows if tk and (g["away_key"] == tk or g["home_key"] == tk)]

    if preferred_week is not None:
        wk = [g for g in candidates if g.get("week") == preferred_week]
        if wk:
            candidates = wk

    if not candidates:
        return None

    candidates = sorted(candidates, key=lambda g: g["kickoff_utc"])
    return candidates[0]

def clean_json_obj(obj):
    if obj is None:
        return None
    try:
        if pd.isna(obj):
            return None
    except Exception:
        pass
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {str(k): clean_json_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_json_obj(v) for v in obj]
    return obj

df = pd.read_csv(BETS)
dash = json.loads(DASH.read_text())

for c in [
    "bet_id",
    "closing_clv_frozen",
    "closing_frozen_at",
    "closing_kickoff_utc",
    "closing_game",
    "closing_market_source",
    "closing_market_book",
    "closing_market_line",
    "closing_market_price",
    "closing_line_clv",
    "closing_price_clv_pp",
    "closing_clv_pct",
    "closing_ev_dollars",
    "closing_ev_pct",
]:
    if c not in df.columns:
        df[c] = None

df["bet_id"] = df.apply(bet_id, axis=1)

if FREEZE.exists():
    frozen = pd.read_csv(FREEZE)
else:
    frozen = pd.DataFrame(columns=[
        "bet_id",
        "frozen_at",
        "kickoff_utc",
        "game",
        "market_source",
        "market_book",
        "market_line",
        "market_price",
        "line_clv",
        "price_clv_pp",
        "clv_pct",
        "ev_dollars",
        "ev_pct",
    ])

frozen_ids = set(frozen["bet_id"].astype(str)) if not frozen.empty else set()
game_rows = load_game_kickoffs()
now = datetime.now(timezone.utc)

audit_rows = []
new_freezes = []

for idx, row in df.iterrows():
    bid = str(row.get("bet_id"))
    game_bet = is_game_bet(row)

    if not game_bet:
        continue

    kickoff = find_kickoff(row, game_rows)
    kickoff_dt = parse_dt(kickoff["kickoff_utc"]) if kickoff else None

    audit_rows.append({
        "bet_id": bid,
        "bet": row.get("Bet"),
        "team": row.get("team_guess"),
        "is_game_bet": game_bet,
        "kickoff_found": kickoff is not None,
        "kickoff_utc": kickoff["kickoff_utc"] if kickoff else None,
        "now_utc": now.isoformat(),
        "already_frozen": bid in frozen_ids,
        "current_market_match": row.get("current_market_match"),
    })

    if bid in frozen_ids:
        continue

    if not kickoff_dt or now < kickoff_dt:
        continue

    if str(row.get("current_market_match")).lower() != "true":
        continue

    game = f"{kickoff.get('away_team')} at {kickoff.get('home_team')}" if kickoff else row.get("current_market_note")

    new_freezes.append({
        "bet_id": bid,
        "frozen_at": now.replace(microsecond=0).isoformat(),
        "kickoff_utc": kickoff_dt.isoformat(),
        "game": game,
        "market_source": row.get("current_market_source"),
        "market_book": row.get("current_market_book"),
        "market_line": row.get("current_market_line"),
        "market_price": row.get("current_market_price"),
        "line_clv": row.get("line_clv_current"),
        "price_clv_pp": row.get("price_clv_current_pp"),
        "clv_pct": row.get("clv_pct_current"),
        "ev_dollars": row.get("ev_current_dollars"),
        "ev_pct": row.get("ev_current_pct"),
    })

if new_freezes:
    frozen = pd.concat([frozen, pd.DataFrame(new_freezes)], ignore_index=True)
    frozen = frozen.drop_duplicates(subset=["bet_id"], keep="last")

# Apply frozen closing values back onto bets.
if not frozen.empty:
    f_map = {str(r["bet_id"]): r for _, r in frozen.iterrows()}
    for idx, row in df.iterrows():
        bid = str(row.get("bet_id"))
        if bid not in f_map:
            continue
        fr = f_map[bid]
        df.at[idx, "closing_clv_frozen"] = True
        df.at[idx, "closing_frozen_at"] = fr.get("frozen_at")
        df.at[idx, "closing_kickoff_utc"] = fr.get("kickoff_utc")
        df.at[idx, "closing_game"] = fr.get("game")
        df.at[idx, "closing_market_source"] = fr.get("market_source")
        df.at[idx, "closing_market_book"] = fr.get("market_book")
        df.at[idx, "closing_market_line"] = fr.get("market_line")
        df.at[idx, "closing_market_price"] = fr.get("market_price")
        df.at[idx, "closing_line_clv"] = fr.get("line_clv")
        df.at[idx, "closing_price_clv_pp"] = fr.get("price_clv_pp")
        df.at[idx, "closing_clv_pct"] = fr.get("clv_pct")
        df.at[idx, "closing_ev_dollars"] = fr.get("ev_dollars")
        df.at[idx, "closing_ev_pct"] = fr.get("ev_pct")

        # For frozen game bets, display/evaluate using closing market values.
        df.at[idx, "current_market_book"] = fr.get("market_book")
        df.at[idx, "current_market_line"] = fr.get("market_line")
        df.at[idx, "current_market_price"] = fr.get("market_price")
        df.at[idx, "line_clv_current"] = fr.get("line_clv")
        df.at[idx, "price_clv_current_pp"] = fr.get("price_clv_pp")
        df.at[idx, "clv_pct_current"] = fr.get("clv_pct")
        df.at[idx, "ev_current_dollars"] = fr.get("ev_dollars")
        df.at[idx, "ev_current_pct"] = fr.get("ev_pct")

# Rebuild dashboard open rows and summary fields.
matched_df = df[df["current_market_match"].astype(str).str.lower().eq("true")].copy()
price_vals = pd.to_numeric(matched_df["price_clv_current_pp"], errors="coerce").dropna()
line_vals = pd.to_numeric(matched_df["line_clv_current"], errors="coerce").dropna()
ev_dollar_vals = pd.to_numeric(matched_df["ev_current_dollars"], errors="coerce").dropna()
ev_pct_vals = pd.to_numeric(matched_df["ev_current_pct"], errors="coerce").dropna()

positive_mask = (
    (pd.to_numeric(matched_df["price_clv_current_pp"], errors="coerce").fillna(0) > 0)
    | (pd.to_numeric(matched_df["line_clv_current"], errors="coerce").fillna(0) > 0)
)

summary = dash.get("summary", {})
summary["current_clv_matched"] = int(len(matched_df))
summary["current_clv_positive"] = int(positive_mask.sum()) if len(matched_df) else 0
summary["pct_bets_beating_current_clv"] = round(summary["current_clv_positive"] / len(matched_df), 4) if len(matched_df) else None
summary["avg_line_clv_current"] = round(float(line_vals.mean()), 3) if len(line_vals) else None
summary["avg_price_clv_current_pp"] = round(float(price_vals.mean()), 3) if len(price_vals) else None
summary["avg_ev_current_dollars"] = round(float(ev_dollar_vals.mean()), 2) if len(ev_dollar_vals) else None
summary["total_ev_current_dollars"] = round(float(ev_dollar_vals.sum()), 2) if len(ev_dollar_vals) else None
summary["avg_ev_current_pct"] = round(float(ev_pct_vals.mean()), 4) if len(ev_pct_vals) else None
summary["closing_clv_frozen_count"] = int(df["closing_clv_frozen"].astype(str).str.lower().eq("true").sum())
summary["closing_clv_new_freezes"] = int(len(new_freezes))

dash["summary"] = summary
dash["open_bets"] = df[df["status"].fillna("").astype(str).str.lower().eq("open")].where(pd.notna(df), None).to_dict("records")
dash["updated_at"] = datetime.now().replace(microsecond=0).isoformat()

df.to_csv(BETS, index=False)
frozen.to_csv(FREEZE, index=False)
pd.DataFrame(audit_rows).to_csv(AUDIT, index=False)

dash = clean_json_obj(dash)
DASH.write_text(json.dumps(dash, indent=2, ensure_ascii=False, allow_nan=False))

print("wrote:", BETS)
print("wrote:", FREEZE)
print("wrote:", AUDIT)
print("game rows:", len(game_rows))
print("new freezes:", len(new_freezes))
print("total frozen:", summary["closing_clv_frozen_count"])
print("matched:", summary["current_clv_matched"])
print("total EV:", summary["total_ev_current_dollars"])
