#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil
import sys

ROOT = Path.home() / "NCAAF_AUTO"

WORKSPACE_FILES = [
    ROOT / "matchup_workspace.js",
    ROOT / "build/public_site/matchup_workspace.js",
    Path.home() / "Sites/NCAAF_SITE/matchup_workspace.js",
]

OPENERS_FILES = [
    ROOT / "openers_v2.html",
    ROOT / "build/public_site/openers.html",
    Path.home() / "Sites/NCAAF_SITE/openers.html",
]

DAILY_SCRIPT = ROOT / "daily_market_update.sh"

JS_START = "/* OPENERS_CONTEXT_PRIORITY_POLICY_START */"
JS_END = "/* OPENERS_CONTEXT_PRIORITY_POLICY_END */"
CSS_START = "/* OPENERS_CONTEXT_PRIORITY_CSS_START */"
CSS_END = "/* OPENERS_CONTEXT_PRIORITY_CSS_END */"
CACHE_VERSION = "20260728-contextpriority3"

POLICY_BLOCK = r'''
/* OPENERS_CONTEXT_PRIORITY_POLICY_START */
function mwContextRecordStats(row){
  const text=[row?.trigger,row?.evidence,row?.detail,row?.headline].join(' ');
  const recordMatch=text.match(/\b(\d+)\s*[-–]\s*(\d+)(?:\s*[-–]\s*(\d+))?\b/);
  const pctMatch=text.match(/\b(\d{1,3}(?:\.\d+)?)\s*%/);
  const sampleMatch=text.match(/\bn\s*=\s*(\d+)\b/i)||text.match(/\bover\s+(\d+)\s+games?\b/i)||text.match(/\b(\d+)\s+games?\b/i);
  let wins=null,losses=null,pushes=0,sample=null,pct=null,record='';
  if(recordMatch){
    wins=Number(recordMatch[1]);losses=Number(recordMatch[2]);pushes=Number(recordMatch[3]||0);
    sample=wins+losses+pushes;
    record=`${wins}-${losses}${recordMatch[3]!=null?'-'+pushes:''}`;
  }
  if(sampleMatch)sample=Number(sampleMatch[1]);
  if(pctMatch)pct=Number(pctMatch[1]);
  if(pct==null&&wins!=null&&losses!=null&&wins+losses>0)pct=(wins/(wins+losses))*100;
  return {record,pct,sample};
}

function mwContextCategory(row){
  const id=String(row?.id||'').toLowerCase();
  const text=[row?.market,row?.trigger,row?.evidence,row?.detail,row?.headline].join(' ').toLowerCase();
  if(id.includes('validated_rp')||text.includes('validated full-game rp')||text.includes('validated rp-edge'))return 'Validated RP';
  if(text.includes('coach')||text.includes(' ats ')||text.includes('ats as '))return 'Coach';
  if(text.includes('injur')||text.includes('qb1')||text.includes('quarterback'))return 'Injury';
  if(text.includes('travel')||text.includes('lookahead')||text.includes('sandwich')||text.includes('short rest')||text.includes('back-to-back')||text.includes('b2b')||text.includes('bye')||text.includes('step up')||text.includes('step down')||text.includes('competition'))return 'Schedule';
  if(text.includes('continuity'))return 'Continuity';
  if(text.includes('stale opener')||text.includes('cross-book')||text.includes('line move'))return 'Market';
  if(text.includes('weather')||text.includes('wind')||text.includes('rain'))return 'Weather';
  if(text.includes('model spread')||text.includes('model total'))return 'Model';
  return 'Other';
}

function mwContextPriority(row){
  const category=mwContextCategory(row),id=String(row?.id||'').toLowerCase(),stats=mwContextRecordStats(row);
  const pct=stats.pct,sample=stats.sample,distance=pct==null?null:Math.abs(pct-50);
  const isHalf=/\b1h\b|\b2h\b|first half|second half/i.test([row?.market,row?.trigger,row?.evidence].join(' '));
  if(category==='Model')return {include:false,priority:'Exclude',score:0,category,stats};
  if(id==='validated_rp_p4_g6_component_25')return {include:true,priority:'High',score:95,category,stats};
  if(id==='validated_rp_p4_p4_underdog')return {include:true,priority:'Medium',score:82,category,stats};
  if(category==='Coach'){
    if(sample==null||pct==null)return {include:false,priority:'Exclude',score:0,category,stats};
    if(!isHalf&&sample>=40&&distance>=10)return {include:true,priority:'High',score:90,category,stats};
    if((!isHalf&&sample>=25&&distance>=7.5)||(isHalf&&sample>=25&&distance>=10))return {include:true,priority:'Medium',score:76,category,stats};
    if(sample>=15&&distance>=5)return {include:true,priority:'Low',score:58,category,stats};
    return {include:false,priority:'Exclude',score:0,category,stats};
  }
  if(category==='Injury')return {include:true,priority:'Medium',score:72,category,stats};
  if(category==='Market')return {include:true,priority:'Low',score:56,category,stats};
  if(category==='Schedule'||category==='Continuity'||category==='Weather')return {include:true,priority:'Low',score:50,category,stats};
  return {include:false,priority:'Exclude',score:0,category,stats};
}

function mwContextConciseRow(row){
  const evaluation=mwContextPriority(row),stats=evaluation.stats,category=evaluation.category;
  let trigger=String(row?.trigger||category),evidence=String(row?.evidence||row?.detail||'');
  if(category==='Validated RP'){
    if(String(row?.id||'')==='validated_rp_p4_g6_component_25'){
      trigger='Validated RP mismatch';
      const m=evidence.match(/overall\s*([+\-]?\d+).*?offense vs defense\s*([+\-]?\d+).*?defense vs offense\s*([+\-]?\d+)/i);
      evidence=m?`OVR ${m[1]} · Off/Def ${m[2]} · Def/Off ${m[3]} · 50-31 ATS`:'50-31 ATS · 61.7% · n=81';
    }else{
      trigger='Validated RP underdog';
      evidence='12-5 ATS · 70.6% · n=17';
    }
  }else if(category==='Coach'){
    trigger=trigger.replace(/^Opposing coach poor\s*/i,'Coach fade · ').replace(/^Coach\s*/i,'Coach · ').replace(/\s+as\s+/i,' · ');
    const pieces=[];
    if(stats.record)pieces.push(stats.record+' ATS');
    if(stats.pct!=null)pieces.push(stats.pct.toFixed(1)+'%');
    if(stats.sample!=null)pieces.push('n='+stats.sample);
    const margin=evidence.match(/([+\-]?\d+(?:\.\d+)?)\s*ATS\s*\+\/-/i);
    if(margin)pieces.push(margin[1]+' ATS +/-');
    evidence=pieces.join(' · ')||evidence;
  }else{
    if(category==='Injury')trigger='Injury edge';
    if(category==='Continuity')trigger='Staff continuity';
    if(category==='Weather')trigger='Weather';
    evidence=evidence.slice(0,90);
  }
  return {...row,priority:evaluation.priority,priorityScore:evaluation.score,trigger,evidence,contextCategory:category};
}

function contextRows(game){
  const baseRows=contextRowsBeforePriorityPolicy(game);
  const filtered=baseRows.map(mwContextConciseRow).filter(row=>mwContextPriority(row).include);
  const seen=new Set(),deduped=[];
  for(const row of filtered){
    const key=[row.market,row.team,row.trigger,row.evidence].join('|').toLowerCase();
    if(seen.has(key))continue;
    seen.add(key);deduped.push(row);
  }
  const order={High:3,Medium:2,Low:1};
  deduped.sort((a,b)=>((order[b.priority]||0)-(order[a.priority]||0))||((Number(b.priorityScore)||0)-(Number(a.priorityScore)||0)));
  return deduped;
}
/* OPENERS_CONTEXT_PRIORITY_POLICY_END */
'''

WORKSPACE_CSS = r'''
/* OPENERS_CONTEXT_PRIORITY_CSS_START */
.mwContextTable{table-layout:fixed;width:100%}
.mwContextTable th:nth-child(1),.mwContextTable td:nth-child(1){width:78px}
.mwContextTable th:nth-child(2),.mwContextTable td:nth-child(2){width:88px}
.mwContextTable th:nth-child(3),.mwContextTable td:nth-child(3){width:150px}
.mwContextTable th:nth-child(4),.mwContextTable td:nth-child(4){width:230px}
.mwContextTable th,.mwContextTable td{white-space:normal;overflow-wrap:anywhere}
.mwPriority{min-width:44px;text-align:center}
.mwContextTable tr[data-priority="High"] .mwPriority{background:#16784f;color:#eafff4}
.mwContextTable tr[data-priority="Medium"] .mwPriority{background:#8a6819;color:#fff5d2}
.mwContextTable tr[data-priority="Low"] .mwPriority{background:#506176;color:#eef4ff}
/* OPENERS_CONTEXT_PRIORITY_CSS_END */
'''

OPENERS_CSS = r'''
/* OPENERS_CONTEXT_PRIORITY_CSS_START */
.contextPriorityDot{display:inline-block;width:8px;height:8px;border-radius:999px;margin-right:4px;vertical-align:middle}
.contextPriorityDot.high{background:#38d98b}
.contextPriorityDot.medium{background:#f2c14e}
.contextPriorityDot.low{background:#8293aa}
.alignedContextTeam img{width:22px;height:22px;object-fit:contain}
/* OPENERS_CONTEXT_PRIORITY_CSS_END */
'''

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
  const ordered=teams.filter(t=>groups.has(t));
  if(!ordered.length)return'<span class="muted">—</span>';
  const priorityOrder={High:3,Medium:2,Low:1};
  const chips=ordered.map(team=>{
    const rows=groups.get(team);
    const highest=rows.reduce((best,row)=>(priorityOrder[row.priority]||0)>(priorityOrder[best]||0)?row.priority:best,'Low');
    const slug=logoSlugs[team];
    const logoHtml=slug?`<img src="logos/${esc(slug)}.png" alt="" onerror="this.style.display='none'">`:logo(TEAM_META[team]||{});
    const title=rows.map(x=>`${x.priority||'Low'} · ${x.market||'Context'}: ${x.trigger||x.evidence||'Qualifying rule'}`).join('\n');
    return `<span class="alignedContextTeam" title="${esc(team)} · ${esc(title)}"><span class="contextPriorityDot ${String(highest).toLowerCase()}"></span>${logoHtml}<b>×${rows.length}</b></span>`;
  });
  if(chips.length===2)chips.splice(1,0,'<span class="alignedContextConflict" title="Qualifying context supports both teams">↔</span>');
  return `<span class="alignedContextRow">${chips.join('')}</span>`;
}'''

def strip_block(text: str, start: str, end: str) -> str:
    return re.sub(re.escape(start)+r".*?"+re.escape(end)+r"\s*", "", text, flags=re.S)

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

def patch_context_table(text: str) -> str:
    span=find_function_span(text,"contextTable")
    if span is None:raise RuntimeError("contextTable() not found")
    start,end=span;old=text[start:end];new=old
    new=new.replace('<tr data-rule="${esc(x.id)}">','<tr data-rule="${esc(x.id)}" data-priority="${esc(x.priority||\'Low\')}">')
    new=new.replace('<th>Priority</th><th>Market</th><th>Team / Side</th><th>Trigger</th><th>Evidence</th>','<th>Priority</th><th>Market</th><th>Side</th><th>Angle</th><th>Key evidence</th>')
    if new==old:raise RuntimeError("contextTable markup pattern not found")
    return text[:start]+new+text[end:]

def patch_workspace(path: Path, original: str) -> str:
    text=strip_block(original,JS_START,JS_END)
    text=strip_block(text,CSS_START,CSS_END)
    text=re.sub(r"\bfunction\s+contextRowsBeforePriorityPolicy\s*\(","function contextRows(",text,count=1)
    span=find_function_span(text,"contextRows")
    if span is None:raise RuntimeError(f"contextRows() not found in {path}")
    start,end=span;fn=text[start:end]
    renamed=re.sub(r"\bfunction\s+contextRows\s*\(","function contextRowsBeforePriorityPolicy(",fn,count=1)
    text=text[:start]+renamed+"\n"+POLICY_BLOCK+text[end:]
    text=patch_context_table(text)
    anchor='.mwSection[data-section="betting-context"] h3'
    pos=text.find(anchor)
    if pos<0:raise RuntimeError(f"CSS anchor not found in {path}")
    line_end=text.find("\n",pos)
    text=text[:line_end+1]+WORKSPACE_CSS+"\n"+text[line_end+1:]
    for token in ["function contextRowsBeforePriorityPolicy(","function contextRows(game)","data-priority=","50-31 ATS","12-5 ATS"]:
        if token not in text:raise RuntimeError(f"Workspace validation missing {token}: {path}")
    return text

def patch_openers(path: Path, original: str) -> str:
    text=strip_block(original,CSS_START,CSS_END)
    span=find_function_span(text,"alignedContextHtml")
    if span is None:raise RuntimeError(f"alignedContextHtml() not found in {path}")
    start,end=span;text=text[:start]+ALIGNED_CONTEXT_FUNCTION+text[end:]
    if "</style>" not in text:raise RuntimeError(f"</style> not found in {path}")
    text=text.replace("</style>",OPENERS_CSS+"\n</style>",1)
    text,count=re.subn(r'(src=["\']matchup_workspace\.js)(?:\?[^"\']*)?(["\'])',rf'\1?v={CACHE_VERSION}\2',text)
    if count<1:raise RuntimeError(f"workspace script reference not found in {path}")
    return text

def backup_path(path: Path, timestamp: str) -> Path:
    base=ROOT/"backups/openers_context_priority"/timestamp
    try:dest=base/path.relative_to(ROOT)
    except ValueError:dest=base/"external"/path.name
    dest.parent.mkdir(parents=True,exist_ok=True)
    return dest

def update_daily(timestamp: str) -> bool:
    if not DAILY_SCRIPT.exists():return False
    command="python3 scripts/site/install_openers_context_priority_policy.py"
    text=DAILY_SCRIPT.read_text(encoding="utf-8",errors="ignore")
    if command in text:return False
    backup=backup_path(DAILY_SCRIPT,timestamp);shutil.copy2(DAILY_SCRIPT,backup)
    block=f"\n\n# Apply concise non-model Openers context priority policy.\nif [ -f scripts/site/install_openers_context_priority_policy.py ]; then\n  {command}\nfi\n"
    DAILY_SCRIPT.write_text(text.rstrip()+block,encoding="utf-8")
    return True

def main():
    workspaces=[p for p in WORKSPACE_FILES if p.exists()]
    openers=[p for p in OPENERS_FILES if p.exists()]
    if not workspaces:raise FileNotFoundError("No matchup_workspace.js files found")
    if not openers:raise FileNotFoundError("No Openers HTML files found")
    patched={}
    for p in workspaces:patched[p]=patch_workspace(p,p.read_text(encoding="utf-8",errors="ignore"))
    for p in openers:patched[p]=patch_openers(p,p.read_text(encoding="utf-8",errors="ignore"))
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    for p,content in patched.items():
        backup=backup_path(p,stamp);shutil.copy2(p,backup);p.write_text(content,encoding="utf-8")
        print(f"patched: {p}");print(f"backup:  {backup}")
    daily=update_daily(stamp)
    print("\nOPENERS CONTEXT PRIORITY INSTALLATION")
    print("="*100)
    print(f"Workspace files patched: {len(workspaces)}")
    print(f"Openers files patched: {len(openers)}")
    print(f"Daily script hook added: {daily}")
    print("Model spread/total rows included: False")
    print("Exploratory 1H RP included: False")
    print("\nPriority policy:")
    print("  High: primary validated RP; full-game coach n>=40 and >=60% or <=40%")
    print("  Medium: RP underdog; strong coach samples; meaningful injuries")
    print("  Low: smaller qualified coach trends and structural context")
    print("  Excluded: model edges, weak coach samples, generic RP gaps")

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        raise
