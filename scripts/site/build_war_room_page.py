#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "war-room.html"
CONTROL_CONFIG = ROOT / "config/war_room_control_plane.json"
control_config = json.loads(CONTROL_CONFIG.read_text()) if CONTROL_CONFIG.exists() else {}
CONTROL_BASE_URL = control_config.get("control_base_url")
POLL_SECONDS = max(30, int(control_config.get("browser_version_poll_seconds", 60)))

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
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:16px;
  min-height:42px;
  padding:7px 12px;
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
  gap:14px;
  flex-wrap:wrap;
}

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
  padding:7px 10px;
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
  flex-basis:100%;
  color:var(--muted);
  font-size:11px;
  text-align:right;
  min-height:14px;
}

.summary-grid{
  display:grid;
  grid-template-columns:1.1fr 1.25fr 1.25fr .65fr 1fr 1fr;
  gap:4px;
  padding:4px;
}

.summary-box{
  min-height:47px;
  border:1px solid var(--line);
  background:var(--panel);
  padding:6px 8px;
}

.summary-label{
  color:var(--muted);
  font-size:11px;
  text-transform:uppercase;
}

.summary-value{
  margin-top:4px;
  font-weight:900;
  font-size:15px;
}

.green{color:var(--green)}
.yellow{color:var(--yellow)}
.red{color:var(--red)}
.cyan{color:var(--cyan)}
.muted{color:var(--muted)}

.health-strip{
  display:flex;
  align-items:center;
  gap:13px;
  flex-wrap:wrap;
  padding:8px 10px;
  margin:0 4px 4px;
  border:1px solid var(--line);
  background:var(--panel);
}

.health-title{
  color:var(--muted);
  font-size:11px;
  font-weight:900;
  letter-spacing:.7px;
  margin-right:6px;
}

.health-book{
  white-space:nowrap;
  font-weight:800;
}

.health-detail{
  color:var(--muted);
  font-weight:500;
  font-size:11px;
}

.ratings-health-strip{
  margin-top:0;
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
  margin:4px;
}

.main-panel{
  margin:0;
  border:1px solid var(--line);
  background:var(--panel);
  min-width:0;
}

.right-rail{
  border:1px solid var(--line);
  background:var(--panel);
  min-width:0;
}

.rail-section{
  border-bottom:1px solid var(--line);
}

.rail-title{
  padding:8px 10px;
  font-weight:900;
  letter-spacing:1px;
  border-bottom:1px solid var(--line);
}

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

.matrix-scroll{
  max-height:690px;
  overflow:auto;
}

.panel-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  height:36px;
  padding:0 10px;
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
  overflow:auto;
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
  padding:6px 7px;
  white-space:nowrap;
}

td{
  border-bottom:1px solid #223444;
  padding:5px 7px;
  vertical-align:middle;
  white-space:nowrap;
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

.quote.best{
  color:var(--green);
}

.quote.none{
  color:#526476;
  font-weight:500;
}

.book-col{
  min-width:95px;
}

.best-col{
  min-width:115px;
}

.model-col{
  min-width:90px;
  font-size:14px;
  font-weight:900;
}


.matchup-col{width:16%}
.model-col{width:5.2%}

.shadow-col{
  width:5.2%;
  text-align:center;
}

.shadow-ready{
  color:var(--purple);
  font-weight:900;
}

.shadow-wait{
  color:var(--yellow);
  font-size:9px;
  font-weight:900;
}
.best-col{width:9%}
.exchange-col{width:9%}
.pinn-col{width:6%}
.edge-col{width:5%}
.injury-col{width:3.5%;text-align:center}
.signal-col{width:6%}
.state-col{width:5%}

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
  color:var(--green);
  font-weight:900;
  line-height:1.15;
  white-space:normal;
}

.market-book{
  display:block;
  font-size:9px;
  color:var(--green);
  letter-spacing:.3px;
}

.market-price{
  display:block;
  margin-top:2px;
  font-size:11px;
  white-space:nowrap;
}

.pinn-quote{
  display:block;
  font-size:10px;
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

.signal-chip img{
  width:16px;
  height:16px;
  object-fit:contain;
}

.signal-count{
  color:var(--green);
}

.edge{
  font-size:14px;
  font-weight:900;
}

.edge.action{color:var(--green)}
.edge.lean{color:var(--yellow)}
.edge.watch{color:#c6d1db}

.badge{
  display:inline-block;
  border:1px solid var(--line2);
  padding:3px 7px;
  border-radius:3px;
  font-weight:900;
  font-size:10px;
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
  padding:7px 10px;
  color:var(--muted);
  border-top:1px solid var(--line);
  background:#060c12;
  font-size:11px;
}

@media(max-width:900px){
  .summary-grid{
    grid-template-columns:repeat(2,1fr);
  }

  .command-grid{
    grid-template-columns:1fr;
  }

  .right-rail{
    display:none;
  }

  .wr-top{
    align-items:flex-start;
    flex-direction:column;
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
    <span class="health-title">FAST MARKET HEALTH</span>
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
    </section>

    <aside class="right-rail">

      <div class="rail-section">
        <div class="rail-title">LIVE MARKET</div>

        <div class="rail-row">
          <div class="rail-key">REFRESH</div>
          <div class="rail-value" id="railRefresh">—</div>
        </div>

        <div class="rail-row">
          <div class="rail-key">ALL FAST</div>
          <div class="rail-value" id="railAllFast">—</div>
        </div>

        <div class="rail-row">
          <div class="rail-key">FBS UNIVERSE</div>
          <div class="rail-value" id="railFbsUniverse">—</div>
        </div>

        <div class="rail-row">
          <div class="rail-key">DISPLAYED</div>
          <div class="rail-value" id="railDisplayed">—</div>
        </div>

        <div class="rail-row">
          <div class="rail-key">DISPLAY STATE</div>
          <div class="rail-value" id="railDisplayState">—</div>
        </div>
      </div>

      <div class="rail-section">
        <div class="rail-title">BETTABLE BOOKS</div>
        <div id="railBettable"></div>
      </div>

      <div class="rail-section">
        <div class="rail-title">SHARP / EXCHANGE</div>
        <div id="railReference"></div>
      </div>

      <div class="rail-section">
        <div class="rail-title">API / QUOTA</div>

        <div class="rail-row">
          <div class="rail-key">STATUS</div>
          <div class="rail-value" id="railQuotaStatus">—</div>
        </div>

        <div class="rail-row">
          <div class="rail-key">LEFT</div>
          <div class="rail-value" id="railQuotaLeft">—</div>
        </div>

        <div class="rail-row">
          <div class="rail-key">PULLS</div>
          <div class="rail-value" id="railQuotaPulls">—</div>
        </div>

        <div class="rail-row">
          <div class="rail-key">RESET</div>
          <div class="rail-value" id="railQuotaReset">—</div>
        </div>
      </div>

      <div class="rail-section">
        <div class="rail-title">MOVEMENT STUDY</div>

        <div class="rail-row">
          <div class="rail-key">MODE</div>
          <div class="rail-value green">PASSIVE RECORDING</div>
        </div>

        <div class="rail-row">
          <div class="rail-key">COST</div>
          <div class="rail-value">0 extra credits</div>
        </div>
      </div>

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
const LIVE_VERSION_URL = 'https://control.barnseywr.com/war-room/live/version';
const LIVE_MATRIX_URL = 'https://control.barnseywr.com/war-room/live/market-matrix';
const LIVE_HEALTH_URL = 'https://control.barnseywr.com/war-room/live/health';

let MATRIX = null;
let HEALTH = null;
let ACTIVE_MARKET = 'spread';
let ACTIVE_WEEK = 'AUTO';
let ACTIVE_SCOPE = 'FBS';
let SORT_KEY = 'best_edge';
let SORT_DIR = 'desc';

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

function ratingStatusDetail(h){
  if(!h) return '';

  const pieces = [];

  if(h.teams){
    pieces.push(`${h.teams}t`);
  }

  if(h.games_available !== null &&
     h.games_available !== undefined){
    pieces.push(`${h.games_available}g`);
  }

  const snapshot =
    h.snapshot_date ||
    h.latest_snapshot_date;

  if(snapshot){
    pieces.push(fmtStatusDate(snapshot));
  }

  const pull =
    h.latest_pull_at ||
    h.latest_pulled_at;

  if(pull){
    pieces.push(fmtStatusTimeET(pull));
  }

  return pieces.join(' · ');
}

function healthDot(color){
  return `<span class="dot ${esc(color || 'RED')}"></span>`;
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

    if(av !== bv){
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

    SORT_DIR =
      key === 'date'
        ? 'asc'
        : 'desc';
  }

  renderMatrix();
}

function renderHealth(){
  const books = HEALTH?.books || {};
  const strip = document.getElementById('healthStrip');

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
    `<span class="health-title">FAST MARKET HEALTH</span>` +
    ordered.map(book=>{
      const h = books[book] || {};
      const games = h.games_with_any_quote ?? 0;
      const age = h.quote_age_median_seconds;

      return `
        <span class="health-book">
          ${healthDot(h.color)}
          ${esc(BOOK_ABBR[book] || book)}
          <span class="health-detail">
            ${games}g${age != null ? ` · ${Math.round(age)}s` : ''}
          </span>
        </span>
      `;
    }).join('');

  const ratings =
    HEALTH?.ratings_health?.sources || {};

  const ratingOrder = [
    ['SP+', 'SP+'],
    ['FPI', 'FPI'],
    ['TR', 'TR'],
    ['SAG', 'SAG'],
    ['DR', 'DR'],
    ['MAS', 'MAS']
  ];

  const ratingsStrip =
    document.getElementById('ratingsHealthStrip');

  if(ratingsStrip){
    const ratingHtml = ratingOrder.map(([key,label])=>{
      const h = ratings[key] || {};

      const detail =
        ratingStatusDetail(h);

      return `
        <span class="health-book">
          ${healthDot(h.color)}
          ${esc(label)}
          <span class="health-status ${esc(h.color || '')}">
            ${esc(h.status || 'UNKNOWN')}
          </span>
          ${
            detail
              ? `<span class="health-detail"> · ${esc(detail)}</span>`
              : ''
          }
        </span>
      `;
    }).join('');

    const weekProjectionHealth =
      ACTIVE_WEEK === 'ALL'
        ? null
        : HEALTH?.projection_health?.by_week?.[String(ACTIVE_WEEK)] || null;

    const projectionItems = [
      ['SPREAD', weekProjectionHealth?.spread],
      ['TOTAL', weekProjectionHealth?.total],
      ['SHADOW', weekProjectionHealth?.shadow]
    ];

    const projectionHtml = projectionItems.map(([label,h])=>{
      const state = h || {
        color:'GRAY',
        status: ACTIVE_WEEK === 'ALL' ? 'SELECT WEEK' : 'UNAVAILABLE',
        displayed_games:0
      };

      return `
        <span class="health-book">
          ${healthDot(state.color)}
          ${esc(label)}
          <span class="health-status ${esc(state.color || '')}">
            ${esc(state.status || 'UNAVAILABLE')}
          </span>
          <span class="health-detail">
            · ${esc(state.displayed_games ?? 0)}g
          </span>
        </span>
      `;
    }).join('');

    ratingsStrip.innerHTML =
      `<span class="health-title">RATINGS / MODEL HEALTH</span>` +
      ratingHtml +
      projectionHtml;
  }

  const q = HEALTH?.api_quota || {};

  document.getElementById('topHealth').innerHTML = `
    <span>
      ${healthDot(q.color)}
      API ${esc(q.status || 'UNKNOWN')}
    </span>
    <span>
      STATE ${esc(
        HEALTH?.fast_market_refresh?.refresh_id || '—'
      )}
    </span>
  `;

  document.getElementById('summaryQuota').innerHTML =
    `<span class="${String(q.color || '').toLowerCase()}">` +
    `${esc(q.credits_remaining ?? '—')} left</span>`;

  const green = ordered.filter(
    b => books[b]?.color === 'GREEN'
  ).length;

  document.getElementById('summaryBooks').innerHTML =
    `<span class="green">${green}</span> / ${ordered.length} GREEN`;


  const refresh =
    HEALTH?.fast_market_refresh || {};

  const stateCounts =
    MATRIX?.summary?.state_counts || {};

  document.getElementById('railRefresh').textContent =
    fmtDateTimeET(refresh.last_fast_pull_at);

  document.getElementById('railAllFast').textContent =
    `${refresh.upcoming_games_in_pull ?? '—'} games`;

  document.getElementById('railFbsUniverse').textContent =
    `${MATRIX?.summary?.fbs_vs_fbs_games ?? '—'} games`;

  const bookRailRow = book => {
    const h = books[book] || {};

    return `
      <div class="rail-row">
        <div class="rail-key">
          ${healthDot(h.color)}
          ${esc(BOOK_ABBR[book] || book)}
        </div>

        <div class="rail-value">
          ${esc(h.games_with_any_quote ?? 0)} games
          <span class="muted">
            · S ${esc(h.spread_completeness_pct ?? '—')}%
            · T ${esc(h.total_completeness_pct ?? '—')}%
          </span>
        </div>
      </div>
    `;
  };

  document.getElementById('railBettable').innerHTML =
    [
      'DraftKings',
      'FanDuel',
      'BetMGM',
      'Caesars'
    ].map(bookRailRow).join('');

  document.getElementById('railReference').innerHTML =
    [
      'Pinnacle',
      'Novig',
      'ProphetX',
      'Kalshi'
    ].map(bookRailRow).join('');

  document.getElementById('railQuotaStatus').innerHTML =
    `${healthDot(q.color)} ${esc(q.status || '—')}`;

  document.getElementById('railQuotaLeft').textContent =
    `${q.credits_remaining ?? '—'} credits`;

  document.getElementById('railQuotaPulls').textContent =
    `${q.estimated_fast_pulls_remaining ?? '—'} est.`;

  document.getElementById('railQuotaReset').textContent =
    `${q.days_until_reset ?? '—'} days`;
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
    `<span class="green">${rows.length}</span> fast games`;

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

  document.getElementById('railDisplayed').textContent =
    `${rows.length} games`;

  document.getElementById('railDisplayState').innerHTML =
    `<span class="cyan">HYB ${counts.HYBRID || 0}</span> · ` +
    `<span class="red">ST ${counts.STALE || 0}</span>`;
}

function renderHead(){
  document.getElementById('matrixHead').innerHTML = `
    <tr>
      <th
        class="matchup-col sortable"
        onclick="setSort('date')"
      >
        DATE / MATCHUP ${sortArrow('date')}
      </th>

      <th class="model-col"><span class="spread-label">SPREAD</span><br>MODEL</th>
      <th class="shadow-col"><span class="spread-label">SPREAD</span><br>SHADOW</th>

      <th class="best-col"><span class="spread-label">SPREAD</span><br>BEST</th>
      <th class="exchange-col"><span class="spread-label">SPREAD</span><br>EXCH</th>
      <th class="pinn-col"><span class="spread-label">SPREAD</span><br>PINN</th>

      <th
        class="edge-col sortable"
        onclick="setSort('spread_edge')"
      >
        <span class="spread-label">SPREAD</span><br>EDGE ${sortArrow('spread_edge')}
      </th>

      <th class="model-col">TOT<br>MODEL</th>
      <th class="shadow-col">TOT<br>SHADOW</th>

      <th class="best-col">TOT<br>BEST</th>
      <th class="exchange-col">TOT<br>EXCH</th>
      <th class="pinn-col">TOT<br>PINN</th>

      <th
        class="edge-col sortable"
        onclick="setSort('total_edge')"
      >
        TOT<br>EDGE ${sortArrow('total_edge')}
      </th>

      <th class="injury-col">INJ</th>
      <th class="signal-col">SIGNALS</th>
      <th class="state-col">STATE</th>
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

  if(market === 'spread'){
    const rounded = Math.round(n * 10) / 10;

    if(rounded === 0){
      return 'PK';
    }

    return rounded > 0
      ? `+${rounded}`
      : `${rounded}`;
  }

  return n.toFixed(1);
}

function edgeDisplay(value){
  const n = Number(value);

  if(!Number.isFinite(n) || n <= 0){
    return '—';
  }

  return `▲${n.toFixed(1)}`;
}


function teamLogoSlug(team){
  if(!team) return '';

  return String(team)
    .toLowerCase()
    .replace(/&/g, 'a')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
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
      <img
        class="signal-logo"
        src="logos/${esc(slug)}.png"
        alt="${esc(team)}"
        onerror="this.style.display='none'"
      >
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



function shadowDisplay(model, market){
  if(!model){
    return `<span class="shadow-wait">WAIT</span>`;
  }

  if(model.selection_status !== 'AVAILABLE'){
    return `<span class="shadow-wait">WAIT</span>`;
  }

  const value =
    market === 'spread'
      ? model.value_home_line
      : model.value_total;

  if(
    value === null ||
    value === undefined
  ){
    return `<span class="shadow-wait">WAIT</span>`;
  }

  return `
    <span class="shadow-ready">
      ${modelDisplay(value, market)}
    </span>
  `;
}

function compactQuote(q, market){
  if(!q) return '—';

  const book =
    BOOK_ABBR[q.book] || q.book || '';

  const quote =
    market === 'spread'
      ? quoteText(q)
      : totalQuoteText(q);

  return `
    <span class="market-best">
      <span class="market-book">${esc(book)}</span>
      <span class="market-price">${quote}</span>
    </span>
  `;
}

function compactPinn(q, market){
  if(!q) return '—';

  const quote =
    market === 'spread'
      ? quoteText(q)
      : totalQuoteText(q);

  return `
    <span class="pinn-quote">
      ${quote}
    </span>
  `;
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

    const sprPinn =
      sprSide
        ? game.market?.pinnacle?.spread?.[sprSide]
        : null;

    const totPinn =
      totSide
        ? game.market?.pinnacle?.total?.[totSide]
        : null;

    const sprModel =
      game.models?.standard_spread?.value_home_line;

    const sprShadow =
      game.models?.shadow_spread;

    const totModel =
      game.models?.standard_total?.value_total;

    const totShadow =
      game.models?.shadow_total;

    return `
      <tr class="game-start">

        <td class="matchup-col">
          <div>
            <span class="game-date">
              ${esc(fmtKickoffDateET(game.kickoff_time))}
            </span>

            <span class="game-time">
              ${esc(fmtKickoffTimeET(game.kickoff_time))}
            </span>
          </div>

          <div class="game-name">
            ${esc(game.away_team)}
            <span class="muted">@</span>
            ${esc(game.home_team)}
          </div>

          <div class="game-meta">
            W${esc(game.week)}
            ${game.neutral_site ? ' · NEUTRAL' : ''}
          </div>
        </td>

        <td class="model-col">
          ${modelDisplay(sprModel, 'spread')}
        </td>

        <td class="shadow-col">
          ${shadowDisplay(sprShadow, 'spread')}
        </td>

        <td class="best-col">
          ${compactQuote(sprBest, 'spread')}
        </td>

        <td class="exchange-col">
          ${compactQuote(sprEx, 'spread')}
        </td>

        <td class="pinn-col">
          ${compactPinn(sprPinn, 'spread')}
        </td>

        <td class="edge-col">
          <span class="edge ${edgeClass(sprEdge)}">
            ${edgeDisplay(sprEdge)}
          </span>
        </td>

        <td class="model-col">
          ${modelDisplay(totModel, 'total')}
        </td>

        <td class="shadow-col">
          ${shadowDisplay(totShadow, 'total')}
        </td>

        <td class="best-col">
          ${compactQuote(totBest, 'total')}
        </td>

        <td class="exchange-col">
          ${compactQuote(totEx, 'total')}
        </td>

        <td class="pinn-col">
          ${compactPinn(totPinn, 'total')}
        </td>

        <td class="edge-col">
          <span class="edge ${edgeClass(totEdge)}">
            ${edgeDisplay(totEdge)}
          </span>
        </td>

        <td class="injury-col">
          <span class="injury-placeholder">—</span>
        </td>

        <td class="signal-col">
          ${signalCell(game)}
        </td>

        <td class="state-col">
          <span class="badge ${esc(game.state)}">
            ${esc(game.state)}
          </span>
        </td>

      </tr>
    `;
  }).join('');

  renderSummary();
}

async function fetchDataPair(matrixUrl,healthUrl){
  const bust = Date.now();
  const [matrixResp, healthResp] = await Promise.all([
    fetch(`${matrixUrl}?v=${bust}`, {cache:'no-store'}),
    fetch(`${healthUrl}?v=${bust}`, {cache:'no-store'})
  ]);
  if(!matrixResp.ok)throw new Error(`Matrix HTTP ${matrixResp.status}`);
  if(!healthResp.ok)throw new Error(`Health HTTP ${healthResp.status}`);
  return Promise.all([matrixResp.json(),healthResp.json()]);
}

async function loadData(){
  try{
    [MATRIX,HEALTH]=await fetchDataPair(LIVE_MATRIX_URL,LIVE_HEALTH_URL);
  }catch(liveError){
    console.warn('Live War Room data unavailable; using static snapshot',liveError);
    [MATRIX,HEALTH]=await fetchDataPair(MATRIX_URL,HEALTH_URL);
  }

  fillWeeks();
  renderHealth();
  renderMatrix();
}

document.getElementById('scopeSelect').addEventListener(
  'change',
  e=>{
    ACTIVE_SCOPE = e.target.value;

    if(ACTIVE_WEEK !== 'ALL'){
      ACTIVE_WEEK = 'AUTO';
    }

    fillWeeks();
    renderHealth();
    renderMatrix();
  }
);

document.getElementById('weekSelect').addEventListener(
  'change',
  e=>{
    ACTIVE_WEEK = e.target.value;
    renderHealth();
    renderMatrix();
  }
);


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

function setOperatorControls(enabled){
  document.querySelectorAll('.operator-control').forEach(el=>el.disabled=!enabled);
}

function connectOperator(){
  const status=document.getElementById('operatorStatus');
  CONTROL_WINDOW=window.open(
    `${CONTROL_BASE_URL}/war-room/bootstrap`,
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
  CONTROL_WINDOW.postMessage({channel:CONTROL_CHANNEL,type:'REQUEST',requestId,action},CONTROL_ORIGIN);
}

addEventListener('message',event=>{
  if(event.origin!==CONTROL_ORIGIN || event.source!==CONTROL_WINDOW)return;
  const message=event.data||{};
  if(message.channel!==CONTROL_CHANNEL)return;
  const status=document.getElementById('operatorStatus');
  const connect=document.getElementById('connectOperatorBtn');
  if(message.type==='READY'){
    setOperatorControls(true);
    connect.hidden=true;
    status.textContent='Operator ready';
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
  status.textContent='Connect authenticated operator session';
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
    const version = live.refresh_id;
    if(LAST_BUILD_ID === null){LAST_BUILD_ID=version;return}
    if(version && version !== LAST_BUILD_ID){LAST_BUILD_ID=version;await loadData()}
  }catch(_err){ /* preserve the last valid rendered state */ }
}
setInterval(pollPublishedVersion, VERSION_POLL_MS);
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
});
</script>

</body>
</html>
'''

HTML = HTML.replace("__CONTROL_BASE_URL__", json.dumps(CONTROL_BASE_URL))
HTML = HTML.replace("__VERSION_POLL_MS__", str(POLL_SECONDS * 1000))
OUT.write_text(HTML)
print("wrote:", OUT)
