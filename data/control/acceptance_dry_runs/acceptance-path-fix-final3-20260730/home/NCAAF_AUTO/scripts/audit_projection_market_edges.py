#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np
import json
import re

ROOT = Path(".")
OUT = ROOT / "data/audit/projection_market_edge_audit.csv"
SUMMARY = ROOT / "data/audit/projection_market_edge_audit_summary.csv"

def first_present(row, cols):
    for c in cols:
        if c in row.index:
            v = row[c]
            if pd.notna(v) and str(v).strip() != "":
                return v, c
    return None, None

def num(v):
    if v is None:
        return np.nan
    if isinstance(v, str):
        vv = v.strip().upper()
        if vv in ["", "NA", "N/A", "NONE", "NULL", "—"]:
            return np.nan
        if vv in ["PK", "PICK", "PICKEM", "PICK'EM"]:
            return 0.0
        vv = vv.replace("+", "")
        try:
            return float(vv)
        except Exception:
            return np.nan
    try:
        return float(v)
    except Exception:
        return np.nan

def calc_home_market_spread(row):
    # Site convention from JS:
    # marketSpread is home-team perspective.
    # negative = home favored, positive = away favored.
    v, src = first_present(row, [
        "market_spread_home",
        "sgo_home_spread",
        "market_home_spread",
        "market_spread",
        "sgo_spread_home",
        "spread_home",
    ])
    return num(v), src, v

def calc_projection_home_margin(row):
    # Positive = home projected to win/favored.
    v, src = first_present(row, [
        "projected_margin_home",
        "blend_spread_home",
        "home_edge",
    ])
    return num(v), src, v

def calc_market_total(row):
    v, src = first_present(row, [
        "market_total",
        "sgo_total",
        "total_market",
        "consensus_total",
    ])
    return num(v), src, v

def calc_projected_total(row):
    v, src = first_present(row, [
        "projected_total",
        "blend_total",
        "total_projection",
    ])
    return num(v), src, v

def side_from_edge(home_edge, away, home):
    if pd.isna(home_edge):
        return ""
    if abs(home_edge) < 1e-9:
        return "No edge"
    return home if home_edge > 0 else away

def main():
    # Prefer game projection blend. This is the canonical projection file.
    p = ROOT / "data/projections/game_projection_blend_2026.csv"
    if not p.exists():
        raise SystemExit(f"Missing {p}")

    df = pd.read_csv(p, low_memory=False)

    rows = []
    for _, r in df.iterrows():
        away = r.get("away_team")
        home = r.get("home_team")

        proj_margin_home, proj_src, proj_raw = calc_projection_home_margin(r)
        market_spread_home, market_src, market_raw = calc_home_market_spread(r)

        # For ATS edge:
        # projected_margin_home positive = home by X.
        # market_spread_home negative = home laying points.
        # home ATS value = projected_margin_home + market_spread_home.
        # Example Stanford projected +3.4, market 0 => home edge +3.4.
        ats_edge_home = (
            proj_margin_home + market_spread_home
            if pd.notna(proj_margin_home) and pd.notna(market_spread_home)
            else np.nan
        )

        proj_total, proj_total_src, proj_total_raw = calc_projected_total(r)
        market_total, market_total_src, market_total_raw = calc_market_total(r)
        total_edge = (
            proj_total - market_total
            if pd.notna(proj_total) and pd.notna(market_total)
            else np.nan
        )

        rows.append({
            "game_id": r.get("game_id"),
            "week": r.get("week"),
            "date": r.get("date"),
            "away_team": away,
            "home_team": home,

            "projection_margin_home": proj_margin_home,
            "projection_margin_home_source": proj_src,
            "projection_margin_home_raw": proj_raw,

            "market_spread_home": market_spread_home,
            "market_spread_home_source": market_src,
            "market_spread_home_raw": market_raw,

            "ats_edge_home": ats_edge_home,
            "ats_edge_side": side_from_edge(ats_edge_home, away, home),

            "projected_total": proj_total,
            "projected_total_source": proj_total_src,
            "projected_total_raw": proj_total_raw,

            "market_total": market_total,
            "market_total_source": market_total_src,
            "market_total_raw": market_total_raw,

            "total_edge": total_edge,
            "total_side": "" if pd.isna(total_edge) else ("Over" if total_edge > 0 else "Under" if total_edge < 0 else "No edge"),

            "has_projection_spread": pd.notna(proj_margin_home),
            "has_market_spread": pd.notna(market_spread_home),
            "has_ats_edge": pd.notna(ats_edge_home),

            "has_projection_total": pd.notna(proj_total),
            "has_market_total": pd.notna(market_total),
            "has_total_edge": pd.notna(total_edge),

            "possible_pk_bug": (
                pd.notna(proj_margin_home)
                and market_raw is not None
                and str(market_raw).strip().upper() in ["0", "0.0", "+0", "+0.0", "-0", "-0.0", "PK", "PICK", "PICKEM", "PICK'EM"]
                and pd.isna(ats_edge_home)
            ),
        })

    out = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    summary_rows = [
        {"metric": "games", "value": len(out)},
        {"metric": "has_projection_spread", "value": int(out["has_projection_spread"].sum())},
        {"metric": "has_market_spread", "value": int(out["has_market_spread"].sum())},
        {"metric": "has_ats_edge", "value": int(out["has_ats_edge"].sum())},
        {"metric": "missing_ats_edge_but_has_projection", "value": int((out["has_projection_spread"] & ~out["has_ats_edge"]).sum())},
        {"metric": "has_projection_total", "value": int(out["has_projection_total"].sum())},
        {"metric": "has_market_total", "value": int(out["has_market_total"].sum())},
        {"metric": "has_total_edge", "value": int(out["has_total_edge"].sum())},
        {"metric": "missing_total_edge_but_has_projection", "value": int((out["has_projection_total"] & ~out["has_total_edge"]).sum())},
        {"metric": "possible_pk_bug", "value": int(out["possible_pk_bug"].sum())},
    ]

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(SUMMARY, index=False)

    print("wrote:", OUT)
    print("wrote:", SUMMARY)
    print()
    print(summary.to_string(index=False))

    print("\nHawaii / Stanford:")
    hs = out[
        out["away_team"].astype(str).eq("Hawaii") &
        out["home_team"].astype(str).eq("Stanford")
    ]
    print(hs.to_string(index=False))

    print("\nGames with projection spread but no ATS edge:")
    miss = out[out["has_projection_spread"] & ~out["has_ats_edge"]]
    cols = [
        "week","date","away_team","home_team",
        "projection_margin_home","market_spread_home_raw",
        "market_spread_home_source","possible_pk_bug"
    ]
    print(miss[cols].head(100).to_string(index=False))

    print("\nTop ATS edges by absolute value:")
    show = out[out["has_ats_edge"]].copy()
    show["abs_edge"] = show["ats_edge_home"].abs()
    cols2 = [
        "week","date","away_team","home_team",
        "projection_margin_home","market_spread_home",
        "ats_edge_home","ats_edge_side"
    ]
    print(show.sort_values("abs_edge", ascending=False)[cols2].head(50).to_string(index=False))

if __name__ == "__main__":
    main()
