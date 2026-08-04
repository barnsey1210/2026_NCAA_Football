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

JS_START = "/* OPENERS_BETTING_ANGLES_HEADER_START */"
JS_END = "/* OPENERS_BETTING_ANGLES_HEADER_END */"

JS_BLOCK = r'''
/* OPENERS_BETTING_ANGLES_HEADER_START */
function renameOpenersContextHeader(){
  const tables=[...document.querySelectorAll('table')];

  for(const table of tables){
    const header=[...table.querySelectorAll('thead th')].find(
      th=>th.textContent.trim().toUpperCase()==='CONTEXT'
    );

    if(header){
      header.textContent='BETTING ANGLES';
      header.title='Highest-priority non-model betting angles';
      header.style.cursor='default';
      return true;
    }
  }

  return false;
}

if(document.readyState==='loading'){
  document.addEventListener(
    'DOMContentLoaded',
    renameOpenersContextHeader,
    {once:true}
  );
}else{
  renameOpenersContextHeader();
}

const bettingAnglesHeaderObserver=new MutationObserver(()=>{
  if(renameOpenersContextHeader()){
    bettingAnglesHeaderObserver.disconnect();
  }
});

bettingAnglesHeaderObserver.observe(document.body,{
  childList:true,
  subtree:true
});
/* OPENERS_BETTING_ANGLES_HEADER_END */
'''

def strip_block(text: str) -> str:
    return re.sub(
        re.escape(JS_START) + r".*?" + re.escape(JS_END) + r"\s*",
        "",
        text,
        flags=re.S,
    )

def patch_page(path: Path, original: str) -> str:
    text = strip_block(original)
    closing_script = text.rfind("</script>")
    if closing_script < 0:
        raise RuntimeError(f"No closing </script> found in {path}")
    text = text[:closing_script] + JS_BLOCK + "\n" + text[closing_script:]

    required = [
        JS_START,
        "renameOpenersContextHeader",
        "BETTING ANGLES",
        "MutationObserver",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        raise RuntimeError(f"Validation failed for {path}: {missing}")

    return text

def backup_path(path: Path, timestamp: str) -> Path:
    base = ROOT / "backups/openers_betting_angles_header" / timestamp
    try:
        destination = base / path.relative_to(ROOT)
    except ValueError:
        destination = base / "external" / path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination

def update_daily_script(timestamp: str) -> bool:
    if not DAILY_SCRIPT.exists():
        return False

    command = "python3 scripts/site/install_openers_betting_angles_header.py"
    text = DAILY_SCRIPT.read_text(encoding="utf-8", errors="ignore")

    if command in text:
        return False

    backup = backup_path(DAILY_SCRIPT, timestamp)
    shutil.copy2(DAILY_SCRIPT, backup)

    block = f"""

# Rename the Openers Context header to Betting Angles.
if [ -f scripts/site/install_openers_betting_angles_header.py ]; then
  {command}
fi
"""

    DAILY_SCRIPT.write_text(
        text.rstrip() + block + "\n",
        encoding="utf-8",
    )
    return True

def main() -> None:
    pages = [path for path in OPENERS_FILES if path.exists()]
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

    daily_updated = update_daily_script(timestamp)

    print()
    print("OPENERS BETTING ANGLES HEADER INSTALLATION")
    print("=" * 100)
    print(f"Openers files patched: {len(pages)}")
    print(f"Daily script hook added: {daily_updated}")
    print("Header renamed to Betting Angles: True")
    print("Sorting added: False")
    print("Board loading/filtering logic changed: False")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
