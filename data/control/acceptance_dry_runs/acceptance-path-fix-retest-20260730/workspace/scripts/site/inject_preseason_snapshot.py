#!/usr/bin/env python3
from pathlib import Path
import json, re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]
SNAPSHOT = Path("data/snapshots/preseason/preseason_db.json")

START = "<!-- preseason-snapshot-data-start -->"
END = "<!-- preseason-snapshot-data-end -->"

def main():
    if not SNAPSHOT.exists():
        raise SystemExit(f"missing {SNAPSHOT}; run create_preseason_snapshot.py first")

    source = json.loads(SNAPSHOT.read_text(errors="ignore"))
    # The site helpers only read team and conference preseason values. Keeping
    # all 902 preseason games in every page added ~1.15 MB without a consumer.
    data = {key: source.get(key) for key in ("meta", "teams", "conferences")}
    payload = json.dumps(data, separators=(",", ":"))

    block = f'''
{START}
<script id="preseason-snapshot-data" type="application/json">{payload}</script>
<script id="preseason-snapshot-helper-js">
(function(){{
  if (window.__preseasonSnapshotInstalled) return;
  window.__preseasonSnapshotInstalled = true;

  function readPreseasonSnapshot(){{
    const el = document.getElementById('preseason-snapshot-data');
    if (!el) return null;
    try {{ return JSON.parse(el.textContent || '{{}}'); }} catch(e) {{ return null; }}
  }}

  window.PRESEASON_SNAPSHOT = readPreseasonSnapshot();

  window.preseasonTeam = function(teamName){{
    const snap = window.PRESEASON_SNAPSHOT;
    if (!snap || !Array.isArray(snap.teams)) return null;
    return snap.teams.find(t => String(t.team) === String(teamName)) || null;
  }};

  window.preseasonConferenceTeam = function(conf, teamName){{
    const snap = window.PRESEASON_SNAPSHOT;
    if (!snap || !Array.isArray(snap.conferences)) return null;
    const c = snap.conferences.find(x => String(x.conference) === String(conf));
    if (!c || !Array.isArray(c.teams)) return null;
    return c.teams.find(t => String(t.team) === String(teamName)) || null;
  }};
}})();
</script>
{END}
'''

    for path in TARGETS:
        if not path.exists():
            continue

        s = path.read_text(errors="ignore")

        if START in s and END in s:
            s = re.sub(re.escape(START) + r".*?" + re.escape(END), block, s, flags=re.S)
        else:
            s = s.replace("</body>", block + "\n</body>")

        path.write_text(s, encoding="utf-8")
        print(path, "injected preseason snapshot")

if __name__ == "__main__":
    main()
