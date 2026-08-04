#!/usr/bin/env python3
"""Test whether contemporaneous weekly SP+ improves opener-to-close forecasts."""
from itertools import combinations
from pathlib import Path
import difflib
import json
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PT = ROOT / "data/import/prediction_tracker"
SP_FILES = [
    ROOT / "data/import/sp_plus/espn_sp_plus_weekly_2021_2024.csv",
    ROOT / "data/import/sp_plus/espn_sp_plus_weekly_2025.csv",
]
OUT = ROOT / "data/research/prediction_tracker_close_movement_blend_with_spplus_2021_2025"
BASE = {"FPI": "lineespn", "TeamRankings": "lineteamrank", "Sagarin Predictor": "linesagpred", "Massey": "linemass"}


def norm(value):
    value = str(value).lower().replace("&", "and")
    value = re.sub(r"\bst\.?\b", "state", value)
    value = re.sub(r"\bn\.?\b", "north", value)
    value = re.sub(r"\bs\.?\b", "south", value)
    return re.sub(r"[^a-z0-9]", "", value)


ALIASES = {
    "appalachianstate": "appstate", "arizonastate": "arizonastate", "ballstate": "ballstate",
    "boisestate": "boisestate", "bostoncollege": "bostoncollege", "bowlinggreen": "bowlinggreen",
    "centralflorida": "ucf", "connecticut": "uconn", "floridainternational": "fiu",
    "georgiasouthern": "gasouthern", "georgiastate": "gastate", "louisiana": "louisianalafayette",
    "louisianamonroe": "ulmonroe", "massachusetts": "umass", "miamifl": "miamiflorida",
    "miamioh": "miamiohio", "middletennessee": "middletennesseestate", "mississippi": "olemiss",
    "nevadaLasVegas": "unlv", "northcarolinastate": "ncstate", "southerncalifornia": "usc",
    "southernmississippi": "southernmiss", "texassanmarcos": "texasstate",
    "texaselpaso": "utep", "texassananatonio": "utsa", "westernkentucky": "wku",
}
ALIASES = {norm(k): norm(v) for k, v in ALIASES.items()}


def weight_grid(n, step=.05):
    units = round(1 / step)
    for bars in combinations(range(units + n - 1), n - 1):
        cuts = (-1,) + bars + (units + n - 1,)
        yield np.array([cuts[i + 1] - cuts[i] - 1 for i in range(n)], float) / units


def metrics(d, pred):
    close = d.line.to_numpy(float); opener = d.lineopen.to_numpy(float)
    actual_move = close - opener; predicted_move = pred - opener
    moved = np.abs(actual_move) >= .5; called = np.abs(predicted_move) >= .25; eligible = moved & called
    return {
        "n": len(d), "close_mae": float(np.mean(np.abs(pred-close))),
        "opener_mae": float(np.mean(np.abs(opener-close))),
        "movement_direction_accuracy_called": float(np.mean(np.sign(predicted_move[eligible]) == np.sign(actual_move[eligible]))) if eligible.any() else None,
        "direction_n_called": int(eligible.sum()),
    }


def fit(train, cols):
    x = train[cols].to_numpy(float); opener = train.lineopen.to_numpy(float); close = train.line.to_numpy(float)
    best = None
    for weights in weight_grid(len(cols)):
        blend = x @ weights
        for response in np.arange(0, 1.5001, .05):
            pred = opener + response * (blend-opener)
            loss = np.mean(np.abs(pred-close))
            if best is None or loss < best[0]: best = (loss, weights, float(response))
    return best


def fit_fair_line(train, cols):
    x=train[cols].to_numpy(float); close=train.line.to_numpy(float)
    best=None
    for weights in weight_grid(len(cols)):
        pred=x@weights; loss=np.mean(np.abs(pred-close))
        if best is None or loss < best[0]: best=(loss,weights)
    return best


def movement_metrics(d, fair):
    opener=d.lineopen.to_numpy(float); close=d.line.to_numpy(float)
    gap=fair-opener; move=close-opener
    eligible=(np.abs(gap)>=.5)&(np.abs(move)>=.5)
    return {"eligible_n":int(eligible.sum()),"direction_accuracy":float(np.mean(np.sign(gap[eligible])==np.sign(move[eligible]))) if eligible.any() else None,
            "mean_abs_opening_gap":float(np.mean(np.abs(gap))),"mean_abs_actual_move":float(np.mean(np.abs(move)))}


def add_spplus(games):
    sp = pd.concat([pd.read_csv(path) for path in SP_FILES], ignore_index=True)
    sp["key"] = sp.team.map(norm).replace(ALIASES)
    available = set(sp.key)
    game_names = sorted(set(games.Home) | set(games.Road))
    mapping = {}
    for name in game_names:
        key = ALIASES.get(norm(name), norm(name))
        if key not in available:
            match = difflib.get_close_matches(key, available, n=1, cutoff=.84)
            key = match[0] if match else None
        mapping[name] = key
    snapshots = {(int(s), int(w)): z.set_index("key").sp_plus.to_dict() for (s,w),z in sp.groupby(["season","snapshot_week"])}
    weeks = {s: sorted(w for ss,w in snapshots if ss == s) for s in games.season.unique()}
    projections=[]; used=[]
    for row in games.itertuples():
        target = max(0, int(row.week)-1)
        prior = [w for w in weeks.get(row.season, []) if w <= target]
        snap = max(prior) if prior else None
        ratings = snapshots.get((row.season, snap), {})
        home = ratings.get(mapping.get(row.Home)); road = ratings.get(mapping.get(row.Road))
        # Prediction Tracker convention: positive means the home team is favored.
        projections.append((home-road+2.5) if home is not None and road is not None else np.nan)
        used.append(snap)
    games["linespplus"] = projections; games["spplus_snapshot_week"] = used
    return games, mapping


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    games=[]
    for season in range(2021, 2026):
        z=pd.read_csv(PT/f"ncaa{season}.csv"); z["season"]=season; games.append(z)
    d=pd.concat(games, ignore_index=True)
    d, mapping = add_spplus(d)
    base_cols=list(BASE.values()); all_cols=base_cols+["linespplus"]
    needed=all_cols+["lineopen","line"]
    d[needed]=d[needed].apply(pd.to_numeric, errors="coerce")
    joined=d.dropna(subset=needed).copy()
    train=joined[joined.season <= 2023]; val=joined[joined.season == 2024]; hold=joined[joined.season == 2025]
    results={}
    for label,cols in [("four_system",base_cols),("four_system_plus_spplus",all_cols)]:
        _,fair_w=fit_fair_line(train,cols)
        fair=lambda z: z[cols].to_numpy(float)@fair_w
        fair_train=fair(train)
        # Calibrate only how much the close historically moves from opener toward fair value.
        opener=train.lineopen.to_numpy(float); close=train.line.to_numpy(float)
        gap=fair_train-opener
        k_grid=np.arange(0,1.5001,.05)
        k=float(min(k_grid,key=lambda x:np.mean(np.abs(opener+x*gap-close))))
        pred=lambda z: z.lineopen.to_numpy(float)+k*(fair(z)-z.lineopen.to_numpy(float))
        names=list(BASE) + (["SP+"] if len(cols)==5 else [])
        results[label]={"fair_line_weights":dict(zip(names,map(float,fair_w))),"convergence_response":k}
        for split,z in [("development",train),("validation_2024",val),("holdout_2025",hold)]:
            fp=fair(z)
            results[label][split]={"fair_line_vs_close":metrics(z,fp),"opening_gap_signal":movement_metrics(z,fp),"predicted_close":metrics(z,pred(z))}
    for label,cols in [("equal_fpi_teamrankings_spplus",["lineespn","lineteamrank","linespplus"]),("equal_all_five",all_cols)]:
        fair=lambda z: z[cols].mean(axis=1).to_numpy(float)
        opener=train.lineopen.to_numpy(float); close=train.line.to_numpy(float); gap=fair(train)-opener
        k=float(min(np.arange(0,1.5001,.05),key=lambda x:np.mean(np.abs(opener+x*gap-close))))
        pred=lambda z: z.lineopen.to_numpy(float)+k*(fair(z)-z.lineopen.to_numpy(float))
        results[label]={"fair_line_weights":"equal","convergence_response":k}
        for split,z in [("development",train),("validation_2024",val),("holdout_2025",hold)]:
            fp=fair(z); results[label][split]={"fair_line_vs_close":metrics(z,fp),"opening_gap_signal":movement_metrics(z,fp),"predicted_close":metrics(z,pred(z))}
    summary={
        "design":{"development":"2021-2023","validation":"2024","holdout":"2025 untouched","spplus_timing":"game week W uses latest ESPN snapshot <= W-1","home_field_adjustment":2.5,"line_convention":"positive means home favored","fair_line_target":"closing home line","movement_formula":"open + response * (independent fair line - open)"},
        "coverage":{"joined_games":len(joined),"development":len(train),"validation_2024":len(val),"holdout_2025":len(hold),"missing_from_full_rows":int(len(d)-len(joined))},
        "results":results,
    }
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    (OUT/"team_name_mapping.json").write_text(json.dumps(mapping,indent=2,sort_keys=True)+"\n")
    joined.to_csv(OUT/"joined_games.csv",index=False)
    (OUT/"README.md").write_text("# Weekly SP+ fair-line and opener-to-close test\n\nSP+ values are aligned without lookahead: Week W games use the latest ESPN rating table published after Week W-1 or earlier. Weights and convergence were selected on 2021-23, checked on 2024, and evaluated once on the recovered weekly 2025 archive.\n\n```json\n"+json.dumps(summary,indent=2)+"\n```\n")
    print(json.dumps(summary,indent=2))


if __name__ == "__main__": main()
