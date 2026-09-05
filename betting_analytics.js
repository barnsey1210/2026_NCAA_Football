(()=>{
'use strict';
const CONTRACT='data/site/historical_betting_analytics_v2.json?v=20260905T001143Z',ORDER_FALLBACK=[],$=id=>document.getElementById(id),pct=v=>v==null?'N/A':(Number(v)*100).toFixed(1)+'%',signed=(v,d=2)=>v==null?'N/A':(Number(v)>0?'+':'')+Number(v).toFixed(d),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let C;
const models=m=>C.models.filter(x=>x.market_type===m&&x.historical_validation!=='LIMITED_PROVENANCE_NOT_EQUIVALENT'),rows=(m,id)=>C.independent_checkpoint_performance.filter(x=>x.market_type===m&&x.model_id===id);
function table(market,title){const root=[...document.querySelectorAll('.histCard')].find(x=>x.querySelector('h2')?.textContent.trim()===title);if(!root)return;const box=document.createElement('div');box.className='histInlineControls';box.innerHTML='<select aria-label="Historical model"></select><select aria-label="Historical checkpoint"></select>';root.querySelector('.histHead>div').appendChild(box);const ms=box.children[0],cs=box.children[1];ms.innerHTML=models(market).map(x=>`<option value="${esc(x.model_id)}">${esc(x.label)}</option>`).join('');ms.value=C.default_selection[market].model_id;
 function checkpoints(){const have=[...new Set(rows(market,ms.value).map(x=>x.checkpoint))];cs.innerHTML=C.checkpoint_order.filter(x=>have.includes(x)).map(x=>`<option value="${x}">${x.replaceAll('_',' ')}</option>`).join('');cs.value=have.includes(C.default_selection[market].checkpoint)?C.default_selection[market].checkpoint:have[0];render()}
 function render(){const data=rows(market,ms.value).filter(x=>x.checkpoint===cs.value).sort((a,b)=>a.threshold-b.threshold),body=root.querySelector('tbody'),model=C.models.find(x=>x.model_id===ms.value);body.innerHTML=data.map(r=>`<tr class="${r.threshold===3?'histActionRow':''} ${r.sample_strength==='VERY_SMALL_INSUFFICIENT'?'histTinySample':''}" title="Sample strength: ${esc(r.sample_strength||'unclassified')}"><td><b>${r.threshold}+</b></td><td>${r.n.toLocaleString()}</td><td>${esc(r.record)}</td><td>${pct(r.win_pct)}</td><td class="${Number(r.roi)>=0?'histPositive':'histNegative'}">${pct(r.roi)}</td><td>${pct(r.beat_close_pct)}</td><td>${pct(r.won_line_move_pct)}</td><td class="histEmphasis">${signed(r.avg_clv)}</td><td>N/A</td></tr>`).join('')||'<tr><td colspan="9">No preserved sample at this checkpoint.</td></tr>';root.querySelector('.histHead small').textContent=`2021–2025 · ${model.label} · ${cs.value.replaceAll('_',' ')} · ${data[0]?.sample_classification||'preserved sample'}`}
 ms.onchange=checkpoints;cs.onchange=render;checkpoints()}
const METRICS={independent:{win_pct:'ATS / O-U Win %',roi:'ROI',avg_clv:'Avg CLV',beat_close_pct:'Beat Close %',won_line_move_pct:'Won Line Move %',n:'Sample N',avg_edge:'Average Edge'},matched:{mean_remaining_edge:'Mean Remaining Edge',remaining_edge_pct:'Original Edge Remaining %',edge_persistence_pct:'Threshold Persistence %',positive_edge_persistence_pct:'Positive-Edge Persistence %',same_side_persistence_pct:'Same-Side Persistence %',reversal_pct:'Reversal %',roi:'Origin Wager ROI',avg_clv:'Origin Wager Avg CLV',n:'Sample N'}};
function options(el,items,value){el.innerHTML=items.map(x=>`<option value="${esc(x.value)}">${esc(x.label)}</option>`).join('');if(value!=null)el.value=value}
function graph(){const market=$('decayMarket'),model=$('decayModel'),threshold=$('decayThreshold'),mode=$('decayMode'),origin=$('decayOrigin'),metric=$('decayMetric');
 function resetModels(){options(model,models(market.value).map(x=>({value:x.model_id,label:x.label})),C.default_selection[market.value].model_id);resetThresholds()}
 function resetThresholds(){const x=[...new Set(rows(market.value,model.value).map(r=>r.threshold))].sort((a,b)=>a-b);options(threshold,x.map(v=>({value:v,label:v+'+'})),C.default_selection[market.value].threshold);resetOrigins()}
 function resetOrigins(){const x=[...new Set(C.matched_signal_decay.filter(r=>r.market_type===market.value&&r.model_id===model.value&&Number(r.threshold)===Number(threshold.value)).map(r=>r.origin_checkpoint))];options(origin,x.map(v=>({value:v,label:'Origin '+v.replaceAll('_',' ')})),x.includes(C.default_selection[market.value].checkpoint)?C.default_selection[market.value].checkpoint:x[0]);resetMetrics()}
 function resetMetrics(){options(metric,Object.entries(METRICS[mode.value]).map(([value,label])=>({value,label})),mode.value==='independent'?'roi':'edge_persistence_pct');origin.hidden=mode.value!=='matched';render()}
 function render(){let data=mode.value==='independent'?rows(market.value,model.value).filter(r=>Number(r.threshold)===Number(threshold.value)):C.matched_signal_decay.filter(r=>r.market_type===market.value&&r.model_id===model.value&&Number(r.threshold)===Number(threshold.value)&&r.origin_checkpoint===origin.value);data=data.filter(r=>r[metric.value]!=null);if(!data.length){$('decayChart').innerHTML='<div class="modelEmpty">No preserved sample for this selection.</div>';return}const order=C.checkpoint_order,W=920,H=250,pad=42,idx=r=>order.indexOf(r.checkpoint),vals=data.map(r=>Number(r[metric.value])),lo=Math.min(...vals),hi=Math.max(...vals),range=hi-lo||1,x=r=>pad+idx(r)*(W-pad*2)/(order.length-1),y=v=>H-pad-(v-lo)/range*(H-pad*2),map=new Map(data.map(r=>[idx(r),r]));let lines='';for(let i=0;i<order.length-1;i++)if(map.has(i)&&map.has(i+1)){const a=map.get(i),b=map.get(i+1);lines+=`<line class="decayLine" x1="${x(a)}" y1="${y(a[metric.value])}" x2="${x(b)}" y2="${y(b[metric.value])}"/>`}const isPct=['win_pct','roi','beat_close_pct','won_line_move_pct','remaining_edge_pct','edge_persistence_pct','positive_edge_persistence_pct','same_side_persistence_pct','reversal_pct'].includes(metric.value),points=data.map(r=>{const v=Number(r[metric.value]),display=metric.value==='n'?r.n.toLocaleString():isPct?pct(v):signed(v);return `<g><circle class="decayPoint" cx="${x(r)}" cy="${y(v)}" r="5"/><text class="decayValue" x="${x(r)}" y="${y(v)-10}" text-anchor="middle">${display}</text><text class="decayLabel" x="${x(r)}" y="${H-12}" text-anchor="middle">${r.checkpoint.replaceAll('_ET','').replaceAll('_',' ')}</text><text class="decayLabel" x="${x(r)}" y="${y(v)+18}" text-anchor="middle">N ${r.n}</text></g>`}).join('');$('decayChart').innerHTML=`<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none"><line class="decayAxis" x1="${pad}" y1="${H-pad}" x2="${W-pad}" y2="${H-pad}"/>${lines}${points}</svg>`;$('decayCoverage').textContent=market.value==='spread'?C.coverage.spread:C.coverage.total;$('decayNote').textContent=(mode.value==='independent'?'Fresh signals are independently selected at each checkpoint.':'Matched origin cohort keeps the original game, wager side, line, and threshold fixed through later checkpoints.')+' CLV-implied EV remains N/A without validated calibration.'}
 market.onchange=resetModels;model.onchange=resetThresholds;threshold.onchange=resetOrigins;mode.onchange=resetMetrics;origin.onchange=render;metric.onchange=render;resetModels()}
fetch(CONTRACT).then(r=>{if(!r.ok)throw Error(r.status);return r.json()}).then(x=>{C=x;table('spread','Historical Spread Edge Validation');table('total','Historical Totals Edge Validation');graph()}).catch(e=>{$('decayChart').innerHTML=`<div class="modelEmpty">Historical analytics unavailable: ${esc(e.message)}</div>`});
})();

(()=>{'use strict';const P='data/site/historical_betting_explorer_v1.json?v=20260905T001143Z',A='data/site/historical_betting_analytics_v2.json?v=20260905T001143Z',q=id=>document.getElementById(id);if(!q('historicalExplorer'))return;let X,H,R=[];const dims={week:r=>'W'+r.week,checkpoint:r=>r.checkpoint.replaceAll('_ET','').replaceAll('_',' '),season:r=>String(r.season),edge:r=>{const e=Math.abs(r.edge);return e>=10?'10+':e>=8?'8–9.99':e>=6?'6–7.99':e>=5?'5–5.99':e>=4?'4–4.99':e>=3?'3–3.99':e>=2?'2–2.99':e>=1?'1–1.99':'0.5–0.99'}};const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function decode(){const d=X.dictionaries,cols=X.columns;R=X.records.map(a=>{const o={};cols.forEach((c,i)=>o[c]=d[c]&&a[i]!=null?d[c][a[i]]:a[i]);return o})}
function options(el,items,all){el.innerHTML=(all?`<option value="all">${all}</option>`:'')+items.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join('')}
function strength(n){return n>=100?'NORMAL':n>=50?'LIMITED':n>=20?'SMALL':'VERY SMALL / INSUFFICIENT'}
function aggregate(a){const n=a.length,w=a.filter(x=>x.result>0).length,l=a.filter(x=>x.result<0).length,p=n-w-l,dec=w+l,clv=a.filter(x=>x.clv!=null),moves=clv.filter(x=>Math.abs(x.clv)>1e-9);return{n,w,l,p,record:`${w}-${l}-${p}`,ats:dec?w/dec:null,roi:n?a.reduce((s,x)=>s+(Number(x.realized_profit)||0),0)/n:null,clv:clv.length?clv.reduce((s,x)=>s+Number(x.clv),0)/clv.length:null,beat:clv.length?clv.filter(x=>x.clv>0).length/clv.length:null,move:moves.length?moves.filter(x=>x.clv>0).length/moves.length:null}}
function filtered(){const model=q('exModel').value,season=q('exSeason').value,week=q('exWeek').value,edge=Number(q('exEdge').value),cp=q('exCheckpoint').value,ev=q('exEvidence').value;return R.filter(r=>r.model_id===model&&(season==='all'||r.season===Number(season))&&(cp==='all'||r.checkpoint===cp)&&(ev==='all'||r.evidence_class===ev)&&Math.abs(r.edge)>=edge&&(week==='all'||week==='0-2'&&r.week<=2||week==='0-4'&&r.week<=4||week==='3-4'&&r.week>=3&&r.week<=4||week==='5+'&&r.week>=5||week.startsWith('W')&&r.week===Number(week.slice(1))))}
function fmt(v,m){if(v==null)return'—';if(m==='n'||m==='record')return v;if(['ats','roi','beat','move'].includes(m))return(v*100).toFixed(1)+'%';return(Number(v)>0?'+':'')+Number(v).toFixed(2)}
function color(v,m,n){if(m==='n')return`rgba(52,152,219,${Math.min(.75,n/150)})`;if(m==='record')return'';const center=m==='ats'?.5:0,x=Math.max(-1,Math.min(1,(Number(v)-center)/(m==='ats'?.12:m==='roi'?.2:m==='clv'?2:.3)));return x>=0?`rgba(35,170,100,${.12+.6*x})`:`rgba(220,70,70,${.12-.6*x})`}
function renderCheckpoint(){
 const data=filtered(),rd=q('exRows').value,cd=q('exCols').value,m=q('exMetric').value;
 if(rd===cd){q('exCols').value=cd=rd==='checkpoint'?'week':'checkpoint'}

 const weekDomain=()=>{
  const w=q('exWeek').value;
  if(w==='0-2')return ['W0','W1','W2'];
  if(w==='0-4')return ['W0','W1','W2','W3','W4'];
  if(w==='3-4')return ['W3','W4'];
  if(w==='5+')return X.week_domain.filter(x=>x>=5).map(x=>'W'+x);
  if(w.startsWith('W'))return [w];
  return X.week_domain.map(x=>'W'+x);
 };

 const domain=d=>
  d==='week'
   ?weekDomain()
   :d==='checkpoint'
    ?X.checkpoint_order.map(x=>dims.checkpoint({checkpoint:x}))
    :[...new Set(data.map(dims[d]))].sort((a,b)=>String(a).localeCompare(String(b),undefined,{numeric:true}));

 const rv=domain(rd),cv=domain(cd);
 const TOTAL='__TOTAL__';

 const cellData=(r,c)=>{
  if(r===TOTAL&&c===TOTAL)return data;
  if(r===TOTAL)return data.filter(x=>dims[cd](x)===c);
  if(c===TOTAL)return data.filter(x=>dims[rd](x)===r);
  return data.filter(x=>dims[rd](x)===r&&dims[cd](x)===c);
 };

 const cell=(r,c,isTotal=false)=>{
  const z=cellData(r,c),a=aggregate(z),v=a[m];
  return `<td class="explorerCell ${a.n<20?'sampleTiny':''}" data-r="${esc(r)}" data-c="${esc(c)}" style="background:${color(v,m,a.n)};${isTotal?'font-weight:700;':''}" title="N ${a.n} · ${a.record} · ${strength(a.n)}">${fmt(v,m)}</td>`;
 };

 q('exHead').innerHTML=
  '<tr><th>'+esc(rd)+'</th>'+
  cv.map(x=>`<th>${esc(x)}</th>`).join('')+
  '<th style="font-weight:700">TOTAL</th></tr>';

 q('exBody').innerHTML=
  rv.map(r=>
   '<tr><th>'+esc(r)+'</th>'+
   cv.map(c=>cell(r,c)).join('')+
   cell(r,TOTAL,true)+
   '</tr>'
  ).join('')+
  '<tr><th style="font-weight:700">TOTAL</th>'+
  cv.map(c=>cell(TOTAL,c,true)).join('')+
  cell(TOTAL,TOTAL,true)+
  '</tr>';

 q('explorerStatus').textContent=`${data.length.toLocaleString()} qualifying states`;
 q('exNote').textContent='Checkpoint Performance: fresh qualifying signals are selected independently at each timestamp. TOTAL cells are recalculated from the underlying qualifying states. Dotted cells have N < 20.';

 q('exBody').querySelectorAll('td').forEach(td=>{
  td.onclick=()=>details(cellData(td.dataset.r,td.dataset.c));
 });

 chart(data,m);
}
function renderMatched(){const model=q('exModel').value,t=Number(q('exEdge').value),rows=H.matched_signal_decay.filter(x=>x.model_id===model&&Number(x.threshold)===t);q('exHead').innerHTML='<tr><th>Origin</th><th>Later checkpoint</th><th>N</th><th>Edge persistence</th><th>Reversal</th><th>AVG CLV</th><th>ROI</th></tr>';q('exBody').innerHTML=rows.map(r=>`<tr><th>${esc(r.origin_checkpoint)}</th><td>${esc(r.checkpoint)}</td><td>${r.n}</td><td>${fmt(r.edge_persistence_pct,'ats')}</td><td>${fmt(r.reversal_pct,'ats')}</td><td>${fmt(r.avg_clv,'clv')}</td><td>${fmt(r.roi,'roi')}</td></tr>`).join('');q('exNote').textContent='Fixed-Origin Matched Decay: the same game, origin side, origin wager, and threshold are followed. Opposite-side signals are reversals, never persistence.';q('explorerStatus').textContent=`${rows.length} corrected matched states`;q('exChart').innerHTML='';q('exDetails').innerHTML=''}
function common(){const z=H.common_sample_spread_comparison.filter(x=>Number(x.threshold)===3&&x.checkpoint==='SUN_9AM_ET');q('exCommon').innerHTML='<details><summary>Corrected 4-source vs 5-source common-sample comparison</summary><div class="explorerWrap"><table class="explorerTable"><thead><tr><th>Cohort</th><th>Model</th><th>N</th><th>Record</th><th>ROI</th><th>Same side</th><th>Disagreements</th></tr></thead><tbody>'+z.map(r=>`<tr><td>${esc(r.cohort)}</td><td>${esc(r.evaluated_model_id)}</td><td>${r.n}</td><td>${esc(r.record)}</td><td>${fmt(r.roi,'roi')}</td><td>${r.same_side_count??'—'}</td><td>${r.disagreement_count??'—'}</td></tr>`).join('')+'</tbody></table></div></details>'}
function render(){q('exMode').value==='matched'?renderMatched():renderCheckpoint()}
Promise.all([fetch(P).then(r=>r.json()),fetch(A).then(r=>r.json())]).then(([x,h])=>{X=x;H=h;decode();options(q('exModel'),Object.entries(X.models).map(([k,v])=>k+'|'+v.label));q('exModel').innerHTML=Object.entries(X.models).map(([k,v])=>`<option value="${k}">${esc(v.label)}</option>`).join('');q('exModel').value=X.default.model_id;options(q('exSeason'),[2021,2022,2023,2024,2025], '2021–2025 / All');for(let w=0;w<=16;w++)q('exWeek').insertAdjacentHTML('beforeend',`<option value="W${w}">Week ${w}</option>`);options(q('exEdge'),X.thresholds.map(x=>x+'+'));q('exEdge').innerHTML=X.thresholds.map(x=>`<option value="${x}">${x}+</option>`).join('');q('exEdge').value='3';options(q('exCheckpoint'),X.checkpoint_order,'All valid checkpoints');options(q('exEvidence'),[...new Set(R.map(x=>x.evidence_class).filter(Boolean))].sort(),'All evidence classes');['exMode','exModel','exSeason','exWeek','exEdge','exCheckpoint','exEvidence','exRows','exCols','exMetric'].forEach(id=>q(id).onchange=render);common();render()}).catch(e=>q('explorerStatus').textContent='Unavailable: '+e.message);
})();
