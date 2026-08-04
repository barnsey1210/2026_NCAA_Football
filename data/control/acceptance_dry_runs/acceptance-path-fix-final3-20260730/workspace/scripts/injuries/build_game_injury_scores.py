#!/usr/bin/env python3
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

INDEX = Path("index.html")
PLAYER_IMPORTANCE = Path("data/rosters/player_importance_2026_alert_ready.csv")
INJURY_EVENTS = Path("data/injuries/injury_events_normalized.csv")

TEAM_OUT = Path("data/injuries/team_injury_scores.csv")
GAME_OUT = Path("data/injuries/game_injury_alerts.csv")

STATUS_MULT = {
    "Out": 1.00,
    "Out For Season": 1.15,
    "OFS": 1.15,
    "Suspended": 1.00,
    "Doubtful": 0.75,
    "Questionable": 0.45,
    "Game Time Decision": 0.40,
    "GTD": 0.40,
    "Limited": 0.25,
    "Probable": 0.15,
    "Status Change": 0.10,
}

def norm_text(x):
    return re.sub(r"\s+", " ", str(x or "")).strip()

def player_key(name):
    s = norm_text(name)
    if "," in s:
        parts = [p.strip() for p in s.split(",", 1)]
        if len(parts) == 2:
            s = f"{parts[1]} {parts[0]}"
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def status_multiplier(status):
    s = norm_text(status).lower()
    if not s:
        return 0.0
    if "season" in s and "out" in s:
        return 1.15
    if "ofs" in s:
        return 1.15
    if "suspend" in s:
        return 1.0
    if "out" in s:
        return 1.0
    if "doubt" in s:
        return 0.75
    if "question" in s:
        return 0.45
    if "game time" in s or "gtd" in s:
        return 0.40
    if "limited" in s:
        return 0.25
    if "prob" in s:
        return 0.15
    return 0.10

def position_group(pos):
    p = norm_text(pos).upper()

    if p == "QB":
        return "QB"
    if p in {"RB", "FB"}:
        return "RB"
    if p.startswith("WR"):
        return "WR"
    if p.endswith("TE") or p == "TE":
        return "TE"
    if p in {"LT", "LG", "C", "RG", "RT", "OL"}:
        return "OL"
    if p in {"DE", "DT", "NT", "LDE", "RDE", "LDT", "RDT", "EDGE", "RUSH", "JACK", "WOLF", "BAN", "BUCK"}:
        return "DL/EDGE"
    if p in {"LB", "MLB", "WLB", "SLB", "OLB", "ILB", "SAM", "MIKE", "WILL", "STING"}:
        return "LB"
    if p in {"CB", "LCB", "RCB", "NB", "STAR", "HUSKY", "FCB", "BCB"}:
        return "CB/NB"
    if p in {"S", "SS", "FS", "SPUR", "ROVER"}:
        return "S"
    if p in {"PK", "KO", "PT", "LS", "H", "PR", "KR"}:
        return "ST"

    return "Other"

def extract_db():
    txt = INDEX.read_text(errors="ignore")
    m = re.search(r'<script id="db" type="application/json">(.*?)</script>', txt, flags=re.S)
    if not m:
        raise SystemExit("Could not find DB script in index.html")
    return json.loads(m.group(1))

def tier(score):
    score = float(score or 0)
    if score >= 10:
        return "Major"
    if score >= 6:
        return "High"
    if score >= 3:
        return "Medium"
    if score > 0:
        return "Low"
    return "None"

def backup_dropoff(players, team, player, pos, depth_rank, importance):
    try:
        depth_rank = int(depth_rank)
    except Exception:
        depth_rank = None

    same_pos = players[
        (players["team"].eq(team)) &
        (players["position"].astype(str).str.upper().eq(str(pos).upper()))
    ].copy()

    if depth_rank is not None:
        backups = same_pos[same_pos["depth_rank"] > depth_rank].sort_values("depth_rank")
    else:
        backups = same_pos[same_pos["player"].astype(str).ne(str(player))].sort_values("depth_rank")

    if backups.empty:
        return 1.5, ""

    next_row = backups.iloc[0]
    next_imp = float(next_row.get("importance_score", 0) or 0)
    drop = max(0.0, float(importance or 0) - next_imp)
    return drop, norm_text(next_row.get("player"))

def main():
    built_at = datetime.now(timezone.utc).isoformat()

    db = extract_db()
    games = pd.DataFrame(db.get("games", []))
    if games.empty:
        raise SystemExit("No games found in index DB")

    teams = sorted(set(games["home_team"].dropna()) | set(games["away_team"].dropna()))

    players = pd.read_csv(PLAYER_IMPORTANCE)
    players["player_key"] = players["player"].map(player_key)
    players["position_group"] = players["position"].map(position_group)

    if INJURY_EVENTS.exists() and INJURY_EVENTS.stat().st_size > 0:
        events = pd.read_csv(INJURY_EVENTS)
    else:
        events = pd.DataFrame()

    scored_events = []

    if not events.empty:
        usable = events.copy()

        usable = usable[usable.get("team", "").notna()] if "team" in usable.columns else pd.DataFrame()
        if not usable.empty and "player" in usable.columns:
            usable = usable[usable["player"].notna()].copy()
        else:
            usable = pd.DataFrame()

        for _, e in usable.iterrows():
            team = norm_text(e.get("team"))
            player = norm_text(e.get("player"))
            status = norm_text(e.get("status"))
            pos = norm_text(e.get("position"))

            if not team or not player:
                continue

            key = player_key(player)
            cand = players[(players["team"].eq(team)) & (players["player_key"].eq(key))].copy()

            if cand.empty and pos:
                cand = players[
                    (players["team"].eq(team)) &
                    (players["position"].astype(str).str.upper().eq(pos.upper())) &
                    (players["player_key"].str.contains(key, regex=False, na=False))
                ].copy()

            if cand.empty:
                importance = 1.0
                depth_rank = None
                role = ""
                position = pos
                group = position_group(pos)
                matched = False
                next_player = ""
                dropoff = 0.5
            else:
                cand = cand.sort_values(["importance_score", "depth_rank"], ascending=[False, True])
                p = cand.iloc[0]
                importance = float(p.get("importance_score", 0) or 0)
                depth_rank = p.get("depth_rank")
                role = norm_text(p.get("role"))
                position = norm_text(p.get("position")) or pos
                group = position_group(position)
                matched = True
                dropoff, next_player = backup_dropoff(players, team, p.get("player"), position, depth_rank, importance)

            mult = status_multiplier(status)
            impact = round((importance * mult) + min(3.0, dropoff * 0.65 * mult), 2)

            scored_events.append({
                "built_at": built_at,
                "team": team,
                "player": player,
                "position": position,
                "position_group": group,
                "status": status,
                "matched_depth_chart_player": matched,
                "importance_score": round(importance, 2),
                "status_multiplier": mult,
                "backup_dropoff": round(dropoff, 2),
                "next_player": next_player,
                "injury_impact": impact,
                "source": norm_text(e.get("source")),
                "item_title": norm_text(e.get("item_title")),
                "item_url": norm_text(e.get("item_url")),
                "raw_text": norm_text(e.get("raw_text"))[:500],
            })

    event_df = pd.DataFrame(scored_events)

    team_rows = []
    for team in teams:
        x = event_df[event_df["team"].eq(team)].copy() if not event_df.empty else pd.DataFrame()

        base_score = float(x["injury_impact"].sum()) if not x.empty else 0.0

        stack_penalty = 0.0
        if not x.empty:
            for group, gx in x.groupby("position_group"):
                if len(gx) >= 2 and group in {"OL", "DL/EDGE", "LB", "CB/NB", "S", "WR"}:
                    stack_penalty += 0.75 * (len(gx) - 1)

        score = round(min(25.0, base_score + stack_penalty), 2)

        top = []
        if not x.empty:
            for _, r in x.sort_values("injury_impact", ascending=False).head(5).iterrows():
                top.append(f"{r['player']} {r['status']} ({r['position']}, {r['injury_impact']})")

        team_rows.append({
            "built_at": built_at,
            "team": team,
            "injury_score": score,
            "injury_tier": tier(score),
            "injury_count": len(x),
            "stack_penalty": round(stack_penalty, 2),
            "top_injuries": "; ".join(top),
        })

    team_scores = pd.DataFrame(team_rows)

    score_map = team_scores.set_index("team").to_dict("index")

    game_rows = []
    for _, g in games.iterrows():
        away = norm_text(g.get("away_team"))
        home = norm_text(g.get("home_team"))

        away_s = score_map.get(away, {})
        home_s = score_map.get(home, {})

        away_score = float(away_s.get("injury_score", 0) or 0)
        home_score = float(home_s.get("injury_score", 0) or 0)

        game_score = max(away_score, home_score)
        injury_edge_home = round(away_score - home_score, 2)

        parts = []
        if away_score > 0:
            parts.append(f"{away}: {away_score} ({away_s.get('injury_tier')}) {away_s.get('top_injuries')}")
        if home_score > 0:
            parts.append(f"{home}: {home_score} ({home_s.get('injury_tier')}) {home_s.get('top_injuries')}")

        game_rows.append({
            "built_at": built_at,
            "game_id": g.get("game_id"),
            "week": g.get("week"),
            "date": g.get("date"),
            "away_team": away,
            "home_team": home,
            "away_injury_score": away_score,
            "home_injury_score": home_score,
            "game_injury_score": round(game_score, 2),
            "game_injury_tier": tier(game_score),
            "injury_edge_home": injury_edge_home,
            "injury_summary": " | ".join(parts),
        })

    game_alerts = pd.DataFrame(game_rows)

    TEAM_OUT.parent.mkdir(parents=True, exist_ok=True)
    GAME_OUT.parent.mkdir(parents=True, exist_ok=True)

    team_scores.to_csv(TEAM_OUT, index=False)
    game_alerts.to_csv(GAME_OUT, index=False)

    print("injury events scored:", len(event_df))
    print("team scores:", len(team_scores))
    print("games scored:", len(game_alerts))
    print("teams with injury score:", int((team_scores["injury_score"] > 0).sum()))
    print("games with injury alert:", int((game_alerts["game_injury_score"] > 0).sum()))
    print("wrote:", TEAM_OUT)
    print("wrote:", GAME_OUT)

    if not event_df.empty:
        print("\nTOP EVENT IMPACTS")
        print(event_df.sort_values("injury_impact", ascending=False).head(25).to_string(index=False))

if __name__ == "__main__":
    main()
