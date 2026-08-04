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

OLD_CSS_START = "/* OPENERS_CONTEXT_GUIDE_CSS_START */"
OLD_CSS_END = "/* OPENERS_CONTEXT_GUIDE_CSS_END */"
OLD_JS_START = "/* OPENERS_CONTEXT_GUIDE_JS_START */"
OLD_JS_END = "/* OPENERS_CONTEXT_GUIDE_JS_END */"
NEW_CSS_START = "/* OPENERS_BETTING_ANGLES_COMPACT_CSS_START */"
NEW_CSS_END = "/* OPENERS_BETTING_ANGLES_COMPACT_CSS_END */"
NEW_JS_START = "/* OPENERS_BETTING_ANGLES_COMPACT_JS_START */"
NEW_JS_END = "/* OPENERS_BETTING_ANGLES_COMPACT_JS_END */"
CACHE_VERSION = "20260728-bettingangles5"

CSS_BLOCK = r'''
/* OPENERS_BETTING_ANGLES_COMPACT_CSS_START */
.bettingAnglesToolbar{display:flex;justify-content:flex-end;align-items:center;margin:4px 0 7px}
.bettingAnglesGuide{position:relative;border:1px solid #315f89;border-radius:999px;background:#0c203b;color:#cfe0f5}
.bettingAnglesGuide summary{cursor:pointer;list-style:none;padding:6px 11px;font-size:10px;font-weight:900;white-space:nowrap}
.bettingAnglesGuide summary::-webkit-details-marker{display:none}
.bettingAnglesGuide summary::after{content:'+';margin-left:6px;color:#8fb7df}
.bettingAnglesGuide[open] summary::after{content:'–'}
.bettingAnglesGuidePanel{position:absolute;z-index:50;right:0;top:calc(100% + 6px);width:min(680px,86vw);display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;padding:9px;border:1px solid #315f89;border-radius:10px;background:#08172c;box-shadow:0 14px 30px rgba(0,0,0,.35)}
.bettingAnglesGuideCard{border:1px solid #274b6d;border-radius:8px;background:#0d213d;padding:8px}
.bettingAnglesGuideHead{display:flex;align-items:center;gap:6px;margin-bottom:5px;font-size:10px;font-weight:950}
.bettingAnglesGuideCard ul{margin:0;padding-left:16px;color:#b8c9df;font-size:9px;line-height:1.35}
.bettingAnglesGuideDot{width:8px;height:8px;border-radius:999px;flex:0 0 auto}
.bettingAnglesGuideDot.high{background:#38d98b}.bettingAnglesGuideDot.medium{background:#f2c14e}.bettingAnglesGuideDot.low{background:#8293aa}
.bettingAnglesSortHeader{cursor:pointer;user-select:none;white-space:nowrap}
.bettingAnglesSortHeader::after{content:' ↕';color:#8fb7df;font-size:10px}
.bettingAnglesSortHeader[data-sort="high"]::after{content:' ↓'}
.bettingAnglesSortHeader[data-sort="low"]::after{content:' ↑'}
.bettingAnglesSortHint{display:block;margin-top:2px;color:#8ea5c4;font-size:8px;font-weight:700;text-transform:none}
@media(max-width:800px){.bettingAnglesGuidePanel{position:fixed;left:10px;right:10px;top:90px;width:auto;grid-template-columns:1fr}}
/* OPENERS_BETTING_ANGLES_COMPACT_CSS_END */
'''

JS_BLOCK = r'''
/* OPENERS_BETTING_ANGLES_COMPACT_JS_START */
function bettingAnglesPriorityValue(row){
  if(row.querySelector('.contextPriorityDot.high'))return 3;
  if(row.querySelector('.contextPriorityDot.medium'))return 2;
  if(row.querySelector('.contextPriorityDot.low'))return 1;
  return 0;
}
function bettingAnglesFindBoard(){
  return [...document.querySelectorAll('table')].find(table=>{
    const headers=[...table.querySelectorAll('thead th')].map(th=>th.textContent.trim().toUpperCase());
    return headers.includes('CONTEXT')||headers.some(x=>x.startsWith('BETTING ANGLES'));
  })||null;
}
function bettingAnglesInstallToolbar(table){
  if(document.querySelector('.bettingAnglesToolbar'))return;
  const toolbar=document.createElement('div');
  toolbar.className='bettingAnglesToolbar';
  toolbar.innerHTML=`
    <details class="bettingAnglesGuide">
      <summary>Angles guide</summary>
      <div class="bettingAnglesGuidePanel">
        <div class="bettingAnglesGuideCard">
          <div class="bettingAnglesGuideHead"><span class="bettingAnglesGuideDot high"></span>High</div>
          <ul><li>P4-vs-G6 RP: 50-31 ATS, 61.7%, n=81</li><li>Full-game coach: n≥40 and ≥60% or ≤40%</li></ul>
        </div>
        <div class="bettingAnglesGuideCard">
          <div class="bettingAnglesGuideHead"><span class="bettingAnglesGuideDot medium"></span>Medium</div>
          <ul><li>P4-vs-P4 RP dog: 12-5 ATS, 70.6%, n=17</li><li>Full-game coach: n≥25 and ≥57.5% or ≤42.5%</li><li>1H/2H coach: n≥25 and ≥60% or ≤40%</li><li>Meaningful injury edge</li></ul>
        </div>
        <div class="bettingAnglesGuideCard">
          <div class="bettingAnglesGuideHead"><span class="bettingAnglesGuideDot low"></span>Low</div>
          <ul><li>Coach: n≥15 and ≥55% or ≤45%</li><li>Schedule, continuity, weather, or market context</li></ul>
        </div>
      </div>
    </details>`;
  table.parentElement.insertBefore(toolbar,table);
}
function bettingAnglesInstallSort(table){
  const headers=[...table.querySelectorAll('thead th')];
  const header=headers.find(th=>{
    const text=th.textContent.trim().toUpperCase();
    return text==='CONTEXT'||text.startsWith('BETTING ANGLES');
  });
  if(!header)return;
  header.classList.add('bettingAnglesSortHeader');
  header.dataset.sort=header.dataset.sort||'default';
  header.innerHTML='BETTING ANGLES<span class="bettingAnglesSortHint">click to sort priority</span>';
  const tbody=table.tBodies?.[0];
  if(!tbody)return;
  [...tbody.rows].forEach((row,index)=>{if(row.dataset.originalOrder==null)row.dataset.originalOrder=String(index)});
  if(header.dataset.bound==='1')return;
  header.dataset.bound='1';
  header.addEventListener('click',()=>{
    const next=header.dataset.sort==='default'?'high':header.dataset.sort==='high'?'low':'default';
    header.dataset.sort=next;
    const rows=[...tbody.rows];
    rows.sort((a,b)=>{
      if(next==='default')return Number(a.dataset.originalOrder)-Number(b.dataset.originalOrder);
      const diff=bettingAnglesPriorityValue(b)-bettingAnglesPriorityValue(a);
      if(next==='low')return -diff||Number(a.dataset.originalOrder)-Number(b.dataset.originalOrder);
      return diff||Number(a.dataset.originalOrder)-Number(b.dataset.originalOrder);
    });
    rows.forEach(row=>tbody.appendChild(row));
  });
}
function bettingAnglesRemoveOldGuide(){document.querySelectorAll('#contextGuide,.contextGuide').forEach(el=>el.remove())}
function bettingAnglesInitialize(){
  bettingAnglesRemoveOldGuide();
  const table=bettingAnglesFindBoard();
  if(!table)return;
  bettingAnglesInstallToolbar(table);
  bettingAnglesInstallSort(table);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bettingAnglesInitialize,{once:true});
else bettingAnglesInitialize();
new MutationObserver(()=>bettingAnglesInitialize()).observe(document.body,{childList:true,subtree:true});
/* OPENERS_BETTING_ANGLES_COMPACT_JS_END */
'''

def strip_block(text: str, start: str, end: str) -> str:
    return re.sub(re.escape(start) + r".*?" + re.escape(end) + r"\s*", "", text, flags=re.S)

def patch_page(path: Path, original: str) -> str:
    text = original
    for start, end in [
        (OLD_CSS_START, OLD_CSS_END),
        (OLD_JS_START, OLD_JS_END),
        (NEW_CSS_START, NEW_CSS_END),
        (NEW_JS_START, NEW_JS_END),
    ]:
        text = strip_block(text, start, end)

    if "</style>" not in text:
        raise RuntimeError(f"</style> not found in {path}")
    text = text.replace("</style>", CSS_BLOCK + "\n</style>", 1)

    final_script = text.rfind("</script>")
    if final_script < 0:
        raise RuntimeError(f"No closing </script> found in {path}")
    text = text[:final_script] + JS_BLOCK + "\n" + text[final_script:]

    text, count = re.subn(
        r'(src=["\']matchup_workspace\.js)(?:\?[^"\']*)?(["\'])',
        rf'\1?v={CACHE_VERSION}\2',
        text,
    )
    if count < 1:
        raise RuntimeError(f"matchup_workspace.js reference not found in {path}")

    for token in ["BETTING ANGLES", "bettingAnglesSortHeader", "Angles guide", "50-31 ATS", "12-5 ATS", f"v={CACHE_VERSION}"]:
        if token not in text:
            raise RuntimeError(f"Validation missing {token}: {path}")
    return text

def backup_path(path: Path, timestamp: str) -> Path:
    base = ROOT / "backups/openers_betting_angles_compact" / timestamp
    try:
        dest = base / path.relative_to(ROOT)
    except ValueError:
        dest = base / "external" / path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest

def update_daily(timestamp: str) -> bool:
    if not DAILY_SCRIPT.exists():
        return False
    command = "python3 scripts/site/install_openers_betting_angles_compact.py"
    text = DAILY_SCRIPT.read_text(encoding="utf-8", errors="ignore")
    if command in text:
        return False
    backup = backup_path(DAILY_SCRIPT, timestamp)
    shutil.copy2(DAILY_SCRIPT, backup)
    block = f"""

# Apply compact Betting Angles guide and sortable priority header.
if [ -f scripts/site/install_openers_betting_angles_compact.py ]; then
  {command}
fi
"""
    DAILY_SCRIPT.write_text(text.rstrip() + block + "\n", encoding="utf-8")
    return True

def main() -> None:
    pages = [p for p in OPENERS_FILES if p.exists()]
    if not pages:
        raise FileNotFoundError("No Openers HTML files found")
    patched = {}
    for path in pages:
        original = path.read_text(encoding="utf-8", errors="ignore")
        patched[path] = patch_page(path, original)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for path, content in patched.items():
        backup = backup_path(path, timestamp)
        shutil.copy2(path, backup)
        path.write_text(content, encoding="utf-8")
        print(f"patched: {path}")
        print(f"backup:  {backup}")
    daily = update_daily(timestamp)
    print()
    print("OPENERS BETTING ANGLES COMPACT INSTALLATION")
    print("=" * 100)
    print(f"Openers files patched: {len(pages)}")
    print(f"Daily script hook added: {daily}")
    print("Large guide removed: True")
    print("Compact guide added near board: True")
    print("Context header renamed to Betting Angles: True")
    print("Priority sorting enabled: High -> Low -> Default")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
