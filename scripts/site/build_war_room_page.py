#!/usr/bin/env python3

import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "war-room.html"
CONTROL_CONFIG = ROOT / "config/war_room_control_plane.json"
control_config = json.loads(CONTROL_CONFIG.read_text()) if CONTROL_CONFIG.exists() else {}
CONTROL_BASE_URL = control_config.get("control_base_url")
POLL_SECONDS = max(1, int(control_config.get("browser_version_poll_seconds", 2)))


def normalized_team_name(value):
    ascii_value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", ascii_value.lower())


def load_team_abbreviations():
    """Load presentation abbreviations from the canonical ESPN team lookup."""
    lookup_path = ROOT / "logos/espn_team_lookup.csv"
    matrix_path = ROOT / "data/site/war_room_market_matrix.json"
    if not lookup_path.exists() or not matrix_path.exists():
        return {}

    matrix = json.loads(matrix_path.read_text())
    teams = {
        game.get(side)
        for game in matrix.get("games", [])
        for side in ("away_team", "home_team")
        if game.get(side)
    }
    with lookup_path.open(newline="", encoding="utf-8") as handle:
        lookup = list(csv.DictReader(handle))

    abbreviations = {}
    for team in sorted(teams):
        canonical = normalized_team_name(team)
        exact = [
            row for row in lookup
            if normalized_team_name(row.get("shortDisplayName")) == canonical
        ]
        candidates = exact or [
            row for row in lookup
            if normalized_team_name(row.get("displayName", "")).startswith(canonical)
        ]
        if len(candidates) == 1 and candidates[0].get("abbreviation"):
            abbreviations[team] = candidates[0]["abbreviation"]
    return abbreviations


TEAM_ABBREVIATIONS = load_team_abbreviations()

HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>2026 NCAAF War Room</title>

<style>
:root{
  --bg:#071019;
  --panel:#0c1722;
  --panel2:#101d29;
  --line:#263849;
  --line2:#33495c;
  --text:#e7edf4;
  --muted:#8294a6;
  --green:#39e89a;
  --yellow:#f4cd4b;
  --red:#ff5d70;
  --cyan:#45d9ed;
  --blue:#4fa3ff;
  --purple:#b67cff;
}

*{box-sizing:border-box}

body{
  margin:0;
  background:var(--bg);
  color:var(--text);
  font-family:
    ui-monospace,
    SFMono-Regular,
    Menlo,
    Monaco,
    Consolas,
    monospace;
  font-size:13px;
}

button,select{
  font:inherit;
}

.wr-shell{
  min-height:100vh;
}

.wr-top{
  position:relative;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:8px;
  min-height:40px;
  padding:4px 8px 12px;
  border-bottom:1px solid var(--line);
  background:#060c12;
}

.wr-title{
  font-size:16px;
  font-weight:900;
  letter-spacing:1.5px;
}

.wr-title span{
  color:var(--green);
}

.wr-top-left,
.wr-top-right{
  display:flex;
  align-items:center;
  gap:6px;
  flex-wrap:nowrap;
}
.wr-top-left{min-width:0}
.wr-top-right{margin-left:auto;white-space:nowrap}

.wr-inline-health{
  display:flex;
  gap:10px;
  color:var(--muted);
  font-weight:800;
}

.dot{
  display:inline-block;
  width:8px;
  height:8px;
  border-radius:50%;
  margin-right:5px;
  background:var(--muted);
  box-shadow:0 0 8px currentColor;
}

.dot.GREEN{background:var(--green);color:var(--green)}
.dot.YELLOW{background:var(--yellow);color:var(--yellow)}
.dot.RED{background:var(--red);color:var(--red)}
.dot.GRAY{background:var(--muted);color:var(--muted)}

.wr-btn{
  border:1px solid var(--line2);
  background:#0c1722;
  color:var(--text);
  border-radius:4px;
  padding:5px 7px;
  font-size:10px;
  cursor:pointer;
}

.wr-btn:hover{
  border-color:var(--green);
}

.wr-btn.refresh{
  color:var(--green);
  border-color:#147a59;
}

.wr-btn.acquire{
  color:var(--yellow);
  border-color:#9b741d;
}
.wr-btn:disabled{
  cursor:not-allowed;
  opacity:.65;
}

.operator-status{
  position:absolute;
  right:9px;
  bottom:1px;
  color:var(--muted);
  font-size:8px;
  text-align:right;
  min-height:9px;
}

.summary-grid{
  display:grid;
  grid-template-columns:1.1fr 1.25fr 1.25fr .65fr 1fr 1fr;
  gap:3px;
  padding:3px 4px 2px;
}

.summary-box{
  min-height:38px;
  border:1px solid var(--line);
  background:var(--panel);
  padding:4px 7px;
}

.summary-label{
  color:var(--muted);
  font-size:9px;
  text-transform:uppercase;
}

.summary-value{
  margin-top:2px;
  font-weight:900;
  font-size:13px;
}

.green{color:var(--green)}
.yellow{color:var(--yellow)}
.red{color:var(--red)}
.cyan{color:var(--cyan)}
.muted{color:var(--muted)}

.health-strip{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
  padding:4px 8px;
  margin:0 4px 2px;
  border:1px solid var(--line);
  background:var(--panel);
}

.health-title{
  color:var(--muted);
  font-size:10px;
  font-weight:900;
  letter-spacing:.7px;
  margin-right:3px;
}

.health-book{
  white-space:nowrap;
  font-weight:800;
}

.health-detail{
  color:var(--muted);
  font-weight:500;
  font-size:10px;
}

.ratings-health-strip{
  margin-top:0;
  display:grid;
  grid-template-columns:max-content minmax(0, 1fr);
  align-items:start;
  gap:3px 8px;
}

.model-health-rows{
  display:grid;
  gap:3px;
  min-width:0;
}

.model-health-row{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
  min-width:0;
}

.model-health-label{
  min-width:154px;
  font-size:10px;
  font-weight:900;
  letter-spacing:.3px;
}

.health-status{
  font-size:10px;
  font-weight:900;
  margin-left:3px;
}

.health-status.GREEN{color:var(--green)}
.health-status.YELLOW{color:var(--yellow)}
.health-status.RED{color:var(--red)}
.health-status.GRAY{color:var(--muted)}

.spread-label{
  font-size:9px;
  letter-spacing:-.2px;
}

.command-grid{
  display:grid;
  grid-template-columns:minmax(0, 1fr) 330px;
  gap:4px;
  margin:2px 4px;
  min-height:320px;
}

.main-panel{
  margin:0;
  border:1px solid var(--line);
  background:var(--panel);
  min-width:0;
  min-height:0;
  display:flex;
  flex-direction:column;
  overflow:hidden;
}

.right-rail{
  border:1px solid var(--line);
  background:var(--panel);
  min-width:0;
  min-height:0;
  display:flex;
  flex-direction:column;
  overflow:hidden;
}

.rail-section{
  border-bottom:1px solid var(--line);
}

.rail-title{
  padding:8px 10px;
  font-weight:900;
  letter-spacing:1px;
  border-bottom:1px solid var(--line);
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:8px;
}
.activity-updated{color:var(--muted);font-size:9px;font-weight:800;letter-spacing:0;white-space:nowrap}

.rail-row{
  display:grid;
  grid-template-columns:72px 1fr;
  gap:8px;
  padding:8px 10px;
  border-bottom:1px solid #1c2d3c;
  line-height:1.25;
}

.rail-key{
  color:var(--muted);
  font-size:11px;
}

.rail-value{
  font-weight:800;
}

.activity-summary{padding:8px 10px;border-bottom:1px solid var(--line);font-size:11px;font-weight:900;line-height:1.45}
.activity-summary-label{display:block;color:var(--muted);font-size:9px;letter-spacing:.7px}
.activity-focus{display:none;padding:7px 9px;border-bottom:1px solid var(--line);background:rgba(66,217,255,.055)}
.activity-focus.active{display:block}
.activity-focus-head{display:flex;align-items:center;justify-content:space-between;gap:8px}
.activity-focus-game{min-width:0;color:var(--cyan);font-size:11px;font-weight:900;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.activity-clear{border:0;background:transparent;color:var(--muted);font-size:9px;font-weight:900;cursor:pointer;white-space:nowrap}
.activity-clear:hover{color:var(--cyan)}
.activity-filters{display:flex;gap:4px;padding:6px;border-bottom:1px solid var(--line);flex-wrap:wrap}
.activity-filter{border:1px solid var(--line2);background:#09131d;color:var(--muted);border-radius:10px;padding:3px 7px;font-size:9px;font-weight:900;cursor:pointer}
.activity-filter.active{border-color:var(--green);color:var(--green)}
.activity-summary.hidden{display:none}
.activity-snapshot{display:none;padding:5px 8px;border-bottom:1px solid var(--line);background:rgba(66,217,255,.035);font-size:9px;line-height:1.28}
.activity-snapshot.active{display:block}
.snapshot-title{color:var(--muted);font-size:8px;font-weight:900;letter-spacing:.7px;margin-bottom:3px}
.snapshot-row{display:grid;grid-template-columns:48px minmax(0,1fr);gap:5px;align-items:baseline;margin-top:2px}
.snapshot-key{color:var(--cyan);font-size:8px;font-weight:900;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.snapshot-value{min-width:0;color:var(--text);font-weight:800;white-space:normal}
.snapshot-components{display:block;color:#9eafbf;font-size:8px;font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.snapshot-book{display:inline-flex;align-items:center;gap:2px;white-space:nowrap}
.snapshot-book img{width:13px;height:13px;object-fit:contain;border-radius:3px;padding:1px;background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.14)}
.activity-list{flex:1;min-height:0;overflow-y:auto;overflow-x:hidden}
.activity-row{display:block;width:100%;border:0;border-bottom:1px solid #1c2d3c;background:transparent;color:var(--text);padding:7px 9px;text-align:left;cursor:default}
.activity-row.game-event{cursor:pointer}
.activity-row.game-event:hover{background:#101d29}
.activity-line{display:flex;align-items:center;gap:6px;min-width:0}
.activity-time{color:var(--muted);font-size:9px;white-space:nowrap}
.activity-kind{font-size:9px;font-weight:900;color:var(--cyan)}
.activity-kind.open{color:#42d9ff}.activity-kind.market{color:#ff9c55}.activity-kind.model{color:#79b9ff}.activity-kind.postgame{color:#c6a0ff}.activity-kind.data{color:#ffd166}
.activity-game{margin-top:2px;font-size:10px;font-weight:900;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.activity-prior-owner{display:block;margin-top:2px;color:var(--cyan);font-size:8px;font-weight:900;letter-spacing:.45px}
.activity-detail{margin-top:2px;color:#aebdca;font-size:10px;line-height:1.25;white-space:normal;display:flex;align-items:center;gap:5px;min-width:0}
.activity-detail-text{min-width:0}
.activity-book-logos{display:inline-flex;align-items:center;gap:3px;flex:0 0 auto}
.activity-book-logo{width:18px;height:18px;object-fit:contain;border:1px solid rgba(255,255,255,.16);border-radius:4px;padding:2px;background:rgba(255,255,255,.09)}
.activity-book-fallback{display:none;color:var(--muted);font-size:8px;font-weight:900}
.activity-empty{padding:16px 10px;color:var(--muted);font-size:10px}
.activity-unread{color:var(--yellow);margin-left:5px}
.activity-flash td{animation:activityFlash 1.8s ease-out}
@keyframes activityFlash{0%{box-shadow:inset 0 0 0 999px rgba(57,232,154,.25)}100%{box-shadow:none}}
.game-start.game-selected td{background:rgba(66,153,255,.075);box-shadow:inset 0 1px rgba(66,217,255,.24),inset 0 -1px rgba(66,217,255,.24)}
.game-start.game-selected td:first-child{box-shadow:inset 3px 0 var(--cyan),inset 0 1px rgba(66,217,255,.24),inset 0 -1px rgba(66,217,255,.24)}

.matrix-scroll{
  flex:1;
  min-height:0;
  max-height:none;
  overflow-y:auto;
  overflow-x:hidden;
}

.mobile-matrix{
  display:none;
}

.mobile-sticky-bar{
  display:none;
}

.panel-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  height:31px;
  padding:0 8px;
  border-bottom:1px solid var(--line);
}

.panel-title{
  font-weight:900;
  letter-spacing:1px;
}

.panel-tools{
  display:flex;
  gap:8px;
  align-items:center;
}


.week-select{
  border:1px solid var(--line);
  background:#09131d;
  color:var(--text);
  padding:5px 8px;
  border-radius:3px;
}

.table-wrap{
  overflow:visible;
}

.table-wrap.matrix-scroll{
  overflow-y:auto;
  overflow-x:hidden;
}

table{
  width:100%;
  border-collapse:collapse;
  table-layout:fixed;
  min-width:0;
}

th.sortable{
  cursor:pointer;
  user-select:none;
}

th.sortable:hover{
  color:var(--green);
}

.sort-arrow{
  color:var(--green);
  margin-left:3px;
}

th{
  position:sticky;
  top:0;
  z-index:4;
  text-align:left;
  background:#0b1620;
  color:var(--muted);
  border-bottom:2px solid var(--line2);
  font-size:10px;
  text-transform:uppercase;
  font-weight:800;
  padding:6px 1px;
  white-space:nowrap;
}

td{
  border-bottom:1px solid #223444;
  padding:5px 1px;
  vertical-align:middle;
  white-space:nowrap;
}

#matrixHead th:not(.matchup-col),
#matrixBody td:not(.matchup-col){
  text-align:center;
}



tr.game-start td{
  border-top:2px solid #31485b;
}

.market-kind{
  color:var(--muted);
  font-size:10px;
  font-weight:900;
  letter-spacing:.6px;
}

.game-subrow{
  padding-left:18px;
  color:var(--muted);
}

tr:hover td{
  background:#101d29;
}

th.spread-group{background:#102334}
td.spread-group{background:rgba(28,68,99,.18)}
th.total-group{background:#241a35}
td.total-group{background:rgba(75,45,96,.18)}
th.context-group{background:#17212b}
td.context-group{background:rgba(34,48,61,.2)}
th.edge-focus{
  border-left:1px solid rgba(235,242,248,.72);
  border-right:1px solid rgba(235,242,248,.72);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.4);
}
td.edge-focus{
  border-left:1px solid rgba(220,230,238,.42);
  border-right:1px solid rgba(220,230,238,.42);
}
tr:hover td.spread-group{background:#153047}
tr:hover td.total-group{background:#302142}
tr:hover td.context-group{background:#202d39}

.game-cell{
  min-width:185px;
}

.game-name{
  font-weight:900;
}

.game-meta{
  color:var(--muted);
  font-size:10px;
  margin-top:2px;
}

.quote{
  font-weight:800;
}

.quote.best{color:var(--text)}

.quote.none{
  color:#526476;
  font-weight:500;
}

.model-col{
  font-size:15px;
  font-weight:900;
}

.matchup-col{width:13.1%}
.model-col{width:4.8%}

.shadow-col{
  width:7.2%;
  font-size:10px;
  text-align:center;
  padding-left:0;
  padding-right:0;
}

.shadow-ready{
  color:var(--purple);
  font-weight:900;
}

.shadow-wait{
  color:var(--yellow);
  font-size:11px;
  font-weight:900;
}
.shadow-team-state{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;white-space:nowrap}
.shadow-team-icons{display:flex;flex-direction:row;align-items:center;justify-content:center;gap:5px}
.shadow-team-chip{position:relative;display:inline-flex;align-items:center;justify-content:center}
.shadow-team-chip .team-logo-holder{--team-logo-size:23px}
.shadow-team-mark{position:absolute;right:-3px;bottom:-4px;font-size:15px;font-weight:950;line-height:1;text-shadow:0 1px 2px #071019,0 0 2px #071019}
.shadow-team-mark.ready{color:var(--green)}
.shadow-team-mark.waiting{color:var(--red)}
.shadow-state-label{font-size:11px;font-weight:900;line-height:1.05;letter-spacing:.03em}
.best-col{width:8.8%}
.exchange-col{width:8%}
.open-col{width:5.7%} /* retained for future/mobile opener presentation */
.edge-col{
  width:6.5%;
  text-align:center;
  padding-left:5px;
  padding-right:5px;
  box-sizing:border-box;
}
.injury-col{width:1.8%;text-align:center}
.signal-col{width:5%}
.state-col{width:5.5%;text-align:center}

/* Canonical Priority Market Matrix header typography. Column classes also
   style body cells, so this late header-only rule prevents those body font
   sizes from leaking into MODEL, SHADOW, OPEN, or other header labels. */
.matrix-header-cell,
.matrix-header-cell .spread-label,
.matrix-header-cell .header-tooltip,
.matrix-header-cell .matchup-sort-button{
  font-family:inherit;
  font-size:9px;
  font-weight:900;
  letter-spacing:.035em;
  text-transform:uppercase;
  line-height:1.12;
}

.matrix-header-cell{
  vertical-align:middle;
  padding-top:6px;
  padding-bottom:6px;
}

.matrix-header-cell.edge-focus{
  font-weight:950;
}

.game-name{
  font-weight:900;
  white-space:normal;
}

.game-date{
  font-size:10px;
  color:var(--muted);
  font-weight:800;
}

.game-time{
  font-size:10px;
  color:#b8c7d5;
  margin-left:5px;
}

.matchup-kickoff{display:flex;align-items:center;gap:5px;margin-bottom:2px}
.matchup-team{display:flex;align-items:center;gap:4px;min-width:0;font-size:11px;font-weight:900;line-height:1.2}
.matchup-team .team-logo-holder{--team-logo-size:18px}
.matchup-team span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.team-composite-rank{flex:0 0 22px;min-width:22px;text-align:right;font-size:9.5px;font-weight:950;font-variant-numeric:tabular-nums;line-height:1;color:var(--muted);overflow:visible!important}
.team-composite-rank.rank-tier-1{color:#39e89a}
.team-composite-rank.rank-tier-2{color:#78e6ad}
.team-composite-rank.rank-tier-3{color:#f4cd4b}
.team-composite-rank.rank-tier-4{color:#ff8a5b}
.team-composite-rank.rank-tier-5{color:#ff4d63}
.matchup-team-name{min-width:0}
.matchup-live-score{margin-left:auto;padding-left:5px;font-size:12px;font-weight:950;color:#eef3f7;font-variant-numeric:tabular-nums}
.game-live-state{font-size:9px;font-weight:950;color:var(--green);letter-spacing:.03em}
.neutral-marker{color:var(--yellow);font-size:8px;font-weight:900;letter-spacing:.04em}
.matchup-sort-head{display:flex;align-items:center;justify-content:space-between;gap:3px}
.matchup-sort-button{appearance:none;border:0;background:transparent;color:var(--muted);font:inherit;font-size:9px;font-weight:900;padding:0;cursor:pointer;text-transform:uppercase;white-space:nowrap}
.matchup-sort-button:hover,.matchup-sort-button.active{color:var(--green)}

.game-meta{
  color:var(--muted);
  font-size:9px;
  margin-top:2px;
}

.compact-market{
  line-height:1.3;
}

.compact-market .spr{
  font-weight:900;
}

.compact-market .tot{
  font-size:10px;
  color:var(--muted);
  margin-top:3px;
}

.market-best{
  color:#dce5ed;
  font-weight:900;
  display:grid;
  grid-template-columns:24px minmax(34px,1fr);
  grid-template-rows:auto auto;
  column-gap:3px;
  align-items:center;
  line-height:1.05;
  width:max-content;
  max-width:100%;
  margin-inline:auto;
}

.market-book-logo{
  grid-column:1;
  grid-row:1 / span 2;
  width:22px;
  height:22px;
  object-fit:contain;
}

.market-line{
  grid-column:2;
  grid-row:1;
  color:#eef3f7;
  font-size:14px;
  white-space:nowrap;
}

.market-juice{
  grid-column:2;
  grid-row:2;
  color:#9fb0bf;
  font-size:11px;
  white-space:nowrap;
}

.open-cell{display:flex;align-items:center;justify-content:center;min-width:0;cursor:help}
.open-quote{display:grid;grid-template-columns:18px minmax(26px,1fr);grid-template-rows:auto auto auto;column-gap:1px;align-items:center;width:100%;min-width:0;line-height:1.02}
.open-cell .market-book-logo{grid-column:1;grid-row:1 / span 2;display:block;width:18px;height:18px;padding:1px}
.open-line{grid-column:2;grid-row:1;font-size:12px;font-weight:900;color:#eef3f7;white-space:nowrap}
.open-price{grid-column:2;grid-row:2;font-size:10px;font-weight:800;color:#9fb0bf;white-space:nowrap}
.open-meta{grid-column:1 / span 2;grid-row:3;display:flex;align-items:center;justify-content:center;gap:1px;min-width:0;font-size:8px;font-weight:750;color:#8296a8;white-space:nowrap}
.open-time{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.open-missing{font-size:8px;font-weight:900;color:#718499;letter-spacing:.02em}
.recency-marker{display:none;font-size:7.5px;font-weight:900;letter-spacing:.01em;line-height:1.05}
.recency-marker.open-new{display:inline;color:#e99362}
.recency-marker.open-recent{display:inline;color:#c7ad58}
.move-marker{display:none;grid-column:3;grid-row:1 / span 2;align-self:center;justify-self:center;font-size:14px;font-weight:950;line-height:1;cursor:help}
.move-marker.move-very-recent{display:inline-block;color:#ff6969}
.move-marker.move-recent{display:inline-block;color:var(--yellow)}
.move-marker.move-older-recent{display:inline-block;color:#8796a4}
.market-best.has-move{grid-template-columns:22px minmax(30px,1fr) 14px}

.decision-edge{
  display:inline-flex;
  width:100%;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:1px;
  white-space:nowrap;
}
.decision-edge-main{display:inline-flex;align-items:center;justify-content:center;gap:3px;white-space:nowrap}
.decision-team-name{display:block;width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:center;color:#aebdca;font-size:7.5px;font-weight:800;line-height:1.05}
.market-book-logo{
  background:rgba(255,255,255,.09);
  border:1px solid rgba(255,255,255,.16);
  border-radius:4px;
  padding:2px;
  filter:drop-shadow(0 0 3px rgba(235,242,248,.2));
}
.decision-edge .team-logo-holder{--team-logo-size:22px}
.decision-side{font-size:12px;font-weight:900}

.team-logo-holder{
  width:var(--team-logo-size,16px);
  height:var(--team-logo-size,16px);
  flex:0 0 var(--team-logo-size,16px);
  display:inline-flex;
  align-items:center;
  justify-content:center;
  padding:1.5px;
  overflow:hidden;
  background:rgba(255,255,255,.08);
  border:1px solid rgba(255,255,255,.12);
  border-radius:4px;
  box-shadow:inset 0 0 0 1px rgba(7,16,25,.22);
}

.team-logo-holder img{
  display:block;
  width:100%;
  height:100%;
  object-fit:contain;
  filter:
    drop-shadow(0 0 1px rgba(255,255,255,.90))
    drop-shadow(0 0 2px rgba(255,255,255,.38))
    drop-shadow(0 1px 1px rgba(0,0,0,.78));
}

.model-tooltip{position:relative;display:inline-flex;justify-content:center;cursor:help}
.model-tooltip-panel{
  display:none;
  position:fixed;
  z-index:80;
  left:0;
  top:0;
  transform:none;
  min-width:190px;
  padding:7px 8px;
  border:1px solid #425a70;
  border-radius:4px;
  background:#050c13;
  box-shadow:0 8px 22px rgba(0,0,0,.45);
  color:#dfe8f0;
  font-size:10px;
  font-weight:700;
  text-align:left;
}
.model-tooltip.open .model-tooltip-panel{display:block}
.model-component{display:grid;grid-template-columns:minmax(78px,1fr) auto;gap:10px;padding:1px 0}
.model-component.missing{color:#718393}

.header-tooltip{position:relative;display:inline-flex;align-items:center;cursor:help}
.header-tooltip-panel{
  display:none;
  position:absolute;
  z-index:30;
  right:0;
  top:calc(100% + 7px);
  width:240px;
  padding:7px 8px;
  border:1px solid #425a70;
  border-radius:4px;
  background:#050c13;
  box-shadow:0 8px 22px rgba(0,0,0,.45);
  color:#dfe8f0;
  font-size:9px;
  font-weight:700;
  line-height:1.35;
  text-align:left;
  text-transform:none;
  white-space:normal;
}
.header-tooltip:hover .header-tooltip-panel,
.header-tooltip:focus-within .header-tooltip-panel{display:block}
.state-definition{display:block;margin:2px 0}
.state-definition strong{color:#fff}

.pinn-quote{
  display:block;
  font-size:11px;
  line-height:1.15;
  white-space:normal;
}

.market-secondary{
  color:#c8d3dd;
  font-size:10px;
  margin-top:3px;
}

.signal-placeholder,
.injury-placeholder{
  color:var(--muted);
}

.signal-stack{
  display:flex;
  gap:5px;
  flex-wrap:wrap;
  align-items:center;
  justify-content:center;
  width:100%;
}

.signal-chip{
  display:inline-flex;
  align-items:center;
  gap:4px;
  border:1px solid #68438b;
  border-radius:12px;
  padding:2px 6px;
  background:#151526;
  font-size:10px;
  font-weight:900;
}

.signal-chip .team-logo-holder{--team-logo-size:18px}

.signal-count{
  color:var(--green);
}

.edge{
  font-size:15px;
  font-weight:900;
}

.edge.action{color:var(--green)}
.edge.lean{color:var(--yellow)}
.edge.watch{color:#c6d1db}

.badge{
  display:inline-block;
  border:1px solid var(--line2);
  padding:3px 4px;
  border-radius:3px;
  font-weight:900;
  font-size:9px;
  letter-spacing:.6px;
}

.badge.HYBRID{
  color:var(--cyan);
  border-color:#247a86;
}

.badge.STALE{
  color:var(--red);
  border-color:#7d2e3a;
}

.badge.UPDATED{
  color:var(--green);
  border-color:#217a59;
}

.badge.SHADOW{
  color:var(--purple);
  border-color:#65458f;
}

.edge-badge{
  display:inline-block;
  min-width:58px;
}

.bottom-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:4px;
  margin:4px;
}

.bottom-panel{
  border:1px solid var(--line);
  background:var(--panel);
}

.health-table{
  width:100%;
  min-width:0;
}

.health-table td{
  padding:8px 10px;
}

.footer{
  padding:4px 8px;
  color:var(--muted);
  border-top:1px solid var(--line);
  background:#060c12;
  font-size:9px;
}

@media(min-width:901px){body{overflow:hidden}}

@media(max-width:900px){
  body{overflow-x:hidden;overflow-y:auto}
  .wr-shell{width:100%;max-width:100vw;overflow:visible}
  .summary-grid{
    grid-template-columns:repeat(2,1fr);
  }

  .command-grid{
    grid-template-columns:1fr;
  }

  .command-grid{height:auto!important}
  .matrix-scroll{display:none}
  .mobile-matrix{display:grid;gap:7px;padding:7px;background:#071019}

  .right-rail{display:none}
  .mobile-activity-slot .right-rail{
    display:flex;
    width:100%;
    min-height:280px;
    max-height:48vh;
    margin-top:0;
    border-left:0;
    border-top:1px solid var(--line2);
    background:#08121c;
  }
  .mobile-activity-slot{border-top:1px solid rgba(69,217,237,.28)}

  .mobile-sticky-bar{
    position:sticky;
    top:0;
    z-index:30;
    display:block;
    min-height:54px;
    padding:calc(4px + env(safe-area-inset-top,0px)) 7px 5px;
    border-bottom:1px solid var(--line2);
    background:rgba(6,12,18,.97);
    box-shadow:0 4px 12px rgba(0,0,0,.35);
  }
  .mobile-sticky-main{display:flex;align-items:center;justify-content:space-between;gap:8px;min-width:0}
  .mobile-sticky-title{color:var(--text);font-size:11px;font-weight:950;letter-spacing:.55px;white-space:nowrap}
  .mobile-sticky-title span{color:var(--green)}
  .mobile-sticky-health{min-width:0;color:var(--muted);font-size:8px;font-weight:900;text-align:right;white-space:nowrap}
  .mobile-sticky-controls{display:grid;grid-template-columns:62px minmax(74px,.8fr) minmax(126px,1.35fr) 72px;gap:4px;margin-top:4px}
  .mobile-control-select,.mobile-controls-toggle{
    min-width:0;
    height:25px;
    border:1px solid var(--line2);
    border-radius:4px;
    background:#0c1722;
    color:var(--text);
    padding:2px 4px;
    font-size:9px;
    font-weight:900;
  }
  .mobile-controls-toggle{color:var(--yellow);cursor:pointer}

  .wr-top{padding-bottom:5px}
  .wr-top-right{display:none;width:100%;margin-left:0;flex-wrap:wrap;padding-top:3px}
  .wr-top-right.mobile-open{display:flex}
  .wr-top-right::-webkit-scrollbar{display:none}
  .operator-status{position:static;width:100%;text-align:left}
  .wr-inline-health{font-size:10px;gap:5px;flex-wrap:wrap}

  .panel-head{display:none}

  .mobile-game-card{
    border:1px solid var(--line2);
    border-radius:6px;
    background:var(--panel);
    overflow:hidden;
  }
  .mobile-game-card.game-selected{
    border-color:var(--cyan);
    box-shadow:0 0 0 1px rgba(69,217,237,.2);
  }
  .mobile-activity-slot:empty{display:none}
  .mobile-game-card.activity-flash{animation:mobileActivityFlash 1.8s ease-out}
  @keyframes mobileActivityFlash{0%{box-shadow:inset 0 0 0 999px rgba(57,232,154,.22)}100%{box-shadow:none}}
  .mobile-game-head{
    display:grid;
    grid-template-columns:auto minmax(0,1fr) auto;
    gap:7px;
    align-items:center;
    padding:7px 8px;
    border-bottom:1px solid var(--line);
    background:#0a141e;
  }
  .mobile-kickoff{display:flex;flex-direction:column;color:var(--muted);font-size:9px;font-weight:900;line-height:1.2}
  .mobile-matchup{min-width:0}
  .mobile-matchup .matchup-team{font-size:11px}
  .mobile-card-state{justify-self:end}
  .mobile-market-band{padding:6px 7px 7px}
  .mobile-market-band + .mobile-market-band{border-top:1px solid var(--line)}
  .mobile-band-title{margin-bottom:5px;color:var(--muted);font-size:9px;font-weight:900;letter-spacing:.8px}
  .mobile-band-grid{
    display:grid;
    grid-template-columns:.78fr 1fr 1.12fr 1.12fr 1fr;
    gap:3px;
    align-items:stretch;
  }
  .mobile-metric{
    min-width:0;
    min-height:54px;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    gap:3px;
    padding:3px 1px;
    border:1px solid rgba(51,73,92,.7);
    border-radius:4px;
    background:rgba(7,16,25,.5);
    text-align:center;
  }
  .mobile-metric.edge-focus{background:rgba(57,232,154,.045);border-color:rgba(57,232,154,.25)}
  .mobile-metric-label{color:#8294a6;font-size:7px;font-weight:900;letter-spacing:.35px}
  .mobile-metric .model-number{font-size:12px}
  .mobile-metric .market-book-logo{width:20px;height:20px}
  .mobile-metric .market-line{font-size:12px}
  .mobile-metric .market-juice{font-size:10px}
  .mobile-metric .shadow-state-label{font-size:10px}
  .mobile-metric .shadow-team-mark{font-size:13px}
  .mobile-metric.edge-focus{overflow:hidden}
  .mobile-metric .decision-edge{min-width:0;max-width:100%}
  .mobile-metric .decision-edge-main{max-width:100%;gap:2px}
  .mobile-metric .decision-edge .team-logo-holder{--team-logo-size:18px}
  .mobile-metric .decision-team-name{width:100%;max-width:100%;padding:0 2px;box-sizing:border-box}
  .mobile-game-foot{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:8px;
    min-height:30px;
    padding:4px 8px;
    border-top:1px solid var(--line);
    background:#09131d;
  }
  .mobile-foot-label{color:var(--muted);font-size:8px;font-weight:900}
  .mobile-foot-signals{display:flex;align-items:center;gap:5px;min-width:0}

  .wr-top{
    align-items:flex-start;
    flex-direction:column;
  }

  .ratings-health-strip{
    grid-template-columns:1fr;
  }

  .model-health-label{
    min-width:145px;
  }
}
</style>
</head>

<body>
<div class="wr-shell">

  <div class="wr-top">
    <div class="wr-top-left">
      <div class="wr-title">
        WAR ROOM / <span>MARKET MATRIX</span>
      </div>

      <div class="wr-inline-health" id="topHealth">
        Loading market state…
      </div>
    </div>

    <div class="wr-top-right">
      <button class="wr-btn" onclick="location.href='index.html'">
        ← MAIN SITE
      </button>

      <button class="wr-btn refresh" id="refreshBtn">
        ↻ RELOAD MARKET
      </button>

      <button class="wr-btn" id="connectOperatorBtn" hidden>
        🔐 CONNECT OPERATOR
      </button>

      <button class="wr-btn acquire operator-control" id="acquireBtn" disabled title="Guarded spreads + totals pull; expected cost 2 Odds API credits">
        ⚡ REFRESH MARKET · 2 CREDITS
      </button>

      <button class="wr-btn operator-control" id="ratingsBtn" disabled>
        ↻ REFRESH RATINGS
      </button>

      <button class="wr-btn operator-control" id="postgameBtn" disabled>
        ↻ REFRESH POSTGAME
      </button>

      <div class="operator-status" id="operatorStatus">Checking operator authentication…</div>
    </div>
  </div>

  <section class="mobile-sticky-bar" id="mobileStickyBar" aria-label="Mobile War Room controls">
    <div class="mobile-sticky-main">
      <span class="mobile-sticky-title">WAR ROOM · <span>MARKET MATRIX</span></span>
      <span class="mobile-sticky-health" id="mobileStickyHealth">API — · UPDATED —</span>
    </div>
    <div class="mobile-sticky-controls">
      <select class="mobile-control-select" id="mobileScopeSelect" aria-label="Game scope"><option value="FBS">FBS</option><option value="ALL">ALL</option></select>
      <select class="mobile-control-select" id="mobileWeekSelect" aria-label="Week"></select>
      <select class="mobile-control-select" id="mobileSortSelect" aria-label="Sort games">
        <option value="date">DATE</option><option value="home_team">HOME TEAM A-Z</option>
        <option value="spread_edge">SPREAD EDGE</option><option value="total_edge">TOTAL EDGE</option>
      </select>
      <button class="mobile-controls-toggle" id="mobileControlsToggle" type="button" aria-expanded="false">CONTROLS</button>
    </div>
  </section>

  <section class="summary-grid">
    <div class="summary-box">
      <div class="summary-label">Markets</div>
      <div class="summary-value" id="summaryMarkets">—</div>
    </div>

    <div class="summary-box">
      <div class="summary-label">Spread</div>
      <div class="summary-value" id="summarySpread">—</div>
    </div>

    <div class="summary-box">
      <div class="summary-label">Total</div>
      <div class="summary-value" id="summaryTotal">—</div>
    </div>

    <div class="summary-box">
      <div class="summary-label">Hybrid / Stale</div>
      <div class="summary-value" id="summaryState">—</div>
    </div>

    <div class="summary-box">
      <div class="summary-label">Book Health</div>
      <div class="summary-value" id="summaryBooks">—</div>
    </div>

    <div class="summary-box">
      <div class="summary-label">Poll / Quota</div>
      <div class="summary-value" id="summaryQuota">—</div>
    </div>
  </section>

  <section class="health-strip" id="healthStrip">
    <span class="health-title">MARKET HEALTH</span>
  </section>

  <section class="health-strip ratings-health-strip" id="ratingsHealthStrip">
    <span class="health-title">RATINGS / MODEL HEALTH</span>
  </section>

  <section class="command-grid">

    <section class="main-panel">
      <div class="panel-head">
        <div class="panel-title">PRIORITY MARKET MATRIX</div>

        <div class="panel-tools">
          <select class="week-select" id="scopeSelect">
            <option value="FBS">FBS ONLY</option>
            <option value="ALL">ALL GAMES</option>
          </select>

          <select class="week-select" id="weekSelect"></select>
        </div>
      </div>

      <div class="table-wrap matrix-scroll">
        <table>
          <thead id="matrixHead"></thead>
          <tbody id="matrixBody"></tbody>
        </table>
      </div>

      <div class="mobile-matrix" id="mobileMatrix" aria-label="Priority Market Matrix mobile view"></div>
    </section>

    <aside class="right-rail" aria-label="War Room Activity">
      <div class="rail-title"><span>WAR ROOM ACTIVITY</span><span class="activity-updated" id="activityUpdated">UPDATED —</span></div>
      <div class="activity-summary" id="activitySummary">Loading activity…</div>
      <div class="activity-focus" id="activityFocus"></div>
      <div class="activity-filters" id="activityFilters">
        <button class="activity-filter active" data-filter="ALL">ALL</button>
        <button class="activity-filter" data-filter="MARKET">MARKET</button>
        <button class="activity-filter" data-filter="MODEL">MODEL</button>
        <button class="activity-filter" data-filter="POSTGAME">POSTGAME</button>
      </div>
      <div class="activity-snapshot" id="activitySnapshot"></div>
      <div class="activity-list" id="activityList"></div>
    </aside>

  </section>

  <footer class="footer">
    FAST WAR ROOM · BEST BOOK = DK / FD / MGM / CZR ·
    BEST EXCHANGE = NOVIG / PROPHETX / KALSHI AT -120 OR BETTER ·
    PINNACLE = SHARP REFERENCE · RELOAD MARKET = 0 CREDITS ·
    ACQUIRE MARKET = GUARDED SPREADS + TOTALS PULL, EXPECTED 2 CREDITS
  </footer>

</div>

<script>
const MATRIX_URL = 'data/site/war_room_market_matrix.json';
const HEALTH_URL = 'data/site/war_room_health.json';
const ACTIVITY_URL = 'data/site/war_room_activity.json';
const LIVE_VERSION_URL = 'https://control.barnseywr.com/war-room/live/version';
const LIVE_MATRIX_URL = 'https://control.barnseywr.com/war-room/live/market-matrix';
const LIVE_HEALTH_URL = 'https://control.barnseywr.com/war-room/live/health';
const LIVE_ACTIVITY_URL = 'https://control.barnseywr.com/war-room/live/activity';

let MATRIX = null;
let HEALTH = null;
let ACTIVITY = null;
let ACTIVITY_FILTER = 'ALL';
let SELECTED_GAME_ID = null;
let SELECTED_GAME_ACTIVITY = null;
let ACTIVITY_VERSION = null;
const GAME_ACTIVITY_CACHE = new Map();
let ACTIVE_MARKET = 'spread';
let ACTIVE_WEEK = 'AUTO';
let ACTIVE_SCOPE = 'FBS';
const INITIAL_MOBILE_VIEW = window.matchMedia('(max-width:900px)').matches;
let SORT_KEY = INITIAL_MOBILE_VIEW ? 'spread_edge' : 'best_edge';
let SORT_DIR = 'desc';

const TEAM_ABBREVIATIONS = __TEAM_ABBREVIATIONS__;

const BOOK_ABBR = {
  DraftKings:'DK',
  FanDuel:'FD',
  BetMGM:'MGM',
  Caesars:'CZR',
  Pinnacle:'PINN',
  Novig:'NOVIG',
  ProphetX:'PROPHET',
  Kalshi:'KALSHI'
};

function esc(v){
  return String(v ?? '')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

function fmtPrice(v){
  if(v === null || v === undefined || v === '') return '';
  const n = Number(v);
  if(!Number.isFinite(n)) return '';
  return n > 0 ? `+${n}` : `${n}`;
}

function fmtLine(v){
  if(v === null || v === undefined || v === '') return '—';
  const n = Number(v);
  if(!Number.isFinite(n)) return '—';
  if(n === 0) return 'PK';
  return n > 0 ? `+${n}` : `${n}`;
}

function quoteText(q){
  if(!q) return '—';
  return `${fmtLine(q.line)} ${fmtPrice(q.price)}`;
}

function totalQuoteText(q){
  if(!q) return '—';

  const prefix =
    q.side === 'under'
      ? 'U'
      : 'O';

  const n = Number(q.line);

  return `${prefix}${
    Number.isFinite(n) ? n : '—'
  } ${fmtPrice(q.price)}`;
}


function fmtKickoffDateET(value){
  if(!value) return '—';

  const d = new Date(value);
  if(Number.isNaN(d.getTime())) return '—';

  return new Intl.DateTimeFormat(
    'en-US',
    {
      timeZone:'America/New_York',
      month:'numeric',
      day:'numeric'
    }
  ).format(d);
}

function fmtKickoffTimeET(value){
  if(!value) return '—';

  const d = new Date(value);
  if(Number.isNaN(d.getTime())) return '—';

  return new Intl.DateTimeFormat(
    'en-US',
    {
      timeZone:'America/New_York',
      hour:'numeric',
      minute:'2-digit',
      hour12:true
    }
  ).format(d) + ' ET';
}


function fmtStatusDate(value){
  if(!value) return '';

  const d = new Date(
    String(value).length === 10
      ? `${value}T12:00:00Z`
      : value
  );

  if(Number.isNaN(d.getTime())){
    return String(value);
  }

  return new Intl.DateTimeFormat(
    'en-US',
    {
      timeZone:'America/New_York',
      month:'numeric',
      day:'numeric'
    }
  ).format(d);
}


function fmtDateTimeET(value){
  if(!value) return '—';

  const d = new Date(value);

  if(Number.isNaN(d.getTime())){
    return String(value);
  }

  return new Intl.DateTimeFormat(
    'en-US',
    {
      timeZone:'America/New_York',
      month:'numeric',
      day:'numeric',
      hour:'numeric',
      minute:'2-digit',
      hour12:true
    }
  ).format(d) + ' ET';
}

function fmtStatusTimeET(value){
  if(!value) return '';

  const d = new Date(value);

  if(Number.isNaN(d.getTime())){
    return '';
  }

  return new Intl.DateTimeFormat(
    'en-US',
    {
      timeZone:'America/New_York',
      hour:'numeric',
      minute:'2-digit',
      hour12:true
    }
  ).format(d);
}

function healthDot(color){
  return `<span class="dot ${esc(color || 'RED')}"></span>`;
}

function quoteBundle(game,book){
  const market = game?.market || {};

  if(book === 'Pinnacle'){
    return market.pinnacle || null;
  }

  return market.primary_sportsbooks?.[book] ||
    market.exchanges?.[book] ||
    null;
}

function hasSpreadQuote(bundle){
  return Boolean(
    bundle?.spread?.away &&
    bundle?.spread?.home
  );
}

function hasTotalQuote(bundle){
  return Boolean(
    bundle?.total?.over &&
    bundle?.total?.under
  );
}

function selectedBookCoverage(book,rows){
  const coverage = {
    required:rows.length,
    games:0,
    spread:0,
    total:0,
    latestQuoteAt:null
  };

  rows.forEach(game=>{
    const bundle = quoteBundle(game,book);
    const spread = hasSpreadQuote(bundle);
    const total = hasTotalQuote(bundle);

    if(spread || total) coverage.games += 1;
    if(spread) coverage.spread += 1;
    if(total) coverage.total += 1;

    const acceptedQuotes = [
      ...(spread ? [bundle.spread.away, bundle.spread.home] : []),
      ...(total ? [bundle.total.over, bundle.total.under] : [])
    ];

    acceptedQuotes.forEach(quote=>{
      const timestamp = quote.last_update || quote.pulled_at;
      const parsed = timestamp ? new Date(timestamp).getTime() : NaN;
      const current = coverage.latestQuoteAt
        ? new Date(coverage.latestQuoteAt).getTime()
        : NaN;
      if(Number.isFinite(parsed) && (!Number.isFinite(current) || parsed > current)){
        coverage.latestQuoteAt = timestamp;
      }
    });
  });

  return coverage;
}

function selectedBookStatus(coverage){
  if(!coverage.required){
    return {status:'UNAVAILABLE',color:'GRAY'};
  }
  if(
    coverage.games === coverage.required &&
    coverage.spread === coverage.required &&
    coverage.total === coverage.required
  ){
    return {status:'CURRENT_HEALTHY',color:'GREEN'};
  }
  if(coverage.games > 0 && (coverage.spread > 0 || coverage.total > 0)){
    return {status:'CURRENT_PARTIAL',color:'YELLOW'};
  }
  return {status:'UNAVAILABLE',color:'RED'};
}

function fmtQuoteAge(value){
  if(!value) return '—';
  const ageSeconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if(!Number.isFinite(ageSeconds)) return '—';
  if(ageSeconds < 60) return `${ageSeconds}s`;
  if(ageSeconds < 3600) return `${Math.floor(ageSeconds / 60)}m`;
  return `${Math.floor(ageSeconds / 3600)}h`;
}

function coveragePct(value,required){
  if(!required) return 0;
  return Math.round((Number(value || 0) / required) * 100);
}

function sourceCoverage(domain,source,rows){
  const entries = rows.map(
    game => game?.standard_freshness?.[domain]?.sources?.[source] || null
  );

  const available = entries.filter(
    item => item?.participating === true
  );

  const pulls = available
    .map(item => item.pulled_at)
    .filter(Boolean)
    .sort();
  const latestPull = pulls.length
    ? pulls[pulls.length - 1]
    : null;

  const states = [...new Set(
    entries
      .map(item => item?.state)
      .filter(Boolean)
  )];

  return {
    required:rows.length,
    available:available.length,
    missing:rows.length - available.length,
    latestPull,
    states
  };
}

function coverageStatus(coverage){
  if(!coverage.required){
    return {status:'UNAVAILABLE',color:'GRAY'};
  }

  if(coverage.available === coverage.required){
    return {status:'CURRENT',color:'GREEN'};
  }

  if(coverage.available > 0){
    return {status:'PARTIAL',color:'YELLOW'};
  }

  return {status:'UNAVAILABLE',color:'RED'};
}

function sourceHealthTooltip(label,status,coverage,fallback){
  const updated =
    coverage.latestPull ||
    fallback?.latest_pull_at ||
    fallback?.latest_pulled_at ||
    fallback?.pulled_at ||
    null;

  const lines = [
    label,
    `Status: ${status.status}`,
    `Freshness: ${coverage.states.join(', ') || fallback?.status || 'UNKNOWN'}`,
    `Availability: ${coverage.available}/${coverage.required} selected-week games`,
    `Missing: ${coverage.missing}`
  ];

  if(updated){
    lines.push(`Updated: ${fmtDateTimeET(updated)}`);
  }

  if(status.status !== 'CURRENT'){
    lines.push('Reason: Source is not complete for the selected week.');
  }

  return lines.join('\n');
}

function edgeClass(edge){
  const n = Number(edge);
  if(!Number.isFinite(n)) return 'watch';
  if(n >= 3) return 'action';
  if(n >= 2) return 'lean';
  return 'watch';
}

function numericSortValue(v){
  if(
    v === null ||
    v === undefined ||
    v === ''
  ){
    return null;
  }

  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function currentRows(){
  if(!MATRIX) return [];

  let rows = MATRIX.games || [];

  if(ACTIVE_SCOPE === 'FBS'){
    rows = rows.filter(
      g => g.scope?.fbs_vs_fbs === true
    );
  }

  if(ACTIVE_WEEK !== 'ALL'){
    rows = rows.filter(
      g => String(g.week) === String(ACTIVE_WEEK)
    );
  }

  return [...rows].sort((a,b)=>{

    let av;
    let bv;

    if(SORT_KEY === 'date'){
      av = new Date(a.kickoff_time || 0).getTime();
      bv = new Date(b.kickoff_time || 0).getTime();
    }

    else if(SORT_KEY === 'home_team'){
      av = String(a.home_team || '');
      bv = String(b.home_team || '');
    }

    else if(SORT_KEY === 'spread_edge'){
      av = numericSortValue(
        a.edges?.spread?.best_edge
      );

      bv = numericSortValue(
        b.edges?.spread?.best_edge
      );
    }

    else if(SORT_KEY === 'total_edge'){
      av = numericSortValue(
        a.edges?.total?.best_edge
      );

      bv = numericSortValue(
        b.edges?.total?.best_edge
      );
    }

    else{
      const aSpread = numericSortValue(
        a.edges?.spread?.best_edge
      );

      const aTotal = numericSortValue(
        a.edges?.total?.best_edge
      );

      const bSpread = numericSortValue(
        b.edges?.spread?.best_edge
      );

      const bTotal = numericSortValue(
        b.edges?.total?.best_edge
      );

      av = Math.max(
        aSpread ?? -999,
        aTotal ?? -999
      );

      bv = Math.max(
        bSpread ?? -999,
        bTotal ?? -999
      );
    }

    if(av === null) av = -999999;
    if(bv === null) bv = -999999;

    if(SORT_KEY === 'home_team'){
      const comparison = av.localeCompare(bv, undefined, {sensitivity:'base'});
      if(comparison){
        return SORT_DIR === 'asc' ? comparison : -comparison;
      }
    }

    else if(av !== bv){
      return SORT_DIR === 'asc'
        ? av - bv
        : bv - av;
    }

    return String(a.kickoff_time || '').localeCompare(
      String(b.kickoff_time || '')
    );
  });
}

function sortArrow(key){
  if(SORT_KEY !== key) return '';

  return `
    <span class="sort-arrow">
      ${SORT_DIR === 'asc' ? '▲' : '▼'}
    </span>
  `;
}

function setSort(key){
  if(SORT_KEY === key){
    SORT_DIR =
      SORT_DIR === 'asc'
        ? 'desc'
        : 'asc';
  }else{
    SORT_KEY = key;

    SORT_DIR = (key === 'date' || key === 'home_team') ? 'asc' : 'desc';
  }

  renderMatrix();
  syncMobileControls();
}

function renderHealth(){
  const books = HEALTH?.books || {};
  const strip = document.getElementById('healthStrip');
  const rows = currentRows();
  const projectionRows = ACTIVE_WEEK === 'ALL'
    ? []
    : rows.filter(game => game.scope?.fbs_vs_fbs === true);

  const ordered = [
    'DraftKings',
    'FanDuel',
    'BetMGM',
    'Caesars',
    'Pinnacle',
    'Novig',
    'ProphetX',
    'Kalshi'
  ];

  strip.innerHTML =
    `<span class="health-title">MARKET HEALTH</span>` +
    ordered.map(book=>{
      const h = books[book] || {};
      const coverage = selectedBookCoverage(book,rows);
      const selected = selectedBookStatus(coverage);
      const title = [
        `${book} selected-week status: ${selected.status}`,
        `Selected-week games: ${coverage.games}/${coverage.required}`,
        `Spread: ${coverage.spread}/${coverage.required}`,
        `Total: ${coverage.total}/${coverage.required}`,
        coverage.latestQuoteAt ? `Latest selected-week quote: ${fmtDateTimeET(coverage.latestQuoteAt)}` : 'Latest selected-week quote: —',
        coverage.latestQuoteAt ? `Quote age: ${fmtQuoteAge(coverage.latestQuoteAt)}` : null,
        `Global diagnostic status: ${h.status || 'UNKNOWN'}`,
        `Global acquisition coverage: ${h.games_with_any_quote ?? 0} games`,
        h.participated_in_last_fast_pull === false
          ? 'Provider participation: not seen in latest global pull'
          : 'Provider participation: seen in latest global pull'
      ].filter(Boolean).join('\n');

      return `
        <span class="health-book" title="${esc(title)}">
          ${healthDot(selected.color)}
          ${esc(BOOK_ABBR[book] || book)}
          <span class="health-detail">
            ${coverage.games}/${coverage.required}
            ${coverage.latestQuoteAt ? ` · ${esc(fmtStatusTimeET(coverage.latestQuoteAt))}` : ''}
          </span>
        </span>
      `;
    }).join('');

  const ratings =
    HEALTH?.ratings_health?.sources || {};

  const ratingsStrip =
    document.getElementById('ratingsHealthStrip');

  if(ratingsStrip){
    const weekProjectionHealth =
      ACTIVE_WEEK === 'ALL'
        ? null
        : HEALTH?.projection_health?.by_week?.[String(ACTIVE_WEEK)] || null;

    const sourceItem = (domain,key,label,healthKey) => {
      const coverage = sourceCoverage(domain,key,projectionRows);
      const status = coverageStatus(coverage);
      const fallback = ratings[healthKey] || {};
      const updated = coverage.latestPull ||
        fallback.latest_pull_at ||
        fallback.latest_pulled_at ||
        fallback.pulled_at ||
        null;
      const title = sourceHealthTooltip(
        label,status,coverage,fallback
      );

      return `
        <span class="health-book" title="${esc(title)}">
          ${healthDot(status.color)}
          ${esc(label)}
          ${updated ? `<span class="health-detail">${esc(fmtStatusTimeET(updated))}</span>` : ''}
        </span>
      `;
    };

    const overall = (label,state) => {
      const resolved = state || {
        color:'GRAY',
        status: ACTIVE_WEEK === 'ALL' ? 'SELECT WEEK' : 'UNAVAILABLE'
      };

      return `
        <span class="model-health-label">
          ${healthDot(resolved.color)}
          ${esc(label)}
          <span class="health-status ${esc(resolved.color || '')}">
            ${esc(resolved.status || 'UNAVAILABLE')}
          </span>
        </span>
      `;
    };

    const spreadSources = [
      sourceItem('spread','SP+','SP+','SP+'),
      sourceItem('spread','FPI','FPI','FPI'),
      sourceItem('spread','TeamRankings','TeamRankings','TR'),
      sourceItem('spread','Sagarin Rating','Sagarin Rating','SAG'),
      sourceItem('spread','DRatings','DRatings','DR')
    ].join('');

    const totalSources = [
      sourceItem('total','SP+','SP+ Total','SP+'),
      sourceItem('total','Massey Dual','Massey Dual','MAS'),
      sourceItem('total','Sagarin Total','Sagarin Total','SAG')
    ].join('');

    ratingsStrip.innerHTML = `
      <span class="health-title">RATINGS / MODEL HEALTH</span>
      <div class="model-health-rows">
        <div class="model-health-row">
          ${overall('SPREAD',weekProjectionHealth?.spread)}
          ${spreadSources}
        </div>
        <div class="model-health-row">
          ${overall('TOTAL',weekProjectionHealth?.total)}
          ${totalSources}
        </div>
      </div>
    `;
  }

  const q = HEALTH?.api_quota || {};

  document.getElementById('topHealth').innerHTML = `
    <span title="${esc(HEALTH?.fast_market_refresh?.refresh_id || '')}">
      ${healthDot(q.color)}
      API ${esc(q.status || 'UNKNOWN')}
      · MARKET ${esc(fmtDateTimeET(HEALTH?.fast_market_refresh?.last_fast_pull_at))}
    </span>
  `;

  const mobileHealth=document.getElementById('mobileStickyHealth');
  if(mobileHealth){
    mobileHealth.innerHTML=`${healthDot(q.color)}API ${esc(q.status || 'UNKNOWN')} · UPDATED ${esc(fmtStatusTimeET(HEALTH?.fast_market_refresh?.last_fast_pull_at))}`;
  }

  document.getElementById('summaryQuota').innerHTML =
    `<span class="${String(q.color || '').toLowerCase()}">` +
    `${esc(q.credits_remaining ?? '—')} left</span>`;

  const covered = ordered.filter(
    b => selectedBookStatus(selectedBookCoverage(b,rows)).color !== 'RED'
  ).length;

  document.getElementById('summaryBooks').innerHTML =
    `<span class="green">${covered}</span> / ${ordered.length} COVERING`;


}

function fillWeeks(){
  const select = document.getElementById('weekSelect');

  const scopeRows = (MATRIX.games || []).filter(
    g => ACTIVE_SCOPE !== 'FBS' ||
         g.scope?.fbs_vs_fbs === true
  );

  const weeks = [...new Set(
    scopeRows
      .map(g => g.week)
      .filter(v => v !== null && v !== undefined)
  )].sort((a,b)=>Number(a)-Number(b));

  select.innerHTML =
    `<option value="ALL">ALL WEEKS</option>` +
    weeks
      .map(
        w => `<option value="${esc(w)}">WEEK ${esc(w)}</option>`
      )
      .join('');

  if(
    ACTIVE_WEEK === 'AUTO' ||
    (
      ACTIVE_WEEK !== 'ALL' &&
      !weeks.some(
        w => String(w) === String(ACTIVE_WEEK)
      )
    )
  ){
    ACTIVE_WEEK =
      weeks.length
        ? String(weeks[0])
        : 'ALL';
  }

  select.value = ACTIVE_WEEK;
  syncMobileControls();
}

function syncMobileControls(){
  const desktopScope=document.getElementById('scopeSelect');
  const desktopWeek=document.getElementById('weekSelect');
  const mobileScope=document.getElementById('mobileScopeSelect');
  const mobileWeek=document.getElementById('mobileWeekSelect');
  const mobileSort=document.getElementById('mobileSortSelect');
  if(mobileScope) mobileScope.value=String(ACTIVE_SCOPE);
  if(mobileWeek && desktopWeek){
    mobileWeek.innerHTML=desktopWeek.innerHTML;
    mobileWeek.value=String(ACTIVE_WEEK);
  }
  if(mobileSort) mobileSort.value=String(SORT_KEY);
  if(desktopScope) desktopScope.value=String(ACTIVE_SCOPE);
}

function getQuote(game, book, market, side){
  return game?.market
    ?.primary_sportsbooks
    ?.[book]
    ?.[market]
    ?.[side] || null;
}

function renderSummary(){
  const rows = currentRows();

  const spreadEdges = rows
    .map(g => Number(g.edges?.spread?.best_edge))
    .filter(Number.isFinite);

  const totalEdges = rows
    .map(g => Number(g.edges?.total?.best_edge))
    .filter(Number.isFinite);

  const spreadAction = spreadEdges.filter(x=>x>=3).length;
  const spreadLean = spreadEdges.filter(x=>x>=2 && x<3).length;

  const totalAction = totalEdges.filter(x=>x>=3).length;
  const totalLean = totalEdges.filter(x=>x>=2 && x<3).length;

  document.getElementById('summaryMarkets').innerHTML =
    `<span class="green">${rows.length}</span> games`;

  document.getElementById('summarySpread').innerHTML =
    `<span class="green">ACT ${spreadAction}</span> ` +
    `<span class="yellow">LEAN ${spreadLean}</span>`;

  document.getElementById('summaryTotal').innerHTML =
    `<span class="green">ACT ${totalAction}</span> ` +
    `<span class="yellow">LEAN ${totalLean}</span>`;

  const counts = rows.reduce((acc,g)=>{
    acc[g.state] = (acc[g.state] || 0) + 1;
    return acc;
  },{});

  document.getElementById('summaryState').innerHTML =
    `<span class="cyan">HYB ${counts.HYBRID || 0}</span> · ` +
    `<span class="red">ST ${counts.STALE || 0}</span>`;
}

function renderHead(){
  document.getElementById('matrixHead').innerHTML = `
    <tr>
      <th class="matrix-header-cell matchup-col">
        <span class="matchup-sort-head">
          <button class="matchup-sort-button ${SORT_KEY === 'date' ? 'active' : ''}" type="button" onclick="setSort('date')">
            DATE ${sortArrow('date') || '↕'}
          </button>
          <button class="matchup-sort-button ${SORT_KEY === 'home_team' ? 'active' : ''}" type="button" onclick="setSort('home_team')">
            HOME ${SORT_KEY === 'home_team' ? sortArrow('home_team') : 'A–Z'}
          </button>
        </span>
      </th>

      <th class="matrix-header-cell model-col spread-group"><span class="spread-label">SPREAD</span><br>MODEL</th>
      <th class="matrix-header-cell shadow-col spread-group"><span class="spread-label">SPREAD</span><br>SHADOW</th>
      <th class="matrix-header-cell best-col spread-group"><span class="spread-label">SPREAD</span><br>BEST</th>
      <th class="matrix-header-cell exchange-col spread-group"><span class="spread-label">SPREAD</span><br>EXCH</th>

      <th
        class="matrix-header-cell edge-col spread-group edge-focus sortable"
        onclick="setSort('spread_edge')"
      >
        <span class="spread-label">SPREAD</span><br>EDGE ${sortArrow('spread_edge')}
      </th>

      <th class="matrix-header-cell model-col total-group">TOTAL<br>MODEL</th>
      <th class="matrix-header-cell shadow-col total-group">TOTAL<br>SHADOW</th>
      <th class="matrix-header-cell best-col total-group">TOTAL<br>BEST</th>
      <th class="matrix-header-cell exchange-col total-group">TOTAL<br>EXCH</th>

      <th
        class="matrix-header-cell edge-col total-group edge-focus sortable"
        onclick="setSort('total_edge')"
      >
        TOTAL<br>EDGE ${sortArrow('total_edge')}
      </th>

      <th class="matrix-header-cell injury-col context-group">INJ</th>
      <th class="matrix-header-cell signal-col context-group">SIGNALS</th>
      <th class="matrix-header-cell state-col context-group">
        <span class="header-tooltip" tabindex="0">
          MODEL<br>STATE
          <span class="header-tooltip-panel" role="tooltip">
            <span class="state-definition"><strong>STALE</strong> · Market exists; Standard inputs are from the prior update cycle.</span>
            <span class="state-definition"><strong>SHADOW</strong> · New market exists and Shadow projections are available.</span>
            <span class="state-definition"><strong>HYBRID</strong> · Some weekly Standard inputs updated; the full set is incomplete.</span>
            <span class="state-definition"><strong>UPDATED</strong> · All scheduled Standard inputs for the week are current.</span>
          </span>
        </span>
      </th>
    </tr>
  `;
}

function modelDisplay(value, market){
  if(
    value === null ||
    value === undefined ||
    value === ''
  ){
    return '—';
  }

  const n = Number(value);

  if(!Number.isFinite(n)){
    return '—';
  }

  return n.toFixed(1);
}

function edgeDisplay(value){
  const n = Number(value);

  if(!Number.isFinite(n) || n < 0){
    return '—';
  }

  return Math.abs(n) < .05 ? '0' : n.toFixed(1);
}

function spreadDecision(game, side, edge, useShortName=false){
  if(!side || !Number.isFinite(Number(edge)) || Number(edge) <= 0){
    return edgeDisplay(edge);
  }
  const team = side === 'away' ? game.away_team : game.home_team;
  const displayTeam = useShortName ? (TEAM_ABBREVIATIONS[team] || team) : team;
  const slug = teamLogoSlug(team);
  return `<span class="decision-edge" title="Bet ${esc(team)}"><span class="decision-edge-main"><span class="team-logo-holder"><img src="logos/${esc(slug)}.png" alt="${esc(team)}" onerror="this.parentElement.style.display='none'"></span><span>${edgeDisplay(edge)}</span></span><span class="decision-team-name" title="${esc(team)}">${esc(displayTeam)}</span></span>`;
}

function totalDecision(side, edge){
  if(!side || !Number.isFinite(Number(edge))){
    return edgeDisplay(edge);
  }
  const label = side === 'under' ? 'U' : 'O';
  const value = edgeDisplay(edge);
  return `<span class="decision-edge total-decision" title="${side === 'under' ? 'Under' : 'Over'}"><span class="decision-edge-main"><span class="decision-side">${label}</span><span>${value}</span></span></span>`;
}

const SPREAD_COMPONENTS = ['SP+','FPI','TeamRankings','Sagarin Rating','DRatings'];
const TOTAL_COMPONENTS = ['SP+','Massey Dual','Sagarin Total'];

function spreadComponentDisplay(value, game){
  const n = Number(value);
  if(!Number.isFinite(n)) return '—';
  if(Math.abs(n) < .05) return 'PK';
  const team = n > 0 ? game.home_team : game.away_team;
  return `${esc(team)} -${Math.abs(n).toFixed(1)}`;
}

function modelTooltip(game, model, market){
  const components = market === 'spread' ? SPREAD_COMPONENTS : TOTAL_COMPONENTS;
  const values = model?.component_values || {};
  const rows = components.map(name=>{
    const value = values[name];
    const missing = value === null || value === undefined || value === '' || !Number.isFinite(Number(value));
    const shown = missing ? '—' : market === 'spread' ? spreadComponentDisplay(value,game) : Number(value).toFixed(1);
    const label = name === 'Sagarin Rating' ? 'Sagarin' : name;
    return `<span class="model-component ${missing?'missing':''}"><span>${esc(label)}</span><span>${shown}</span></span>`;
  }).join('');
  const value = market === 'spread' ? model?.value_home_line : model?.value_total;
  return `<span class="model-tooltip" data-no-game-select tabindex="0" onmouseenter="positionModelTooltip(this)" onmouseleave="closeModelTooltip(this)" onfocus="positionModelTooltip(this)" onblur="closeModelTooltip(this)"><span>${modelDisplay(value,market)}</span><span class="model-tooltip-panel" role="tooltip">${rows}</span></span>`;
}

function positionModelTooltip(trigger){
  const panel = trigger?.querySelector('.model-tooltip-panel');
  if(!panel) return;
  trigger.classList.add('open');
  panel.style.visibility = 'hidden';
  panel.style.left = '0px';
  panel.style.top = '0px';
  const rect = trigger.getBoundingClientRect();
  const width = panel.offsetWidth;
  const height = panel.offsetHeight;
  const gap = 7;
  const margin = 8;
  let left = rect.left + (rect.width - width) / 2;
  left = Math.max(margin, Math.min(left, window.innerWidth - width - margin));
  let top = rect.top - height - gap;
  if(top < margin){
    top = rect.bottom + gap;
  }
  top = Math.max(margin, Math.min(top, window.innerHeight - height - margin));
  panel.style.left = `${Math.round(left)}px`;
  panel.style.top = `${Math.round(top)}px`;
  panel.style.visibility = 'visible';
}

function closeModelTooltip(trigger){
  const panel = trigger?.querySelector('.model-tooltip-panel');
  if(panel) panel.style.visibility = '';
  trigger?.classList.remove('open');
}


const TEAM_LOGO_SLUGS = {
  'Texas A&M':'texas-a-m'
};

function teamLogoSlug(team){
  if(!team) return '';

  if(TEAM_LOGO_SLUGS[team]){
    return TEAM_LOGO_SLUGS[team];
  }

  return String(team)
    .toLowerCase()
    .replace(/&/g, 'a')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function compositeRankClass(rank){
  const value=Number(rank);
  if(!Number.isInteger(value) || value<1) return '';
  if(value<=28) return 'rank-tier-1';
  if(value<=56) return 'rank-tier-2';
  if(value<=83) return 'rank-tier-3';
  if(value<=111) return 'rank-tier-4';
  if(value<=138) return 'rank-tier-5';
  return '';
}

function matchupTeam(team,rank,score=null){
  const slug = teamLogoSlug(team);
  const value=Number(rank);
  const valid=Number.isInteger(value) && value>=1 && value<=138;
  const scoreHtml=score===null || score===undefined || score==='' ? '' : `<span class="matchup-live-score">${esc(score)}</span>`;
  return `<div class="matchup-team"><span class="team-logo-holder"><img src="logos/${esc(slug)}.png" alt="${esc(team)}" onerror="this.parentElement.style.display='none'"></span><span class="team-composite-rank ${compositeRankClass(rank)}" title="Canonical composite rank">${valid?esc(value):'—'}</span><span class="matchup-team-name">${esc(team)}</span>${scoreHtml}</div>`;
}

function liveGameDisplay(game){
  const status=String(game?.live_status || '').toLowerCase();
  const hasScores=game?.live_away_score!==null && game?.live_away_score!==undefined &&
                  game?.live_home_score!==null && game?.live_home_score!==undefined;

  if(status==='in_progress'){
    const period=Number(game?.live_period);
    const periodText=Number.isFinite(period) ? `Q${period}` : 'LIVE';
    const clock=game?.live_clock ? ` · ${game.live_clock}` : '';
    return {
      active:true,
      label:`LIVE · ${periodText}${clock}`,
      awayScore:hasScores ? game.live_away_score : null,
      homeScore:hasScores ? game.live_home_score : null
    };
  }

  if(status==='final' || status==='completed'){
    return {
      active:true,
      label:'FINAL',
      awayScore:hasScores ? game.live_away_score : null,
      homeScore:hasScores ? game.live_home_score : null
    };
  }

  return {
    active:false,
    label:null,
    awayScore:null,
    homeScore:null
  };
}

function signalChip(team, count){
  const n = Number(count);

  if(!team || !Number.isFinite(n) || n <= 0){
    return '';
  }

  const slug = teamLogoSlug(team);

  return `
    <span
      class="signal-chip"
      title="${esc(team)} · ${n} betting signal${n === 1 ? '' : 's'}"
    >
      <span class="team-logo-holder"><img
        class="signal-logo"
        src="logos/${esc(slug)}.png"
        alt="${esc(team)}"
        onerror="this.parentElement.style.display='none'"
      ></span>
      <span class="signal-count">×${n}</span>
    </span>
  `;
}

function signalCell(game){
  const s = game?.betting_signals;

  if(!s || !s.total_count){
    return `<span class="signal-placeholder">—</span>`;
  }

  const chips = [
    signalChip(
      s.away?.team,
      s.away?.count
    ),
    signalChip(
      s.home?.team,
      s.home?.count
    )
  ].filter(Boolean);

  return `
    <div class="signal-stack">
      ${chips.join('')}
    </div>
  `;
}



function shadowTeamChip(team,ready){
  const slug=teamLogoSlug(team);
  return `<span class="shadow-team-chip" title="${esc(team)} · ${ready?'Shadow input ready':'Shadow input not ready'}"><span class="team-logo-holder"><img src="logos/${esc(slug)}.png" alt="${esc(team)}" onerror="this.parentElement.style.display='none'"></span><span class="shadow-team-mark ${ready?'ready':'waiting'}">${ready?'✓':'✕'}</span></span>`;
}

function shadowDisplay(game, model, market){
  const readiness=game?.shadow_readiness||{};
  const awayReady=Boolean(readiness[`away_${market}_shadow_ready`]);
  const homeReady=Boolean(readiness[`home_${market}_shadow_ready`]);
  const readyCount=Number(awayReady)+Number(homeReady);
  const value=market==='spread'?model?.value_home_line:model?.value_total;
  const available=readyCount===2 && model?.selection_status==='AVAILABLE' && value!==null && value!==undefined;
  const label=available?modelDisplay(value,market):(readyCount===0?'WAIT':readyCount===1?'PARTIAL':'UNAVAILABLE');
  return `<span class="shadow-team-state"><span class="shadow-team-icons">${shadowTeamChip(game.away_team,awayReady)}${shadowTeamChip(game.home_team,homeReady)}</span><span class="shadow-state-label ${available?'shadow-ready':'shadow-wait'}">${label}</span></span>`;
}

const BOOK_LOGOS = {
  DraftKings:'draftkings', FanDuel:'fanduel', BetMGM:'betmgm',
  Caesars:'caesars', Pinnacle:'pinnacle', Novig:'novig',
  ProphetX:'prophetx', Kalshi:'kalshi'
};

function elapsedMinutes(value){
  const stamp=new Date(value).getTime();
  return Number.isFinite(stamp) ? Math.max(0,(Date.now()-stamp)/60000) : null;
}

function ageLabel(value){
  const minutes=elapsedMinutes(value);
  if(minutes===null) return 'age unavailable';
  if(minutes<1) return 'less than 1 minute ago';
  if(minutes<60) return `${Math.floor(minutes)} minutes ago`;
  const hours=Math.floor(minutes/60);
  return `${hours} hour${hours===1?'':'s'} ago`;
}

function openerRecency(value){
  const minutes=elapsedMinutes(value);
  if(minutes===null || minutes>90) return '';
  return minutes<=30 ? 'open-new' : 'open-recent';
}

function compactOpenerTimeET(value){
  if(!value) return '—';
  const opened=new Date(value);
  if(Number.isNaN(opened.getTime())) return '—';
  const dateKey=d=>new Intl.DateTimeFormat('en-CA',{
    timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'
  }).format(d);
  if(dateKey(opened)===dateKey(new Date())) return fmtStatusTimeET(value);
  return new Intl.DateTimeFormat('en-US',{
    timeZone:'America/New_York',month:'numeric',day:'numeric',
    hour:'numeric',minute:'2-digit',hour12:true
  }).format(opened);
}

function movementRecency(move){
  const minutes=elapsedMinutes(move?.detected_at);
  if(minutes===null || minutes>90) return '';
  const ids=MATRIX?.fast_market_refresh?.recent_completed_refresh_ids || [];
  const generation=ids.indexOf(String(move?.detected_refresh_id || ''));
  if(minutes<=15 || generation===0) return 'move-very-recent';
  if(minutes<=45 || generation===1 || generation===2) return 'move-recent';
  return 'move-older-recent';
}

function moveGlyph(direction){
  return direction==='UP'?'▲':direction==='DOWN'?'▼':'↔';
}

function movementTitle(game,move){
  if(!move) return '';
  const side=move.side==='away'?game.away_team:move.side==='home'?game.home_team:'';
  const transition=move.market==='spread'
    ? `${side ? `${side} ` : ''}${fmtLine(move.old_line)} → ${fmtLine(move.new_line)}`
    : `${Number(move.old_line)} → ${Number(move.new_line)}`;
  const magnitude=move.market==='spread'
    ? `Line moved ${move.direction}: ${move.magnitude_old} → ${move.magnitude_new}`
    : `Line moved ${move.direction}`;
  const previous=Number(move.previous_qualifying_moves)>0
    ? `\nPrevious qualifying moves: ${move.previous_qualifying_moves}`:'';
  return `${game.away_team} @ ${game.home_team}\n${move.book} ${move.market}\n${transition}\n${magnitude}\nDetected ${fmtDateTimeET(move.detected_at)} · ${ageLabel(move.detected_at)}\nDetected refresh: ${move.detected_refresh_id || 'unavailable'}\nProvider quote time: ${move.quote_timestamp ? fmtDateTimeET(move.quote_timestamp) : 'unavailable'}${previous}`;
}

function compactQuote(q, market, game){
  if(!q) return '—';

  const book = q.book || '';
  const logo = BOOK_LOGOS[book] || 'default';
  const line = market === 'spread'
    ? fmtLine(q.line)
    : `${q.side === 'under' ? 'U' : 'O'}${Number.isFinite(Number(q.line)) ? Number(q.line) : '—'}`;
  const price = fmtPrice(q.price) || '—';
  const move=q.last_material_move;
  const moveClass=movementRecency(move);

  return `
    <span class="market-best ${moveClass?'has-move':''}" title="${esc(book)}">
      <img class="market-book-logo" src="logos/books/${esc(logo)}.png" alt="${esc(book)}">
      <span class="market-line">${line}</span>
      <span class="market-juice">${price}</span>
      ${move ? `<span class="move-marker ${moveClass}" data-move-detected-at="${esc(move.detected_at || '')}" data-move-refresh-id="${esc(move.detected_refresh_id || '')}" title="${esc(movementTitle(game,move))}">${moveGlyph(move.direction)}</span>` : ''}
    </span>
  `;
}

function compactOpen(game,market){
  const opener=game.market?.openers?.[market];
  if(!opener) return '<span class="open-missing">NOT TRACKED</span>';
  const logo=BOOK_LOGOS[opener.book] || 'default';
  const line=market==='spread'
    ? fmtLine(opener.line)
    : `${Number.isFinite(Number(opener.line)) ? Number(opener.line) : '—'}`;
  const price=fmtPrice(opener.price) || '—';
  const recency=openerRecency(opener.observed_at);
  const label=recency==='open-new'?'NEW':recency==='open-recent'?'RECENT':'';
  const tooltip=`Opened ${fmtDateTimeET(opener.observed_at)} · ${opener.book || opener.source || 'Unknown source'} · ${line} ${price}`;
  return `<span class="open-cell" data-opened-at="${esc(opener.observed_at || '')}" title="${esc(tooltip)}"><span class="open-quote"><img class="market-book-logo" src="logos/books/${esc(logo)}.png" alt="${esc(opener.book || '')}"><span class="open-line">${line}</span><span class="open-price">${price}</span><span class="open-meta"><span class="open-time">${esc(compactOpenerTimeET(opener.observed_at))}</span><span class="recency-marker ${recency}">${label}</span></span></span></span>`;
}

function updateMatrixRecencyMarkers(){
  document.querySelectorAll('[data-opened-at]').forEach(cell=>{
    const marker=cell.querySelector('.recency-marker');
    if(!marker)return;
    marker.classList.remove('open-new','open-recent');
    const state=openerRecency(cell.dataset.openedAt);
    if(state)marker.classList.add(state);
    marker.textContent=state==='open-new'?'NEW':state==='open-recent'?'RECENT':'';
  });
  document.querySelectorAll('[data-move-detected-at]').forEach(marker=>{
    const move={detected_at:marker.dataset.moveDetectedAt,detected_refresh_id:marker.dataset.moveRefreshId};
    marker.classList.remove('move-very-recent','move-recent','move-older-recent');
    const state=movementRecency(move);
    if(state)marker.classList.add(state);
    marker.closest('.market-best')?.classList.toggle('has-move',Boolean(state));
    marker.title=marker.title.replace(
      /Detected [^\n]*/,
      `Detected ${fmtDateTimeET(move.detected_at)} · ${ageLabel(move.detected_at)}`
    );
  });
}

function mobileMetric(label,content,extraClass=''){
  return `<div class="mobile-metric ${extraClass}"><span class="mobile-metric-label">${label}</span>${content}</div>`;
}

function renderMobileMatrix(rows){
  const mobile=document.getElementById('mobileMatrix');
  if(!mobile) return;
  const rail=document.querySelector('.right-rail');
  const grid=document.querySelector('.command-grid');
  if(rail && grid && rail.parentElement!==grid) grid.appendChild(rail);
  mobile.innerHTML=rows.map(game=>{
    const sprSide=game.edges?.spread?.best_side;
    const totSide=game.edges?.total?.best_side;
    const sprEdge=sprSide?game.edges?.spread?.best_edge:null;
    const totEdge=totSide?game.edges?.total?.best_edge:null;
    const sprBest=sprSide?game.market?.best_sportsbook?.spread?.[sprSide]:null;
    const totBest=totSide?game.market?.best_sportsbook?.total?.[totSide]:null;
    const sprEx=sprSide?game.market?.best_exchange?.spread?.[sprSide]:null;
    const totEx=totSide?game.market?.best_exchange?.total?.[totSide]:null;
    const sprShadow=game.models?.shadow_spread;
    const totShadow=game.models?.shadow_total;
    const live=liveGameDisplay(game);
    return `<article class="mobile-game-card game-start ${String(game.game_id)===String(SELECTED_GAME_ID)?'game-selected':''}" data-game-id="${esc(game.game_id)}">
      <div class="mobile-game-head">
        <div class="mobile-kickoff">${live.active
          ? `<span class="game-live-state">${esc(live.label)}</span>`
          : `<span>${esc(fmtKickoffDateET(game.kickoff_time))}</span><span>${esc(fmtKickoffTimeET(game.kickoff_time))}</span>`
        }${game.neutral_site?'<span class="neutral-marker">NEUTRAL</span>':''}</div>
        <div class="mobile-matchup">${matchupTeam(game.away_team,game.team_composite_rank?.away,live.awayScore)}${matchupTeam(game.home_team,game.team_composite_rank?.home,live.homeScore)}</div>
        <div class="mobile-card-state"><span class="badge ${esc(game.state)}">${esc(game.state)}</span></div>
      </div>
      <div class="mobile-market-band spread-group">
        <div class="mobile-band-title">SPREAD</div>
        <div class="mobile-band-grid">
          ${mobileMetric('EDGE',`<span class="edge ${edgeClass(sprEdge)}">${spreadDecision(game,sprSide,sprEdge,true)}</span>`,'edge-focus')}
          ${mobileMetric('BEST',compactQuote(sprBest,'spread',game))}
          ${mobileMetric('MODEL',modelTooltip(game,game.models?.standard_spread,'spread'))}
          ${mobileMetric('SHADOW',shadowDisplay(game,sprShadow,'spread'))}
          ${mobileMetric('EXCH',compactQuote(sprEx,'spread',game))}
        </div>
      </div>
      <div class="mobile-market-band total-group">
        <div class="mobile-band-title">TOTAL</div>
        <div class="mobile-band-grid">
          ${mobileMetric('EDGE',`<span class="edge ${edgeClass(totEdge)}">${totalDecision(totSide,totEdge)}</span>`,'edge-focus')}
          ${mobileMetric('BEST',compactQuote(totBest,'total',game))}
          ${mobileMetric('MODEL',modelTooltip(game,game.models?.standard_total,'total'))}
          ${mobileMetric('SHADOW',shadowDisplay(game,totShadow,'total'))}
          ${mobileMetric('EXCH',compactQuote(totEx,'total',game))}
        </div>
      </div>
      <div class="mobile-game-foot"><span class="mobile-foot-label">INJ —</span><span class="mobile-foot-signals"><span class="mobile-foot-label">SIGNALS</span>${signalCell(game)}</span></div>
      ${String(game.game_id)===String(SELECTED_GAME_ID)?'<div class="mobile-activity-slot"></div>':''}
    </article>`;
  }).join('');
  mobile.querySelectorAll('.mobile-game-card[data-game-id]').forEach(card=>card.addEventListener('click',event=>{
    if(event.target.closest('button,a,input,select,summary,[role="button"],[data-no-game-select]')) return;
    const game=rows.find(item=>String(item.game_id)===String(card.dataset.gameId));
    if(game) selectActivityGame(game);
  }));
  placeActivityRail();
}

function isMobileView(){
  return window.matchMedia('(max-width:900px)').matches;
}

function placeActivityRail(){
  const rail=document.querySelector('.right-rail');
  const grid=document.querySelector('.command-grid');
  if(!rail || !grid) return;
  if(isMobileView() && SELECTED_GAME_ID){
    const selected=[...document.querySelectorAll('.mobile-game-card[data-game-id]')]
      .find(card=>String(card.dataset.gameId)===String(SELECTED_GAME_ID));
    const slot=selected?.querySelector('.mobile-activity-slot');
    if(slot && rail.parentElement!==slot) slot.appendChild(rail);
    return;
  }
  if(rail.parentElement!==grid) grid.appendChild(rail);
}

function renderMatrix(){
  renderHead();

  const rows = currentRows();
  const body = document.getElementById('matrixBody');

  body.innerHTML = rows.map(game=>{

    const sprSide =
      game.edges?.spread?.best_side;

    const totSide =
      game.edges?.total?.best_side;

    const sprEdge =
      sprSide
        ? game.edges?.spread?.best_edge
        : null;

    const totEdge =
      totSide
        ? game.edges?.total?.best_edge
        : null;

    const sprBest =
      sprSide
        ? game.market?.best_sportsbook?.spread?.[sprSide]
        : null;

    const totBest =
      totSide
        ? game.market?.best_sportsbook?.total?.[totSide]
        : null;

    const sprEx =
      sprSide
        ? game.market?.best_exchange?.spread?.[sprSide]
        : null;

    const totEx =
      totSide
        ? game.market?.best_exchange?.total?.[totSide]
        : null;

    const sprModel =
      game.models?.standard_spread?.value_home_line;

    const sprShadow =
      game.models?.shadow_spread;

    const totModel =
      game.models?.standard_total?.value_total;

    const totShadow =
      game.models?.shadow_total;

    const live=liveGameDisplay(game);

    return `
      <tr class="game-start ${String(game.game_id)===String(SELECTED_GAME_ID)?'game-selected':''}" data-game-id="${esc(game.game_id)}">

        <td class="matchup-col">
          <div class="matchup-kickoff">
            ${live.active
              ? `<span class="game-live-state">${esc(live.label)}</span>`
              : `<span class="game-date">${esc(fmtKickoffDateET(game.kickoff_time))}</span>
                 <span class="game-time">${esc(fmtKickoffTimeET(game.kickoff_time))}</span>`
            }
            ${game.neutral_site ? '<span class="neutral-marker" title="Neutral site">N</span>' : ''}
          </div>
          ${matchupTeam(game.away_team,game.team_composite_rank?.away,live.awayScore)}
          ${matchupTeam(game.home_team,game.team_composite_rank?.home,live.homeScore)}
        </td>

        <td class="model-col spread-group">
          ${modelTooltip(game, game.models?.standard_spread, 'spread')}
        </td>

        <td class="shadow-col spread-group">
          ${shadowDisplay(game, sprShadow, 'spread')}
        </td>

        <td class="best-col spread-group">
          ${compactQuote(sprBest, 'spread', game)}
        </td>

        <td class="exchange-col spread-group">
          ${compactQuote(sprEx, 'spread', game)}
        </td>

        <td class="edge-col spread-group edge-focus">
          <span class="edge ${edgeClass(sprEdge)}">
            ${spreadDecision(game, sprSide, sprEdge)}
          </span>
        </td>

        <td class="model-col total-group">
          ${modelTooltip(game, game.models?.standard_total, 'total')}
        </td>

        <td class="shadow-col total-group">
          ${shadowDisplay(game, totShadow, 'total')}
        </td>

        <td class="best-col total-group">
          ${compactQuote(totBest, 'total', game)}
        </td>

        <td class="exchange-col total-group">
          ${compactQuote(totEx, 'total', game)}
        </td>

        <td class="edge-col total-group edge-focus">
          <span class="edge ${edgeClass(totEdge)}">
            ${totalDecision(totSide, totEdge)}
          </span>
        </td>

        <td class="injury-col context-group">
          <span class="injury-placeholder">—</span>
        </td>

        <td class="signal-col context-group">
          ${signalCell(game)}
        </td>

        <td class="state-col context-group">
          <span class="badge ${esc(game.state)}">
            ${esc(game.state)}
          </span>
        </td>

      </tr>
    `;
  }).join('');

  body.querySelectorAll('tr[data-game-id]').forEach(row=>row.addEventListener('click',event=>{
    if(event.target.closest('button,a,input,select,summary,[role="button"],[data-no-game-select]')) return;
    const game=rows.find(item=>String(item.game_id)===String(row.dataset.gameId));
    if(game) selectActivityGame(game);
  }));

  renderMobileMatrix(rows);

  renderSummary();
}

function activityCategory(event){
  if(event?.prior_context) return 'POSTGAME';
  if(['MARKET_OPENED','PINNACLE_OPENED'].includes(event?.event_type)) return 'OPEN';
  if(String(event?.event_type || '').startsWith('MARKET_') || String(event?.event_type || '').startsWith('PINNACLE_')) return 'MARKET';
  if(['FINAL_POSTED','POSTGAME_REFRESHED'].includes(event?.event_type)) return 'POSTGAME';
  if(String(event?.event_type || '').startsWith('PROVIDER_')) return 'DATA';
  return 'MODEL';
}

function activityTime(value){
  if(!value) return '—';
  const d = new Date(value);
  if(Number.isNaN(d.getTime())) return esc(value);
  return new Intl.DateTimeFormat('en-US',{
    timeZone:'America/New_York',
    month:'numeric',day:'numeric',hour:'numeric',minute:'2-digit'
  }).format(d);
}

function activityMatchup(event){
  return event.away_team && event.home_team
    ? `${event.away_team} @ ${event.home_team}`
    : '';
}

function activityBooks(event){
  const books = event?.payload?.books || (event.book ? [event.book] : []);
  return [...new Set(books.filter(Boolean))];
}

function activityBookLogos(event){
  return activityBooks(event).map(book=>{
    const logo=BOOK_LOGOS[book];
    const fallback=BOOK_ABBR[book] || book;
    if(!logo) return `<span class="activity-book-fallback" style="display:inline" title="${esc(book)}">${esc(fallback)}</span>`;
    return `<span title="${esc(book)}"><img class="activity-book-logo" src="logos/books/${esc(logo)}.png" alt="${esc(book)}" onerror="this.style.display='none';this.nextElementSibling.style.display='inline'"><span class="activity-book-fallback">${esc(fallback)}</span></span>`;
  }).join('');
}

function activityTitle(event){
  const p = event.payload || {};
  const book = p.sportsbook ? `${BOOK_ABBR[p.sportsbook] || p.sportsbook} ` : '';
  const labels = {
    MARKET_OPENED:'Market opened', PINNACLE_OPENED:'Pinnacle open',
    MARKET_MOVE:'Market move', PINNACLE_MOVE:'Pinnacle move', MARKET_FOLLOW:'Market follow',
    RATINGS_UPDATED:'Ratings update',
    MODEL_STATE_CHANGED:`${p.domain || 'Model'} state changed`,
    SHADOW_SPREAD_READY:'Shadow spread ready', SHADOW_TOTAL_READY:'Shadow total ready',
    FINAL_POSTED:'Final posted', POSTGAME_REFRESHED:'Postgame refreshed',
    PROVIDER_DEGRADED:`${event.book || 'Provider'} degraded`,
    PROVIDER_RECOVERED:`${event.book || 'Provider'} recovered`,
    PROVIDER_UNAVAILABLE:`${event.book || 'Provider'} unavailable`,
    PRIOR_GAME_STATUS:'Prior game status'
  };
  return labels[event.event_type] || String(event.event_type || 'Activity').replaceAll('_',' ');
}

function activityDetail(event){
  const p = event.payload || {};
  if(event.event_type==='PRIOR_GAME_STATUS') return String(event.prior_context?.status || 'WAITING').replaceAll('_',' ');
  if(['MARKET_MOVE','PINNACLE_MOVE','MARKET_FOLLOW'].includes(event.event_type)){
    const prefix=event.event_type==='PINNACLE_MOVE'?'Pinnacle ':event.event_type==='MARKET_FOLLOW'?'Market follow ':'';
    const team=event.market==='spread' && event.home_team ? `${event.home_team} ` : '';
    const oldValue=event.market==='total'?(event.old_line ?? '—'):fmtLine(event.old_line);
    const newValue=event.market==='total'?(event.new_line ?? '—'):fmtLine(event.new_line);
    return `${prefix}${team}${oldValue} → ${newValue}`;
  }
  if(['MARKET_OPENED','PINNACLE_OPENED'].includes(event.event_type)){
    if(event.market==='spread') return `Spread opened ${event.home_team || ''} ${fmtLine(event.new_line)}`;
    return `Total opened ${event.new_line ?? '—'}`;
  }
  if(event.event_type === 'RATINGS_UPDATED') return (p.sources || []).join(' · ');
  if(event.event_type === 'MODEL_STATE_CHANGED'){
    if(p.old_state !== p.new_state) return `${p.old_state || '—'} → ${p.new_state || '—'}`;
    if(p.old_spread_authority !== p.spread_authority) return `Spread ${p.old_spread_authority || '—'} → ${p.spread_authority || '—'}`;
    return `Total ${p.old_total_authority || '—'} → ${p.total_authority || '—'}`;
  }
  if(event.event_type === 'SHADOW_SPREAD_READY') return 'Spread Shadow available';
  if(event.event_type === 'SHADOW_TOTAL_READY') return 'Total Shadow available';
  if(event.event_type === 'FINAL_POSTED') return `Final: ${event.home_team || 'Home'} ${p.home_score ?? '—'}, ${event.away_team || 'Away'} ${p.away_score ?? '—'}`;
  if(String(event.event_type || '').startsWith('PROVIDER_')){
    const c=p.current || {};
    return `Week ${event.week ?? '—'} · ${c.games ?? 0}/${c.required ?? 0} games · S ${c.spread ?? 0} · T ${c.total ?? 0}`;
  }
  return p.reason || p.market || p.status || '';
}

function activityRefreshTimestamp(){
  const refreshes=ACTIVITY?.pipeline_refreshes || {};
  if(ACTIVITY_FILTER==='MARKET') return refreshes.market || HEALTH?.fast_market_refresh?.last_fast_pull_at;
  if(ACTIVITY_FILTER==='MODEL') return refreshes.model || HEALTH?.ratings_health?.generated_at;
  if(ACTIVITY_FILTER==='POSTGAME') return refreshes.postgame;
  return [refreshes.market,refreshes.model,refreshes.postgame]
    .filter(Boolean).sort((a,b)=>new Date(b)-new Date(a))[0] || ACTIVITY?.built_at;
}

function selectedGame(){
  return (MATRIX?.games || []).find(game=>String(game.game_id)===String(SELECTED_GAME_ID)) || null;
}

function fallbackGameActivity(game){
  const openers=(ACTIVITY?.opening_markets || {})[game.game_id] || {};
  return {
    schema_version:'war-room-game-activity-fallback-v1',
    built_at:ACTIVITY?.built_at,
    latest_refresh_id:ACTIVITY?.latest_refresh_id,
    game_id:game.game_id,season:game.season,week:game.week,
    away_team:game.away_team,home_team:game.home_team,
    openers,
    prior_games:((ACTIVITY?.game_contexts || {})[game.game_id] || {}).prior_games || {},
    events:[...openerEventsFromSummary(game,openers),
      ...(ACTIVITY?.events || []).filter(event=>
        String(event.game_id)===String(game.game_id) && !['MARKET_OPENED','PINNACLE_OPENED'].includes(event.event_type)
      )].sort((a,b)=>new Date(b.observed_at||0)-new Date(a.observed_at||0))
  };
}

function openerEventsFromSummary(game,openers){
  return Object.entries(openers || {}).filter(([,row])=>row).map(([key,row])=>({
    event_id:`static-opener-${game.game_id}-${key}`,
    event_type:key.startsWith('pinnacle_')?'PINNACLE_OPENED':'MARKET_OPENED',
    entity_type:'market_opener',source_system:'canonical_market_history',
    observed_at:row.observed_at,event_timestamp:row.observed_at,
    game_id:game.game_id,season:game.season,week:game.week,
    away_team:game.away_team,home_team:game.home_team,
    book:row.book,market:row.market,new_line:row.line,new_price:row.price,
    payload:{opening_book:row.book,opener_key:key,provenance:row.provenance,authority:row.authority},
    metadata:{opening_book:row.book,opener_key:key,provenance:row.provenance,authority:row.authority}
  }));
}

async function fetchGameActivity(game){
  const cacheKey=`${ACTIVITY_VERSION || ACTIVITY?.built_at || 'static'}|${game.game_id}`;
  if(GAME_ACTIVITY_CACHE.has(cacheKey)) return GAME_ACTIVITY_CACHE.get(cacheKey);
  let payload;
  try{
    const separator=LIVE_ACTIVITY_URL.includes('?')?'&':'?';
    const response=await fetch(`${LIVE_ACTIVITY_URL}${separator}game_id=${encodeURIComponent(game.game_id)}&v=${Date.now()}`,{cache:'no-store'});
    if(!response.ok) throw new Error(`Game Activity HTTP ${response.status}`);
    payload=await response.json();
  }catch(_error){
    payload=fallbackGameActivity(game);
  }
  GAME_ACTIVITY_CACHE.set(cacheKey,payload);
  return payload;
}

function applySelectedRow(){
  document.querySelectorAll('tr[data-game-id],.mobile-game-card[data-game-id]').forEach(row=>{
    row.classList.toggle('game-selected',String(row.dataset.gameId)===String(SELECTED_GAME_ID));
  });
}

async function selectActivityGame(game,{toggle=true}={}){
  if(!game?.game_id) return;
  if(toggle && String(SELECTED_GAME_ID)===String(game.game_id)){
    clearActivityGame();
    return;
  }
  SELECTED_GAME_ID=String(game.game_id);
  SELECTED_GAME_ACTIVITY=null;
  renderMobileMatrix(currentRows());
  applySelectedRow();
  renderActivity();
  const requested=SELECTED_GAME_ID;
  const payload=await fetchGameActivity(game);
  if(requested!==SELECTED_GAME_ID) return;
  SELECTED_GAME_ACTIVITY=payload;
  renderActivity();
}

function clearActivityGame(){
  SELECTED_GAME_ID=null;
  SELECTED_GAME_ACTIVITY=null;
  renderMobileMatrix(currentRows());
  applySelectedRow();
  renderActivity();
}

function reconcileSelectedGame(){
  if(!SELECTED_GAME_ID) return;
  if(!currentRows().some(game=>String(game.game_id)===String(SELECTED_GAME_ID))){
    SELECTED_GAME_ID=null;
    SELECTED_GAME_ACTIVITY=null;
  }
}

function priorContextEvents(){
  if(!SELECTED_GAME_ID) return [];
  const gameData=SELECTED_GAME_ACTIVITY || fallbackGameActivity(selectedGame() || {});
  const seen=new Set();
  const output=[];
  for(const role of ['away','home']){
    const prior=gameData?.prior_games?.[role];
    const selectedTeam=prior?.selected_team || selectedGame()?.[`${role}_team`];
    if(!prior || !prior.game_id) continue;
    const rows=prior.events || [];
    if(!rows.length) continue;
    rows.forEach(event=>{
      if(seen.has(event.event_id)) return;
      seen.add(event.event_id);
      output.push({...event,prior_context:{role,selected_team:selectedTeam,status:prior.status}});
    });
  }
  return output;
}

function visibleActivity(){
  const gameData=SELECTED_GAME_ID ? (SELECTED_GAME_ACTIVITY || fallbackGameActivity(selectedGame() || {})) : null;
  const selectedEvents=gameData?.events || [];
  const priorEvents=priorContextEvents();
  const selectedHasFinal=selectedEvents.some(event=>event.event_type==='FINAL_POSTED');
  const genuineSelectedEvents=selectedEvents.filter(event=>event.entity_type!=='market_opener');
  const source=SELECTED_GAME_ID
    ? (ACTIVITY_FILTER==='POSTGAME'
      ? [...selectedEvents.filter(event=>activityCategory(event)==='POSTGAME' || (selectedHasFinal && activityCategory(event)==='MODEL')),...priorEvents]
      : ACTIVITY_FILTER==='ALL' ? genuineSelectedEvents : selectedEvents)
    : (ACTIVITY?.events || []);
  const deduped=new Set();
  return source.filter(event=>{
    const identity=`${event.event_id || ''}|${event.prior_context?.selected_team || ''}`;
    if(deduped.has(identity)) return false;
    deduped.add(identity);
    const category = activityCategory(event);
    if(SELECTED_GAME_ID && event.event_type==='RATINGS_UPDATED') return false;
    if(ACTIVITY_FILTER === 'MARKET' && !['OPEN','MARKET'].includes(category)) return false;
    if(ACTIVITY_FILTER === 'MODEL' && category !== 'MODEL') return false;
    if(ACTIVITY_FILTER === 'POSTGAME' && category !== 'POSTGAME') return false;
    if(SELECTED_GAME_ID) return event.prior_context || String(event.game_id)===String(SELECTED_GAME_ID);
    if(ACTIVE_WEEK === 'ALL') return true;
    return event.week === null || event.week === undefined || String(event.week) === String(ACTIVE_WEEK);
  });
}

async function focusActivityGame(event){
  if(!event.game_id) return;
  if(event.week !== null && event.week !== undefined && String(event.week) !== String(ACTIVE_WEEK)){
    const option = [...document.getElementById('weekSelect').options].find(o=>o.value===String(event.week));
    if(option){ ACTIVE_WEEK=String(event.week); document.getElementById('weekSelect').value=ACTIVE_WEEK; renderHealth(); renderMatrix(); }
  }
  const game=(MATRIX?.games || []).find(item=>String(item.game_id)===String(event.game_id));
  if(game) await selectActivityGame(game,{toggle:false});
  requestAnimationFrame(()=>{
    const row = [...document.querySelectorAll('tr[data-game-id],.mobile-game-card[data-game-id]')].find(el=>{
      if(el.dataset.gameId!==String(event.game_id)) return false;
      return el.offsetParent!==null;
    });
    if(!row) return;
    const matrix=document.querySelector('.matrix-scroll');
    if(matrix && getComputedStyle(matrix).display!=='none'){
      matrix.scrollTo({top:Math.max(0,row.offsetTop-(matrix.clientHeight-row.offsetHeight)/2),behavior:'smooth'});
    }else{
      row.scrollIntoView({block:'center',behavior:'smooth'});
    }
    row.classList.add('activity-flash');
    setTimeout(()=>row.classList.remove('activity-flash'),1800);
  });
}

function renderGameFocus(){
  const focus=document.getElementById('activityFocus');
  const game=selectedGame();
  if(!SELECTED_GAME_ID || !game){focus.classList.remove('active');focus.innerHTML='';return}
  focus.classList.add('active');
  focus.innerHTML=`<div class="activity-focus-head"><span class="activity-focus-game">${esc(game.away_team)} @ ${esc(game.home_team)}</span><button class="activity-clear" id="activityClear" type="button">× CLEAR</button></div>`;
  document.getElementById('activityClear').addEventListener('click',clearActivityGame);
}

function snapshotBook(book){
  if(!book) return '—';
  const logo=BOOK_LOGOS[book];
  const label=BOOK_ABBR[book] || book;
  return `<span class="snapshot-book" title="${esc(book)}">${logo?`<img src="logos/books/${esc(logo)}.png" alt="${esc(book)}" onerror="this.style.display='none'">`:''}<span>${esc(label)}</span></span>`;
}

function snapshotAuthority(model){
  const raw=model?.authority || model?.availability_status || 'UNAVAILABLE';
  return String(raw).replace('OPERATIONAL_DEGRADED','DEGRADED').replaceAll('_',' ');
}

function componentText(model,names,market,game){
  const values=model?.component_values || {};
  const labels={'TeamRankings':'TR','Sagarin Rating':'SAG','DRatings':'DR','Massey Dual':'MAS','Sagarin Total':'SAG'};
  return names.map(name=>{
    const value=values[name];
    const missing=value===null || value===undefined || !Number.isFinite(Number(value));
    const shown=missing?'—':market==='spread'?spreadComponentDisplay(value,game):Number(value).toFixed(1);
    return `${labels[name] || name} ${shown}`;
  }).join(' · ');
}

function renderMarketSnapshot(game,gameData){
  const openers=gameData?.openers || {};
  const spreadOpen=openers.spread;
  const totalOpen=openers.total;
  const spreadCurrent=game?.market?.best_sportsbook?.spread?.home;
  const totalCurrent=game?.market?.best_sportsbook?.total?.over;
  const openSpread=spreadOpen?`${esc(game.home_team)} ${fmtLine(spreadOpen.line)} ${snapshotBook(spreadOpen.book)}`:'NOT TRACKED';
  const openTotal=totalOpen?`${Number(totalOpen.line).toFixed(1)} ${snapshotBook(totalOpen.book)}`:'NOT TRACKED';
  return `<div class="snapshot-title">MARKET SNAPSHOT</div>
    <div class="snapshot-row"><span class="snapshot-key">SPREAD</span><span class="snapshot-value" title="${spreadOpen?.observed_at?`Opened ${esc(fmtDateTimeET(spreadOpen.observed_at))}`:'Opening timestamp unavailable'}">OPEN ${openSpread} · CURRENT ${spreadCurrent?`${esc(game.home_team)} ${fmtLine(spreadCurrent.line)}`:'—'}</span></div>
    <div class="snapshot-row"><span class="snapshot-key">TOTAL</span><span class="snapshot-value" title="${totalOpen?.observed_at?`Opened ${esc(fmtDateTimeET(totalOpen.observed_at))}`:'Opening timestamp unavailable'}">OPEN ${openTotal} · CURRENT ${totalCurrent?Number(totalCurrent.line).toFixed(1):'—'}</span></div>`;
}

function renderModelSnapshot(game){
  const spread=game?.models?.standard_spread || {};
  const total=game?.models?.standard_total || {};
  return `<div class="snapshot-title">MODEL SNAPSHOT</div>
    <div class="snapshot-row"><span class="snapshot-key">SPREAD</span><span class="snapshot-value">${modelDisplay(spread.value_home_line,'spread')} · ${esc(snapshotAuthority(spread))}<span class="snapshot-components">${componentText(spread,SPREAD_COMPONENTS,'spread',game)}</span></span></div>
    <div class="snapshot-row"><span class="snapshot-key">TOTAL</span><span class="snapshot-value">${modelDisplay(total.value_total,'total')} · ${esc(snapshotAuthority(total))}<span class="snapshot-components">${componentText(total,TOTAL_COMPONENTS,'total',game)}</span></span></div>`;
}

function priorStatusLine(prior){
  if(!prior?.game_id) return 'NO PRIOR GAME';
  const finalEvent=(prior.events || []).find(event=>event.event_type==='FINAL_POSTED');
  const opponent=prior.selected_team===prior.home_team?prior.away_team:prior.home_team;
  let result='';
  if(finalEvent){
    const p=finalEvent.payload || finalEvent.metadata || {};
    const selectedScore=prior.selected_team===prior.home_team?p.home_score:p.away_score;
    const opponentScore=prior.selected_team===prior.home_team?p.away_score:p.home_score;
    if(selectedScore!==null && selectedScore!==undefined && opponentScore!==null && opponentScore!==undefined){
      const outcome=Number(selectedScore)>Number(opponentScore)?'W':Number(selectedScore)<Number(opponentScore)?'L':'T';
      result=`${outcome} ${selectedScore}-${opponentScore}`;
    }
  }
  const status=String(prior.status || 'STATUS UNAVAILABLE').replaceAll('_',' ');
  return `${opponent?`vs ${opponent}`:'OPPONENT UNAVAILABLE'}${result?` · ${result}`:''} · ${status}`;
}

function currentGameStatus(game,gameData){
  const finalEvent=(gameData?.events || []).find(event=>event.event_type==='FINAL_POSTED');
  if(finalEvent){
    const p=finalEvent.payload || finalEvent.metadata || {};
    return `FINAL${p.away_score!==undefined && p.home_score!==undefined?` · ${game.away_team} ${p.away_score}, ${game.home_team} ${p.home_score}`:''}`;
  }
  const kickoff=new Date(game?.kickoff_time || 0).getTime();
  if(Number.isFinite(kickoff) && kickoff>Date.now()) return `PREGAME · ${fmtKickoffDateET(game.kickoff_time)} ${fmtKickoffTimeET(game.kickoff_time)} ET`;
  return 'STATUS UNAVAILABLE';
}

function renderPostgameSnapshot(game,gameData){
  const prior=gameData?.prior_games || {};
  return `<div class="snapshot-title">POSTGAME STATUS</div>
    <div class="snapshot-row"><span class="snapshot-key" title="${esc(game.away_team)} PRIOR">${esc(game.away_team)} PRIOR</span><span class="snapshot-value">${esc(priorStatusLine(prior.away))}</span></div>
    <div class="snapshot-row"><span class="snapshot-key" title="${esc(game.home_team)} PRIOR">${esc(game.home_team)} PRIOR</span><span class="snapshot-value">${esc(priorStatusLine(prior.home))}</span></div>
    <div class="snapshot-row"><span class="snapshot-key">CURRENT</span><span class="snapshot-value">${esc(game.away_team)} @ ${esc(game.home_team)} · ${esc(currentGameStatus(game,gameData))}</span></div>`;
}

function renderSelectedSnapshot(){
  const snapshot=document.getElementById('activitySnapshot');
  const game=selectedGame();
  if(!game || !SELECTED_GAME_ID || ACTIVITY_FILTER==='ALL'){
    snapshot.classList.remove('active');snapshot.innerHTML='';return;
  }
  const gameData=SELECTED_GAME_ACTIVITY || fallbackGameActivity(game);
  snapshot.innerHTML=ACTIVITY_FILTER==='MARKET'
    ? renderMarketSnapshot(game,gameData)
    : ACTIVITY_FILTER==='MODEL'
      ? renderModelSnapshot(game)
      : renderPostgameSnapshot(game,gameData);
  snapshot.classList.add('active');
}

function renderActivity(){
  placeActivityRail();
  const events = visibleActivity();
  const latestIds = new Set(ACTIVITY?.latest_refresh_event_ids || []);
  const latestEvents = (ACTIVITY?.events || []).filter(event=>
    latestIds.has(event.event_id) &&
    (ACTIVE_WEEK === 'ALL' || event.week === null || event.week === undefined || String(event.week) === String(ACTIVE_WEEK))
  );
  const since = {open:0,moves:0,ratings:0,model:0,final:0};
  latestEvents.forEach(event=>{
    if(['MARKET_OPENED','PINNACLE_OPENED'].includes(event.event_type)) since.open++;
    else if(['MARKET_MOVE','PINNACLE_MOVE','MARKET_FOLLOW'].includes(event.event_type)) since.moves++;
    else if(event.event_type==='RATINGS_UPDATED') since.ratings++;
    else if(['MODEL_STATE_CHANGED','SHADOW_SPREAD_READY','SHADOW_TOTAL_READY'].includes(event.event_type)) since.model++;
    else if(['FINAL_POSTED','POSTGAME_REFRESHED'].includes(event.event_type)) since.final++;
  });
  const compact = [
    ['OPEN',since.open],['MOVES',since.moves],['RATINGS',since.ratings],
    ['MODEL',since.model],['FINAL',since.final]
  ].filter(([,count])=>Number(count)>0).map(([label,count])=>`${count} ${label}`).join(' · ');
  const activityRefresh=activityRefreshTimestamp();
  const updated=document.getElementById('activityUpdated');
  updated.textContent=`UPDATED ${fmtDateTimeET(activityRefresh)}`;
  updated.title=`${ACTIVITY_FILTER} pipeline refresh${ACTIVITY?.latest_refresh_id ? ` · ${ACTIVITY.latest_refresh_id}` : ''}`;
  const summary=document.getElementById('activitySummary');
  summary.classList.toggle('hidden',Boolean(SELECTED_GAME_ID));
  summary.innerHTML=`<span class="activity-summary-label">SINCE LAST REFRESH</span>${esc(compact || 'NO MATERIAL CHANGES')}`;
  renderGameFocus();
  renderSelectedSnapshot();
  document.getElementById('activityList').innerHTML = events.length ? events.map((event,index)=>`
    <button class="activity-row ${event.game_id ? 'game-event' : ''}" data-activity-index="${index}">
      <span class="activity-line"><time class="activity-time">${esc(activityTime(event.observed_at || event.created_at))}</time><span class="activity-kind ${activityCategory(event).toLowerCase()}">${esc(activityCategory(event))}</span></span>
      ${event.prior_context ? `<span class="activity-prior-owner">${esc(event.prior_context.selected_team || 'TEAM')} PRIOR GAME · ${esc(String(event.prior_context.status || 'WAITING').replaceAll('_',' '))}</span>` : ''}
      <span class="activity-game">${esc(activityMatchup(event) || activityTitle(event))}</span>
      ${activityDetail(event) ? `<span class="activity-detail"><span class="activity-detail-text">${esc(activityDetail(event))}</span><span class="activity-book-logos">${activityBookLogos(event)}</span></span>` : ''}
    </button>`).join('') : '<div class="activity-empty">No activity for this selection.</div>';
  document.querySelectorAll('[data-activity-index]').forEach((el)=>el.addEventListener('click',()=>focusActivityGame(events[Number(el.dataset.activityIndex)])));
}

async function fetchDataBundle(matrixUrl,healthUrl,activityUrl){
  const bust = Date.now();
  const [matrixResp, healthResp, activityResp] = await Promise.all([
    fetch(`${matrixUrl}?v=${bust}`, {cache:'no-store'}),
    fetch(`${healthUrl}?v=${bust}`, {cache:'no-store'}),
    fetch(`${activityUrl}?v=${bust}`, {cache:'no-store'})
  ]);
  if(!matrixResp.ok)throw new Error(`Matrix HTTP ${matrixResp.status}`);
  if(!healthResp.ok)throw new Error(`Health HTTP ${healthResp.status}`);
  if(!activityResp.ok)throw new Error(`Activity HTTP ${activityResp.status}`);
  return Promise.all([matrixResp.json(),healthResp.json(),activityResp.json()]);
}

async function loadData(){
  const priorActivityVersion=ACTIVITY_VERSION;
  try{
    [MATRIX,HEALTH,ACTIVITY]=await fetchDataBundle(LIVE_MATRIX_URL,LIVE_HEALTH_URL,LIVE_ACTIVITY_URL);
  }catch(liveError){
    console.warn('Live War Room data unavailable; using static snapshot',liveError);
    [MATRIX,HEALTH,ACTIVITY]=await fetchDataBundle(MATRIX_URL,HEALTH_URL,ACTIVITY_URL);
  }

  ACTIVITY_VERSION=[ACTIVITY?.built_at,ACTIVITY?.latest_refresh_id,ACTIVITY?.public_event_count].join('|');
  if(priorActivityVersion && priorActivityVersion!==ACTIVITY_VERSION){
    GAME_ACTIVITY_CACHE.clear();
    if(SELECTED_GAME_ID){
      const game=selectedGame();
      SELECTED_GAME_ACTIVITY=game ? await fetchGameActivity(game) : null;
    }
  }

  fillWeeks();
  reconcileSelectedGame();
  renderHealth();
  renderMatrix();
  renderActivity();
  syncWorkingViewport();
}

function syncWorkingViewport(){
  const grid=document.querySelector('.command-grid');
  if(!grid || window.innerWidth<=900){ if(grid) grid.style.height=''; return; }
  const footer=document.querySelector('.footer');
  const available=window.innerHeight-grid.getBoundingClientRect().top-(footer?.offsetHeight || 0)-5;
  grid.style.height=`${Math.max(280,available)}px`;
}

window.addEventListener('resize',()=>{
  syncWorkingViewport();
  placeActivityRail();
});

document.getElementById('scopeSelect').addEventListener(
  'change',
  e=>{
    ACTIVE_SCOPE = e.target.value;

    if(ACTIVE_WEEK !== 'ALL'){
      ACTIVE_WEEK = 'AUTO';
    }

    fillWeeks();
    reconcileSelectedGame();
    renderHealth();
    renderMatrix();
    renderActivity();
  }
);

document.getElementById('weekSelect').addEventListener(
  'change',
  e=>{
    ACTIVE_WEEK = e.target.value;
    reconcileSelectedGame();
    renderHealth();
    renderMatrix();
    renderActivity();
  }
);

document.getElementById('mobileScopeSelect').addEventListener('change',e=>{
  ACTIVE_SCOPE=e.target.value;
  if(ACTIVE_WEEK!=='ALL') ACTIVE_WEEK='AUTO';
  fillWeeks();
  reconcileSelectedGame();
  renderHealth();
  renderMatrix();
  renderActivity();
});

document.getElementById('mobileWeekSelect').addEventListener('change',e=>{
  ACTIVE_WEEK=e.target.value;
  document.getElementById('weekSelect').value=String(ACTIVE_WEEK);
  reconcileSelectedGame();
  renderHealth();
  renderMatrix();
  renderActivity();
});

document.getElementById('mobileSortSelect').addEventListener('change',e=>{
  SORT_KEY=e.target.value;
  SORT_DIR=(SORT_KEY==='date' || SORT_KEY==='home_team')?'asc':'desc';
  renderMatrix();
  syncMobileControls();
});

document.getElementById('mobileControlsToggle').addEventListener('click',e=>{
  const controls=document.querySelector('.wr-top-right');
  const open=controls?.classList.toggle('mobile-open') || false;
  e.currentTarget.setAttribute('aria-expanded',String(open));
});

document.querySelectorAll('.activity-filter').forEach(button=>button.addEventListener('click',()=>{
  ACTIVITY_FILTER=button.dataset.filter;
  document.querySelectorAll('.activity-filter').forEach(b=>b.classList.toggle('active',b===button));
  renderActivity();
}));


document.getElementById('refreshBtn').addEventListener(
  'click',
  async ()=>{
    const btn = document.getElementById('refreshBtn');
    const old = btn.textContent;

    btn.textContent = '↻ RELOADING…';

    try{
      await loadData();
      btn.textContent = '✓ MARKET RELOADED';
    }catch(err){
      console.error(err);
      btn.textContent = '⚠ RELOAD FAILED';
    }

    setTimeout(()=>{
      btn.textContent = old;
    },1500);
  }
);

const CONTROL_BASE_URL = __CONTROL_BASE_URL__;
const VERSION_POLL_MS = __VERSION_POLL_MS__;
const CONTROL_ORIGIN = CONTROL_BASE_URL ? new URL(CONTROL_BASE_URL).origin : '';
const CONTROL_CHANNEL = 'ncaaf-war-room-control-v1';
const CONTROL_ACTIONS = new Set(['market','ratings','postgame']);
const RELAY_REQUESTS = new Map();
let CONTROL_WINDOW = null;
const CONTROL_NONCE_KEY = 'ncaaf-war-room-control-nonce-v1';
let CONTROL_NONCE = sessionStorage.getItem(CONTROL_NONCE_KEY) || '';

function ensureControlNonce(){
  if(!CONTROL_NONCE){
    CONTROL_NONCE=crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    sessionStorage.setItem(CONTROL_NONCE_KEY,CONTROL_NONCE);
  }
  return CONTROL_NONCE;
}

function setOperatorControls(enabled){
  document.querySelectorAll('.operator-control').forEach(el=>el.disabled=!enabled);
}

function connectOperator(){
  const status=document.getElementById('operatorStatus');
  CONTROL_WINDOW=window.open(
    `${CONTROL_BASE_URL}/war-room/bootstrap?channel_nonce=${encodeURIComponent(ensureControlNonce())}`,
    'ncaaf-war-room-control',
    'popup=yes,width=520,height=260,resizable=yes,scrollbars=yes'
  );
  if(!CONTROL_WINDOW){status.textContent='Operator connection blocked · allow popups and retry';return}
  status.textContent='Waiting for operator authentication…';
}

function requestViaRelay(action, button, old){
  if(!CONTROL_ACTIONS.has(action) || !CONTROL_WINDOW || CONTROL_WINDOW.closed) throw new Error('Operator session is not connected');
  const requestId=crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;
  RELAY_REQUESTS.set(requestId,{button,old});
  CONTROL_WINDOW.postMessage({channel:CONTROL_CHANNEL,channelNonce:ensureControlNonce(),type:'REQUEST',requestId,action},CONTROL_ORIGIN);
}

addEventListener('message',event=>{
  if(event.origin!==CONTROL_ORIGIN)return;
  const message=event.data||{};
  if(message.channel!==CONTROL_CHANNEL || message.channelNonce!==ensureControlNonce())return;
  if(message.type==='READY' && !CONTROL_WINDOW) CONTROL_WINDOW=event.source;
  if(event.source!==CONTROL_WINDOW)return;
  const status=document.getElementById('operatorStatus');
  const connect=document.getElementById('connectOperatorBtn');
  if(message.type==='READY'){
    setOperatorControls(true);
    connect.hidden=true;
    if(RELAY_REQUESTS.size===0){
      status.textContent='Operator ready';
    }
    return;
  }
  const pending=RELAY_REQUESTS.get(message.requestId);
  if(!pending)return;
  if(message.type==='ACK'){
    pending.button.textContent='✓ REQUESTED';
    status.textContent=`Task ${message.payload.task_id} · ${message.payload.status || 'REQUESTED'}`;
  }else if(message.type==='TASK'){
    status.textContent=operationDetail(message.task||{});
    const terminal=new Set(['COMPLETED','COMPLETED_WITH_WARNINGS','FAILED','BLOCKED_BY_OVERLAP','DEFERRED_BY_DAILY_BACKBONE']);
    if(terminal.has(message.task?.status)){
      if(message.task.status==='COMPLETED' || message.task.status==='COMPLETED_WITH_WARNINGS')loadData();
      RELAY_REQUESTS.delete(message.requestId);
      setTimeout(()=>{pending.button.textContent=pending.old;pending.button.disabled=false},2500);
    }
  }else if(message.type==='ERROR'){
    pending.button.textContent='⚠ REQUEST FAILED';
    status.textContent=`Request failed · ${message.message}`;
    RELAY_REQUESTS.delete(message.requestId);
    setTimeout(()=>{pending.button.textContent=pending.old;pending.button.disabled=false},2500);
  }
});

function requestOperation(action, button, runningLabel){
  const old = button.textContent;
  button.disabled = true;
  button.textContent = runningLabel;
  const status = document.getElementById('operatorStatus');
  status.textContent = 'Submitting authenticated request…';
  try{requestViaRelay(action,button,old)}catch(err){
    button.textContent='⚠ REQUEST FAILED';
    status.textContent = `Request failed · ${err.message}`;
    setTimeout(()=>{button.textContent=old;button.disabled=false},2500);
  }
}

function operationDetail(task){
  const parts=[`Task ${task.task_id}`,task.status];
  if(task.credits_consumed != null) parts.push(`${task.credits_consumed} credits`);
  if(task.provider_result) parts.push(String(task.provider_result));
  if(task.publication_result) parts.push(String(task.publication_result));
  if(task.error) parts.push(String(task.error));
  return parts.filter(Boolean).join(' · ');
}

function detectOperator(){
  const status=document.getElementById('operatorStatus');
  const connect=document.getElementById('connectOperatorBtn');
  if(!CONTROL_BASE_URL){status.textContent='Operator authentication unavailable';return}
  setOperatorControls(false);
  connect.hidden=false;
  connect.disabled=false;
  ensureControlNonce();
  status.textContent='Reconnecting operator session…';
  setTimeout(()=>{
    if(!CONTROL_WINDOW){status.textContent='Connect authenticated operator session';connect.hidden=false}
  },2000);
}

document.getElementById('connectOperatorBtn').addEventListener('click',connectOperator);

document.getElementById('acquireBtn').addEventListener(
  'click',
  async ()=>{
    const btn = document.getElementById('acquireBtn');
    if(!window.confirm('Acquire a fresh spreads + totals market snapshot? Expected cost: 2 Odds API credits.')) return;
    requestOperation('market', btn, '⚡ REQUESTING MARKET…');
  }
);

document.getElementById('ratingsBtn').addEventListener('click', e=>requestOperation('ratings',e.currentTarget,'↻ REQUESTING RATINGS…'));
document.getElementById('postgameBtn').addEventListener('click', e=>requestOperation('postgame',e.currentTarget,'↻ REQUESTING POSTGAME…'));

let LAST_BUILD_ID = null;
async function pollPublishedVersion(){
  try{
    const response = await fetch(`${LIVE_VERSION_URL}?version=${Date.now()}`,{cache:'no-store'});
    if(!response.ok) return;
    const live = await response.json();
    const version = [live.refresh_id,live.activity_built_at,live.activity_event_count,live.scoreboard_pulled_at,live.schedule_built_at].join('|');
    if(LAST_BUILD_ID === null){LAST_BUILD_ID=version;return}
    if(version && version !== LAST_BUILD_ID){LAST_BUILD_ID=version;await loadData()}
  }catch(_err){ /* preserve the last valid rendered state */ }
}
setInterval(pollPublishedVersion, VERSION_POLL_MS);
setInterval(updateMatrixRecencyMarkers, 30000);
detectOperator();

loadData().catch(err=>{
  console.error(err);

  document.getElementById('matrixBody').innerHTML = `
    <tr>
      <td colspan="11" class="red">
        Could not load War Room data: ${esc(err.message)}
      </td>
    </tr>
  `;
  const mobile=document.getElementById('mobileMatrix');
  if(mobile) mobile.innerHTML=`<div class="red">Could not load War Room data: ${esc(err.message)}</div>`;
});
</script>

</body>
</html>
'''

HTML = HTML.replace("__CONTROL_BASE_URL__", json.dumps(CONTROL_BASE_URL))
HTML = HTML.replace("__VERSION_POLL_MS__", str(POLL_SECONDS * 1000))
HTML = HTML.replace("__TEAM_ABBREVIATIONS__", json.dumps(TEAM_ABBREVIATIONS, sort_keys=True))
OUT.write_text(HTML)
print("wrote:", OUT)
