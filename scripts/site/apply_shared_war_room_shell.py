#!/usr/bin/env python3
"""Apply the canonical War Room shell to every public production page."""
from __future__ import annotations
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/public_site'
LINKS=[
 ('Home','index.html'),('Ratings','ratings.html'),('Matchups','matchups.html'),('Openers','openers.html'),
 ('Command Center','war-room.html'),('Odds','odds.html'),('Schedule','schedule.html'),
 ('Futures','futures.html'),('Conferences','conferences.html'),('Coaches','coaches.html'),
 ('Playoff','playoff.html'),('Sim Lab','sim_lab.html'),('Betting','betting.html'),
]
# Command Center remains a standalone page while sharing the canonical public shell.
ACTIVE_ALIASES={'simulations.html':'sim_lab.html'}
CANONICAL={href for _,href in LINKS}|set(ACTIVE_ALIASES)|{'team.html','matchup.html'}
STYLE="""<style id="shared-war-room-shell-v2">
:root{--wr-blue:#3caaff;--wr-gold:#ffc83d;--wr-green:#32e89f;--wr-line:#214a70}
.war-room-global{width:100%!important;max-width:none!important;min-height:82px!important;display:grid!important;grid-template-columns:280px minmax(0,1fr) max-content!important;gap:14px!important;align-items:center!important;padding:0 22px!important;margin:0!important;background:#020914!important;border-bottom:1px solid #17395d!important}
.war-room-global .war-room-brand{min-width:0!important}.war-room-global .war-room-brand a{display:block!important;color:#fff!important;text-decoration:none!important}.war-room-global .war-room-brand strong{display:block!important;font:900 42px/.88 Impact,Haettenschweiler,"Arial Narrow Bold",sans-serif!important;letter-spacing:.025em!important}.war-room-global .war-room-brand strong span{color:var(--wr-blue)!important;margin-left:4px!important}.war-room-global .war-room-brand small{display:block!important;margin-top:9px!important;color:var(--wr-gold)!important;font-size:9px!important;font-weight:1000!important;letter-spacing:.16em!important;white-space:nowrap!important}
.war-room-global .war-room-nav{display:flex!important;align-items:stretch!important;gap:0!important;min-width:0!important;overflow-x:auto!important;overflow-y:hidden!important;height:82px!important;scrollbar-width:none!important}.war-room-global .war-room-nav::-webkit-scrollbar{display:none!important}.war-room-global .war-room-nav a{display:flex!important;align-items:center!important;padding:0 10px!important;color:#becada!important;font-size:14px!important;font-weight:900!important;white-space:nowrap!important;text-decoration:none!important;position:relative!important}.war-room-global .war-room-nav a.active{color:var(--wr-gold)!important}.war-room-global .war-room-nav a.active:after{content:"";position:absolute;left:9px;right:9px;bottom:0;height:4px;background:var(--wr-gold);border-radius:4px}
.war-room-global .war-room-meta{display:flex!important;align-items:center!important;justify-content:flex-end!important;gap:9px!important;min-width:max-content!important}.war-room-global .war-room-context{color:#8fa7c5!important;font-size:10px!important;font-weight:900!important;letter-spacing:.08em!important;text-transform:uppercase!important}.war-room-global .war-room-health{margin:0!important;white-space:nowrap!important}
@media(max-width:1550px){.war-room-global{grid-template-columns:235px minmax(0,1fr) max-content!important;padding:0 14px!important}.war-room-global .war-room-brand strong{font-size:34px!important}.war-room-global .war-room-nav a{font-size:12px!important;padding:0 7px!important}.war-room-global .war-room-context{display:none!important}}
@media(max-width:1050px){.war-room-global{grid-template-columns:205px minmax(0,1fr)!important}.war-room-global .war-room-meta{display:none!important}}
@media(max-width:700px){.war-room-global{min-height:70px!important;grid-template-columns:155px minmax(0,1fr)!important;padding:0 9px!important;gap:6px!important}.war-room-global .war-room-brand strong{font-size:28px!important}.war-room-global .war-room-brand small{font-size:7px!important;letter-spacing:.09em!important}.war-room-global .war-room-nav{height:70px!important}.war-room-global .war-room-nav a{font-size:11px!important;padding:0 7px!important}}
</style>"""

def shell_markup(target:str)->str:
    active_target=ACTIVE_ALIASES.get(target,target)
    links=''.join(f'<a href="{href}"'+(' class="active"' if href==active_target else '')+f'>{label}</a>' for label,href in LINKS)
    label=next((label for label,href in LINKS if href==target), target.removesuffix('.html').replace('-',' ').title())
    return '<div class="brand war-room-brand"><a href="index.html"><strong>WAR<span>ROOM</span></strong><small>COLLEGE FOOTBALL INTELLIGENCE</small></a></div><nav class="nav war-room-nav">'+links+'</nav><div class="war-room-meta"><span class="war-room-context">'+label+'</span><div class="war-room-health"><i></i>Data Healthy</div></div>'

def remove_legacy_shell(text:str, target:str)->str:
    """Remove complete page-owned headers before installing one global shell."""
    text=re.sub(r'<header class="war-room-global">.*?</header>\s*','',text,count=1,flags=re.S)
    text=re.sub(r'<header class="top">.*?</header>\s*','',text,count=1,flags=re.S)
    text=re.sub(r'<header>\s*.*?<nav>.*?</nav>\s*</header>\s*','',text,count=1,flags=re.S)
    if target == 'index.html':
        text=re.sub(r'<header>.*?</header>\s*','',text,count=1,flags=re.S)
    text=re.sub(
        r'<div class="top">.*?</div>(?=\s*(?:<section|<div class="page"|<div class="viewSwitch"))\s*',
        '',text,count=1,flags=re.S,
    )
    text=re.sub(
        r'<div class="site-nav">.*?</div>(?=\s*<header class="odds-controls-header")\s*',
        '',text,count=1,flags=re.S,
    )
    return text

def apply(path:Path)->None:
    target=path.name
    text=path.read_text(errors='ignore')

    markup=shell_markup(target)
    text=remove_legacy_shell(text,target)
    text=re.sub(
        r'(<body(?:\s[^>]*)?>)',
        r'\1\n<header class="war-room-global">'+markup+r'</header>',
        text,count=1,flags=re.S,
    )
    if 'shared-war-room-shell-v2' not in text:
        text=text.replace('</head>',STYLE+'</head>',1)
    path.write_text(text)
    print(f'War Room shell: {path}')

def main():
    if not OUT.exists():
        raise SystemExit(f'missing public build: {OUT}')
    for path in sorted(OUT.glob('*.html')):
        if path.name in CANONICAL or path.name=='index.html':
            apply(path)
    if (ROOT/'index.html').exists():
        apply(ROOT/'index.html')

if __name__=='__main__':
    main()
