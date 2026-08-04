#!/usr/bin/env python3
from pathlib import Path
import os
import re
import json
import math
import hashlib
import requests
import pandas as pd
import numpy as np

ROOT = Path(".")
CACHE = ROOT / "cfbd_cache/returning_production_signals"
IMPORT_DIR = ROOT / "data/import/cfbd"
RESEARCH_DIR = ROOT / "data/research"
SIGNALS_DIR = ROOT / "data/signals"

RP_RAW_OUT = IMPORT_DIR / "cfbd_returning_production_2023_2026.csv"
HIST_GAMES_OUT = RESEARCH_DIR / "returning_production_early_season_games.csv"
HIST_SUMMARY_OUT = RESEARCH_DIR / "returning_production_early_season_summary.csv"
SIGNALS_OUT = SIGNALS_DIR / "returning_production_early_season_signals.csv"
MASTER_SIGNALS_OUT = SIGNALS_DIR / "game_betting_signals.csv"
AUDIT_OUT = ROOT / "data/audit/returning_production_early_season_audit.csv"

YEARS_RP = [2023, 2024, 2025, 2026]
YEARS_HIST = [2023, 2024, 2025]
EARLY_WEEKS = [0, 1, 2, 3, 4]

HIGH_Q = 0.75
LOW_Q = 0.25

API_BASE = "https://api.collegefootballdata.com"

def ensure_dirs():
    for p in [CACHE, IMPORT_DIR, RESEARCH_DIR, SIGNALS_DIR, AUDIT_OUT.parent]:
        p.mkdir(parents=True, exist_ok=True)

def snake(s):
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(s))
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s)
    return s.strip("_").lower()

def norm_team(x):
    return re.sub(r"\s+", " ", str(x or "").strip()).lower()

TEAM_ALIASES = {
    "miami (oh)": "miami (oh)",
    "miami ohio": "miami (oh)",
    "utsa": "utsa",
    "texas-san antonio": "utsa",
    "ul monroe": "ulm",
    "louisiana monroe": "ulm",
    "louisiana-monroe": "ulm",
    "louisiana": "louisiana",
    "louisiana lafayette": "louisiana",
    "ul lafayette": "louisiana",
    "ucf": "ucf",
    "central florida": "ucf",
    "byu": "byu",
    "bowling green state": "bowling green",
}

def team_key(x):
    n = norm_team(x)
    return TEAM_ALIASES.get(n, n)

def cache_key(path, params):
    blob = json.dumps({"path": path, "params": params}, sort_keys=True)
    return hashlib.md5(blob.encode()).hexdigest()

def cfbd_get(path, params):
    key = os.environ.get("CFBD_API_KEY") or os.environ.get("COLLEGEFOOTBALLDATA_API_KEY")
    cache_file = CACHE / f"{path.strip('/').replace('/','_')}_{cache_key(path, params)}.json"

    if cache_file.exists():
        return json.loads(cache_file.read_text())

    if not key:
        raise SystemExit(
            "Missing CFBD_API_KEY or COLLEGEFOOTBALLDATA_API_KEY and cache file does not exist. "
            "Set your key, then rerun."
        )

    headers = {"Authorization": f"Bearer {key}"}
    r = requests.get(API_BASE + path, params=params, headers=headers, timeout=45)
    if r.status_code != 200:
        raise SystemExit(f"CFBD request failed {r.status_code}: {path} {params}\n{r.text[:500]}")
    data = r.json()
    cache_file.write_text(json.dumps(data))
    return data

def flatten_records(records):
    if not records:
        return pd.DataFrame()
    df = pd.json_normalize(records)
    df.columns = [snake(c) for c in df.columns]
    return df

def pull_returning_production():
    dfs = []
    for year in YEARS_RP:
        data = cfbd_get("/player/returning", {"year": year})
        df = flatten_records(data)
        if df.empty:
            continue
        if "season" not in df.columns:
            df["season"] = year
        if "year" not in df.columns:
            df["year"] = year
        dfs.append(df)
        print("returning production", year, "rows:", len(df))

    if not dfs:
        raise SystemExit("No returning production rows pulled.")

    out = pd.concat(dfs, ignore_index=True)
    out.to_csv(RP_RAW_OUT, index=False)
    return out

def pull_games_and_lines():
    games_all = []
    lines_all = []

    for year in YEARS_HIST:
        games = cfbd_get("/games", {"year": year, "seasonType": "regular"})
        gdf = flatten_records(games)
        if not gdf.empty:
            games_all.append(gdf)

        lines = cfbd_get("/lines", {"year": year, "seasonType": "regular"})
        ldf = flatten_records(lines)
        if not ldf.empty:
            lines_all.append(ldf)

        print("games/lines", year, "games:", len(gdf), "line games:", len(ldf))

    games_df = pd.concat(games_all, ignore_index=True) if games_all else pd.DataFrame()
    lines_df = pd.concat(lines_all, ignore_index=True) if lines_all else pd.DataFrame()

    return games_df, lines_df

def to_num(x):
    return pd.to_numeric(x, errors="coerce")

def first_col(df, names):
    for n in names:
        if n in df.columns:
            return n
    return None

def pick_rp_metrics(rp):
    numeric_cols = []
    for c in rp.columns:
        if c in {"season", "year"}:
            continue
        vals = pd.to_numeric(rp[c], errors="coerce")
        if vals.notna().sum() >= 25:
            numeric_cols.append(c)

    def score_col(c, mode):
        cl = c.lower()
        score = 0
        if any(x in cl for x in ["return", "production", "ppa", "usage", "pct", "percent"]):
            score += 5
        if mode == "overall":
            if any(x in cl for x in ["overall", "total"]):
                score += 8
            if any(x in cl for x in ["offense", "off_", "defense", "def_"]):
                score -= 6
        elif mode == "offense":
            if any(x in cl for x in ["offense", "off_"]):
                score += 10
            if any(x in cl for x in ["passing", "rushing", "receiving"]):
                score += 4
        elif mode == "defense":
            if any(x in cl for x in ["defense", "def_"]):
                score += 10
        return score

    picks = {}
    for mode in ["overall", "offense", "defense"]:
        candidates = sorted(
            numeric_cols,
            key=lambda c: score_col(c, mode),
            reverse=True
        )
        candidates = [c for c in candidates if score_col(c, mode) > 4]
        picks[mode] = candidates[0] if candidates else None

    return picks

def standardize_rp(rp):
    rp = rp.copy()
    team_col = first_col(rp, ["team", "school"])
    conf_col = first_col(rp, ["conference"])
    season_col = first_col(rp, ["season", "year"])

    if not team_col or not season_col:
        raise SystemExit(f"Could not identify team/season columns in RP. Columns: {list(rp.columns)}")

    picks = pick_rp_metrics(rp)

    out = pd.DataFrame({
        "season": to_num(rp[season_col]).astype("Int64"),
        "team": rp[team_col].astype(str),
        "team_key": rp[team_col].map(team_key),
        "conference": rp[conf_col].astype(str) if conf_col else "",
    })

    for metric, col in picks.items():
        out[f"rp_{metric}"] = to_num(rp[col]) if col else np.nan
        out[f"rp_{metric}_source_col"] = col or ""

    # Percentile classes within each season.
    for metric in ["overall", "offense", "defense"]:
        col = f"rp_{metric}"
        if out[col].notna().sum() == 0:
            out[f"rp_{metric}_pctile"] = np.nan
            out[f"rp_{metric}_class"] = ""
            continue

        out[f"rp_{metric}_pctile"] = out.groupby("season")[col].rank(pct=True)
        out[f"rp_{metric}_class"] = np.where(
            out[f"rp_{metric}_pctile"] >= HIGH_Q, "High",
            np.where(out[f"rp_{metric}_pctile"] <= LOW_Q, "Low", "Mid")
        )

    return out, picks

def extract_lines(lines_df):
    rows = []

    if lines_df.empty:
        return pd.DataFrame()

    id_col = first_col(lines_df, ["id", "game_id"])
    if not id_col:
        return pd.DataFrame()

    # json_normalize may flatten lines into columns, but usually there is a nested lines list
    # if not flattened. Re-pull cache/raw shape is easier through existing data not available here,
    # so handle common normalized columns and nested objects.
    for _, r in lines_df.iterrows():
        game_id = r.get(id_col)
        spread_vals = []
        total_vals = []

        # normalized style: lines list may remain as object
        line_obj = r.get("lines")
        if isinstance(line_obj, list):
            for ln in line_obj:
                try:
                    sp = ln.get("spread")
                    if sp is not None:
                        spread_vals.append(float(sp))
                except Exception:
                    pass
                try:
                    ou = ln.get("overUnder") if "overUnder" in ln else ln.get("over_under")
                    if ou is not None:
                        total_vals.append(float(ou))
                except Exception:
                    pass

        # flattened columns fallback
        for c in lines_df.columns:
            cl = c.lower()
            if cl.endswith("_spread") or cl == "spread":
                v = pd.to_numeric(r.get(c), errors="coerce")
                if pd.notna(v):
                    spread_vals.append(float(v))
            if "over_under" in cl or "overunder" in cl or cl.endswith("_total"):
                v = pd.to_numeric(r.get(c), errors="coerce")
                if pd.notna(v):
                    total_vals.append(float(v))

        if spread_vals:
            spread = float(np.nanmean(spread_vals))
        else:
            spread = np.nan

        if total_vals:
            total = float(np.nanmean(total_vals))
        else:
            total = np.nan

        rows.append({
            "game_id": game_id,
            "home_spread": spread,
            "total_line": total,
            "line_count": len(spread_vals),
        })

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.groupby("game_id", as_index=False).agg({
        "home_spread": "mean",
        "total_line": "mean",
        "line_count": "max",
    })
    return out

def standardize_games(games_df, lines_std):
    id_col = first_col(games_df, ["id", "game_id"])
    season_col = first_col(games_df, ["season", "year"])
    week_col = first_col(games_df, ["week"])
    date_col = first_col(games_df, ["start_date", "start_time", "date"])
    home_col = first_col(games_df, ["home_team", "home"])
    away_col = first_col(games_df, ["away_team", "away"])
    hp_col = first_col(games_df, ["home_points", "home_score"])
    ap_col = first_col(games_df, ["away_points", "away_score"])

    required = [id_col, season_col, week_col, home_col, away_col, hp_col, ap_col]
    if any(x is None for x in required):
        raise SystemExit(f"Could not identify required game columns. Columns: {list(games_df.columns)}")

    out = pd.DataFrame({
        "game_id": games_df[id_col],
        "season": to_num(games_df[season_col]).astype("Int64"),
        "week": to_num(games_df[week_col]).astype("Int64"),
        "date": games_df[date_col] if date_col else "",
        "home_team": games_df[home_col].astype(str),
        "away_team": games_df[away_col].astype(str),
        "home_key": games_df[home_col].map(team_key),
        "away_key": games_df[away_col].map(team_key),
        "home_points": to_num(games_df[hp_col]),
        "away_points": to_num(games_df[ap_col]),
    })

    out = out[out["week"].isin(EARLY_WEEKS)].copy()
    out = out.merge(lines_std, on="game_id", how="left")

    out["home_margin"] = out["home_points"] - out["away_points"]
    out["away_margin"] = -out["home_margin"]

    # CFBD spread is treated as home spread. Negative means home favored.
    out["away_spread"] = -out["home_spread"]
    out["home_ats_margin"] = out["home_margin"] + out["home_spread"]
    out["away_ats_margin"] = out["away_margin"] + out["away_spread"]

    out["favorite_team"] = np.where(
        out["home_spread"] < 0, out["home_team"],
        np.where(out["home_spread"] > 0, out["away_team"], "")
    )
    out["underdog_team"] = np.where(
        out["home_spread"] < 0, out["away_team"],
        np.where(out["home_spread"] > 0, out["home_team"], "")
    )

    return out

def ats_result(margin):
    if pd.isna(margin):
        return ""
    if margin > 0:
        return "W"
    if margin < 0:
        return "L"
    return "P"

def build_historical(games, rp_std):
    rows = []

    for metric in ["overall", "offense", "defense"]:
        class_col = f"rp_{metric}_class"
        value_col = f"rp_{metric}"
        pct_col = f"rp_{metric}_pctile"

        if class_col not in rp_std.columns or rp_std[class_col].astype(str).eq("").all():
            continue

        rp_small = rp_std[["season", "team", "team_key", value_col, pct_col, class_col]].copy()
        rp_small = rp_small.rename(columns={
            "team": "rp_team",
            value_col: "rp_value",
            pct_col: "rp_pctile",
            class_col: "rp_class",
        })

        m = games.merge(
            rp_small.rename(columns={
                "rp_team": "home_rp_team",
                "team_key": "home_key",
                "rp_value": "home_rp_value",
                "rp_pctile": "home_rp_pctile",
                "rp_class": "home_rp_class",
            }),
            on=["season", "home_key"],
            how="left"
        ).merge(
            rp_small.rename(columns={
                "rp_team": "away_rp_team",
                "team_key": "away_key",
                "rp_value": "away_rp_value",
                "rp_pctile": "away_rp_pctile",
                "rp_class": "away_rp_class",
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
            high_margin = g[f"{high_side}_margin"]

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
                "high_rp_margin": high_margin,
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

    grp_cols = ["metric", "high_rp_role"]
    summary = hist.groupby(grp_cols, dropna=False).agg(
        games=("game_id", "count"),
        ats_w=("high_rp_ats_result", lambda x: int((x == "W").sum())),
        ats_l=("high_rp_ats_result", lambda x: int((x == "L").sum())),
        ats_p=("high_rp_ats_result", lambda x: int((x == "P").sum())),
        avg_ats_margin=("high_rp_ats_margin", "mean"),
        avg_spread=("high_rp_spread", "mean"),
        avg_rp_pctile_gap=("high_rp_pctile", "mean"),
    ).reset_index()

    denom = summary["ats_w"] + summary["ats_l"]
    summary["ats_pct"] = np.where(denom > 0, summary["ats_w"] / denom, np.nan)
    summary["ats_record"] = summary["ats_w"].astype(str) + "-" + summary["ats_l"].astype(str) + "-" + summary["ats_p"].astype(str)

    summary.to_csv(HIST_SUMMARY_OUT, index=False)
    return hist, summary

def load_2026_schedule():
    candidates = [
        ROOT / "data/projections/game_projection_blend_2026.csv",
        ROOT / "data/projections/game_projection_sources_2026.csv",
        ROOT / "game_projection_blend_2026.csv",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if not p:
        raise SystemExit("Could not find 2026 projection/schedule file.")

    df = pd.read_csv(p, low_memory=False)
    away_col = "away_team" if "away_team" in df.columns else "away"
    home_col = "home_team" if "home_team" in df.columns else "home"
    game_col = "game_id" if "game_id" in df.columns else None
    date_col = "date" if "date" in df.columns else None
    spread_col = next((c for c in ["blend_spread_home", "projected_margin_home", "model_spread_home"] if c in df.columns), None)

    out = pd.DataFrame({
        "game_id": df[game_col].astype(str) if game_col else df.index.astype(str),
        "date": df[date_col] if date_col else "",
        "away_team": df[away_col].astype(str),
        "home_team": df[home_col].astype(str),
        "away_key": df[away_col].map(team_key),
        "home_key": df[home_col].map(team_key),
        "home_edge": to_num(df[spread_col]) if spread_col else np.nan,
    })

    if date_col:
        out["date_dt"] = pd.to_datetime(out["date"], errors="coerce")
        min_date = out["date_dt"].min()
        out["days_from_first"] = (out["date_dt"] - min_date).dt.days
        out = out[out["days_from_first"].between(0, 28, inclusive="both")].copy()

    return out

def role_from_home_edge(home_edge, side):
    if pd.isna(home_edge) or abs(float(home_edge)) < 0.05:
        return "Pick"
    # project convention: positive = home favored
    if side == "home":
        return "Favorite" if home_edge > 0 else "Underdog"
    return "Underdog" if home_edge > 0 else "Favorite"

def strength_from_summary(row):
    if row is None or row.empty:
        return "Watch"
    games = float(row.get("games", 0))
    margin = float(row.get("avg_ats_margin", 0))
    ats_pct = row.get("ats_pct", np.nan)

    if games >= 20 and margin >= 2.5:
        return "Strong"
    if games >= 12 and margin >= 1.25:
        return "Medium"
    if games >= 8 and margin >= 0.5:
        return "Watch"
    return "Info"

def build_2026_signals(rp_std, summary):
    sched = load_2026_schedule()

    rp2026 = rp_std[rp_std["season"].astype(str).eq("2026")].copy()
    if rp2026.empty:
        print("WARNING: no 2026 RP rows. 2026 signals will be empty.")
        pd.DataFrame().to_csv(SIGNALS_OUT, index=False)
        return pd.DataFrame()

    signals = []

    for metric in ["overall", "offense", "defense"]:
        class_col = f"rp_{metric}_class"
        value_col = f"rp_{metric}"
        pct_col = f"rp_{metric}_pctile"

        if class_col not in rp2026.columns or rp2026[class_col].astype(str).eq("").all():
            continue

        rp_small = rp2026[["team", "team_key", value_col, pct_col, class_col]].copy()

        m = sched.merge(
            rp_small.rename(columns={
                "team": "home_rp_team",
                "team_key": "home_key",
                value_col: "home_rp_value",
                pct_col: "home_rp_pctile",
                class_col: "home_rp_class",
            }),
            on="home_key",
            how="left"
        ).merge(
            rp_small.rename(columns={
                "team": "away_rp_team",
                "team_key": "away_key",
                value_col: "away_rp_value",
                pct_col: "away_rp_pctile",
                class_col: "away_rp_class",
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
                (summary["metric"].astype(str).eq(metric)) &
                (summary["high_rp_role"].astype(str).eq(role))
            ]
            hist = hist_row.iloc[0] if not hist_row.empty else None

            if hist is not None:
                hist_games = int(hist["games"])
                hist_record = str(hist["ats_record"])
                hist_pct = float(hist["ats_pct"]) if pd.notna(hist["ats_pct"]) else np.nan
                hist_margin = float(hist["avg_ats_margin"]) if pd.notna(hist["avg_ats_margin"]) else np.nan
                strength = strength_from_summary(hist)
                supporting = f"Historical early-season high-{metric} RP {role}: {hist_record} ATS, {hist_pct:.1%}, {hist_margin:+.2f} ATS margin over {hist_games} games"
            else:
                hist_games = ""
                hist_record = ""
                hist_pct = np.nan
                hist_margin = np.nan
                strength = "Watch"
                supporting = "No matching historical summary row yet."

            headline = f"{high_team} early-season returning production edge"
            detail = (
                f"{high_team} is High {metric} RP vs {low_team} Low {metric} RP. "
                f"Projected role: {role}. {supporting}."
            )

            signals.append({
                "game_id": g["game_id"],
                "date": g["date"],
                "away_team": g["away_team"],
                "home_team": g["home_team"],
                "signal_group": "Returning Production",
                "signal_type": f"Early Season High-vs-Low {metric.title()} RP",
                "market": "Spread",
                "period": "Full Game",
                "team": high_team,
                "opponent": low_team,
                "direction": high_team,
                "strength": strength,
                "score": hist_margin,
                "confidence": "Medium" if hist_games and int(hist_games) >= 12 else "Low",
                "headline": headline,
                "detail": detail,
                "supporting_data": supporting,
                "source": "CFBD returning production + CFBD historical lines",
                "metric": metric,
                "projected_role": role,
                "team_rp_value": g[f"{high_side}_rp_value"],
                "opponent_rp_value": g[f"{low_side}_rp_value"],
                "team_rp_pctile": g[f"{high_side}_rp_pctile"],
                "opponent_rp_pctile": g[f"{low_side}_rp_pctile"],
                "historical_games": hist_games,
                "historical_ats_record": hist_record,
                "historical_ats_pct": hist_pct,
                "historical_avg_ats_margin": hist_margin,
            })

    out = pd.DataFrame(signals)
    out.to_csv(SIGNALS_OUT, index=False)

    # Add/replace this signal group in master game_betting_signals.csv.
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

    rp_raw = pull_returning_production()
    rp_std, picks = standardize_rp(rp_raw)

    games_raw, lines_raw = pull_games_and_lines()
    lines_std = extract_lines(lines_raw)
    games = standardize_games(games_raw, lines_std)

    hist, summary = build_historical(games, rp_std)
    signals = build_2026_signals(rp_std, summary)

    audit_rows = [
        {"metric": "rp_raw_rows", "value": len(rp_raw)},
        {"metric": "rp_standard_rows", "value": len(rp_std)},
        {"metric": "games_early_rows", "value": len(games)},
        {"metric": "historical_high_low_games", "value": len(hist)},
        {"metric": "historical_summary_rows", "value": len(summary)},
        {"metric": "returning_production_2026_signals", "value": len(signals)},
        {"metric": "overall_metric_col", "value": picks.get("overall") or ""},
        {"metric": "offense_metric_col", "value": picks.get("offense") or ""},
        {"metric": "defense_metric_col", "value": picks.get("defense") or ""},
    ]
    audit = pd.DataFrame(audit_rows)
    audit.to_csv(AUDIT_OUT, index=False)

    print("wrote:", RP_RAW_OUT, "rows:", len(rp_raw))
    print("wrote:", HIST_GAMES_OUT, "rows:", len(hist))
    print("wrote:", HIST_SUMMARY_OUT, "rows:", len(summary))
    print("wrote:", SIGNALS_OUT, "rows:", len(signals))
    print("wrote:", MASTER_SIGNALS_OUT)
    print("wrote:", AUDIT_OUT)
    print()
    print(audit.to_string(index=False))
    print()
    if not summary.empty:
        print("Historical summary:")
        print(summary.sort_values(["metric", "high_rp_role"]).to_string(index=False))
    print()
    if not signals.empty:
        cols = ["date", "away_team", "home_team", "signal_type", "team", "projected_role", "strength", "supporting_data"]
        print("2026 signal sample:")
        print(signals[cols].head(30).to_string(index=False))

if __name__ == "__main__":
    main()
