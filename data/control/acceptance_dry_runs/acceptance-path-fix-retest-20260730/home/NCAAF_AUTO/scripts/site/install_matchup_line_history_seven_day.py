#!/usr/bin/env python3
"""Install seven-day daily matchup line history with opener timestamps."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import py_compile
import re
import shutil
import subprocess
import sys

ROOT = Path.home() / "NCAAF_AUTO"
INJECTOR = ROOT / "scripts/site/inject_matchup_line_history.py"
WORKSPACE_FILES = [
    ROOT / "matchup_workspace.js",
    ROOT / "build/public_site/matchup_workspace.js",
    Path.home() / "Sites/NCAAF_SITE/matchup_workspace.js",
]
BACKUP_ROOT = ROOT / "backups/matchup_line_history_seven_day"

OLD_INJECTOR_LINE = '''                "snapshot_date": clean_str(r.get("snapshot_date")),
                "snapshot_label": clean_str(r.get("snapshot_label")),'''

NEW_INJECTOR_LINE = '''                "snapshot_date": clean_str(r.get("snapshot_date")),
                "snapshot_ts": clean_str(r.get("snapshot_ts") or r.get("snapshot_date")),
                "snapshot_label": clean_str(r.get("snapshot_label")),'''

NEW_MARKET_CARDS = r'''  function marketCards(game, history){
    const allRows=[...(history[game.game.game_id]||[])].sort((a,b)=>{
      const ak=String(a.snapshot_ts||a.snapshot_date||a.market_spread_last_update||a.market_total_last_update||'');
      const bk=String(b.snapshot_ts||b.snapshot_date||b.market_spread_last_update||b.market_total_last_update||'');
      return ak.localeCompare(bk);
    });

    const byDate=new Map();
    for(const row of allRows){
      const rawDate=String(row.snapshot_date||row.snapshot_ts||row.market_spread_last_update||row.market_total_last_update||'');
      const dateKey=rawDate.slice(0,10)||rawDate;
      if(!dateKey)continue;
      byDate.set(dateKey,row);
    }

    const daily=[...byDate.entries()]
      .sort((a,b)=>String(a[0]).localeCompare(String(b[0])))
      .map(([,row])=>row);

    const firstSpread=daily.find(x=>finite(x.market_spread_home))||{};
    const firstTotal=daily.find(x=>finite(x.market_total))||{};
    const latest=[...daily].reverse().slice(0,7);

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
          <thead><tr><th>Date / Time</th><th>Book</th><th>ATS spread</th><th>Spread price</th><th>Spread move</th><th>O/U total</th><th>Over</th><th>Under</th><th>Total move</th><th>Source</th></tr></thead>
          <tbody>${latest.map((x,i)=>{
            const older=latest[i+1]||{};
            const displayDate=String(x.snapshot_date||x.snapshot_ts||x.market_spread_last_update||x.market_total_last_update||'—').slice(0,10);
            return `<tr><td>${esc(displayDate)}</td><td>${bookLogo(x.market_spread_book||x.market_total_book)||esc(x.market_spread_book||x.market_total_book||'—')}</td><td>${line(x.market_spread_home)}</td><td>${price(x.market_spread_price)}</td><td>${movementText(x.market_spread_home,older.market_spread_home)}</td><td>${num(x.market_total)}</td><td>${price(x.market_total_over_price)}</td><td>${price(x.market_total_under_price)}</td><td>${movementText(x.market_total,older.market_total)}</td><td>${esc(x.snapshot_label||x.source||'Snapshot')}</td></tr>`;
          }).join('')||'<tr><td colspan="10" class="mwMuted">No line-history snapshots available.</td></tr>'}</tbody>
        </table>
      </div>
    </section>`;
  }
'''


def backup(path: Path, timestamp: str) -> Path:
    base = BACKUP_ROOT / timestamp
    try:
        destination = base / path.relative_to(ROOT)
    except ValueError:
        destination = base / "external" / path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    return destination


def replace_market_cards(text: str, path: Path) -> str:
    pattern = re.compile(r"(?ms)^  function marketCards\(game, history\)\{.*?^  function injuries\(game\)\{")
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"Could not locate marketCards() in {path}")
    replacement = NEW_MARKET_CARDS.rstrip() + "\n  function injuries(game){"
    updated = text[:match.start()] + replacement + text[match.end():]
    if "slice(0,7)" not in updated or "Captured:" not in updated:
        raise RuntimeError(f"Validation failed after patching {path}")
    return updated


def run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, check=False)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}")


def copy_if_exists(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print(f"copied:  {source} -> {destination}")


def main() -> None:
    if not INJECTOR.exists():
        raise FileNotFoundError(INJECTOR)

    existing_workspaces = [path for path in WORKSPACE_FILES if path.exists()]
    if not existing_workspaces:
        raise FileNotFoundError("No matchup_workspace.js files found")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    injector_text = INJECTOR.read_text(encoding="utf-8", errors="ignore")
    if NEW_INJECTOR_LINE in injector_text:
        updated_injector = injector_text
    elif OLD_INJECTOR_LINE in injector_text:
        updated_injector = injector_text.replace(OLD_INJECTOR_LINE, NEW_INJECTOR_LINE, 1)
    else:
        raise RuntimeError("Could not locate injector snapshot_date output block")

    patched_workspaces = {}
    for path in existing_workspaces:
        original = path.read_text(encoding="utf-8", errors="ignore")
        patched_workspaces[path] = replace_market_cards(original, path)

    injector_backup = backup(INJECTOR, timestamp)
    INJECTOR.write_text(updated_injector, encoding="utf-8")
    py_compile.compile(str(INJECTOR), doraise=True)
    print(f"patched: {INJECTOR}")
    print(f"backup:  {injector_backup}")

    for path, content in patched_workspaces.items():
        path_backup = backup(path, timestamp)
        path.write_text(content, encoding="utf-8")
        print(f"patched: {path}")
        print(f"backup:  {path_backup}")

    run(["python3", "scripts/history/build_matchup_line_history_clean.py"], ROOT)
    run(["python3", "scripts/site/inject_matchup_line_history.py"], ROOT)
    run(["python3", "scripts/site/build_matchups_view.py"], ROOT)

    for name in ["matchup_line_history.json", "matchups_view.json"]:
        source = ROOT / "data/site" / name
        copy_if_exists(source, ROOT / "build/public_site/data/site" / name)
        copy_if_exists(source, Path.home() / "Sites/NCAAF_SITE/data/site" / name)

    copy_if_exists(ROOT / "matchup.html", ROOT / "build/public_site/matchup.html")
    copy_if_exists(ROOT / "matchup.html", Path.home() / "Sites/NCAAF_SITE/matchup.html")

    print()
    print("SEVEN-DAY MATCHUP LINE-HISTORY INSTALLATION")
    print("=" * 100)
    print("One row per distinct snapshot date: True")
    print("Most recent daily rows displayed: 7")
    print("Unchanged daily snapshots preserved: True")
    print("Opening ATS capture timestamp added: True")
    print("Opening O/U capture timestamp added: True")
    print("snapshot_ts added to line-history JSON asset: True")
    print("Local line-history assets rebuilt: True")
    print("GitHub working copy updated locally: True")
    print("No commit or push performed: True")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
