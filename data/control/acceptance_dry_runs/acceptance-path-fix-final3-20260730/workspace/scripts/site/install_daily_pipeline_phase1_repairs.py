#!/usr/bin/env python3
from __future__ import annotations
from datetime import datetime
from pathlib import Path
import base64
import py_compile
import re
import shutil
import subprocess
import sys

ROOT = Path.home() / "NCAAF_AUTO"
CANONICAL = ROOT / "daily_market_update.sh"
SCHEDULED = Path.home() / "Scripts/NCAAF/daily_market_update.sh"
CLEANER = ROOT / "scripts/agents/clean_daily_game_line_moves.py"
BACKUPS = ROOT / "backups/daily_pipeline_phase1"
CLEANER_B64 = "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCmZyb20gcGF0aGxpYiBpbXBvcnQgUGF0aAppbXBvcnQgbWF0aAppbXBvcnQgcmUKaW1wb3J0IHN5cwppbXBvcnQgcGFuZGFzIGFzIHBkCgpDU1YgPSBQYXRoKCdkYXRhL2FnZW50cy9kYWlseV9iZXR0aW5nX2FuZ2xlcy5jc3YnKQpBVURJVCA9IFBhdGgoJ2RhdGEvYXVkaXRzL2RhaWx5X2dhbWVfbGluZV9tb3ZlX2NsZWFuaW5nLmNzdicpCk5VTUJFUl9NT1ZFX1JFID0gcmUuY29tcGlsZShyJyg/UDxsYWJlbD5cYlNwcmVhZFxifFxiVG90YWxcYilccysoP1A8b2xkPlsrLV0/XGQrKD86XC5cZCspPylccyooPzrihpJ8LT58PT58dG8pXHMqKD9QPG5ldz5bKy1dP1xkKyg/OlwuXGQrKT8pJywgcmUuSSkKUFJJQ0VfT05MWV9SRSA9IHJlLmNvbXBpbGUocidcYig/OlNwcmVhZHxUb3RhbClcYi4qP1xiKD86UHJpY2V8T3ZlclxzK1ByaWNlfFVuZGVyXHMrUHJpY2UpXGInLCByZS5JKQoKZGVmIGNsZWFuX3RleHQodmFsdWUpOgogICAgaWYgdmFsdWUgaXMgTm9uZTogcmV0dXJuICcnCiAgICB0cnk6CiAgICAgICAgaWYgcGQuaXNuYSh2YWx1ZSk6IHJldHVybiAnJwogICAgZXhjZXB0IEV4Y2VwdGlvbjogcGFzcwogICAgdGV4dCA9IHN0cih2YWx1ZSkuc3RyaXAoKQogICAgdGV4dCA9IHJlLnN1YihyJ1xibmFuXGInLCAnJywgdGV4dCwgZmxhZ3M9cmUuSSkKICAgIHRleHQgPSByZS5zdWIocidcc3syLH0nLCAnICcsIHRleHQpCiAgICB0ZXh0ID0gcmUuc3ViKHInXHMrKFssLjs6XSknLCByJ1wxJywgdGV4dCkKICAgIHJldHVybiB0ZXh0LnN0cmlwKCcgwrd8JykKCmRlZiB2YWxpZF9nYW1lX2xpbmVfbW92ZSh0aXRsZSk6CiAgICBpZiBQUklDRV9PTkxZX1JFLnNlYXJjaCh0aXRsZSk6IHJldHVybiBGYWxzZSwgJ3ByaWNlX29ubHknCiAgICBtYXRjaCA9IE5VTUJFUl9NT1ZFX1JFLnNlYXJjaCh0aXRsZSkKICAgIGlmIG5vdCBtYXRjaDogcmV0dXJuIEZhbHNlLCAnbm9fc3ByZWFkX29yX3RvdGFsX251bWJlcl9tb3ZlJwogICAgb2xkLCBuZXcgPSBmbG9hdChtYXRjaC5ncm91cCgnb2xkJykpLCBmbG9hdChtYXRjaC5ncm91cCgnbmV3JykpCiAgICBpZiBub3QgKG1hdGguaXNmaW5pdGUob2xkKSBhbmQgbWF0aC5pc2Zpbml0ZShuZXcpKTogcmV0dXJuIEZhbHNlLCAnbm9uZmluaXRlX2xpbmUnCiAgICBpZiBhYnMobmV3LW9sZCkgPCAxZS05OiByZXR1cm4gRmFsc2UsICd1bmNoYW5nZWRfbGluZScKICAgIHJldHVybiBUcnVlLCAnYWN0dWFsX2xpbmVfbW92ZScKCmRlZiBtYWluKCk6CiAgICBpZiBub3QgQ1NWLmV4aXN0cygpOgogICAgICAgIHByaW50KGYnV0FSTklORzogbWlzc2luZyB7Q1NWfTsgbm90aGluZyB0byBjbGVhbicpOyByZXR1cm4KICAgIGRmID0gcGQucmVhZF9jc3YoQ1NWLCBsb3dfbWVtb3J5PUZhbHNlKQogICAgaWYgZGYuZW1wdHk6CiAgICAgICAgcHJpbnQoJ0RhaWx5IGJldHRpbmcgYW5nbGVzIENTViBpcyBlbXB0eTsgbm90aGluZyB0byBjbGVhbicpOyByZXR1cm4KICAgIGZvciBjb2wgaW4gWydjYXRlZ29yeScsJ3RpdGxlJywndGVhbScsJ2dyYWRlJywnc2NvcmUnLCdyZWFzb24nLCdhY3Rpb24nLCdzb3VyY2UnLCdyZXNlYXJjaF9xdWVyeSddOgogICAgICAgIGlmIGNvbCBub3QgaW4gZGYuY29sdW1uczogZGZbY29sXSA9ICcnCiAgICBmb3IgY29sIGluIFsnY2F0ZWdvcnknLCd0aXRsZScsJ3RlYW0nLCdncmFkZScsJ3JlYXNvbicsJ2FjdGlvbicsJ3NvdXJjZScsJ3Jlc2VhcmNoX3F1ZXJ5J106CiAgICAgICAgZGZbY29sXSA9IGRmW2NvbF0ubWFwKGNsZWFuX3RleHQpCiAgICBnYW1lX21hc2sgPSBkZlsnY2F0ZWdvcnknXS5zdHIuY2FzZWZvbGQoKS5lcSgnZ2FtZSBsaW5lIG1vdmUnKQogICAga2VlcCA9IHBkLlNlcmllcyhUcnVlLCBpbmRleD1kZi5pbmRleCkKICAgIGF1ZGl0X3Jvd3MgPSBbXQogICAgZm9yIGlkeCwgcm93IGluIGRmLmxvY1tnYW1lX21hc2tdLml0ZXJyb3dzKCk6CiAgICAgICAgdmFsaWQsIGF1ZGl0X3JlYXNvbiA9IHZhbGlkX2dhbWVfbGluZV9tb3ZlKGNsZWFuX3RleHQocm93Wyd0aXRsZSddKSkKICAgICAgICBrZWVwLmxvY1tpZHhdID0gdmFsaWQKICAgICAgICBhdWRpdF9yb3dzLmFwcGVuZCh7J2tlcHQnOnZhbGlkLCdhdWRpdF9yZWFzb24nOmF1ZGl0X3JlYXNvbiwnY2F0ZWdvcnknOmNsZWFuX3RleHQocm93LmdldCgnY2F0ZWdvcnknLCcnKSksJ3RpdGxlJzpjbGVhbl90ZXh0KHJvdy5nZXQoJ3RpdGxlJywnJykpLCdyZWFzb24nOmNsZWFuX3RleHQocm93LmdldCgncmVhc29uJywnJykpLCdzb3VyY2UnOmNsZWFuX3RleHQocm93LmdldCgnc291cmNlJywnJykpfSkKICAgIGNsZWFuZWQgPSBkZi5sb2Nba2VlcF0uY29weSgpCiAgICBiZWZvcmUgPSBsZW4oY2xlYW5lZCkKICAgIGNsZWFuZWRbJ19rZXknXSA9IGNsZWFuZWQuYXBwbHkobGFtYmRhIHI6IHJlLnN1YihyJ1xzKycsICcgJywgZiJ7Y2xlYW5fdGV4dChyLmdldCgndGl0bGUnLCcnKSkubG93ZXIoKX18e2NsZWFuX3RleHQoci5nZXQoJ3JlYXNvbicsJycpKS5sb3dlcigpfSIpLnN0cmlwKCksIGF4aXM9MSkKICAgIGNsZWFuZWQgPSBjbGVhbmVkLmRyb3BfZHVwbGljYXRlcygnX2tleScsIGtlZXA9J2ZpcnN0JykuZHJvcChjb2x1bW5zPVsnX2tleSddKQogICAgZHVwZXMgPSBiZWZvcmUgLSBsZW4oY2xlYW5lZCkKICAgIGNsZWFuZWRbJ3Njb3JlJ10gPSBjbGVhbmVkWydzY29yZSddLndoZXJlKGNsZWFuZWRbJ3Njb3JlJ10ubm90bmEoKSwgJycpCiAgICBBVURJVC5wYXJlbnQubWtkaXIocGFyZW50cz1UcnVlLCBleGlzdF9vaz1UcnVlKQogICAgcGQuRGF0YUZyYW1lKGF1ZGl0X3Jvd3MpLnRvX2NzdihBVURJVCwgaW5kZXg9RmFsc2UpCiAgICBjbGVhbmVkLnRvX2NzdihDU1YsIGluZGV4PUZhbHNlKQogICAgaW5pdGlhbCA9IGludChnYW1lX21hc2suc3VtKCkpCiAgICByZXRhaW5lZCA9IGludChjbGVhbmVkWydjYXRlZ29yeSddLnN0ci5jYXNlZm9sZCgpLmVxKCdnYW1lIGxpbmUgbW92ZScpLnN1bSgpKQogICAgcHJpbnQoJ0RBSUxZIEdBTUUtTElORSBNT1ZFIENMRUFOSU5HJykKICAgIHByaW50KCc9Jyo4OCkKICAgIHByaW50KGYnUm93cyBiZWZvcmU6IHtsZW4oZGYpfScpCiAgICBwcmludChmJ0dhbWUtbGluZSBtb3ZlIHJvd3MgYmVmb3JlOiB7aW5pdGlhbH0nKQogICAgcHJpbnQoZidWYWxpZCBzcHJlYWQvdG90YWwgbGluZSBtb3ZlcyByZXRhaW5lZDoge3JldGFpbmVkfScpCiAgICBwcmludChmJ1ByaWNlLW9ubHkvaW52YWxpZCBnYW1lIG1vdmVzIHJlbW92ZWQ6IHtpbml0aWFsLXJldGFpbmVkfScpCiAgICBwcmludChmJ0V4YWN0IGR1cGxpY2F0ZSByb3dzIHJlbW92ZWQ6IHtkdXBlc30nKQogICAgcHJpbnQoZidXcm90ZToge0NTVn0nKQogICAgcHJpbnQoZidBdWRpdDoge0FVRElUfScpCgppZiBfX25hbWVfXyA9PSAnX19tYWluX18nOgogICAgdHJ5OiBtYWluKCkKICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZXhjOgogICAgICAgIHByaW50KGYnRVJST1I6IHtleGN9JywgZmlsZT1zeXMuc3RkZXJyKTsgcmFpc2UK"

PUBLISH_BLOCK = r'''  # AUTO_GITHUB_PUBLISH_START
  PUBLISH_REPO="$HOME/Sites/NCAAF_SITE"
  if [ -d "$PUBLISH_REPO/.git" ]; then
    echo "Running GitHub publish sanity check..."
    if python3 scripts/publish/check_index_before_publish.py; then
      echo "Copying refreshed site assets to GitHub Pages repo..."
      cp index.html "$PUBLISH_REPO/index.html"
      [ -f matchup.html ] && cp matchup.html "$PUBLISH_REPO/matchup.html"
      if [ -f openers_v2.html ]; then
        cp openers_v2.html "$PUBLISH_REPO/openers.html"
      elif [ -f build/public_site/openers.html ]; then
        cp build/public_site/openers.html "$PUBLISH_REPO/openers.html"
      fi
      [ -f matchup_workspace.js ] && cp matchup_workspace.js "$PUBLISH_REPO/matchup_workspace.js"
      if [ -f odds.html ]; then
        cp odds.html "$PUBLISH_REPO/odds.html"
      elif [ -f build/public_site/odds.html ]; then
        cp build/public_site/odds.html "$PUBLISH_REPO/odds.html"
      fi
      if [ -d data/site ]; then
        mkdir -p "$PUBLISH_REPO/data/site"
        rsync -a --delete data/site/ "$PUBLISH_REPO/data/site/"
      fi
      if [ -d logos ]; then
        mkdir -p "$PUBLISH_REPO/logos"
        rsync -a logos/ "$PUBLISH_REPO/logos/"
      fi
      cd "$PUBLISH_REPO"
      git status --short
      git add index.html
      [ -f matchup.html ] && git add matchup.html
      [ -f openers.html ] && git add openers.html
      [ -f matchup_workspace.js ] && git add matchup_workspace.js
      [ -f odds.html ] && git add odds.html
      [ -d data/site ] && git add -A data/site
      [ -d logos ] && git add -A logos
      if git diff --cached --quiet; then
        echo "No GitHub Pages changes to commit"
      else
        git commit -m "Daily NCAAF site update $(date +%Y-%m-%d)"
        git push
        echo "GitHub Pages publish completed"
      fi
      cd "$HOME/NCAAF_AUTO"
    else
      echo "WARNING: publish sanity check failed; skipping GitHub publish"
    fi
  else
    echo "WARNING: GitHub publish repo not found at $PUBLISH_REPO"
  fi
  # AUTO_GITHUB_PUBLISH_END'''


def backup(path: Path, stamp: str) -> Path:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = Path("external") / path.name
    dst = BACKUPS / stamp / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)
    return dst


def remove_lines(text: str, fragments: list[str]) -> str:
    lines = [
        line for line in text.splitlines()
        if not any(fragment in line for fragment in fragments)
    ]
    return "\n".join(lines) + "\n"


def patch(text: str) -> str:
    text = remove_lines(
        text,
        [
            'run_py "scripts/odds/append_game_line_history.py"',
            'run_py "scripts/odds/build_game_line_movement_report.py"',
        ],
    )

    site_anchor = '  echo "Using ~/NCAAF_AUTO/index.html as automation baseline template. No iCloud copy is performed."'
    history_block = '''  # Append today's normalized game lines before site/email rendering.
  run_py "scripts/odds/append_game_line_history.py" "append_game_line_history.py" || echo "WARNING: game line history append failed"
  run_py "scripts/odds/build_game_line_movement_report.py" "build_game_line_movement_report.py" || echo "WARNING: game line movement report build failed"

'''
    if site_anchor not in text:
        raise RuntimeError("site-build insertion anchor not found")
    text = text.replace(site_anchor, history_block + site_anchor, 1)

    text = remove_lines(
        text,
        [
            'run_py "scripts/agents/build_daily_betting_angles_html.py"',
            'run_py "scripts/agents/prepend_game_line_moves_to_daily_betting_angles.py"',
            'run_py "scripts/agents/prepend_injury_alerts_to_daily_betting_angles.py"',
            'run_py "scripts/agents/clean_daily_game_line_moves.py"',
        ],
    )

    email_anchor = "  mkdir -p backups/html"
    email_block = '''  # Add supplemental rows, remove juice-only game moves, then render HTML.
  run_py "scripts/agents/prepend_game_line_moves_to_daily_betting_angles.py" "prepend_game_line_moves_to_daily_betting_angles.py" || echo "WARNING: prepend game line moves to email failed"
  run_py "scripts/agents/prepend_injury_alerts_to_daily_betting_angles.py" "prepend_injury_alerts_to_daily_betting_angles.py" || echo "WARNING: prepend injury alerts failed"
  run_py "scripts/agents/clean_daily_game_line_moves.py" "clean_daily_game_line_moves.py" || echo "WARNING: daily game-line move cleaning failed"
  run_py "scripts/agents/build_daily_betting_angles_html.py" "build_daily_betting_angles_html.py"

'''
    if email_anchor not in text:
        raise RuntimeError("email-build insertion anchor not found")
    text = text.replace(email_anchor, email_block + email_anchor, 1)

    publish_pattern = re.compile(
        r"(?ms)^  # AUTO_GITHUB_PUBLISH_START.*?^  # AUTO_GITHUB_PUBLISH_END"
    )
    if publish_pattern.search(text):
        text = publish_pattern.sub(PUBLISH_BLOCK, text, count=1)
    else:
        finish_anchor = '  echo "Daily market update finished: $(date)"'
        if finish_anchor not in text:
            raise RuntimeError("publish insertion anchor not found")
        text = text.replace(
            finish_anchor,
            PUBLISH_BLOCK + "\n\n" + finish_anchor,
            1,
        )

    return re.sub(r"(?m)^run_py ", "  run_py ", text)


def validate_shell(path: Path) -> None:
    result = subprocess.run(
        ["/bin/bash", "-n", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"shell syntax failed for {path}: {result.stderr.strip()}"
        )


def main() -> None:
    if not CANONICAL.exists():
        raise FileNotFoundError(CANONICAL)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    CLEANER.parent.mkdir(parents=True, exist_ok=True)
    if CLEANER.exists():
        print(f"backup:  {backup(CLEANER, stamp)}")
    CLEANER.write_bytes(base64.b64decode(CLEANER_B64))
    CLEANER.chmod(0o755)
    py_compile.compile(str(CLEANER), doraise=True)
    print(f"installed: {CLEANER}")

    original = CANONICAL.read_text(encoding="utf-8", errors="ignore")
    updated = patch(original)
    print(f"backup:  {backup(CANONICAL, stamp)}")
    CANONICAL.write_text(updated, encoding="utf-8")
    CANONICAL.chmod(0o755)
    print(f"patched: {CANONICAL}")

    SCHEDULED.parent.mkdir(parents=True, exist_ok=True)
    if SCHEDULED.exists():
        print(f"backup:  {backup(SCHEDULED, stamp)}")
    SCHEDULED.write_text(
        '#!/bin/bash\nset -e\nexec /bin/bash "$HOME/NCAAF_AUTO/daily_market_update.sh"\n',
        encoding="utf-8",
    )
    SCHEDULED.chmod(0o755)
    print(f"installed wrapper: {SCHEDULED}")

    validate_shell(CANONICAL)
    validate_shell(SCHEDULED)

    current = CANONICAL.read_text(encoding="utf-8")
    history_pos = current.find("append_game_line_history.py")
    site_pos = current.find("build_site_from_workbook_safe_with_movement.py")
    cleaner_pos = current.find("clean_daily_game_line_moves.py")
    html_pos = current.find("build_daily_betting_angles_html.py")

    if not (0 <= history_pos < site_pos):
        raise RuntimeError("history ordering check failed")
    if not (0 <= cleaner_pos < html_pos):
        raise RuntimeError("email ordering check failed")

    for token in [
        "git push",
        "cp matchup.html",
        "cp openers_v2.html",
        "git add -A data/site",
    ]:
        if token not in current:
            raise RuntimeError(f"publish token missing: {token}")

    print()
    print("NCAAF DAILY PIPELINE PHASE 1 INSTALLATION")
    print("=" * 100)
    print("LaunchAgent wrapper points to canonical pipeline: True")
    print("Game-line history runs before site build: True")
    print("Juice-only spread/total email moves filtered: True")
    print("Email HTML renders after move cleaning: True")
    print("Full static-site GitHub publishing installed: True")
    print("Python and shell syntax validation passed: True")
    print("No network pulls, emails, commits, or pushes were run by this installer.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
