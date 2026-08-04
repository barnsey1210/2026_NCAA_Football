#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import sys

ROOT = Path.home() / "NCAAF_AUTO"

OPENERS_FILES = [
    ROOT / "openers_v2.html",
    ROOT / "build/public_site/openers.html",
    Path.home() / "Sites/NCAAF_SITE/openers.html",
]

DAILY_SCRIPT = ROOT / "daily_market_update.sh"

CSS_START = "/* OPENERS_CONTEXT_GUIDE_CSS_START */"
CSS_END = "/* OPENERS_CONTEXT_GUIDE_CSS_END */"
JS_START = "/* OPENERS_CONTEXT_GUIDE_JS_START */"
JS_END = "/* OPENERS_CONTEXT_GUIDE_JS_END */"

CACHE_VERSION = "20260728-contextguide4"

CSS_BLOCK = r'''
/* OPENERS_CONTEXT_GUIDE_CSS_START */
.contextGuide{margin:10px 0 14px;border:1px solid #2d5f8c;border-radius:12px;background:#0a1930;overflow:hidden}
.contextGuide summary{cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 14px;color:#d9e7fb;font-weight:900;list-style:none}
.contextGuide summary::-webkit-details-marker{display:none}
.contextGuide summary::after{content:'+';display:inline-flex;align-items:center;justify-content:center;width:23px;height:23px;border:1px solid #3b6f9f;border-radius:999px;color:#bcd5f3;font-size:16px}
.contextGuide[open] summary::after{content:'–'}
.contextGuideIntro{color:#9fb4d1;font-size:12px;font-weight:700}
.contextGuideBody{border-top:1px solid #244765;padding:12px 14px 14px}
.contextGuideGrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}
.contextGuideCard{border:1px solid #274b6d;border-radius:10px;background:#0c203b;padding:10px}
.contextGuideHead{display:flex;align-items:center;gap:7px;margin-bottom:7px;font-weight:900}
.contextGuideDot{width:9px;height:9px;border-radius:999px;flex:0 0 auto}
.contextGuideDot.high{background:#38d98b}.contextGuideDot.medium{background:#f2c14e}.contextGuideDot.low{background:#8293aa}
.contextGuideCard ul{margin:0;padding-left:18px;color:#bdcee4;font-size:11px;line-height:1.45}
.contextGuideNote{margin-top:10px;color:#91a6c6;font-size:10px}
.contextGuideRule{color:#eef5ff;font-weight:800}
.contextLogoFallback{display:inline-flex;align-items:center;justify-content:center;min-width:22px;height:22px;padding:0 4px;border-radius:999px;background:#173b62;border:1px solid #3e6f9c;color:#f2f7ff;font-size:8px;font-weight:950}
@media(max-width:900px){.contextGuideGrid{grid-template-columns:1fr}}
/* OPENERS_CONTEXT_GUIDE_CSS_END */
'''

GUIDE_HTML = r'''
<details class="contextGuide" id="contextGuide">
  <summary>
    <span>Betting context guide</span>
    <span class="contextGuideIntro">What qualifies as High, Medium, or Low priority</span>
  </summary>
  <div class="contextGuideBody">
    <div class="contextGuideGrid">
      <div class="contextGuideCard">
        <div class="contextGuideHead"><span class="contextGuideDot high"></span>High priority</div>
        <ul>
          <li><span class="contextGuideRule">Validated P4-vs-G6 RP mismatch:</span> 50-31 ATS, 61.7%, n=81.</li>
          <li><span class="contextGuideRule">Full-game coach role:</span> n≥40 and ATS rate ≥60% or ≤40%.</li>
        </ul>
      </div>
      <div class="contextGuideCard">
        <div class="contextGuideHead"><span class="contextGuideDot medium"></span>Medium priority</div>
        <ul>
          <li><span class="contextGuideRule">Validated P4-vs-P4 RP underdog:</span> 12-5 ATS, 70.6%, n=17.</li>
          <li><span class="contextGuideRule">Full-game coach role:</span> n≥25 and ≥57.5% or ≤42.5%.</li>
          <li><span class="contextGuideRule">1H/2H coach role:</span> n≥25 and ≥60% or ≤40%.</li>
          <li><span class="contextGuideRule">Meaningful injury edge:</span> impact and recency weighted.</li>
        </ul>
      </div>
      <div class="contextGuideCard">
        <div class="contextGuideHead"><span class="contextGuideDot low"></span>Low priority</div>
        <ul>
          <li><span class="contextGuideRule">Coach trend:</span> n≥15 and ≥55% or ≤45%.</li>
          <li><span class="contextGuideRule">Schedule, continuity, weather, or market context:</span> qualifying setup without validated ATS history.</li>
          <li>Model spread and total edges are excluded here because they already appear in the main board.</li>
        </ul>
      </div>
    </div>
    <div class="contextGuideNote">Priority reflects historical support and sample size, not bet size. Rules can be revised as new research is validated.</div>
  </div>
</details>
'''

JS_BLOCK = r'''
/* OPENERS_CONTEXT_GUIDE_JS_START */
function contextLogoCandidates(team,summarySlug){
  const teamMetaSlug=TEAM_META?.[team]?.logo_slug;
  const explicit={
    'Texas A&M':['texas-am','texas-a-m','texas_a_m','texas-aandm'],
    'Miami-FL':['miami-fl','miami'],
    'Miami-OH':['miami-oh','miami-ohio']
  };
  const normalized=String(team||'').toLowerCase().replace(/&/g,'and').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
  return [...new Set([summarySlug,teamMetaSlug,...(explicit[team]||[]),normalized].filter(Boolean))];
}
function contextLogoError(img){
  const candidates=JSON.parse(img.dataset.candidates||'[]');
  const next=Number(img.dataset.index||0)+1;
  if(next<candidates.length){
    img.dataset.index=String(next);
    img.src=`logos/${candidates[next]}.png`;
    return;
  }
  const fallback=document.createElement('span');
  fallback.className='contextLogoFallback';
  fallback.textContent=img.dataset.fallback||'?';
  img.replaceWith(fallback);
}
function contextTeamLogoHtml(team,summarySlug){
  const candidates=contextLogoCandidates(team,summarySlug);
  const fallback=String(team||'?').split(/\s+/).map(part=>part[0]||'').join('').slice(0,3).toUpperCase();
  if(!candidates.length)return `<span class="contextLogoFallback">${esc(fallback)}</span>`;
  return `<img src="logos/${esc(candidates[0])}.png" alt="" data-candidates="${esc(JSON.stringify(candidates))}" data-index="0" data-fallback="${esc(fallback)}" onerror="contextLogoError(this)">`;
}
function installContextGuide(){
  if(document.getElementById('contextGuide'))return;
  const guideTemplate=document.createElement('template');
  guideTemplate.innerHTML=`__GUIDE_HTML__`;
  const guide=guideTemplate.content.firstElementChild;
  const projectionLabel=[...document.querySelectorAll('*')].find(el=>el.children.length===0&&el.textContent.trim()==='PROJECTION VIEW');
  if(projectionLabel){
    const row=projectionLabel.parentElement;
    row.parentElement.insertBefore(guide,row);
    return;
  }
  const board=document.querySelector('table');
  if(board)board.parentElement.insertBefore(guide,board);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',installContextGuide,{once:true});
else installContextGuide();
/* OPENERS_CONTEXT_GUIDE_JS_END */
'''.replace("__GUIDE_HTML__", GUIDE_HTML.replace("`","\\`"))

ALIGNED_CONTEXT_FUNCTION = r'''function alignedContextHtml(summary){
  if(!summary||!Array.isArray(summary.rows))return'<span class="muted">—</span>';
  const teams=[summary.away_team,summary.home_team];
  const logoSlugs={[summary.away_team]:summary.away_logo_slug,[summary.home_team]:summary.home_logo_slug};
  const groups=new Map();
  for(const row of summary.rows){
    const raw=String(row.team||'').toLowerCase();
    const team=teams.find(t=>raw.includes(String(t||'').toLowerCase()));
    if(!team)continue;
    if(!groups.has(team))groups.set(team,[]);
    groups.get(team).push(row);
  }
  const ordered=teams.filter(team=>groups.has(team));
  if(!ordered.length)return'<span class="muted">—</span>';
  const priorityOrder={High:3,Medium:2,Low:1};
  const chips=ordered.map(team=>{
    const rows=groups.get(team);
    const highest=rows.reduce((best,row)=>(priorityOrder[row.priority]||0)>(priorityOrder[best]||0)?row.priority:best,'Low');
    const title=rows.map(row=>`${row.priority||'Low'} · ${row.market||'Context'}: ${row.trigger||row.evidence||'Qualifying rule'}`).join('\n');
    return `<span class="alignedContextTeam" title="${esc(team)} · ${esc(title)}"><span class="contextPriorityDot ${String(highest).toLowerCase()}"></span>${contextTeamLogoHtml(team,logoSlugs[team])}<b>×${rows.length}</b></span>`;
  });
  if(chips.length===2)chips.splice(1,0,'<span class="alignedContextConflict" title="Qualifying context supports both teams">↔</span>');
  return `<span class="alignedContextRow">${chips.join('')}</span>`;
}'''

def strip_block(text: str, start: str, end: str) -> str:
    return re.sub(re.escape(start)+r".*?"+re.escape(end)+r"\s*","",text,flags=re.S)

def find_function_span(text: str, name: str):
    m=re.search(rf"\bfunction\s+{re.escape(name)}\s*\([^)]*\)\s*\{{",text)
    if not m:return None
    opening=text.find("{",m.start());depth=0;ins=False;quote="";escd=False
    for i in range(opening,len(text)):
        ch=text[i]
        if ins:
            if escd:escd=False
            elif ch=="\\":escd=True
            elif ch==quote:ins=False
            continue
        if ch in {"'","\"","`"}:ins=True;quote=ch;continue
        if ch=="{":depth+=1
        elif ch=="}":
            depth-=1
            if depth==0:return m.start(),i+1
    raise RuntimeError(f"Unclosed function: {name}")

def patch_openers(path: Path, original: str) -> str:
    text=strip_block(original,CSS_START,CSS_END)
    text=strip_block(text,JS_START,JS_END)
    span=find_function_span(text,"alignedContextHtml")
    if span is None:raise RuntimeError(f"alignedContextHtml() not found in {path}")
    start,end=span;text=text[:start]+ALIGNED_CONTEXT_FUNCTION+text[end:]
    if "</style>" not in text:raise RuntimeError(f"</style> not found in {path}")
    text=text.replace("</style>",CSS_BLOCK+"\n</style>",1)
    final_script=text.rfind("</script>")
    if final_script<0:raise RuntimeError(f"No closing </script> found in {path}")
    text=text[:final_script]+JS_BLOCK+"\n"+text[final_script:]
    text,count=re.subn(r'(src=["\']matchup_workspace\.js)(?:\?[^"\']*)?(["\'])',rf'\1?v={CACHE_VERSION}\2',text)
    if count<1:raise RuntimeError(f"matchup_workspace.js reference not found in {path}")
    for token in ["contextLogoCandidates","contextTeamLogoHtml","Betting context guide","50-31 ATS","12-5 ATS",f"v={CACHE_VERSION}"]:
        if token not in text:raise RuntimeError(f"Validation missing {token}: {path}")
    return text

def backup_path(path: Path, timestamp: str) -> Path:
    base=ROOT/"backups/openers_context_guide"/timestamp
    try:dest=base/path.relative_to(ROOT)
    except ValueError:dest=base/"external"/path.name
    dest.parent.mkdir(parents=True,exist_ok=True)
    return dest

def update_daily(timestamp: str) -> bool:
    if not DAILY_SCRIPT.exists():return False
    command="python3 scripts/site/install_openers_context_guide.py"
    text=DAILY_SCRIPT.read_text(encoding="utf-8",errors="ignore")
    if command in text:return False
    backup=backup_path(DAILY_SCRIPT,timestamp);shutil.copy2(DAILY_SCRIPT,backup)
    block=f"\n\n# Add/update the Openers betting-context guide and logo fallbacks.\nif [ -f scripts/site/install_openers_context_guide.py ]; then\n  {command}\nfi\n"
    DAILY_SCRIPT.write_text(text.rstrip()+block,encoding="utf-8")
    return True

def main():
    pages=[p for p in OPENERS_FILES if p.exists()]
    if not pages:raise FileNotFoundError("No Openers HTML files found")
    patched={}
    for p in pages:patched[p]=patch_openers(p,p.read_text(encoding="utf-8",errors="ignore"))
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    for p,content in patched.items():
        backup=backup_path(p,stamp);shutil.copy2(p,backup);p.write_text(content,encoding="utf-8")
        print(f"patched: {p}");print(f"backup:  {backup}")
    daily=update_daily(stamp)
    print("\nOPENERS CONTEXT GUIDE INSTALLATION")
    print("="*100)
    print(f"Openers files patched: {len(pages)}")
    print(f"Daily script hook added: {daily}")
    print("Expandable context guide added: True")
    print("Texas A&M logo fallback added: True")
    print("Priority dots preserved: True")

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        raise
