#!/usr/bin/env python3
from pathlib import Path
import sys
import re
import json
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.signals.build_returning_production_early_season_signals import (
    cfbd_get,
    flatten_records,
    extract_lines,
    standardize_games,
    load_2026_schedule,
    role_from_home_edge,
)

ROOT = Path(".")
RP_HIST = ROOT / "data/import/sp_plus/sp_plus_returning_production_2023_2025.csv"
HTML = ROOT / "index.html"

OUT_GAMES = ROOT / "data/research/returning_production_spplus_early_season_games.csv"
OUT_SUMMARY = ROOT / "data/research/returning_production_spplus_early_season_summary.csv"
OUT_SIGNALS = ROOT / "data/signals/returning_production_early_season_signals.csv"
OUT_MASTER = ROOT / "data/signals/game_betting_signals.csv"
OUT_AUDIT = ROOT / "data/audit/returning_production_spplus_signals_audit.csv"

YEARS = [2023, 2024, 2025]
EARLY_WEEKS = [0, 1, 2, 3, 4]
HIGH_Q = 0.75
LOW_Q = 0.25

def norm_simple(x):
    return re.sub(r"[^a-z0-9]+", "", str(x or "").lower())

ALIASES = {
    "floridast": "floridastate",
    "fla": "florida",
    "fa": "fau",
    "bostoncoll": "bostoncollege",
    "southalabama": "southalabama",
    "salabama": "southalabama",
    "northtexas": "northtexas",
    "ntexas": "northtexas",
    "coastalcaro": "coastalcarolina",
    "latech": "louisianatech",
    "vatech": "virginiatech",
    "miamioh": "miamioh",
    "miamiohio": "miamioh",
    "miamioh": "miamioh",
    "miamifla": "miamifl",
    "miami": "miamifl",
    "northcarolina": "northcarolina",
    "ncarolina": "northcarolina",
    "ohiost": "ohiostate",
    "boisest": "boisestate",
    "gtech": "georgiatech",
    "gatech": "georgiatech",
    "georgiatech": "georgiatech",
    "oregonst": "oregonstate",
    "pennst": "pennstate",
    "newmexicost": "newmexicostate",
    "nmsu": "newmexicostate",
    "jaxvillest": "jacksonvillestate",
    "jvillest": "jacksonvillestate",
    "jamesmadison": "jamesmadison",
    "jmu": "jamesmadison",
    "centralmich": "centralmichigan",
    "cmu": "centralmichigan",
    "easternmich": "easternmichigan",
    "eastmich": "easternmichigan",
    "emu": "easternmichigan",
    "westernmich": "westernmichigan",
    "westmich": "westernmichigan",
    "wmu": "westernmichigan",
    "bowlinggreen": "bowlinggreen",
    "bgsu": "bowlinggreen",
    "westvirginia": "westvirginia",
    "wvirginia": "westvirginia",
    "westernkentucky": "westernkentucky",
    "westkent": "westernkentucky",
    "wku": "westernkentucky",
    "southernmiss": "southernmiss",
    "somiss": "southernmiss",
    "southernmississippi": "southernmiss",
    "sanjosest": "sanjosestate",
    "sjsu": "sanjosestate",
    "sdsu": "sandiegostate",
    "sandiegost": "sandiegostate",
    "ulmonroe": "ulm",
    "louisianamonroe": "ulm",
    "ulm": "ulm",
    "olddominion": "olddominion",
    "odu": "olddominion",
    "middletenn": "middletennessee",
    "mtsu": "middletennessee",
    "middletennessee": "middletennessee",
    "appst": "appalachianstate",
    "appalachianst": "appalachianstate",
    "appalachianstate": "appalachianstate",
    "eastcarolina": "eastcarolina",
    "ecu": "eastcarolina",
    "washst": "washingtonstate",
    "washingtonst": "washingtonstate",
    "wazzu": "washingtonstate",
    "ucf": "ucf",
    "usf": "southflorida",
    "southflorida": "southflorida",
    "utsa": "utsa",
    "fiu": "fiu",
    "uab": "uab",
    "umass": "umass",
    "unlv": "unlv",
}

def team_key(x):
    k = norm_simple(x)
    return ALIASES.get(k, k)

def add_classes(df, value_cols):
    df = df.copy()
    for col in value_cols:
        cls = col + "_class"
        pct = col + "_pctile"
        df[pct] = df.groupby("season")[col].rank(pct=True)
        df[cls] = np.where(
            df[pct] >= HIGH_Q, "High",
            np.where(df[pct] <= LOW_Q, "Low", "Mid")
        )
    return df

def extract_js_object_constant(html_text, const_name):
    start_pat = f"const {const_name} = "
    start = html_text.find(start_pat)
    if start == -1:
        raise SystemExit(f"Could not find {const_name} in index.html")

    i = start + len(start_pat)
    while i < len(html_text) and html_text[i].isspace():
        i += 1

    depth = 0
    in_str = False
    esc = False
    end = None

    for j in range(i, len(html_text)):
        ch = html_text[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break

    if end is None:
        raise SystemExit(f"Could not parse {const_name}")

    return json.loads(html_text[i:end])

def load_hist_rp():
    if not RP_HIST.exists():
        raise SystemExit(f"Missing {RP_HIST}")

    df = pd.read_csv(RP_HIST)
    df["team_key"] = df["team"].map(team_key)
    df = add_classes(df, ["overall", "offense", "defense"])
    return df

def load_2026_rp():
    obj = extract_js_object_constant(HTML.read_text(errors="ignore"), "RETURNING_PRODUCTION_2026")

    rows = []
    for team, r in obj.items():
        rows.append({
            "season": 2026,
            "team": team,
            "team_key": team_key(team),
            "overall": pd.to_numeric(r.get("overall"), errors="coerce"),
            "overall_rank": pd.to_numeric(r.get("rank"), errors="coerce"),
            "offense": pd.to_numeric(r.get("off"), errors="coerce"),
            "offense_rank": pd.to_numeric(r.get("offRank"), errors="coerce"),
            "defense": pd.to_numeric(r.get("def"), errors="coerce"),
            "defense_rank": pd.to_numeric(r.get("defRank"), errors="coerce"),
        })

    df = pd.DataFrame(rows)
    df = add_classes(df, ["overall", "offense", "defense"])
    return df

def pull_games():
    games_all = []
    lines_all = []

    for year in YEARS:
        g = flatten_records(cfbd_get("/games", {"year": year, "seasonType": "regular"}))
        l = flatten_records(cfbd_get("/lines", {"year": year, "seasonType": "regular"}))

        print("games/lines", year, "games:", len(g), "line games:", len(l))

        if not g.empty:
            games_all.append(g)
        if not l.empty:
            lines_all.append(l)

    games_raw = pd.concat(games_all, ignore_index=True)
    lines_raw = pd.concat(lines_all, ignore_index=True)
    lines_std = extract_lines(lines_raw)
    games = standardize_games(games_raw, lines_std)
    games = games[games["week"].isin(EARLY_WEEKS)].copy()

    games["home_key"] = games["home_team"].map(team_key)
    games["away_key"] = games["away_team"].map(team_key)

    return games

def ats_result(x):
    if pd.isna(x):
        return ""
    if x > 0:
        return "W"
    if x < 0:
        return "L"
    return "P"

def classify_role(spread):
    if pd.isna(spread):
        return ""
    if spread < 0:
        return "Favorite"
    if spread > 0:
        return "Underdog"
    return "Pick"

def build_hist_case(games, rp, case_name, high_metric, low_metric, high_class_col, low_class_col):
    rp_small = rp[[
        "season", "team", "team_key",
        "overall", "overall_rank", "offense", "offense_rank", "defense", "defense_rank",
        "overall_class", "offense_class", "defense_class"
    ]].copy()

    m = games.merge(
        rp_small.add_prefix("home_rp_").rename(columns={
            "home_rp_season": "season",
            "home_rp_team_key": "home_key"
        }),
        on=["season", "home_key"],
        how="left"
    ).merge(
        rp_small.add_prefix("away_rp_").rename(columns={
            "away_rp_season": "season",
            "away_rp_team_key": "away_key"
        }),
        on=["season", "away_key"],
        how="left"
    )

    rows = []

    for _, g in m.iterrows():
        home_high = g.get(f"home_rp_{high_class_col}") == "High"
        away_low = g.get(f"away_rp_{low_class_col}") == "Low"
        away_high = g.get(f"away_rp_{high_class_col}") == "High"
        home_low = g.get(f"home_rp_{low_class_col}") == "Low"

        if home_high and away_low:
            side = "home"
            opp = "away"
        elif away_high and home_low:
            side = "away"
            opp = "home"
        else:
            continue

        team = g[f"{side}_team"]
        opponent = g[f"{opp}_team"]
        spread = g[f"{side}_spread"]
        ats_margin = g[f"{side}_ats_margin"]

        rows.append({
            "season": g["season"],
            "week": g["week"],
            "date": g["date"],
            "game_id": g["game_id"],
            "case": case_name,
            "team": team,
            "opponent": opponent,
            "team_side": side,
            "role": classify_role(spread),
            "spread": spread,
            "ats_margin": ats_margin,
            "ats_result": ats_result(ats_margin),
            "team_overall": g[f"{side}_rp_overall"],
            "team_overall_rank": g[f"{side}_rp_overall_rank"],
            "team_offense": g[f"{side}_rp_offense"],
            "team_offense_rank": g[f"{side}_rp_offense_rank"],
            "team_defense": g[f"{side}_rp_defense"],
            "team_defense_rank": g[f"{side}_rp_defense_rank"],
            "opponent_overall": g[f"{opp}_rp_overall"],
            "opponent_overall_rank": g[f"{opp}_rp_overall_rank"],
            "opponent_offense": g[f"{opp}_rp_offense"],
            "opponent_offense_rank": g[f"{opp}_rp_offense_rank"],
            "opponent_defense": g[f"{opp}_rp_defense"],
            "opponent_defense_rank": g[f"{opp}_rp_defense_rank"],
        })

    return pd.DataFrame(rows)

def summarize(hist):
    if hist.empty:
        return pd.DataFrame()

    s = hist.groupby(["case", "role"], dropna=False).agg(
        games=("game_id", "count"),
        ats_w=("ats_result", lambda x: int((x == "W").sum())),
        ats_l=("ats_result", lambda x: int((x == "L").sum())),
        ats_p=("ats_result", lambda x: int((x == "P").sum())),
        avg_ats_margin=("ats_margin", "mean"),
        avg_spread=("spread", "mean"),
    ).reset_index()

    denom = s["ats_w"] + s["ats_l"]
    s["ats_pct"] = np.where(denom > 0, s["ats_w"] / denom, np.nan)
    s["ats_record"] = s["ats_w"].astype(str) + "-" + s["ats_l"].astype(str) + "-" + s["ats_p"].astype(str)
    return s

def load_coach_context():
    p = ROOT / "data/coach/game_coach_fav_dog_context.csv"
    if not p.exists():
        return pd.DataFrame()

    df = pd.read_csv(p, low_memory=False)
    if df.empty:
        return df

    df = df[
        df["is_applicable"].astype(str).str.lower().eq("true") &
        df["period"].astype(str).eq("Full Game")
    ].copy()

    return df

def strength_from_hist(row):
    if row is None:
        return "Watch"

    games = int(row["games"])
    margin = float(row["avg_ats_margin"])
    pct = float(row["ats_pct"]) if pd.notna(row["ats_pct"]) else 0

    if games >= 20 and margin >= 2.0 and pct >= 0.55:
        return "Strong"
    if games >= 15 and margin >= 1.0:
        return "Medium"
    if games >= 10 and margin >= 0.25:
        return "Watch"
    if margin <= -1.0:
        return "Fade"
    return "Info"

def confidence_from_games(n):
    try:
        n = int(n)
    except Exception:
        return "Low"
    if n >= 30:
        return "High"
    if n >= 15:
        return "Medium"
    return "Low"

def build_2026_case(sched, rp, summary, case_name, high_class_col, low_class_col):
    rp_small = rp[[
        "team", "team_key",
        "overall", "overall_rank", "offense", "offense_rank", "defense", "defense_rank",
        "overall_class", "offense_class", "defense_class"
    ]].copy()

    m = sched.copy()
    m["home_key"] = m["home_team"].map(team_key)
    m["away_key"] = m["away_team"].map(team_key)

    m = m.merge(
        rp_small.add_prefix("home_rp_").rename(columns={"home_rp_team_key": "home_key"}),
        on="home_key",
        how="left"
    ).merge(
        rp_small.add_prefix("away_rp_").rename(columns={"away_rp_team_key": "away_key"}),
        on="away_key",
        how="left"
    )

    signals = []

    for _, g in m.iterrows():
        home_high = g.get(f"home_rp_{high_class_col}") == "High"
        away_low = g.get(f"away_rp_{low_class_col}") == "Low"
        away_high = g.get(f"away_rp_{high_class_col}") == "High"
        home_low = g.get(f"home_rp_{low_class_col}") == "Low"

        if home_high and away_low:
            side = "home"
            opp = "away"
        elif away_high and home_low:
            side = "away"
            opp = "home"
        else:
            continue

        team = g[f"{side}_team"]
        opponent = g[f"{opp}_team"]
        role = role_from_home_edge(g["home_edge"], side)

        hist_row = summary[
            summary["case"].astype(str).eq(case_name) &
            summary["role"].astype(str).eq(role)
        ]

        hist = hist_row.iloc[0] if not hist_row.empty else None

        if hist is not None:
            hist_games = int(hist["games"])
            hist_record = str(hist["ats_record"])
            hist_pct = float(hist["ats_pct"]) if pd.notna(hist["ats_pct"]) else np.nan
            hist_margin = float(hist["avg_ats_margin"]) if pd.notna(hist["avg_ats_margin"]) else np.nan
            supporting = f"2023–25 early-season {case_name} {role}s: {hist_record} ATS, {hist_pct:.1%}, {hist_margin:+.2f} ATS margin over {hist_games} games"
            strength = strength_from_hist(hist)
            confidence = confidence_from_games(hist_games)
        else:
            hist_games = ""
            hist_record = ""
            hist_pct = np.nan
            hist_margin = np.nan
            supporting = "No matching historical role summary."
            strength = "Watch"
            confidence = "Low"

        detail = (
            f"{team} triggers {case_name} vs {opponent}. "
            f"2026 RP: {team} overall {g[f'{side}_rp_overall']}% #{int(g[f'{side}_rp_overall_rank'])}, "
            f"off {g[f'{side}_rp_offense']}% #{int(g[f'{side}_rp_offense_rank'])}, "
            f"def {g[f'{side}_rp_defense']}% #{int(g[f'{side}_rp_defense_rank'])}. "
            f"Opponent RP: overall {g[f'{opp}_rp_overall']}% #{int(g[f'{opp}_rp_overall_rank'])}, "
            f"off {g[f'{opp}_rp_offense']}% #{int(g[f'{opp}_rp_offense_rank'])}, "
            f"def {g[f'{opp}_rp_defense']}% #{int(g[f'{opp}_rp_defense_rank'])}. "
            f"Projected role: {role}. {supporting}."
        )

        signals.append({
            "game_id": g["game_id"],
            "date": g["date"],
            "away_team": g["away_team"],
            "home_team": g["home_team"],
            "signal_group": "Returning Production",
            "signal_type": case_name,
            "market": "Spread",
            "period": "Full Game",
            "team": team,
            "opponent": opponent,
            "direction": team,
            "strength": strength,
            "score": hist_margin,
            "confidence": confidence,
            "headline": f"{team} returning production edge",
            "detail": detail,
            "supporting_data": supporting,
            "source": "2026 Bill Connelly/SP+ RP + 2023–25 SP+ RP historical backtest with CFBD lines",
            "projected_role": role,
            "historical_games": hist_games,
            "historical_ats_record": hist_record,
            "historical_ats_pct": hist_pct,
            "historical_avg_ats_margin": hist_margin,
        })

    return pd.DataFrame(signals)

def attach_coach_context(signals):
    coaches = load_coach_context()
    if signals.empty or coaches.empty:
        return signals

    out = signals.copy()

    coach_cols = [
        "game_id", "team", "coach", "ats_record", "avg_ats_margin",
        "projected_team_role", "source"
    ]

    for c in coach_cols:
        if c not in coaches.columns:
            coaches[c] = ""

    csmall = coaches[coach_cols].copy()
    csmall = csmall.rename(columns={
        "coach": "team_coach",
        "ats_record": "team_coach_role_ats_record",
        "avg_ats_margin": "team_coach_role_avg_ats_margin",
        "projected_team_role": "team_coach_role",
        "source": "team_coach_source",
    })

    out = out.merge(csmall, on=["game_id", "team"], how="left")

    return out

def main():
    for p in [OUT_GAMES.parent, OUT_SUMMARY.parent, OUT_SIGNALS.parent, OUT_AUDIT.parent]:
        p.mkdir(parents=True, exist_ok=True)

    rp_hist = load_hist_rp()
    games = pull_games()

    hist_parts = [
        build_hist_case(games, rp_hist, "High Overall RP vs Low Overall RP", "overall", "overall", "overall_class", "overall_class"),
        build_hist_case(games, rp_hist, "High Offense RP vs Low Defense RP", "offense", "defense", "offense_class", "defense_class"),
        build_hist_case(games, rp_hist, "High Defense RP vs Low Offense RP", "defense", "offense", "defense_class", "offense_class"),
    ]

    hist = pd.concat([x for x in hist_parts if not x.empty], ignore_index=True)
    summary = summarize(hist)

    hist.to_csv(OUT_GAMES, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)

    rp_2026 = load_2026_rp()
    sched_2026 = load_2026_schedule()

    sig_parts = [
        build_2026_case(sched_2026, rp_2026, summary, "High Overall RP vs Low Overall RP", "overall_class", "overall_class"),
        build_2026_case(sched_2026, rp_2026, summary, "High Offense RP vs Low Defense RP", "offense_class", "defense_class"),
        build_2026_case(sched_2026, rp_2026, summary, "High Defense RP vs Low Offense RP", "defense_class", "offense_class"),
    ]

    signals = pd.concat([x for x in sig_parts if not x.empty], ignore_index=True) if sig_parts else pd.DataFrame()
    signals = attach_coach_context(signals)
    signals.to_csv(OUT_SIGNALS, index=False)

    if OUT_MASTER.exists():
        master = pd.read_csv(OUT_MASTER, low_memory=False)
        if "signal_group" in master.columns:
            master = master[master["signal_group"].astype(str).ne("Returning Production")].copy()
        master = pd.concat([master, signals], ignore_index=True, sort=False)
    else:
        master = signals.copy()

    master.to_csv(OUT_MASTER, index=False)

    audit = pd.DataFrame([
        {"metric": "historical_spplus_rp_rows", "value": len(rp_hist)},
        {"metric": "historical_early_games_with_lines", "value": len(games)},
        {"metric": "historical_signal_games", "value": len(hist)},
        {"metric": "historical_summary_rows", "value": len(summary)},
        {"metric": "site_2026_rp_teams", "value": len(rp_2026)},
        {"metric": "returning_production_2026_signals", "value": len(signals)},
    ])

    audit.to_csv(OUT_AUDIT, index=False)

    print("wrote:", OUT_GAMES, "rows:", len(hist))
    print("wrote:", OUT_SUMMARY, "rows:", len(summary))
    print("wrote:", OUT_SIGNALS, "rows:", len(signals))
    print("wrote:", OUT_MASTER)
    print("wrote:", OUT_AUDIT)
    print()
    print(audit.to_string(index=False))
    print()
    print("Historical summary:")
    print(summary.sort_values(["case", "role"]).to_string(index=False))
    print()
    if not signals.empty:
        cols = [
            "date", "away_team", "home_team", "signal_type", "team",
            "projected_role", "strength", "historical_ats_record",
            "historical_avg_ats_margin", "team_coach", "team_coach_role_ats_record"
        ]
        print("2026 signals sample:")
        print(signals[cols].head(50).to_string(index=False))

if __name__ == "__main__":
    main()
