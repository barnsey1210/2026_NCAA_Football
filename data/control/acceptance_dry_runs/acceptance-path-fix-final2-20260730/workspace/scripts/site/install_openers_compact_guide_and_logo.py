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

LOGO_DIRS = [
    ROOT / "logos",
    ROOT / "build/public_site/logos",
    Path.home() / "Sites/NCAAF_SITE/logos",
]

DAILY_SCRIPT = ROOT / "daily_market_update.sh"

CSS_START = "/* OPENERS_COMPACT_ANGLES_GUIDE_CSS_START */"
CSS_END = "/* OPENERS_COMPACT_ANGLES_GUIDE_CSS_END */"
JS_START = "/* OPENERS_COMPACT_ANGLES_GUIDE_JS_START */"
JS_END = "/* OPENERS_COMPACT_ANGLES_GUIDE_JS_END */"

CACHE_VERSION = "20260728-compactguide-safe6"

CSS_BLOCK = r'''
/* OPENERS_COMPACT_ANGLES_GUIDE_CSS_START */
.contextGuide{
  position:relative;
  width:max-content;
  max-width:100%;
  margin:5px 0 7px auto;
  overflow:visible;
  border:1px solid #315f89;
  border-radius:999px;
  background:#0c203b;
}
.contextGuide summary{
  min-width:0;
  padding:6px 10px;
  gap:7px;
  font-size:10px;
  white-space:nowrap;
}
.contextGuide summary > span:first-child{font-size:10px}
.contextGuide summary > .contextGuideIntro{display:none}
.contextGuide summary::after{
  width:18px;
  height:18px;
  font-size:13px;
}
.contextGuideBody{
  position:absolute;
  z-index:80;
  right:0;
  top:calc(100% + 6px);
  width:min(700px,88vw);
  padding:9px;
  border:1px solid #315f89;
  border-radius:10px;
  background:#08172c;
  box-shadow:0 14px 34px rgba(0,0,0,.38);
}
.contextGuideGrid{gap:7px}
.contextGuideCard{padding:8px;border-radius:8px}
.contextGuideHead{margin-bottom:5px;font-size:10px}
.contextGuideCard ul{padding-left:15px;font-size:9px;line-height:1.35}
.contextGuideNote{margin-top:7px;font-size:9px}
@media(max-width:800px){
  .contextGuide{margin-left:0}
  .contextGuideBody{
    position:fixed;
    left:10px;
    right:10px;
    top:90px;
    width:auto;
  }
  .contextGuideGrid{grid-template-columns:1fr}
}
/* OPENERS_COMPACT_ANGLES_GUIDE_CSS_END */
'''

JS_BLOCK = r'''
/* OPENERS_COMPACT_ANGLES_GUIDE_JS_START */
function compactAnglesGuideInstall(){
  const guide=document.querySelector('.contextGuide');
  if(guide){
    guide.removeAttribute('open');
    const title=guide.querySelector('summary > span:first-child');
    if(title)title.textContent='Angles guide';
  }

  const tables=[...document.querySelectorAll('table')];
  for(const table of tables){
    const headers=[...table.querySelectorAll('thead th')];
    const contextHeader=headers.find(
      th=>th.textContent.trim().toUpperCase()==='CONTEXT'
    );
    if(contextHeader){
      contextHeader.textContent='BETTING ANGLES';
      contextHeader.title='Highest-priority non-model betting context';
      break;
    }
  }
}

if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',compactAnglesGuideInstall,{once:true});
}else{
  compactAnglesGuideInstall();
}
/* OPENERS_COMPACT_ANGLES_GUIDE_JS_END */
'''

def strip_block(text: str, start: str, end: str) -> str:
    return re.sub(
        re.escape(start) + r".*?" + re.escape(end) + r"\s*",
        "",
        text,
        flags=re.S,
    )

def normalized_stem(path: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "", path.stem.lower())

def texas_am_score(path: Path) -> int:
    stem = normalized_stem(path)
    name = path.name.lower()
    score = 0

    exact = {
        "texasam": 100,
        "texasamaggies": 98,
        "texasaandm": 96,
        "texasaggies": 90,
        "tamu": 88,
    }

    if stem in exact:
        score += exact[stem]
    if "texas" in stem:
        score += 25
    if "aggie" in stem:
        score += 25
    if "am" in stem:
        score += 15
    if "a-m" in name or "a_m" in name or "a&m" in name:
        score += 20
    if path.suffix.lower() == ".png":
        score += 10

    for negative in [
        "state",
        "tech",
        "longhorn",
        "utep",
        "utsa",
        "northtexas",
        "texassouthern",
    ]:
        if negative in stem:
            score -= 80

    return score

def find_texas_am_logo() -> Path:
    candidates = []

    for logo_dir in LOGO_DIRS:
        if not logo_dir.exists():
            continue

        for path in logo_dir.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue

            score = texas_am_score(path)
            if score > 0:
                candidates.append((score, path))

    if not candidates:
        raise FileNotFoundError(
            "No likely Texas A&M logo was found in:\n"
            + "\n".join(str(path) for path in LOGO_DIRS)
        )

    candidates.sort(key=lambda item: (item[0], item[1].name), reverse=True)
    best_score, best_path = candidates[0]

    if best_score < 50:
        details = "\n".join(
            f"{score:>3}  {path}"
            for score, path in candidates[:20]
        )
        raise RuntimeError(
            "Texas A&M logo match was too uncertain.\n"
            f"Candidates:\n{details}"
        )

    return best_path

def patch_openers(path: Path, original: str) -> str:
    text = strip_block(original, CSS_START, CSS_END)
    text = strip_block(text, JS_START, JS_END)

    if "</style>" not in text:
        raise RuntimeError(f"</style> not found in {path}")

    text = text.replace(
        "</style>",
        CSS_BLOCK + "\n</style>",
        1,
    )

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
        raise RuntimeError(
            f"matchup_workspace.js reference not found in {path}"
        )

    required = [
        "compactAnglesGuideInstall",
        "BETTING ANGLES",
        "Angles guide",
        CSS_START,
        JS_START,
        f"v={CACHE_VERSION}",
    ]

    missing = [token for token in required if token not in text]
    if missing:
        raise RuntimeError(
            f"Post-patch validation failed for {path}: {missing}"
        )

    return text

def backup_path(path: Path, timestamp: str) -> Path:
    base = ROOT / "backups/openers_compact_guide_safe" / timestamp

    try:
        relative = path.relative_to(ROOT)
        destination = base / relative
    except ValueError:
        destination = base / "external" / path.name

    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination

def install_logo(source_logo: Path, timestamp: str):
    installed = []

    for logo_dir in LOGO_DIRS:
        if not logo_dir.parent.exists():
            continue

        logo_dir.mkdir(parents=True, exist_ok=True)
        destination = logo_dir / "texas-am.png"

        if destination.exists():
            backup = backup_path(destination, timestamp)
            shutil.copy2(destination, backup)

        if source_logo.resolve() != destination.resolve():
            shutil.copy2(source_logo, destination)

        installed.append(destination)

    return installed

def update_daily_script(timestamp: str) -> bool:
    if not DAILY_SCRIPT.exists():
        return False

    command = (
        "python3 scripts/site/"
        "install_openers_compact_guide_and_logo.py"
    )
    text = DAILY_SCRIPT.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    if command in text:
        return False

    backup = backup_path(DAILY_SCRIPT, timestamp)
    shutil.copy2(DAILY_SCRIPT, backup)

    block = f"""

# Keep the Openers guide compact and install the Texas A&M logo alias.
if [ -f scripts/site/install_openers_compact_guide_and_logo.py ]; then
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

    texas_logo = find_texas_am_logo()

    patched = {}

    for path in pages:
        original = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
        patched[path] = patch_openers(path, original)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for path, content in patched.items():
        backup = backup_path(path, timestamp)
        shutil.copy2(path, backup)
        path.write_text(content, encoding="utf-8")
        print(f"patched: {path}")
        print(f"backup:  {backup}")

    installed_logos = install_logo(texas_logo, timestamp)
    daily_updated = update_daily_script(timestamp)

    print()
    print("OPENERS COMPACT GUIDE + LOGO INSTALLATION")
    print("=" * 100)
    print(f"Openers files patched: {len(pages)}")
    print(f"Texas A&M source logo: {texas_logo}")
    print(f"Texas A&M logo aliases installed: {len(installed_logos)}")
    for path in installed_logos:
        print(f"  {path}")
    print(f"Daily script hook added: {daily_updated}")
    print("Guide changed to compact floating panel: True")
    print("Context header renamed to Betting Angles: True")
    print("Board sorting/loading code changed: False")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
