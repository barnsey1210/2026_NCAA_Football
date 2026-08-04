#!/usr/bin/env python3
"""Join weekly official CFP ranks to contemporaneous eight-metric resumes."""
from __future__ import annotations

import re
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RANKS = ROOT / "data/models/cfp_weekly_rankings_official_2021_2024.csv"
GAMES = ROOT / "data/research/pbp_market_modeling_2021_2025/full_game_modeling_rows.csv"
GC = ROOT / "data/research/game_control_history_2021_2025/team_game_game_control.csv"
OUT = ROOT / "data/models/cfp_weekly_rankings_history.csv"
ALIASES = {"Miami": "Miami-FL", "Southern California": "USC", "Mississippi": "Ole Miss"}


def team(value): return ALIASES.get(str(value), str(value))


def ranking_date(season, label):
    clean = re.sub(r"SELECTION DAY\s*", "", str(label), flags=re.I).title()
    return pd.to_datetime(f"{clean} {int(season)}")


def main():
    ranks = pd.read_csv(RANKS)
    ranks["team"] = ranks.team.map(team)
    ranks["cutoff"] = [ranking_date(s, d) for s, d in zip(ranks.season, ranks.ranking_date)]
    games = pd.read_csv(GAMES, usecols=["game_id", "season", "week", "start_date", "home_team", "away_team", "home_score", "away_score"])
    games = games.drop_duplicates(["game_id"]).copy()
    games["start_date"] = pd.to_datetime(games.start_date, utc=True).dt.tz_localize(None)
    games["home_team"] = games.home_team.map(team); games["away_team"] = games.away_team.map(team)
    gc = pd.read_csv(GC, usecols=["game_id", "team", "raw_game_control"])
    gc["team"] = gc.team.map(team); gc["game_id"] = gc.game_id.astype(str)
    gc_map = {(r.game_id, r.team): float(r.raw_game_control) for r in gc.itertuples()}
    rows = []
    prior_top25_by_season = {}
    for (season, release), poll in ranks.groupby(["season", "release_index"]):
        snapshot_start = len(rows)
        cutoff = poll.cutoff.iloc[0]
        played = games[(games.season == season) & (games.start_date < cutoff)].copy()
        records = []
        for g in played.itertuples():
            hs, aas = float(g.home_score), float(g.away_score)
            for name, opp, scored, allowed, venue in [(g.home_team, g.away_team, hs, aas, "home"), (g.away_team, g.home_team, aas, hs, "away")]:
                records.append({"game_id": str(g.game_id), "team": name, "opponent": opp, "margin": scored-allowed, "venue": venue,
                                "raw_gc": gc_map.get((str(g.game_id), name), 1/(1+np.exp(-(scored-allowed)/12)))})
        frame = pd.DataFrame(records)
        if frame.empty: continue
        wins = frame.assign(win=frame.margin > 0).groupby("team").win.agg(["sum", "count"])
        wp = (wins["sum"] / wins["count"]).to_dict()
        opponents = frame.groupby("team").opponent.apply(list).to_dict()
        opp_wp = {t: np.mean([wp.get(o, .5) for o in os]) for t, os in opponents.items()}
        current_top25 = set(poll.team)
        prior_top25 = prior_top25_by_season.get(season, set())
        actual = dict(zip(poll.team, poll.actual_cfp_rank))
        for name, group in frame.groupby("team"):
            opps = list(group.opponent)
            venue_wp = [np.clip(wp.get(o,.5) + (.025 if v=="away" else -.025),0,1) for o,v in zip(group.opponent,group.venue)]
            sos = (2/3)*np.mean(venue_wp) + (1/3)*np.mean([opp_wp.get(o,.5) for o in opps])
            win_rows, loss_rows = group[group.margin>0], group[group.margin<0]
            mol = [abs(r.margin) * (.6 + .8*(1-wp.get(r.opponent,.5))) for r in loss_rows.itertuples()]
            raw_gc = float(group.raw_gc.mean())
            game_control = float(np.clip(raw_gc + .35*(sos-.5),0,1))
            rows.append({"season":season,"week":release,"ranking_date":cutoff.date(),"team":name,
                "actual_cfp_rank":int(actual.get(name,26)),"raw_game_control":raw_gc,"game_control":game_control,"game_control_rank":0,
                "game_control_index":100.0*(game_control-.5),"wins":int(len(win_rows)),"losses":int(len(loss_rows)),
                "game_control_method":"PBP AUC + 0.35*(SOS-.500)","championship_wins_power":0,"championship_wins_g6":0,
                "quality_wins":int(sum(wp.get(o,.5)>.5 for o in win_rows.opponent)),
                "top25_wins":int(sum(o in current_top25 for o in win_rows.opponent)),
                "prior_top25_wins":int(sum(o in prior_top25 for o in win_rows.opponent)),
                "provisional_top25_wins":0,
                "avg_capped_mov":float(np.minimum(win_rows.margin,21).mean()) if len(win_rows) else 0,
                "avg_weighted_mol":float(np.mean(mol)) if mol else 0,"bad_losses":int(sum(wp.get(o,.5)<=.5 for o in loss_rows.opponent)),
                "sos":float(sos),"source_url":poll.source_url.iloc[0],"notes":"Championship flags pending conference-title crosswalk"})
        snapshot = rows[snapshot_start:]
        provisional = pd.DataFrame(snapshot)
        provisional["gc_pct"] = provisional.game_control.rank(pct=True, method="average")
        provisional["qw_pct"] = provisional.quality_wins.rank(pct=True, method="average")
        provisional_top25 = set(provisional.assign(score=.8*provisional.gc_pct+.2*provisional.qw_pct).nlargest(25,"score").team)
        wins_by_team = frame[frame.margin>0].groupby("team").opponent.apply(list).to_dict()
        for row in snapshot:
            row["provisional_top25_wins"] = int(sum(o in provisional_top25 for o in wins_by_team.get(row["team"],[])))
        prior_top25_by_season[season] = current_top25
    out = pd.DataFrame(rows)
    out["game_control_rank"] = out.groupby(["season","week"]).game_control.rank(ascending=False,method="min").astype(int)
    OUT.parent.mkdir(parents=True,exist_ok=True); out.to_csv(OUT,index=False)
    print(f"Wrote {len(out)} team-week validation rows to {OUT}")
    print(f"Official ranked rows represented: {(out.actual_cfp_rank<=25).sum()}")


if __name__ == "__main__": main()
