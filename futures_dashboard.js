(function(){
'use strict';

const BOOKS=['DraftKings','FanDuel','BetMGM','Caesars','Kalshi'];
const BOOK_SLUG={
  DraftKings:'draftkings',
  FanDuel:'fanduel',
  BetMGM:'betmgm',
  Caesars:'caesars',
  Kalshi:'kalshi'
};

let state={
  mode:'wins',
  conference:'all',
  search:'',
  sortKey:'rank',
  sortDir:'asc',
  selectedTeam:null,
  mobileExpandedTeam:null,
  railTab:'overview',
  scenario:{
    loaded:false,
    loading:false,
    error:null,
    universe:null,
    selections:{},
    openGames:[],
    baseline:null,
    current:null,
    leverageByTeam:null
  }
};

const mobileSortState={
  wins:{key:'edge',dir:'desc'},
  title:{key:'edge',dir:'desc'},
  cfp:{key:'edge',dir:'desc'},
  national:{key:'edge',dir:'desc'}
};

const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
}[c]));

const hasNumber=v=>
  v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v));

const num=(v,d=1)=>hasNumber(v)?Number(v).toFixed(d):'—';
const pct=v=>hasNumber(v)?`${(Number(v)*100).toFixed(1)}%`:'—';
const odds=v=>hasNumber(v)?`${Number(v)>0?'+':''}${Math.round(Number(v))}`:'—';
const quoteOdds=(q,side)=>{
  const price=q?.price??(side==='Under'?q?.under_price:q?.over_price);
  const native=q?.native_ask_cents??(side==='Under'?q?.under_native_ask_cents:q?.over_native_ask_cents);
  return q?.provider_type==='exchange'&&hasNumber(native)
    ? `${Number(native).toLocaleString('en-US',{maximumFractionDigits:2})}¢ (${odds(price)})`
    : odds(price);
};


const SCENARIO_UNIVERSE_URL='data/site/futures_scenario_universe_2026.json';

function decodeB64(value){
  const raw=atob(value||'');
  const out=new Uint8Array(raw.length);
  for(let i=0;i<raw.length;i++)out[i]=raw.charCodeAt(i);
  return out;
}

function scenarioBit(buffer,offset,index){
  return Boolean(
    buffer[offset+(index>>3)] & (1<<(index&7))
  );
}

function scenarioSelectionCount(){
  return Object.keys(state.scenario.selections||{}).length;
}

function scenarioActive(){
  return Boolean(
    state.scenario.loaded &&
    state.scenario.current &&
    scenarioSelectionCount()
  );
}

function scenarioSampleLabel(count){
  if(count<=0)return'NO MATCH';
  if(count<100)return'VERY THIN';
  if(count<500)return'THIN';
  if(count<2000)return'GOOD';
  return'STRONG';
}

function scenarioTeamGame(team){
  return state.scenario.universe?.teamGame?.[team]||null;
}

function decodeScenarioUniverse(raw){
  const maskBytes=Number(raw.encoding?.mask_bytes||0);
  const teams=raw.teams||[];
  const games=raw.games||[];

  const universe={
    raw,
    trials:Number(raw.trials||0),
    validTrials:Number(raw.valid_trials||0),
    week:Number(raw.week||0),
    maskBytes,
    teams,
    teamIndex:Object.fromEntries(teams.map((team,i)=>[team,i])),
    games,
    gameById:Object.fromEntries(games.map(g=>[g.game_id,g])),
    teamGame:{},
    gameMasks:decodeB64(raw.home_win_masks_b64),
    regularWins:decodeB64(raw.regular_wins_u8_b64),
    confMasks:decodeB64(raw.conference_champion_masks_b64),
    cfpMasks:decodeB64(raw.cfp_masks_b64),
    champions:decodeB64(raw.national_champion_u8_b64),
    validMask:decodeB64(raw.valid_trial_mask_b64)
  };

  for(const game of games){
    if(game.away_is_fbs)universe.teamGame[game.away_team]=game;
    if(game.home_is_fbs)universe.teamGame[game.home_team]=game;
  }

  return universe;
}

function trialIsValid(u,trial){
  return scenarioBit(u.validMask,0,trial);
}

function gameHomeWon(u,game,trial){
  return scenarioBit(
    u.gameMasks,
    Number(game.home_win_mask_index)*u.maskBytes,
    trial
  );
}

function trialMatchesScenario(u,trial,selections){
  for(const [gameId,choice] of Object.entries(selections||{})){
    const game=u.gameById[gameId];
    if(!game)return false;

    const homeWon=gameHomeWon(u,game,trial);

    if(choice==='home'&&!homeWon)return false;
    if(choice==='away'&&homeWon)return false;
  }

  return true;
}

function computeScenarioStats(u,selections){
  const nTeams=u.teams.length;
  const winsSum=new Float64Array(nTeams);
  const confCount=new Uint32Array(nTeams);
  const cfpCount=new Uint32Array(nTeams);
  const natCount=new Uint32Array(nTeams);
  let matches=0;

  for(let trial=0;trial<u.trials;trial++){
    if(!trialIsValid(u,trial))continue;
    if(!trialMatchesScenario(u,trial,selections))continue;

    matches++;
    const base=trial*nTeams;

    for(let ti=0;ti<nTeams;ti++){
      winsSum[ti]+=u.regularWins[base+ti];

      if(scenarioBit(u.confMasks,ti*u.maskBytes,trial)){
        confCount[ti]++;
      }

      if(scenarioBit(u.cfpMasks,ti*u.maskBytes,trial)){
        cfpCount[ti]++;
      }
    }

    const champion=u.champions[trial];
    if(champion!==255&&champion<nTeams){
      natCount[champion]++;
    }
  }

  const byTeam={};

  for(let ti=0;ti<nTeams;ti++){
    const team=u.teams[ti];

    byTeam[team]={
      projected_wins:matches?winsSum[ti]/matches:null,
      conference_title_prob:matches?confCount[ti]/matches:null,
      playoff_prob:matches?cfpCount[ti]/matches:null,
      national_title_prob:matches?natCount[ti]/matches:null
    };
  }

  return {matches,byTeam};
}

function scenarioConditionalForTeam(u,team,game,choice){
  const ti=u.teamIndex[team];
  if(ti===undefined||!game)return null;

  let n=0;
  let wins=0;
  let conf=0;
  let cfp=0;
  let nat=0;

  for(let trial=0;trial<u.trials;trial++){
    if(!trialIsValid(u,trial))continue;

    const homeWon=gameHomeWon(u,game,trial);
    if(choice==='home'&&!homeWon)continue;
    if(choice==='away'&&homeWon)continue;

    n++;
    wins+=u.regularWins[trial*u.teams.length+ti];

    if(scenarioBit(u.confMasks,ti*u.maskBytes,trial))conf++;
    if(scenarioBit(u.cfpMasks,ti*u.maskBytes,trial))cfp++;
    if(u.champions[trial]===ti)nat++;
  }

  if(!n)return null;

  return {
    n,
    projected_wins:wins/n,
    conference_title_prob:conf/n,
    playoff_prob:cfp/n,
    national_title_prob:nat/n
  };
}

function leveragePercentileLabel(value,values){
  if(!Number.isFinite(value)||!values.length)return'—';

  const sorted=[...values].sort((a,b)=>a-b);
  let rank=0;

  for(const candidate of sorted){
    if(candidate<=value)rank++;
  }

  const pctile=rank/sorted.length;

  if(pctile>=.90)return'EXTREME';
  if(pctile>=.70)return'HIGH';
  if(pctile>=.30)return'MED';
  return'LOW';
}

function buildScenarioLeverage(u){
  const out={};

  for(const team of u.teams){
    const game=u.teamGame[team];
    if(!game)continue;

    const home=game.home_team===team;
    const p=home
      ? Number(game.home_win_probability)
      : 1-Number(game.home_win_probability);

    const winChoice=home?'home':'away';
    const lossChoice=home?'away':'home';

    const win=scenarioConditionalForTeam(u,team,game,winChoice);
    const loss=scenarioConditionalForTeam(u,team,game,lossChoice);

    if(!win||!loss)continue;

    const uncertainty=2*p*(1-p);

    out[team]={
      game_id:game.game_id,
      win_probability:p,
      win_branch:win,
      loss_branch:loss,
      projected_wins_leverage:uncertainty,
      conference_leverage:
        uncertainty*Math.abs(
          win.conference_title_prob-loss.conference_title_prob
        ),
      cfp_leverage:
        uncertainty*Math.abs(
          win.playoff_prob-loss.playoff_prob
        ),
      national_title_leverage:
        uncertainty*Math.abs(
          win.national_title_prob-loss.national_title_prob
        ),
      cfp_loss_downside:Math.max(
        0,
        (state.scenario.baseline?.byTeam?.[team]?.playoff_prob||0)-
        loss.playoff_prob
      )
    };
  }

  const winValues=Object.values(out)
    .map(x=>x.projected_wins_leverage)
    .filter(Number.isFinite);

  const confValues=Object.values(out)
    .map(x=>x.conference_leverage)
    .filter(Number.isFinite);

  const cfpValues=Object.values(out)
    .map(x=>x.cfp_leverage)
    .filter(Number.isFinite);

  const favoriteDownsides=Object.values(out)
    .filter(x=>x.win_probability>=.80)
    .map(x=>x.cfp_loss_downside)
    .filter(Number.isFinite)
    .sort((a,b)=>a-b);

  const downsideCutoff=favoriteDownsides.length
    ? favoriteDownsides[
        Math.floor(.75*(favoriteDownsides.length-1))
      ]
    : Infinity;

  for(const item of Object.values(out)){
    item.win_label=leveragePercentileLabel(
      item.projected_wins_leverage,
      winValues
    );

    item.conference_label=leveragePercentileLabel(
      item.conference_leverage,
      confValues
    );

    item.cfp_label=leveragePercentileLabel(
      item.cfp_leverage,
      cfpValues
    );

    item.upset_risk=Boolean(
      item.win_probability>=.80 &&
      item.cfp_loss_downside>0.005 &&
      item.cfp_loss_downside>=downsideCutoff
    );
  }

  return out;
}

async function ensureScenarioUniverse(){
  if(state.scenario.loaded||state.scenario.loading)return;

  state.scenario.loading=true;
  state.scenario.error=null;
  renderRail();

  try{
    const version=encodeURIComponent(
      String(D?.built_at||D?.summary?.built_at||'current')
    );

    const response=await fetch(
      `${SCENARIO_UNIVERSE_URL}?v=${version}`
    );

    if(!response.ok){
      throw new Error(`HTTP ${response.status}`);
    }

    const raw=await response.json();
    const universe=decodeScenarioUniverse(raw);

    state.scenario.universe=universe;
    state.scenario.baseline=computeScenarioStats(universe,{});
    state.scenario.current=state.scenario.baseline;
    state.scenario.leverageByTeam=buildScenarioLeverage(universe);
    state.scenario.loaded=true;
    state.scenario.loading=false;
  }catch(error){
    state.scenario.loading=false;
    state.scenario.error=String(error?.message||error);
  }

  renderCommandCenter();
}

function recomputeScenario(){
  if(!state.scenario.loaded)return;

  state.scenario.current=computeScenarioStats(
    state.scenario.universe,
    state.scenario.selections
  );

  renderCommandCenter();
}

function scenarioCanonicalValue(row,metric){
  if(metric==='wins')return hasNumber(row.projected_wins)
    ? Number(row.projected_wins)
    : null;

  if(metric==='conf')return hasNumber(row.title_model_prob)
    ? Number(row.title_model_prob)
    : null;

  if(metric==='cfp')return hasNumber(row.playoff_model_prob)
    ? Number(row.playoff_model_prob)
    : null;

  if(metric==='nat')return hasNumber(row.national_title_model_prob)
    ? Number(row.national_title_model_prob)
    : null;

  return null;
}

function scenarioUniverseValue(stats,team,metric){
  const row=stats?.byTeam?.[team];
  if(!row)return null;

  if(metric==='wins')return row.projected_wins;
  if(metric==='conf')return row.conference_title_prob;
  if(metric==='cfp')return row.playoff_prob;
  if(metric==='nat')return row.national_title_prob;

  return null;
}

function scenarioAdjustedValue(row,metric){
  if(!scenarioActive())return null;

  const canonical=scenarioCanonicalValue(row,metric);
  const conditional=scenarioUniverseValue(
    state.scenario.current,
    row.team,
    metric
  );
  const baseline=scenarioUniverseValue(
    state.scenario.baseline,
    row.team,
    metric
  );

  if(
    !Number.isFinite(canonical)||
    !Number.isFinite(conditional)||
    !Number.isFinite(baseline)
  )return null;

  let value=canonical+(conditional-baseline);

  if(metric!=='wins'){
    value=Math.max(0,Math.min(1,value));
  }

  return value;
}

function scenarioMetricDelta(row,metric){
  const scenario=scenarioAdjustedValue(row,metric);
  const canonical=scenarioCanonicalValue(row,metric);

  if(
    !Number.isFinite(scenario)||
    !Number.isFinite(canonical)
  )return null;

  return scenario-canonical;
}

function scenarioGameLabel(game){
  return `${game.away_team} @ ${game.home_team}`;
}

function scenarioGameCard(game){
  if(!game)return'';

  const choice=state.scenario.selections[game.game_id]||'unset';

  return `<div class="scenarioGameCard">
    <div class="scenarioGameTitle">
      <b>${esc(scenarioGameLabel(game))}</b>
      <small>
        ${pct(game.home_win_probability)} ${esc(game.home_team)}
      </small>
    </div>

    <div class="scenarioChoiceGrid">
      <button
        type="button"
        data-scenario-game="${esc(game.game_id)}"
        data-scenario-choice="unset"
        class="${choice==='unset'?'active':''}"
      >UNSET</button>

      <button
        type="button"
        data-scenario-game="${esc(game.game_id)}"
        data-scenario-choice="away"
        class="${choice==='away'?'active':''}"
      >${esc(game.away_team)} W</button>

      <button
        type="button"
        data-scenario-game="${esc(game.game_id)}"
        data-scenario-choice="home"
        class="${choice==='home'?'active':''}"
      >${esc(game.home_team)} W</button>
    </div>
  </div>`;
}

function scenarioVisibleGameIds(row){
  const ids=[];
  const own=scenarioTeamGame(row.team);

  if(own)ids.push(own.game_id);

  for(const id of Object.keys(state.scenario.selections||{})){
    if(!ids.includes(id))ids.push(id);
  }

  for(const id of state.scenario.openGames||[]){
    if(!ids.includes(id))ids.push(id);
  }

  return ids;
}

function scenarioCandidateGames(){
  const u=state.scenario.universe;
  if(!u)return[];

  if(state.conference==='all'){
    return u.games;
  }

  return u.games.filter(game=>{
    const away=rowForTeam(game.away_team);
    const home=rowForTeam(game.home_team);

    return away?.conference===state.conference ||
      home?.conference===state.conference;
  });
}

function renderRailScenario(row){
  if(state.scenario.loading){
    return `<div class="scenarioLoading">
      <b>Loading Week 3 scenario universe…</b>
      <small>20,000 precomputed simulations</small>
    </div>`;
  }

  if(state.scenario.error){
    return `<div class="scenarioLoading scenarioError">
      <b>Scenario universe unavailable</b>
      <small>${esc(state.scenario.error)}</small>
      <button type="button" id="scenarioRetry">Retry</button>
    </div>`;
  }

  if(!state.scenario.loaded){
    return `<div class="scenarioLoading">
      <b>Scenario Builder</b>
      <small>
        Loads the 20,000-trial universe once, then every scenario
        is calculated instantly in your browser.
      </small>
      <button type="button" id="scenarioLoad">Load Scenario Builder</button>
    </div>`;
  }

  const u=state.scenario.universe;
  const ids=scenarioVisibleGameIds(row);
  const candidates=scenarioCandidateGames()
    .filter(g=>!ids.includes(g.game_id));

  const matches=state.scenario.current?.matches??u.validTrials;
  const active=scenarioSelectionCount();

  return `<div class="scenarioSummary">
    <span>WEEK ${u.week}</span>
    <b>${matches.toLocaleString()} / ${u.validTrials.toLocaleString()}</b>
    <strong>${scenarioSampleLabel(matches)}</strong>
  </div>

  ${ids.map(id=>scenarioGameCard(u.gameById[id])).join('')}

  <div class="scenarioAdd">
    <label for="scenarioAddGame">ADD ANOTHER GAME</label>
    <select id="scenarioAddGame">
      <option value="">Choose a Week ${u.week} game…</option>
      ${candidates.map(g=>
        `<option value="${esc(g.game_id)}">${esc(scenarioGameLabel(g))}</option>`
      ).join('')}
    </select>
  </div>

  <div class="scenarioActions">
    <span>${active} active outcome${active===1?'':'s'}</span>
    <button type="button" id="scenarioClearAll">CLEAR ALL</button>
  </div>

  <div class="scenarioImpactPanel">
    <h3>${esc(row.team)} · SCENARIO IMPACT</h3>
    <div class="scenarioImpactHead">
      <span></span><b>BASE</b><b>SCENARIO</b><b>Δ</b>
    </div>
    <div class="scenarioImpactRow">
      <span>Projected wins</span>
      <b>${num(row.projected_wins)}</b>
      <strong>${num(scenarioAdjustedValue(row,'wins'))}</strong>
      <em>${scenarioMetricDelta(row,'wins')===null?'—':`${scenarioMetricDelta(row,'wins')>=0?'+':''}${num(scenarioMetricDelta(row,'wins'),2)}`}</em>
    </div>
    <div class="scenarioImpactRow">
      <span>Conference</span>
      <b>${pct(row.title_model_prob)}</b>
      <strong>${pct(scenarioAdjustedValue(row,'conf'))}</strong>
      <em>${scenarioMetricDelta(row,'conf')===null?'—':`${scenarioMetricDelta(row,'conf')>=0?'+':''}${(scenarioMetricDelta(row,'conf')*100).toFixed(1)} pp`}</em>
    </div>
    <div class="scenarioImpactRow">
      <span>Make CFP</span>
      <b>${pct(row.playoff_model_prob)}</b>
      <strong>${pct(scenarioAdjustedValue(row,'cfp'))}</strong>
      <em>${scenarioMetricDelta(row,'cfp')===null?'—':`${scenarioMetricDelta(row,'cfp')>=0?'+':''}${(scenarioMetricDelta(row,'cfp')*100).toFixed(1)} pp`}</em>
    </div>
    <div class="scenarioImpactRow">
      <span>National title</span>
      <b>${pct(row.national_title_model_prob)}</b>
      <strong>${pct(scenarioAdjustedValue(row,'nat'))}</strong>
      <em>${scenarioMetricDelta(row,'nat')===null?'—':`${scenarioMetricDelta(row,'nat')>=0?'+':''}${(scenarioMetricDelta(row,'nat')*100).toFixed(1)} pp`}</em>
    </div>
  </div>`;
}

function bindScenarioRail(){
  const rail=document.getElementById('futuresRail');
  if(!rail)return;

  rail.querySelector('#scenarioLoad')?.addEventListener('click',()=>{
    ensureScenarioUniverse();
  });

  rail.querySelector('#scenarioRetry')?.addEventListener('click',()=>{
    state.scenario.error=null;
    ensureScenarioUniverse();
  });

  rail.querySelectorAll('[data-scenario-game]').forEach(button=>{
    button.addEventListener('click',()=>{
      const gameId=button.dataset.scenarioGame;
      const choice=button.dataset.scenarioChoice;

      if(choice==='unset'){
        delete state.scenario.selections[gameId];
      }else{
        state.scenario.selections[gameId]=choice;
      }

      recomputeScenario();
    });
  });

  rail.querySelector('#scenarioAddGame')?.addEventListener('change',event=>{
    const id=event.target.value;
    if(!id)return;

    if(!state.scenario.openGames.includes(id)){
      state.scenario.openGames.push(id);
    }

    renderRail();
  });

  rail.querySelector('#scenarioClearAll')?.addEventListener('click',()=>{
    state.scenario.selections={};
    state.scenario.openGames=[];
    recomputeScenario();
  });
}

function renderScenarioBanner(){
  let banner=document.getElementById('futuresScenarioBanner');

  if(!banner){
    banner=document.createElement('section');
    banner.id='futuresScenarioBanner';
    banner.className='futuresScenarioBanner';

    const controls=document.getElementById('futuresCommandControls');
    controls?.insertAdjacentElement('afterend',banner);
  }

  if(!scenarioActive()){
    banner.hidden=true;
    return;
  }

  const count=scenarioSelectionCount();
  const matches=state.scenario.current?.matches||0;
  const total=state.scenario.universe?.validTrials||0;

  banner.hidden=false;
  banner.innerHTML=`
    <b>SCENARIO ACTIVE</b>
    <span>${count} game${count===1?'':'s'}</span>
    <span>${matches.toLocaleString()} / ${total.toLocaleString()} SIMS</span>
    <strong>${scenarioSampleLabel(matches)}</strong>
    <button type="button" id="scenarioBannerClear">CLEAR</button>
  `;

  banner.querySelector('#scenarioBannerClear')?.addEventListener('click',()=>{
    state.scenario.selections={};
    state.scenario.openGames=[];
    recomputeScenario();
  });
}

function fairOdds(p){
  if(!hasNumber(p))return'—';
  p=Number(p);
  if(p<=0)return'+∞';
  if(p>=1)return'-∞';
  return p>=.5
    ? `${Math.round(-100*p/(1-p))}`
    : `+${Math.round(100*(1-p)/p)}`;
}

function ratingHistoryRows(row){
  return Array.isArray(row?.team_rating_history)
    ? row.team_rating_history
    : [];
}

function historyRatingValue(item){
  if(!item)return null;
  for(const key of ['rating','team_rating','value']){
    if(hasNumber(item[key]))return Number(item[key]);
  }
  return null;
}

function historyDateValue(item){
  return String(
    item?.snapshot_date||
    item?.date||
    item?.rating_date||
    ''
  ).slice(0,10);
}

function l2BaselineRating(row){
  const history=ratingHistoryRows(row)
    .map(x=>({date:historyDateValue(x),rating:historyRatingValue(x)}))
    .filter(x=>x.date&&hasNumber(x.rating))
    .sort((a,b)=>b.date.localeCompare(a.date));

  if(history.length>=2)return Number(history[1].rating);
  if(hasNumber(row?.team_rating_prior_week))return Number(row.team_rating_prior_week);
  return null;
}

function priorRankMap(){
  const candidates=(D.rows||[])
    .map(row=>({team:row.team,rating:l2BaselineRating(row)}))
    .filter(x=>hasNumber(x.rating))
    .sort((a,b)=>Number(b.rating)-Number(a.rating));

  const out={};
  candidates.forEach((x,i)=>out[x.team]=i+1);
  return out;
}

function movementArrow(delta,invert=false){
  if(!hasNumber(delta)||Math.abs(Number(delta))<0.0001){
    return '<span class="moveFlat" title="No movement">→</span>';
  }

  const positive=invert ? Number(delta)<0 : Number(delta)>0;
  return positive
    ? '<span class="moveUp" title="Improved">↑</span>'
    : '<span class="moveDown" title="Declined">↓</span>';
}

function movementWithAmount(delta,invert=false,digits=1){
  if(!hasNumber(delta))return'';

  delta=Number(delta);

  if(Math.abs(delta)<0.0001){
    return '<span class="moveFlat" title="No movement">→</span>';
  }

  const improved=invert ? delta<0 : delta>0;
  const cls=improved?'moveUp':'moveDown';
  const arrow=improved?'↑':'↓';
  const amount=Math.abs(delta).toFixed(digits);

  return `<span class="${cls}" title="${improved?'Improved':'Declined'}">${arrow} ${amount}</span>`;
}

function ratingMovement(row){
  const base=l2BaselineRating(row);
  if(!hasNumber(base)||!hasNumber(row?.team_rating))return'';

  return movementWithAmount(
    Number(row.team_rating)-Number(base),
    false,
    1
  );
}

function rankMovement(row){
  const prior=priorRankMap()[row.team];
  const current=Number(row.overall_rank??row.rank);

  if(!Number.isFinite(current)||!Number.isFinite(Number(prior)))return'';

  return movementWithAmount(
    current-Number(prior),
    true,
    0
  );
}

function conferenceSOS(row){
  const games=scheduleFor(row).filter(g=>!g.completed&&g.is_conference_game);
  const ratings=games
    .map(g=>g.opponentRow?.team_rating)
    .filter(hasNumber)
    .map(Number);

  if(!ratings.length)return null;

  return ratings.reduce((a,b)=>a+b,0)/ratings.length;
}

function conferenceSOSRank(row){
  if(!row?.conference||row.conference==='Independent')return null;

  const pool=(D.rows||[])
    .filter(r=>r.conference===row.conference)
    .map(r=>({team:r.team,sos:conferenceSOS(r)}))
    .filter(x=>hasNumber(x.sos))
    .sort((a,b)=>Number(b.sos)-Number(a.sos));

  const idx=pool.findIndex(x=>x.team===row.team);
  return idx<0?null:{rank:idx+1,total:pool.length,sos:pool[idx].sos};
}

function teamLogo(row,cls=''){
  return row?.slug
    ? `<img class="${cls}" src="logos/${esc(row.slug)}.png" alt="${esc(row.team||'')}" onerror="this.style.display='none'">`
    : '';
}

function bookLogo(book){
  const slug=BOOK_SLUG[book];
  return slug
    ? `<img class="futBookLogo" src="logos/books/${slug}.png" alt="${esc(book)}" title="${esc(book)}">`
    : '';
}

function rowForTeam(name){
  return (D.rows||[]).find(r=>r.team===name)||null;
}

function rankClass(rank){
  rank=Number(rank);
  if(!Number.isFinite(rank))return'';

  const total=Math.max(1,(D?.rows||[]).length||138);
  const pctRank=rank/total;

  if(pctRank<=.20)return'rankElite';
  if(pctRank<=.40)return'rankStrong';
  if(pctRank<=.60)return'rankGood';
  if(pctRank<=.80)return'rankMid';
  return'rankLow';
}

function probabilityClass(p){
  if(!hasNumber(p))return'';
  p=Number(p);
  if(p>=.70)return'probStrong';
  if(p>=.55)return'probGood';
  if(p<=.30)return'probLow';
  if(p<=.45)return'probWeak';
  return'probEven';
}

function seasonProjectedRecord(row){
  if(!hasNumber(row?.projected_wins))return null;
  const r=row.record||{};
  const totalGames=
    Number(r.wins||0)+
    Number(r.losses||0)+
    Number(row.games_remaining||0);

  const wins=Number(row.projected_wins);
  return {
    wins,
    losses:Math.max(0,totalGames-wins)
  };
}

function projectedRecordMarkup(row){
  const r=seasonProjectedRecord(row);
  return r
    ? `<b>${num(r.wins)}-${num(r.losses)}</b>`
    : '<span class="muted">—</span>';
}

function projectedConferenceMarkup(row){
  const r=row?.projected_conference_record;
  return r?.complete&&hasNumber(r.wins)&&hasNumber(r.losses)
    ? `<b>${num(r.wins)}-${num(r.losses)}</b>`
    : '<span class="muted">—</span>';
}

function scheduleFor(row){
  return (row?.schedule_game_ids||[])
    .map(id=>{
      const g=D.schedule_games?.[id];
      if(!g)return null;

      const isHome=row.team===g.home_team;
      const homeProb=hasNumber(g.home_win_probability)
        ? Number(g.home_win_probability)
        : null;

      const teamProb=g.completed
        ? null
        : homeProb===null
          ? null
          : isHome
            ? homeProb
            : 1-homeProb;

      const own=isHome?g.home_score:g.away_score;
      const opp=isHome?g.away_score:g.home_score;

      let result=null;
      if(g.completed&&hasNumber(own)&&hasNumber(opp)){
        result=Number(own)>Number(opp)?'W':
          Number(own)<Number(opp)?'L':'T';
      }

      const opponent=isHome?g.away_team:g.home_team;

      return {
        ...g,
        game_id:id,
        opponent,
        opponentRow:rowForTeam(opponent),
        site:g.neutral_site?'N':isHome?'HOME':'AWAY',
        team_probability:teamProb,
        team_score:own,
        opponent_score:opp,
        result
      };
    })
    .filter(Boolean)
    .sort((a,b)=>
      Number(a.week||99)-Number(b.week||99) ||
      String(a.date||'').localeCompare(String(b.date||''))
    );
}

function nextGameMarkup(row){
  const g=row.next_game;
  if(!g)return '<span class="neutral">—</span>';

  const opp=rowForTeam(g.opponent);
  const site=g.site==='AWAY'?'@':g.site==='N'?'vs*':'vs';
  const opponentRank=opp&&hasNumber(opp.rank)?Number(opp.rank):null;
  const rankLabel=opponentRank!=null?`<span class="${rankClass(opponentRank)}">${opponentRank}</span> `:'';

  const rowProb=hasNumber(g.win_probability)?Number(g.win_probability):null;
  const probabilityText=rowProb!=null
    ? `${esc(row.team||'Team')} win %: ${pct(rowProb)}`
    : 'Win probability unavailable';
  const probabilityStyle=rowProb==null
    ? 'neutral'
    : rowProb>=0.5
      ? 'good'
      : 'teamUnderdogProbability';

  return `<div class="nextGameCell">
    ${teamLogo(opp,'oppLogo')}
    <span class="nextGameIdentity">
      <b>${site} ${rankLabel}${esc(g.opponent)}</b>
      <small class="${probabilityStyle}">${probabilityText}</small>
    </span>
  </div>`;
}

function teamCell(row){
  const rank=row.overall_rank??row.rank;
  return `<button type="button" class="futTeamButton" data-select-team="${esc(row.team)}">
    <span class="teamRankBadge ${rankClass(rank)}">${rank??'—'}</span>
    ${teamLogo(row,'futTeamLogo')}
    <span class="futTeamIdentity">
      <b>${esc(row.team)}</b>
      <small>${esc(row.conference||'IND')}</small>
    </span>
  </button>`;
}

function rankMarkup(row){
  const rank=row.overall_rank??row.rank;
  return `<div class="metricMove">
    <b class="${rankClass(rank)}">${rank??'—'}</b>
    ${rankMovement(row)}
  </div>`;
}

function ratingMarkup(row){
  const rank=row.overall_rank??row.rank;
  return `<div class="metricMove">
    <b class="${rankClass(rank)}">${num(row.team_rating)}</b>
    ${ratingMovement(row)}
  </div>`;
}

function projectedWinMarkup(row){
  if(!hasNumber(row.title_model_prob))return'<span class="muted">—</span>';
  return `<div class="projWinStack">
    <b>${pct(row.title_model_prob)}</b>
    <small>${fairOdds(row.title_model_prob)}</small>
  </div>`;
}

function sosMarkup(row){
  const x=conferenceSOSRank(row);
  return x
    ? `<div class="sosStack"><b>${x.rank}/${x.total}</b><small>${num(x.sos)}</small></div>`
    : '<span class="muted">—</span>';
}

function quoteKind(row,kind){
  if(kind==='wins')return {
    quotes:row.win_quotes||{},
    bestBook:row.win_book,
    side:row.win_direction,
    line:row.market_win_total,
    price:row.win_price,
    label:'Win total'
  };

  if(kind==='title')return {
    quotes:row.title_quotes||{},
    bestBook:row.title_book,
    price:row.title_price,
    label:'Conference title'
  };

  if(kind==='cfp')return {
    quotes:row.playoff_quotes||{},
    bestBook:row.playoff_book,
    price:row.playoff_price,
    label:'Make CFP'
  };

  return {
    quotes:row.national_title_quotes||{},
    bestBook:row.national_title_book,
    price:row.national_title_price,
    label:'National title'
  };
}

function fourBookCount(data){
  return BOOKS.filter(book=>data.quotes?.[book]).length;
}

function bestMarketMarkup(row,kind){
  const d=quoteKind(row,kind);
  const payload=encodeURIComponent(JSON.stringify({
    team:row.team,
    kind
  }));

  const primary=kind==='wins'
    ? `${esc((d.side||'').slice(0,1).toUpperCase())} ${num(d.line)}`
    : odds(d.price);

  const secondary=kind==='wins'
    ? odds(d.price)
    : esc(d.bestBook||'');

  return `<button type="button" class="bestMarketButton" data-four-quotes="${payload}" aria-label="Show all sportsbook quotes">
    <span class="bestBookLogo">${bookLogo(d.bestBook)}</span>
    <span class="bestMarketStack">
      <span class="bestPrimary">${primary}</span>
      <span class="bestSecondary">${secondary}</span>
    </span>
  </button>`;
}

function edgeMarkup(v,kind){
  if(!hasNumber(v))return'<span class="muted">—</span>';

  if(kind==='wins'){
    const x=Number(v);
    return `<b class="${x>=0?'good':'bad'}">${x>0?'+':''}${x.toFixed(1)} W</b>`;
  }

  const x=Number(v)*100;
  return `<b class="${x>=0?'good':'bad'}">${x>0?'+':''}${x.toFixed(1)}%</b>`;
}

function wagerMarkup(row){
  const n=(row.open_wagers||[]).length;
  return n
    ? `<span class="bet" title="${n} open wager${n===1?'':'s'}">YES</span>`
    : '<span class="muted">—</span>';
}

function sortable(label,key){
  const active=state.sortKey===key;
  const arrow=active?(state.sortDir==='asc'?' ▲':' ▼'):'';
  return `<button class="futSort" data-sort-key="${esc(key)}">${esc(label)}${arrow}</button>`;
}

function sortValue(row,key){

  if(key==='scenario_value'){
    return scenarioTableValue(row);
  }

  if(key==='scenario_delta'){
    return scenarioTableDelta(row);
  }

  if(key==='swing'){
    return swingForRow(row)?.value??null;
  }


  const projected=seasonProjectedRecord(row);
  const confProjected=row.projected_conference_record||{};

  const map={
    team:row.team,
    rank:row.overall_rank??row.rank,
    rating:row.team_rating,
    record:Number(row.record?.wins||0),
    left:row.games_remaining,
    projected:projected?.wins,
    next:row.next_game?.win_probability,
    model_wins:row.projected_wins,
    win_market:row.market_win_total,
    win_edge:row.win_edge,
    conf_record:Number(row.record?.conf_wins||0),
    conf_left:row.conference_games_remaining,
    conf_projected:confProjected.wins,
    title_model:row.title_model_prob,
    conf_sos:conferenceSOSRank(row)?.rank,
    title_price:row.title_price,
    title_edge:row.title_edge,
    cfp_model:row.playoff_model_prob,
    cfp_price:row.playoff_price,
    cfp_edge:row.playoff_edge,
    national_model:row.national_title_model_prob,
    national_price:row.national_title_price,
    national_edge:row.national_title_edge,
    wager:(row.open_wagers||[]).length
  };

  return map[key];
}

function visibleRows(){
  const query=state.search.trim().toLowerCase();

  return (D.rows||[]).filter(row=>{
    if(state.mode==='title'){
      if(row.conference==='Independent')return false;
      if(!Object.keys(row.title_quotes||{}).length)return false;
    }

    return (
      (state.conference==='all'||row.conference===state.conference) &&
      (!query||String(row.team||'').toLowerCase().includes(query))
    );
  });
}

function sortedVisibleRows(){
  const data=visibleRows().slice();
  const key=state.sortKey;
  const dir=state.sortDir==='asc'?1:-1;

  data.sort((a,b)=>{
    const av=sortValue(a,key);
    const bv=sortValue(b,key);

    const am=av===null||av===undefined||
      (typeof av==='number'&&!Number.isFinite(av));
    const bm=bv===null||bv===undefined||
      (typeof bv==='number'&&!Number.isFinite(bv));

    if(am&&bm)return String(a.team).localeCompare(String(b.team));
    if(am)return 1;
    if(bm)return -1;

    if(typeof av==='string'||typeof bv==='string'){
      return String(av).localeCompare(String(bv))*dir;
    }

    const diff=(Number(av)-Number(bv))*dir;
    return diff||String(a.team).localeCompare(String(b.team));
  });

  return data;
}


function scenarioMetricForMode(){
  if(state.mode==='title')return'conf';
  if(state.mode==='playoff')return'cfp';
  return'wins';
}

function swingForRow(row){
  const item=state.scenario.leverageByTeam?.[row.team];
  if(!item)return null;

  let value=null;

  if(state.mode==='title'){
    value=Math.abs(
      item.win_branch.conference_title_prob-
      item.loss_branch.conference_title_prob
    );
  }else if(state.mode==='playoff'){
    value=Math.abs(
      item.win_branch.playoff_prob-
      item.loss_branch.playoff_prob
    );
  }else{
    return null;
  }

  return {
    value,
    display:`${(value*100).toFixed(1)}%`
  };
}

function swingClass(value){
  const pctValue=Number(value)*100;

  if(pctValue>=20)return'swing-red';
  if(pctValue>=10)return'swing-yellow';
  if(pctValue>=5)return'swing-green';
  return'swing-muted';
}

function swingMarkup(row){
  const item=swingForRow(row);

  if(!item)return'<span class="swingUnavailable">—</span>';

  return `<div class="swingCell">
    <b class="swingValue ${swingClass(item.value)}">
      ${esc(item.display)}
    </b>
  </div>`;
}

function scenarioTableValue(row){
  return scenarioAdjustedValue(
    row,
    scenarioMetricForMode()
  );
}

function scenarioTableDelta(row){
  return scenarioMetricDelta(
    row,
    scenarioMetricForMode()
  );
}

function scenarioTableValueMarkup(row){
  const value=scenarioTableValue(row);
  if(!Number.isFinite(value))return'—';

  if(state.mode==='wins'){
    return `<b>${num(value)}</b>`;
  }

  return `<b>${pct(value)}</b>`;
}

function scenarioTableDeltaMarkup(row){
  const delta=scenarioTableDelta(row);
  if(!Number.isFinite(delta))return'—';

  const positive=delta>0;
  const negative=delta<0;
  const cls=positive?'scenarioDeltaUp':
    negative?'scenarioDeltaDown':'scenarioDeltaFlat';

  if(state.mode==='wins'){
    return `<b class="${cls}">
      ${delta>0?'+':''}${num(delta,2)}
    </b>`;
  }

  return `<b class="${cls}">
    ${delta>0?'+':''}${(delta*100).toFixed(1)} pp
  </b>`;
}

function scenarioExtraHeaders(){
  const active=scenarioActive();
  const showSwing=
    state.mode==='title'||state.mode==='playoff';

  const swingLabel=state.mode==='title'
    ? 'Conf Swing'
    : 'CFP Swing';

  return `${
    active
      ? `<th class="colScenario">${sortable('Scenario','scenario_value')}</th>
         <th class="colDelta">${sortable('Δ','scenario_delta')}</th>`
      : ''
  }${
    showSwing
      ? `<th class="colSwing">${sortable(swingLabel,'swing')}</th>`
      : ''
  }`;
}

function scenarioExtraCells(row){
  const active=scenarioActive();
  const showSwing=
    state.mode==='title'||state.mode==='playoff';

  return `${
    active
      ? `<td class="scenarioValueCell">${scenarioTableValueMarkup(row)}</td>
         <td class="scenarioDeltaCell">${scenarioTableDeltaMarkup(row)}</td>`
      : ''
  }${
    showSwing
      ? `<td class="swingTableCell">${swingMarkup(row)}</td>`
      : ''
  }`;
}

function renderWins(data){
  head.innerHTML=`<tr>
    <th class="colTeam">${sortable('Team','team')}</th>
    <th class="colNext">${sortable('Next Game','next')}</th>
    <th class="colRank">${sortable('Rank','rank')}</th>
    <th class="colRating">${sortable('Rating','rating')}</th>
    <th class="colRecord">${sortable('Record','record')}</th>
    <th class="colTiny">${sortable('Left','left')}</th>
    <th class="colProjected">${sortable('Proj Record','projected')}</th>
    <th class="colModel">${sortable('Model Wins','model_wins')}</th>
    ${scenarioExtraHeaders()}
    <th class="marketCol">${sortable('Best','win_market')}</th>
    <th class="colEdge">${sortable('Edge','win_edge')}</th>
    <th class="colWager">${sortable('Wager','wager')}</th>
  </tr>`;

  rows.innerHTML=data.map(row=>`<tr data-fut-team="${esc(row.team)}" class="${row.team===state.selectedTeam?'selectedRow':''}">
    <td>${teamCell(row)}</td>
    <td>${nextGameMarkup(row)}</td>
    <td>${rankMarkup(row)}</td>
    <td>${ratingMarkup(row)}</td>
    <td><b>${row.record?.wins??0}-${row.record?.losses??0}</b></td>
    <td><b>${row.games_remaining??'—'}</b></td>
    <td>${projectedRecordMarkup(row)}</td>
    <td><b>${num(row.projected_wins)}</b></td>
    ${scenarioExtraCells(row)}
    <td class="marketCol">${bestMarketMarkup(row,'wins')}</td>
    <td>${edgeMarkup(row.win_edge,'wins')}</td>
    <td>${wagerMarkup(row)}</td>
  </tr>`).join('');
}

function renderConference(data){
  head.innerHTML=`<tr>
    <th class="colTeam">${sortable('Team','team')}</th>
    <th class="colNext">${sortable('Next Game','next')}</th>
    <th class="colRank">${sortable('Rank','rank')}</th>
    <th class="colRating">${sortable('Rating','rating')}</th>
    <th class="colRecord">${sortable('Conf Rec','conf_record')}</th>
    <th class="colTiny">${sortable('Left','conf_left')}</th>
    <th class="colProjected">${sortable('Proj Conf','conf_projected')}</th>
    <th class="colSos">${sortable('Rem SOS','conf_sos')}</th>
    <th class="colModel">${sortable('Proj Win %','title_model')}</th>
    ${scenarioExtraHeaders()}
    <th class="marketCol">${sortable('Best','title_price')}</th>
    <th class="colEdge">${sortable('Edge','title_edge')}</th>
    <th class="colWager">${sortable('Wager','wager')}</th>
  </tr>`;

  rows.innerHTML=data.map(row=>`<tr data-fut-team="${esc(row.team)}" class="${row.team===state.selectedTeam?'selectedRow':''}">
    <td>${teamCell(row)}</td>
    <td>${nextGameMarkup(row)}</td>
    <td>${rankMarkup(row)}</td>
    <td>${ratingMarkup(row)}</td>
    <td><b>${row.record?.conf_wins??0}-${row.record?.conf_losses??0}</b></td>
    <td><b>${row.conference_games_remaining??'—'}</b></td>
    <td>${projectedConferenceMarkup(row)}</td>
    <td>${sosMarkup(row)}</td>
    <td>${projectedWinMarkup(row)}</td>
    ${scenarioExtraCells(row)}
    <td class="marketCol">${bestMarketMarkup(row,'title')}</td>
    <td>${edgeMarkup(row.title_edge,'title')}</td>
    <td>${wagerMarkup(row)}</td>
  </tr>`).join('');
}

function renderPlayoffs(data){
  head.innerHTML=`<tr>
    <th class="colTeam">${sortable('Team','team')}</th>
    <th class="colNext">${sortable('Next Game','next')}</th>
    <th class="colRank">${sortable('Rank','rank')}</th>
    <th class="colRating">${sortable('Rating','rating')}</th>
    <th class="colProjected">${sortable('Projected Record','projected')}</th>
    <th class="colModel">${sortable('CFP Model','cfp_model')}</th>
    ${scenarioExtraHeaders()}
    <th class="marketCol">${sortable('Best CFP','cfp_price')}</th>
    <th class="colEdge">${sortable('CFP Edge','cfp_edge')}</th>
    <th class="colModel">${sortable('Title Model','national_model')}</th>
    <th class="marketCol">${sortable('Best Title','national_price')}</th>
    <th class="colEdge">${sortable('Title Edge','national_edge')}</th>
  </tr>`;

  rows.innerHTML=data.map(row=>`<tr data-fut-team="${esc(row.team)}" class="${row.team===state.selectedTeam?'selectedRow':''}">
    <td>${teamCell(row)}</td>
    <td>${nextGameMarkup(row)}</td>
    <td>${rankMarkup(row)}</td>
    <td>${ratingMarkup(row)}</td>
    <td>${projectedRecordMarkup(row)}</td>
    <td><b>${pct(row.playoff_model_prob)}</b></td>
    ${scenarioExtraCells(row)}
    <td class="marketCol">${bestMarketMarkup(row,'cfp')}</td>
    <td>${edgeMarkup(row.playoff_edge,'cfp')}</td>
    <td><b>${pct(row.national_title_model_prob)}</b></td>
    <td class="marketCol">${bestMarketMarkup(row,'national')}</td>
    <td>${edgeMarkup(row.national_title_edge,'national')}</td>
  </tr>`).join('');
}

function mobileMarketConfig(kind){
  if(kind==='wins')return {
    heading:'Win Totals',modelKey:'projected_wins',edgeKey:'win_edge',quoteKind:'wins'
  };
  if(kind==='title')return {
    heading:'Conference Titles',modelKey:'title_model_prob',edgeKey:'title_edge',quoteKind:'title'
  };
  if(kind==='cfp')return {
    heading:'Playoffs / CFP',modelKey:'playoff_model_prob',edgeKey:'playoff_edge',quoteKind:'cfp'
  };
  return {
    heading:'National Title',modelKey:'national_title_model_prob',edgeKey:'national_title_edge',quoteKind:'national'
  };
}

function mobileSortedRows(data,kind){
  const cfg=mobileMarketConfig(kind);
  const spec=mobileSortState[kind];
  const dir=spec.dir==='asc'?1:-1;

  return data.slice().sort((a,b)=>{
    if(spec.key==='team'){
      return String(a.team||'').localeCompare(String(b.team||''))*dir;
    }

    const av=a[cfg.edgeKey],bv=b[cfg.edgeKey];
    const am=!hasNumber(av),bm=!hasNumber(bv);
    if(am&&bm)return String(a.team||'').localeCompare(String(b.team||''));
    if(am)return 1;
    if(bm)return -1;
    return (Number(av)-Number(bv))*dir||String(a.team||'').localeCompare(String(b.team||''));
  });
}

function mobileSortButton(label,kind,key){
  const spec=mobileSortState[kind];
  const active=spec.key===key;
  const arrow=active?(spec.dir==='asc'?' ▲':' ▼'):'';
  return `<button type="button" class="mobileSortButton${active?' active':''}" data-mobile-sort="${kind}" data-mobile-key="${key}" aria-label="Sort ${label} ${active&&spec.dir==='asc'?'descending':'ascending'}">${label}${arrow}</button>`;
}

function mobileBestMarketMarkup(row,kind){
  const d=quoteKind(row,kind);
  const selected=d.quotes?.[d.bestBook]||null;
  const price=quoteOdds(selected,d.side);
  const line=price;
  const secondary=esc(d.bestBook||'—');

  return `<button type="button" class="mobileBestButton" data-four-quotes="${encodeURIComponent(JSON.stringify({team:row.team,kind}))}" aria-label="${esc(d.bestBook||'Best price')} ${esc(line)}; show all provider quotes">
    ${bookLogo(d.bestBook)}
    <span><b>${line}</b><small>${secondary}</small></span>
  </button>`;
}

function mobileTeamMarkup(row){
  return `<button type="button" class="mobileTeamButton" data-mobile-team="${esc(row.team)}" aria-expanded="${row.team===state.mobileExpandedTeam?'true':'false'}">
    ${teamLogo(row,'mobileTeamLogo')}<span><b>${esc(row.team)}</b><small>${esc(row.conference||'IND')}</small></span>
  </button>`;
}

function mobileDetailMarkup(row,kind){
  if(row.team!==state.mobileExpandedTeam)return'';
  const rank=row.overall_rank??row.rank;
  const projected=seasonProjectedRecord(row);
  return `<tr class="mobileDetailRow" data-mobile-detail="${esc(row.team)}"><td colspan="4"><div>
    <span><small>Rank</small><b>${rank??'—'}</b></span>
    <span><small>Rating</small><b>${num(row.team_rating)}</b></span>
    <span><small>Record</small><b>${row.record?.wins??0}-${row.record?.losses??0}</b></span>
    <span><small>Projected</small><b>${projected?`${num(projected.wins)}-${num(projected.losses)}`:'—'}</b></span>
    <button type="button" data-mobile-full-detail="${esc(row.team)}">Full details</button>
  </div></td></tr>`;
}

function mobileTableMarkup(data,kind){
  const cfg=mobileMarketConfig(kind);
  const sorted=mobileSortedRows(data,kind);
  const modelLabel=kind==='wins'?'Total':'Model';

  return `<section class="mobileFuturesSection" data-mobile-market="${kind}">
    ${state.mode==='playoff'?`<h2>${cfg.heading}</h2>`:''}
    <div class="mobileTableViewport">
      <table class="mobileFuturesTable">
        <thead><tr>
          <th>${mobileSortButton('Team',kind,'team')}</th>
          <th>${modelLabel}</th>
          <th>Best</th>
          <th>${mobileSortButton('Edge',kind,'edge')}</th>
        </tr></thead>
        <tbody>${sorted.map(row=>`<tr data-mobile-row="${esc(row.team)}">
          <td>${mobileTeamMarkup(row)}</td>
          <td><b>${kind==='wins'?`${esc((row.win_direction||'').slice(0,1).toUpperCase())} ${num(row.market_win_total)}`:pct(row[cfg.modelKey])}</b></td>
          <td>${mobileBestMarketMarkup(row,cfg.quoteKind)}</td>
          <td>${edgeMarkup(row[cfg.edgeKey],kind==='wins'?'wins':kind)}</td>
        </tr>${mobileDetailMarkup(row,kind)}`).join('')||'<tr><td colspan="4" class="empty">No matching futures markets.</td></tr>'}</tbody>
      </table>
    </div>
  </section>`;
}

function renderMobileTables(data){
  const host=document.getElementById('mobileFuturesTables');
  if(!host)return;
  host.innerHTML=state.mode==='playoff'
    ? mobileTableMarkup(data,'cfp')+mobileTableMarkup(data,'national')
    : mobileTableMarkup(data,state.mode==='title'?'title':'wins');

  host.querySelectorAll('[data-mobile-sort]').forEach(button=>{
    button.onclick=event=>{
      event.stopPropagation();
      const kind=button.dataset.mobileSort;
      const key=button.dataset.mobileKey;
      const spec=mobileSortState[kind];
      if(spec.key===key)spec.dir=spec.dir==='asc'?'desc':'asc';
      else Object.assign(spec,{key,dir:key==='team'?'asc':'desc'});
      renderCommandCenter();
    };
  });

  host.querySelectorAll('[data-mobile-team]').forEach(button=>{
    button.onclick=event=>{
      event.stopPropagation();
      state.mobileExpandedTeam=state.mobileExpandedTeam===button.dataset.mobileTeam?null:button.dataset.mobileTeam;
      renderCommandCenter();
    };
  });

  host.querySelectorAll('[data-mobile-full-detail]').forEach(button=>{
    button.onclick=event=>{
      event.stopPropagation();
      state.selectedTeam=button.dataset.mobileFullDetail;
      renderRail();
      document.getElementById('futuresRail')?.scrollIntoView({behavior:'smooth',block:'start'});
    };
  });
}

function bindSorting(){
  document.querySelectorAll('[data-sort-key]').forEach(button=>{
    button.onclick=event=>{
      event.stopPropagation();
      const key=button.dataset.sortKey;

      if(state.sortKey===key){
        state.sortDir=state.sortDir==='asc'?'desc':'asc';
      }else{
        state.sortKey=key;
        state.sortDir=['team','rank'].includes(key)?'asc':'desc';
      }

      renderCommandCenter();
    };
  });
}

function bindSelection(){
  document.querySelectorAll('[data-fut-team]').forEach(tr=>{
    tr.onclick=()=>{
      state.selectedTeam=tr.dataset.futTeam;
      renderCommandCenter();
    };
  });

  document.querySelectorAll('[data-select-team]').forEach(button=>{
    button.onclick=event=>{
      event.stopPropagation();
      state.selectedTeam=button.dataset.selectTeam;
      renderCommandCenter();
    };
  });
}

function fourBookBoard(row,kind){
  const data=quoteKind(row,kind);

  return `<div class="railMarketBoard">
    ${BOOKS.map(book=>{
      const q=data.quotes?.[book];
      const best=book===data.bestBook;

      if(!q){
        return `<div class="railBookRow missingBook">
          <span>${bookLogo(book)}</span>
          <b>—</b>
          <small>NO QUOTE</small>
        </div>`;
      }

      const price=kind==='wins'
        ? data.side==='Under'
          ? q.under_price
          : q.over_price
        : q.price;

      const line=kind==='wins'&&hasNumber(q.number)
        ? `${data.side?.slice(0,1)||''} ${num(q.number)}`
        : '';

      return `<div class="railBookRow ${best?'bestBookRow':''}">
        <span>${bookLogo(book)}</span>
        <b>${line?`${esc(line)} · `:''}${quoteOdds(q,data.side)}</b>
        <small>${best?'BEST':'AVAILABLE'}</small>
      </div>`;
    }).join('')}
  </div>`;
}

function renderRailOverview(row){
  const season=seasonProjectedRecord(row);
  const next=row.next_game;

  return `<div class="railOverviewGrid">
    <div><span>RANK</span><b class="${rankClass(row.overall_rank??row.rank)}">#${row.overall_rank??row.rank??'—'}</b></div>
    <div><span>RATING</span><b>${num(row.team_rating)}</b></div>
    <div><span>RECORD</span><b>${row.record?.wins??0}-${row.record?.losses??0}</b></div>
    <div><span>PROJECTED</span><b>${season?`${num(season.wins)}-${num(season.losses)}`:'—'}</b></div>
    <div><span>GAMES LEFT</span><b>${row.games_remaining??'—'}</b></div>
    <div><span>MODEL WINS</span><b>${num(row.projected_wins)}</b></div>
  </div>

  <div class="railSection">
    <h3>NEXT GAME</h3>
    ${next?nextGameMarkup(row):'<p class="railEmpty">Season complete.</p>'}
  </div>

  <div class="railSection">
    <h3>FUTURES SNAPSHOT</h3>
    <div class="railSnapshotRow"><span>Win total</span><b>${num(row.market_win_total)}</b><strong>${edgeMarkup(row.win_edge,'wins')}</strong></div>
    <div class="railSnapshotRow"><span>Conference</span><b>${pct(row.title_model_prob)}</b><strong>${edgeMarkup(row.title_edge,'title')}</strong></div>
    <div class="railSnapshotRow"><span>Make CFP</span><b>${pct(row.playoff_model_prob)}</b><strong>${edgeMarkup(row.playoff_edge,'cfp')}</strong></div>
    <div class="railSnapshotRow"><span>National title</span><b>${pct(row.national_title_model_prob)}</b><strong>${edgeMarkup(row.national_title_edge,'national')}</strong></div>
  </div>`;
}

function renderRailSchedule(row){
  const games=scheduleFor(row);

  const body=games.map(g=>{
    const opp=g.opponentRow;
    const rank=opp?.overall_rank??opp?.rank;
    let status='UPCOMING';
    let cls='';

    if(g.completed){
      status=`${g.result||'F'} ${num(g.team_score,0)}-${num(g.opponent_score,0)}`;
      cls=g.result==='W'?'resultWin':g.result==='L'?'resultLoss':'';
    }

    return `<div class="railScheduleRow">
      <span class="railWeek">W${g.week??'—'}</span>
      <span class="railOpponent">
        ${teamLogo(opp,'railOppLogo')}
        <span>
          <b>${g.site==='AWAY'?'@ ':g.site==='N'?'vs* ':'vs '}${esc(g.opponent)}</b>
          <small>
            ${rank?`<span class="${rankClass(rank)}">#${rank}</span> · `:''}
            ${hasNumber(opp?.team_rating)?num(opp.team_rating):'NR'}
            ${g.is_conference_game?' · CONF':''}
          </small>
        </span>
      </span>
      <span class="${cls}">${status}</span>
      <b class="${probabilityClass(g.team_probability)}">${g.completed?'—':pct(g.team_probability)}</b>
    </div>`;
  }).join('');

  const season=seasonProjectedRecord(row);

  return `<div class="railScheduleHead">
    <span>WK</span><span>OPPONENT</span><span>STATUS</span><span>WIN %</span>
  </div>
  ${body||'<p class="railEmpty">Schedule unavailable.</p>'}

  <div class="scheduleTotals compactScheduleTotals">
    <div><span>CURRENT RECORD</span><b>${row.record?.wins??0}-${row.record?.losses??0}</b></div>
    <div><span>PROJECTED RECORD</span><b>${season?`${num(season.wins)}-${num(season.losses)}`:'—'}</b></div>
  </div>`;
}

function renderRailMarket(row){
  if(state.mode==='wins'){
    return `<div class="railSection"><h3>WIN TOTAL · ${esc(row.win_direction||'')}</h3>${fourBookBoard(row,'wins')}</div>`;
  }

  if(state.mode==='title'){
    return `<div class="railSection"><h3>CONFERENCE TITLE</h3>${fourBookBoard(row,'title')}</div>`;
  }

  return `<div class="railSection"><h3>MAKE CFP</h3>${fourBookBoard(row,'cfp')}</div>
    <div class="railSection"><h3>NATIONAL TITLE</h3>${fourBookBoard(row,'national')}</div>`;
}

function renderRailHistory(row){
  const specs={
    wins:{
      model:'model_projected_wins',
      market:'market_win_total',
      label:'WIN TOTAL'
    },
    title:{
      model:'conference_title_model_prob',
      market:'conference_title_market_prob',
      label:'CONFERENCE TITLE'
    },
    playoff:{
      model:'cfp_model_prob',
      market:'cfp_market_prob',
      label:'MAKE CFP'
    }
  };

  const spec=specs[state.mode]||specs.wins;
  const history=(row.history||[]).slice(-10);

  if(!history.length){
    return '<p class="railEmpty">Historical futures checkpoints unavailable.</p>';
  }

  return `<div class="railHistoryHead"><span>${spec.label}</span><b>MODEL</b><b>MARKET</b></div>
    ${history.map(h=>{
      const prob=state.mode!=='wins';
      return `<div class="railHistoryRow">
        <span>${esc(h.checkpoint_date||'Checkpoint')}</span>
        <b>${prob?pct(h[spec.model]):num(h[spec.model])}</b>
        <b>${prob?pct(h[spec.market]):num(h[spec.market])}</b>
      </div>`;
    }).join('')}`;
}

function renderRail(){
  const rail=document.getElementById('futuresRail');
  const row=rowForTeam(state.selectedTeam);

  if(!rail||!row)return;

  const content=
    state.railTab==='schedule'?renderRailSchedule(row):
    state.railTab==='scenario'?renderRailScenario(row):
    state.railTab==='market'?renderRailMarket(row):
    state.railTab==='history'?renderRailHistory(row):
    renderRailOverview(row);

  const rank=row.overall_rank??row.rank;
  const record=`${row.record?.wins??0}-${row.record?.losses??0}`;

  rail.innerHTML=`<div class="futuresRailHead compactRailHead">
    ${teamLogo(row,'railTeamLogo')}
    <div class="compactTeamIdentity">
      <span class="compactTeamRank ${rankClass(rank)}">#${rank??'—'}</span>
      <b class="compactTeamName">${esc(row.team)}</b>
      <span>${esc(row.conference||'IND')}</span>
      <span>Rating ${num(row.team_rating)}</span>
      <span>Record ${record}</span>
    </div>
  </div>

  <nav class="futuresRailTabs">
    ${['overview','schedule','scenario','market','history'].map(tab=>
      `<button data-rail-tab="${tab}" class="${state.railTab===tab?'active':''}">${tab.toUpperCase()}</button>`
    ).join('')}
  </nav>

  <section class="futuresRailBody">${content}</section>`;

  rail.querySelectorAll('[data-rail-tab]').forEach(button=>{
    button.onclick=()=>{
      state.railTab=button.dataset.railTab;
      renderRail();

      if(state.railTab==='scenario'&&!state.scenario.loaded){
        ensureScenarioUniverse();
      }
    };
  });

  if(state.railTab==='scenario'){
    bindScenarioRail();
  }
}

function renderFourBookTooltip(button){
  const data=JSON.parse(decodeURIComponent(button.dataset.fourQuotes));
  const row=rowForTeam(data.team);
  if(!row)return;

  const qd=quoteKind(row,data.kind);

  quotePanel.innerHTML=`<div class="quoteHead">
    <span>${esc(row.team)} · ${esc(qd.label)}</span>
    <button class="detailButton" id="quoteClose">Close</button>
  </div>
  ${BOOKS.map(book=>{
    const q=qd.quotes?.[book];
    const best=book===qd.bestBook;

    if(!q){
      return `<div class="fourBookTooltipRow missingBook">
        <span>${bookLogo(book)}</span>
        <b>—</b>
        <small>NO QUOTE</small>
      </div>`;
    }

    const price=data.kind==='wins'
      ? qd.side==='Under'
        ? q.under_price
        : q.over_price
      : q.price;

    const line=data.kind==='wins'&&hasNumber(q.number)
      ? `${qd.side?.slice(0,1)||''} ${num(q.number)}`
      : '';

    const when=q.pulled_at
      ? fmtExact(q.pulled_at)
      : q.observed_date
        ? fmtObserved(q.observed_date)
        : 'Timestamp unavailable';

    return `<div class="fourBookTooltipRow ${best?'bestBookRow':''}">
      <span>${bookLogo(book)}</span>
      <b>${line?`${esc(line)} · `:''}${quoteOdds(q,qd.side)}</b>
      <small>${best?'BEST · ':''}${esc(when)}</small>
    </div>`;
  }).join('')}`;

  const rect=button.getBoundingClientRect();
  quotePanel.style.left=Math.max(10,Math.min(rect.left,innerWidth-380))+'px';
  quotePanel.style.top=Math.max(10,Math.min(rect.bottom+6,innerHeight-330))+'px';
  quotePanel.hidden=false;

  document.getElementById('quoteClose').onclick=()=>quotePanel.hidden=true;
}

function bindFourBookTooltips(){
  const canHover=window.matchMedia?.('(hover:hover) and (pointer:fine)')?.matches;

  document.querySelectorAll('[data-four-quotes]').forEach(button=>{
    button.onclick=event=>{
      event.stopPropagation();
      renderFourBookTooltip(button);
    };

    if(canHover){
      button.onmouseenter=()=>{
        renderFourBookTooltip(button);
      };

      button.onmouseleave=()=>{
        window.setTimeout(()=>{
          if(!quotePanel.matches(':hover'))quotePanel.hidden=true;
        },120);
      };
    }
  });

  quotePanel.onmouseleave=()=>{
    if(canHover)quotePanel.hidden=true;
  };
}

function applyMobileMetricLabels(){
  const labels=[...head.querySelectorAll('th')].map(th=>
    String(th.textContent||'')
      .replace(/[▲▼↕]/g,'')
      .replace(/\s+/g,' ')
      .trim()
  );

  rows.querySelectorAll('tr').forEach(tr=>{
    [...tr.children].forEach((cell,index)=>{
      cell.dataset.label=index===0?'':(labels[index]||'');
    });
  });
}

function sortControlEdgeKey(){
  if(state.mode==='title')return 'title_edge';
  if(state.mode==='playoff')return 'cfp_edge';
  return 'win_edge';
}

function syncSortControl(){
  const select=document.getElementById('futSort');
  if(!select)return;

  if(state.sortKey==='rank'&&state.sortDir==='asc'){
    select.value='default';
  }else if(state.sortKey==='model_wins'&&state.sortDir==='desc'){
    select.value='model_wins';
  }else if(state.sortKey===sortControlEdgeKey()&&state.sortDir==='desc'){
    select.value='edge';
  }else if(state.sortKey==='swing'&&state.sortDir==='desc'){
    select.value='swing';
  }else{
    select.value='custom';
  }
}

function installSortControl(){
  const controls=document.getElementById('futuresCommandControls');
  if(!controls||document.getElementById('futSort'))return;

  const label=document.createElement('label');
  label.className='futSortControl';
  label.innerHTML=`<span>Sort</span>
    <select id="futSort">
      <option value="default">Default</option>
      <option value="edge">Edge</option>
      <option value="model_wins">Model Wins</option>
      <option value="swing">Postseason Swing</option>
      <option value="custom" hidden>Column Sort</option>
    </select>`;

  const reset=controls.querySelector('button');
  if(reset)reset.before(label);
  else controls.appendChild(label);

  label.querySelector('select').onchange=event=>{
    const value=event.target.value;

    if(value==='edge'){
      state.sortKey=sortControlEdgeKey();
      state.sortDir='desc';
    }else if(value==='model_wins'){
      state.sortKey='model_wins';
      state.sortDir='desc';
    }else if(value==='swing'){
      if(state.mode==='wins'){
        state.sortKey='rank';
        state.sortDir='asc';
      }else{
        state.sortKey='swing';
        state.sortDir='desc';
      }
    }else{
      state.sortKey='rank';
      state.sortDir='asc';
    }

    renderCommandCenter();
  };

  syncSortControl();
}

function renderCommandCenter(){
  if(!state.scenario.loaded&&!state.scenario.loading){
    void ensureScenarioUniverse();
  }
  if(!D)return;

  let data=sortedVisibleRows();

  if(!data.some(r=>r.team===state.selectedTeam)){
    state.selectedTeam=data[0]?.team||null;
  }

  document.querySelectorAll('.tabs button').forEach(button=>{
    button.classList.toggle('active',button.dataset.mode===state.mode);
  });

  if(state.mode==='title')renderConference(data);
  else if(state.mode==='playoff')renderPlayoffs(data);
  else renderWins(data);

  if(!data.length){
    rows.innerHTML='<tr><td colspan="10" class="empty">No matching futures markets.</td></tr>';
  }

  renderMobileTables(data);

  applyMobileMetricLabels();
  syncSortControl();

  bindSorting();
  bindSelection();
  bindFourBookTooltips();
  renderScenarioBanner();
  renderRail();
}

function fmtExact(value){
  if(!value)return'—';

  return new Date(value).toLocaleString('en-US',{
    timeZone:'America/New_York',
    month:'short',
    day:'numeric',
    hour:'numeric',
    minute:'2-digit'
  });
}

function fmtObserved(value){
  if(!value)return'—';

  const d=new Date(`${value}T12:00:00`);
  return d.toLocaleDateString('en-US',{
    month:'short',
    day:'numeric'
  });
}

function latestBookEvidence(field,book){
  let exact=[];
  let dates=[];

  for(const row of D.rows||[]){
    const q=row?.[field]?.[book];
    if(!q)continue;
    if(q.pulled_at)exact.push(q.pulled_at);
    if(q.observed_date)dates.push(q.observed_date);
  }

  if(exact.length){
    exact.sort();
    return {kind:'exact',value:exact.at(-1)};
  }

  if(dates.length){
    dates.sort();
    return {kind:'date',value:dates.at(-1)};
  }

  return null;
}

function freshnessCell(field,book,label){
  const evidence=latestBookEvidence(field,book);

  if(!evidence){
    return `<span class="bookFreshCell stale"><b>—</b></span>`;
  }

  let display='—';

  if(evidence.kind==='exact'){
    const d=new Date(evidence.value);
    display=Number.isNaN(d.getTime())
      ? '—'
      : d.toLocaleTimeString('en-US',{
          hour:'numeric',
          minute:'2-digit',
          timeZone:'America/New_York'
        });
  }else{
    const d=new Date(`${evidence.value}T12:00:00`);
    display=Number.isNaN(d.getTime())
      ? esc(evidence.value)
      : d.toLocaleDateString('en-US',{
          month:'short',
          day:'numeric'
        });
  }

  return `<span class="bookFreshCell current"><b>${display}</b></span>`;
}


function compactFreshTime(value){
  if(!value)return '—';
  const d=new Date(value);
  if(Number.isNaN(d.getTime()))return '—';
  return d.toLocaleString('en-US',{
    month:'short',
    day:'numeric',
    hour:'numeric',
    minute:'2-digit',
    timeZone:'America/New_York'
  }).replace(',', ' ·')+' ET';
}

function latestFuturesMarketTime(){
  const exact=[];
  const dated=[];

  ['win_quotes','title_quotes','playoff_quotes','national_title_quotes'].forEach(field=>{
    BOOKS.forEach(book=>{
      const evidence=latestBookEvidence(field,book);
      if(!evidence)return;

      if(evidence.kind==='exact'){
        const ms=new Date(evidence.value).getTime();
        if(Number.isFinite(ms))exact.push(ms);
      }else if(evidence.kind==='date'){
        const ms=new Date(`${evidence.value}T00:00:00-04:00`).getTime();
        if(Number.isFinite(ms))dated.push(ms);
      }
    });
  });

  const values=exact.length?exact:dated;
  return values.length?new Date(Math.max(...values)).toISOString():null;
}

function compactModelStatus(){
  const holder=document.getElementById('modelFreshRows');
  if(!holder)return;

  const mf=D?.model_freshness||{};
  const season=mf.season_simulation||{};
  const cfp=mf.playoff_simulation||{};
  const baseline=D?.weekly_baseline||{};

  const shortTime=value=>{
    if(!value)return '—';
    const d=new Date(value);
    if(Number.isNaN(d.getTime()))return '—';
    return d.toLocaleTimeString('en-US',{
      hour:'numeric',
      minute:'2-digit',
      timeZone:'America/New_York'
    });
  };

  const baselineDate=baseline.checkpoint_date
    ? new Date(`${baseline.checkpoint_date}T12:00:00`).toLocaleDateString('en-US',{
        month:'short',
        day:'numeric'
      }).toUpperCase()
    : '';

  const baselineText=baseline.status==='available'
    ? `W${baseline.prior_week}${baselineDate?` · ${baselineDate}`:''}`
    : 'Unavailable';

  holder.innerHTML=`
    <div class="compactModelTable">
      <div class="compactModelHeader">
        <span>SOURCE</span>
        <span>WEIGHT</span>
        <span>MODEL RUN</span>
        <span>TIME</span>
      </div>

      <div class="compactModelRow">
        <span>SP+</span>
        <b>25%</b>
        <span>SEASON SIM</span>
        <b>${shortTime(season.built_at)}</b>
      </div>

      <div class="compactModelRow">
        <span>FPI</span>
        <b>25%</b>
        <span>CFP SIM</span>
        <b>${shortTime(cfp.built_at)}</b>
      </div>

      <div class="compactModelRow">
        <span>TEAMRANKINGS</span>
        <b>25%</b>
        <span></span>
        <b></b>
      </div>

      <div class="compactModelRow sagarinNoteRow">
        <span>SAGARIN</span>
        <b>25%</b>
        <span class="modelMovementInline">
          Ratings/rank movement compares current values with the post–Week ${baseline.prior_week ?? '—'} reference baseline${baselineDate ? ` captured ${baselineDate}` : ''}.
        </span>
        <b></b>
      </div>
    </div>
  `;
}
function renderSportsbookFreshness(){
  const holder=document.getElementById('marketFreshRows');
  if(!holder)return;

  const latest=latestFuturesMarketTime();
  const qa=D?.market_qa||{};
  const qaStatus=String(qa.status||'unknown').toUpperCase();
  const warningCount=Array.isArray(qa.warnings)?qa.warnings.length:0;
  const errorCount=Array.isArray(qa.errors)?qa.errors.length:0;

  let qaClass='current';
  if(errorCount>0 || qaStatus==='FAIL' || qaStatus==='FAILED')qaClass='stale';
  else if(warningCount>0 || qaStatus==='WARN' || qaStatus==='WARNING')qaClass='warn';

  const status=document.getElementById('marketFreshStatus');
  if(status){
    status.textContent=errorCount>0?'STALE':'CURRENT';
    status.className=`freshStatus ${errorCount>0?'stale':'current'}`;
  }

  const compactEvidence=(field,book)=>{
    const evidence=latestBookEvidence(field,book);
    if(!evidence)return '—';

    let value=evidence.value;

    if(
      evidence.kind!=='exact' &&
      (field==='title_quotes' || field==='win_quotes') &&
      qa.generated_at
    ){
      value=qa.generated_at;
    }

    const d=new Date(value);
    if(Number.isNaN(d.getTime()))return '—';

    return d.toLocaleTimeString('en-US',{
      hour:'numeric',
      minute:'2-digit',
      timeZone:'America/New_York'
    });
  };

  const qaText=errorCount
    ? `FAIL ${errorCount}`
    : warningCount
      ? `WARN ${warningCount}`
      : 'PASS';

  holder.innerHTML=`
    <div class="compactMarketLead">
      <span>LAST MARKET REFRESH</span>
      <b>${latest?compactFreshTime(latest):'—'}</b>
    </div>

    <div class="compactMarketTable">
      <div class="compactMarketHeader">
        <span>BOOK</span>
        <span>WIN TOTAL</span>
        <span>CONF TITLE</span>
        <span>CFP</span>
        <span>NAT TITLE</span>
      </div>

      ${BOOKS.map(book=>`
        <div class="compactMarketRow">
          <span class="compactMarketBook">${bookLogo(book)}</span>
          <b>${compactEvidence('win_quotes',book)}</b>
          <b>${compactEvidence('title_quotes',book)}</b>
          <b>${compactEvidence('playoff_quotes',book)}</b>
          <b>${compactEvidence('national_title_quotes',book)}</b>
        </div>
      `).join('')}
    </div>

  `;

  const legacyQa=document.getElementById('marketQaRow');
  if(legacyQa)legacyQa.innerHTML='';
}

function installControls(){
  document.getElementById('dashboardControls')?.remove();
  document.getElementById('dashboardHelp')?.remove();
  document.getElementById('playoffFocus')?.remove();

  const legacy=document.querySelector('.filters');
  if(legacy)legacy.hidden=true;

  const highlights=document.getElementById('highlights');
  if(highlights)highlights.hidden=true;

  document.querySelector('.tabs [data-mode="bets"]')?.remove();

  let controls=document.getElementById('futuresCommandControls');

  if(!controls){
    controls=document.createElement('section');
    controls.id='futuresCommandControls';
    controls.className='futuresCommandControls';
    document.querySelector('.tabs').insertAdjacentElement('afterend',controls);
  }

  const conferences=[...new Set(
    (D.rows||[]).map(r=>r.conference).filter(Boolean)
  )].sort();

  controls.innerHTML=`<label>
    <span>Conference</span>
    <select id="futConference">
      <option value="all">All conferences</option>
      ${conferences.map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join('')}
    </select>
  </label>
  <label class="futSearchControl">
    <span>Team Search</span>
    <input id="futSearch" type="search" placeholder="Find a team">
  </label>
  <button type="button" id="futReset">Reset</button>`;

  futConference.value=state.conference;
  futSearch.value=state.search;

  futConference.onchange=()=>{
    state.conference=futConference.value;
    renderCommandCenter();
  };

  futSearch.oninput=()=>{
    state.search=futSearch.value;
    renderCommandCenter();
  };

  futReset.onclick=()=>{
    state.conference='all';
    state.search='';
    state.sortKey='rank';
    state.sortDir='asc';
    state.selectedTeam=null;
    futConference.value='all';
    futSearch.value='';
    renderCommandCenter();
  };
}

function installWorkspace(){
  if(document.getElementById('futuresWorkspace'))return;

  const card=document.querySelector('.card');
  if(!card)return;

  const workspace=document.createElement('div');
  workspace.id='futuresWorkspace';
  workspace.className='futuresWorkspace';

  card.parentNode.insertBefore(workspace,card);
  workspace.appendChild(card);

  const mobileTables=document.createElement('div');
  mobileTables.id='mobileFuturesTables';
  mobileTables.className='mobileFuturesTables';
  card.appendChild(mobileTables);

  const rail=document.createElement('aside');
  rail.id='futuresRail';
  rail.className='futuresRail';
  rail.setAttribute('aria-label','Futures team intelligence');
  workspace.appendChild(rail);
}

function installStyles(){
  if(document.getElementById('futuresCommandCenterFinalStyles'))return;

  const style=document.createElement('style');
  style.id='futuresCommandCenterFinalStyles';
  style.textContent=`
    .futuresCommandControls{
      display:grid;
      grid-template-columns:210px minmax(240px,430px) 90px;
      gap:8px;
      align-items:end;
      margin:10px 0;
    }
    .futuresCommandControls label{
      display:grid;
      gap:4px;
      color:var(--muted);
      font-size:10px;
      font-weight:950;
      letter-spacing:.06em;
      text-transform:uppercase;
    }
    .futuresCommandControls select,
    .futuresCommandControls input{
      width:100%;
      background:#091a34;
      border:1px solid var(--line);
      color:#fff;
      border-radius:7px;
      padding:9px 10px;
      font-size:13px;
      font-weight:800;
    }
    #futReset{
      height:39px;
      border:1px solid var(--line);
      background:#102949;
      color:#cfe4ff;
      border-radius:7px;
      font-weight:900;
      cursor:pointer;
    }
    .futuresWorkspace{
      display:grid;
      grid-template-columns:minmax(0,1fr) 390px;
      gap:10px;
      align-items:start;
    }
    .futuresWorkspace .card{min-width:0}
    .mobileFuturesTables{display:none}
    .futuresWorkspace .wrap{
      max-height:calc(100vh - 255px);
      overflow:auto;
    }
    .futuresWorkspace table{
      table-layout:auto;
      min-width:1180px;
    }
    .futuresWorkspace th,
    .futuresWorkspace td{
      padding:7px 7px;
      text-align:center;
      vertical-align:middle;
    }
    .futuresWorkspace th:first-child,
    .futuresWorkspace td:first-child{
      text-align:left;
      min-width:180px;
    }
    .futSort{
      border:0;
      background:none;
      color:inherit;
      font:inherit;
      font-weight:950;
      text-transform:uppercase;
      cursor:pointer;
      padding:0;
      white-space:nowrap;
    }
    .futSort:hover{color:#fff}
    .futTeamButton{
      display:flex;
      align-items:center;
      gap:8px;
      border:0;
      background:none;
      color:inherit;
      padding:0;
      cursor:pointer;
      text-align:left;
      width:100%;
    }

    .futTeamLogo,
    .oppLogo{
      background:#fff;
      border-radius:7px;
      padding:3px;
      box-sizing:border-box;
      box-shadow:0 0 0 1px rgba(255,255,255,.16);
    }

    .teamUnderdogProbability{
      color:#ffd166!important;
      font-weight:900!important;
    }

.futTeamLogo{
      width:30px;
      height:30px;
      object-fit:contain;
      flex:0 0 auto;
    }
    .futTeamIdentity{
      display:grid;
      min-width:0;
    }
    .futTeamIdentity>b{
      overflow:hidden;
      text-overflow:ellipsis;
      white-space:nowrap;
      font-size:12px;
    }
    .futTeamIdentity small{
      color:var(--muted);
      font-size:9px;
    }
    .ratingStack{display:grid}
    .ratingStack>b{font-size:12px}
    .ratingStack small{
      color:var(--muted);
      font-size:10px;
      font-weight:850;
    }
    .rankElite{color:#39e89a!important}
    .rankStrong{color:#a9df6a!important}
    .rankGood{color:#f4cd4b!important}
    .rankMid{color:#f28c45!important}
    .rankLow{color:#ff626f!important}
    .probStrong{color:#39e89a!important}
    .probGood{color:#a9df6a!important}
    .probEven{color:#f4cd4b!important}
    .probWeak{color:#f28c45!important}
    .probLow{color:#ff626f!important}
    .nextGameCell{
      display:flex;
      align-items:center;
      justify-content:center;
      gap:6px;
      min-width:125px;
    }
    .nextGameCell>span{
      display:grid;
      text-align:left;
    }
    .nextGameCell b{
      font-size:10px;
      white-space:nowrap;
    }
    .nextGameCell small{
      font-size:9px;
      font-weight:900;
    }
    .oppLogo,.railOppLogo{
      width:24px;
      height:24px;
      object-fit:contain;
    }
    .teamRankBadge{
      width:24px;
      min-width:24px;
      text-align:center;
      font-size:10px;
      font-weight:950;
    }
    .metricMove{
      display:flex;
      align-items:center;
      justify-content:center;
      gap:4px;
      white-space:nowrap;
    }
    .moveUp{color:var(--green);font-weight:950}
    .moveDown{color:var(--red);font-weight:950}
    .moveFlat{color:var(--muted);font-weight:950}
    .projWinStack,.sosStack{
      display:grid;
      justify-items:center;
      gap:1px;
    }
    .projWinStack small,.sosStack small{
      color:var(--muted);
      font-size:8px;
      font-weight:900;
    }
    .marketCol{background:#17132b!important}
    th.marketCol{background:#56356f!important}
    .bestMarketButton{
      border:0;
      background:none;
      color:inherit;
      cursor:pointer;
      display:flex;
      align-items:center;
      justify-content:center;
      gap:6px;
      width:100%;
      padding:2px 4px;
    }
    .bestBookLogo{
      display:flex;
      align-items:center;
      justify-content:center;
    }
    .bestMarketStack{
      display:grid;
      justify-items:start;
      line-height:1.05;
    }
    .bestPrimary{
      font-size:12px;
      font-weight:950;
      color:#fff;
    }
    .bestSecondary{
      font-size:9px;
      font-weight:900;
      color:var(--muted);
    }
    .futBookLogo{
      width:25px;
      height:18px;
      object-fit:contain;
      background:#fff;
      border-radius:4px;
      padding:2px;
    }
    tr.selectedRow td{
      background:#12365a!important;
      box-shadow:inset 0 1px 0 #4da9ff55,inset 0 -1px 0 #4da9ff55;
    }
    tr.selectedRow td:first-child{
      box-shadow:inset 4px 0 0 var(--blue),inset 0 1px 0 #4da9ff55,inset 0 -1px 0 #4da9ff55;
    }
    .futuresRail{
      position:sticky;
      top:92px;
      height:calc(100vh - 108px);
      overflow:auto;
      border:1px solid #4777a8;
      background:#07172d;
      border-radius:10px;
      padding:11px;
    }
    .futuresRailHead{
      border-bottom:1px solid var(--line);
      padding-bottom:9px;
    }
    .futuresRailHead>div{
      display:flex;
      align-items:center;
      gap:9px;
    }
    .futuresRailHead span{display:grid}
    .futuresRailHead small{
      color:var(--muted);
      font-size:10px;
    }
    .railTeamLogo{
      width:34px;
      height:34px;
      object-fit:contain;
    }
    .futuresRailTabs{
      display:grid;
      grid-template-columns:repeat(4,1fr);
      gap:4px;
      margin:9px 0;
    }
    .futuresRailTabs button{
      border:1px solid var(--line);
      background:#091a34;
      color:var(--muted);
      border-radius:6px;
      padding:7px 3px;
      font-size:9px;
      font-weight:950;
      cursor:pointer;
    }
    .futuresRailTabs button.active{
      background:#fff;
      color:#07172d;
      border-color:#fff;
    }
    .railOverviewGrid{
      display:grid;
      grid-template-columns:repeat(3,1fr);
      gap:6px;
      margin-bottom:8px;
    }
    .railOverviewGrid>div{
      border:1px solid #21466d;
      background:#0b1c35;
      border-radius:7px;
      padding:7px;
      text-align:center;
    }
    .railOverviewGrid span,
    .scheduleTotals span{
      display:block;
      color:var(--muted);
      font-size:8px;
      font-weight:950;
      letter-spacing:.05em;
    }
    .railOverviewGrid b{font-size:13px}
    .railSection{
      border:1px solid #21466d;
      background:#0b1c35;
      border-radius:8px;
      padding:8px;
      margin-top:8px;
    }
    .railSection h3{
      margin:0 0 7px;
      color:#cfe4ff;
      font-size:10px;
      letter-spacing:.06em;
    }
    .railSnapshotRow{
      display:grid;
      grid-template-columns:1fr auto auto;
      gap:8px;
      align-items:center;
      border-top:1px solid #17345c;
      padding:7px 0;
      font-size:10px;
    }
    .railSnapshotRow span{color:var(--muted)}
    .railScheduleHead,
    .railScheduleRow{
      display:grid;
      grid-template-columns:28px minmax(145px,1fr) 82px 50px;
      gap:5px;
      align-items:center;
    }
    .railScheduleHead{
      color:var(--muted);
      font-size:8px;
      font-weight:950;
      padding:4px 0;
    }
    .railScheduleRow{
      border-top:1px solid #17345c;
      padding:6px 0;
      font-size:9px;
    }
    .railOpponent{
      display:flex;
      align-items:center;
      gap:6px;
      min-width:0;
    }
    .railOpponent>span{display:grid;min-width:0}
    .railOpponent b{
      white-space:nowrap;
      overflow:hidden;
      text-overflow:ellipsis;
    }
    .railOpponent small{
      color:var(--muted);
      font-size:8px;
    }
    .railScheduleRow>:last-child{text-align:right}
    .resultWin{color:var(--green);font-weight:950}
    .resultLoss{color:var(--red);font-weight:950}
    .scheduleTotals{
      margin-top:10px;
      border-top:2px solid #31537b;
      padding-top:7px;
    }
    .scheduleTotals>div{
      display:flex;
      justify-content:space-between;
      gap:10px;
      padding:5px 0;
      border-top:1px solid #17345c;
    }
    .scheduleTotals span{font-size:8px}
    .scheduleTotalWins{
      margin-top:4px;
      background:#102d35;
      padding:8px!important;
      border-radius:6px;
    }
    .scheduleTotalWins b{
      color:var(--green);
      font-size:15px;
    }
    .railMarketBoard{display:grid}
    .railBookRow,
    .fourBookTooltipRow{
      display:grid;
      grid-template-columns:50px 1fr auto;
      gap:8px;
      align-items:center;
      border-top:1px solid #17345c;
      padding:7px 3px;
    }
    .railBookRow>b,
    .fourBookTooltipRow>b{
      text-align:right;
    }
    .railBookRow small,
    .fourBookTooltipRow small{
      color:var(--muted);
      font-size:8px;
      font-weight:950;
    }
    .bestBookRow{
      background:#102d35;
      box-shadow:inset 3px 0 0 var(--green);
    }
    .missingBook{opacity:.42}
    .railHistoryHead,
    .railHistoryRow{
      display:grid;
      grid-template-columns:1fr auto auto;
      gap:10px;
      border-top:1px solid #17345c;
      padding:7px 2px;
      font-size:10px;
    }
    .railHistoryHead{
      color:var(--muted);
      border:0;
      font-size:8px;
    }
    .bookFreshHeader,
    .bookFreshRow{
      display:grid;
      grid-template-columns:44px repeat(4,minmax(0,1fr));
      gap:5px;
      align-items:center;
    }
    .bookFreshHeader{
      color:var(--muted);
      font-size:8px;
      font-weight:950;
      padding-bottom:3px;
    }
    .bookFreshRow{
      border-top:1px solid #17345c;
      padding:4px 0;
    }
    .bookFreshLogo{
      display:flex;
      align-items:center;
    }
    .bookFreshCell{
      display:grid;
      text-align:center;
      line-height:1.05;
    }
    .bookFreshCell small{
      color:var(--muted);
      font-size:7px;
      font-weight:950;
    }
    .bookFreshCell b{
      font-size:8px;
      white-space:nowrap;
    }
    .bookFreshCell.current b{color:var(--green)}
    .bookFreshCell.stale b{color:var(--red)}
    .muted,.railEmpty{color:var(--muted)}
    @media(max-width:1280px){
      .futuresWorkspace{grid-template-columns:minmax(0,1fr) 340px}
      .futuresRail{padding:8px}
    }
    @media(max-width:900px){
      .futuresCommandControls{
        grid-template-columns:1fr 1fr;
      }
      #futReset{grid-column:1/-1}
      .futuresWorkspace{
        display:flex;
        flex-direction:column;
      }
      .futuresRail{
        position:relative;
        top:auto;
        width:100%;
        height:auto;
        max-height:none;
        order:1;
      }
      .futuresWorkspace .card{order:1;width:100%;overflow:visible!important}
      .futuresWorkspace .wrap{display:none!important}
      .futuresRail{order:2}
      .mobileFuturesTables{display:block;width:100%}
      .mobileFuturesSection+ .mobileFuturesSection{margin-top:16px}
      .mobileFuturesSection h2{margin:8px 2px 6px;font-size:15px;color:#dbeaff}
      .mobileTableViewport{overflow:visible}
      .mobileFuturesTable{display:table!important;width:100%!important;min-width:0!important;table-layout:fixed!important;border-collapse:separate;border-spacing:0;background:var(--panel);border:1px solid var(--line);border-radius:9px;overflow:hidden}
      .mobileFuturesTable thead{display:table-header-group!important}
      .mobileFuturesTable tbody{display:table-row-group!important}
      .mobileFuturesTable tr{display:table-row!important;margin:0!important;padding:0!important;border:0!important;background:transparent!important}
      .mobileFuturesTable th,.mobileFuturesTable td{display:table-cell!important;height:auto!important;min-height:0!important;padding:8px 5px!important;vertical-align:middle!important;white-space:normal!important;text-align:right!important;border-top:1px solid #17345c!important}
      .mobileFuturesTable thead th{position:sticky!important;top:0!important;z-index:5!important;background:#132a50!important;border-top:0!important;font-size:9px!important}
      .mobileFuturesTable th:first-child,.mobileFuturesTable td:first-child{width:34%!important;text-align:left!important}
      .mobileFuturesTable th:nth-child(2),.mobileFuturesTable td:nth-child(2){width:16%!important}
      .mobileFuturesTable th:nth-child(3),.mobileFuturesTable td:nth-child(3){width:31%!important}
      .mobileFuturesTable th:nth-child(4),.mobileFuturesTable td:nth-child(4){width:19%!important}
      .mobileSortButton{border:0;background:transparent;color:#afbfda;font:inherit;font-weight:950;text-transform:uppercase;padding:4px 0;cursor:pointer}
      .mobileSortButton.active{color:#fff}
      .mobileTeamButton,.mobileBestButton{display:flex;align-items:center;gap:5px;width:100%;min-width:0;border:0;background:transparent;color:inherit;padding:0;text-align:left;cursor:pointer}
      .mobileTeamButton span,.mobileBestButton span{display:grid;min-width:0;line-height:1.1}
      .mobileTeamButton b{font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .mobileTeamButton small,.mobileBestButton small{font-size:8px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
      .mobileTeamLogo{width:23px;height:23px;object-fit:contain;background:#fff;border-radius:5px;padding:2px;flex:0 0 23px}
      .mobileBestButton{justify-content:flex-end}
      .mobileBestButton .futBookLogo{width:21px!important;height:16px!important;flex:0 0 21px}
      .mobileBestButton b{font-size:10px;white-space:nowrap}
      .mobileFuturesTable .good,.mobileFuturesTable .bad{font-size:10px;white-space:nowrap}
      .mobileDetailRow>td{padding:7px!important;background:#091a34!important;border-top:1px solid #4777a8!important}
      .mobileDetailRow>td>div{display:grid;grid-template-columns:repeat(4,1fr);gap:5px}
      .mobileDetailRow span{display:grid;text-align:center;padding:5px 2px;background:#0d2443;border-radius:5px}
      .mobileDetailRow small{font-size:7px;color:var(--muted);text-transform:uppercase;font-weight:900}
      .mobileDetailRow b{font-size:10px}
      .mobileDetailRow button{grid-column:1/-1;border:1px solid #315c88;background:#102949;color:#cfe4ff;border-radius:6px;padding:7px;font-size:10px;font-weight:900}
    }
  `;

  document.head.appendChild(style);
}

function enhance(){
  if(typeof D==='undefined'||!D){
    setTimeout(enhance,40);
    return;
  }

  installStyles();
  installControls();
  installWorkspace();

  document.querySelectorAll('.tabs button').forEach(button=>{
    if(!['wins','title','playoff'].includes(button.dataset.mode))return;

    button.onclick=()=>{
      state.mode=button.dataset.mode;

      if(state.mode==='title'){
        state.sortKey='title_model';
        state.sortDir='desc';
      }else if(state.mode==='playoff'){
        state.sortKey='cfp_model';
        state.sortDir='desc';
      }else{
        state.sortKey='rank';
        state.sortDir='asc';
      }

      state.railTab='overview';
      state.selectedTeam=null;
      renderCommandCenter();
    };
  });

  compactModelStatus();
  renderSportsbookFreshness();

  render=renderCommandCenter;
  mode='wins';

  renderCommandCenter();
}

window.FuturesDashboard={
  BOOKS,
  scheduleFor,
  seasonProjectedRecord
};

enhance();
installSortControl();

(function installCompactFuturesTable(){
  const style=document.createElement('style');
  style.id='futuresCompactTableV2';
  style.textContent=`
    @media (min-width:901px){
      .futuresWorkspace{
        min-width:0!important;
      }

      .futuresWorkspace .card,
      .futuresWorkspace .wrap{
        min-width:0!important;
        overflow-x:hidden!important;
      }

      .futuresWorkspace table{
        width:100%!important;
        min-width:0!important;
        table-layout:fixed!important;
      }

      .futuresWorkspace th,
      .futuresWorkspace td{
        padding-left:5px!important;
        padding-right:5px!important;
        font-size:12px!important;
        white-space:nowrap;
      }

      .futuresWorkspace th{
        font-size:10px!important;
        letter-spacing:0!important;
      }

      .futuresWorkspace th:nth-child(1),
      .futuresWorkspace td:nth-child(1){
        width:16%!important;
      }

      .futuresWorkspace th:nth-child(2),
      .futuresWorkspace td:nth-child(2){
        width:19%!important;
      }

      .futuresWorkspace th:nth-child(3),
      .futuresWorkspace td:nth-child(3){
        width:6%!important;
      }

      .futuresWorkspace th:nth-child(4),
      .futuresWorkspace td:nth-child(4){
        width:8%!important;
      }

      .futTeamButton{
        gap:5px!important;
        min-width:0!important;
      }

      .futTeamLogo{
        width:23px!important;
        height:23px!important;
        flex:0 0 23px!important;
      }

      .teamRankBadge{
        width:19px!important;
        min-width:19px!important;
      }

      .futTeamIdentity{
        min-width:0!important;
      }

      .metricMove{
        gap:3px!important;
        white-space:nowrap!important;
      }

      .moveUp,
      .moveDown,
      .moveFlat{
        font-size:10px!important;
      }

      .bestMarketButton{
        gap:4px!important;
        padding:1px 2px!important;
      }

      .futBookLogo{
        width:21px!important;
        height:16px!important;
      }

      .bestPrimary{
        font-size:11px!important;
      }

      .bestSecondary{
        font-size:9px!important;
      }

      .futuresWorkspace th:nth-last-child(2),
      .futuresWorkspace td:nth-last-child(2){
        width:7%!important;
      }

      .futuresWorkspace th:last-child,
      .futuresWorkspace td:last-child{
        width:5%!important;
        text-align:center!important;
      }

      .bet{
        padding:2px 5px!important;
        font-size:9px!important;
      }
    }
  `;
  document.head.appendChild(style);
})();

})();


/* FUTURES_DENSITY_RESPONSIVE_V1 */
(function installFuturesDensityResponsive(){
  if(typeof document==='undefined')return;

  const style=document.createElement('style');
  style.id='futuresDensityResponsiveV1';
  style.textContent=`
    @media (min-width:901px){
      .shell{
        padding-top:10px!important;
      }

      .hero{
        margin:7px 0 5px!important;
        align-items:center!important;
      }

      .hero h1{
        font-size:29px!important;
        line-height:1.05!important;
      }

      .hero p{
        margin:1px 0 0!important;
        font-size:12px!important;
        line-height:1.2!important;
      }

      .summary{
        gap:5px!important;
      }

      .tile{
        padding:4px 8px!important;
        border-radius:7px!important;
      }

      .tile span{
        font-size:8px!important;
      }

      .tile b{
        font-size:16px!important;
        line-height:1.1!important;
      }



    .freshnessGrid{
      display:grid!important;
      grid-template-columns:minmax(620px,1fr) minmax(650px,820px)!important;
      gap:6px!important;
      margin:3px 0 6px!important;
      align-items:start!important;
    }

    .freshCard{
      display:grid!important;
      grid-template-columns:150px minmax(0,1fr)!important;
      align-items:center!important;
      min-height:32px!important;
      padding:3px 8px!important;
      border-radius:4px!important;
      background:#0b1725!important;
    }

    .freshHead{
      display:flex!important;
      align-items:center!important;
      justify-content:flex-start!important;
      gap:8px!important;
      margin:0!important;
      min-width:0;
    }

    .freshHead strong{
      font-size:11px!important;
      letter-spacing:.06em!important;
      white-space:nowrap;
      color:#aebcd0;
    }

    .freshStatus{
      font-size:10px!important;
      font-weight:950!important;
      white-space:nowrap;
    }

    .freshRows{
      display:block!important;
      min-width:0;
    }


    .compactModelAuthority{
      display:flex;
      align-items:center;
      gap:8px;
      min-height:20px;
      white-space:nowrap;
      overflow:hidden;
      margin-bottom:1px;
    }

    .compactModelAuthority span{
      color:#8195ae;
      font-size:9px;
      font-weight:900;
      letter-spacing:.05em;
    }

    .compactModelAuthority b{
      color:#f3f7fc;
      font-size:11px;
      font-weight:950;
    }

    .compactMarketLead{
      display:flex;
      align-items:center;
      gap:8px;
      min-height:18px;
      margin-bottom:2px;
    }

    .compactMarketLead span{
      color:#8195ae;
      font-size:9px;
      font-weight:900;
      letter-spacing:.05em;
    }

    .compactMarketLead b{
      color:#fff;
      font-size:11px;
      font-weight:950;
    }


    .compactModelTable{
      display:grid;
      gap:0;
      width:max-content;
    }

    .compactModelHeader,
    .compactModelRow{
      display:grid;
      grid-template-columns:105px 55px 105px 92px;
      align-items:center;
      gap:7px;
      min-height:17px;
      width:max-content;
    }

    .compactModelHeader{
      color:#8195ae;
      font-size:8px;
      font-weight:900;
      letter-spacing:.04em;
    }

    .compactModelRow{
      border-top:1px solid #203a55;
      font-size:10px;
    }

    .compactModelRow>span{
      color:#dce7f5;
      font-weight:850;
    }

    .compactModelRow>b{
      color:#fff;
      font-size:10px;
      font-weight:950;
    }

    .sagarinNoteRow{
      align-items:start!important;
    }

    .modelMovementInline{
      grid-column:3 / 5!important;
      color:#aebed2!important;
      font-size:9px!important;
      font-weight:800!important;
      line-height:1.2!important;
      white-space:normal!important;
      max-width:235px!important;
      padding-top:1px!important;
    }

    .modelMovementNote{
      margin-top:5px;
      padding-top:4px;
      border-top:1px solid #203a55;
      color:#8195ae;
      font-size:9px;
      font-weight:750;
      line-height:1.2;
      white-space:nowrap;
    }

    .compactMarketTable{
      display:grid;
      gap:0;
    }

    .compactMarketHeader,
    .compactMarketRow{
      display:grid;
      grid-template-columns:38px repeat(4,minmax(76px,1fr));
      align-items:center;
      gap:5px;
      min-height:17px;
    }

    .compactMarketHeader{
      color:#8195ae;
      font-size:8px;
      font-weight:900;
      letter-spacing:.04em;
    }

    .compactMarketRow{
      border-top:1px solid #203a55;
    }

    .compactMarketRow b{
      color:#eef5ff;
      font-size:10px;
      font-weight:900;
    }

    .compactMarketBook{
      display:flex;
      align-items:center;
    }

    .compactMarketBook .futBookLogo{
      width:19px!important;
      height:15px!important;
      padding:1px!important;
    }

    .compactMarketQa{
      position:absolute;
      right:9px;
      top:5px;
      font-size:9px;
      font-weight:950;
    }

    .marketStatusCard{
      position:relative;
    }

    .compactMarketQa.current{color:var(--green)}
    .compactMarketQa.warn{color:#ffd166}

    .compactMarketQa.stale{color:var(--red)}

    .freshnessGrid{
      display:grid!important;
      grid-template-columns:660px max-content!important;
      gap:6px!important;
      align-items:stretch!important;
      justify-content:start!important;
      margin:3px 0 6px!important;
    }

    .modelStatusCard,
    .marketStatusCard{
      box-sizing:border-box!important;
      height:112px!important;
      min-height:112px!important;
      max-height:112px!important;
      align-self:stretch!important;
    }

    .modelStatusCard{
      display:grid!important;
      grid-template-columns:142px auto!important;
      align-items:start!important;
      width:max-content!important;
      min-width:0!important;
    }

    .modelStatusCard .freshHead{
      padding-top:3px!important;
    }

    #modelFreshRows{
      display:block!important;
      min-width:0!important;
      overflow:visible!important;
    }

    .modelSourceGrid{
      display:grid!important;
      grid-template-columns:72px 72px 118px 78px!important;
      gap:8px!important;
      align-items:center!important;
      justify-content:start!important;
      min-width:0!important;
    }

    .modelSourceGrid>span,
    .modelTimingGrid>span{
      display:flex!important;
      align-items:baseline!important;
      gap:5px!important;
      white-space:nowrap!important;
      min-width:0!important;
    }

    .modelSourceGrid small,
    .modelTimingGrid small{
      color:#8195ae!important;
      font-size:9px!important;
      font-weight:900!important;
      letter-spacing:.04em!important;
    }

    .modelSourceGrid b{
      color:#f4f7fb!important;
      font-size:12px!important;
      font-weight:950!important;
    }

    .modelTimingGrid{
      display:grid!important;
      grid-template-columns:145px 135px 170px!important;
      gap:8px!important;
      align-items:center!important;
      justify-content:start!important;
      border-top:1px solid #29435e!important;
      padding-top:6px!important;
    }

    .modelTimingGrid b{
      color:#fff!important;
      font-size:11px!important;
      font-weight:950!important;
    }

    .marketStatusCard{
      width:max-content!important;
      min-width:0!important;
      max-width:none!important;
      grid-template-columns:142px auto!important;
    }

    .marketStatusCard #marketFreshRows{
      width:auto!important;
      min-width:0!important;
    }

    .compactMarketTable{
      width:max-content!important;
    }

    .compactMarketHeader,
    .compactMarketRow{
      grid-template-columns:32px 74px 76px 66px 74px!important;
      gap:6px!important;
      width:max-content!important;
    }

    .compactMarketLead{
      width:max-content!important;
      min-width:0!important;
    }

    .compactMarketLead b{
      margin-right:4px!important;
    }

    .compactMarketQa{
      right:7px!important;
      top:5px!important;
    }


    .compactModelStrip,
    .compactMarketStrip{
      display:flex;
      align-items:center;
      gap:0;
      min-height:24px;
      overflow:hidden;
    }

    .compactStatusItem{
      display:inline-flex;
      align-items:center;
      gap:5px;
      min-height:22px;
      padding:0 12px;
      border-left:1px solid #29435e;
      white-space:nowrap;
    }

    .compactStatusItem:first-child{
      border-left:0;
    }

    .compactStatusItem small{
      color:#8195ae;
      font-size:9px;
      font-weight:900;
      letter-spacing:.05em;
    }

    .compactStatusItem b{
      color:#eef5ff;
      font-size:12px;
      font-weight:950;
    }

    .compactPrimary b{
      color:#fff;
    }

    .compactBook{
      display:inline-flex;
      align-items:center;
    }

    .compactBook .futBookLogo{
      width:20px!important;
      height:16px!important;
      padding:2px!important;
      border-radius:4px!important;
    }

    .compactStatusItem b.current{
      color:var(--green);
    }

    .compactStatusItem b.warn{
      color:#ffd166;
    }

    .compactQa.current b{
      color:var(--green);
    }

    .compactQa.warn b{
      color:#ffd166;
    }

    .compactQa.stale b{
      color:var(--red);
    }

    .freshnessGrid{
      grid-template-columns:minmax(360px,.62fr) minmax(700px,1.38fr)!important;
      align-items:start!important;
      gap:7px!important;
      margin:4px 0 7px!important;
    }

    .freshCard{
      padding:7px 9px!important;
      align-self:start!important;
    }

    .modelStatusCard{
      min-height:0!important;
    }

    .marketStatusCard{
      min-height:0!important;
    }

    #modelFreshRows{
      display:grid!important;
      grid-template-columns:repeat(3,minmax(0,1fr))!important;
      gap:9px!important;
    }

    #modelFreshRows .freshRow{
      display:grid!important;
      grid-template-columns:1fr!important;
      gap:1px!important;
      align-content:start!important;
      min-height:0!important;
      font-size:11px!important;
      line-height:1.2!important;
    }

    #modelFreshRows .freshRow span:first-child{
      font-size:9px!important;
      color:#91a8c5!important;
      font-weight:900!important;
    }

    #modelFreshRows .freshRow span:last-child{
      text-align:left!important;
      white-space:normal!important;
      overflow:visible!important;
      font-size:11px!important;
      color:#fff!important;
      font-weight:900!important;
    }

    .freshHead{
      margin-bottom:7px!important;
    }

    .freshHead strong{
      font-size:11px!important;
      letter-spacing:.07em!important;
    }

    .freshStatus{
      font-size:10px!important;
    }

    .freshRows{
      gap:5px!important;
    }

    .freshRow{
      min-height:22px;
      font-size:12px!important;
      line-height:1.3!important;
    }

    .freshRow span:first-child{
      color:#9fb1ca!important;
      font-weight:800!important;
    }

    .freshRow span:last-child{
      color:#f2f6fb!important;
      font-weight:850!important;
    }

    .marketFreshnessLead{
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:8px;
      margin:0 0 5px;
      padding:4px 7px;
      border:1px solid #315c88;
      border-radius:7px;
      background:#102949;
    }

    .marketFreshnessLead span{
      color:#9fb1ca;
      font-size:9px;
      font-weight:900;
      letter-spacing:.07em;
      text-transform:uppercase;
    }

    .marketFreshnessLead b{
      color:#fff;
      font-size:11px;
      font-weight:950;
    }

    .bookFreshRow{
      min-height:21px!important;
      border-top:1px solid #17345c;
    }

    .bookFreshLogo{
      min-width:40px!important;
    }

    .bookFreshLogo img,
    .bookFreshLogo .futBookLogo{
      width:21px!important;
      height:17px!important;
    }

    .freshTime,
    .bookFreshTime{
      color:#f2f6fb!important;
    }

    .marketQaRow{
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:12px;
      border-top:1px solid #17345c;
      margin-top:4px;
      padding-top:5px;
      color:#9fb1ca;
      font-size:11px;
      font-weight:850;
    }

    .marketQaBadge{
      display:inline-flex;
      align-items:center;
      gap:5px;
      border:1px solid #755f26;
      border-radius:999px;
      padding:3px 8px;
      color:#ffd166;
      background:#ffd16612;
      font-size:10px;
      font-weight:950;
    }

.freshnessGrid{
        gap:6px!important;
        margin:3px 0 6px!important;
      }

      .freshCard{
        padding:4px 8px!important;
        border-radius:8px!important;
      }

      .freshHead{
        margin-bottom:1px!important;
      }

      .freshHead strong{
        font-size:9px!important;
      }

      .freshStatus{
        font-size:9px!important;
      }

      #modelFreshRows .freshRow{
        font-size:9px!important;
        line-height:1.12!important;
      }

      .bookFreshHeader,
      .bookFreshRow{
        min-height:20px!important;
        padding:1px 0!important;
      }

      .bookFreshHeader{
        font-size:9px!important;
      }

      .bookFreshCell small{
        font-size:8px!important;
        line-height:1!important;
      }

      .bookFreshCell b{
        font-size:10.5px!important;
        line-height:1.05!important;
      }

      .bookFreshLogo img,
      .bookFreshLogo .futBookLogo{
        width:20px!important;
        height:15px!important;
      }

      #marketQaRow .freshRow{
        font-size:9px!important;
        line-height:1.1!important;
      }

      .tabs{
        margin:6px 0!important;
      }

      .tabs button{
        padding:7px 13px!important;
        font-size:12px!important;
      }

      .dashboardControls{
        margin:5px 0 6px!important;
        gap:6px!important;
      }

      .dashboardControls label{
        gap:2px!important;
        font-size:9px!important;
      }

      .dashboardControls select,
      .dashboardControls input{
        padding:7px 9px!important;
        font-size:12px!important;
      }

      .resetButton{
        height:34px!important;
      }

      .dashboardHelp,
      .dashboardSummary{
        margin-top:4px!important;
        margin-bottom:5px!important;
      }

      .futuresWorkspace .wrap,
      .card .wrap{
        max-height:none!important;
        overflow-y:visible!important;
      }

      .futuresWorkspace{
        align-items:start!important;
      }

      .futuresRail{
        width:390px!important;
        min-width:390px!important;
      }

      .compactRailHead{
        display:flex!important;
        align-items:center!important;
        gap:8px!important;
        padding:6px 0!important;
        min-height:46px!important;
      }

      .compactRailHead .railTeamLogo{
        width:30px!important;
        height:30px!important;
        flex:0 0 auto!important;
      }

      .compactTeamIdentity{
        display:flex!important;
        align-items:center!important;
        flex-wrap:wrap!important;
        gap:3px 8px!important;
        min-width:0!important;
        line-height:1.1!important;
      }

      .compactTeamRank{
        font-size:13px!important;
        font-weight:950!important;
      }

      .compactTeamName{
        font-size:15px!important;
        white-space:nowrap!important;
      }

      .compactTeamIdentity>span:not(.compactTeamRank){
        color:var(--muted)!important;
        font-size:9px!important;
        font-weight:850!important;
        white-space:nowrap!important;
      }

      .futuresRailTabs{
        margin:4px 0!important;
        gap:4px!important;
      }

      .futuresRailTabs button{
        padding:5px 4px!important;
        font-size:8px!important;
      }

      .railScheduleHead,
      .railScheduleRow{
        grid-template-columns:25px minmax(135px,1fr) 72px 48px!important;
        gap:4px!important;
      }

      .railScheduleHead{
        padding:2px 0!important;
        font-size:7px!important;
      }

      .railScheduleRow{
        padding:4px 0!important;
        min-height:38px!important;
        font-size:9px!important;
      }

      .railOpponent{
        gap:5px!important;
      }

      .railOppLogo{
        width:21px!important;
        height:21px!important;
      }

      .railOpponent b{
        font-size:9px!important;
      }

      .railOpponent small{
        font-size:7.5px!important;
      }

      .compactScheduleTotals{
        margin-top:5px!important;
        padding-top:4px!important;
      }

      .compactScheduleTotals>div{
        padding:4px 0!important;
      }

      .compactScheduleTotals span{
        font-size:8px!important;
      }

      .compactScheduleTotals b{
        font-size:12px!important;
      }
    }

    @media (max-width:900px){
      .shell{
        padding:8px!important;
      }

      .hero{
        margin:8px 0 6px!important;
        display:block!important;
      }

      .hero h1{
        font-size:25px!important;
      }

      .hero p{
        font-size:11px!important;
        line-height:1.25!important;
      }

      .freshnessGrid{
        grid-template-columns:1fr!important;
        gap:5px!important;
        margin:5px 0!important;
      }

      .freshCard{
        padding:5px 7px!important;
      }

      .bookFreshHeader,
      .bookFreshRow{
        grid-template-columns:34px repeat(4,minmax(52px,1fr))!important;
      }

      .bookFreshCell b{
        font-size:9px!important;
      }

      .bookFreshCell small{
        font-size:7px!important;
      }

      .tabs{
        gap:5px!important;
        margin:6px 0!important;
      }

      .tabs button{
        flex:1 1 auto!important;
        padding:8px 9px!important;
        font-size:11px!important;
      }

      .dashboardControls{
        grid-template-columns:1fr 1fr!important;
        margin:6px 0!important;
        gap:6px!important;
      }

      .searchControl{
        grid-column:1/-1!important;
      }

      .resetButton{
        grid-column:1/-1!important;
      }

      .futuresWorkspace .wrap,
      .card .wrap{
        max-height:none!important;
        overflow:visible!important;
      }

      .futuresWorkspace table{
        min-width:0!important;
      }

      .futuresRail{
        width:100%!important;
        min-width:0!important;
        position:relative!important;
        max-height:none!important;
        overflow:visible!important;
      }

      .compactRailHead{
        display:flex!important;
        align-items:center!important;
        gap:8px!important;
        padding:7px 0!important;
      }

      .compactRailHead .railTeamLogo{
        width:30px!important;
        height:30px!important;
      }

      .compactTeamIdentity{
        display:flex!important;
        align-items:center!important;
        flex-wrap:wrap!important;
        gap:3px 7px!important;
      }

      .compactTeamName{
        font-size:15px!important;
      }

      .compactTeamIdentity>span{
        font-size:9px!important;
      }

      .futuresRailTabs{
        position:sticky!important;
        top:0!important;
        z-index:5!important;
        background:#07172d!important;
        padding:4px 0!important;
        margin:2px 0 4px!important;
      }

      .futuresRailTabs button{
        padding:7px 3px!important;
        font-size:8px!important;
      }

      .railScheduleHead,
      .railScheduleRow{
        grid-template-columns:25px minmax(120px,1fr) 70px 48px!important;
        gap:4px!important;
      }

      .railScheduleRow{
        padding:5px 0!important;
      }

      .railOpponent b{
        white-space:normal!important;
      }

      .compactScheduleTotals{
        margin-bottom:8px!important;
      }
    }

    @media (max-width:560px){
      .bookFreshHeader,
      .bookFreshRow{
        grid-template-columns:28px repeat(4,minmax(46px,1fr))!important;
      }

      .bookFreshHeader{
        font-size:7px!important;
      }

      .bookFreshCell b{
        font-size:8px!important;
      }

      .railScheduleHead,
      .railScheduleRow{
        grid-template-columns:23px minmax(105px,1fr) 62px 45px!important;
      }

      .railScheduleRow{
        font-size:8px!important;
      }

      .railOpponent b{
        font-size:8.5px!important;
      }
    }
  `;

  document.head.appendChild(style);
})();


/* FUTURES_DENSITY_FINISH_V2 */
(function installFuturesDensityFinishV2(){
  if(typeof document==='undefined')return;

  const style=document.createElement('style');
  style.id='futuresDensityFinishV2';
  style.textContent=`
    @media (min-width:901px){
      .freshnessGrid{
        grid-template-columns:minmax(300px,.72fr) minmax(620px,1.28fr)!important;
        align-items:stretch!important;
        gap:6px!important;
        margin:2px 0 4px!important;
      }

      .freshCard{
        padding:3px 7px!important;
        min-height:0!important;
      }

      .freshHead{
        min-height:17px!important;
        margin:0 0 1px!important;
      }

      #modelFreshRows{
        display:grid!important;
        grid-template-columns:repeat(3,minmax(0,1fr))!important;
        gap:4px!important;
        align-items:start!important;
      }

      #modelFreshRows .freshRow{
        display:grid!important;
        grid-template-columns:1fr!important;
        gap:0!important;
        padding:1px 3px!important;
        min-height:0!important;
        line-height:1.02!important;
      }

      #modelFreshRows .freshRow span:first-child{
        font-size:7px!important;
        line-height:1!important;
      }

      #modelFreshRows .freshRow span:last-child{
        font-size:8.5px!important;
        line-height:1.05!important;
        overflow:hidden!important;
        text-overflow:ellipsis!important;
        white-space:nowrap!important;
      }

      .bookFreshHeader{
        min-height:14px!important;
        padding:0!important;
        font-size:8px!important;
        line-height:1!important;
      }

      .bookFreshRow{
        min-height:17px!important;
        padding:0!important;
      }

      .bookFreshCell{
        min-height:0!important;
      }

      .bookFreshCell small{
        font-size:7px!important;
        line-height:1!important;
      }

      .bookFreshCell b{
        font-size:10.5px!important;
        line-height:1!important;
      }

      .bookFreshLogo img,
      .bookFreshLogo .futBookLogo{
        width:19px!important;
        height:14px!important;
      }

      #marketQaRow .freshRow{
        padding:1px 0 0!important;
        min-height:12px!important;
        font-size:8px!important;
        line-height:1!important;
      }

      .futuresCommandControls{
        display:grid!important;
        grid-template-columns:155px minmax(240px,1fr) 145px 70px!important;
        align-items:end!important;
        gap:6px!important;
        margin:4px 0 5px!important;
      }

      .futuresCommandControls label{
        display:grid!important;
        gap:2px!important;
        margin:0!important;
        font-size:8px!important;
      }

      .futuresCommandControls label>span{
        font-size:8px!important;
        line-height:1!important;
      }

      .futuresCommandControls select,
      .futuresCommandControls input{
        height:32px!important;
        padding:5px 8px!important;
        font-size:11px!important;
      }

      .futuresCommandControls button{
        height:32px!important;
        min-height:32px!important;
        margin:0!important;
      }

      .futuresRail{
        width:370px!important;
        min-width:370px!important;
      }
    }

    @media (max-width:900px){
      .futuresCommandControls{
        display:grid!important;
        grid-template-columns:1fr 1fr!important;
        gap:6px!important;
        margin:6px 0!important;
      }

      .futuresCommandControls .searchControl{
        grid-column:1/-1!important;
      }

      .futuresCommandControls .futSortControl{
        grid-column:auto!important;
      }

      .futuresCommandControls button{
        grid-column:1/-1!important;
      }

      .futuresWorkspace tbody td[data-label]{
        position:relative!important;
      }

      .futuresWorkspace tbody td[data-label]:not([data-label=""])::before{
        content:attr(data-label)!important;
        display:block!important;
        margin-bottom:2px!important;
        color:var(--muted)!important;
        font-size:7px!important;
        font-weight:900!important;
        letter-spacing:.35px!important;
        line-height:1!important;
        text-transform:uppercase!important;
      }

      .futuresWorkspace tbody td[data-label=""]::before{
        content:none!important;
        display:none!important;
      }
    }

    @media (max-width:560px){
      .futuresWorkspace tbody td[data-label]:not([data-label=""])::before{
        font-size:6.5px!important;
      }
    }
  `;

  document.head.appendChild(style);
(function installScenarioBuilderStyles(){
  if(document.getElementById('futuresScenarioBuilderStyles'))return;

  const style=document.createElement('style');
  style.id='futuresScenarioBuilderStyles';
  style.textContent=`
    .futuresRailTabs{
      grid-template-columns:repeat(5,1fr)!important;
    }
    .futuresScenarioBanner{
      display:flex;
      align-items:center;
      gap:9px;
      flex-wrap:wrap;
      margin:8px 0;
      padding:7px 10px;
      border:1px solid #3f78ad;
      border-radius:8px;
      background:#0c2945;
      font-size:10px;
      font-weight:900;
    }
    .futuresScenarioBanner[hidden]{display:none!important}
    .futuresScenarioBanner>b{color:#fff}
    .futuresScenarioBanner span{color:#cfe4ff}
    .futuresScenarioBanner strong{
      color:var(--green);
      margin-left:auto;
    }
    .futuresScenarioBanner button,
    .scenarioActions button,
    .scenarioLoading button{
      border:1px solid var(--line);
      background:#102949;
      color:#d7e9ff;
      border-radius:6px;
      padding:6px 8px;
      font-size:9px;
      font-weight:950;
      cursor:pointer;
    }
    .scenarioLoading{
      display:grid;
      gap:7px;
      border:1px solid #21466d;
      background:#0b1c35;
      border-radius:8px;
      padding:12px;
    }
    .scenarioLoading small{color:var(--muted)}
    .scenarioError b{color:var(--red)}
    .scenarioSummary{
      display:grid;
      grid-template-columns:auto 1fr auto;
      gap:7px;
      align-items:center;
      margin-bottom:8px;
      padding:8px;
      border:1px solid #31537b;
      background:#0b1c35;
      border-radius:7px;
      font-size:9px;
    }
    .scenarioSummary span{color:var(--muted);font-weight:950}
    .scenarioSummary b{text-align:center}
    .scenarioSummary strong{
      color:var(--green);
      text-align:right;
    }
    .scenarioGameCard{
      border:1px solid #21466d;
      background:#0b1c35;
      border-radius:8px;
      padding:8px;
      margin-top:7px;
    }
    .scenarioGameTitle{
      display:flex;
      justify-content:space-between;
      gap:8px;
      align-items:center;
      margin-bottom:7px;
      font-size:10px;
    }
    .scenarioGameTitle small{
      color:var(--muted);
      white-space:nowrap;
    }
    .scenarioChoiceGrid{
      display:grid;
      grid-template-columns:.7fr 1fr 1fr;
      gap:4px;
    }
    .scenarioChoiceGrid button{
      min-width:0;
      border:1px solid #31537b;
      background:#091a34;
      color:#b8cce4;
      border-radius:6px;
      padding:7px 3px;
      font-size:8px;
      font-weight:950;
      cursor:pointer;
      overflow:hidden;
      text-overflow:ellipsis;
      white-space:nowrap;
    }
    .scenarioChoiceGrid button.active{
      background:#fff;
      color:#07172d;
      border-color:#fff;
    }
    .scenarioAdd{
      display:grid;
      gap:4px;
      margin-top:9px;
    }
    .scenarioAdd label{
      color:var(--muted);
      font-size:8px;
      font-weight:950;
      letter-spacing:.05em;
    }
    .scenarioAdd select{
      width:100%;
      background:#091a34;
      border:1px solid #31537b;
      color:#fff;
      border-radius:6px;
      padding:8px;
      font-size:10px;
    }
    .scenarioActions{
      display:flex;
      justify-content:space-between;
      gap:8px;
      align-items:center;
      margin-top:8px;
      color:var(--muted);
      font-size:9px;
      font-weight:900;
    }
    .scenarioImpactPanel{
      margin-top:10px;
      border:1px solid #31537b;
      background:#081a31;
      border-radius:8px;
      padding:8px;
    }
    .scenarioImpactPanel h3{
      margin:0 0 6px;
      font-size:9px;
      color:#cfe4ff;
    }
    .scenarioImpactHead,
    .scenarioImpactRow{
      display:grid;
      grid-template-columns:1fr 52px 62px 55px;
      gap:5px;
      align-items:center;
      padding:5px 0;
      border-top:1px solid #17345c;
      font-size:9px;
    }
    .scenarioImpactHead{
      color:var(--muted);
      font-size:7px;
      font-weight:950;
      border-top:0;
      padding-bottom:2px;
    }
    .scenarioImpactRow span{color:var(--muted)}
    .scenarioImpactRow b,
    .scenarioImpactRow strong,
    .scenarioImpactRow em{
      text-align:right;
      font-style:normal;
    }
    .scenarioImpactRow strong{color:#fff}
    .scenarioImpactRow em{color:#a9df6a}

    @media(max-width:900px){
      .futuresScenarioBanner strong{margin-left:0}
      .scenarioChoiceGrid{
        grid-template-columns:1fr;
      }
      .scenarioChoiceGrid button{
        min-height:38px;
      }
    }
  `;

  document.head.appendChild(style);
})();

(function installScenarioTableStyles(){
  if(document.getElementById('futuresScenarioTableStyles'))return;

  const style=document.createElement('style');
  style.id='futuresScenarioTableStyles';
  style.textContent=`
    .scenarioValueCell{
      background:#0d2944!important;
    }
    .scenarioValueCell>b{
      color:#fff;
      font-size:12px;
    }
    .scenarioDeltaCell{
      min-width:66px;
    }
    .scenarioDeltaUp{color:var(--green)!important}
    .scenarioDeltaDown{color:var(--red)!important}
    .scenarioDeltaFlat{color:var(--muted)!important}
    .swingTableCell{
      min-width:86px;
    }
    .swingCell{
      display:flex;
      justify-content:center;
      align-items:center;
    }
    .swingValue{
      display:inline-flex;
      align-items:center;
      justify-content:center;
      min-width:58px;
      border-radius:999px;
      padding:4px 7px;
      font-size:9px;
      font-weight:950;
      white-space:nowrap;
    }
    .swing-muted{
      color:#8ea7c3;
      background:#0b1c35;
      border:1px solid #31537b;
    }
    .swing-green{
      color:#7df1bd;
      background:#102d35;
      border:1px solid #26755d;
    }
    .swing-yellow{
      color:#f4cd4b;
      background:#2b2715;
      border:1px solid #6d6024;
    }
    .swing-red{
      color:#fff;
      background:#8b2440;
      border:1px solid #ff6686;
    }
    .swingUnavailable{
      color:var(--muted);
    }

    @media(min-width:901px){
      .futuresWorkspace table{
        width:100%!important;
        min-width:0!important;
        table-layout:fixed!important;
      }

      .futuresWorkspace th,
      .futuresWorkspace td{
        padding-left:7px!important;
        padding-right:7px!important;
      }

      .futuresWorkspace .colTeam{
        width:205px!important;
      }

      .futuresWorkspace .colNext{
        width:170px!important;
      }

      .futuresWorkspace .colRank{
        width:58px!important;
      }

      .futuresWorkspace .colRating{
        width:72px!important;
      }

      .futuresWorkspace .colRecord{
        width:68px!important;
      }

      .futuresWorkspace .colTiny{
        width:45px!important;
      }

      .futuresWorkspace .colProjected{
        width:94px!important;
      }

      .futuresWorkspace .colSos{
        width:70px!important;
      }

      .futuresWorkspace .colModel{
        width:82px!important;
      }

      .futuresWorkspace .colScenario{
        width:82px!important;
      }

      .futuresWorkspace .colDelta{
        width:66px!important;
      }

      .futuresWorkspace .colSwing,
      .futuresWorkspace .swingTableCell{
        width:82px!important;
        min-width:0!important;
      }

      .futuresWorkspace .marketCol{
        width:98px!important;
      }

      .futuresWorkspace .colEdge{
        width:76px!important;
      }

      .futuresWorkspace .colWager{
        width:62px!important;
      }

      .futuresWorkspace th.colTeam,
      .futuresWorkspace th.colNext,
      .futuresWorkspace td:first-child,
      .futuresWorkspace td:nth-child(2){
        overflow:hidden;
      }

      .futuresWorkspace td:first-child>*,
      .futuresWorkspace td:nth-child(2)>*{
        max-width:100%;
        min-width:0;
      }
    }

    @media(max-width:900px){
      .swingTableCell{
        min-width:0;
      }
      .swingCell{
        justify-content:flex-end;
      }
    }
  `;

  document.head.appendChild(style);
})();

(function installFuturesDesktopWidthFinal(){
  if(document.getElementById('futuresDesktopWidthFinal'))return;

  const style=document.createElement('style');
  style.id='futuresDesktopWidthFinal';
  style.textContent=`
    @media (min-width:901px){

      .futuresWorkspace{
        grid-template-columns:minmax(0,1fr) 310px!important;
        gap:10px!important;
      }

      .futuresRail{
        width:310px!important;
        min-width:310px!important;
        max-width:310px!important;
      }

      .compactRailHead{
        gap:5px!important;
        padding:4px 0!important;
        min-height:40px!important;
      }

      .compactRailHead .railTeamLogo{
        width:27px!important;
        height:27px!important;
      }

      .compactTeamName{
        font-size:14px!important;
      }

      .compactTeamRank{
        font-size:12px!important;
      }

      .compactTeamIdentity{
        gap:2px 5px!important;
      }

      .compactTeamIdentity>span:not(.compactTeamRank){
        font-size:8px!important;
      }

      .futuresRailTabs{
        gap:3px!important;
        margin:3px 0!important;
      }

      .futuresRailTabs button{
        padding:6px 3px!important;
        font-size:7.5px!important;
        letter-spacing:.02em!important;
      }

      .scenarioGameCard{
        padding:7px!important;
      }

      .scenarioChoiceGrid{
        gap:3px!important;
      }

      .scenarioChoiceGrid button{
        padding:6px 2px!important;
        font-size:7.5px!important;
      }

      .scenarioAdd{
        margin-top:7px!important;
      }

      .scenarioAdd select{
        padding:6px!important;
        font-size:9px!important;
      }

      .scenarioActions{
        margin-top:6px!important;
      }

      .scenarioImpactPanel{
        margin-top:7px!important;
        padding:6px!important;
      }

      .futuresWorkspace table{
        width:100%!important;
        min-width:0!important;
        table-layout:fixed!important;
      }

      .futuresWorkspace th,
      .futuresWorkspace td{
        padding-left:5px!important;
        padding-right:5px!important;
      }

      .futuresWorkspace th:nth-child(1),
      .futuresWorkspace td:nth-child(1){
        width:180px!important;
      }

      .futuresWorkspace th:nth-child(2),
      .futuresWorkspace td:nth-child(2){
        width:160px!important;
      }

      .futuresWorkspace th:nth-child(3),
      .futuresWorkspace td:nth-child(3){
        width:54px!important;
      }

      .futuresWorkspace th:nth-child(4),
      .futuresWorkspace td:nth-child(4){
        width:68px!important;
      }

      .futTeamButton{
        width:100%!important;
        min-width:0!important;
        max-width:100%!important;
        overflow:hidden!important;
      }

      .futTeamIdentity{
        min-width:0!important;
        overflow:hidden!important;
        flex:1 1 auto!important;
      }

      .futTeamIdentity>b{
        display:block!important;
        max-width:100%!important;
        overflow:hidden!important;
        text-overflow:ellipsis!important;
        white-space:nowrap!important;
      }

      .futTeamIdentity small{
        display:block!important;
        overflow:hidden!important;
        text-overflow:ellipsis!important;
        white-space:nowrap!important;
      }

      .nextGameCell{
        width:100%!important;
        min-width:0!important;
        gap:5px!important;
      }

      .nextGameIdentity{
        display:block!important;
        min-width:0!important;
        overflow:hidden!important;
      }

      .nextGameIdentity>b{
        display:block!important;
        overflow:hidden!important;
        text-overflow:ellipsis!important;
        white-space:nowrap!important;
      }

      .nextGameIdentity small{
        display:block!important;
        white-space:nowrap!important;
      }

      .nextOppRank{
        font-weight:950!important;
      }

      .futuresWorkspace .colProjected{
        width:88px!important;
      }

      .futuresWorkspace .colSos{
        width:66px!important;
      }

      .futuresWorkspace .colModel{
        width:78px!important;
      }

      .futuresWorkspace .colScenario{
        width:78px!important;
      }

      .futuresWorkspace .colDelta{
        width:62px!important;
      }

      .futuresWorkspace .colSwing,
      .futuresWorkspace .swingTableCell{
        width:86px!important;
      }

      .futuresWorkspace .marketCol{
        width:96px!important;
      }

      .futuresWorkspace .colEdge{
        width:72px!important;
      }

      .futuresWorkspace .colWager{
        width:58px!important;
      }
    }
  `;

  document.head.appendChild(style);
})();


})();
