(async()=>{
  const target=document.getElementById('futures');
  if(!target)return;
  try{
    const data=await fetch('data/site/futures_view.json?v=20260826T040633Z').then(r=>r.json());
    const candidates=data.rows
      .filter(x=>Number.isFinite(Number(x.national_title_edge)))
      .sort((a,b)=>Number(b.national_title_edge)-Number(a.national_title_edge))
      .slice(0,5);
    const section=document.createElement('section');
    section.className='card';
    section.innerHTML=`<div class="head"><h2>Research — playoff markets</h2><a href="futures_v2.html">Open Playoffs</a></div>
      <div class="sectionNote">National-title prices versus simulation. Make-CFP market feed is not connected yet.</div>
      <div>${candidates.map(x=>`<div class="item"><div><b>${String(x.team)}</b><div class="sub">Win title ${(100*Number(x.national_title_model_prob)).toFixed(1)}% model · ${(100*Number(x.national_title_market_prob)).toFixed(1)}% market · ${Number(x.national_title_price)>0?'+':''}${Number(x.national_title_price)} ${String(x.national_title_book||'')}</div></div><span class="${Number(x.national_title_edge)>=0?'good':'bad'}">${Number(x.national_title_edge)>=0?'+':''}${(100*Number(x.national_title_edge)).toFixed(1)} pts</span></div>`).join('')||'<div class="empty">No comparable playoff markets.</div>'}</div>`;
    target.closest('.card').after(section);
  }catch(err){
    console.warn('Playoff dashboard block unavailable',err);
  }
})();
