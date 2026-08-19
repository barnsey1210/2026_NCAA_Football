#!/usr/bin/env python3
"""Apply the canonical War Room shell to every public production page."""
from __future__ import annotations
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/public_site'
LINKS=[
 ('Home','index.html'),('Ratings','ratings.html'),('Matchups','matchups.html'),
 ('Openers','openers.html'),('Odds','odds.html'),('Schedule','schedule.html'),
 ('Futures','futures.html'),('Conferences','conferences.html'),('Coaches','coaches.html'),
 ('Playoff','playoff.html'),('Sim Lab','simulations.html'),('Betting','betting.html'),
]
CANONICAL={href for _,href in LINKS}|{'team.html','matchup.html'}
STYLE="""<style id="shared-war-room-shell-v2">
:root{--wr-blue:#3caaff;--wr-gold:#ffc83d;--wr-green:#32e89f;--wr-line:#214a70}
.top{width:100%!important;max-width:none!important;min-height:82px!important;display:grid!important;grid-template-columns:300px minmax(0,1fr) auto!important;gap:14px!important;align-items:center!important;padding:0 22px!important;background:#020914!important;border-bottom:1px solid #17395d!important}
.top .brand.war-room-brand{min-width:0!important}.war-room-brand a{display:block!important;color:#fff!important;text-decoration:none!important}.war-room-brand strong{display:block!important;font:900 42px/.88 Impact,Haettenschweiler,"Arial Narrow Bold",sans-serif!important;letter-spacing:.025em!important}.war-room-brand strong span{color:var(--wr-blue)!important}.war-room-brand small{display:block!important;margin-top:9px!important;color:var(--wr-gold)!important;font-size:9px!important;font-weight:1000!important;letter-spacing:.16em!important;white-space:nowrap!important}
.top .nav.war-room-nav{display:flex!important;align-items:stretch!important;gap:0!important;min-width:0!important;overflow:visible!important;height:82px!important}.top .nav.war-room-nav a{display:flex!important;align-items:center!important;padding:0 10px!important;color:#becada!important;font-size:15px!important;font-weight:900!important;white-space:nowrap!important;border-radius:0!important;background:none!important;position:relative!important}.top .nav.war-room-nav a.active{color:var(--wr-gold)!important}.top .nav.war-room-nav a.active:after{content:"";position:absolute;left:9px;right:9px;bottom:0;height:4px;background:var(--wr-gold);border-radius:4px}
.war-room-health{display:flex!important;align-items:center!important;gap:7px!important;padding:9px 13px!important;border:1px solid #277155!important;border-radius:999px!important;background:#05251d!important;color:#c5f8e0!important;font-size:12px!important;font-weight:900!important;white-space:nowrap!important}.war-room-health i{width:9px;height:9px;border-radius:50%;background:var(--wr-green);box-shadow:0 0 10px rgba(50,232,159,.75)}
.top>.model,.top>.tools,.top>.actions{display:none!important}.shell,.wrap,.container,main{max-width:none!important}.shell,.wrap{width:100%!important;padding-left:22px!important;padding-right:22px!important}
@media(max-width:1550px){.top{grid-template-columns:255px minmax(0,1fr) auto!important;padding:0 14px!important}.war-room-brand strong{font-size:36px!important}.top .nav.war-room-nav a{font-size:13px!important;padding:0 7px!important}.war-room-health{font-size:11px!important;padding:8px 10px!important}}
@media(max-width:1180px){.top{grid-template-columns:220px minmax(0,1fr)!important}.war-room-health{display:none!important}.top .nav.war-room-nav{overflow:auto!important;scrollbar-width:none}.top .nav.war-room-nav::-webkit-scrollbar{display:none}}
.war-room-global{width:100%!important;max-width:none!important;min-height:82px!important;display:grid!important;grid-template-columns:300px minmax(0,1fr) auto!important;gap:14px!important;align-items:center!important;padding:0 22px!important;background:#020914!important;border-bottom:1px solid #17395d!important}
.war-room-global .war-room-brand{min-width:0!important}.war-room-global .war-room-brand a{display:block!important;color:#fff!important;text-decoration:none!important}.war-room-global .war-room-brand strong{display:block!important;font:900 42px/.88 Impact,Haettenschweiler,"Arial Narrow Bold",sans-serif!important;letter-spacing:.025em!important}.war-room-global .war-room-brand strong span{color:var(--wr-blue)!important}.war-room-global .war-room-brand small{display:block!important;margin-top:9px!important;color:var(--wr-gold)!important;font-size:9px!important;font-weight:1000!important;letter-spacing:.16em!important;white-space:nowrap!important}
.war-room-global .war-room-nav{display:flex!important;align-items:stretch!important;gap:0!important;min-width:0!important;overflow:visible!important;height:82px!important}.war-room-global .war-room-nav a{display:flex!important;align-items:center!important;padding:0 10px!important;color:#becada!important;font-size:15px!important;font-weight:900!important;white-space:nowrap!important;text-decoration:none!important;position:relative!important}.war-room-global .war-room-nav a.active{color:var(--wr-gold)!important}.war-room-global .war-room-nav a.active:after{content:"";position:absolute;left:9px;right:9px;bottom:0;height:4px;background:var(--wr-gold);border-radius:4px}
.war-room-global .war-room-health{justify-self:end!important}
@media(max-width:1550px){.war-room-global{grid-template-columns:255px minmax(0,1fr) auto!important;padding:0 14px!important}.war-room-global .war-room-brand strong{font-size:36px!important}.war-room-global .war-room-nav a{font-size:13px!important;padding:0 7px!important}}
@media(max-width:1180px){.war-room-global{grid-template-columns:220px minmax(0,1fr)!important}.war-room-global .war-room-health{display:none!important}.war-room-global .war-room-nav{overflow:auto!important;scrollbar-width:none}.war-room-global .war-room-nav::-webkit-scrollbar{display:none}}
</style>"""

def shell_markup(target:str)->str:
    links=''.join(f'<a href="{href}"'+(' class="active"' if href==target else '')+f'>{label}</a>' for label,href in LINKS)
    return '<div class="brand war-room-brand"><a href="index.html"><strong>WAR<span>ROOM</span></strong><small>COLLEGE FOOTBALL INTELLIGENCE</small></a></div><div class="nav war-room-nav">'+links+'</div><div class="war-room-health"><i></i>Data Healthy</div>'

def apply(path:Path)->None:
    target=path.name
    text=path.read_text(errors='ignore')

    # Idempotency: remove duplicate health controls left by previous shell passes.
    # Odds already owns the canonical global shell, so preserve its health badge.
    if target != 'index.html' and target != 'odds.html':
        text = re.sub(
            r'<div class="war-room-health"[^>]*>.*?</div>',
            '',
            text,
            flags=re.S,
        )
    if target=='index.html':
        text=text.replace('<div class="header-right"><div class="round">⌕</div><div class="round">⚙</div><div class="round">JL</div><div class="health"><span class="pulse"></span>Data Healthy</div></div>','<div class="header-right"><div class="health"><span class="pulse"></span>Data Healthy</div></div>')
        if 'canonical-war-room-shell-v2' not in text:
            text=text.replace('</head>','<style id="canonical-war-room-shell-v2">.page{width:min(1680px,calc(100vw - 32px))!important;max-width:1680px!important;margin-inline:auto!important}header{grid-template-columns:290px minmax(0,1fr) auto!important}header nav a{font-size:14px!important}.round{display:none!important}</style></head>',1)
    else:
        markup=shell_markup(target)

        # Odds uses <header class="top"> for market filters, tabs, and its
        # timestamp. Keep that functional control bar and add the global site
        # navigation above it instead of replacing it.
        if target == "odds.html":
            # Remove the separate legacy Odds navigation before adding the
            # canonical War Room global navigation.
            text = re.sub(
                r'<div class="site-nav">\s*'
                r'<div class="brand">.*?</div>\s*'
                r'<nav class="site-nav-links".*?</nav>\s*'
                r'<div class="site-nav-status".*?</div>\s*'
                r'</div>\s*',
                '',
                text,
                count=1,
                flags=re.S,
            )
            # Always rebuild odds global shell so stale/manual headers cannot
            # survive without the canonical health badge.
            text = re.sub(
                r'<header class="war-room-global">.*?</header>\s*',
                '',
                text,
                count=1,
                flags=re.S,
            )
            text=text.replace(
                '<header class="odds-controls-header">',
                '<header class="war-room-global">'+markup+'</header>\n  <header class="odds-controls-header">',
                1,
            )
            if 'shared-war-room-shell-v2' not in text:
                text=text.replace('</head>',STYLE+'</head>',1)
            path.write_text(text)
            print(f'War Room shell: {path}')
            return

        patterns=[
            r'<div class="brand(?: [^"]*)?">.*?</div><(?:div|nav) class="nav(?: [^"]*)?">.*?</(?:div|nav)>',
            r'<div class="brand">NCAAF Edge</div><nav class="nav">.*?</nav>',
        ]
        replaced=False
        for pattern in patterns:
            text,n=re.subn(pattern,markup,text,count=1,flags=re.S)
            if n:
                replaced=True
                break
        if not replaced and 'class="top"' in text:
            print(f'warning: top shell pattern not replaced: {path}')
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
