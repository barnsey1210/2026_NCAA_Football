(function () {
  'use strict';

  const DATA_URL = 'data/site/matchups_view.json?v=20260905T043521Z';
  const HISTORY_URL = (
    window.MATCHUP_LINE_HISTORY_URL
    || `data/site/matchup_line_history.json?v=${Date.now()}`
  );
  const DECISION_KEY = 'openers-v2-decisions';
  const BET_KEY = 'ncaaf-game-bets-v1';
  const NOTE_KEY = 'openers-v2-notes';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const finite = value => value !== null && value !== '' && Number.isFinite(Number(value));
  const num = (value, digits=1) => finite(value) ? Number(value).toFixed(digits) : '—';
  const line = value => finite(value) ? `${Number(value)>0?'+':''}${Number(value).toFixed(1)}` : '—';
  const price = value => finite(value) ? `${Number(value)>0?'+':''}${Number(value).toFixed(0)}` : '—';
  const pct = value => finite(value) ? `${(Number(value)*100).toFixed(1)}%` : '—';
  const store = key => { try { return JSON.parse(localStorage.getItem(key) || '{}'); } catch (_) { return {}; } };
  const save = (key, value) => localStorage.setItem(key, JSON.stringify(value));
  const decisions = store(DECISION_KEY), localBets = store(BET_KEY), notes = store(NOTE_KEY);
  let dataPromise, historyPromise, selectedId = null, selectedGame = null;

  const css = `
  #mwBackdrop{display:none;position:fixed;inset:0;background:#020714b8;z-index:9000;padding:2vh 1vw;align-items:flex-start;justify-content:center}
  #mwBackdrop.open{display:flex}.mwShell{width:75vw;max-width:1480px;min-width:760px;max-height:96vh;overflow-x:hidden;overflow-y:auto;background:#07172f;color:#f4f7ff;border:1px solid #315f92;border-radius:15px;box-shadow:0 24px 80px #000b;font:13px/1.4 Inter,system-ui,sans-serif}
  .mwHead{position:sticky;top:0;z-index:4;display:flex;justify-content:space-between;gap:12px;padding:13px 16px;background:#081a35;border-bottom:1px solid #244873}.mwHead h2{margin:0;font-size:23px}.mwSub,.mwMuted{color:#91a6c6}.mwClose{width:38px;height:38px;border:1px solid #37618f;background:#102b50;color:white;border-radius:9px;font-size:22px}.mwBody{padding:12px}.mwSection{min-width:0;border:1px solid #244873;background:#0b1b36;border-radius:11px;padding:10px;margin-bottom:10px}.mwSection h3{margin:0 0 8px;color:#a9bddb;text-transform:uppercase;letter-spacing:.07em;font-size:10px}.mwGrid2{display:grid;grid-template-columns:1fr 1fr;gap:9px}.mwNumbers{display:grid;grid-template-columns:repeat(4,1fr);gap:7px}.mwNumber,.mwStat{background:#081932;border-radius:8px;padding:8px}.mwNumber span,.mwStat span{display:block;color:#91a6c6;font-size:9px;text-transform:uppercase}.mwNumber b{display:block;margin-top:3px;font-size:14px}.mwActions{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.mwActions button{border:1px solid #37618f;background:#102b50;color:white;border-radius:8px;padding:7px 10px;font-weight:850}.mwActions .primary{background:#14764e;border-color:#40d093}.mwActions .active{color:#ffd84f;border-color:#b58a24;background:#4a3812}.mwTeam{display:grid;grid-template-columns:82px 1fr;gap:9px;align-items:center}.mwTeam>img{width:78px;height:70px;object-fit:contain}.mwTeam h4{font-size:16px;margin:0 0 5px}.mwRole{display:inline-block;border:1px solid #3b6698;border-radius:999px;padding:2px 7px;color:#bcd3f0;font-size:9px}.mwStats{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}.mwCoach{grid-column:1/-1}.mwRp{grid-column:1/-1}.mwGood{color:#43df96}.mwWarn{color:#ffc45b}.mwBad{color:#ff7280}.mwRank{font-weight:900;white-space:nowrap}.mwRankGood{color:#43df96}.mwRankWarn{color:#ffc45b}.mwRankBad{color:#ff7280}.mwRankMissing{color:#7185a4}.mwTableWrap{overflow-x:auto}.mwTable{width:100%;border-collapse:collapse;min-width:680px}.mwTable th{background:#10284a;color:#afbfda;text-align:left;text-transform:uppercase;font-size:9px;padding:6px;white-space:nowrap}.mwTable td{border-top:1px solid #17345c;padding:6px;vertical-align:top}.mwTable .right{text-align:right}.mwFive .mwTable,.mwSchedule .mwTable,.mwHistory .mwTable,.mwSpots .mwTable{min-width:0}.mwCurrent{background:#12345c}.mwPriority{display:inline-flex;width:21px;height:21px;align-items:center;justify-content:center;border-radius:50%;background:#175f44;color:#baf8d6;font-weight:900}.mwHistoryHead{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap}.mwOpeners{font-size:10px;color:#c5d5eb;text-align:right}.mwTicket{display:flex;justify-content:space-between;gap:8px;background:#081932;border-radius:7px;padding:7px;margin-top:5px}.mwTicket button{border:1px solid #9b4350;background:#4b1e29;color:#ffc2c9;border-radius:6px}.mwNotes{width:100%;min-height:82px;background:#081932;border:1px solid #315780;color:white;border-radius:8px;padding:8px;resize:vertical}.mwBetModal{display:none;position:fixed;z-index:9100;inset:0;background:#020714c0;align-items:center;justify-content:center}.mwBetModal.open{display:flex}.mwBetCard{width:min(430px,92vw);background:#0d2140;border:1px solid #315f92;border-radius:13px;padding:16px}.mwBetCard label{display:grid;grid-template-columns:95px 1fr;gap:7px;margin:7px 0}.mwBetCard input,.mwBetCard select{background:#081932;border:1px solid #315780;color:white;border-radius:7px;padding:8px}
  .mwSourceState{display:inline-block;margin-left:5px;font-size:9px;color:#ffc45b}.mwSourceState.bet{color:#43df96}
  @media(max-width:1050px){#mwBackdrop{padding:1vh .5vw}.mwShell{width:98vw;min-width:0}.mwGrid2,.mwMarketGrid{grid-template-columns:1fr}.mwNumbers{grid-template-columns:1fr 1fr}.mwStats{grid-template-columns:1fr 1fr}}
  @media(max-width:620px){.mwTeam{grid-template-columns:58px 1fr}.mwTeam>img{width:54px;height:50px}.mwBody{padding:7px}.mwNumbers{grid-template-columns:1fr}.mwHead h2{font-size:18px}.mwSchedule .mwTable,.mwHistory .mwTable{font-size:10px}.mwSchedule th:nth-child(5),.mwSchedule td:nth-child(5),.mwHistory th:nth-child(7),.mwHistory td:nth-child(7){display:none}}

  .mwTeamCompact{display:block}.mwTeamHeader{display:grid;grid-template-columns:56px 1fr;gap:9px;align-items:center;margin-bottom:8px}.mwTeamHeader>img{width:54px;height:48px;object-fit:contain}.mwTeamHeader h4{font-size:17px;margin:0}.mwChipRow{display:flex;flex-wrap:wrap;gap:5px;margin-top:4px}.mwChip{display:inline-flex;align-items:center;gap:4px;border:1px solid #365b85;background:#102543;border-radius:999px;padding:3px 7px;font-size:10px;font-weight:850}.mwMetricGrid{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}.mwMetric{background:#081932;border-radius:8px;padding:7px}.mwMetric span{display:block;color:#91a6c6;font-size:8px;text-transform:uppercase}.mwMetric b{font-size:14px}.mwDual{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:6px}.mwMiniCard{background:#081932;border-radius:8px;padding:7px}.mwMiniTitle{color:#91a6c6;font-size:9px;text-transform:uppercase;letter-spacing:.05em;margin-bottom:5px}.mwRpLine,.mwStaffLine{display:grid;grid-template-columns:26px 1fr auto;gap:6px;align-items:center;padding:3px 0}.mwStaffStatus{border:1px solid #49627e;border-radius:999px;padding:1px 6px;font-size:8px;text-transform:uppercase;font-weight:900}.mwStatusReturning{color:#43df96;border-color:#238d61}.mwStatusNew{color:#ff7280;border-color:#a64b5d}.mwStatusPartial{color:#ffc45b;border-color:#9c7622}.mwStatusUnverified{color:#91a6c6}.mwContextChip{display:inline-flex;border-radius:999px;padding:3px 8px;font-size:10px;font-weight:900;background:#15314f;border:1px solid #38658f}.mwCoachDetail summary{cursor:pointer;color:#cfe0f5;font-weight:900}.mwCoachGrid{display:grid;grid-template-columns:150px repeat(2,minmax(155px,1fr));gap:1px;background:#24405f;margin-top:8px}.mwCoachCell{background:#0b1b36;padding:7px}.mwCoachHead{background:#10284a;color:#afbfda;text-transform:uppercase;font-size:9px;font-weight:900}.mwContextTable td{vertical-align:middle}.mwEvidence{color:#b8c9df}.mwSection[data-section="betting-context"]{border-color:#31745c;box-shadow:inset 0 0 0 1px #123c31}.mwSection[data-section="betting-context"] h3{color:#8af0bb}

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

  `;

  function ensureShell(){
    if(document.getElementById('mwBackdrop')) return;
    document.head.insertAdjacentHTML('beforeend', `<style id="matchup-workspace-css">${css}
  /* Compact visual pass v3 */
  .mwBody{padding:8px}
  .mwSection{padding:8px;margin-bottom:7px;border-radius:9px}
  .mwSection h3{margin-bottom:6px;font-size:9px}
  .mwNumbers{grid-template-columns:repeat(6,minmax(0,1fr));gap:5px}
  .mwNumber,.mwStat{padding:6px}
  .mwNumber span,.mwStat span{font-size:8px}
  .mwNumber b{font-size:13px;line-height:1.2}
  .mwActions{margin-top:6px}
  .mwActions button{padding:6px 9px;font-size:11px}
  .mwTeamHeader{grid-template-columns:46px 1fr;gap:7px;margin-bottom:6px}
  .mwTeamHeader>img{width:44px;height:42px}
  .mwTeamHeader h4{font-size:15px}
  .mwChipRow{gap:4px;margin-top:3px}
  .mwChip{padding:2px 6px;font-size:9px}
  .mwMetricGrid{gap:4px}
  .mwMetric{padding:6px}
  .mwMetric span{font-size:7px}
  .mwMetric b{font-size:13px}
  .mwDual{gap:4px;margin-top:4px}
  .mwMiniCard{padding:6px}
  .mwMiniTitle{font-size:8px;margin-bottom:3px}
  .mwRpLine,.mwStaffLine{padding:2px 0;font-size:10px}
  .mwStaffStatus{font-size:7px;padding:1px 5px}
  .mwTable th{padding:5px;font-size:8px}
  .mwTable td{padding:5px;font-size:11px}
  .mwFive .mwTable td{padding:4px 5px}
  .mwPriority{width:19px;height:19px;font-size:10px}
  .mwContextTable{min-width:760px}
  .mwSection[data-section="betting-context"]{background:#0a2130}
  .mwDenseGrid{display:grid;grid-template-columns:1fr 1fr;gap:7px}
  .mwCompactDetails>summary{cursor:pointer;color:#cfe0f5;font-size:11px;font-weight:900;list-style:none}
  .mwCompactDetails>summary::-webkit-details-marker{display:none}
  .mwCompactDetails>summary:before{content:'▸';display:inline-block;margin-right:6px;color:#65dba4}
  .mwCompactDetails[open]>summary:before{content:'▾'}
  .mwSpotGrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px}
  .mwSpot{background:#081932;border-radius:7px;padding:6px}
  .mwSpot b{display:block;font-size:9px;color:#a9bddb}
  .mwSpot span{font-size:10px}
  .mwEmpty{padding:4px 0;color:#7185a4;font-size:10px}
  @media(max-width:1100px){.mwNumbers{grid-template-columns:repeat(3,1fr)}.mwDenseGrid{grid-template-columns:1fr}.mwSpotGrid{grid-template-columns:repeat(2,1fr)}}


  /* Incremental visual pass: rank scale + top summary only */
  .mwRankGood{color:#3ee58f;background:#0b3b2b;border-color:#1f9b68}
  .mwRankGoodWarn{color:#a8e85f;background:#273a1f;border-color:#6fa543}
  .mwRankWarn{color:#ffd45c;background:#493b13;border-color:#b78d24}
  .mwRankWarnBad{color:#ff9d4d;background:#4b2a17;border-color:#b9652e}
  .mwRankBad{color:#ff6978;background:#491d27;border-color:#b43d50}
  .mwRankMissing{color:#8da0bc;background:#17243a;border-color:#425675}
  .mwRank{
    display:inline-flex;
    align-items:center;
    justify-content:center;
    min-width:34px;
    padding:2px 6px;
    border:1px solid;
    border-radius:999px;
    font-size:10px;
    line-height:1;
    font-weight:950;
  }
  .mwSummaryGrid{
    display:grid;
    grid-template-columns:1fr 1fr 1.2fr 1.45fr;
    gap:6px;
  }
  .mwSummaryCard{
    min-width:0;
    padding:9px;
    border-radius:9px;
    background:#081932;
  }
  .mwSummaryTeam{
    display:grid;
    grid-template-columns:38px minmax(0,1fr);
    gap:8px;
    align-items:center;
  }
  .mwSummaryTeam img{
    width:36px;
    height:36px;
    object-fit:contain;
  }
  .mwSummaryTitle{
    color:#fff;
    font-size:13px;
    font-weight:950;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
  }
  .mwSummaryLabel{
    color:#dce8fa;
    font-size:10px;
    font-weight:950;
    letter-spacing:.04em;
    text-transform:uppercase;
  }
  .mwSummaryRow{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:8px;
    margin-top:5px;
    line-height:1.15;
  }
  .mwSummaryRow span{
    color:#91a6c6;
    font-size:9px;
    text-transform:uppercase;
  }
  .mwSummaryRow b{
    color:#fff;
    font-size:13px;
    white-space:nowrap;
  }
  .mwModelCard .mwSummaryRow b{font-size:12px}
  @media(max-width:1050px){
    .mwSummaryGrid{grid-template-columns:1fr 1fr}
  }


  /* Source-page link + expansion repair */
  a[data-matchup-id],
  a[href*="game_id="]{
    color:inherit !important;
    text-decoration:none !important;
  }
  a[data-matchup-id]:hover,
  a[href*="game_id="]:hover{
    color:#ffffff !important;
    text-decoration:underline !important;
  }


  .teamLink,
  a.teamLink,
  .matchup a{
    color:inherit !important;
    text-decoration:none !important;
  }
  .teamLink:hover,
  a.teamLink:hover,
  .matchup a:hover{
    color:#ffffff !important;
    text-decoration:underline !important;
  }


  /* Incremental team-card refinement v3.7 */
  .mwRankNumber{
    font-weight:950;
    font-size:14px;
    line-height:1;
    white-space:nowrap;
  }
  .mwRankNumber.mwRankGood{color:#3ee58f;background:none;border:0}
  .mwRankNumber.mwRankGoodWarn{color:#a8e85f;background:none;border:0}
  .mwRankNumber.mwRankWarn{color:#ffd45c;background:none;border:0}
  .mwRankNumber.mwRankWarnBad{color:#ff9d4d;background:none;border:0}
  .mwRankNumber.mwRankBad{color:#ff6978;background:none;border:0}
  .mwRankNumber.mwRankMissing{color:#8da0bc;background:none;border:0}
  .mwTeamRankGrid{
    display:grid;
    grid-template-columns:repeat(3,minmax(0,1fr));
    gap:5px;
  }
  .mwTeamRankItem{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:8px;
    min-width:0;
    background:#081932;
    border-radius:8px;
    padding:7px 9px;
  }
  .mwTeamRankLabel{
    color:#91a6c6;
    font-size:8px;
    font-weight:900;
    letter-spacing:.05em;
    text-transform:uppercase;
  }
  .mwTeamRankValue{
    display:flex;
    align-items:baseline;
    gap:6px;
    min-width:0;
  }
  .mwRatingValue{
    color:#eef5ff;
    font-size:13px;
    font-weight:950;
    white-space:nowrap;
  }
  .mwCoachRecords{
    display:grid;
    grid-template-columns:repeat(3,minmax(0,1fr));
    gap:5px;
    margin-top:5px;
  }
  .mwCoachRecord{
    min-width:0;
    padding:6px 7px;
    border-radius:7px;
    background:#0d203b;
  }
  .mwCoachRecordLabel{
    color:#91a6c6;
    font-size:8px;
    font-weight:950;
    letter-spacing:.05em;
    text-transform:uppercase;
    margin-bottom:3px;
  }
  .mwCoachRecordLine{
    color:#f0f5fc;
    font-size:10px;
    font-weight:850;
    line-height:1.25;
    white-space:nowrap;
  }
  @media(max-width:900px){
    .mwCoachRecords{grid-template-columns:1fr}
  }


  /* Incremental spacing + coaching refinement v3.8 */
  .mwTeamHeader h4{
    font-size:19px;
    line-height:1.1;
  }
  .mwRole{
    padding:3px 8px;
    font-size:10px;
  }
  .mwChipRow{
    gap:6px;
    margin-top:6px;
  }
  .mwChip{
    padding:4px 9px;
    font-size:11px;
    line-height:1;
  }
  .mwRpLine{
    grid-template-columns:30px 52px auto;
    justify-content:start;
    gap:5px;
  }
  .mwRpLine .mwRank{
    min-width:38px;
  }
  .mwSummaryLabel{
    text-align:center;
    font-size:11px;
  }
  .mwModelCard .mwSummaryRow,
  .mwMarketCard .mwSummaryRow{
    display:grid;
    grid-template-columns:max-content max-content;
    justify-content:center;
    column-gap:12px;
  }
  .mwModelCard .mwSummaryRow span,
  .mwMarketCard .mwSummaryRow span{
    min-width:48px;
  }
  .mwApplicableRole{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:8px;
    padding:6px 8px;
    margin:5px 0;
    border:1px solid #365b85;
    border-radius:7px;
    background:#0c203c;
  }
  .mwApplicableRoleLabel{
    color:#91a6c6;
    font-size:8px;
    font-weight:950;
    letter-spacing:.05em;
    text-transform:uppercase;
  }
  .mwApplicableRoleValue{
    color:#f5f8fd;
    font-size:11px;
    font-weight:900;
    text-align:right;
  }


  /* Incremental market, coach-color, and lower-card refinement v4.0 */
  .mwCoachGood{color:#3ee58f !important}
  .mwCoachNeutral{color:#ffd45c !important}
  .mwCoachBad{color:#ff6978 !important}
  .mwCoachMissing{color:#91a6c6 !important}
  .mwCoachRecordLine b,
  .mwApplicableRoleValue b{font-weight:950}
  .mwBookLogo{
    display:inline-flex;
    align-items:center;
    justify-content:center;
    width:28px;
    height:21px;
    padding:2px;
    border-radius:5px;
    background:#f7f9fc;
    flex:0 0 auto;
  }
  .mwBookLogo img{
    max-width:24px;
    max-height:17px;
    object-fit:contain;
  }
  .mwMarketValue{
    display:flex;
    align-items:center;
    justify-content:flex-end;
    gap:7px;
    min-width:0;
  }
  .mwSummaryGrid{
    grid-template-columns:1fr 1fr 1.15fr 1.35fr;
  }
  .mwSummaryCard{
    padding:8px 10px;
  }
  .mwSummaryLabel{
    margin-bottom:3px;
  }
  .mwModelCard .mwSummaryRow,
  .mwMarketCard .mwSummaryRow{
    grid-template-columns:52px minmax(0,max-content);
    column-gap:9px;
  }
  .mwContextTable th,
  .mwContextTable td{
    padding:5px 7px;
    line-height:1.2;
  }
  .mwContextTable .mwPriority{
    width:24px;
    height:24px;
  }
  .mwFive{
    padding:7px 9px;
  }
  .mwFive h3{
    margin-bottom:5px;
  }
  .mwFive .mwTable th,
  .mwFive .mwTable td{
    padding:4px 6px;
    line-height:1.15;
  }


  /* Lower-half density cleanup v4.1 */
  .mwBookLogo{
    width:23px;
    height:18px;
    padding:1px;
    border-radius:4px;
    background:#eef3f8;
  }
  .mwBookLogo img{
    max-width:21px;
    max-height:15px;
  }
  .mwContextEmpty{
    padding:8px 10px !important;
    text-align:left;
    font-size:11px;
  }
  .mwContextEmptySection{
    padding-bottom:7px;
  }
  .mwContextEmptySection .mwTableWrap{
    overflow:visible;
  }
  .mwContextEmptySection .mwTable thead{
    display:none;
  }
  .mwContextEmptySection .mwTable{
    min-width:0;
  }
  .mwFive{
    padding:6px 8px;
  }
  .mwFive h3{
    margin-bottom:4px;
  }
  .mwFive .mwTable th,
  .mwFive .mwTable td{
    padding:3px 5px;
    line-height:1.05;
    font-size:10px;
  }
  .mwFive .mwRank{
    padding:1px 5px;
    min-width:31px;
    font-size:9px;
  }
  .mwCoachDetail,
  .mwHistory{
    padding:6px 9px;
  }
  .mwCompactDetails summary{
    padding:1px 0;
    line-height:1.2;
  }
  .mwSchedule{
    padding:7px 8px;
  }
  .mwSchedule .mwTable th,
  .mwSchedule .mwTable td{
    padding:4px 5px;
    line-height:1.1;
    font-size:10px;
  }
  .mwSchedule .mwRank{
    padding:1px 5px;
    min-width:31px;
    font-size:9px;
  }


  /* Five Factors readability + global modal font pass v4.2 */
  .mwShell{
    font-size:14px;
    line-height:1.45;
  }
  .mwHead h2{
    font-size:25px;
  }
  .mwSection h3{
    font-size:12px;
    font-weight:950;
    letter-spacing:.055em;
  }
  .mwFive{
    padding:8px 10px;
  }
  .mwFive h3{
    margin-bottom:7px;
    font-size:13px;
    font-weight:950;
    color:#d9e6f8;
  }
  .mwFive .mwTable{
    table-layout:fixed;
  }
  .mwFive .mwTable th{
    padding:6px 7px;
    font-size:10px;
    text-align:center;
    vertical-align:middle;
  }
  .mwFive .mwTable td{
    padding:7px 7px;
    font-size:12px;
    text-align:center;
    vertical-align:middle;
    line-height:1.15;
  }
  .mwFive .mwTable tbody tr{
    height:40px;
  }
  .mwFive .mwFactorName{
    font-size:13px;
    font-weight:950;
  }
  .mwFive .mwColumnTeam{
    color:#dce8fa;
    font-size:10px;
    font-weight:950;
    line-height:1.15;
    white-space:normal;
  }
  .mwFive .mwEdgeLogo{
    width:30px;
    height:30px;
    object-fit:contain;
    vertical-align:middle;
  }
  .mwFive .mwEdgeDash{
    color:#91a6c6;
    font-size:14px;
    font-weight:900;
  }
  .mwFive .mwRank{
    font-size:10px;
    min-width:34px;
    padding:2px 6px;
  }
  .mwTable th{
    font-size:10px;
  }
  .mwTable td{
    font-size:12px;
  }
  .mwChip{
    font-size:12px;
  }
  .mwSummaryRow span,
  .mwTeamRankLabel,
  .mwMiniTitle,
  .mwCoachRecordLabel,
  .mwApplicableRoleLabel{
    font-size:9px;
  }
  .mwSummaryRow b,
  .mwCoachRecordLine,
  .mwApplicableRoleValue{
    font-size:12px;
  }


  .mwSchedule .mwByeRow td{
    background:#0b1c34;
    color:#a9bad2;
    font-style:italic;
  }
  .mwSchedule .mwByeRow td:nth-child(2),
  .mwSchedule .mwByeRow td:nth-child(6){
    color:#ffd45c;
    font-style:normal;
    font-weight:950;
  }


  /* Matchup final structure pass v4.4 */
  .mwContextEmptySection{
    border-color:#2c5f4c;
    padding:7px 10px;
  }
  .mwContextEmptySection h3{
    display:none;
  }
  .mwContextEmpty{
    padding:2px 0 !important;
    font-size:12px;
  }
  .mwMarketEdgeRow{
    display:flex;
    justify-content:center;
    gap:6px;
    margin-top:7px;
    flex-wrap:wrap;
  }
  .mwMarketEdgeChip{
    display:inline-flex;
    align-items:center;
    gap:4px;
    padding:3px 7px;
    border:1px solid #355a82;
    border-radius:999px;
    background:#0b203c;
    color:#dce8fa;
    font-size:10px;
    font-weight:900;
  }
  .mwMarketEdgeChip.mwEdgeGood{
    border-color:#1d9b67;
    color:#55e7a0;
  }
  .mwHistory{
    padding:9px 10px;
  }
  .mwHistory h3{
    margin-bottom:7px;
    font-size:14px;
    color:#dce8fa;
  }
  .mwHistorySummary{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:7px;
    margin-bottom:8px;
  }
  .mwHistorySummaryCard{
    padding:7px 9px;
    border-radius:7px;
    background:#0b203c;
    border:1px solid #31577f;
    font-size:11px;
  }
  .mwHistorySummaryCard b{
    color:#fff;
  }
  .mwHistory .mwTable th,
  .mwHistory .mwTable td{
    padding:5px 6px;
    text-align:center;
    font-size:11px;
  }
  .mwMovementUp{color:#ffb14a;font-weight:950}
  .mwMovementDown{color:#55e7a0;font-weight:950}
  .mwMovementFlat{color:#91a6c6;font-weight:900}
  .mwSpots{
    width:100%;
  }
  .mwSpotTeam{
    display:flex;
    align-items:center;
    gap:8px;
    margin-bottom:6px;
    font-size:13px;
    font-weight:950;
  }
  .mwSpotTeam img{
    width:28px;
    height:28px;
    object-fit:contain;
  }
  .mwSpotGrid{
    grid-template-columns:repeat(4,minmax(0,1fr));
    gap:5px;
  }
  .mwSpot{
    padding:7px 6px;
    border-radius:7px;
    background:#0b203c;
    text-align:center;
  }
  .mwSpot b{
    display:block;
    font-size:9px;
    margin-bottom:3px;
  }
  .mwSpotValue{
    display:inline-flex;
    align-items:center;
    justify-content:center;
    min-width:58px;
    padding:3px 7px;
    border-radius:999px;
    font-size:10px;
    font-weight:950;
  }
  .mwSpotYes{background:#113f30;color:#55e7a0;border:1px solid #1d9b67}
  .mwSpotNo{background:#18304e;color:#b9c7da;border:1px solid #456481}
  .mwSpotWatch{background:#493b13;color:#ffd45c;border:1px solid #b78d24}
  .mwScheduleOpponent{
    display:flex;
    align-items:center;
    gap:6px;
    white-space:nowrap;
  }
  .mwScheduleOpponent img{
    width:20px;
    height:20px;
    object-fit:contain;
  }
  .mwByeRow td{
    text-align:center !important;
    background:#0b1c34 !important;
  }
  .mwByeLabel{
    color:#ffd45c;
    font-weight:950;
    letter-spacing:.08em;
  }
  .mwEmptyTools{
    display:flex;
    gap:8px;
    align-items:center;
  }
  .mwAddNoteBtn{
    padding:6px 10px;
  }


  /* Schedule context placement refinement v4.5 */
  .mwSchedule{
    padding:7px 9px;
  }
  .mwSchedule h3{
    font-size:12px;
    margin-bottom:5px;
  }


  /* Final polish pass v4.6 */
  .mwContextEmptySection{
    padding:4px 9px;
    min-height:0;
  }
  .mwContextEmptySection .mwContextEmpty{
    padding:0 !important;
    line-height:1.2;
  }
  .mwSpots{
    grid-column:1 / -1;
  }
  .mwSpots .mwDenseGrid{
    grid-template-columns:1fr 1fr;
  }
  .mwHistoryLegend{
    display:flex;
    justify-content:flex-end;
    gap:10px;
    margin:-2px 0 6px;
    color:#91a6c6;
    font-size:9px;
    font-weight:850;
  }
  .mwHistoryLegend span{
    display:inline-flex;
    align-items:center;
    gap:4px;
  }
  .mwLegendDot{
    width:8px;
    height:8px;
    border-radius:50%;
    display:inline-block;
  }
  .mwLegendLower{background:#55e7a0}
  .mwLegendHigher{background:#ffb14a}
  .mwLegendFlat{background:#91a6c6}
  .mwMarketEdgeChip{
    gap:6px;
    font-size:11px;
    padding:4px 8px;
  }
  .mwMarketEdgeChip img{
    width:17px;
    height:17px;
    object-fit:contain;
  }
  .mwMarketEdgeChip.mwEdgeGood{
    background:#113f30;
  }
  .mwMarketEdgeChip.mwEdgeNeutral{
    color:#c2cfdf;
    border-color:#456481;
  }
  @media(max-width:1100px){
    .mwSummaryGrid{grid-template-columns:1fr 1fr}
    .mwGrid2{grid-template-columns:1fr}
    .mwSpots .mwDenseGrid{grid-template-columns:1fr}
    .mwHistorySummary{grid-template-columns:1fr}
  }
  @media(max-width:700px){
    .mwSummaryGrid{grid-template-columns:1fr}
    .mwCoachRecords{grid-template-columns:1fr}
    .mwSpotGrid{grid-template-columns:repeat(2,minmax(0,1fr))}
    .mwHistoryLegend{justify-content:flex-start;flex-wrap:wrap}
  }

</style>`);
    document.body.insertAdjacentHTML('beforeend', `<div id="mwBackdrop"><article class="mwShell" role="dialog" aria-modal="true"><div id="mwContent"></div></article></div><div class="mwBetModal" id="mwBetModal"><div class="mwBetCard"><h2>Add bet</h2><div id="mwBetGame" class="mwMuted"></div><label><span>Market</span><select id="mwBetMarket"><option>Spread</option><option>Total</option><option>Moneyline</option></select></label><label><span>Selection</span><input id="mwBetSelection"></label><label><span>Price</span><input id="mwBetPrice"></label><label><span>Book</span><input id="mwBetBook"></label><label><span>Stake</span><input id="mwBetStake"></label><div class="mwActions"><button onclick="closeMatchupBet()">Cancel</button><button class="primary" onclick="saveMatchupBet()">Save bet</button></div></div></div>`);
    document.getElementById('mwBackdrop').addEventListener('click', e=>{if(e.target.id==='mwBackdrop') closeMatchupWorkspace()});
  }
  function loadData(){ return dataPromise ||= fetch(DATA_URL).then(r=>{if(!r.ok)throw Error('Matchup data unavailable');return r.json()}); }
  function loadHistory(){ return historyPromise ||= fetch(HISTORY_URL, {cache:'no-store'}).then(r=>r.ok?r.json():{}).catch(()=>({})); }
  function logo(team){ return `<img src="logos/${esc(team.logo_slug)}.png" alt="" onerror="this.style.display='none'">`; }
  function role(team, game){ const s=Number(game.model.home_spread); if(!Number.isFinite(s)||Math.abs(s)<.05)return "Pick'em"; return team.team===game.game.home_team?(s<0?'Favorite':'Underdog'):(s>0?'Favorite':'Underdog'); }
  function projectedPoints(game){ const total=Number(game.model.total), spread=Number(game.model.home_spread); if(!Number.isFinite(total)||!Number.isFinite(spread))return{away:null,home:null}; return {away:(total+spread)/2,home:(total-spread)/2}; }
  function coachRole(team, game){ const coach=(game.matchup.coaches||[]).find(x=>x.team===team.team), r=role(team,game), split=(coach?.role_splits||[]).find(x=>x.role===r); return {coach,split,r}; }
  function coachPeriod(coach, period){ return (coach?.periods||[]).find(x=>x?.period===period)||{}; }
  function rankClass(value){ if(!finite(value))return 'mwRankMissing'; const n=Number(value); return n<=28?'mwRankGood':n<=55?'mwRankGoodWarn':n<=83?'mwRankWarn':n<=110?'mwRankWarnBad':'mwRankBad'; }
  function rank(value){ return `<span class="mwRank ${rankClass(value)}">${finite(value)?'#'+Number(value).toFixed(0):'—'}</span>`; }
  function rankNumber(value){ return `<span class="mwRankNumber ${rankClass(value)}">${finite(value)?'#'+Number(value).toFixed(0):'—'}</span>`; }
  function parsedAtsPct(record){
    const m=String(record||'').match(/(\d+)\s*-\s*(\d+)(?:\s*-\s*(\d+))?/);
    if(!m)return null;
    const wins=Number(m[1]),losses=Number(m[2]);
    return wins+losses>0?wins/(wins+losses):null;
  }
  function coachAtsPct(row){
    if(finite(row?.ats_pct))return Number(row.ats_pct)>1?Number(row.ats_pct)/100:Number(row.ats_pct);
    return parsedAtsPct(row?.ats_record);
  }
  function coachAtsClass(value){
    if(!finite(value))return 'mwCoachMissing';
    const n=Number(value)>1?Number(value)/100:Number(value);
    return n>=.55?'mwCoachGood':n<.45?'mwCoachBad':'mwCoachNeutral';
  }
  function coachPctText(value){
    if(!finite(value))return '—';
    const n=Number(value)>1?Number(value)/100:Number(value);
    return `${(n*100).toFixed(1)}%`;
  }
  function movementText(current, previous){
    if(!finite(current)||!finite(previous))return '<span class="mwMovementFlat">—</span>';
    const delta=Number(current)-Number(previous);
    if(Math.abs(delta)<0.01)return '<span class="mwMovementFlat">0.0</span>';
    const cls=delta>0?'mwMovementUp':'mwMovementDown';
    return `<span class="${cls}">${delta>0?'+':''}${delta.toFixed(1)}</span>`;
  }
  function edgeTeamLogo(name, game){
    const team=name===game.game.away_team?game.teams.away:name===game.game.home_team?game.teams.home:null;
    return team?.logo_slug?`<img src="logos/${esc(team.logo_slug)}.png" alt="" onerror="this.style.display='none'">`:'';
  }
  function scheduleOpponentLogo(name, game){
    const team=name===game.teams.away.team?game.teams.away:name===game.teams.home.team?game.teams.home:null;
    if(team?.logo_slug)return `<img src="logos/${esc(team.logo_slug)}.png" alt="" onerror="this.style.display='none'">`;
    const slug=String(name||'').toLowerCase().replace(/&/g,'and').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
    return slug?`<img src="logos/${esc(slug)}.png" alt="" onerror="this.style.display='none'">`:'';
  }
  function bookLogo(book){
    const raw=String(book||'').trim(),b=raw.toLowerCase();
    let src='',label=raw||'Sportsbook';
    if(b.includes('fanduel')){src='logos/books/fanduel.png';label='FanDuel'}
    else if(b.includes('draftkings')){src='logos/books/draftkings.png';label='DraftKings'}
    else if(b.includes('betmgm')||b==='mgm'){src='logos/books/betmgm.png';label='BetMGM'}
    else if(b.includes('caesars')){src='logos/books/caesars.png';label='Caesars'}
    else if(b.includes('bet365')){src='logos/books/bet365.png';label='bet365'}
    else if(b.includes('betrivers')){src='logos/books/betrivers.png';label='BetRivers'}
    return src?`<span class="mwBookLogo" title="${esc(label)}"><img src="${src}" alt="${esc(label)}"></span>`:'';
  }
  function statusClass(value){const s=String(value||'unverified').toLowerCase();return `mwStaffStatus mwStatus${s.charAt(0).toUpperCase()+s.slice(1)}`;}
  function staffLine(label,name,status,extra=''){return `<div class="mwStaffLine"><b>${label}</b><span>${esc(name||'—')}${extra?` <span class="mwMuted">${esc(extra)}</span>`:''}</span><i class="${statusClass(status)}">${esc(status||'unverified')}</i></div>`;}
  function rpLine(label,pctValue,rankValue){return `<div class="mwRpLine"><b>${label}</b><span>${finite(pctValue)?num(pctValue,0)+'%':'—'}</span>${rank(rankValue)}</div>`;}
  function teamCard(team, game){
    const cr=coachRole(team,game),rec=team.record||{},br=team.betting_record||{},rp=team.returning_production||{},staff=team.staff_continuity||{};
    const hcTenure=finite(staff.head_coach_tenure_year)?`Year ${Number(staff.head_coach_tenure_year).toFixed(0)}`:'';
    const coach=cr.coach||{};
    const recordCard=(label,period)=>{
      const row=coachPeriod(coach,period),atsPct=coachAtsPct(row),atsClass=coachAtsClass(atsPct);
      return `<div class="mwCoachRecord"><div class="mwCoachRecordLabel">${label}</div><div class="mwCoachRecordLine ${atsClass}">ATS <b>${esc(row.ats_record||'—')}</b> · <b>${coachPctText(atsPct)}</b></div><div class="mwCoachRecordLine">O/U ${esc(row.ou_record||'—')}</div></div>`;
    };
    return `<section class="mwSection mwTeamCompact">
      <div class="mwTeamHeader">${logo(team)}<div><h4>${esc(team.team)} <span class="mwRole">${esc(cr.r)}</span></h4><div class="mwChipRow"><span class="mwChip">${esc(team.conference||'—')}</span><span class="mwChip">${rec.wins??0}-${rec.losses??0}</span><span class="mwChip">ATS ${esc(br.ats||'—')}</span><span class="mwChip">O/U ${esc(br.ou||'—')}</span></div></div></div>
      <div class="mwTeamRankGrid">
        <div class="mwTeamRankItem"><span class="mwTeamRankLabel">Overall</span><span class="mwTeamRankValue">${rankNumber(team.overall_rank)} <span class="mwRatingValue">${num(team.rating,1)}</span></span></div>
        <div class="mwTeamRankItem"><span class="mwTeamRankLabel">Offense</span><span class="mwTeamRankValue">${rankNumber(team.offense_rank)}</span></div>
        <div class="mwTeamRankItem"><span class="mwTeamRankLabel">Defense</span><span class="mwTeamRankValue">${rankNumber(team.defense_rank)}</span></div>
      </div>
      <div class="mwDual"><div class="mwMiniCard"><div class="mwMiniTitle">Returning production</div>${rpLine('OVR',rp.overall_pct,rp.overall_rank)}${rpLine('OFF',rp.offense_pct,rp.offense_rank)}${rpLine('DEF',rp.defense_pct,rp.defense_rank)}</div><div class="mwMiniCard"><div class="mwMiniTitle">2026 staff continuity</div>${staffLine('HC',staff.head_coach,staff.head_coach_status,hcTenure)}${staffLine('OC',staff.offensive_coordinator,staff.oc_status)}${staffLine('DC',staff.defensive_coordinator,staff.dc_status)}</div></div>
      <div class="mwMiniCard" style="margin-top:6px"><div class="mwMiniTitle">Coach betting records — ${esc(coach.coach||'Coach unavailable')}</div><div class="mwApplicableRole"><span class="mwApplicableRoleLabel">Applicable ${esc(cr.r)} role</span><span class="mwApplicableRoleValue">${cr.split?.ats_record?`<span class="${coachAtsClass(coachAtsPct(cr.split))}">ATS <b>${esc(cr.split.ats_record)}</b> · <b>${coachPctText(coachAtsPct(cr.split))}</b></span> · O/U ${esc(cr.split.ou_record||'—')}`:'No qualifying role sample'}</span></div><div class="mwCoachRecords">${recordCard('Overall','full_game')}${recordCard('1H','first_half')}${recordCard('2H','second_half')}</div></div>
    </section>`;
  }

  function marketSummary(game){
    const s=game.market.spread||{},t=game.market.total||{},pp=projectedPoints(game);
    const awayWin=finite(game.model.home_win_probability)?1-Number(game.model.home_win_probability):null;
    const teamSummary=(team,score,win)=>`<div class="mwSummaryCard"><div class="mwSummaryTeam">${logo(team)}<div><div class="mwSummaryTitle">${esc(team.team)}</div><div class="mwSummaryRow"><span>Projected score</span><b>${num(score)}</b></div><div class="mwSummaryRow"><span>Win probability</span><b>${pct(win)}</b></div></div></div></div>`;
    const modelSpread=finite(game.model.home_spread)?`${esc(game.game.home_team)} ${line(game.model.home_spread)}`:'—';
    const marketSpread=finite(s.home_line)?`${esc(game.game.home_team)} ${line(s.home_line)} ${price(s.price)}`:'—';
    const marketTotal=finite(t.line)?`${num(t.line)} · O ${price(t.over_price)} / U ${price(t.under_price)}`:'—';
    const spreadEdge=finite(game.model.home_spread)&&finite(s.home_line)?Number(game.model.home_spread)-Number(s.home_line):null;
    const totalEdge=finite(game.model.total)&&finite(t.line)?Number(game.model.total)-Number(t.line):null;
    const spreadSide=finite(spreadEdge)?(spreadEdge>0?game.game.away_team:game.game.home_team):'';
    const totalSide=finite(totalEdge)?(totalEdge>0?'Over':'Under'):'';
    const edgeChip=(label,value)=>finite(value)?`<span class="mwMarketEdgeChip ${Math.abs(value)>=2?'mwEdgeGood':'mwEdgeNeutral'}">${edgeTeamLogo(label,game)}<span>${esc(label)} ${Math.abs(Number(value)).toFixed(1)}</span></span>`:'';
    return `<div class="mwSummaryGrid">
      ${teamSummary(game.teams.away,pp.away,awayWin)}
      ${teamSummary(game.teams.home,pp.home,game.model.home_win_probability)}
      <div class="mwSummaryCard mwModelCard"><div class="mwSummaryLabel">Model</div><div class="mwSummaryRow"><span>Spread</span><b>${modelSpread}</b></div><div class="mwSummaryRow"><span>Total</span><b>${num(game.model.total)}</b></div><div class="mwMarketEdgeRow">${edgeChip(spreadSide,spreadEdge)}${edgeChip(totalSide,totalEdge)}</div></div>
      <div class="mwSummaryCard mwMarketCard"><div class="mwSummaryLabel">Current market</div><div class="mwSummaryRow"><span>Spread</span><span class="mwMarketValue"><b>${marketSpread}</b>${bookLogo(s.book)}</span></div><div class="mwSummaryRow"><span>Total</span><span class="mwMarketValue"><b>${marketTotal}</b>${bookLogo(t.book)}</span></div></div>
    </div>`;
  }
  const fiveLabels={success:'Success',explosiveness:'Explosiveness',finishing_drives:'Finishing drives',field_position:'Field position',havoc:'Havoc'};
  function fiveFactorTable(title, rows, offenseTeam, defenseTeam, game){
    const by=new Map((rows||[]).map(x=>[x.metric,x]));
    const edgeLogo=name=>{
      if(!name)return '<span class="mwEdgeDash">—</span>';
      const team=name===game.teams.away.team?game.teams.away:name===game.teams.home.team?game.teams.home:null;
      return team?`<img class="mwEdgeLogo" src="logos/${esc(team.logo_slug)}.png" alt="${esc(name)}" title="${esc(name)}" onerror="this.style.display='none'">`:`<span class="mwEdgeDash" title="${esc(name)}">—</span>`;
    };
    return `<section class="mwSection mwFive"><h3>${esc(title)}</h3><div class="mwTableWrap"><table class="mwTable"><thead><tr><th class="mwColumnTeam">${esc(offenseTeam)}<br>Offense</th><th>Factor</th><th class="mwColumnTeam">${esc(defenseTeam)}<br>Defense</th><th>Edge</th></tr></thead><tbody>${Object.entries(fiveLabels).map(([key,label])=>{const x=by.get(key)||{};return `<tr><td>${rank(x.offense_rank)}</td><td class="mwFactorName">${label}</td><td>${rank(x.defense_rank)}</td><td>${edgeLogo(x.edge_team)}</td></tr>`}).join('')}</tbody></table></div></section>`;
  }
  function scheduleRows(team, game){
    const rows=[...(team.recent_form||[]),...(team.upcoming_schedule||[])]
      .filter(x=>String(x.date||'').startsWith('2026')||String(x.season||'')==='2026');
    const unique=[...new Map(rows.map(x=>[x.game_id||`${x.date}|${x.opponent}`,x])).values()]
      .sort((a,b)=>String(a.date).localeCompare(String(b.date)));

    const expanded=[];
    for(let i=0;i<unique.length;i++){
      const current=unique[i];
      expanded.push(current);
      const next=unique[i+1];
      if(!next||!current.date||!next.date)continue;
      const currentDate=new Date(`${current.date}T12:00:00`);
      const nextDate=new Date(`${next.date}T12:00:00`);
      const gapDays=Math.round((nextDate-currentDate)/86400000);
      if(gapDays<12)continue;

      for(let offset=7;offset<=gapDays-7;offset+=7){
        const byeDate=new Date(currentDate.getTime()+offset*86400000);
        const iso=byeDate.toISOString().slice(0,10);
        expanded.push({
          game_id:`bye-${team.team}-${iso}`,
          date:iso,
          opponent:'BYE',
          status:'Bye week',
          is_bye:true,
          opponent_ranks:{overall:null,offense:null,defense:null},
          spread:null,
          total_line:null
        });
      }
    }

    expanded.sort((a,b)=>String(a.date).localeCompare(String(b.date)));
    const index=expanded.findIndex(x=>String(x.game_id)===String(game.game.game_id));
    const selected=index>=0?index:expanded.findIndex(x=>x.date===game.game.date&&!x.is_bye);
    return expanded.filter((_,i)=>i>=Math.max(0,selected-3)&&i<=selected+5);
  }
  function scheduleCard(team, game){ const rows=scheduleRows(team,game); return `<section class="mwSection mwSchedule"><h3>${esc(team.team)} — 2026 schedule context</h3><div class="mwTableWrap"><table class="mwTable"><thead><tr><th>Date</th><th>Opponent</th><th>Ovr</th><th>Off</th><th>Def</th><th>Status</th><th>Spread</th><th>Total</th></tr></thead><tbody>${rows.map(x=>{const current=!x.is_bye&&(String(x.game_id)===String(game.game.game_id)||x.date===game.game.date);if(x.is_bye)return `<tr class="mwByeRow"><td>${esc(x.date)}</td><td colspan="7"><span class="mwByeLabel">BYE WEEK</span></td></tr>`;return `<tr class="${current?'mwCurrent':''}"><td>${esc(x.date||'—')}</td><td><span class="mwScheduleOpponent">${scheduleOpponentLogo(x.opponent,game)}<span>${esc(x.opponent||'Selected game')}</span></span></td><td>${rank(x.opponent_ranks?.overall)}</td><td>${rank(x.opponent_ranks?.offense)}</td><td>${rank(x.opponent_ranks?.defense)}</td><td>${current?'Selected':esc(x.score||x.status||'Upcoming')}</td><td>${line(x.spread??x.model_spread)}</td><td>${num(x.total_line??x.model_total)}</td></tr>`}).join('')||'<tr><td colspan="8" class="mwMuted">No 2026 schedule context available.</td></tr>'}</tbody></table></div></section>`; }
  function opponentTeam(team, game){ return team.team===game.game.away_team?game.teams.home:game.teams.away; }
  function tendencyKind(row){const receive=Number(row?.receive_pct),defer=Number(row?.defer_pct);if(Number(row?.toss_wins)<6)return null;if(receive>=65)return 'receive';if(defer>=65)return 'defer';return null;}
  function continuityScore(staff){if(!staff||Number(staff.unverified_count)>0)return null;return Number(staff.returning_count)+(Number(staff.partial_count)*.5);}
  function legacyContextRows(game){
    const out=[], s=game.market.spread||{},t=game.market.total||{};
    const add=x=>{if(x.team&&x.team!=='—'&&x.evidence)out.push(x)};
    const rpCandidates=(game.angles||[]).filter(x=>{
      const group=String(x.signal_group||'').toLowerCase();
      const type=String(x.signal_type||'').toLowerCase();
      return group==='returning production'||type==='rp_support';
    });
    const rpSignal=
      rpCandidates.find(x=>String(x.signal_group||'').toLowerCase()==='returning production')||
      rpCandidates[0]||
      null;
    const hasHistoricalRpSignal=!!rpSignal;
    if(rpSignal&&Number(game.game.week)<=4){
      const rawTeam=rpSignal.team||rpSignal.direction||'';
      const action=String(rpSignal.strength||'').toLowerCase()==='fade'?'Fade':'Support';
      const side=rawTeam?`${action} ${rawTeam}`:action;
      const histGames=Number(rpSignal.historical_games);
      const histPctRaw=Number(rpSignal.historical_ats_pct);
      const histPct=Number.isFinite(histPctRaw)?(histPctRaw>1?histPctRaw/100:histPctRaw):null;
      const histMargin=Number(rpSignal.historical_avg_ats_margin);
      const evidence=[
        rpSignal.detail,
        rpSignal.historical_ats_record?`${rpSignal.historical_ats_record} ATS`:null,
        histPct!==null?`${(histPct*100).toFixed(1)}% ATS`:null,
        Number.isFinite(histMargin)?`${histMargin>=0?'+':''}${histMargin.toFixed(2)} average ATS margin`:null,
        Number.isFinite(histGames)?`${histGames} historical games`:null,
        rpSignal.source?`Source: ${rpSignal.source}`:null
      ].filter(Boolean).join(' · ');
      add({
        id:'rp_study_signal',
        score:88,
        market:rpSignal.market||'Spread',
        team:side,
        trigger:rpSignal.headline||rpSignal.signal_type||'Historical early-season returning-production signal',
        evidence:evidence||'2023–25 early-season returning-production study match.'
      });
    }
    if(finite(s.home_line)&&finite(game.model.home_spread)){const edge=Math.abs(Number(s.home_line)-Number(game.model.home_spread));if(edge>=2)add({id:'model_spread_edge',score:100,market:'Spread',team:Number(s.home_line)>Number(game.model.home_spread)?game.game.home_team:game.game.away_team,trigger:`Model spread edge ${num(edge)} pts`,evidence:`Home perspective: model ${line(game.model.home_spread)} vs market ${line(s.home_line)}`})}
    if(finite(t.line)&&finite(game.model.total)){const edge=Math.abs(Number(t.line)-Number(game.model.total));if(edge>=2.5)add({id:'model_total_edge',score:95,market:'Total',team:Number(game.model.total)>Number(t.line)?'Over':'Under',trigger:`Model total edge ${num(edge)} pts`,evidence:`Model ${num(game.model.total)} vs market ${num(t.line)}`})}
    for(const team of [game.teams.away,game.teams.home]){
      const c=coachRole(team,game),opp=opponentTeam(team,game);
      for(const period of ['Full Game','1H','2H']){
        const sp=(c.coach?.role_splits||[]).find(x=>x.role===c.r&&x.period===period),games=Number(sp?.games),rate=Number(sp?.ats_pct),margin=Number(sp?.ats_margin),minimum=period==='Full Game'?25:12;
        if(games>=minimum&&rate>=.55&&margin>=1.5)add({id:`coach_${period.replaceAll(' ','_').toLowerCase()}_positive`,score:period==='Full Game'?82:78,market:period==='Full Game'?'Spread':period,team:team.team,trigger:`Coach ${period} ATS strength as ${c.r.toLowerCase()}`,evidence:`${sp.ats_record}, ${pct(rate)}, ${num(margin)} ATS +/- over ${games} games`});
        if(games>=minimum&&rate<=.45&&margin<=-1.5)add({id:`coach_${period.replaceAll(' ','_').toLowerCase()}_negative`,score:period==='Full Game'?82:78,market:period==='Full Game'?'Spread':period,team:opp.team,trigger:`Opposing coach poor ${period} ATS as ${c.r.toLowerCase()}`,evidence:`Supports ${opp.team}: ${team.team} coach ${sp.ats_record}, ${pct(rate)}, ${num(margin)} ATS +/- over ${games} games`});
      }
    }
    const opening=game.matchup.opening_possession||{},awayKind=tendencyKind(opening.away),homeKind=tendencyKind(opening.home);
    if(awayKind&&homeKind&&awayKind!==homeKind&&opening.projected_opening_receiver){const receiveTeam=awayKind==='receive'?game.teams.away:game.teams.home,deferTeam=awayKind==='defer'?game.teams.away:game.teams.home,prob=receiveTeam.team===game.game.away_team?opening.away_projected_receive_pct:opening.home_projected_receive_pct;if(Number(prob)>=60)add({id:'opening_possession_1h',score:76,market:'1H',team:opening.projected_opening_receiver,trigger:'Opposing receive vs defer toss tendencies',evidence:`${receiveTeam.team} coach receives ${num(receiveTeam.team===game.game.away_team?opening.away.receive_pct:opening.home.receive_pct,0)}% after wins; ${deferTeam.team} coach defers ${num(deferTeam.team===game.game.away_team?opening.away.defer_pct:opening.home.defer_pct,0)}%. Projected first possession: ${opening.projected_opening_receiver} (${num(prob,1)}%).`})}
    if(Number(game.game.week)<=4){const a=game.teams.away,h=game.teams.home,as=continuityScore(a.staff_continuity),hs=continuityScore(h.staff_continuity);if(as!==null&&hs!==null){const gap=Math.abs(as-hs),winner=as>hs?a:hs>as?h:null,loser=winner===a?h:a;if(winner&&((Number(winner.staff_continuity.returning_count)===3&&gap>=1)||(gap>=2)))add({id:'staff_continuity',score:70,market:'Early season',team:winner.team,trigger:'Coaching continuity advantage',evidence:`${winner.team}: ${winner.staff_continuity.returning_count}/3 returning vs ${loser.team}: ${loser.staff_continuity.returning_count}/3 returning (${loser.staff_continuity.new_count} new, ${loser.staff_continuity.partial_count} partial).`})}}
    const a=game.teams.away,h=game.teams.home,ar=a.returning_production||{},hr=h.returning_production||{},rpRank=Math.abs(Number(ar.overall_rank)-Number(hr.overall_rank)),rpPct=Math.abs(Number(ar.overall_pct)-Number(hr.overall_pct));if(!hasHistoricalRpSignal&&Number(game.game.week)<=4&&((Number.isFinite(rpRank)&&rpRank>=45)||(Number.isFinite(rpPct)&&rpPct>=20))){const team=Number(ar.overall_rank)<Number(hr.overall_rank)?a:h;if(finite(team.returning_production?.overall_rank))add({id:'returning_production_gap',score:60,market:'Spread',team:team.team,trigger:'Returning-production gap',evidence:`Supports ${team.team}: #${ar.overall_rank??'—'} (${ar.overall_pct??'—'}%) vs #${hr.overall_rank??'—'} (${hr.overall_pct??'—'}%)`})}
    if(Number(game.game.week)>=3){for(const team of [a,h]){const c=team.competition_context||{};if(c.qualifies){const opp=opponentTeam(team,game),supported=c.direction==='step_down'?team:opp;add({id:`competition_${c.direction}_${team.team}`,score:52,market:'Spread',team:supported.team,trigger:c.direction==='step_up'?`${team.team} steps up in competition`:`${team.team} steps down in competition`,evidence:`Current opponent #${c.current_opponent_rank} vs prior-schedule average #${num(c.prior_opponent_average_rank,0)} across ${c.prior_opponents} games (${Math.abs(Number(c.rank_gap)).toFixed(0)} rank spots).`})}}}
    return out.sort((x,y)=>y.score-x.score).map((x,i)=>({...x,priority:i+1}));
  }

/* VALIDATED_RP_MATCHUP_CONTEXT_START */
const MW_VALIDATED_FULL_GAME_RP_SIGNALS=[{"game_id":"g18","week":1,"date":"2026-09-03","away_team":"Akron","home_team":"Wake Forest","signal_team":"Wake Forest","signal_opponent":"Akron","primary_rule_key":"P4_G6_DEFENSE_15_PLUS","primary_rule_label":"P4 vs G6: defensive RP edge 15+","production_behavior":"context_only","overall_rp_edge":13.0,"offense_vs_defense_edge":8.0,"defense_vs_offense_edge":17.0,"has_defensive_support":true},{"game_id":"g24","week":1,"date":"2026-09-05","away_team":"East Carolina","home_team":"Alabama","signal_team":"Alabama","signal_opponent":"East Carolina","primary_rule_key":"P4_G6_EITHER_COMPONENT_25_PLUS","primary_rule_label":"P4 vs G6: either RP component edge 25+","production_behavior":"directional","overall_rp_edge":6.0,"offense_vs_defense_edge":-15.0,"defense_vs_offense_edge":28.0,"has_defensive_support":true},{"game_id":"g39","week":1,"date":"2026-09-05","away_team":"Florida Atlantic","home_team":"Florida","signal_team":"Florida","signal_opponent":"Florida Atlantic","primary_rule_key":"P4_G6_DEFENSE_15_PLUS","primary_rule_label":"P4 vs G6: defensive RP edge 15+","production_behavior":"context_only","overall_rp_edge":2.0,"offense_vs_defense_edge":-10.0,"defense_vs_offense_edge":15.0,"has_defensive_support":true},{"game_id":"g79","week":1,"date":"2026-09-05","away_team":"Kent State","home_team":"South Carolina","signal_team":"South Carolina","signal_opponent":"Kent State","primary_rule_key":"P4_G6_EITHER_COMPONENT_25_PLUS","primary_rule_label":"P4 vs G6: either RP component edge 25+","production_behavior":"directional","overall_rp_edge":20.0,"offense_vs_defense_edge":37.0,"defense_vs_offense_edge":4.0,"has_defensive_support":false},{"game_id":"g86","week":1,"date":"2026-09-05","away_team":"Missouri State","home_team":"Texas A&M","signal_team":"Texas A&M","signal_opponent":"Missouri State","primary_rule_key":"P4_G6_EITHER_COMPONENT_25_PLUS","primary_rule_label":"P4 vs G6: either RP component edge 25+","production_behavior":"directional","overall_rp_edge":31.0,"offense_vs_defense_edge":23.0,"defense_vs_offense_edge":38.0,"has_defensive_support":true},{"game_id":"g38","week":1,"date":"2026-09-05","away_team":"Tulane","home_team":"Duke","signal_team":"Duke","signal_opponent":"Tulane","primary_rule_key":"P4_G6_DEFENSE_15_PLUS","primary_rule_label":"P4 vs G6: defensive RP edge 15+","production_behavior":"context_only","overall_rp_edge":9.0,"offense_vs_defense_edge":-4.0,"defense_vs_offense_edge":23.0,"has_defensive_support":true},{"game_id":"g156","week":2,"date":"2026-09-12","away_team":"Charlotte","home_team":"Ole Miss","signal_team":"Ole Miss","signal_opponent":"Charlotte","primary_rule_key":"P4_G6_EITHER_COMPONENT_25_PLUS","primary_rule_label":"P4 vs G6: either RP component edge 25+","production_behavior":"directional","overall_rp_edge":18.0,"offense_vs_defense_edge":27.0,"defense_vs_offense_edge":10.0,"has_defensive_support":false},{"game_id":"g115","week":2,"date":"2026-09-12","away_team":"Georgia Southern","home_team":"Clemson","signal_team":"Clemson","signal_opponent":"Georgia Southern","primary_rule_key":"P4_G6_EITHER_COMPONENT_25_PLUS","primary_rule_label":"P4 vs G6: either RP component edge 25+","production_behavior":"directional","overall_rp_edge":10.0,"offense_vs_defense_edge":-16.0,"defense_vs_offense_edge":38.0,"has_defensive_support":true},{"game_id":"g180","week":2,"date":"2026-09-12","away_team":"Old Dominion","home_team":"Virginia Tech","signal_team":"Virginia Tech","signal_opponent":"Old Dominion","primary_rule_key":"P4_G6_EITHER_COMPONENT_25_PLUS","primary_rule_label":"P4 vs G6: either RP component edge 25+","production_behavior":"directional","overall_rp_edge":29.0,"offense_vs_defense_edge":13.0,"defense_vs_offense_edge":44.0,"has_defensive_support":true},{"game_id":"g108","week":2,"date":"2026-09-12","away_team":"Southern Miss","home_team":"Auburn","signal_team":"Auburn","signal_opponent":"Southern Miss","primary_rule_key":"P4_G6_EITHER_COMPONENT_25_PLUS","primary_rule_label":"P4 vs G6: either RP component edge 25+","production_behavior":"directional","overall_rp_edge":35.0,"offense_vs_defense_edge":36.0,"defense_vs_offense_edge":35.0,"has_defensive_support":true},{"game_id":"g125","week":2,"date":"2026-09-12","away_team":"Western Kentucky","home_team":"Georgia","signal_team":"Georgia","signal_opponent":"Western Kentucky","primary_rule_key":"P4_G6_EITHER_COMPONENT_25_PLUS","primary_rule_label":"P4 vs G6: either RP component edge 25+","production_behavior":"directional","overall_rp_edge":36.0,"offense_vs_defense_edge":37.0,"defense_vs_offense_edge":35.0,"has_defensive_support":true},{"game_id":"g247","week":3,"date":"2026-09-19","away_team":"Kennesaw State","home_team":"Tennessee","signal_team":"Tennessee","signal_opponent":"Kennesaw State","primary_rule_key":"P4_G6_DEFENSE_15_PLUS","primary_rule_label":"P4 vs G6: defensive RP edge 15+","production_behavior":"context_only","overall_rp_edge":13.0,"offense_vs_defense_edge":3.0,"defense_vs_offense_edge":23.0,"has_defensive_support":true},{"game_id":"g249","week":3,"date":"2026-09-19","away_team":"Kentucky","home_team":"Texas A&M","signal_team":"Texas A&M","signal_opponent":"Kentucky","primary_rule_key":"P4_P4_OVERALL_15_TO_24_9","primary_rule_label":"P4 vs P4: overall RP edge 15-24.9","production_behavior":"underdog_only","overall_rp_edge":19.0,"offense_vs_defense_edge":15.0,"defense_vs_offense_edge":23.0,"has_defensive_support":false},{"game_id":"g243","week":3,"date":"2026-09-19","away_team":"Mississippi State","home_team":"South Carolina","signal_team":"South Carolina","signal_opponent":"Mississippi State","primary_rule_key":"P4_P4_OVERALL_15_TO_24_9","primary_rule_label":"P4 vs P4: overall RP edge 15-24.9","production_behavior":"underdog_only","overall_rp_edge":20.0,"offense_vs_defense_edge":24.0,"defense_vs_offense_edge":17.0,"has_defensive_support":false},{"game_id":"g223","week":3,"date":"2026-09-19","away_team":"Troy","home_team":"Missouri","signal_team":"Missouri","signal_opponent":"Troy","primary_rule_key":"P4_G6_EITHER_COMPONENT_25_PLUS","primary_rule_label":"P4 vs G6: either RP component edge 25+","production_behavior":"directional","overall_rp_edge":10.0,"offense_vs_defense_edge":27.0,"defense_vs_offense_edge":-7.0,"has_defensive_support":false},{"game_id":"g248","week":3,"date":"2026-09-19","away_team":"UTSA","home_team":"Texas","signal_team":"Texas","signal_opponent":"UTSA","primary_rule_key":"P4_G6_EITHER_COMPONENT_25_PLUS","primary_rule_label":"P4 vs G6: either RP component edge 25+","production_behavior":"directional","overall_rp_edge":14.0,"offense_vs_defense_edge":29.0,"defense_vs_offense_edge":-1.0,"has_defensive_support":false},{"game_id":"g300","week":4,"date":"2026-09-26","away_team":"Appalachian State","home_team":"NC State","signal_team":"NC State","signal_opponent":"Appalachian State","primary_rule_key":"P4_G6_DEFENSE_15_PLUS","primary_rule_label":"P4 vs G6: defensive RP edge 15+","production_behavior":"context_only","overall_rp_edge":20.0,"offense_vs_defense_edge":23.0,"defense_vs_offense_edge":16.0,"has_defensive_support":true},{"game_id":"g311","week":4,"date":"2026-09-26","away_team":"Missouri State","home_team":"SMU","signal_team":"SMU","signal_opponent":"Missouri State","primary_rule_key":"P4_G6_EITHER_COMPONENT_25_PLUS","primary_rule_label":"P4 vs G6: either RP component edge 25+","production_behavior":"directional","overall_rp_edge":28.0,"offense_vs_defense_edge":22.0,"defense_vs_offense_edge":33.0,"has_defensive_support":true},{"game_id":"g265","week":4,"date":"2026-09-26","away_team":"South Carolina","home_team":"Alabama","signal_team":"South Carolina","signal_opponent":"Alabama","primary_rule_key":"P4_P4_OVERALL_15_TO_24_9","primary_rule_label":"P4 vs P4: overall RP edge 15-24.9","production_behavior":"underdog_only","overall_rp_edge":20.0,"offense_vs_defense_edge":15.0,"defense_vs_offense_edge":26.0,"has_defensive_support":false},{"game_id":"g270","week":4,"date":"2026-09-26","away_team":"Virginia Tech","home_team":"Boston College","signal_team":"Virginia Tech","signal_opponent":"Boston College","primary_rule_key":"P4_P4_OVERALL_15_TO_24_9","primary_rule_label":"P4 vs P4: overall RP edge 15-24.9","production_behavior":"underdog_only","overall_rp_edge":19.0,"offense_vs_defense_edge":14.0,"defense_vs_offense_edge":23.0,"has_defensive_support":false}];
const MW_VALIDATED_FULL_GAME_RP_BY_ID=new Map();
const MW_VALIDATED_FULL_GAME_RP_BY_MATCHUP=new Map();

function mwValidatedRpNormalizeTeam(value){
  return String(value??'')
    .toLowerCase()
    .replace(/&/g,' and ')
    .replace(/[^a-z0-9]+/g,' ')
    .trim();
}

function mwValidatedRpMatchupKey(away,home){
  return [
    mwValidatedRpNormalizeTeam(away),
    mwValidatedRpNormalizeTeam(home)
  ].sort().join('||');
}

for(const row of MW_VALIDATED_FULL_GAME_RP_SIGNALS){
  const gameId=String(row.game_id||'');

  if(gameId){
    if(!MW_VALIDATED_FULL_GAME_RP_BY_ID.has(gameId)){
      MW_VALIDATED_FULL_GAME_RP_BY_ID.set(gameId,[]);
    }
    MW_VALIDATED_FULL_GAME_RP_BY_ID.get(gameId).push(row);
  }

  const key=mwValidatedRpMatchupKey(row.away_team,row.home_team);
  if(!MW_VALIDATED_FULL_GAME_RP_BY_MATCHUP.has(key)){
    MW_VALIDATED_FULL_GAME_RP_BY_MATCHUP.set(key,[]);
  }
  MW_VALIDATED_FULL_GAME_RP_BY_MATCHUP.get(key).push(row);
}

function mwValidatedRpSignals(game){
  const gameId=String(game?.game?.game_id||'');
  const byId=MW_VALIDATED_FULL_GAME_RP_BY_ID.get(gameId)||[];
  if(byId.length) return byId;

  const key=mwValidatedRpMatchupKey(
    game?.game?.away_team,
    game?.game?.home_team
  );
  return MW_VALIDATED_FULL_GAME_RP_BY_MATCHUP.get(key)||[];
}

function mwValidatedRpNumber(value){
  const number=Number(value);
  return Number.isFinite(number)?number:null;
}

function mwValidatedRpHomeSpread(game){
  const spread=
    game?.market?.spread?.home_line ??
    game?.market?.spread_home ??
    game?.market_spread_home ??
    game?.model?.home_spread ??
    null;

  return mwValidatedRpNumber(spread);
}

function mwValidatedRpTeamSpread(game,signalTeam){
  const homeSpread=mwValidatedRpHomeSpread(game);
  if(homeSpread===null) return null;

  if(signalTeam===game?.game?.home_team) return homeSpread;
  if(signalTeam===game?.game?.away_team) return -homeSpread;
  return null;
}

function mwValidatedRpSigned(value){
  const number=mwValidatedRpNumber(value);
  if(number===null) return '—';
  return `${number>0?'+':''}${number.toFixed(0)}`;
}

function mwValidatedRpLegacyRow(row){
  const id=String(row?.id||'').toLowerCase();
  const group=String(row?.signal_group||'').toLowerCase();
  const type=String(row?.signal_type||'').toLowerCase();
  const text=[
    row?.market,
    row?.team,
    row?.trigger,
    row?.evidence,
    row?.headline,
    row?.detail
  ].join(' ').toLowerCase();

  return (
    id.includes('returning_production') ||
    id.startsWith('rp_') ||
    group==='returning production' ||
    type==='rp_support' ||
    text.includes('returning-production') ||
    text.includes('returning production') ||
    text.includes('high overall rp') ||
    text.includes('high defense rp') ||
    text.includes('low offense rp')
  );
}

function mwValidatedRpContextRows(game){
  const rows=[];

  for(const signal of mwValidatedRpSignals(game)){
    const overall=mwValidatedRpSigned(signal.overall_rp_edge);
    const offense=mwValidatedRpSigned(signal.offense_vs_defense_edge);
    const defense=mwValidatedRpSigned(signal.defense_vs_offense_edge);

    if(signal.primary_rule_key==='P4_G6_EITHER_COMPONENT_25_PLUS'){
      rows.push({
        id:'validated_rp_p4_g6_component_25',
        score:84,
        priority:'High',
        market:'Spread',
        team:signal.signal_team,
        trigger:'Validated full-game RP mismatch',
        evidence:
          `${signal.signal_team} owns the returning-production matchup edge `+
          `(overall ${overall}, offense vs defense ${offense}, `+
          `defense vs offense ${defense}). `+
          `Historical rule: 50-31 ATS (61.7%, n=81), 2021-25 Weeks 1-4.`
      });
      continue;
    }

    if(signal.primary_rule_key==='P4_P4_OVERALL_15_TO_24_9'){
      const teamSpread=mwValidatedRpTeamSpread(
        game,
        signal.signal_team
      );

      if(teamSpread!==null && teamSpread>0){
        rows.push({
          id:'validated_rp_p4_p4_underdog',
          score:80,
          priority:'High',
          market:'Spread',
          team:signal.signal_team,
          trigger:'Validated RP-edge underdog',
          evidence:
            `${signal.signal_team} owns the returning-production edge `+
            `(overall ${overall}, offense vs defense ${offense}, `+
            `defense vs offense ${defense}) and is a ${teamSpread>0?'+':''}${teamSpread.toFixed(1)} underdog. `+
            `Historical RP-edge underdogs: 12-5 ATS (70.6%, n=17).`
        });
      }
      continue;
    }

    // P4_G6_DEFENSE_15_PLUS is supporting context only.
    // It remains visible in the validated RP detail card but is deliberately
    // excluded from this qualifying-rules-only table.
  }

  return rows;
}

function contextRows(game){
  const legacyRows=legacyContextRows(game);
  const nonRpRows=legacyRows.filter(
    row=>!mwValidatedRpLegacyRow(row)
  );
  return [
    ...nonRpRows,
    ...mwValidatedRpContextRows(game)
  ].sort((a,b)=>(Number(b.score)||0)-(Number(a.score)||0));
}
/* VALIDATED_RP_MATCHUP_CONTEXT_END */


function contextTable(game){ const rows=contextRows(game); const empty=!rows.length; return `<section class="mwSection ${empty?'mwContextEmptySection':''}" data-section="betting-context"><h3>Key betting context — qualifying rules only</h3><div class="mwTableWrap"><table class="mwTable mwContextTable"><thead><tr><th>Priority</th><th>Market</th><th>Side</th><th>Angle</th><th>Key evidence</th></tr></thead><tbody>${rows.map(x=>`<tr data-rule="${esc(x.id)}" data-priority="${esc(x.priority||'Low')}"><td><span class="mwPriority">${x.priority}</span></td><td>${esc(x.market)}</td><td><b>${esc(x.team)}</b></td><td>${esc(x.trigger)}</td><td class="mwEvidence">${esc(x.evidence)}</td></tr>`).join('')||'<tr><td colspan="5" class="mwMuted mwContextEmpty">No qualifying betting context for this matchup.</td></tr>'}</tbody></table></div></section>`; }
  function splitCell(split){if(!split||split.available===false)return '<span class="mwMuted">No matched sample</span>';return `<b>${esc(split.ats_record||'—')} ATS</b> · ${pct(split.ats_pct)} · ${num(split.ats_margin,1)} +/-<br><span class="mwMuted">O/U ${esc(split.ou_record||'—')} · N=${split.games??'—'}</span>`;}
  function coachingDetail(game){const rows=(game.matchup.coaches||[]);return `<section class="mwSection mwCoachDetail"><details><summary>Complete coaching ATS / totals splits — Full Game, 1H and 2H</summary><div class="mwCoachGrid"><div class="mwCoachCell mwCoachHead">Team / period</div><div class="mwCoachCell mwCoachHead">Favorite</div><div class="mwCoachCell mwCoachHead">Underdog</div>${rows.map(c=>['Full Game','1H','2H'].map((period,i)=>{const fav=(c.role_splits||[]).find(x=>x.period===period&&x.role==='Favorite'),dog=(c.role_splits||[]).find(x=>x.period===period&&x.role==='Underdog');return `<div class="mwCoachCell"><b>${i===0?esc(c.team)+'<br>':''}${esc(period)}</b>${i===0?`<br><span class="mwMuted">${esc(c.coach||'—')}</span>`:''}</div><div class="mwCoachCell">${splitCell(fav)}</div><div class="mwCoachCell">${splitCell(dog)}</div>`}).join('')).join('')}</div></details></section>`;}
  function daysBetween(a,b){const x=Date.parse(a),y=Date.parse(b);return Number.isFinite(x)&&Number.isFinite(y)?Math.round((y-x)/86400000):null}
  function spotValue(value,detail=''){return `<b class="${value==='Yes'?'mwWarn':value==='No'?'mwGood':'mwMuted'}">${value}</b>${detail?`<span class="mwMuted"> · ${esc(detail)}</span>`:''}`}
  function teamSpots(team,game){
    const rows=scheduleRows(team,game);
    const idx=rows.findIndex(x=>String(x.game_id)===String(game.game.game_id)||(!x.is_bye&&x.date===game.game.date));
    const cur=idx>=0?rows[idx]:null,prev=idx>0?rows[idx-1]:null,next=idx>=0&&idx<rows.length-1?rows[idx+1]:null;
    const road=x=>/away|neutral/i.test(String(x?.site||''));
    const rest=prev&&cur?daysBetween(prev.date,cur.date):null;
    const b2b=cur&&prev&&road(cur)&&road(prev)?'Yes':'No';
    const bye=prev?.is_bye||rest>=12?'Yes':'No';
    const nextRank=next?.opponent_ranks?.overall;
    const look=next&&!next.is_bye&&finite(nextRank)&&Number(nextRank)<=25?'Watch':'No';
    const travel=road(cur)?'Road':'No';
    return {b2b,bye,look,travel};
  }
  function spotsTable(game){
    const away=teamSpots(game.teams.away,game),home=teamSpots(game.teams.home,game);
    const rows=[['B2B road','b2b'],['Off bye','bye'],['Lookahead','look'],['Travel','travel']];
    const value=v=>`<span class="mwSpotValue ${v==='Yes'?'mwSpotYes':v==='Watch'?'mwSpotWatch':'mwSpotNo'}">${esc(v)}</span>`;
    const side=(team,spots)=>`<div class="mwMiniCard"><div class="mwSpotTeam">${logo(team)}<span>${esc(team.team)}</span></div><div class="mwSpotGrid">${rows.map(([label,key])=>`<div class="mwSpot"><b>${label}</b>${value(spots[key])}</div>`).join('')}</div></div>`;
    return `<section class="mwSection mwSpots"><h3>Schedule spots</h3><div class="mwDenseGrid">${side(game.teams.away,away)}${side(game.teams.home,home)}</div></section>`;
  }
  function marketCards(game, history){
    const ACTIONABLE_HISTORY_BOOKS=new Set(['DraftKings','FanDuel','BetMGM','Caesars']);
    const normalizeHistoryBook=v=>{
      const s=String(v||'').trim().toLowerCase();
      if(s==='draftkings')return'DraftKings';
      if(s==='fanduel')return'FanDuel';
      if(s==='betmgm')return'BetMGM';
      if(s==='caesars'||s==='williamhill_us'||s==='william hill')return'Caesars';
      return String(v||'').trim();
    };
    const rowBook=row=>normalizeHistoryBook(row.market_spread_book||row.market_total_book||'');
    const rowQuality=row=>{
      let q=0;
      if(finite(row.market_spread_home))q+=2;
      if(finite(row.market_spread_price))q+=2;
      if(finite(row.market_total))q+=2;
      if(finite(row.market_total_over_price))q+=1;
      if(finite(row.market_total_under_price))q+=1;
      if(String(row.source||row.snapshot_label||'').toLowerCase()==='the odds api')q+=1;
      return q;
    };

    const allRows=[...(history[game.game.game_id]||[])]
      .filter(row=>ACTIONABLE_HISTORY_BOOKS.has(rowBook(row)))
      .sort((a,b)=>{
        const ak=String(a.snapshot_ts||a.snapshot_date||a.market_spread_last_update||a.market_total_last_update||'');
        const bk=String(b.snapshot_ts||b.snapshot_date||b.market_spread_last_update||b.market_total_last_update||'');
        return ak.localeCompare(bk);
      });

    const byDate=new Map();
    for(const row of allRows){
      const rawDate=String(row.snapshot_date||row.snapshot_ts||row.market_spread_last_update||row.market_total_last_update||'');
      const dateKey=rawDate.slice(0,10)||rawDate;
      if(!dateKey)continue;
      const prior=byDate.get(dateKey);
      if(!prior||rowQuality(row)>=rowQuality(prior))byDate.set(dateKey,row);
    }

    const daily=[...byDate.entries()]
      .sort((a,b)=>String(a[0]).localeCompare(String(b[0])))
      .map(([,row])=>row);

    const firstSpread=daily.find(x=>finite(x.market_spread_home))||{};
    const firstTotal=daily.find(x=>finite(x.market_total))||{};
    const cutoff=new Date();
    cutoff.setDate(cutoff.getDate()-7);
    const latest=daily.filter(row=>{
      const d=new Date(row.snapshot_ts||row.snapshot_date||row.market_spread_last_update||row.market_total_last_update);
      return !Number.isNaN(d.getTime()) && d>=cutoff;
    }).reverse();

    const capturedText=(row,market)=>{
      const value=market==='spread'
        ? (row.snapshot_ts||row.market_spread_last_update||row.snapshot_date)
        : (row.snapshot_ts||row.market_total_last_update||row.snapshot_date);
      if(!value)return 'Captured: —';
      const text=String(value);
      const parsed=new Date(text);
      if(!Number.isNaN(parsed.getTime())&&text.includes('T')){
        return `Captured: ${parsed.toLocaleString([],{
          year:'numeric',month:'2-digit',day:'2-digit',
          hour:'numeric',minute:'2-digit'
        })}`;
      }
      return `Captured: ${esc(text.slice(0,16).replace('T',' '))}`;
    };

    const openSpread=finite(firstSpread.market_spread_home)
      ? `${esc(game.game.home_team)} ${line(firstSpread.market_spread_home)} ${price(firstSpread.market_spread_price)}`
      : '—';

    const openTotal=finite(firstTotal.market_total)
      ? `${num(firstTotal.market_total)} · O ${price(firstTotal.market_total_over_price)} / U ${price(firstTotal.market_total_under_price)}`
      : '—';

    return `<section class="mwSection mwHistory" data-section="line-history">
      <h3>Line history — ATS spread and O/U total</h3>
      <div class="mwHistoryLegend">
        <span><i class="mwLegendDot mwLegendLower"></i>Lower</span>
        <span><i class="mwLegendDot mwLegendHigher"></i>Higher</span>
        <span><i class="mwLegendDot mwLegendFlat"></i>Unchanged</span>
      </div>
      <div class="mwHistorySummary">
        <div class="mwHistorySummaryCard">
          <b>Opening ATS line:</b> ${openSpread}
          <div class="mwMuted">${capturedText(firstSpread,'spread')}</div>
        </div>
        <div class="mwHistorySummaryCard">
          <b>Opening O/U:</b> ${openTotal}
          <div class="mwMuted">${capturedText(firstTotal,'total')}</div>
        </div>
      </div>
      <div class="mwTableWrap">
        <table class="mwTable">
          <thead><tr><th>Date / Time</th><th>Book</th><th>ATS spread</th><th>Spread price</th><th>Spread move</th><th>O/U total</th><th>Over</th><th>Under</th><th>Total move</th></tr></thead>
          <tbody>${latest.map((x,i)=>{
            const older=latest[i+1]||{};
            const displayDate=String(x.snapshot_date||x.snapshot_ts||x.market_spread_last_update||x.market_total_last_update||'—').slice(0,10);
            const book=rowBook(x);
            return `<tr><td>${esc(displayDate)}</td><td>${bookLogo(book)||esc(book||'—')}</td><td>${line(x.market_spread_home)}</td><td>${price(x.market_spread_price)}</td><td>${movementText(x.market_spread_home,older.market_spread_home)}</td><td>${num(x.market_total)}</td><td>${price(x.market_total_over_price)}</td><td>${price(x.market_total_under_price)}</td><td>${movementText(x.market_total,older.market_total)}</td></tr>`;
          }).join('')||'<tr><td colspan="9" class="mwMuted">No actionable-book line-history snapshots available.</td></tr>'}</tbody>
        </table>
      </div>
    </section>`;
  }
  function injuries(game){ const teams=[game.teams.away,game.teams.home]; if(!teams.some(team=>(team.injuries||[]).length))return ''; return `<section class="mwSection"><h3>Injuries</h3><div class="mwDenseGrid">${teams.map(team=>`<div class="mwMiniCard"><div class="mwMiniTitle">${esc(team.team)}</div>${(team.injuries||[]).slice(0,4).map(x=>`<div class="mwTicket"><span>${esc(x.player||x.name||'Player')} · ${esc(x.position||'')}</span><b>${esc(x.status||'Unknown')}</b></div>`).join('')||'<div class="mwEmpty">No matched injury records.</div>'}</div>`).join('')}</div></section>`; }
  function betsHtml(game){ const all=[...(game.activity?.wagers||[]).map(x=>({...x,sheet:true})),...(localBets[game.game.game_id]||[])];return all.map((x,i)=>`<div class="mwTicket"><div><b>${esc(x.market||'Bet')} · ${esc(x.selection||'—')} ${price(x.price)}</b><div class="mwMuted">${x.sheet?'Google Sheet':esc(x.book||'Local')} · ${finite(x.stake)?'$'+num(x.stake,2):'Stake not set'}</div></div>${x.sheet?'<span class="mwGood">LIVE</span>':`<button onclick="removeMatchupBet(${i-(game.activity?.wagers||[]).length})">Remove</button>`}</div>`).join('')||'<div class="mwMuted">No saved bets on this game.</div>'; }
  function bottom(game){
    const hasBets=(game.activity?.wagers||[]).length+(localBets[game.game.game_id]||[]).length>0;
    const hasNote=!!notes[game.game.game_id];
    const bets=hasBets?`<section class="mwSection"><h3>Saved bets</h3><div id="mwSavedBets">${betsHtml(game)}</div></section>`:'';
    const note=hasNote?`<section class="mwSection"><h3>Notes</h3><textarea id="mwNotes" class="mwNotes" placeholder="Add matchup notes…">${esc(notes[game.game.game_id]||'')}</textarea><div class="mwActions"><button onclick="saveMatchupNote()">Save note</button></div></section>`:`<section class="mwSection"><div class="mwEmptyTools"><button class="mwAddNoteBtn" onclick="this.closest('.mwSection').innerHTML='<h3>Notes</h3><textarea id=&quot;mwNotes&quot; class=&quot;mwNotes&quot; placeholder=&quot;Add matchup notes…&quot;></textarea><div class=&quot;mwActions&quot;><button onclick=&quot;saveMatchupNote()&quot;>Save note</button></div>'">Add note</button></div></section>`;
    return bets||hasNote?`<div class="mwGrid2">${bets}${note}</div>`:note;
  }
  function actions(game){const d=decisions[game.game.game_id];return `<div class="mwActions"><button class="primary" onclick="openMatchupBet('${game.game.game_id}','Spread')">Bet Spread</button><button class="primary" onclick="openMatchupBet('${game.game.game_id}','Total')">Bet Total</button><button class="${d==='watch'?'active':''}" onclick="setMatchupDecision('watch')">${d==='watch'?'★ Watched':'☆ Watch'}</button><button class="${d==='pass'?'active':''}" onclick="setMatchupDecision('pass')">${d==='pass'?'Remove Pass':'Pass'}</button>${d?'<button onclick="setMatchupDecision(null)">Clear</button>':''}</div>`;}
  function render(game, history, section){ document.getElementById('mwContent').innerHTML=`<header class="mwHead"><div><h2>${esc(game.game.away_team)} at ${esc(game.game.home_team)}</h2><div class="mwSub">${esc(game.game.date)} · Week ${game.game.week} · ${esc(game.game.game_id)}</div></div><button class="mwClose" onclick="closeMatchupWorkspace()">×</button></header><div class="mwBody"><section class="mwSection">${marketSummary(game)}${actions(game)}</section><div class="mwGrid2">${teamCard(game.teams.away,game)}${teamCard(game.teams.home,game)}</div><div class="mwGrid2">${scheduleCard(game.teams.away,game)}${scheduleCard(game.teams.home,game)}</div>${contextTable(game)}<div class="mwGrid2">${fiveFactorTable(`${game.game.away_team} offense vs ${game.game.home_team} defense`,game.matchup.away_offense_vs_home_defense,game.game.away_team,game.game.home_team,game)}${fiveFactorTable(`${game.game.home_team} offense vs ${game.game.away_team} defense`,game.matchup.home_offense_vs_away_defense,game.game.home_team,game.game.away_team,game)}</div>${spotsTable(game)}${injuries(game)}${marketCards(game,history)}${bottom(game)}</div>`; if(section){const el=document.querySelector(`#mwContent [data-section="${CSS.escape(section)}"]`);el?.scrollIntoView()}}
  async function open(gameId, initialSection){ ensureShell(); const [data,history]=await Promise.all([loadData(),loadHistory()]); const game=data.games.find(x=>String(x.game.game_id)===String(gameId)); if(!game)throw Error(`Game not found: ${gameId}`); selectedId=String(gameId);selectedGame=game;render(game,history,initialSection);document.getElementById('mwBackdrop').classList.add('open');document.body.style.overflow='hidden'; }
  function close(){document.getElementById('mwBackdrop')?.classList.remove('open');document.body.style.overflow='';selectedId=null;selectedGame=null;}
  function emit(){decorateLinks();document.dispatchEvent(new CustomEvent('matchup-workspace-statechange',{detail:{gameId:selectedId,decision:decisions[selectedId],notes:!!notes[selectedId],betCount:(localBets[selectedId]||[]).length+(selectedGame?.activity?.wagers||[]).length}}));}
  function rerender(){if(selectedGame)loadHistory().then(h=>render(selectedGame,h));emit();}
  function decision(value){if(!selectedId)return;if(!value||decisions[selectedId]===value)delete decisions[selectedId];else decisions[selectedId]=value;save(DECISION_KEY,decisions);rerender();}
  function note(){if(!selectedId)return;const value=document.getElementById('mwNotes')?.value||'';if(value.trim())notes[selectedId]=value;else delete notes[selectedId];save(NOTE_KEY,notes);rerender();}
  function openBet(gameId,kind='Spread'){selectedId=String(gameId);const g=selectedGame;if(!g)return;const spread=g.market.spread||{},total=g.market.total||{};document.getElementById('mwBetGame').textContent=`${g.game.away_team} at ${g.game.home_team}`;document.getElementById('mwBetMarket').value=kind;document.getElementById('mwBetSelection').value=kind==='Total'?`Total ${num(total.line??g.model.total)}`:`${g.game.home_team} ${line(spread.home_line??g.model.home_spread)}`;document.getElementById('mwBetPrice').value=kind==='Total'?price(total.over_price??-110):price(spread.price??-110);document.getElementById('mwBetBook').value=kind==='Total'?(total.book||''):(spread.book||'');document.getElementById('mwBetStake').value='';document.getElementById('mwBetModal').classList.add('open');}
  function closeBet(){document.getElementById('mwBetModal')?.classList.remove('open');}
  function saveBet(){if(!selectedId)return;(localBets[selectedId] ||= []).push({market:document.getElementById('mwBetMarket').value,selection:document.getElementById('mwBetSelection').value,price:document.getElementById('mwBetPrice').value,book:document.getElementById('mwBetBook').value,stake:document.getElementById('mwBetStake').value,time:new Date().toISOString()});save(BET_KEY,localBets);closeBet();rerender();}
  function removeBet(index){if(!selectedId||!localBets[selectedId])return;localBets[selectedId].splice(index,1);if(!localBets[selectedId].length)delete localBets[selectedId];save(BET_KEY,localBets);rerender();}
  function decorateLinks(){
    document.querySelectorAll('a[href*="game_id="],[data-matchup-id]').forEach(a=>{
      const raw=a.dataset.matchupId||new URL(a.href,location.href).searchParams.get('game_id');
      if(!raw)return;
      if(a.dataset.matchupId!==raw)a.dataset.matchupId=raw;
      a.style.setProperty('color','inherit','important');
      a.style.setProperty('text-decoration','none','important');
      a.onclick=e=>{e.preventDefault();e.stopPropagation();open(raw,a.dataset.matchupSection)};
      let badge=a.querySelector('.mwSourceState');
      const bits=[];
      if(decisions[raw]==='watch')bits.push('★');
      if(decisions[raw]==='pass')bits.push('PASS');
      if(notes[raw])bits.push('NOTE');
      const count=(localBets[raw]||[]).length;
      if(count)bits.push(`BET ${count}`);
      if(bits.length){
        if(!badge){badge=document.createElement('span');badge.className='mwSourceState';a.appendChild(badge)}
        const next=bits.join(' · ');
        if(badge.textContent!==next)badge.textContent=next;
        badge.classList.toggle('bet',count>0);
      }else if(badge){
        badge.remove();
      }
    });
  }

  window.NCAAFMatchupContextSummary=async function(gameId){
    const data=await loadData();
    const game=data.games.find(x=>String(x.game.game_id)===String(gameId));
    if(!game)return null;
    return {
      game_id:String(gameId),
      away_team:game.game.away_team,
      home_team:game.game.home_team,
      away_logo_slug:game.teams.away.logo_slug,
      home_logo_slug:game.teams.home.logo_slug,
      rows:contextRows(game)
    };
  };

  window.NCAAFMatchupContextSummaryFromText=async function(rowText){
    const data=await loadData();
    const raw=String(rowText||'').toLowerCase();
    const matches=data.games.filter(x=>{
      const away=String(x.game.away_team||'').toLowerCase();
      const home=String(x.game.home_team||'').toLowerCase();
      return away&&home&&raw.includes(away)&&raw.includes(home);
    });
    if(!matches.length)return null;
    const game=matches[0];
    return {
      game_id:String(game.game.game_id),
      away_team:game.game.away_team,
      home_team:game.game.home_team,
      away_logo_slug:game.teams.away.logo_slug,
      home_logo_slug:game.teams.home.logo_slug,
      rows:contextRows(game)
    };
  };
  window.openMatchupWorkspace=open;window.closeMatchupWorkspace=close;window.setMatchupDecision=decision;window.saveMatchupNote=note;window.openMatchupBet=openBet;window.closeMatchupBet=closeBet;window.saveMatchupBet=saveBet;window.removeMatchupBet=removeBet;
  window.__matchupWorkspaceTest={rankClass,contextRows,teamSpots,scheduleRows};
  function gameIdFromTrigger(target){
    if(/schedule_v2\.html(?:$|[?#])/i.test(location.pathname+location.search+location.hash))return null;
    if(!target)return null;
    if(target.closest?.('.scheduleNativeRow'))return null;
    const row=target.closest?.('tr');

    const direct=
      target.dataset?.matchupId||
      target.dataset?.gameId||
      target.dataset?.id||
      row?.dataset?.matchupId||
      row?.dataset?.gameId||
      row?.dataset?.id||
      row?.dataset?.game;
    if(direct)return String(direct);

    const linked=row?.querySelector?.('a[href*="game_id="]');
    if(linked){
      try{
        const linkedId=new URL(linked.getAttribute('href'),location.href).searchParams.get('game_id');
        if(linkedId)return linkedId;
      }catch(_){}
    }

    const attrs=[
      target.getAttribute?.('onclick')||'',
      row?.getAttribute?.('onclick')||'',
      target.closest?.('a[href]')?.getAttribute('href')||'',
      row?.innerHTML||''
    ].join(' ');

    const exact=attrs.match(/(?:openDrawer|openGame|openMatchupWorkspace|showMatchup|openWorkspace)\s*\(\s*['"]([^'"]+)['"]/i);
    if(exact)return exact[1];

    const gid=attrs.match(/\b(g\d+)\b/i);
    return gid?gid[1]:null;
  }

  async function inferGameIdFromRow(row){
    if(!row)return null;
    const data=await loadData();
    const rowText=(row.textContent||'').replace(/\s+/g,' ').trim().toLowerCase();
    if(!rowText)return null;

    const matches=data.games.filter(game=>{
      const away=String(game.game.away_team||'').toLowerCase();
      const home=String(game.game.home_team||'').toLowerCase();
      return away&&home&&rowText.includes(away)&&rowText.includes(home);
    });

    if(matches.length===1)return String(matches[0].game.game_id);

    const weekMatch=rowText.match(/\bw(?:eek)?\s*(\d+)\b/i);
    if(matches.length>1&&weekMatch){
      const week=Number(weekMatch[1]);
      const narrowed=matches.filter(game=>Number(game.game.week)===week);
      if(narrowed.length===1)return String(narrowed[0].game.game_id);
    }
    return null;
  }

  function isRowOpenClick(target,row){
    if(!row||row.closest('thead'))return false;
    if(target.closest('input,select,textarea,label'))return false;

    const button=target.closest('button');
    if(button){
      const label=(button.textContent||'').trim();
      return button.matches('.open,.open-matchup,.matchup-open,[data-open-matchup],[data-matchup-id],[data-game-id]')||
        label==='›'||label==='>'||label==='→';
    }

    return !!row.closest('tbody');
  }

  document.addEventListener('click',async e=>{
    const row=e.target.closest?.('tr');
    if(!isRowOpenClick(e.target,row))return;

    const button=e.target.closest?.('button');
    if(button&&!['›','>','→'].includes((button.textContent||'').trim())&&
       !button.matches('.open,.open-matchup,.matchup-open,[data-open-matchup],[data-matchup-id],[data-game-id]'))return;

    let gameId=gameIdFromTrigger(e.target);
    if(!gameId)gameId=await inferGameIdFromRow(row);
    if(!gameId)return;

    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();

    open(gameId,e.target.dataset?.matchupSection)
      .catch(error=>console.warn('Unable to open shared matchup workspace:',error.message));
  },true);

  ensureShell();decorateLinks();new MutationObserver(decorateLinks).observe(document.body,{childList:true,subtree:true});document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeBet();close()}});
  const linkedGameId = new URLSearchParams(location.search).get('game_id');
  if(linkedGameId) open(linkedGameId).catch(error=>console.warn('Unable to open shared matchup workspace:',error.message));
  // Backward-compatible canonical opener for the Openers page.
  window.openDrawer=open;window.closeDrawer=close;
})();
