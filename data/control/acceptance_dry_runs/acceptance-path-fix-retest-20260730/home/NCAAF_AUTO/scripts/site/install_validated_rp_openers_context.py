#!/usr/bin/env python3
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import json,re,shutil,sys
from typing import Any
import numpy as np
import pandas as pd

ROOT=Path.home()/"NCAAF_AUTO"
SOURCE_CSV=ROOT/"data/signals/returning_production_validated_matches_2026_with_market_role.csv"
PAGES=[ROOT/"openers_v2.html",ROOT/"build/public_site/openers.html",ROOT/"openers.html",Path.home()/"Sites/NCAAF_SITE/openers.html"]
JSON_REL=Path("data/site/returning_production_validated_signals_2026.json")
JSON_TARGETS=[ROOT/JSON_REL,ROOT/"build/public_site"/JSON_REL,Path.home()/"Sites/NCAAF_SITE"/JSON_REL]
DAILY=ROOT/"daily_market_update.sh"
START="/* VALIDATED_RP_OPENERS_CONTEXT_START */"; END="/* VALIDATED_RP_OPENERS_CONTEXT_END */"
CSS_START="/* VALIDATED_RP_OPENERS_CSS_START */"; CSS_END="/* VALIDATED_RP_OPENERS_CSS_END */"

def clean(v:Any)->str:
    if v is None or (isinstance(v,float) and np.isnan(v)): return ""
    return str(v).strip()

def num(v):
    try:
        x=float(v); return x if np.isfinite(x) else None
    except Exception:return None

def consolidate(df):
    req={'game_id','week','date','away_team','home_team','signal_team','signal_opponent','rule_key','rule_label','rule_priority','overall_rp_edge','offense_vs_defense_edge','defense_vs_offense_edge'}
    miss=sorted(req-set(df.columns))
    if miss: raise KeyError(f"Missing columns: {miss}")
    df=df.copy(); df['rule_priority']=pd.to_numeric(df['rule_priority'],errors='coerce')
    df=df.sort_values(['game_id','signal_team','rule_priority'])
    out=[]
    for (gid,team),g in df.groupby(['game_id','signal_team'],dropna=False):
        keys=set(g.rule_key.astype(str)); p=g.iloc[0]
        if 'P4_G6_EITHER_COMPONENT_25_PLUS' in keys:
            key='P4_G6_EITHER_COMPONENT_25_PLUS'; p=g[g.rule_key.eq(key)].iloc[0]; title='Strong RP mismatch'; rec='50-31'; pct=61.73; n=81; tier='A'
        elif 'P4_P4_OVERALL_15_TO_24_9' in keys:
            key='P4_P4_OVERALL_15_TO_24_9'; p=g[g.rule_key.eq(key)].iloc[0]; title='Role-dependent RP edge'; rec='29-22-1'; pct=56.86; n=52; tier='C'
        else:
            key='P4_G6_DEFENSE_15_PLUS'; p=g[g.rule_key.eq(key)].iloc[0]; title='Defensive continuity edge'; rec='46-32'; pct=58.97; n=78; tier='B'
        out.append({
          'game_id':clean(gid),'week':int(float(p.week)),'date':clean(p.date),'away_team':clean(p.away_team),'home_team':clean(p.home_team),
          'signal_team':clean(team),'signal_opponent':clean(p.signal_opponent),'primary_rule_key':key,'primary_rule_label':clean(p.rule_label),
          'title':title,'tier':tier,'overall_record':rec,'overall_ats_pct':pct,'overall_games':n,
          'overall_rp_edge':num(p.overall_rp_edge),'offense_vs_defense_edge':num(p.offense_vs_defense_edge),'defense_vs_offense_edge':num(p.defense_vs_offense_edge),
          'has_defensive_support':'P4_G6_DEFENSE_15_PLUS' in keys,'matched_rule_count':len(g),'history_window':'2021-2025, Weeks 1-4'
        })
    return sorted(out,key=lambda x:(x['week'],x['date'],x['away_team']))

def write_json(signals):
    payload={'meta':{'generated_at':datetime.now().isoformat(timespec='seconds'),'history_window':'2021-2025, Weeks 1-4','unique_games':len({x['game_id'] for x in signals}),'signal_rows':len(signals)},'signals':signals}
    text=json.dumps(payload,indent=2)
    for p in JSON_TARGETS:
        if p==JSON_TARGETS[0] or p.parent.parent.exists():
            p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text+'\n'); print('wrote JSON:',p)

JS_BLOCK=r'''
/* VALIDATED_RP_OPENERS_CONTEXT_START */
let VALIDATED_RP_SIGNALS={meta:{},signals:[]};let VALIDATED_RP_BY_GAME=new Map();
function validatedRpLoad(payload){VALIDATED_RP_SIGNALS=payload||{meta:{},signals:[]};VALIDATED_RP_BY_GAME=new Map();for(const row of(VALIDATED_RP_SIGNALS.signals||[])){const k=String(row.game_id||'');if(!VALIDATED_RP_BY_GAME.has(k))VALIDATED_RP_BY_GAME.set(k,[]);VALIDATED_RP_BY_GAME.get(k).push(row)}}
function validatedRpSignal(r){const rows=VALIDATED_RP_BY_GAME.get(String(r?.game?.game_id||''))||[];return rows[0]||null}
function validatedRpTeamSpread(r,s){const h=r?.market?.spread?.home_line;if(h==null||!Number.isFinite(Number(h)))return null;return s.signal_team===r.game.home_team?Number(h):s.signal_team===r.game.away_team?-Number(h):null}
function validatedRpRole(x){return x==null?'Unknown':x<0?'Favorite':x>0?'Underdog':"Pick'em"}
function validatedRpBucket(x){if(x==null)return'Unknown';const a=Math.abs(x);if(x<0)return a>=21?'Fav 21+':a>=14?'Fav 14-20.5':a>=7?'Fav 7-13.5':'Fav 0.5-6.5';if(x>0)return a>=21?'Dog 21+':a>=14?'Dog 14-20.5':a>=7?'Dog 7-13.5':'Dog 0.5-6.5';return"Pick'em"}
function validatedRpComparison(s,x){const role=validatedRpRole(x),bucket=validatedRpBucket(x),T={
'P4_G6_EITHER_COMPONENT_25_PLUS':{'Favorite':['49-31',61.3,80,'favorite subset'],'Fav 14-20.5':['13-9',59.1,22,'14–20.5 favorites'],'Fav 21+':['27-20',57.4,47,'21+ favorites']},
'P4_G6_DEFENSE_15_PLUS':{'Favorite':['43-31',58.1,74,'favorite subset'],'Fav 14-20.5':['11-6',64.7,17,'14–20.5 favorites'],'Fav 21+':['25-19',56.8,44,'21+ favorites']},
'P4_P4_OVERALL_15_TO_24_9':{'Favorite':['17-17-1',50.0,35,'RP-edge favorites'],'Underdog':['12-5',70.6,17,'RP-edge underdogs'],'Fav 0.5-6.5':['7-8',46.7,15,'short favorites']}};const z=T[s.primary_rule_key]||{},v=z[bucket]||z[role];return v?{record:v[0],pct:v[1],games:v[2],label:v[3]}:null}
function validatedRpStatus(s,x){const role=validatedRpRole(x);if(role==='Unknown')return{tone:'watch',label:'Line watch',read:'Qualifying RP side is known; market role is pending.'};if(s.primary_rule_key==='P4_P4_OVERALL_15_TO_24_9'){if(role==='Underdog')return{tone:'positive',label:'Positive betting context',read:'The RP-edge underdog subset went 12-5 ATS.'};if(role==='Favorite')return{tone:'neutral',label:'Context only',read:'RP-edge favorites went 17-17-1 ATS; no historical favorite edge.'};return{tone:'watch',label:'Line watch',read:'Market role is needed before activating this signal.'}}return{tone:'positive',label:'RP lean',read:'The qualifying P4 team is the historical bet side.'}}
function validatedRpDetail(s,r){const spread=validatedRpTeamSpread(r,s),role=validatedRpRole(spread),cmp=validatedRpComparison(s,spread),st=validatedRpStatus(s,spread),spreadText=spread==null?'spread not open':`${spread>0?'+':''}${spread.toFixed(1)}`,support=s.has_defensive_support?' · defensive 15+ support':'',hist=cmp?`${cmp.label}: ${cmp.record} ATS (${cmp.pct.toFixed(1)}%, n=${cmp.games})`:`overall rule: ${s.overall_record} ATS (${Number(s.overall_ats_pct).toFixed(1)}%, n=${s.overall_games})`;return{status:st,comparisonText:hist,detail:`${s.title}: ${s.signal_team} · overall ${s.overall_rp_edge>=0?'+':''}${Number(s.overall_rp_edge).toFixed(0)} · Off vs Def ${s.offense_vs_defense_edge>=0?'+':''}${Number(s.offense_vs_defense_edge).toFixed(0)} · Def vs Off ${s.defense_vs_offense_edge>=0?'+':''}${Number(s.defense_vs_offense_edge).toFixed(0)}${support} · ${role}, ${spreadText} · ${hist}`}}
function validatedRpAdvantageRow(r){const s=validatedRpSignal(r);if(!s)return null;const c=validatedRpDetail(s,r);return{category:'Returning prod.',team:s.signal_team,detail:`${c.status.label} · ${c.detail}`,rpValidated:true}}
function validatedRpDrawerHtml(r){const s=validatedRpSignal(r);if(!s)return'';const c=validatedRpDetail(s,r),tone=c.status.tone||'watch';return`<div class="validatedRpCard ${tone}"><div class="validatedRpHead"><span class="validatedRpBadge">2021–25 RP</span><b>${esc(c.status.label)}: ${esc(s.signal_team)}</b></div><div class="validatedRpRule">${esc(s.title)} · ${esc(s.primary_rule_label)}</div><div class="validatedRpEdges"><span>Overall <b>${s.overall_rp_edge>=0?'+':''}${num(s.overall_rp_edge,0)}</b></span><span>Off vs Def <b>${s.offense_vs_defense_edge>=0?'+':''}${num(s.offense_vs_defense_edge,0)}</b></span><span>Def vs Off <b>${s.defense_vs_offense_edge>=0?'+':''}${num(s.defense_vs_offense_edge,0)}</b></span></div><div class="validatedRpRead">${esc(c.status.read)}</div><div class="validatedRpHistory">${esc(c.comparisonText)} · ${esc(s.history_window)}</div></div>`}
/* VALIDATED_RP_OPENERS_CONTEXT_END */
'''
CSS=r'''
/* VALIDATED_RP_OPENERS_CSS_START */
.validatedRpCard{border:1px solid #37618f;background:#0a1e3a;border-radius:10px;padding:10px;margin:0 0 8px}.validatedRpCard.positive{border-color:#27865f;background:#0a2a2a}.validatedRpCard.neutral{border-color:#7d6a35;background:#292514}.validatedRpHead{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.validatedRpBadge{display:inline-flex;border-radius:999px;padding:3px 7px;font-size:9px;font-weight:950;color:#c9dcff;border:1px solid #4d78a8;background:#15345d}.validatedRpCard.positive .validatedRpBadge{color:#baf8d6;border-color:#27865f;background:#104b38}.validatedRpRule,.validatedRpHistory,.validatedRpRead{margin-top:5px;color:#afc1dc;font-size:10px}.validatedRpRead{color:#f4f7ff;font-weight:800}.validatedRpEdges{display:flex;gap:6px;flex-wrap:wrap;margin-top:7px}.validatedRpEdges span{border:1px solid #315780;background:#081932;border-radius:7px;padding:5px 7px;color:#a9bddb;font-size:9px}.validatedRpEdges b{color:#f4f7ff}.rpContextPill{border:1px solid #27865f;color:#a8f3cf;background:#104b38;border-radius:999px;padding:3px 7px;font-size:9px;font-weight:950;margin-left:4px}
/* VALIDATED_RP_OPENERS_CSS_END */
'''

def strip_block(t,a,b):return re.sub(re.escape(a)+r'.*?'+re.escape(b)+r'\s*','',t,flags=re.S)

def patch(path):
    t=path.read_text(errors='ignore'); backup=ROOT/'backups/ui'/f'{path.stem}_before_validated_rp_{datetime.now():%Y%m%d_%H%M%S}{path.suffix}'; backup.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(path,backup)
    t=strip_block(strip_block(t,START,END),CSS_START,CSS_END)
    if '</style>' not in t or 'function advantageRows(r){' not in t: raise RuntimeError(f'Unsupported Openers layout: {path}')
    t=t.replace('</style>',CSS+'\n</style>',1).replace('function advantageRows(r){',JS_BLOCK+'\nfunction advantageRows(r){',1)
    pat=re.compile(r"const ar=r\.teams\.away\.returning_production\?\.overall_rank,hr=r\.teams\.home\.returning_production\?\.overall_rank;rows\.push\(ar&&hr&&Math\.abs\(ar-hr\)>=20\?\{category:'Returning prod\.',team:ar<hr\?r\.game\.away_team:r\.game\.home_team,detail:`#\$\{Math\.min\(ar,hr\)\} vs #\$\{Math\.max\(ar,hr\)\} overall returning production`\}:\{category:'Returning prod\.',detail:'No major overall-rank gap'\}\);")
    t,n=pat.subn("const validatedRp=validatedRpAdvantageRow(r);rows.push(validatedRp||{category:'Returning prod.',detail:'No validated 2021–2025 RP betting rule'});",t,count=1)
    if n!=1: raise RuntimeError(f'Old RP rule not found: {path}')
    old='<div class="detail"><h3>Consolidated betting context</h3>${contextHtml(r)}'; new='<div class="detail"><h3>Consolidated betting context</h3>${validatedRpDrawerHtml(r)}${contextHtml(r)}'
    if old not in t: raise RuntimeError(f'Context block not found: {path}')
    t=t.replace(old,new,1)
    if 'adv=advantageRows(r).filter(x=>x.team).length;' not in t: raise RuntimeError(f'Context count not found: {path}')
    t=t.replace('adv=advantageRows(r).filter(x=>x.team).length;','adv=advantageRows(r).filter(x=>x.team).length,rpSignal=validatedRpSignal(r);',1)
    oldcell='<td>${adv?`<span class="contextPill">${adv} edge${adv===1?\'\':\'s\'}</span>`:\'<span class="muted">—</span>\'}</td>'
    newcell='<td>${adv?`<span class="contextPill">${adv} edge${adv===1?\'\':\'s\'}</span>`:\'<span class="muted">—</span>\'}${rpSignal?`<span class="rpContextPill">RP ${esc(rpSignal.signal_team)}</span>`:\'\'}</td>'
    if oldcell not in t: raise RuntimeError(f'Context cell not found: {path}')
    t=t.replace(oldcell,newcell,1)
    initpat=re.compile(r"async function init\(\)\{DATA=await fetch\('data/site/matchups_view\.json'\)\.then\(r=>r\.json\(\)\);")
    init="async function init(){const [matchupData,rpData]=await Promise.all([fetch('data/site/matchups_view.json',{cache:'no-store'}).then(r=>r.json()),fetch('data/site/returning_production_validated_signals_2026.json',{cache:'no-store'}).then(r=>r.ok?r.json():({meta:{},signals:[]})).catch(()=>({meta:{},signals:[]}))]);DATA=matchupData;validatedRpLoad(rpData);"
    t,n=initpat.subn(init,t,count=1)
    if n!=1: raise RuntimeError(f'init fetch not found: {path}')
    path.write_text(t); print('patched:',path); print('backup:',backup)

def update_daily():
    if not DAILY.exists():return
    cmd='python3 scripts/site/install_validated_rp_openers_context.py'
    t=DAILY.read_text()
    if cmd in t:return
    b=ROOT/'backups/scripts'/f'daily_market_update_before_validated_rp_{datetime.now():%Y%m%d_%H%M%S}.sh'; b.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(DAILY,b)
    DAILY.write_text(t.rstrip()+f"\n\n# Refresh validated 2021-2025 RP Openers context.\nif [ -f scripts/site/install_validated_rp_openers_context.py ]; then\n  {cmd}\nfi\n")
    print('updated:',DAILY)

def main():
    if not SOURCE_CSV.exists():raise FileNotFoundError(SOURCE_CSV)
    signals=consolidate(pd.read_csv(SOURCE_CSV)); write_json(signals)
    count=0
    for p in PAGES:
        if p.exists():patch(p);count+=1
    if not count:raise FileNotFoundError('No Openers HTML found')
    update_daily()
    print(f'COMPLETE: {len(signals)} consolidated RP signals across {len({x["game_id"] for x in signals})} games')

if __name__=='__main__':
    try:main()
    except Exception as e:print('ERROR:',e,file=sys.stderr);raise
