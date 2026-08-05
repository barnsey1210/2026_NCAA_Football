#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TARGETS=[
    ROOT/"build/public_site/matchups.html",
    ROOT/"build/public_site/openers.html",
    ROOT/"matchups.html",
    ROOT/"openers.html",
]
MARKER="canonical-spread-side-label-v1"
SCRIPT='''<script id="canonical-spread-side-label-v1">
(()=>{
  const parseTeams=()=>{
    const headings=[...document.querySelectorAll('h1,h2,.drawerHead h2,.drawer-head h2')];
    for(const h of headings){
      const m=(h.textContent||'').trim().match(/^(.+?)\\s+at\\s+(.+?)$/i);
      if(m)return {away:m[1].trim(),home:m[2].trim()};
    }
    return null;
  };
  const fmt=n=>`${n>0?'+':''}${n.toFixed(1)}`;
  const enhance=()=>{
    const teams=parseTeams(); if(!teams)return;
    for(const table of document.querySelectorAll('table')){
      const heads=[...table.querySelectorAll('thead th')].map(x=>(x.textContent||'').trim().toUpperCase());
      const idx=heads.findIndex(x=>x.includes('ATS SPREAD'));
      if(idx<0)continue;
      for(const row of table.querySelectorAll('tbody tr')){
        const cell=row.children[idx];
        if(!cell||cell.dataset.sideLabeled==='1')continue;
        const raw=(cell.textContent||'').trim().replace(/[−–]/g,'-');
        const v=Number(raw); if(!Number.isFinite(v))continue;
        cell.textContent=v<0?`${teams.home} ${fmt(v)}`:v>0?`${teams.away} ${fmt(-v)}`:`Pick'em`;
        cell.dataset.sideLabeled='1';
      }
    }
  };
  new MutationObserver(enhance).observe(document.documentElement,{childList:true,subtree:true});
  document.addEventListener('click',()=>setTimeout(enhance,0),true);
  enhance();
})();
</script>'''
for path in TARGETS:
    if not path.exists(): continue
    text=path.read_text(encoding="utf-8")
    if MARKER in text: continue
    if "</body>" not in text:
        raise SystemExit(f"Missing </body>: {path}")
    path.write_text(text.replace("</body>",SCRIPT+"\n</body>",1),encoding="utf-8")
    print(f"injected spread-side labels: {path}")
