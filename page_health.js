(function(){
  'use strict';
  const file=(location.pathname.split('/').pop()||'index.html').toLowerCase();
  const pageMap={'index.html':'dashboard','dashboard.html':'dashboard','ratings.html':'ratings','openers.html':'openers','matchups.html':'matchups','odds.html':'odds','schedule.html':'schedule','futures.html':'futures','conferences.html':'conferences','playoff.html':'playoff','simulations.html':'simulations','betting.html':'betting'};
  const pageId=pageMap[file];
  if(!pageId)return;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const when=v=>{if(!v)return'Unavailable';const d=new Date(v);return Number.isNaN(d.valueOf())?String(v):d.toLocaleString([],{dateStyle:'medium',timeStyle:'short'})};
  const insertPoint=()=>document.querySelector('.hero')||document.querySelector('.site-nav')||document.querySelector('h1')?.parentElement;
  function render(p){
    (p.legacy_status_selectors||[]).forEach(selector=>document.querySelectorAll(selector).forEach(el=>{el.hidden=true;el.setAttribute('aria-hidden','true')}));
    const warnings=[...(p.critical_failures||[]),...(p.warnings||[]),...(p.unavailable_reasons||[])];
    const metrics=(p.metrics||[]).map(m=>`<div class="page-health__metric" title="${esc(m.detail||m.label)}"><span>${esc(m.label)}</span><b>${esc(m.value)}</b></div>`).join('');
    const sources=(p.source_artifacts||[]).map(s=>`<li><code>${esc(s)}</code></li>`).join('');
    const notes=warnings.length?warnings.map(w=>`<li>${esc(w)}</li>`).join(''):'<li>No warnings.</li>';
    const el=document.createElement('section');el.className='page-health';el.dataset.status=p.status;el.id='page-health-summary';el.setAttribute('aria-label',`${p.display_name} data health: ${p.status_label}`);
    el.innerHTML=`<div class="page-health__top"><span class="page-health__dot" aria-hidden="true"></span><span class="page-health__name">Data health</span><span class="page-health__label">${esc(p.status_label)} (${esc(String(p.status).toUpperCase())})</span><span class="page-health__summary">${esc(p.summary)}</span><span class="page-health__time">Data ${esc(when(p.last_success_at))} · Health built ${esc(when(window.PAGE_HEALTH_BUILT_AT))}</span></div><div class="page-health__metrics">${metrics}</div><details><summary>Details and provenance</summary><div class="page-health__details"><div><b>Warnings / availability</b><ul>${notes}</ul></div><div><b>Source artifacts</b><ul>${sources}</ul></div></div></details>`;
    const point=insertPoint();if(point)point.insertAdjacentElement('afterend',el);else document.body.prepend(el);
  }
  fetch('data/site/page_health_status.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json()}).then(data=>{window.PAGE_HEALTH_BUILT_AT=data.built_at;const p=(data.pages||[]).find(x=>x.page_id===pageId);if(!p)throw new Error(`No health record for ${pageId}`);render(p)}).catch(error=>{const point=insertPoint(),el=document.createElement('section');el.className='page-health page-health--error';el.dataset.status='red';el.id='page-health-summary';el.setAttribute('aria-label','Data health unavailable');el.innerHTML=`<div class="page-health__top"><span class="page-health__dot" aria-hidden="true"></span><span class="page-health__label">Health status unavailable (RED)</span><span class="page-health__summary">${esc(error.message)}</span></div>`;(point||document.body).insertAdjacentElement(point?'afterend':'afterbegin',el)});
})();
