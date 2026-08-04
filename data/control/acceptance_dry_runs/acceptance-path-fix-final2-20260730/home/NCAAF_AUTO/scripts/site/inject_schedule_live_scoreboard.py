#!/usr/bin/env python3
from __future__ import annotations
import json,re,shutil
from pathlib import Path

ROOT=Path.home()/"NCAAF_AUTO"
PAGE=ROOT/"schedule_v2.html"
DATA=ROOT/"data/site/schedule_live_enrichment.json"
START="<!-- SCHEDULE_LIVE_SCOREBOARD_START -->"
END="<!-- SCHEDULE_LIVE_SCOREBOARD_END -->"

def make_block():
    payload=json.loads(DATA.read_text()) if DATA.exists() else {"games":[]}
    data=json.dumps(payload)
    template=r'''__START__
<style>
.schedule-title-line{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.schedule-rules-inline{margin:0!important}
.schedule-replay-hidden{display:none!important}
.schedule-live-status{font-weight:800}
.schedule-live-status[data-status="Complete"]{color:#34d399}
.schedule-live-status[data-status="Partial"]{color:#fbbf24}
.schedule-live-status[data-status="Pending"]{color:#94a3b8}
.schedule-live-impact-pos{color:#34d399;font-weight:800}
.schedule-live-impact-neg{color:#fb7185;font-weight:800}
.schedule-detail-row td{padding:0!important}
.schedule-detail-panel{padding:14px 18px;background:rgba(15,23,42,.7);border-top:1px solid rgba(148,163,184,.18)}
.schedule-detail-grid{display:grid;grid-template-columns:repeat(4,minmax(180px,1fr));gap:10px 18px}
.schedule-detail-item{font-size:13px}
.schedule-detail-label{display:block;opacity:.62;font-size:11px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px}
.schedule-clickable-row{cursor:pointer}
.schedule-clickable-row:hover{background:rgba(59,130,246,.07)}
@media(max-width:1000px){.schedule-detail-grid{grid-template-columns:repeat(2,minmax(160px,1fr))}}
</style>
<script id="schedule-live-enrichment-data" type="application/json">__DATA__</script>
<script>
(function(){
 const payload=JSON.parse(document.getElementById('schedule-live-enrichment-data').textContent);
 const games=payload.games||[];
 const norm=s=>(s||'').toString().trim().toLowerCase().replace(/\s+/g,' ');
 const byTeams=new Map(games.map(g=>[norm(`${g.away_team} at ${g.home_team}`),g]));
 const num=(v,d=1)=>Number.isFinite(Number(v))?Number(v).toFixed(d):'—';
 const impactClass=v=>Number(v)>0?'schedule-live-impact-pos':Number(v)<0?'schedule-live-impact-neg':'';
 function findTable(){return [...document.querySelectorAll('table')].find(t=>{const h=[...t.querySelectorAll('thead th')].map(x=>norm(x.textContent));return h.some(x=>x.includes('matchup'))&&h.some(x=>x.includes('spread'));});}
 function moveRules(){
   const h1=[...document.querySelectorAll('h1')].find(x=>norm(x.textContent).includes('schedule'));
   const btn=[...document.querySelectorAll('button,a')].find(x=>norm(x.textContent).includes('saturday rules'));
   if(h1&&btn&&!h1.parentElement.classList.contains('schedule-title-line')){
     const wrap=document.createElement('div');wrap.className='schedule-title-line';
     h1.parentNode.insertBefore(wrap,h1);wrap.appendChild(h1);btn.classList.add('schedule-rules-inline');wrap.appendChild(btn);
   }
 }
 function hideReplay(){
   const title=[...document.querySelectorAll('h2,h3,div')].find(x=>norm(x.textContent)==='historical saturday shadow replay');
   if(title){const card=title.closest('section,.card,[class*="panel"],[class*="card"]')||title.parentElement;if(card)card.classList.add('schedule-replay-hidden');}
 }
 function parseKickoff(raw,dateRaw){if(!raw)return null;let d=new Date(raw);if(!Number.isNaN(d.getTime()))return d;if(dateRaw){d=new Date(`${dateRaw} ${raw}`);if(!Number.isNaN(d.getTime()))return d;}return null;}
 function fmtDate(g,existing){const d=parseKickoff(g.kickoff_raw,g.date);if(!d)return `${existing.split('\n')[0]||g.date||''}<br><span class="muted">TBD</span>`;const date=d.toLocaleDateString('en-US',{month:'numeric',day:'numeric'});const time=d.toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit',timeZone:'America/New_York'});return `${date}<br><strong>${time} ET</strong>`;}
 function detailHtml(g){
   const items=[['Opening spread',g.opening_spread],['Closing spread',g.closing_spread],['Opening total',g.opening_total],['Closing total',g.closing_total],['Market baseline spread',g.market_baseline_spread],['Raw spread delta',g.raw_spread_delta],['Applied spread impact',g.spread_impact],['Next shadow spread',g.next_projection_spread],['Market baseline total',g.market_baseline_total],['Raw total/PBP delta',g.raw_total_delta],['Applied total impact',g.total_impact],['Next shadow total',g.next_projection_total],['CFBD status',g.cfbd_status||'Pending'],['PBP status',g.pbp_status||'Pending'],['Spread status',g.spread_status||'Pending'],['Total status',g.total_status||'Pending']];
   return `<div class="schedule-detail-panel"><div class="schedule-detail-grid">${items.map(([l,v])=>`<div class="schedule-detail-item"><span class="schedule-detail-label">${l}</span>${v===null||v===undefined?'—':v}</div>`).join('')}</div></div>`;
 }
 function enhance(){
   moveRules();hideReplay();
   const table=findTable();if(!table||table.dataset.liveEnhanced==='1')return;
   const hs=[...table.querySelectorAll('thead th')], map={};hs.forEach((h,i)=>map[norm(h.textContent)]=i);
   const idx=k=>Object.entries(map).find(([x])=>x.includes(k))?.[1];
   const cfbd=idx('cfbd'),pbp=idx('pbp'),ready=idx('ready'),date=idx('date'),matchup=idx('matchup');
   if(cfbd!=null)hs[cfbd].style.display='none';if(pbp!=null)hs[pbp].style.display='none';
   if(ready!=null)hs[ready].textContent='DATA STATUS';if(date!=null)hs[date].textContent='DATE / TIME';
   const anchor=ready!=null?hs[ready]:null;
   ['SPREAD IMPACT','TOTAL IMPACT','NEXT PROJECTION'].forEach(label=>{const th=document.createElement('th');th.textContent=label;hs[0].parentNode.insertBefore(th,anchor);});
   const rows=[...table.querySelectorAll('tbody tr')];
   rows.forEach(row=>{
     const cells=[...row.children], text=matchup!=null?norm(cells[matchup]?.textContent):'';
     let g=null;for(const [key,val] of byTeams.entries()){if(text.includes(key)){g=val;break;}}
     if(!g)return;
     row.classList.add('schedule-clickable-row');
     if(cfbd!=null&&cells[cfbd])cells[cfbd].style.display='none';if(pbp!=null&&cells[pbp])cells[pbp].style.display='none';
     if(date!=null&&cells[date])cells[date].innerHTML=fmtDate(g,cells[date].innerText);
     const statusCell=ready!=null?cells[ready]:null;
     if(statusCell)statusCell.innerHTML=`<span class="schedule-live-status" data-status="${g.data_status||'Pending'}">${g.data_status||'Pending'}</span>`;
     const spread=document.createElement('td');spread.className=impactClass(g.spread_impact);spread.textContent=num(g.spread_impact);
     const total=document.createElement('td');total.className=impactClass(g.total_impact);total.textContent=num(g.total_impact);
     const next=document.createElement('td');next.innerHTML=`<strong>${num(g.next_projection_spread)}</strong><br><span class="muted">${num(g.next_projection_total)}</span>`;
     row.insertBefore(spread,statusCell);row.insertBefore(total,statusCell);row.insertBefore(next,statusCell);
     const kickoff=parseKickoff(g.kickoff_raw,g.date);row.dataset.sortTime=kickoff?String(kickoff.getTime()):'9999999999999';
     row.addEventListener('click',e=>{if(e.target.closest('button,a,input,select'))return;const n=row.nextElementSibling;if(n&&n.classList.contains('schedule-detail-row')){n.remove();return;}const d=document.createElement('tr');d.className='schedule-detail-row';const td=document.createElement('td');td.colSpan=row.children.length;td.innerHTML=detailHtml(g);d.appendChild(td);row.parentNode.insertBefore(d,row.nextSibling);});
   });
   rows.sort((a,b)=>Number(a.dataset.sortTime||9e15)-Number(b.dataset.sortTime||9e15)).forEach(r=>table.tBodies[0].appendChild(r));
   table.dataset.liveEnhanced='1';
 }
 let timer=null;const obs=new MutationObserver(()=>{clearTimeout(timer);timer=setTimeout(enhance,80);});obs.observe(document.documentElement,{subtree:true,childList:true});enhance();
})();
</script>
__END__'''
    return template.replace('__START__',START).replace('__END__',END).replace('__DATA__',data)

def main():
    if not PAGE.exists(): raise SystemExit(f"Missing: {PAGE}")
    backup=ROOT/"backups/ui/schedule_v2_before_live_scoreboard_v1.html"
    backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(PAGE,backup)
    text=PAGE.read_text(encoding="utf-8",errors="ignore"); b=make_block()
    if START in text and END in text:
      text=re.sub(re.escape(START)+r".*?"+re.escape(END),lambda _m:b,text,flags=re.S)
    else:
      text=text.replace("</body>",b+"\n</body>")
    PAGE.write_text(text,encoding="utf-8")
    print("patched:",PAGE);print("backup:",backup)
if __name__=="__main__": main()
