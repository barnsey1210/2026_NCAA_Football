#!/usr/bin/env python3
from pathlib import Path
import re
import json
import math
import sys
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Reuse the CFBD pulling/cache/game-line helpers from the first script.
from scripts.signals.build_returning_production_early_season_signals import (
    cfbd_get,
    flatten_records,
    standardize_games,
    extract_lines,
    load_2026_schedule,
    role_from_home_edge,
    team_key,
    to_num,
)

HTML = Path(".") / "index.html"

IMPORT_DIR = ROOT / "data/import/cfbd"
RESEARCH_DIR = ROOT / "data/research"
SIGNALS_DIR = ROOT / "data/signals"
AUDIT_OUT = ROOT / "data/audit/returning_production_early_season_v2_audit.csv"

RP_RAW_OUT = IMPORT_DIR / "cfbd_returning_production_2023_2025.csv"
HIST_GAMES_OUT = RESEARCH_DIR / "returning_production_early_season_games_v2.csv"
HIST_SUMMARY_OUT = RESEARCH_DIR / "returning_production_early_season_summary_v2.csv"
SIGNALS_OUT = SIGNALS_DIR / "returning_production_early_season_signals.csv"
MASTER_SIGNALS_OUT = SIGNALS_DIR / "game_betting_signals.csv"

YEARS_HIST = [2023, 2024, 2025]
EARLY_WEEKS = [0, 1, 2, 3, 4]

HIGH_Q = 0.75
LOW_Q = 0.25

def ensure_dirs():
    for p in [IMPORT_DIR, RESEARCH_DIR, SIGNALS_DIR, AUDIT_OUT.parent]:
        p.mkdir(parents=True, exist_ok=True)

def norm_team(name):
    return re.sub(r"\s+", " ", str(name or "").strip()).lower()

def extract_js_object_constant(html_text, const_name):
    start_pat = f"const {const_name} = "
    start = html_text.find(start_pat)
    if start == -1:
        raise SystemExit(f"Could not find JS constant {const_name}")

    i = start + len(start_pat)
    while i < len(html_text) and html_text[i].isspace():
        i += 1
    if i >= len(html_text) or html_text[i] != "{":
        raise SystemExit(f"{const_name} did not start with object literal")

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
        raise SystemExit(f"Could not parse JS object for {const_name}")

    return json.loads(html_text[i:end])

def load_2026_returning_production_from_site():
    s = HTML.read_text(errors="ignore")
    obj = extract_js_object_constant(s, "RETURNING_PRODUCTION_2026")

    rows = []
    for team, r in obj.items():
        rows.append({
            "season": 2026,
            "team": team,
            "team_key": team_key(team),
            "rp_overall": pd.to_numeric(r.get("overall"), errors="coerce"),
            "rp_offense": pd.to_numeric(r.get("off"), errors="coerce"),
            "rp_defense": pd.to_numeric(r.get("def"), errors="coerce"),
            "rp_overall_rank": pd.to_numeric(r.get("rank"), errors="coerce"),
            "rp_offense_rank": pd.to_numeric(r.get("offRank"), errors="coerce"),
            "rp_defense_rank": pd.to_numeric(r.get("defRank"), errors="coerce"),
        })

    df = pd.DataFrame(rows)

    for metric in ["overall", "offense", "defense"]:
        col = f"rp_{metric}"
        df[f"rp_{metric}_pctile"] = df[col].rank(pct=True)
        df[f"rp_{metric}_class"] = np.where(
            df[f"rp_{metric}_pctile"] >= HIGH_Q, "High",
            np.where(df[f"rp_{metric}_pctile"] <= LOW_Q, "Low", "Mid")
        )

    return df

def pull_cfbd_historical_rp():
    dfs = []
    for year in YEARS_HIST:
        data = cfbd_get("/player/returning", {"year": year})
        df = flatten_records(data)
        if df.empty:
            continue
        if "season" not in df.columns:
            df["season"] = year
        dfs.append(df)
        print("returning production", year, "rows:", len(df))

    if not dfs:
        raise SystemExit("No CFBD returning-production rows pulled.")

    raw = pd.concat(dfs, ignore_index=True)
    raw.to_csv(RP_RAW_OUT, index=False)

    required = ["season", "team", "percent_ppa"]
    missing = [c for c in required if c not in raw.columns]
    if missing:
        raise SystemExit(f"Missing expected CFBD RP columns: {missing}. Columns: {list(raw.columns)}")

    out = pd.DataFrame({
        "season": pd.to_numeric(raw["season"], errors="coerce").astype("Int64"),
        "team": raw["team"].astype(str),
        "team_key": raw["team"].map(team_key),
        "conference": raw.get("conference", ""),
        "rp_overall": pd.to_numeric(raw["percent_ppa"], errors="coerce"),
        "rp_passing": pd.to_numeric(raw.get("percent_passing_ppa"), errors="coerce"),
        "rp_rushing": pd.to_numeric(raw.get("percent_rushing_ppa"), errors="coerce"),
        "rp_receiving": pd.to_numeric(raw.get("percent_receiving_ppa"), errors="coerce"),
    })

    for metric in ["overall", "passing", "rushing", "receiving"]:
        col = f"rp_{metric}"
        if col not in out.columns or out[col].notna().sum() == 0:
            continue
        out[f"rp_{metric}_pctile"] = out.groupby("season")[col].rank(pct=True)
        out[f"rp_{metric}_class"] = np.where(
            out[f"rp_{metric}_pctile"] >= HIGH_Q, "High",
            np.where(out[f"rp_{metric}_pctile"] <= LOW_Q, "Low", "Mid")
        )

    return raw, out

def pull_historical_games_and_lines():
    games_all = []
    lines_all = []

    for year in YEARS_HIST:
        games = cfbd_get("/games", {"year": year, "seasonType": "regular"})
        lines = cfbd_get("/lines", {"year": year, "seasonType": "regular"})

        gdf = flatten_records(games)
        ldf = flatten_records(lines)

        print("games/lines", year, "games:", len(gdf), "line games:", len(ldf))

        if not gdf.empty:
            games_all.append(gdf)
        if not ldf.empty:
            lines_all.append(ldf)

    games_df = pd.concat(games_all, ignore_index=True) if games_all else pd.DataFrame()
    lines_df = pd.concat(lines_all, ignore_index=True) if lines_all else pd.DataFrame()

    lines_std = extract_lines(lines_df)
    games_std = standardize_games(games_df, lines_std)
    games_std = games_std[games_std["week"].isin(EARLY_WEEKS)].copy()

    return games_std

def ats_result(margin):
    if pd.isna(margin):
        return ""
    if margin > 0:
        return "W"
    if margin < 0:
        return "L"
    return "P"

def build_historical_high_low(games, rp_hist):
    rows = []

    # Do not include defense here. CFBD returning endpoint is offensive production-based.
    metrics = ["overall", "passing", "rushing", "receiving"]

    for metric in metrics:
        class_col = f"rp_{metric}_class"
        value_col = f"rp_{metric}"
        pct_col = f"rp_{metric}_pctile"

        if class_col not in rp_hist.columns:
            continue

        rp_small = rp_hist[["season", "team", "team_key", value_col, pct_col, class_col]].copy()

        m = games.merge(
            rp_small.rename(columns={
                "team": "home_rp_team",
                "team_key": "home_key",
                value_col: "home_rp_value",
                pct_col: "home_rp_pctile",
                class_col: "home_rp_class",
            }),
            on=["season", "home_key"],
            how="left"
        ).merge(
            rp_small.rename(columns={
                "team": "away_rp_team",
                "team_key": "away_key",
                value_col: "away_rp_value",
                pct_col: "away_rp_pctile",
                class_col: "away_rp_class",
            }),
            on=["season", "away_key"],
            how="left"
        )

        hvsl = m[
            ((m["home_rp_class"] == "High") & (m["away_rp_class"] == "Low")) |
            ((m["home_rp_class"] == "Low") & (m["away_rp_class"] == "High"))
        ].copy()

        for _, g in hvsl.iterrows():
            high_side = "home" if g["home_rp_class"] == "High" else "away"
            low_side = "away" if high_side == "home" else "home"

            high_team = g[f"{high_side}_team"]
            low_team = g[f"{low_side}_team"]
            high_spread = g[f"{high_side}_spread"]
            high_ats_margin = g[f"{high_side}_ats_margin"]

            if pd.isna(high_spread):
                role = ""
            elif high_spread < 0:
                role = "Favorite"
            elif high_spread > 0:
                role = "Underdog"
            else:
                role = "Pick"

            rows.append({
                "season": g["season"],
                "week": g["week"],
                "date": g["date"],
                "game_id": g["game_id"],
                "metric": metric,
                "home_team": g["home_team"],
                "away_team": g["away_team"],
                "high_rp_team": high_team,
                "low_rp_team": low_team,
                "high_rp_side": high_side,
                "high_rp_role": role,
                "high_rp_value": g[f"{high_side}_rp_value"],
                "low_rp_value": g[f"{low_side}_rp_value"],
                "high_rp_pctile": g[f"{high_side}_rp_pctile"],
                "low_rp_pctile": g[f"{low_side}_rp_pctile"],
                "high_rp_spread": high_spread,
                "high_rp_ats_margin": high_ats_margin,
                "high_rp_ats_result": ats_result(high_ats_margin),
                "home_spread": g["home_spread"],
                "total_line": g["total_line"],
            })

    hist = pd.DataFrame(rows)
    hist.to_csv(HIST_GAMES_OUT, index=False)

    if hist.empty:
        summary = pd.DataFrame()
        summary.to_csv(HIST_SUMMARY_OUT, index=False)
        return hist, summary

    summary = hist.groupby(["metric", "high_rp_role"], dropna=False).agg(
        games=("game_id", "count"),
        ats_w=("high_rp_ats_result", lambda x: int((x == "W").sum())),
        ats_l=("high_rp_ats_result", lambda x: int((x == "L").sum())),
        ats_p=("high_rp_ats_result", lambda x: int((x == "P").sum())),
        avg_ats_margin=("high_rp_ats_margin", "mean"),
        avg_spread=("high_rp_spread", "mean"),
        avg_high_rp=("high_rp_value", "mean"),
        avg_low_rp=("low_rp_value", "mean"),
    ).reset_index()

    denom = summary["ats_w"] + summary["ats_l"]
    summary["ats_pct"] = np.where(denom > 0, summary["ats_w"] / denom, np.nan)
    summary["ats_record"] = summary["ats_w"].astype(str) + "-" + summary["ats_l"].astype(str) + "-" + summary["ats_p"].astype(str)

    summary.to_csv(HIST_SUMMARY_OUT, index=False)
    return hist, summary

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

    keep = [
        "game_id", "team", "projected_team_role", "coach", "games",
        "ats_record", "avg_ats_margin", "ou_record", "avg_total_margin", "source"
    ]
    for c in keep:
        if c not in df.columns:
            df[c] = ""

    return df[keep].copy()

def confidence_label(games):
    try:
        g = int(games)
    except Exception:
        return "Low"
    if g >= 40:
        return "High"
    if g >= 20:
        return "Medium"
    return "Low"

def strength_from_hist(hist):
    if hist is None:
        return "Watch"

    games = int(hist["games"])
    margin = float(hist["avg_ats_margin"])
    pct = float(hist["ats_pct"]) if pd.notna(hist["ats_pct"]) else 0

    if games >= 20 and margin >= 2.0 and pct >= 0.55:
        return "Strong"
    if games >= 15 and margin >= 1.0:
        return "Medium"
    if games >= 10 and margin >= 0.25:
        return "Watch"
    if margin <= -1.0:
        return "Fade"
    return "Info"

def build_2026_signals(rp_2026, summary):
    sched = load_2026_schedule()
    coaches = load_coach_context()

    signals = []

    # Main actionable signal for now: overall RP high-vs-low using Bill Connelly/SP+ 2026 RP.
    metric = "overall"
    rp_small = rp_2026[[
        "team", "team_key", "rp_overall", "rp_overall_pctile", "rp_overall_class",
        "rp_offense", "rp_offense_class", "rp_defense", "rp_defense_class",
        "rp_overall_rank", "rp_offense_rank", "rp_defense_rank",
    ]].copy()

    m = sched.merge(
        rp_small.rename(columns={
            "team": "home_rp_team",
            "team_key": "home_key",
            "rp_overall": "home_rp_value",
            "rp_overall_pctile": "home_rp_pctile",
            "rp_overall_class": "home_rp_class",
            "rp_offense": "home_rp_offense",
            "rp_offense_class": "home_rp_offense_class",
            "rp_defense": "home_rp_defense",
            "rp_defense_class": "home_rp_defense_class",
            "rp_overall_rank": "home_rp_rank",
            "rp_offense_rank": "home_rp_off_rank",
            "rp_defense_rank": "home_rp_def_rank",
        }),
        on="home_key",
        how="left"
    ).merge(
        rp_small.rename(columns={
            "team": "away_rp_team",
            "team_key": "away_key",
            "rp_overall": "away_rp_value",
            "rp_overall_pctile": "away_rp_pctile",
            "rp_overall_class": "away_rp_class",
            "rp_offense": "away_rp_offense",
            "rp_offense_class": "away_rp_offense_class",
            "rp_defense": "away_rp_defense",
            "rp_defense_class": "away_rp_defense_class",
            "rp_overall_rank": "away_rp_rank",
            "rp_offense_rank": "away_rp_off_rank",
            "rp_defense_rank": "away_rp_def_rank",
        }),
        on="away_key",
        how="left"
    )

    hvsl = m[
        ((m["home_rp_class"] == "High") & (m["away_rp_class"] == "Low")) |
        ((m["home_rp_class"] == "Low") & (m["away_rp_class"] == "High"))
    ].copy()

    for _, g in hvsl.iterrows():
        high_side = "home" if g["home_rp_class"] == "High" else "away"
        low_side = "away" if high_side == "home" else "home"

        high_team = g[f"{high_side}_team"]
        low_team = g[f"{low_side}_team"]
        role = role_from_home_edge(g["home_edge"], high_side)

        hist_row = summary[
            summary["metric"].astype(str).eq("overall") &
            summary["high_rp_role"].astype(str).eq(role)
        ]
        hist = hist_row.iloc[0] if not hist_row.empty else None

        if hist is not None:
            hist_games = int(hist["games"])
            hist_record = str(hist["ats_record"])
            hist_pct = float(hist["ats_pct"]) if pd.notna(hist["ats_pct"]) else np.nan
            hist_margin = float(hist["avg_ats_margin"]) if pd.notna(hist["avg_ats_margin"]) else np.nan
            hist_support = (
                f"2023–25 early-season high-overall RP {role}s: "
                f"{hist_record} ATS, {hist_pct:.1%}, {hist_margin:+.2f} ATS margin over {hist_games} games"
            )
            strength = strength_from_hist(hist)
            confidence = confidence_label(hist_games)
        else:
            hist_games = ""
            hist_record = ""
            hist_pct = np.nan
            hist_margin = np.nan
            hist_support = "No matching 2023–25 historical high-vs-low RP summary."
            strength = "Watch"
            confidence = "Low"

        # Coach add-on context for same game/team.
        coach_note = ""
        coach_row = pd.DataFrame()
        opp_coach_row = pd.DataFrame()
        if not coaches.empty:
            coach_row = coaches[
                coaches["game_id"].astype(str).eq(str(g["game_id"])) &
                coaches["team"].astype(str).eq(str(high_team))
            ]
            opp_coach_row = coaches[
                coaches["game_id"].astype(str).eq(str(g["game_id"])) &
                coaches["team"].astype(str).eq(str(low_team))
            ]

        if not coach_row.empty:
            cr = coach_row.iloc[0]
            coach_note = (
                f" Coach: {cr.get('coach','')} as {cr.get('projected_team_role','')}: "
                f"{cr.get('ats_record','')} ATS, {float(cr.get('avg_ats_margin')):+.2f} ATS margin."
            ) if pd.notna(cr.get("avg_ats_margin")) else (
                f" Coach: {cr.get('coach','')} as {cr.get('projected_team_role','')}: {cr.get('ats_record','')} ATS."
            )

        headline = f"{high_team} early-season returning production edge"
        detail = (
            f"{high_team} is High 2026 overall returning production "
            f"({g[f'{high_side}_rp_value']:.0f}%, rank #{int(g[f'{high_side}_rp_rank'])}) "
            f"vs {low_team} Low 2026 overall returning production "
            f"({g[f'{low_side}_rp_value']:.0f}%, rank #{int(g[f'{low_side}_rp_rank'])}). "
            f"Projected role: {role}. {hist_support}.{coach_note}"
        )

        signals.append({
            "game_id": g["game_id"],
            "date": g["date"],
            "away_team": g["away_team"],
            "home_team": g["home_team"],
            "signal_group": "Returning Production",
            "signal_type": "Early Season High-vs-Low Overall RP",
            "market": "Spread",
            "period": "Full Game",
            "team": high_team,
            "opponent": low_team,
            "direction": high_team,
            "strength": strength,
            "score": hist_margin,
            "confidence": confidence,
            "headline": headline,
            "detail": detail,
            "supporting_data": hist_support,
            "source": "2026 Bill Connelly/SP+ returning production + 2023–25 CFBD historical lines",
            "metric": "overall",
            "projected_role": role,
            "team_rp_value": g[f"{high_side}_rp_value"],
            "opponent_rp_value": g[f"{low_side}_rp_value"],
            "team_rp_rank": g[f"{high_side}_rp_rank"],
            "opponent_rp_rank": g[f"{low_side}_rp_rank"],
            "team_rp_offense": g[f"{high_side}_rp_offense"],
            "team_rp_defense": g[f"{high_side}_rp_defense"],
            "opponent_rp_offense": g[f"{low_side}_rp_offense"],
            "opponent_rp_defense": g[f"{low_side}_rp_defense"],
            "historical_games": hist_games,
            "historical_ats_record": hist_record,
            "historical_ats_pct": hist_pct,
            "historical_avg_ats_margin": hist_margin,
            "team_coach": coach_row.iloc[0]["coach"] if not coach_row.empty else "",
            "team_coach_role_ats_record": coach_row.iloc[0]["ats_record"] if not coach_row.empty else "",
            "team_coach_role_avg_ats_margin": coach_row.iloc[0]["avg_ats_margin"] if not coach_row.empty else "",
            "opponent_coach": opp_coach_row.iloc[0]["coach"] if not opp_coach_row.empty else "",
            "opponent_coach_role_ats_record": opp_coach_row.iloc[0]["ats_record"] if not opp_coach_row.empty else "",
            "opponent_coach_role_avg_ats_margin": opp_coach_row.iloc[0]["avg_ats_margin"] if not opp_coach_row.empty else "",
        })

    out = pd.DataFrame(signals)
    out.to_csv(SIGNALS_OUT, index=False)

    if MASTER_SIGNALS_OUT.exists():
        master = pd.read_csv(MASTER_SIGNALS_OUT, low_memory=False)
        if "signal_group" in master.columns:
            master = master[master["signal_group"].astype(str).ne("Returning Production")].copy()
        master = pd.concat([master, out], ignore_index=True, sort=False)
    else:
        master = out.copy()

    master.to_csv(MASTER_SIGNALS_OUT, index=False)
    return out

def main():
    ensure_dirs()

    rp_raw, rp_hist = pull_cfbd_historical_rp()
    games = pull_historical_games_and_lines()
    hist, summary = build_historical_high_low(games, rp_hist)

    rp_2026 = load_2026_returning_production_from_site()
    signals = build_2026_signals(rp_2026, summary)

    audit = pd.DataFrame([
        {"metric": "cfbd_rp_2023_2025_rows", "value": len(rp_raw)},
        {"metric": "historical_early_games_with_lines", "value": len(games)},
        {"metric": "historical_high_low_games", "value": len(hist)},
        {"metric": "historical_summary_rows", "value": len(summary)},
        {"metric": "site_2026_returning_production_teams", "value": len(rp_2026)},
        {"metric": "returning_production_2026_signals", "value": len(signals)},
        {"metric": "historical_primary_metric", "value": "CFBD percent_ppa"},
        {"metric": "site_2026_metric", "value": "Bill Connelly/SP+ overall/off/def"},
    ])
    audit.to_csv(AUDIT_OUT, index=False)

    print("wrote:", RP_RAW_OUT, "rows:", len(rp_raw))
    print("wrote:", HIST_GAMES_OUT, "rows:", len(hist))
    print("wrote:", HIST_SUMMARY_OUT, "rows:", len(summary))
    print("wrote:", SIGNALS_OUT, "rows:", len(signals))
    print("wrote:", MASTER_SIGNALS_OUT)
    print("wrote:", AUDIT_OUT)
    print()
    print(audit.to_string(index=False))

    if not summary.empty:
        print("\nHistorical summary:")
        print(summary.sort_values(["metric", "high_rp_role"]).to_string(index=False))

    if not signals.empty:
        print("\n2026 signal sample:")
        cols = [
            "date", "away_team", "home_team", "team", "projected_role",
            "strength", "historical_ats_record", "historical_avg_ats_margin",
            "team_coach", "team_coach_role_ats_record", "detail"
        ]
        print(signals[cols].head(40).to_string(index=False))

if __name__ == "__main__":
    main()
