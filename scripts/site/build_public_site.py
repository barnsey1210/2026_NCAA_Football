#!/usr/bin/env python3
"""Assemble approved pages while retaining the monolith for team detail routes."""
from pathlib import Path
import re, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build/public_site"
PAGES = {"openers_v2.html":"openers.html",
         "matchups.html":"matchups.html", "matchup.html":"matchup.html", "futures_v2.html":"futures.html",
         "betting_v2.html":"betting.html",
         "team_v2.html":"team.html", "ratings_v2.html":"ratings.html",
         "simulations_v2.html":"simulations.html", "playoff_v2.html":"playoff.html",
         "schedule_v2.html":"schedule.html", "odds_v2.html":"odds.html"}
LINKS = [('Home','index.html'), ('Ratings','ratings.html'), ('Openers','openers.html'), ('Matchups','matchups.html'),
         ('ODDS','odds.html'), ('Schedule','schedule.html'), ('Futures','futures.html'), ('Conferences','conferences.html'), ('Playoff','playoff.html'),
         ('Simulations','simulations.html'), ('Betting','betting.html')]
CSS = """<style id="production-nav-css">
.top .brand a,.top .nav a{color:inherit;text-decoration:none}.top .nav a{color:var(--muted);padding:8px 11px;font-weight:800;white-space:nowrap;border-radius:9px}.top .nav a.active{background:#173b72;color:#fff}.top .model{margin-left:auto}
</style>"""
PAGE_HEALTH_ASSETS = ('page_health.css', 'page_health.js')

def nav(target):
    links=''.join(f'<a href="{href}"'+(' class="active"' if href==target else '')+f'>{label}</a>' for label,href in LINKS)
    return f'<div class="brand"><a href="index.html">NCAAF</a></div><div class="nav">{links}</div>'

def transform(text,target):
    for old,new in {'openers_v2.html':'openers.html','matchups_v2.html':'matchups.html',
                    'futures_v2.html':'futures.html',
                    'conferences_v2.html':'conferences.html','betting_v2.html':'betting.html',
                    'schedule_v2.html':'schedule.html',
                    'index.html#team/':'team.html?team='}.items(): text=text.replace(old,new)
    text=text.replace('openers.html?game_id=', 'openers.html?game_id=')
    text=re.sub(r'<div class="brand">NCAAF</div><(?:div|nav) class="nav">.*?</(?:div|nav)>',nav(target),text,count=1,flags=re.S)
    text=re.sub(r'<div class="brand">NCAAF Edge</div><nav class="nav">.*?</nav>',nav(target),text,count=1,flags=re.S)
    text=text.replace('</head>',CSS+'</head>')
    text=text.replace('</head>','<link rel="stylesheet" href="page_health.css"><script defer src="page_health.js"></script></head>')
    text=text.replace('</head>','<style id="team-link-css">.teamLink,.team,.match a,.opp{color:inherit!important;text-decoration:none!important}</style></head>')
    if target == 'index.html':
        text=text.replace('changes.innerHTML=movements().slice(0,7)', "changes.innerHTML=movements().filter(m=>week.value==='all'||String(m.y.week)===week.value).slice(0,7)")
        text=text.replace('<section class="summary">','<div class="dashboardWeekChips" id="dashboardWeekChips"></div><section class="summary">',1)
        text=text.replace('</head>','<style id="dashboard-week-css">.hero select{display:none}.dashboardWeekChips{display:flex;gap:5px;flex-wrap:wrap;margin:8px 0}.dashboardWeekChips button{border:1px solid var(--line);background:#091a34;color:var(--muted);border-radius:999px;padding:6px 10px;font-weight:900}.dashboardWeekChips button.active{background:#1857a7;color:#fff}</style></head>')
        dash_script="""<script id="dashboard-week-js">const dashboardWeek=document.getElementById('week'),dashboardWeekChips=document.getElementById('dashboardWeekChips');function syncDashboardWeeks(){dashboardWeekChips.innerHTML=[...dashboardWeek.options].map(o=>`<button class="${o.value===dashboardWeek.value?'active':''}" data-week="${o.value}">${o.textContent}</button>`).join('');dashboardWeekChips.querySelectorAll('button').forEach(b=>b.onclick=()=>{dashboardWeek.value=b.dataset.week;dashboardWeek.dispatchEvent(new Event('input',{bubbles:true}));syncDashboardWeeks()})}new MutationObserver(syncDashboardWeeks).observe(dashboardWeek,{childList:true});dashboardWeek.addEventListener('input',syncDashboardWeeks);</script>"""
        text=text.replace('</body>',dash_script+'</body>')
    if target == 'openers.html':
        text=text.replace('<div class="filters">','<div class="weekChips" id="openerWeekChips"></div><div class="filters">',1)
        text=text.replace('</head>','<style id="opener-week-css">#week{display:none}.weekChips{display:flex;gap:5px;flex-wrap:wrap;margin:8px 0}.weekChips button{border:1px solid var(--line);background:#091a34;color:var(--muted);border-radius:999px;padding:6px 10px;font-weight:900;cursor:pointer}.weekChips button.active{background:#1857a7;color:#fff}</style></head>')
        panel = '<details class="freshness" id="postgameShadow"><summary>Saturday shadow: loading…</summary><div class="freshnessBody"></div></details>'
        text=text.replace('<div class="mode" id="modes">',panel+'<div class="mode" id="modes">',1)
        script="""<script id="postgame-shadow-ui">
fetch('data/site/postgame_shadow_updates.json').then(r=>r.json()).then(d=>{const box=document.getElementById('postgameShadow');if(!box)return;const n=d.summary?.completed_team_updates||0;box.querySelector('summary').textContent=`Saturday shadow · ${d.status.replaceAll('_',' ')} · ${n} team estimates · not applied`;box.querySelector('.freshnessBody').innerHTML=`<div class="freshnessSource"><b>Spread</b><br>${d.spread_model.status}<br><span class="muted">Score/ATS model; PBP excluded after holdout</span></div><div class="freshnessSource"><b>Total</b><br>${d.total_model.status.replaceAll('_',' ')}<br><span class="muted">Requires current-season PBP</span></div><div class="freshnessSource"><b>Safety</b><br>Shadow only<br><span class="muted">Official ratings and projections unchanged</span></div>`}).catch(()=>{});
</script>"""
        week_script="""<script id="opener-week-js">const openerWeek=document.getElementById('week'),openerWeekChips=document.getElementById('openerWeekChips');function syncOpenerWeeks(){const opts=[...openerWeek.options].filter(o=>o.value!=='all');if(!opts.length)return;openerWeekChips.innerHTML=opts.map(o=>`<button class="${o.value===openerWeek.value?'active':''}" data-week="${o.value}">${o.textContent}</button>`).join('');openerWeekChips.querySelectorAll('button').forEach(b=>b.onclick=()=>{openerWeek.value=b.dataset.week;openerWeek.dispatchEvent(new Event('input',{bubbles:true}));syncOpenerWeeks()})}new MutationObserver(syncOpenerWeeks).observe(openerWeek,{childList:true});openerWeek.addEventListener('input',syncOpenerWeeks);</script>"""
        text=text.replace('</body>',script+week_script+'</body>')
    if target == 'matchups.html':
        text=text.replace('</head>','<style id="matchups-hide-page-health">#page-health-summary{display:none!important}</style></head>')
        text=text.replace('</head>','<style id="single-line-matchups">.shell{max-width:none;padding-left:10px;padding-right:10px}.tableWrap{overflow-x:hidden;max-height:calc(100vh - 260px)}.tableWrap table{min-width:0;width:100%;table-layout:fixed;font-size:12px}.tableWrap th{position:sticky;top:0;z-index:4}.tableWrap th,.tableWrap td{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding:6px}.tableWrap td{height:50px}.tableWrap th:nth-child(1){width:8%}.tableWrap th:nth-child(2){width:30%}.tableWrap th:nth-child(3){width:13%}.tableWrap th:nth-child(4){width:18%}.tableWrap th:nth-child(5){width:8%}.tableWrap th:nth-child(6){width:14%}.tableWrap th:nth-child(7){width:6%}.tableWrap th:nth-child(8){width:3%}.tableWrap .teamLine{min-width:0}.tableWrap .team img{width:21px;height:21px}.tableWrap .book{width:27px;height:22px}.tableWrap .edge{display:inline-flex;align-items:center;gap:4px;white-space:nowrap;font-size:13px}.tableWrap .angle{white-space:nowrap}.tableWrap .open{padding:4px 6px}</style></head>')
    if target == 'futures.html':
        text=text.replace(
            '<td><span class="team">${logo(x)}<span>${e(x.team)}<span class="sub">#${x.rank} · ${e(x.conference)}</span></span></span></td>',
            '<td><a class="team" href="team.html?team=${e(x.slug)}">${logo(x)}<span>${e(x.team)}<span class="sub">#${x.rank} · ${e(x.conference)}</span></span></a></td>')
        text=text.replace('</head>','<style>.team{text-decoration:none;color:inherit}</style></head>')
    if target == 'ratings.html':
        text=text.replace('teams=[...m.values()];conf.innerHTML', 'teams=[...m.values()].filter(t=>t.rating!=null&&t.overall_rank!=null);conf.innerHTML')
    if target == 'odds.html':
        text=text.replace('<title>Odds Screen — Isolated V2 Prototype</title>', '<title>NCAAF Odds</title>')
    if target == 'team.html':
        pass
    if target == 'conferences.html':
        text=text.replace('<span>${e(x.team)}<span class="sub">#${x.rank} rating · #${x.projected_finish} projected</span></span>', '<span>${e(x.team)}</span>')
        text=text.replace('<tr><th>Proj finish</th><th>Team</th><th>Current overall</th><th>Current conf</th><th>Projected overall</th><th>Projected conf</th><th>Overall SOS</th><th>Remaining SOS</th><th>Title game</th><th>Win title</th><th>Wagers</th></tr>', '<tr><th>Proj finish</th><th>Team</th><th>Rating</th><th>Current overall</th><th>Current conf</th><th>Projected overall</th><th>Projected conf</th><th>Conf SOS</th><th>Remaining SOS</th><th>Make Title</th><th>Win title</th><th>Wagers</th></tr>')
        text=text.replace('<tr><td>#${x.projected_finish}</td><td>${team(x)}</td><td>${x.current_wins}-${x.current_losses}</td><td>${x.current_conf_wins}-${x.current_conf_losses}</td><td>${n(x.projected_wins,1)}</td><td>${n(x.projected_conf_wins,1)}</td><td>${n(x.overall_sos,1)}</td><td>${n(x.remaining_sos,1)}</td><td>${pct(x.make_title_game_pct)}</td><td>${pct(x.title_pct)}</td><td>${x.open_wagers.length?`<span class="bet">BET ${x.open_wagers.length}</span>`:\'—\'}</td></tr>', '<tr><td>#${x.projected_finish}</td><td>${team(x)}</td><td class="rankTone" data-rank="${x.rank}">${n(x.rating,1)} · #${x.rank}</td><td>${x.current_wins}-${x.current_losses}</td><td>${x.current_conf_wins}-${x.current_conf_losses}</td><td>${n(x.projected_wins,1)}-${n(x.projected_losses,1)}</td><td>${n(x.projected_conf_wins,1)}-${n(x.projected_conf_losses,1)}</td><td class="rankTone" data-rank="${x.conf_sos_rank}">${n(x.conf_sos,1)} · #${x.conf_sos_rank}</td><td class="rankTone" data-rank="${x.remaining_sos_rank}">${n(x.remaining_sos,1)} · #${x.remaining_sos_rank}</td><td>${pct(x.make_title_game_pct)}</td><td>${pct(x.title_pct)}</td><td>${x.open_wagers.length?x.open_wagers.map(w=>`<span class="bet">${e(w.selection)} ${od(w.price)}</span>`).join(\'<br>\'):\'—\'}</td></tr>')
        text=text.replace("conference.innerHTML=D.conferences.map(x=>`<option>${e(x.conference)}</option>`).join('');render()", "conference.innerHTML=D.conferences.map(x=>`<option>${e(x.conference)}</option>`).join('');const requestedConference=new URLSearchParams(location.search).get('conference');if(requestedConference&&D.conferences.some(x=>x.conference===requestedConference))conference.value=requestedConference;render()")
        text=text.replace('<div class="summary">','<div class="conferenceChips" id="conferenceChips"></div><div class="summary">',1)
        text=text.replace('</head>','<style id="conference-chip-css">.conferenceChips{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 12px}.conferenceChips button{border:1px solid var(--l);background:#091a34;color:var(--m);border-radius:999px;padding:7px 12px;font-weight:900;cursor:pointer}.conferenceChips button.active{background:#1857a7;border-color:#55a2ff;color:#fff}#head th{cursor:pointer}#head th:hover{color:#fff}.rankTone[data-rank]{font-weight:900}.rankTone[data-rank^="1"],.rankTone[data-rank^="2"],.rankTone[data-rank^="3"]{color:var(--g)}.bet{display:inline-block;margin:1px 0}</style></head>')
        script="""<script id="conference-chip-js">const conferenceSelect=document.getElementById('conference'),chipBox=document.getElementById('conferenceChips');function syncConferenceChips(){if(!chipBox||!conferenceSelect)return;chipBox.innerHTML=[...conferenceSelect.options].map(o=>`<button class="${o.value===conferenceSelect.value?'active':''}" data-conf="${o.value}">${o.textContent}</button>`).join('');chipBox.querySelectorAll('button').forEach(b=>b.onclick=()=>{conferenceSelect.value=b.dataset.conf;conferenceSelect.dispatchEvent(new Event('input',{bubbles:true}));syncConferenceChips()})}const chipObserver=new MutationObserver(syncConferenceChips);chipObserver.observe(conferenceSelect,{childList:true});conferenceSelect.addEventListener('input',syncConferenceChips);</script>"""
        text=text.replace('</body>',script+'</body>')
        sort_script="""<script id="conference-sort-js">let conferenceSort={index:-1,dir:1};function toneConferenceRanks(){document.querySelectorAll('.rankTone').forEach(x=>{const r=Number(x.dataset.rank);x.style.color=r<=35?'var(--g)':r<=75?'#ffc45b':'var(--r)'})}new MutationObserver(toneConferenceRanks).observe(document.getElementById('rows'),{childList:true,subtree:true});document.getElementById('head').addEventListener('click',ev=>{const th=ev.target.closest('th');if(!th)return;const cells=[...th.parentElement.children],index=cells.indexOf(th);conferenceSort.dir=conferenceSort.index===index?-conferenceSort.dir:1;conferenceSort.index=index;const body=document.getElementById('rows'),list=[...body.rows];list.sort((a,b)=>{const av=a.cells[index]?.innerText.trim()||'',bv=b.cells[index]?.innerText.trim()||'',an=parseFloat(av.replace(/[^0-9.+-]/g,'')),bn=parseFloat(bv.replace(/[^0-9.+-]/g,''));return (Number.isFinite(an)&&Number.isFinite(bn)?an-bn:av.localeCompare(bv))*conferenceSort.dir});list.forEach(row=>body.appendChild(row));cells.forEach(x=>x.removeAttribute('aria-sort'));th.setAttribute('aria-sort',conferenceSort.dir>0?'ascending':'descending')});</script>"""
        text=text.replace('</body>',sort_script+'</body>')
        text=text.replace('</head>','<style id="conference-logo-css">.conferenceBadge{min-width:54px;height:54px}.conferenceBadge img{width:42px;height:42px;object-fit:contain}</style></head>')
        logo_script="""<script id="conference-logo-js">const conferenceLogoObserver=new MutationObserver(()=>{const c=typeof cur==='function'?cur():null,b=document.querySelector('.conferenceBadge');if(c&&b&&!b.querySelector('img'))b.innerHTML=`<img src="logos/conferences/${c.slug}.png" alt="${c.conference} logo">`});conferenceLogoObserver.observe(document.getElementById('conferenceIdentity'),{childList:true,subtree:true});</script>"""
        text=text.replace('</body>',logo_script+'</body>')
    return text

def main():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    subprocess.run([sys.executable, str(ROOT/'scripts/model_tracking/build_model_performance_view.py')], check=True)
    subprocess.run([sys.executable, str(ROOT/'scripts/site/build_page_health_status.py')], check=True)
    for source,target in PAGES.items():
        source_path=ROOT/source
        if not source_path.exists():
            # The authoritative repository tracks the canonical public names;
            # the runtime retains *_v2 source names for compatibility.
            source_path=ROOT/source
        (OUT/target).write_text(transform(source_path.read_text(),target))
    for asset in PAGE_HEALTH_ASSETS:
        shutil.copy2(ROOT/asset, OUT/asset)
    # The approved Conference Logo Schedule is generated from current conference
    # workspace and matchup artifacts after shared page-health assets exist.
    subprocess.run([sys.executable, str(ROOT/'scripts/site/build_conference_logo_schedule.py')], check=True)
    # Keep the canonical Odds publication artifact aligned with odds_v2.html;
    # daily_market_update.sh publishes this root copy when it is present.
    shutil.copy2(OUT/'odds.html', ROOT/'odds.html')

    shutil.copy2(ROOT/'playoff_futures_tab.js',OUT/'playoff_futures_tab.js')
    shutil.copy2(ROOT/'dashboard_playoff_edges.js',OUT/'dashboard_playoff_edges.js')
    shutil.copy2(ROOT/'coach_cards.js',OUT/'coach_cards.js')
    shutil.copy2(ROOT/'team_coach_card.js',OUT/'team_coach_card.js')
    shutil.copy2(ROOT/'matchup_workspace.js',OUT/'matchup_workspace.js')
    # Local preview assets. Publishing copies these directories independently.
    for name in ('data','logos','helmets'):
        target=ROOT/name
        if target.exists(): (OUT/name).symlink_to(target, target_is_directory=True)
    print(f'Built {len(PAGES)} non-home pages in {OUT}')

if __name__=='__main__': main()

# OPENERS_V2_PUBLIC_SYNC_START
# Keep the published Openers page and shared matchup workspace aligned with
# their canonical V2 source files after the normal public-site build finishes.
import atexit as _openers_sync_atexit
import shutil as _openers_sync_shutil
from pathlib import Path as _OpenersSyncPath

def _sync_openers_v2_public_artifacts():
    _project_root = ROOT
    _public_root = _project_root / "build" / "public_site"
    _pairs = (
        ((_project_root / "openers_v2.html") if (_project_root / "openers_v2.html").exists() else (_project_root / "openers.html"), _public_root / "openers.html"),
        (_project_root / "matchup_workspace.js", _public_root / "matchup_workspace.js"),
    )
    _public_root.mkdir(parents=True, exist_ok=True)
    for _source, _target in _pairs:
        if not _source.exists():
            raise RuntimeError(f"Required public artifact source is missing: {_source}")
        if _target.name == "openers.html":
            _target.write_text(transform(_source.read_text(), "openers.html"))
        else:
            _openers_sync_shutil.copy2(_source, _target)
        print(f"synced public artifact: {_source.name} -> {_target}")
    # The canonical Openers and Schedule builders run after the shared page
    # transform. Reapply only the production ODDS nav item they would otherwise
    # replace, leaving all other page markup untouched.
    for _name in ("openers.html", "schedule.html"):
        _page = _public_root / _name
        if not _page.exists():
            continue
        _text = _page.read_text()
        if 'href="odds.html"' not in _text:
            _text = _text.replace(
                '<a href="schedule.html">Schedule</a>',
                '<a href="odds.html">ODDS</a><a href="schedule.html">Schedule</a>',
                1,
            )
        if 'href="odds.html"' not in _text:
            _text = _text.replace(
                '<a href="futures.html">Futures</a>',
                '<a href="odds.html">ODDS</a><a href="futures.html">Futures</a>',
                1,
            )
        if 'href="page_health.css"' not in _text:
            _text = _text.replace(
                '</head>',
                '<link rel="stylesheet" href="page_health.css">'
                '<script defer src="page_health.js"></script></head>',
                1,
            )
        _page.write_text(_text)

_openers_sync_atexit.register(_sync_openers_v2_public_artifacts)
# OPENERS_V2_PUBLIC_SYNC_END

# SCHEDULE_PERSISTENT_PUBLIC_SYNC_START
import atexit as _schedule_persist_atexit
import subprocess as _schedule_persist_subprocess
import sys as _schedule_persist_sys
from pathlib import Path as _SchedulePersistPath

def _sync_schedule_persistent_public_artifacts():
    _root = ROOT
    _script = _root / "scripts/site/build_schedule_persistent.py"
    if not _script.exists():
        print(f"schedule persistent builder unavailable; retaining assembled page: {_script}")
        return
    _schedule_persist_subprocess.run(
        [_schedule_persist_sys.executable, str(_script)],
        check=True,
    )

_schedule_persist_atexit.register(_sync_schedule_persistent_public_artifacts)
# SCHEDULE_PERSISTENT_PUBLIC_SYNC_END
