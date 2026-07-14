from pathlib import Path
import re,json,csv

# Place at scripts/site/build_matchup_page.py and run after index.html has been promoted and injury overlay injected.
# It extracts the current embedded DB + injury overlay from index.html, writes matchup.html,
# and patches season schedule Matchup buttons to link to matchup.html?game_id=... .
src=Path('index.html')
s=src.read_text(errors='ignore')
db=json.loads(re.search(r'<script id="db" type="application/json">(.*?)</script>',s,re.S).group(1))
inj=[]
m=re.search(r'<script id="game-injury-overlay-data" type="application/json">(.*?)</script>',s,re.S)
if m:
    inj=json.loads(m.group(1))

HISTORY_PATH = Path("data/history/game_line_model_history.csv")
history_rows = []
if HISTORY_PATH.exists() and HISTORY_PATH.stat().st_size > 0:
    with HISTORY_PATH.open(newline="", encoding="utf-8") as f:
        history_rows = list(csv.DictReader(f))

WEATHER_PATH = Path("data/weather/game_weather_latest.csv")
weather_rows = []
if WEATHER_PATH.exists() and WEATHER_PATH.stat().st_size > 0:
    with WEATHER_PATH.open(newline="", encoding="utf-8") as f:
        weather_rows = list(csv.DictReader(f))

def safe_json(obj):
    return json.dumps(obj,separators=(',',':')).replace('</','<\\/')


def extract_js_object_const(name):
    m = re.search(r'const\s+' + re.escape(name) + r'\s*=\s*(\{.*?\});', s, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except Exception:
        return {}

rating_trends = extract_js_object_const('RATING_TRENDS')
returning_prod = extract_js_object_const('RETURNING_PRODUCTION_2026')

html=f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>2026 NCAAF Matchup Card</title>
<style>
:root{{--bg:#071120;--panel:#101d34;--panel2:#0b1628;--panel3:#122544;--line:rgba(148,163,184,.22);--muted:#9ca3af;--text:#e5e7eb;--good:#22c55e;--warn:#eab308;--bad:#ef4444;--blue:#60a5fa;--cyan:#67e8f9;}}
*{{box-sizing:border-box}}
body{{margin:0;background:radial-gradient(circle at top,#13234a 0,#071120 40%,#050b15 100%);color:var(--text);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}}
.team-with-logo{{display:inline-flex;align-items:center;gap:8px;vertical-align:middle;min-width:0}}
.team-logo-wrap{{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;flex:0 0 auto;vertical-align:middle}}
.team-logo-wrap.needs-badge{{border-radius:8px;background:rgba(255,255,255,.92);border:1px solid rgba(255,255,255,.22);box-shadow:0 2px 8px rgba(0,0,0,.18)}}
.team-logo{{width:26px;height:26px;object-fit:contain;display:block;filter:drop-shadow(0 1px 1px rgba(0,0,0,.45))}}
.team-logo-wrap.needs-badge .team-logo{{width:22px;height:22px;filter:none}}
.team-record-line{{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-top:2px}}
.record-pill{{display:inline-flex;align-items:center;border-radius:999px;padding:3px 7px;border:1px solid rgba(148,163,184,.20);background:rgba(148,163,184,.10);font-size:10px;font-weight:900;color:#dbeafe;white-space:nowrap}}
.team-mini-panels{{display:grid;grid-template-columns:1fr;gap:9px;margin-top:6px}}
.mini-panel{{border:1px solid rgba(148,163,184,.15);background:rgba(2,6,23,.24);border-radius:12px;padding:10px}}
.mini-head{{display:flex;align-items:center;justify-content:space-between;gap:8px;text-transform:uppercase;letter-spacing:.11em;color:#aab4c6;font-size:10px;font-weight:1000;margin-bottom:5px}}
.mini-head.returning-head{{justify-content:flex-start;gap:10px}}
.mini-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}
.coach-mini-grid{{grid-template-columns:repeat(2,1fr)}}
.returning-prod-grid{{grid-template-columns:repeat(2,1fr)}}
.coach-rows{{display:grid;gap:7px}}
.coach-row-mini{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.mini-stat{{border-radius:10px;background:rgba(148,163,184,.07);padding:7px 8px;min-width:0}}
.mini-label{{font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8;font-weight:900;white-space:nowrap}}
.mini-value{{font-size:13px;font-weight:1000;margin-top:3px;white-space:nowrap}}
.mini-panel .rank-chip{{font-size:10px;min-width:28px;padding:3px 5px;border-radius:7px}}
.mini-value.pos{{color:#4ade80}}
.mini-value.neg{{color:#fb7185}}
.mini-value.neu{{color:#dbeafe}}
@media(min-width:1050px){{.team-mini-panels{{grid-template-columns:1fr}} .mini-panel.coach-mini{{grid-column:auto}}}}
.center-records{{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;margin-top:-2px}}
.team-title-logo .team-logo-wrap{{width:44px;height:44px}}
.team-title-logo .team-logo{{width:40px;height:40px}}
.team-title-logo.team-with-logo{{justify-content:center;gap:12px}}
.team-name .rank-chip{{font-size:16px;min-width:38px;padding:5px 8px;border-radius:9px}}
.bigline .rank-chip{{font-size:19px;min-width:42px;padding:5px 9px;border-radius:10px}}
.sportsbook-logo-wrap{{display:inline-flex;align-items:center;justify-content:center;width:38px;height:30px;border-radius:8px;background:rgba(255,255,255,.96);border:1px solid rgba(255,255,255,.24);vertical-align:middle;margin:0 4px 0 0}}
.sportsbook-logo{{max-width:31px;max-height:25px;object-fit:contain;display:block}}
.book-strip{{display:flex;gap:6px;flex-wrap:wrap;align-items:center}}
.market-compact{{display:grid;grid-template-columns:1.2fr 1fr;gap:10px}}
.market-primary{{border:1px solid rgba(148,163,184,.15);background:rgba(2,6,23,.30);border-radius:14px;padding:11px}}
.market-primary b{{display:block;font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:#aab4c6;margin-bottom:5px}}
.market-primary-grid{{display:grid;grid-template-columns:1fr minmax(220px,.75fr);gap:12px;align-items:start}}
.model-box{{border:1px solid rgba(148,163,184,.14);border-radius:12px;background:rgba(15,23,42,.58);padding:9px}}
.model-box b{{font-size:11px;margin-bottom:4px}}
.open-line{{font-size:16px;font-weight:1000;color:#dbeafe;margin-top:6px}}
.edge-diff{{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;padding:6px 10px;font-weight:1000;margin-top:5px;border:1px solid rgba(148,163,184,.24)}}
.edge-diff.green{{background:rgba(34,197,94,.18);border-color:rgba(34,197,94,.42);color:#bbf7d0}}
.edge-diff.yellow{{background:rgba(234,179,8,.17);border-color:rgba(234,179,8,.42);color:#fef3c7}}
.edge-diff.red{{background:rgba(239,68,68,.15);border-color:rgba(239,68,68,.38);color:#fecaca}}
.line-history{{margin-top:8px;border:1px solid rgba(148,163,184,.12);border-radius:12px;background:rgba(2,6,23,.24);padding:10px 10px 8px}}
.line-history-labels{{display:flex;justify-content:space-between;font-size:11px;color:#aab4c6;font-weight:900;margin-top:2px}}
.line-history svg{{width:100%;height:112px;display:block;overflow:visible}}
.line-history .axis{{stroke:rgba(148,163,184,.20);stroke-width:1}}
.line-history .gridline{{stroke:rgba(148,163,184,.12);stroke-width:1}}
.line-history .y-label{{font-size:10px;fill:#aab4c6;font-weight:900}}
.line-history .line{{stroke:#60a5fa;stroke-width:3;fill:none;stroke-linecap:round}}
.line-history .model-line{{stroke:#22c55e;stroke-width:2;stroke-dasharray:4 4}}
.line-history .dot{{fill:#dbeafe;stroke:#0f172a;stroke-width:2}}
.line-history .model-dot{{fill:#22c55e;stroke:#0f172a;stroke-width:2}}
@media(max-width:900px){{.market-primary-grid{{grid-template-columns:1fr}}}}
.market-big{{font-size:22px;font-weight:1000;display:flex;align-items:center;gap:8px;flex-wrap:wrap}}
.market-sub{{font-size:12px;color:#aab4c6;margin-top:4px}}
.market-best-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:10px}}
.market-best{{border:1px solid rgba(148,163,184,.14);border-radius:12px;background:rgba(2,6,23,.26);padding:9px}}
.market-best b{{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#aab4c6;margin-bottom:5px}}
@media(max-width:900px){{.market-compact,.market-best-grid{{grid-template-columns:1fr}}}}
a{{color:inherit}}
.page{{max-width:1420px;margin:0 auto;padding:18px 18px 48px}}
.topbar{{display:flex;gap:12px;align-items:center;justify-content:space-between;margin-bottom:14px}}
.back{{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:999px;padding:8px 12px;background:rgba(15,23,42,.65);text-decoration:none;font-weight:800;color:#dbeafe}}
.small{{font-size:12px;color:var(--muted)}}
.muted{{color:var(--muted)}}
.hero{{display:grid;grid-template-columns:minmax(240px,1fr) minmax(340px,1.45fr) minmax(240px,1fr);gap:12px;align-items:stretch;margin-bottom:14px}}
.team-hero,.game-hero,.card{{background:rgba(15,23,42,.78);border:1px solid var(--line);border-radius:18px;box-shadow:0 16px 40px rgba(0,0,0,.24)}}
.team-hero{{padding:16px;display:flex;flex-direction:column;gap:10px}}
.team-name{{font-size:28px;font-weight:950;letter-spacing:-.03em;line-height:1}}
.team-meta{{display:flex;gap:8px;flex-wrap:wrap;align-items:center}}
.pill{{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:5px 9px;border:1px solid rgba(148,163,184,.24);background:rgba(148,163,184,.10);font-size:12px;font-weight:900;white-space:nowrap}}
.pill.good{{background:rgba(34,197,94,.14);border-color:rgba(34,197,94,.34);color:#bbf7d0}}
.pill.warn{{background:rgba(234,179,8,.13);border-color:rgba(234,179,8,.34);color:#fef3c7}}
.pill.bad{{background:rgba(239,68,68,.13);border-color:rgba(239,68,68,.34);color:#fecaca}}
.pill.blue{{background:rgba(96,165,250,.14);border-color:rgba(96,165,250,.34);color:#dbeafe}}
.statgrid{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}
.stat{{background:rgba(2,6,23,.40);border:1px solid rgba(148,163,184,.15);border-radius:12px;padding:9px}}
.label{{font-size:10px;text-transform:uppercase;letter-spacing:.14em;color:#aab4c6;font-weight:900}}
.value{{font-size:20px;font-weight:950;margin-top:3px}}
.value .rank-mini{{font-size:11px;margin-left:6px;vertical-align:middle}}
.game-proj-strip{{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:2px}}
.game-proj-pill{{font-size:15px;font-weight:1000;border-radius:999px;padding:8px 12px;border:1px solid rgba(96,165,250,.30);background:rgba(96,165,250,.14);color:#dbeafe}}
.game-proj-pill.market{{background:rgba(34,197,94,.16);border-color:rgba(34,197,94,.34);color:#bbf7d0}}
.game-proj-pill.total{{background:rgba(234,179,8,.15);border-color:rgba(234,179,8,.34);color:#fef3c7}}
.score-banner{{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;padding:9px 15px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18);font-weight:1000;font-size:16px}}
.score-banner.conflict{{background:rgba(234,179,8,.15);border-color:rgba(234,179,8,.42);color:#fef3c7}}
.point-label{{font-size:10px;fill:#dbeafe;font-weight:1000;text-shadow:0 1px 2px rgba(0,0,0,.75)}}
.point-label.model{{fill:#bbf7d0}}
.game-hero{{padding:16px 16px 14px;text-align:center;display:flex;flex-direction:column;justify-content:flex-start;gap:8px}}
.kicker{{font-size:12px;color:#93c5fd;letter-spacing:.16em;text-transform:uppercase;font-weight:950}}
.match-title{{display:flex;align-items:center;justify-content:center;gap:14px;flex-wrap:wrap}}
.vs{{font-weight:950;color:#94a3b8;font-size:16px}}
.bigline{{font-size:44px;font-weight:1000;letter-spacing:-.04em;line-height:1}}
.subline{{display:flex;align-items:center;justify-content:center;gap:10px;flex-wrap:wrap;color:#cbd5e1;font-weight:800}}
.dashboard{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin:12px 0 14px}}
.edge-card{{background:linear-gradient(180deg,rgba(15,23,42,.88),rgba(15,23,42,.66));border:1px solid var(--line);border-radius:16px;padding:12px;min-height:96px}}
.edge-card .label{{margin-bottom:8px}}
.edge-main{{font-size:18px;font-weight:1000}}
.edge-note{{font-size:12px;color:#cbd5e1;margin-top:6px;line-height:1.25}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}}
.grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:14px}}
.card{{padding:14px;overflow:hidden}}
.card-title{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px;font-weight:1000;text-transform:uppercase;letter-spacing:.13em;font-size:13px;color:#dbeafe}}
.table-wrap{{overflow:auto;border-radius:12px;border:1px solid rgba(148,163,184,.15)}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#aab4c6;background:rgba(30,41,59,.72);padding:8px;white-space:nowrap}}
td{{padding:8px;border-top:1px solid rgba(148,163,184,.13);vertical-align:top;white-space:nowrap}}
tr:nth-child(even) td{{background:rgba(148,163,184,.035)}}
.metric-row{{display:grid;grid-template-columns:1.1fr .9fr .9fr .9fr;gap:8px;align-items:center;border-top:1px solid rgba(148,163,184,.13);padding:9px 0}}
.metric-row:first-child{{border-top:none}}
.factor-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.factor-side{{border:1px solid rgba(148,163,184,.16);border-radius:14px;overflow:hidden;background:rgba(2,6,23,.26)}}
.factor-head{{display:flex;justify-content:center;gap:10px;align-items:center;padding:10px;background:rgba(30,41,59,.55);font-weight:1000;text-transform:uppercase;letter-spacing:.12em;font-size:12px}}
.factor-table th,.factor-table td{{text-align:center}}
.factor-table td.metric-name{{text-align:center;font-weight:950}}
.edge-pill{{display:inline-flex;align-items:center;justify-content:center;gap:4px;border-radius:999px;padding:5px 9px;min-width:34px;background:rgba(148,163,184,.14);color:#cbd5e1;font-weight:1000;font-size:12px;white-space:nowrap}}
.edge-pill.edge-off,.edge-pill.edge-def{{background:rgba(34,197,94,.16);border:1px solid rgba(34,197,94,.35);color:#bbf7d0}}
.edge-pill.even{{background:rgba(148,163,184,.12);color:#94a3b8}}
.rank-chip{{display:inline-flex;align-items:center;justify-content:center;min-width:34px;border-radius:8px;padding:3px 6px;font-size:12px;line-height:1;font-weight:1000;background:rgba(148,163,184,.16);color:#dbeafe}}
.rank-chip.green{{background:rgba(34,197,94,.86);color:#052e16}}
.rank-chip.yellow{{background:rgba(234,179,8,.92);color:#2a1e02}}
.rank-chip.red{{background:rgba(239,68,68,.88);color:#fff}}
.spot-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}}
.spot-team{{border:1px solid rgba(148,163,184,.15);border-radius:12px;padding:10px;background:rgba(2,6,23,.28)}}
.spot-list{{display:flex;gap:7px;flex-wrap:wrap;margin-top:7px}}
.spot-item{{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:900;color:#cbd5e1}}
.spot-box{{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;border-radius:5px;border:1px solid rgba(148,163,184,.38);color:#051018;background:rgba(15,23,42,.7)}}
.spot-box.checked.good{{background:#22c55e;border-color:#22c55e}}
.spot-box.checked.warn{{background:#eab308;border-color:#eab308}}
.spot-box.checked.bad{{background:#ef4444;border-color:#ef4444;color:white}}
.market-lines{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.market-line{{padding:9px;border:1px solid rgba(148,163,184,.14);border-radius:12px;background:rgba(2,6,23,.30)}}
.market-line b{{display:block;margin-bottom:4px}}

.edge-snapshot{{margin-top:8px;border:1px solid rgba(148,163,184,.22);background:rgba(2,6,23,.28);border-radius:15px;overflow:hidden;text-align:center}}
.snapshot-title{{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:9px 12px;background:rgba(30,41,59,.55);border-bottom:1px solid rgba(148,163,184,.18)}}
.snapshot-title .title{{font-size:11px;letter-spacing:.18em;text-transform:uppercase;font-weight:1000;color:#dbeafe}}
.snapshot-title .summary{{font-size:11px;color:#aab4c6;font-weight:900}}
.edge-table{{width:100%;border-collapse:collapse;table-layout:fixed;font-size:11px}}
.edge-table th{{padding:7px 6px;color:#aab4c6;font-size:9px;letter-spacing:.14em;text-transform:uppercase;border-bottom:1px solid rgba(148,163,184,.16)}}
.edge-table td{{padding:5px 6px;border-bottom:1px solid rgba(148,163,184,.11);vertical-align:middle;text-align:center}}
.edge-table tr:last-child td{{border-bottom:0}}
.edge-table .cat{{font-weight:1000;color:#e5e7eb;line-height:1.05}}
.edge-table .subcat{{display:block;color:#94a3b8;font-size:8px;font-weight:900;letter-spacing:.07em;text-transform:uppercase;margin-top:2px}}
.snap-edge{{display:inline-flex;align-items:center;justify-content:center;min-height:22px;border-radius:999px;padding:4px 8px;font-size:10px;font-weight:1000;white-space:nowrap;border:1px solid rgba(148,163,184,.22);background:rgba(148,163,184,.10);color:#aeb8c8}}
.snap-edge.win{{background:rgba(34,197,94,.17);border-color:rgba(34,197,94,.42);color:#bbf7d0}}
.snap-edge.total{{background:rgba(234,179,8,.15);border-color:rgba(234,179,8,.42);color:#fef3c7}}
.snap-edge.bad{{background:rgba(239,68,68,.14);border-color:rgba(239,68,68,.36);color:#fecaca}}
.snapshot-note{{font-size:10px;color:#94a3b8;margin-top:6px;line-height:1.25}}

.game-tags{{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 14px}}
.game-tag{{display:inline-flex;align-items:center;gap:6px;border:1px solid rgba(96,165,250,.25);background:rgba(96,165,250,.10);border-radius:999px;padding:7px 10px;font-size:12px;font-weight:1000;color:#dbeafe}}
.game-tag.good{{background:rgba(34,197,94,.13);border-color:rgba(34,197,94,.32);color:#bbf7d0}}
.game-tag.warn{{background:rgba(234,179,8,.13);border-color:rgba(234,179,8,.32);color:#fef3c7}}
.game-tag.bad{{background:rgba(239,68,68,.13);border-color:rgba(239,68,68,.32);color:#fecaca}}
.market-fresh{{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}}

.weather-card{{margin-bottom:14px}}
.weather-grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-top:10px}}
.weather-cell{{border:1px solid rgba(148,163,184,.15);background:rgba(2,6,23,.30);border-radius:12px;padding:9px}}
.weather-cell b{{display:block;font-size:10px;text-transform:uppercase;letter-spacing:.11em;color:#aab4c6;margin-bottom:4px}}
.weather-val{{font-size:18px;font-weight:1000}}
.weather-flags{{display:flex;gap:7px;flex-wrap:wrap;margin-top:8px}}
.weather-flag{{display:inline-flex;align-items:center;border-radius:999px;padding:5px 9px;border:1px solid rgba(148,163,184,.25);background:rgba(148,163,184,.10);font-size:11px;font-weight:1000;color:#dbeafe}}
.weather-flag.warn{{background:rgba(234,179,8,.14);border-color:rgba(234,179,8,.36);color:#fef3c7}}
.weather-flag.bad{{background:rgba(239,68,68,.14);border-color:rgba(239,68,68,.36);color:#fecaca}}
.weather-flag.good{{background:rgba(34,197,94,.13);border-color:rgba(34,197,94,.34);color:#bbf7d0}}
@media(max-width:900px){{.weather-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:700px){{.market-lines,.spot-grid{{grid-template-columns:1fr}}}}
@media(max-width:1000px){{.factor-grid{{grid-template-columns:1fr}}}}
.metric-name{{font-weight:900}}
.bar{{height:10px;border-radius:999px;background:rgba(148,163,184,.18);overflow:hidden}}
.bar>span{{display:block;height:100%;background:linear-gradient(90deg,#60a5fa,#22c55e);width:50%}}
.read-box{{font-size:14px;line-height:1.45;color:#d1d5db}}
.read-box b{{color:white}}
.team-chip{{font-weight:1000;color:#fff}}
.summary-list{{display:grid;gap:8px}}
.summary-item{{padding:10px;border:1px solid rgba(148,163,184,.15);border-radius:12px;background:rgba(2,6,23,.32)}}
.summary-item b{{display:block;margin-bottom:3px}}
details{{border:1px solid rgba(148,163,184,.16);border-radius:14px;background:rgba(2,6,23,.24);padding:10px;margin-top:10px}}
summary{{cursor:pointer;font-weight:950;color:#bfdbfe}}
@media(max-width:1000px){{.hero{{grid-template-columns:1fr}}.dashboard{{grid-template-columns:repeat(2,1fr)}}.grid2,.grid3{{grid-template-columns:1fr}}.bigline{{font-size:34px}}}}
</style>
</head>
<body>
<div class="page">
  <div class="topbar">
    <a class="back" href="index.html">← Season Schedule</a>
    <div class="small">2026 NCAAF betting matchup card · compact view</div>
  </div>
  <div id="app"></div>
</div>
<script id="db" type="application/json">{safe_json(db)}</script>
<script id="game-injury-overlay-data" type="application/json">{safe_json(inj)}</script>
<script id="game-line-model-history-data" type="application/json">{safe_json(history_rows)}</script>
<script id="rating-trends-data" type="application/json">{safe_json(rating_trends)}</script>
<script id="returning-production-data" type="application/json">{safe_json(returning_prod)}</script>
<script id="game-weather-latest-data" type="application/json">{safe_json(weather_rows)}</script>
<script>
const DB = JSON.parse(document.getElementById('db').textContent);
let INJURY = [];
try {{ INJURY = JSON.parse(document.getElementById('game-injury-overlay-data').textContent || '[]'); }} catch(e) {{ INJURY = []; }}
let MATCHUP_HISTORY = [];
try {{ MATCHUP_HISTORY = JSON.parse(document.getElementById('game-line-model-history-data').textContent || '[]'); }} catch(e) {{ MATCHUP_HISTORY = []; }}
let RATING_TRENDS = {{}};
try {{ RATING_TRENDS = JSON.parse(document.getElementById('rating-trends-data').textContent || '{{}}'); }} catch(e) {{ RATING_TRENDS = {{}}; }}
let RETURNING_PRODUCTION = {{}};
try {{ RETURNING_PRODUCTION = JSON.parse(document.getElementById('returning-production-data').textContent || '{{}}'); }} catch(e) {{ RETURNING_PRODUCTION = {{}}; }}
let GAME_WEATHER = [];
try {{ GAME_WEATHER = JSON.parse(document.getElementById('game-weather-latest-data').textContent || '[]'); }} catch(e) {{ GAME_WEATHER = []; }}
const teamByName = {{}};
(DB.teams||[]).forEach(t=>{{teamByName[String(t.team||'').toLowerCase()] = t;}});
const OFF_RANKS = Object.fromEntries((DB.teams||[]).filter(t=>Number.isFinite(Number(t.sp_offense))).slice().sort((a,b)=>Number(b.sp_offense)-Number(a.sp_offense)).map((t,i)=>[t.team,i+1]));
const DEF_RANKS = Object.fromEntries((DB.teams||[]).filter(t=>Number.isFinite(Number(t.sp_defense))).slice().sort((a,b)=>Number(a.sp_defense)-Number(b.sp_defense)).map((t,i)=>[t.team,i+1]));
function absRankMap(rows, teamKey){{
  return Object.fromEntries((rows||[]).filter(r=>Number.isFinite(Number(r.avg_total_margin))).slice().sort((a,b)=>Math.abs(Number(b.avg_total_margin))-Math.abs(Number(a.avg_total_margin))).map((r,i)=>[String(r[teamKey]||r.team||r.current_team),i+1]));
}}
const COACH_OU_RANKS = absRankMap(DB.coach_betting||[], 'team');
const COACH_1H_OU_RANKS = absRankMap(DB.coach_1h_betting||[], 'current_team');
const COACH_2H_OU_RANKS = absRankMap(DB.coach_2h_betting||[], 'current_team');

const LOGO_BADGE_TEAMS = new Set(['Air Force','Boise State','BYU','Duke','Georgia Tech','Iowa','Navy','North Carolina','North Dakota State','Notre Dame','Penn State','Pittsburgh','Rice','Toledo','Tulane','UTEP','Virginia','Wake Forest','West Virginia']);
function teamImageFileForTeam(t){{if(!t) return null; if(t.team==='Texas A&M') return 'texas-aandm'; return t.slug;}}
function teamLogo(name){{const t=teamByName[String(name||'').toLowerCase()]; if(!t) return ''; const file=teamImageFileForTeam(t); if(!file) return ''; const badge=LOGO_BADGE_TEAMS.has(t.team)?' needs-badge':''; return `<span class="team-logo-wrap${{badge}}"><img class="team-logo" src="logos/${{file}}.png" alt="" loading="lazy" onerror="this.closest('.team-logo-wrap').style.display='none'"></span>`;}}
function teamLabel(name, cls=''){{return `<span class="team-with-logo ${{cls}}">${{teamLogo(name)}}<span>${{esc(name||'—')}}</span></span>`;}}
function teamRankLabel(name, cls=''){{const t=teamRow(name); return `<span class="team-with-logo ${{cls}}">${{teamLogo(name)}}<span>${{esc(name||'—')}}</span>${{rankChip(t.rank)}}</span>`;}}
function rankMini(r){{if(r==null||!Number.isFinite(Number(r))) return ''; return `<span class="rank-mini">${{rankChip(r)}}</span>`;}}
function toneForSigned(v){{const n=Number(v); if(!Number.isFinite(n)||Math.abs(n)<0.1) return 'neu'; return n>0?'pos':'neg';}}
function signedMini(v,d=1){{const n=Number(v); if(!Number.isFinite(n)) return '—'; return (n>0?'+':'')+n.toFixed(d);}}
function trendMini(team){{
  const tr=RATING_TRENDS[String(team||'')];
  if(!tr) return '';
  const rankMove=Number(tr.rank_trend);
  const rankText=Number.isFinite(rankMove)?(rankMove>0?`Up ${{Math.round(rankMove)}}`:rankMove<0?`Down ${{Math.abs(Math.round(rankMove))}}`:'Flat'):'—';
  return `<div class="mini-panel"><div class="mini-head"><span>Rating trend</span><span>${{esc(tr.source_count_2025!=null?tr.source_count_2025+'/5 src':'')}}</span></div><div class="mini-grid"><div class="mini-stat"><div class="mini-label">2025 EOY</div><div class="mini-value">${{num(tr.rating_2025_eoy,1)}} ${{rankMini(tr.rank_2025_eoy)}}</div></div><div class="mini-stat"><div class="mini-label">Rating Δ</div><div class="mini-value ${{toneForSigned(tr.rating_trend)}}">${{signedMini(tr.rating_trend,1)}}</div></div><div class="mini-stat"><div class="mini-label">Rank Δ</div><div class="mini-value ${{toneForSigned(rankMove)}}">${{esc(rankText)}}</div></div></div></div>`;
}}
function returningProdForTeam(team){{
  if(RETURNING_PRODUCTION[team]) return RETURNING_PRODUCTION[team];
  const norm=String(team||'').toLowerCase().replace(/[^a-z0-9]/g,'');
  for(const [k,v] of Object.entries(RETURNING_PRODUCTION||{{}})){{if(String(k).toLowerCase().replace(/[^a-z0-9]/g,'')===norm) return v;}}
  return null;
}}
function returningMini(team){{
  const rp=returningProdForTeam(team);
  if(!rp) return '';
  return `<div class="mini-panel"><div class="mini-head returning-head"><span>Returning prod</span><span>${{num(rp.overall,0)}}% ${{rankChip(rp.rank)}}</span></div><div class="mini-grid returning-prod-grid"><div class="mini-stat"><div class="mini-label">Off</div><div class="mini-value">${{num(rp.off,0)}}% ${{rankMini(rp.offRank)}}</div></div><div class="mini-stat"><div class="mini-label">Def</div><div class="mini-value">${{num(rp.def,0)}}% ${{rankMini(rp.defRank)}}</div></div></div></div>`;
}}
function coachMini(team){{
  const c=coachRow(team), h1=coachHalf(team,'1H'), h2=coachHalf(team,'2H');
  if(!c&&!h1&&!h2) return '';
  const coach=c.head_coach||h1.head_coach||h2.head_coach||'';
  const atsRec=r=>esc(r.ats_record||((r.ats_w!=null&&r.ats_l!=null)?r.ats_w+'-'+r.ats_l:'—'));
  const ouRec=r=>esc(r.ou_record||r.over_under_record||((r.overs!=null&&r.unders!=null)?r.overs+'-'+r.unders:'—'));
  const ouRank=(label)=>label==='Game'?COACH_OU_RANKS[team]:(label==='1H'?COACH_1H_OU_RANKS[team]:COACH_2H_OU_RANKS[team]);
  const row=(label,r)=>`<div class="coach-row-mini"><div class="mini-stat"><div class="mini-label">${{label}} ATS</div><div class="mini-value">${{atsRec(r)}} ${{rankMini(r.ats_rank)}}</div></div><div class="mini-stat"><div class="mini-label">${{label}} O/U</div><div class="mini-value">${{ouRec(r)}} ${{rankMini(ouRank(label))}}</div></div></div>`;
  return `<div class="mini-panel coach-mini"><div class="mini-head"><span>Coach betting</span><span>${{esc(coach)}}</span></div><div class="coach-rows">${{row('Game',c)}}${{row('1H',h1)}}${{row('2H',h2)}}</div></div>`;
}}

function sportsbookLogo(book){{const raw=String(book||'').trim(); const b=raw.toLowerCase(); let src='', label=raw||'Book'; if(b.includes('fanduel')||b==='fd'||b==='fan duel'){{src='logos/books/fanduel.png';label='FanDuel';}} else if(b.includes('draftkings')||b==='dk'||b==='draft kings'){{src='logos/books/draftkings.png';label='DraftKings';}} else if(b.includes('betmgm')||b.includes('mgm')){{src='logos/books/betmgm.png';label='BetMGM';}} else if(b.includes('caesars')||b.includes('caesar')||b==='cz'){{src='logos/books/caesars.png';label='Caesars';}} if(!src) return raw?`<span class="pill">${{esc(raw)}}</span>`:'—'; return `<span class="sportsbook-logo-wrap" title="${{esc(label)}}"><img class="sportsbook-logo" src="${{src}}" alt="${{esc(label)}}"></span>`;}}
function bookStrip(books){{const arr=String(books||'').split(',').map(x=>x.trim()).filter(Boolean); if(!arr.length) return '—'; return `<span class="book-strip">${{arr.map(sportsbookLogo).join('')}}</span>`;}}
const $ = (sel, root=document) => root.querySelector(sel);
function esc(x){{return String(x ?? '').replace(/[&<>"']/g, c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));}}
function num(x,d=1){{const n=Number(x); return Number.isFinite(n)?n.toFixed(d):'—';}}
function pct(x,d=0){{const n=Number(x); return Number.isFinite(n)?(n*100).toFixed(d)+'%':'—';}}
function signed(x,d=1){{const n=Number(x); if(!Number.isFinite(n)) return '—'; return (n>0?'+':'')+n.toFixed(d);}}
function spreadText(team, spread){{const n=Number(spread); if(!Number.isFinite(n)) return '—'; return team+' '+(n>0?'+':'')+n.toFixed(Math.abs(n)%1?1:0);}}
function fmtDate(s){{if(!s) return 'TBD'; const d=new Date(s+'T12:00:00'); if(isNaN(d)) return esc(s); return d.toLocaleDateString(undefined,{{month:'short',day:'numeric'}});}}
function fmtDateTime(s){{if(!s) return '—'; const d=new Date(s); if(isNaN(d)) return esc(s); return d.toLocaleString(undefined,{{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}});}}
function teamRow(team){{return (DB.teams||[]).find(t=>String(t.team)===String(team)) || {{team}};}}
function coachRow(team){{return (DB.coach_betting||[]).find(t=>String(t.team)===String(team)) || {{}};}}
function coachHalf(team, half){{const arr = half==='1H' ? DB.coach_1h_betting : DB.coach_2h_betting; return (arr||[]).find(t=>String(t.team)===String(team) || String(t.current_team)===String(team)) || {{}};}}
function styleRow(team){{return (DB.team_style_profiles||[]).find(t=>String(t.team)===String(team)) || {{}};}}
function firstVal(obj, keys){{for(const k of keys){{const v=obj?.[k]; if(v!==undefined && v!==null && v!=='' && Number.isFinite(Number(v))) return Number(v);}} return null;}}
function styleMetric(team, metric, side){{const s=styleRow(team)||{{}}; const map={{
  success: side==='off'?['success_rate_score','off_success_score','offense_score']:['success_prevent_score','def_success_score','defense_score'],
  explosive: side==='off'?['explosive_score','explosiveness_score']:['expl_prevent_score','explosive_prevention_score','def_explosive_score'],
  finishing: side==='off'?['finishing_drives_score','finishing_score','finish_score','red_zone_score','offense_score']:['finishing_prevent_score','finish_prevent_score','red_zone_def_score','defense_score'],
  field: side==='off'?['field_position_score','field_pos_score','starting_field_position_score','tempo_score','offense_score']:['field_position_prevent_score','field_pos_def_score','starting_field_position_def_score','defense_score'],
  havoc: side==='off'?['havoc_avoid_score','havoc_allowed_score','ball_security_score','turnover_avoidance_score','offense_score']:['havoc_creation_score','havoc_rate_score','pressure_score','defense_score']
}}; return firstVal(s,map[metric]||[]);}}
function metricRank(team, metric, side){{const v=styleMetric(team,metric,side); return v==null?null:Math.max(1,Math.min(138,Math.round(139-Number(v)*1.38)));}}
function rankChip(r){{if(r==null||!Number.isFinite(Number(r))) return '<span class="rank-chip">—</span>'; r=Number(r); const cls=r<=35?'green':r<=75?'yellow':'red'; return `<span class="rank-chip ${{cls}}">#${{Math.round(r)}}</span>`;}}
function checkCountByRankGap(gap){{const n=Math.abs(Number(gap)); if(!Number.isFinite(n)||n<8) return 0; if(n<25) return 1; if(n<55) return 2; return 3;}}
function edgePill(team,count,cls){{if(!team||!count) return '<span class="edge-pill even">—</span>'; return `<span class="edge-pill ${{cls}}">${{esc(team)}} ${{'✓'.repeat(Math.max(1,Math.min(3,count)))}}</span>`;}}
function factorRow(label, metric, offTeam, defTeam){{const or=metricRank(offTeam,metric,'off'); const dr=metricRank(defTeam,metric,'def'); let offEdge='<span class="edge-pill even">—</span>'; let defEdge='<span class="edge-pill even">—</span>'; if(or!=null&&dr!=null){{const gap=Number(dr)-Number(or); const count=checkCountByRankGap(gap); if(count&&gap>0) offEdge=edgePill(offTeam,count,'edge-off'); else if(count&&gap<0) defEdge=edgePill(defTeam,count,'edge-def');}} return `<tr><td>${{offEdge}}</td><td>${{rankChip(or)}}</td><td class="metric-name">${{esc(label)}}</td><td>${{rankChip(dr)}}</td><td>${{defEdge}}</td></tr>`;}}
function fiveFactorsSide(offTeam,defTeam){{return `<div class="factor-side"><div class="factor-head"><span>${{teamLabel(offTeam)}} OFF</span><span class="muted">vs</span><span>${{teamLabel(defTeam)}} DEF</span></div><div class="table-wrap" style="border:0;border-radius:0"><table class="factor-table"><thead><tr><th>Off Edge</th><th>Off Rk</th><th>Metric</th><th>Def Rk</th><th>Def Edge</th></tr></thead><tbody>${{factorRow('Success Rate','success',offTeam,defTeam)}}${{factorRow('Explosiveness','explosive',offTeam,defTeam)}}${{factorRow('Finishing Drives','finishing',offTeam,defTeam)}}${{factorRow('Field Position','field',offTeam,defTeam)}}${{factorRow('Havoc Rate','havoc',offTeam,defTeam)}}</tbody></table></div></div>`;}}
function fiveFactorsCard(g){{return `<div class="card"><div class="card-title"><span>Five Factors matchup edges</span><span class="small">ranks out of 138 · offense vs opponent defense</span></div><div class="factor-grid">${{fiveFactorsSide(g.away_team,g.home_team)}}${{fiveFactorsSide(g.home_team,g.away_team)}}</div></div>`;}}
function contextRow(team){{return (DB.team_context_ratings||[]).find(t=>String(t.team)===String(team)) || {{}};}}
function tcRow(team){{return (DB.teamcrafters_position_group_ratings||[]).find(t=>String(t.team)===String(team)) || {{}};}}
function injuryRow(gameId){{return INJURY.find(r=>String(r.game_id)===String(gameId)) || {{}};}}
function matchupRows(g){{return (DB.game_matchup_edges||[]).filter(r=>String(r.game_id)===String(g.game_id));}}
function getParam(k){{return new URLSearchParams(location.search).get(k);}}
function findGame(){{const gid=getParam('game_id')||getParam('id'); let g=(DB.games||[]).find(x=>String(x.game_id)===String(gid) || String(x.cfbd_game_id)===String(gid)); if(!g) g=(DB.games||[])[0]; return g;}}
function favoriteFromProjection(g){{const margin=Number(g.projected_margin_home); if(!Number.isFinite(margin)) return {{team:'—',spread:'—'}}; return margin>=0?{{team:g.home_team,spread:-Math.abs(margin)}}:{{team:g.away_team,spread:-Math.abs(margin)}};}}
function projectedScore(g){{const total=Number(g.projected_total), margin=Number(g.projected_margin_home); if(!Number.isFinite(total)||!Number.isFinite(margin)) return null; if(total < Math.abs(margin)-0.05) return {{conflict:true,total,margin,note:`Projection conflict: spread exceeds total (${{num(Math.abs(margin),1)}} > ${{num(total,1)}})`}}; const home=(total+margin)/2, away=(total-margin)/2; return {{away,home,conflict:false}};}}
function spreadEdge(g){{
  const m=Number(g.market_spread_home), margin=Number(g.projected_margin_home);
  if(!Number.isFinite(m)||!Number.isFinite(margin)) return {{team:'No edge',pts:0,note:'Missing market or projection'}};
  const projHomeSpread=-margin;
  const homeEdge=m - projHomeSpread;
  const fair = favoriteFromProjection(g);
  const fairText = `Model fair spread: ${{spreadText(fair.team, fair.spread)}}`;
  if(Math.abs(homeEdge)<0.75) return {{team:'No edge',pts:homeEdge,note:'Projection close to market'}};
  if(homeEdge>0) return {{team:g.home_team,pts:homeEdge,note:fairText}};
  return {{team:g.away_team,pts:-homeEdge,note:fairText}};
}}
function totalEdge(g){{const p=Number(g.projected_total), m=Number(g.market_total); if(!Number.isFinite(p)||!Number.isFinite(m)) return {{side:'No total',pts:0,note:'Missing market total'}}; const diff=p-m; if(Math.abs(diff)<1.5) return {{side:'No edge',pts:diff,note:'Projection near total'}}; return {{side:diff>0?'Over':'Under',pts:Math.abs(diff),note:`Projection ${{num(p,1)}} vs market ${{num(m,1)}}`}};}}
function moveText(g){{const cur=Number(g.market_spread_home), open=Number(g.market_spread_open_home); if(!Number.isFinite(cur)||!Number.isFinite(open)) return {{main:'No opener',note:'Opening line unavailable'}}; const mv=cur-open; if(Math.abs(mv)<0.25) return {{main:'Flat',note:'No meaningful spread move'}}; return mv<0?{{main:`Toward ${{g.home_team}}`,note:`Home spread moved ${{signed(mv,1)}} pts`}}:{{main:`Toward ${{g.away_team}}`,note:`Home spread moved ${{signed(mv,1)}} pts`}};}}
function coachEdge(g){{const a=coachRow(g.away_team), h=coachRow(g.home_team); const am=Number(a.avg_ats_margin), hm=Number(h.avg_ats_margin); if(!Number.isFinite(am)||!Number.isFinite(hm)) return {{team:'No edge',note:'Coach ATS data incomplete'}}; const diff=hm-am; if(Math.abs(diff)<0.6) return {{team:'No edge',note:'Similar full-game ATS profiles'}}; return diff>0?{{team:g.home_team,note:`Coach ATS margin edge ${{signed(diff,1)}}`}}:{{team:g.away_team,note:`Coach ATS margin edge ${{signed(-diff,1)}}`}};}}
function injuryEdge(g){{const r=injuryRow(g.game_id); const away=Number(r.away_injury_score||0), home=Number(r.home_injury_score||0); if(!away&&!home) return {{main:'No injury edge',note:'No current impact flagged'}}; const diff=away-home; if(Math.abs(diff)<1) return {{main:'Balanced injuries',note:`${{g.away_team}} ${{num(away,1)}} · ${{g.home_team}} ${{num(home,1)}}`}}; return diff>0?{{main:`${{g.home_team}} edge`,note:`${{g.away_team}} more injured by ${{num(diff,1)}}`}}:{{main:`${{g.away_team}} edge`,note:`${{g.home_team}} more injured by ${{num(-diff,1)}}`}};}}
function checkMarks(v){{const n=Math.abs(Number(v)||0); if(n>=6) return '✓✓✓'; if(n>=3) return '✓✓'; if(n>=1.5) return '✓'; return '';}}
function dashEdge(){{return '<span class="snap-edge">—</span>';}}
function snapPill(label, cls='win'){{return `<span class="snap-edge ${{cls}}">${{esc(label)}}</span>`;}}
function edgeCells(edgeTeam, label, cls, awayTeam, homeTeam){{
  if(!edgeTeam||edgeTeam==='Game'||edgeTeam==='No edge'||edgeTeam==='Mixed') return [dashEdge(), snapPill(label||edgeTeam||'No edge', cls||'')];
  if(edgeTeam===awayTeam) return [snapPill(label, cls||'win'), dashEdge()];
  if(edgeTeam===homeTeam) return [dashEdge(), snapPill(label, cls||'win')];
  return [dashEdge(), snapPill(label, cls||'')];
}}
function rpEdgeOverall(a,h){{
  const ar=returningProdForTeam(a), hr=returningProdForTeam(h); if(!ar||!hr) return {{team:null,label:'—'}};
  const diff=Number(ar.overall)-Number(hr.overall); if(!Number.isFinite(diff)||Math.abs(diff)<4) return {{team:'Game',label:'No edge',cls:''}};
  const team=diff>0?a:h; return {{team,label:`${{team}} ${{checkMarks(diff)||'✓'}}`,cls:'win'}};
}}
function rpMatchupEdge(offTeam,defTeam){{
  const off=returningProdForTeam(offTeam), def=returningProdForTeam(defTeam); if(!off||!def) return {{team:null,label:'—'}};
  const diff=Number(off.off)-Number(def.def); if(!Number.isFinite(diff)||Math.abs(diff)<4) return {{team:'Game',label:'No edge',cls:''}};
  const team=diff>0?offTeam:defTeam; const side=diff>0?'O':'D'; return {{team,label:`${{team}} ${{side}} ${{checkMarks(diff)||'✓'}}`,cls:'win'}};
}}
function coachAtsSnapshot(a,h,half){{
  const ar=half==='Game'?coachRow(a):coachHalf(a,half); const hr=half==='Game'?coachRow(h):coachHalf(h,half);
  const av=Number(ar.avg_ats_margin ?? ar.avg_ats ?? ar.ats_margin); const hv=Number(hr.avg_ats_margin ?? hr.avg_ats ?? hr.ats_margin);
  if(!Number.isFinite(av)||!Number.isFinite(hv)||Math.abs(av-hv)<0.6) return {{team:'Game',label:'No edge',cls:''}};
  const team=av>hv?a:h; return {{team,label:`${{team}} ${{checkMarks(Math.abs(av-hv))||'✓'}}`,cls:'win'}};
}}
function coachTotalsSnapshot(a,h){{
  const ar=coachRow(a), hr=coachRow(h); const av=Number(ar.avg_total_margin), hv=Number(hr.avg_total_margin);
  if(!Number.isFinite(av)||!Number.isFinite(hv)) return {{team:'Game',label:'—',cls:''}};
  if(av>0.8&&hv>0.8) return {{team:'Game',label:`Over ${{checkMarks((av+hv)/2)||'✓'}}`,cls:'total'}};
  if(av<-0.8&&hv<-0.8) return {{team:'Game',label:`Under ${{checkMarks((Math.abs(av)+Math.abs(hv))/2)||'✓'}}`,cls:'total'}};
  return {{team:'Game',label:'Mixed',cls:''}};
}}
function scheduleSpotSnapshot(g){{
  const a=g.away_team,h=g.home_team; const af=situationalFlags(g,a), hf=situationalFlags(g,h);
  const score=flags=>flags.reduce((s,f)=>s+(f.cls==='good'?1:f.cls==='bad'?-1:0),0);
  const diff=score(af)-score(hf); if(Math.abs(diff)<1) return {{team:'Game',label:'No edge',cls:''}};
  const team=diff>0?a:h; return {{team,label:`${{team}} ${{diff>0?'spot':'spot'}} ✓`,cls:'win'}};
}}
function injuriesSnapshot(g){{
  const ie=injuryEdge(g); if(String(ie.main).toLowerCase().includes('no injury')||String(ie.main).toLowerCase().includes('balanced')) return {{team:'Game',label:String(ie.main).includes('Balanced')?'Balanced':'No edge',cls:''}};
  const team=String(ie.main).replace(' edge',''); return {{team,label:`${{team}} ✓`,cls:'win'}};
}}
function snapshotRow(awayCell,cat,sub,homeCell){{return `<tr><td>${{awayCell}}</td><td class="cat">${{esc(cat)}}${{sub?`<span class="subcat">${{esc(sub)}}</span>`:''}}</td><td>${{homeCell}}</td></tr>`;}}
function bettingEdgeSnapshot(g){{
  const a=g.away_team,h=g.home_team; const rows=[];
  const se=spreadEdge(g); let [l,r]=edgeCells(se.team, se.team==='No edge'?'No edge':`${{se.team}} ${{signed(se.pts,1)}} ${{checkMarks(se.pts)}}`, 'win', a, h); rows.push(snapshotRow(l,'Spread Value','',r));
  const te=totalEdge(g); rows.push(snapshotRow(dashEdge(),'Total Value','', te.side==='No edge'||te.side==='No total'?snapPill('No edge',''):snapPill(`${{te.side}} ${{signed(te.pts,1)}}`,'total')));
  let e=rpEdgeOverall(a,h); [l,r]=edgeCells(e.team,e.label,e.cls,a,h); rows.push(snapshotRow(l,'Returning Production','Overall',r));
  e=rpMatchupEdge(a,h); [l,r]=edgeCells(e.team,e.label,e.cls,a,h); rows.push(snapshotRow(l,`${{a}} Off RP`,`vs ${{h}} Def RP`,r));
  e=rpMatchupEdge(h,a); [l,r]=edgeCells(e.team,e.label,e.cls,a,h); rows.push(snapshotRow(l,`${{h}} Off RP`,`vs ${{a}} Def RP`,r));
  e=coachAtsSnapshot(a,h,'Game'); [l,r]=edgeCells(e.team,e.label,e.cls,a,h); rows.push(snapshotRow(l,'Coach ATS','Full Game',r));
  e=coachAtsSnapshot(a,h,'1H'); [l,r]=edgeCells(e.team,e.label,e.cls,a,h); rows.push(snapshotRow(l,'Coach ATS','1H',r));
  e=coachAtsSnapshot(a,h,'2H'); [l,r]=edgeCells(e.team,e.label,e.cls,a,h); rows.push(snapshotRow(l,'Coach ATS','2H',r));
  e=coachTotalsSnapshot(a,h); [l,r]=edgeCells(e.team,e.label,e.cls,a,h); rows.push(snapshotRow(l,'Coach Totals','',r));
  e=scheduleSpotSnapshot(g); [l,r]=edgeCells(e.team,e.label,e.cls,a,h); rows.push(snapshotRow(l,'Schedule Spot','',r));
  e=injuriesSnapshot(g); [l,r]=edgeCells(e.team,e.label,e.cls,a,h); rows.push(snapshotRow(l,'Injuries','',r));
  return `<div class="edge-snapshot"><div class="snapshot-title"><div class="title">Betting Edge Snapshot</div><div class="summary">Early-season inputs only</div></div><table class="edge-table"><thead><tr><th>${{esc(a)}} edge</th><th>Category</th><th>${{esc(h)}} / game edge</th></tr></thead><tbody>${{rows.join('')}}</tbody></table></div><div class="snapshot-note">Returning production matchup rows compare offense continuity versus opponent defensive continuity.</div>`;
}}

function daysBetween(a,b){{if(!a||!b) return null; const da=new Date(a), db=new Date(b); if(isNaN(da)||isNaN(db)) return null; return Math.round((db-da)/(1000*60*60*24));}}
function teamGames(team){{return (DB.games||[]).filter(g=>g.home_team===team||g.away_team===team).slice().sort((a,b)=>String(a.date||'').localeCompare(String(b.date||'')));}}
function opponent(g,team){{return g.home_team===team?g.away_team:g.home_team;}}
function isRoad(g,team){{return !g.neutral_site && g.away_team===team;}}
function scoreVal(g, side){{
  const keys = side==='home' ? ['home_points','home_score','home_pts','cfbd_home_points','cfbd_home_score'] : ['away_points','away_score','away_pts','cfbd_away_points','cfbd_away_score'];
  for(const k of keys){{ const v=Number(g[k]); if(Number.isFinite(v)) return v; }}
  return null;
}}
function teamSeasonRecord(team){{
  let w=0,l=0,atsW=0,atsL=0,atsP=0,ov=0,un=0,totP=0;
  (DB.games||[]).forEach(g=>{{
    if(!(g.home_team===team||g.away_team===team)) return;
    if(!g.cfbd_completed && !g.completed && !g.status_final) return;
    const home=g.home_team===team;
    const hp=scoreVal(g,'home'), ap=scoreVal(g,'away');
    if(hp==null||ap==null) return;
    const pf=home?hp:ap, pa=home?ap:hp;
    if(pf>pa) w++; else if(pf<pa) l++;
    const spreadHome=Number(g.market_spread_home ?? g.closing_spread_home ?? g.spread_home);
    if(Number.isFinite(spreadHome)){{
      const homeMargin=hp-ap;
      const cover=homeMargin + spreadHome;
      const teamCover=home?cover:-cover;
      if(teamCover>0) atsW++; else if(teamCover<0) atsL++; else atsP++;
    }}
    const total=Number(g.market_total ?? g.closing_total ?? g.total);
    if(Number.isFinite(total)){{
      const diff=hp+ap-total;
      if(diff>0) ov++; else if(diff<0) un++; else totP++;
    }}
  }});
  const ats=`${{atsW}}-${{atsL}}${{atsP?'-'+atsP:''}}`;
  const ou=`${{ov}}-${{un}}${{totP?'-'+totP:''}}`;
  return {{overall:`${{w}}-${{l}}`, ats, ou}};
}}
function recordLine(team){{
  const r=teamSeasonRecord(team);
  return `<div class="team-record-line"><span class="record-pill">${{esc(r.overall)}}</span><span class="record-pill">ATS ${{esc(r.ats)}}</span><span class="record-pill">O/U ${{esc(r.ou)}}</span></div>`;
}}

function situationalFlags(g,team){{const games=teamGames(team); const idx=games.findIndex(x=>String(x.game_id)===String(g.game_id)); const prev=idx>0?games[idx-1]:null; const next=idx>=0&&idx<games.length-1?games[idx+1]:null; const flags=[]; if(prev&&isRoad(prev,team)&&isRoad(g,team)) flags.push({{label:'B2B road',cls:'warn'}}); const rest=prev?daysBetween(prev.date,g.date):null; if(rest!=null&&rest>=10) flags.push({{label:'Off bye',cls:'good'}}); if(rest!=null&&rest<=5) flags.push({{label:'Short rest',cls:'bad'}}); if(next){{const opp=opponent(next,team); const o=teamRow(opp); const rivalry=(team==='Ohio State'&&opp==='Michigan')||(team==='Michigan'&&opp==='Ohio State'); if(rivalry||(o&&Number(o.rank)<=15)) flags.push({{label:'Lookahead',detail:opp,cls:'warn'}}); const prevOpp=prev?opponent(prev,team):''; const nextRank=Number(o.rank); const curOpp=opponent(g,team); const curRank=Number(teamRow(curOpp).rank); const prevRank=Number(teamRow(prevOpp).rank); if(Number.isFinite(prevRank)&&Number.isFinite(nextRank)&&Number.isFinite(curRank)&&prevRank<=40&&nextRank<=40&&curRank>60) flags.push({{label:'Sandwich',cls:'warn'}}); }} return flags;}}
function spotChecklist(team,g){{const flags=situationalFlags(g,team); const labels=[['B2B road','warn'],['Off bye','good'],['Short rest','bad'],['Lookahead','warn'],['Sandwich','warn']]; const raw=flags.map(f=>String(f.label||'').toLowerCase()); return `<div class="spot-list">${{labels.map(([label,cls])=>{{const checked=raw.some(x=>x.includes(label.toLowerCase().split(' ')[0]) || x===label.toLowerCase()); return `<span class="spot-item"><span class="spot-box ${{checked?'checked '+cls:''}}">${{checked?'✓':''}}</span>${{esc(label)}}</span>`;}}).join('')}}</div>`;}}
function spotCard(g,team){{const flags=situationalFlags(g,team); const note=flags.length?flags.map(f=>f.detail?`${{f.label}}: ${{f.detail}}`:f.label).join(' · '):'Clean schedule spot'; return `<div class="spot-team"><b>${{teamLabel(team)}}</b><div class="small">${{esc(note)}}</div>${{spotChecklist(team,g)}}</div>`;}}
function edgeClass(points){{points=Number(points)||0; if(Math.abs(points)>=3) return 'good'; if(Math.abs(points)>=1.5) return 'warn'; return 'blue';}}
function teamHero(team, side){{const t=teamRow(team), c=contextRow(team), st=styleRow(team); return `<div class="team-hero">
  <div class="kicker">${{side}}</div><div class="team-name">${{teamRankLabel(team)}}</div>${{recordLine(team)}}
  <div class="team-meta"><span class="pill blue">${{esc(t.conference||'')}}</span><span class="pill">Rank #${{esc(t.rank||'—')}}</span><span class="pill">HFA ${{num(t.hfa,1)}}</span></div>
  <div class="statgrid"><div class="stat"><div class="label">Power</div><div class="value">${{num(t.combo,1)}} ${{rankMini(t.rank)}}</div></div><div class="stat"><div class="label">Off</div><div class="value">${{num(t.sp_offense,1)}} ${{rankMini(OFF_RANKS[team])}}</div></div><div class="stat"><div class="label">Def</div><div class="value">${{num(t.sp_defense,1)}} ${{rankMini(DEF_RANKS[team])}}</div></div></div>
  <div class="team-mini-panels">${{trendMini(team)}}${{returningMini(team)}}${{coachMini(team)}}</div>
  <div class="small">${{esc(st.style_summary || st.play_call_style || 'Style profile pending')}}${{c.luck_rank?` · Luck rank #${{esc(c.luck_rank)}}`:''}}</div>
</div>`;}}
function dashboard(g){{const se=spreadEdge(g), te=totalEdge(g), mv=moveText(g), ce=coachEdge(g), ie=injuryEdge(g); const proj=favoriteFromProjection(g); return `<div class="dashboard">
  <div class="edge-card"><div class="label">Spread Edge</div><div class="edge-main"><span class="pill ${{edgeClass(se.pts)}}">${{esc(se.team)}} ${{se.team==='No edge'?'':signed(se.pts,1)}}</span></div><div class="edge-note">${{esc(se.note)}}</div></div>
  <div class="edge-card"><div class="label">Total Edge</div><div class="edge-main"><span class="pill ${{edgeClass(te.pts)}}">${{esc(te.side)}} ${{te.side==='No edge'||te.side==='No total'?'':signed(te.pts,1)}}</span></div><div class="edge-note">${{esc(te.note)}}</div></div>
  <div class="edge-card"><div class="label">Market Move</div><div class="edge-main">${{esc(mv.main)}}</div><div class="edge-note">${{esc(mv.note)}}</div></div>
  <div class="edge-card"><div class="label">Injury Edge</div><div class="edge-main">${{esc(ie.main)}}</div><div class="edge-note">${{esc(ie.note)}}</div></div>
  <div class="edge-card"><div class="label">Coach Edge</div><div class="edge-main">${{esc(ce.team)}}</div><div class="edge-note">${{esc(ce.note)}}</div></div>
  <div class="edge-card"><div class="label">Model Fair</div><div class="edge-main">${{esc(proj.team)}}</div><div class="edge-note">${{esc(spreadText(proj.team, proj.spread))}} · total ${{num(g.projected_total,1)}}</div></div>
</div>`;}}
function gameTags(g){{const tags=[]; const ar=Number(teamRow(g.away_team).rank), hr=Number(teamRow(g.home_team).rank); if(Number.isFinite(ar)&&Number.isFinite(hr)){{if(ar<=10&&hr<=10) tags.push(['Top-10 matchup','good']); else if(ar<=25&&hr<=25) tags.push(['Top-25 matchup','good']);}} const m=Number(g.market_spread_home); if(Number.isFinite(m)){{const fav=m<0?g.home_team:m>0?g.away_team:'Pickem'; if(fav==='Pickem') tags.push(['Market PK','warn']); else if(fav===g.away_team) tags.push(['Road favorite','warn']);}} const se=spreadEdge(g), te=totalEdge(g), ie=injuryEdge(g), mv=moveText(g); if(Math.abs(Number(se.pts)||0)>=3) tags.push(['Spread value','good']); if(Math.abs(Number(te.pts)||0)>=3) tags.push(['Total value','good']); if(String(ie.main).toLowerCase().includes('no injury')) tags.push(['No injury edge','good']); if(!String(mv.main).toLowerCase().includes('flat')&&!String(mv.main).toLowerCase().includes('no opener')) tags.push([String(mv.main).replace(/^Toward +/,'Move: '),'warn']); [g.away_team,g.home_team].forEach(t=>{{situationalFlags(g,t).forEach(f=>tags.push([`${{t}}: ${{f.detail?f.label+' '+f.detail:f.label}}`,f.cls||'warn']));}}); const out=tags.slice(0,8); return `<div class="game-tags">${{out.length?out.map(([t,cls])=>`<span class="game-tag ${{cls}}">${{esc(t)}}</span>`).join(''):'<span class="game-tag">Standard spot</span>'}}</div>`;}}
function gameHero(g){{const ps=projectedScore(g); const proj=favoriteFromProjection(g); return `<div class="game-hero">
  <div class="kicker">Week ${{esc(g.week??g.cfbd_week??'—')}} · ${{fmtDate(g.date||g.cfbd_date)}}</div>
  <div class="match-title"><span class="bigline">${{teamRankLabel(g.away_team,'team-title-logo')}}</span><span class="vs">at</span><span class="bigline">${{teamRankLabel(g.home_team,'team-title-logo')}}</span></div><div class="center-records"><span class="record-pill">${{esc(g.away_team)}} ${{esc(teamSeasonRecord(g.away_team).overall)}} · ATS ${{esc(teamSeasonRecord(g.away_team).ats)}} · O/U ${{esc(teamSeasonRecord(g.away_team).ou)}}</span><span class="record-pill">${{esc(g.home_team)}} ${{esc(teamSeasonRecord(g.home_team).overall)}} · ATS ${{esc(teamSeasonRecord(g.home_team).ats)}} · O/U ${{esc(teamSeasonRecord(g.home_team).ou)}}</span></div>
  <div class="subline"><span>${{esc(g.cfbd_venue||'Venue TBD')}}</span><span>·</span><span>${{g.neutral_site?'Neutral site':'Home field'}}</span></div>
  <div class="game-proj-strip"><span class="game-proj-pill market">Market: ${{esc(g.market_spread_text||g.market_formatted_spread||'—')}}</span><span class="game-proj-pill">Projection: ${{esc(spreadText(proj.team, proj.spread))}}</span><span class="game-proj-pill total">Total: ${{num(g.market_total,1)}}</span></div><div class="score-banner ${{ps&&ps.conflict?'conflict':''}}">${{ps&&ps.conflict?esc(ps.note):`Projected score: ${{ps?`${{esc(g.away_team)}} ${{num(ps.away,1)}} · ${{esc(g.home_team)}} ${{num(ps.home,1)}}`:'—'}}`}}</div>
  ${{bettingEdgeSnapshot(g)}}
</div>`;}}
function scheduleTable(team, focusId){{const games=(DB.games||[]).filter(g=>g.away_team===team||g.home_team===team).sort((a,b)=>String(a.date).localeCompare(String(b.date))); return `<div class="card"><div class="card-title"><span>${{esc(team)}} Schedule / Results</span><span class="small">ATS/PGWE fields can populate in-season</span></div><div class="table-wrap"><table><thead><tr><th>Date</th><th>Opp / Rank</th><th>Market</th><th>Proj</th><th>Status</th></tr></thead><tbody>${{games.map(g=>{{const home=g.home_team===team; const opp=home?g.away_team:g.home_team; const proj=favoriteFromProjection(g); const isFocus=String(g.game_id)===String(focusId); return `<tr style="${{isFocus?'outline:2px solid rgba(96,165,250,.35);':''}}"><td>${{fmtDate(g.date)}}</td><td>${{home?'vs':'@'}} ${{teamLabel(opp)}} ${{rankChip(teamRow(opp).rank)}}</td><td>${{esc(g.market_spread_text||'—')}}</td><td>${{esc(spreadText(proj.team, proj.spread))}}</td><td>${{esc(g.cfbd_completed?'Final':'Scheduled')}}</td></tr>`;}}).join('')}}</tbody></table></div></div>`;}}
function predictive(g){{const trows=matchupRows(g); const fields=[['pass_off_edge','Pass Off'],['rush_off_edge','Rush Off'],['pass_protection_edge','Pass Pro'],['pass_rush_edge','Pass Rush'],['explosive_edge','Explosives'],['havoc_edge','Havoc']]; function side(team){{const r=trows.find(x=>x.team===team)||{{}}; return `<div class="summary-item"><b>${{esc(team)}} vs ${{esc(team===g.away_team?g.home_team:g.away_team)}}</b>${{fields.map(([k,l])=>`<div class="metric-row"><div class="metric-name">${{l}}</div><div>${{signed(r[k],1)}}</div><div class="bar"><span style="width:${{Math.max(5,Math.min(95,50+(Number(r[k])||0)*8))}}%"></span></div><div class="small">${{Number(r[k])>0?esc(team):Number(r[k])<0?esc(team===g.away_team?g.home_team:g.away_team):'Even'}}</div></div>`).join('')}}<div class="small">${{esc(r.summary||'No matchup edge row loaded yet.')}}</div></div>`;}} return `<div class="card"><div class="card-title"><span>Predictive matchup snapshot</span><span class="small">Offense vs opponent defense</span></div><div class="summary-list">${{side(g.away_team)}}${{side(g.home_team)}}</div></div>`;}}
function coachCard(g){{function row(team){{const c=coachRow(team), h1=coachHalf(team,'1H'), h2=coachHalf(team,'2H'); return `<tr><td><b>${{teamLabel(team)}}</b><div class="small">${{esc(c.head_coach||c.current_coach||'')}}</div></td><td>#${{esc(c.ats_rank||'—')}}<div class="small">${{esc(c.ats_record||'')}} · ATS ${{signed(c.avg_ats_margin,1)}}</div></td><td>#${{esc(h1.ats_rank||'—')}}<div class="small">${{esc(h1.ats_w||'—')}}-${{esc(h1.ats_l||'—')}} · ${{signed(h1.avg_ats,1)}}</div></td><td>#${{esc(h2.ats_rank||'—')}}<div class="small">${{esc(h2.ats_w||'—')}}-${{esc(h2.ats_l||'—')}} · ${{signed(h2.avg_ats,1)}}</div></td></tr>`;}} return `<div class="card"><div class="card-title"><span>Coaching / ATS profile</span><span class="small">Full game · 1H · 2H</span></div><div class="table-wrap"><table><thead><tr><th>Team</th><th>Game ATS</th><th>1H ATS</th><th>2H ATS</th></tr></thead><tbody>${{row(g.away_team)}}${{row(g.home_team)}}</tbody></table></div></div>`;}}
function injuriesCard(g){{const r=injuryRow(g.game_id); const a=Number(r.away_injury_score||0), h=Number(r.home_injury_score||0); return `<div class="card"><div class="card-title"><span>Injuries + schedule spot</span><span class="small">recency-weighted injuries · betting spot flags</span></div><div class="summary-list"><div class="summary-item"><b>${{teamLabel(g.away_team)}} INJ ${{num(a,1)}}</b><div class="small">${{a?esc(r.injury_summary||'Injury impact flagged'):'No current injury impact flagged'}}</div></div><div class="summary-item"><b>${{teamLabel(g.home_team)}} INJ ${{num(h,1)}}</b><div class="small">${{h?esc(r.injury_summary||'Injury impact flagged'):'No current injury impact flagged'}}</div></div></div><div class="spot-grid">${{spotCard(g,g.away_team)}}${{spotCard(g,g.home_team)}}</div></div>`;}}
function edgeTone(v){{v=Math.abs(Number(v)||0); if(v>=3) return 'green'; if(v>=1.5) return 'yellow'; return 'red';}}
function modelFairText(g){{const fair=favoriteFromProjection(g); return spreadText(fair.team,fair.spread);}}
function seasonAxisLabels(){{
  const weeks=(DB.games||[]).map(g=>Number(g.cfbd_week||g.week)).filter(Number.isFinite);
  const maxW=Math.max(16,...weeks);
  const labels=['Preseason'];
  for(let i=1;i<=maxW;i++) labels.push(`Wk ${{i}}`);
  return labels;
}}
function historyForGame(g){{
  const rows=(MATCHUP_HISTORY||[]).filter(r=>String(r.game_id)===String(g.game_id) || String(r.cfbd_game_id)===String(g.cfbd_game_id));
  if(rows.length) return rows;
  const modelSpreadHome=-Number(g.projected_margin_home);
  return [{{snapshot_label:'Preseason',market_spread_home:g.market_spread_open_home,market_total:g.market_total_open,model_spread_home:modelSpreadHome,projected_total:g.projected_total}},{{snapshot_label:'Current',market_spread_home:g.market_spread_home,market_total:g.market_total,model_spread_home:modelSpreadHome,projected_total:g.projected_total}}];
}}
function seasonHistoryChart(g, kind){{
  const axis=seasonAxisLabels();
  const rows=historyForGame(g);
  const labelIndex=Object.fromEntries(axis.map((x,i)=>[x,i]));
  const w=620,h=150,padL=42,padR=22,padT=28,padB=38;
  const xFor=i=>padL+(i/(axis.length-1))*(w-padL-padR);
  const marketKey=kind==='spread'?'market_spread_home':'market_total';
  const modelKey=kind==='spread'?'model_spread_home':'projected_total';
  const marketPts=[]; const modelPts=[];
  rows.forEach(r=>{{
    const lab=r.snapshot_label||'Preseason';
    const idx=labelIndex[lab] ?? (lab==='Current'?axis.length-1:null);
    if(idx==null) return;
    const mv=Number(r[marketKey]);
    const mod=Number(r[modelKey]);
    if(Number.isFinite(mv)) marketPts.push({{idx,value:mv,label:lab}});
    if(Number.isFinite(mod)) modelPts.push({{idx,value:mod,label:lab}});
  }});
  const vals=[...marketPts.map(p=>p.value),...modelPts.map(p=>p.value)].filter(Number.isFinite);
  if(vals.length<2) return '<div class="line-history"><div class="small">Season line history will populate as weekly snapshots are saved.</div></div>';
  let min=Math.min(...vals), max=Math.max(...vals);
  let span=(max-min)||1;
  const padVal=Math.max(span*.28, kind==='spread'?1.5:1.0);
  min-=padVal; max+=padVal; span=max-min;
  const yFor=v=>padT+(max-v)/span*(h-padT-padB);
  const path=pts=>pts.sort((a,b)=>a.idx-b.idx).map(p=>`${{xFor(p.idx)}},${{yFor(p.value)}}`).join(' ');
  const fmt=kind==='spread'?v=>signed(Number(v),1):v=>num(v,1);
  const tickEvery=axis.length>14?2:1;
  const yTicks=[min,(min+max)/2,max];
  return `<div class="line-history season"><svg viewBox="0 0 ${{w}} ${{h}}" preserveAspectRatio="none">${{yTicks.map(v=>`<line class="gridline" x1="${{padL}}" y1="${{yFor(v)}}" x2="${{w-padR}}" y2="${{yFor(v)}}"></line><text class="y-label" x="${{padL-8}}" y="${{yFor(v)+3}}" text-anchor="end">${{fmt(v)}}</text>`).join('')}}<line class="axis" x1="${{padL}}" y1="${{h-padB}}" x2="${{w-padR}}" y2="${{h-padB}}"></line>${{axis.map((lab,i)=>i%tickEvery===0?`<line class="axis" x1="${{xFor(i)}}" y1="${{h-padB}}" x2="${{xFor(i)}}" y2="${{h-padB+4}}"></line>`:'').join('')}}${{marketPts.length>=2?`<polyline class="line" points="${{path(marketPts)}}"></polyline>`:''}}${{modelPts.length>=2?`<polyline class="model-line" points="${{path(modelPts)}}"></polyline>`:''}}${{marketPts.map(p=>`<circle class="dot" cx="${{xFor(p.idx)}}" cy="${{yFor(p.value)}}" r="3.5"><title>Market ${{p.label}}: ${{fmt(p.value)}}</title></circle>`).join('')}}${{modelPts.map(p=>`<circle class="model-dot" cx="${{xFor(p.idx)}}" cy="${{yFor(p.value)}}" r="3.5"><title>Model ${{p.label}}: ${{fmt(p.value)}}</title></circle>`).join('')}}${{marketPts.map(p=>`<text class="point-label" x="${{xFor(p.idx)}}" y="${{Math.max(14,yFor(p.value)-10)}}" text-anchor="middle">${{fmt(p.value)}}</text>`).join('')}}${{modelPts.map(p=>`<text class="point-label model" x="${{xFor(p.idx)}}" y="${{Math.min(h-padB-8,yFor(p.value)+18)}}" text-anchor="middle">${{fmt(p.value)}}</text>`).join('')}}</svg><div class="line-history-labels">${{axis.map((lab,i)=>i%tickEvery===0?`<span>${{i===0?'Pre':lab.replace('Wk ','W')}}</span>`:'').join('')}}</div><div class="small" style="margin-top:4px">Blue = market · green dashed = model · spread shown from home-team perspective</div></div>`;
}}

function weatherForGame(g){{
  const gid=String(g.game_id||''); const cfbd=String(g.cfbd_game_id||'');
  return (GAME_WEATHER||[]).find(w=>String(w.game_id||'')===gid || (cfbd && String(w.cfbd_game_id||'')===cfbd));
}}
function wxNum(x,d=0){{const n=Number(x); return Number.isFinite(n)?n.toFixed(d):'—';}}
function wxTone(score){{score=Number(score)||0; if(score>=4)return 'bad'; if(score>=2)return 'warn'; if(score>=1)return 'warn'; return 'good';}}
function weatherCard(g){{
  const w=weatherForGame(g);
  if(!w){{return `<div class="card weather-card"><div class="card-title"><span>Weather</span><span class="small">wind · precipitation · kickoff conditions</span></div><div class="summary-item"><b>No weather row yet</b><div class="muted">Run the weather pull after venue locations are seeded.</div></div></div>`;}}
  const status=String(w.status||'');
  const flags=String(w.weather_flags||'').split(';').filter(Boolean);
  const score=Number(w.weather_edge_score)||0;
  const statusText = status==='forecast' ? 'Forecast available' : (status==='not_in_forecast_window' ? 'Not in forecast window yet' : status.replaceAll('_',' '));
  const cells = [
    ['Kickoff local', w.start_time_local ? fmtDateTime(w.start_time_local) : '—'],
    ['Temp', wxNum(w.temperature_f,0)+'°F'],
    ['Wind', wxNum(w.wind_speed_mph,0)+' mph'],
    ['Gust', wxNum(w.wind_gust_mph,0)+' mph'],
    ['Precip', wxNum(w.precip_probability_pct,0)+'%'],
    ['Score', score]
  ].map(([k,v])=>`<div class="weather-cell"><b>${{esc(k)}}</b><div class="weather-val">${{esc(v)}}</div></div>`).join('');
  const flagHtml = flags.length ? flags.map(f=>`<span class="weather-flag ${{wxTone(score)}}">${{esc(f)}}</span>`).join('') : `<span class="weather-flag good">No weather edge yet</span>`;
  return `<div class="card weather-card"><div class="card-title"><span>Weather</span><span class="small">wind · precipitation · kickoff conditions</span></div><div class="summary-item"><b>${{esc(statusText)}}</b><div class="muted">${{esc(w.venue||g.venue||'')}} · source: ${{esc(w.source||'Open-Meteo')}}${{w.reason?` · ${{esc(w.reason)}}`:''}}</div></div><div class="weather-grid">${{cells}}</div><div class="weather-flags">${{flagHtml}}</div></div>`;
}}

function marketCard(g){{const se=spreadEdge(g), te=totalEdge(g), mv=moveText(g); const projHomeSpread=-Number(g.projected_margin_home); const spreadEdgePts=Number(se.pts)||0; const totalEdgePts=Number(te.pts)||0; return `<div class="card"><div class="card-title"><span>Market betting data</span><span class="small">spread · total · best books · season history</span></div><div class="market-compact"><div class="market-primary"><div class="market-primary-grid"><div><b>Spread</b><div class="market-big">${{esc(g.market_spread_text||g.market_formatted_spread||'—')}} ${{g.market_spread_price?esc(String(g.market_spread_price)):''}} ${{sportsbookLogo(g.market_spread_book||g.market_line_source)}}</div><div class="open-line">Open: ${{Number.isFinite(Number(g.market_spread_open_home))?esc(spreadText(g.home_team, Number(g.market_spread_open_home))):'—'}}</div><div class="market-sub">${{esc(String(mv.main).replace(/^Toward +/,'Move: '))}} — ${{esc(mv.note)}}</div></div><div class="model-box"><b>Model prediction</b><div>Fair spread: <strong>${{esc(modelFairText(g))}}</strong></div><div class="edge-diff ${{edgeTone(spreadEdgePts)}}">Edge: ${{esc(se.team)}} ${{se.team==='No edge'?'':signed(spreadEdgePts,1)}}</div></div></div>${{seasonHistoryChart(g,'spread')}}</div><div class="market-primary"><div class="market-primary-grid"><div><b>Total</b><div class="market-big">${{num(g.market_total,1)}} · O ${{g.market_total_over_price?esc(String(g.market_total_over_price)):'—'}} / U ${{g.market_total_under_price?esc(String(g.market_total_under_price)):'—'}} ${{sportsbookLogo(g.market_total_book)}}</div><div class="open-line">Open total: ${{Number.isFinite(Number(g.market_total_open))?num(g.market_total_open,1):'—'}}</div><div class="market-sub">Current total vs opener and projection</div></div><div class="model-box"><b>Model prediction</b><div>Projected total: <strong>${{num(g.projected_total,1)}}</strong></div><div class="edge-diff ${{edgeTone(totalEdgePts)}}">Edge: ${{esc(te.side)}} ${{te.side==='No edge'||te.side==='No total'?'':signed(totalEdgePts,1)}}</div></div></div>${{seasonHistoryChart(g,'total')}}</div></div><div class="market-best-grid"><div class="market-best"><b>Best home</b><div>${{esc(g.market_best_home_spread_text||'—')}} ${{g.market_best_home_spread_price?esc(String(g.market_best_home_spread_price)):''}}</div><div>${{sportsbookLogo(g.market_best_home_spread_book)}}</div></div><div class="market-best"><b>Best away</b><div>${{esc(g.market_best_away_spread_text||'—')}} ${{g.market_best_away_spread_price?esc(String(g.market_best_away_spread_price)):''}}</div><div>${{sportsbookLogo(g.market_best_away_spread_book)}}</div></div><div class="market-best"><b>Best over</b><div>${{num(g.market_best_over_total,1)}} ${{g.market_best_over_price?esc(String(g.market_best_over_price)):'—'}}</div><div>${{sportsbookLogo(g.market_best_over_book)}}</div></div><div class="market-best"><b>Best under</b><div>${{num(g.market_best_under_total,1)}} ${{g.market_best_under_price?esc(String(g.market_best_under_price)):'—'}}</div><div>${{sportsbookLogo(g.market_best_under_book)}}</div></div></div><div class="summary-item" style="margin-top:10px"><b>Market freshness</b><div>Updated: ${{fmtDateTime(g.market_spread_last_update||g.market_total_last_update||g.market_pulled_at)}}</div><div class="market-fresh"><span class="pill">Books</span>${{bookStrip(g.market_books_available)}}<span class="pill">Source: ${{esc(g.market_line_source||'—')}}</span>${{g.market_spread_hold_pct?`<span class="pill">Hold ${{num(g.market_spread_hold_pct,1)}}%</span>`:''}}</div></div></div>`;}}
function positionCard(g){{function row(team){{const r=tcRow(team); const keys=['qb','rb','wr','te','ol','dl','lb','db','kp']; return `<tr><td><b>${{teamLabel(team)}}</b></td>${{keys.map(k=>`<td>${{num(r[k],1)}}</td>`).join('')}}</tr>`;}} return `<details><summary>More detail: position-group ratings</summary><div class="table-wrap" style="margin-top:10px"><table><thead><tr><th>Team</th><th>QB</th><th>RB</th><th>WR</th><th>TE</th><th>OL</th><th>DL</th><th>LB</th><th>DB</th><th>K/P</th></tr></thead><tbody>${{row(g.away_team)}}${{row(g.home_team)}}</tbody></table></div></details>`;}}
function bettingRead(g){{const se=spreadEdge(g), te=totalEdge(g), ie=injuryEdge(g), ce=coachEdge(g); const spreadPhrase=se.team==='No edge'?'No clear spread edge':`${{se.team}} lean`; const totalPhrase=te.side==='No edge'?'No clear total edge':`${{te.side}} lean`; return `<div class="card"><div class="card-title"><span>Betting read summary</span><span class="small">awareness, not auto-bet</span></div><div class="read-box"><p><b>Spread:</b> ${{esc(spreadPhrase)}}. ${{esc(se.note)}}.</p><p><b>Total:</b> ${{esc(totalPhrase)}}. ${{esc(te.note)}}.</p><p><b>Context:</b> Injury read is ${{esc(ie.main.toLowerCase())}}; coach read is ${{esc(ce.team)}}. Confirm late injuries, line movement, and any depth-chart news before kickoff.</p></div></div>`;}}
function render(){{const g=findGame(); if(!g){{$('#app').innerHTML='<div class="card">No game found.</div>';return;}} document.title=`${{g.away_team}} at ${{g.home_team}} · Matchup Card`; $('#app').innerHTML=`<div class="hero">${{teamHero(g.away_team,'Away')}}${{gameHero(g)}}${{teamHero(g.home_team,'Home')}}</div>${{dashboard(g)}}${{gameTags(g)}}${{bettingRead(g)}}${{weatherCard(g)}}${{marketCard(g)}}<div class="grid2">${{scheduleTable(g.away_team,g.game_id)}}${{scheduleTable(g.home_team,g.game_id)}}</div>${{injuriesCard(g)}}${{coachCard(g)}}${{positionCard(g)}}`;}}
render();
</script>
</body>
</html>
'''
Path('matchup.html').write_text(html)
# patch index matchupButton
patched=s
old="""function matchupButton(g){\n  const gid = matchupGameId(g);\n  const safeId = String(gid).replace(/'/g, "\\'");\n  return `<button class=\"matchup-toggle\" type=\"button\" onclick=\"toggleMatchupRow('${safeId}'); event.stopPropagation();\">Matchup</button><div class=\"small\">${matchupCompactLabel(g)}</div>`;\n}\n"""
new="""function matchupButton(g){\n  const gid = g.game_id || matchupGameId(g);\n  const safeId = encodeURIComponent(String(gid));\n  return `<a class=\"matchup-toggle\" style=\"text-decoration:none\" href=\"matchup.html?game_id=${safeId}\" onclick=\"event.stopPropagation();\">Matchup</a><div class=\"small\">${matchupCompactLabel(g)}</div>`;\n}\n"""
if new in patched:
    src.write_text(patched)
    print('wrote matchup.html; index.html matchup buttons already patched')
elif old in patched:
    patched = patched.replace(old, new)
    src.write_text(patched)
    print('wrote matchup.html and patched index.html matchup buttons')
else:
    import re
    pattern = r"function matchupButton\(g\)\s*\{.*?\n\}"
    patched2, n = re.subn(pattern, new, patched, count=1, flags=re.S)
    if n:
        src.write_text(patched2)
        print('wrote matchup.html and patched index.html matchup buttons by regex')
    else:
        src.write_text(patched)
        print('wrote matchup.html; WARNING: matchupButton block not found in index.html')
