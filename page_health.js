(function(){
  'use strict';

  const file=(location.pathname.split('/').pop()||'index.html').toLowerCase();

  const pageMap={
    'index.html':'dashboard',
    'dashboard.html':'dashboard',
    'ratings.html':'ratings',
    'openers.html':'openers',
    'matchups.html':'matchups',
    'odds.html':'odds',
    'schedule.html':'schedule',
    'futures.html':'futures',
    'conferences.html':'conferences',
    'playoff.html':'playoff',
    'simulations.html':'simulations',
    'betting.html':'betting'
  };

  const pageId=pageMap[file];
  if(!pageId)return;

  const esc=v=>String(v??'').replace(
    /[&<>"']/g,
    c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])
  );

  const when=v=>{
    if(!v)return'Unavailable';
    const d=new Date(v);
    if(Number.isNaN(d.valueOf()))return String(v);
    return d.toLocaleString('en-US',{
      timeZone:'America/New_York',
      month:'short',
      day:'numeric',
      year:'numeric',
      hour:'numeric',
      minute:'2-digit'
    })+' ET';
  };

  function healthControl(){
    return (
      document.querySelector('.war-room-health') ||
      document.querySelector('.header-right .health') ||
      document.querySelector('header .health')
    );
  }

  function removeLegacyBodyHealth(){
    document.querySelectorAll('#page-health-summary,.page-health').forEach(el=>{
      if(!el.classList.contains('page-health-popover')) el.remove();
    });
  }

  function buildPopover(p){
    document.getElementById('page-health-popover')?.remove();

    const warnings=[
      ...(p.critical_failures||[]),
      ...(p.warnings||[]),
      ...(p.unavailable_reasons||[])
    ];

    const metrics=(p.metrics||[])
      .map(m=>`
        <div class="page-health-popover__metric">
          <span>${esc(m.label)}</span>
          <b>${esc(m.value)}</b>
        </div>
      `).join('');

    const notes=warnings.length
      ? warnings.map(w=>`<li>${esc(w)}</li>`).join('')
      : '<li>No warnings.</li>';

    const sources=(p.source_artifacts||[])
      .map(s=>`<li><code>${esc(s)}</code></li>`).join('');

    const panel=document.createElement('div');
    panel.id='page-health-popover';
    panel.className='page-health-popover';
    panel.dataset.status=p.status;

    panel.innerHTML=`
      <div class="page-health-popover__head">
        <div>
          <b>${esc(p.display_name)} data health</b>
          <span>${esc(p.status_label)}</span>
        </div>
        <button type="button" class="page-health-popover__close" aria-label="Close">×</button>
      </div>

      <div class="page-health-popover__summary">${esc(p.summary)}</div>

      <div class="page-health-popover__metrics">${metrics}</div>

      <div class="page-health-popover__time">
        Data ${esc(when(p.last_success_at))}<br>
        Health built ${esc(when(window.PAGE_HEALTH_BUILT_AT))}
      </div>

      <details>
        <summary>Warnings and provenance</summary>
        <div class="page-health-popover__details">
          <div>
            <b>Warnings / availability</b>
            <ul>${notes}</ul>
          </div>
          <div>
            <b>Source artifacts</b>
            <ul>${sources}</ul>
          </div>
        </div>
      </details>
    `;

    document.body.appendChild(panel);

    panel.querySelector('.page-health-popover__close').onclick=()=>{
      panel.remove();
      const c=healthControl();
      if(c)c.setAttribute('aria-expanded','false');
    };

    return panel;
  }

  function render(p){
    removeLegacyBodyHealth();

    (p.legacy_status_selectors||[]).forEach(selector=>{
      document.querySelectorAll(selector).forEach(el=>{
        el.hidden=true;
        el.setAttribute('aria-hidden','true');
      });
    });

    const control=healthControl();
    if(!control)return;

    control.dataset.status=p.status;
    control.classList.add('page-health-control');
    control.setAttribute('role','button');
    control.setAttribute('tabindex','0');
    control.setAttribute('aria-expanded','false');
    control.setAttribute(
      'aria-label',
      `${p.display_name} data health: ${p.status_label}. Activate for details.`
    );

    const label =
      p.status==='green' ? 'Data Healthy' :
      p.status==='yellow' ? 'Data Warning' :
      p.status==='red' ? 'Data Issue' :
      'Data Status';

    control.innerHTML=`<i></i><span>${esc(label)}</span>`;

    const toggle=()=>{
      const existing=document.getElementById('page-health-popover');

      if(existing){
        existing.remove();
        control.setAttribute('aria-expanded','false');
        return;
      }

      buildPopover(p);
      control.setAttribute('aria-expanded','true');
    };

    control.onclick=toggle;
    control.onkeydown=e=>{
      if(e.key==='Enter'||e.key===' '){
        e.preventDefault();
        toggle();
      }
    };
  }

  fetch('data/site/page_health_status.json',{cache:'no-store'})
    .then(r=>{
      if(!r.ok)throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then(data=>{
      window.PAGE_HEALTH_BUILT_AT=data.built_at;
      const p=(data.pages||[]).find(x=>x.page_id===pageId);
      if(!p)throw new Error(`No health record for ${pageId}`);
      render(p);
    })
    .catch(error=>{
      removeLegacyBodyHealth();

      const control=healthControl();
      if(!control)return;

      control.dataset.status='red';
      control.classList.add('page-health-control');
      control.innerHTML='<i></i><span>Data Issue</span>';
      control.title=`Health status unavailable: ${error.message}`;
    });
})();
