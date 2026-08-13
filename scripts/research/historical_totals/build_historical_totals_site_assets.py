#!/usr/bin/env python3
from pathlib import Path
import json
import math
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[3]

BACKBONE = ROOT / "data/research/historical/historical_game_model_market_matrix_2021_2025.csv"
MARKET = ROOT / "data/research/historical/the_odds_api/historical_actionable_market_states_2021_2025.csv"

SP = ROOT / "data/research/historical_totals/sp_plus/sp_plus_totals_game_level_2021_2025_final.csv"
SAG = ROOT / "data/research/historical_totals/sagarin/sagarin_totals_game_level_2021_2025_research_grade_repaired.csv"
MAS = ROOT / "data/research/historical_totals/massey/massey_totals_game_level_2021_2025.csv"
DR = ROOT / "data/research/historical_totals/dratings/dratings_provenance_safe_game_level_2021_2025.csv"

OUT_EDGE = ROOT / "data/site/historical_totals_edge_validation_2021_2025.csv"
OUT_MODELS = ROOT / "data/site/historical_totals_model_performance_2021_2025.json"

# Temporary smooth totals-specific CLV -> EV approximation.
# 1.0 point CLV ~= +2.8 percentage points of fair win probability.
# Assumes -110 benchmark pricing and no spread-style key-number adjustment.
TOTAL_POINT_WIN_PROB_VALUE = 0.028

THRESHOLDS = [
    0.5, 1.0, 1.5,
    2.0, 2.5, 3.0, 3.5, 4.0, 4.5,
    5.0, 6.0, 7.0, 8.0, 10.0,
]

SCOPES = [
    "2021-2025",
    "2021",
    "2022",
    "2023",
    "2024",
    "2025",
]

VIEWS = ["all", "3.0"]


def finite(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def american_profit(price):
    p = finite(price)
    if p is None or p == 0:
        return np.nan
    if p < 0:
        return 100.0 / abs(p)
    return p / 100.0


def approx_ev_from_clv(avg_clv):
    c = finite(avg_clv)
    if c is None:
        return np.nan

    fair_p = 0.50 + TOTAL_POINT_WIN_PROB_VALUE * c

    # Keep generic estimate within sane bounds.
    fair_p = min(max(fair_p, 0.01), 0.99)

    win_profit = 100.0 / 110.0

    return (
        fair_p * win_profit
        - (1.0 - fair_p)
    )


def scope_filter(df, scope):
    if scope == "2021-2025":
        return df.copy()

    return df[
        df["season"].eq(int(scope))
    ].copy()


def build_bets(df, model_col):
    x = df[
        df[model_col].notna()
        & df["actual_total_points"].notna()
        & df["best_us_over_total"].notna()
        & df["best_us_under_total"].notna()
    ].copy()

    x["model_total"] = pd.to_numeric(
        x[model_col],
        errors="coerce",
    )

    x["over_edge"] = (
        x["model_total"]
        - x["best_us_over_total"]
    )

    x["under_edge"] = (
        x["best_us_under_total"]
        - x["model_total"]
    )

    choose_over = (
        x["over_edge"] >= x["under_edge"]
    )

    x["side"] = np.where(
        choose_over,
        "OVER",
        "UNDER",
    )

    x["edge"] = np.where(
        choose_over,
        x["over_edge"],
        x["under_edge"],
    )

    x["bet_line"] = np.where(
        choose_over,
        x["best_us_over_total"],
        x["best_us_under_total"],
    )

    x["bet_price"] = np.where(
        choose_over,
        x["best_us_over_price"],
        x["best_us_under_price"],
    )

    over = x["side"].eq("OVER")
    under = x["side"].eq("UNDER")

    x["result"] = np.select(
        [
            over & (
                x["actual_total_points"]
                > x["bet_line"]
            ),
            over & (
                x["actual_total_points"]
                < x["bet_line"]
            ),
            under & (
                x["actual_total_points"]
                < x["bet_line"]
            ),
            under & (
                x["actual_total_points"]
                > x["bet_line"]
            ),
        ],
        ["W", "L", "W", "L"],
        default="P",
    )

    x["profit"] = np.where(
        x["result"].eq("W"),
        x["bet_price"].map(american_profit),
        np.where(
            x["result"].eq("L"),
            -1.0,
            0.0,
        ),
    )

    x["clv"] = np.where(
        over,
        x["closing_total"] - x["bet_line"],
        x["bet_line"] - x["closing_total"],
    )

    # Won line move excludes same-line closes.
    x["line_moved"] = (
        pd.to_numeric(x["clv"], errors="coerce")
        .abs()
        .gt(1e-12)
    )

    x["won_line_move"] = (
        pd.to_numeric(x["clv"], errors="coerce")
        .gt(1e-12)
    )

    return x


def summarize_bets(z):
    if not len(z):
        return {
            "games": 0,
            "wins": 0,
            "losses": 0,
            "pushes": 0,
            "record": "0-0-0",
            "win_pct": None,
            "roi": None,
            "beat_close_pct": None,
            "won_line_move_pct": None,
            "avg_clv": None,
        }

    wins = int(z["result"].eq("W").sum())
    losses = int(z["result"].eq("L").sum())
    pushes = int(z["result"].eq("P").sum())

    decisions = wins + losses

    clv = pd.to_numeric(
        z["clv"],
        errors="coerce",
    )

    moved = z[
        z["line_moved"]
    ]

    roi_denom = int(
        z["profit"].notna().sum()
    )

    return {
        "games": int(len(z)),
        "wins": wins,
        "losses": losses,
        "pushes": pushes,
        "record": f"{wins}-{losses}-{pushes}",
        "win_pct":
            wins / decisions
            if decisions else None,
        "roi":
            float(z["profit"].sum() / roi_denom)
            if roi_denom else None,
        "beat_close_pct":
            float((clv > 1e-12).mean())
            if clv.notna().any() else None,
        "won_line_move_pct":
            float(
                moved["won_line_move"].mean()
            )
            if len(moved) else None,
        "avg_clv":
            float(clv.mean())
            if clv.notna().any() else None,
    }


# ============================================================
# LOAD CANONICAL GAMES
# ============================================================

base = pd.read_csv(
    BACKBONE,
    low_memory=False,
)

base = base[
    [
        "game_id",
        "season",
        "week",
        "actual_total_points",
        "closing_total",
        "theodds_event_id",
    ]
].drop_duplicates("game_id").copy()

for c in [
    "actual_total_points",
    "closing_total",
]:
    base[c] = pd.to_numeric(
        base[c],
        errors="coerce",
    )


# ============================================================
# MODEL SOURCES
# ============================================================

sp = pd.read_csv(
    SP,
    low_memory=False,
)

sag = pd.read_csv(
    SAG,
    low_memory=False,
)

mas = pd.read_csv(
    MAS,
    low_memory=False,
)

dr = pd.read_csv(
    DR,
    low_memory=False,
)

sp_col = next(
    c for c in [
        "sp_plus_total",
        "projected_total",
        "total",
    ]
    if c in sp.columns
)

sag_col = next(
    c for c in [
        "sagarin_total",
        "projected_total",
        "total",
    ]
    if c in sag.columns
)

spx = sp[
    ["game_id", sp_col]
].drop_duplicates("game_id").copy()

spx["sp_plus"] = pd.to_numeric(
    spx[sp_col],
    errors="coerce",
)

sagx = sag[
    ["game_id", sag_col]
].drop_duplicates("game_id").copy()

sagx["sagarin"] = pd.to_numeric(
    sagx[sag_col],
    errors="coerce",
)

masx = mas[
    [
        "game_id",
        "massey_total",
        "away_pred",
        "home_pred",
    ]
].drop_duplicates("game_id").copy()

for c in [
    "massey_total",
    "away_pred",
    "home_pred",
]:
    masx[c] = pd.to_numeric(
        masx[c],
        errors="coerce",
    )

masx["massey_pred_sum"] = (
    masx["away_pred"]
    + masx["home_pred"]
)

masx["massey_dual"] = (
    masx["massey_total"]
    + masx["massey_pred_sum"]
) / 2.0

drx = dr[
    ["game_id", "dratings_total"]
].drop_duplicates("game_id").copy()

drx["dratings"] = pd.to_numeric(
    drx["dratings_total"],
    errors="coerce",
)


df = (
    base
    .merge(
        spx[["game_id", "sp_plus"]],
        on="game_id",
        how="left",
        validate="one_to_one",
    )
    .merge(
        masx[
            [
                "game_id",
                "massey_total",
                "massey_pred_sum",
                "massey_dual",
            ]
        ],
        on="game_id",
        how="left",
        validate="one_to_one",
    )
    .merge(
        sagx[["game_id", "sagarin"]],
        on="game_id",
        how="left",
        validate="one_to_one",
    )
    .merge(
        drx[["game_id", "dratings"]],
        on="game_id",
        how="left",
        validate="one_to_one",
    )
)


# ============================================================
# COMPOSITES
# ============================================================

df["sp_massey_core"] = np.where(
    df["sp_plus"].notna()
    & df["massey_dual"].notna(),
    (
        0.50 * df["sp_plus"]
        + 0.50 * df["massey_dual"]
    ),
    np.nan,
)

df["primary_40_40_20"] = np.where(
    df["sp_plus"].notna()
    & df["massey_dual"].notna()
    & df["sagarin"].notna(),
    (
        0.40 * df["sp_plus"]
        + 0.40 * df["massey_dual"]
        + 0.20 * df["sagarin"]
    ),
    np.nan,
)


# ============================================================
# SUNDAY 9 PM MARKET
# ============================================================

market = pd.read_csv(
    MARKET,
    low_memory=False,
)

market["theodds_event_id"] = (
    market["theodds_event_id"]
    .astype(str)
    .replace("nan", "")
)

event_map = (
    base[
        base["theodds_event_id"].notna()
    ]
    .assign(
        theodds_event_id=lambda x:
        x["theodds_event_id"].astype(str)
    )
    .drop_duplicates("theodds_event_id")
    .set_index("theodds_event_id")["game_id"]
)

market["game_id"] = (
    market["theodds_event_id"]
    .map(event_map)
)

m9 = market[
    market["market_state_slot"].eq(
        "SUN_9PM_ET"
    )
    & market["game_id"].notna()
].copy()

m9 = m9.drop_duplicates(
    "game_id"
)

for c in [
    "best_us_over_total",
    "best_us_over_price",
    "best_us_under_total",
    "best_us_under_price",
]:
    m9[c] = pd.to_numeric(
        m9[c],
        errors="coerce",
    )

df = df.merge(
    m9[
        [
            "game_id",
            "best_us_over_total",
            "best_us_over_price",
            "best_us_under_total",
            "best_us_under_price",
        ]
    ],
    on="game_id",
    how="left",
    validate="one_to_one",
)


# ============================================================
# PRIMARY TOTALS EDGE VALIDATION
# ============================================================

primary_bets = build_bets(
    df,
    "primary_40_40_20",
)

edge_rows = []

for threshold in THRESHOLDS:
    z = primary_bets[
        primary_bets["edge"] >= threshold
    ].copy()

    s = summarize_bets(z)

    ev = approx_ev_from_clv(
        s["avg_clv"]
    )

    edge_rows.append({
        "edge_threshold": threshold,
        "games": s["games"],
        "record": s["record"],
        "wins": s["wins"],
        "losses": s["losses"],
        "pushes": s["pushes"],
        "ou_pct": s["win_pct"],
        "actual_roi": s["roi"],
        "beat_close_pct": s["beat_close_pct"],
        "won_line_move_pct": s["won_line_move_pct"],
        "avg_clv_points": s["avg_clv"],
        "ev_pct": ev,
        "signal":
            "STRONG"
            if threshold >= 5
            else "ACTIONABLE"
            if threshold >= 4
            else "BET_SIGNAL"
            if threshold >= 3
            else "LEAN"
            if threshold >= 2
            else "",
        "model": "40/40/20 + Sagarin",
    })

edge_df = pd.DataFrame(
    edge_rows
)

OUT_EDGE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

edge_df.to_csv(
    OUT_EDGE,
    index=False,
)


# ============================================================
# MODEL PERFORMANCE
# ============================================================

MODELS = [
    (
        "40/40/20 + Sagarin",
        "primary_40_40_20",
        "PRIMARY",
        False,
    ),
    (
        "SP+/Massey 50/50",
        "sp_massey_core",
        "CORE",
        False,
    ),
    (
        "SP+",
        "sp_plus",
        None,
        False,
    ),
    (
        "Massey Total",
        "massey_total",
        None,
        False,
    ),
    (
        "Massey Pred Sum",
        "massey_pred_sum",
        None,
        False,
    ),
    (
        "Massey Dual",
        "massey_dual",
        None,
        False,
    ),
    (
        "Sagarin",
        "sagarin",
        None,
        False,
    ),
    (
        "DRatings",
        "dratings",
        None,
        True,
    ),
]


model_rows = []

for scope in SCOPES:
    scoped = scope_filter(
        df,
        scope,
    )

    for name, col, badge, limited in MODELS:
        bets = build_bets(
            scoped,
            col,
        )

        for view in VIEWS:
            if view == "all":
                z = bets.copy()
            else:
                z = bets[
                    bets["edge"] >= 3.0
                ].copy()

            s = summarize_bets(z)

            pred = pd.to_numeric(
                z["model_total"],
                errors="coerce",
            )

            actual = pd.to_numeric(
                z["actual_total_points"],
                errors="coerce",
            )

            err = pred - actual

            model_rows.append({
                "view": view,
                "scope": scope,
                "model": name,
                "badge": badge,
                "limited_coverage": limited,
                "games": s["games"],
                "wins": s["wins"],
                "losses": s["losses"],
                "pushes": s["pushes"],
                "ou_pct": s["win_pct"],
                "roi": s["roi"],
                "beat_close_pct": s["beat_close_pct"],
                "avg_clv": s["avg_clv"],
                "mae":
                    float(err.abs().mean())
                    if len(z) else None,
                "bias":
                    float(err.mean())
                    if len(z) else None,
            })


payload = {
    "schema":
        "historical-totals-model-performance-v1",
    "market_snapshot":
        "Sunday 9 PM ET",
    "seasons":
        "2021-2025",
    "primary_model": {
        "name":
            "40/40/20 + Sagarin",
        "weights": {
            "SP+": 0.40,
            "Massey Dual": 0.40,
            "Sagarin": 0.20,
        },
    },
    "core_model": {
        "name":
            "SP+/Massey 50/50",
        "weights": {
            "SP+": 0.50,
            "Massey Dual": 0.50,
        },
    },
    "totals_clv_ev_estimate": {
        "version":
            "totals-clv-ev-v1-generic",
        "fair_win_probability_per_total_point":
            TOTAL_POINT_WIN_PROB_VALUE,
        "benchmark_price":
            -110,
        "notes":
            "Temporary smooth approximation. No spread-style key-number adjustment. Replace with empirical totals point-value curve when validated.",
    },
    "rows":
        model_rows,
}

OUT_MODELS.write_text(
    json.dumps(
        payload,
        indent=2,
    )
    + "\n"
)


# ============================================================
# AUDIT
# ============================================================

print("=" * 110)
print("HISTORICAL TOTALS SITE ASSETS")
print("=" * 110)

print("\nPRIMARY EDGE TABLE:")
print(
    edge_df[
        [
            "edge_threshold",
            "games",
            "record",
            "ou_pct",
            "actual_roi",
            "avg_clv_points",
            "ev_pct",
            "signal",
        ]
    ].to_string(index=False)
)

print("\nMODEL ROWS:", len(model_rows))
print("expected:", len(MODELS) * len(SCOPES) * len(VIEWS))

print("\nMODEL COVERAGE — ALL YEARS / ALL GAMES:")

audit = pd.DataFrame(
    model_rows
)

print(
    audit[
        (audit["scope"] == "2021-2025")
        & (audit["view"] == "all")
    ][
        [
            "model",
            "games",
            "ou_pct",
            "roi",
            "avg_clv",
            "mae",
            "bias",
        ]
    ].to_string(index=False)
)

print("\nWROTE:")
print(OUT_EDGE)
print(OUT_MODELS)
