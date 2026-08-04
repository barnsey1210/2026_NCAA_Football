#!/usr/bin/env python3
from pathlib import Path
import re

FILES = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

STYLE = '''
<style id="sidebar-last-updated-style">
  .last-updated-sub {
    margin-top: 8px;
    color: #94a3b8;
    font-size: 12px;
    font-weight: 700;
    line-height: 1.25;
  }
  .last-updated-sub strong {
    color: #dbeafe;
    font-weight: 800;
  }
</style>
'''

SCRIPT = '''
<script id="sidebar-last-updated-script">
(function(){
  function esc(s){
    return String(s).replace(/[<>&"]/g, function(c){
      return {"<":"&lt;",">":"&gt;","&":"&amp;",'"':"&quot;"}[c];
    });
  }
  function run(){
    try {
      var dbEl = document.getElementById("db");
      if (!dbEl) return;
      var db = JSON.parse(dbEl.textContent || "{}");
      var label = db.meta && (db.meta.last_updated_et || db.meta.generated_at || db.meta.updated_at);
      var el = document.getElementById("last-updated-sub");
      if (el && label) {
        el.innerHTML = 'Last updated<br><strong>' + esc(label) + '</strong>';
      }
    } catch(e) {}
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
</script>
'''

for p in FILES:
    if not p.exists():
        continue

    txt = p.read_text(errors="ignore")

    # Remove old sidebar prototype text.
    txt = re.sub(
        r'\s*<div class="sub">\s*Workbook-powered prototype\s*</div>',
        '',
        txt,
        flags=re.I
    )
    txt = re.sub(r'Workbook-powered prototype', '', txt, flags=re.I)

    # Remove Season Schedule subtitle blocks.
    txt = re.sub(
        r'\s*<div class="page-sub">\s*Schedule and projections remain workbook-driven\..*?</div>',
        '',
        txt,
        flags=re.S | re.I
    )

    # Remove escaped JS-template version if present.
    txt = re.sub(
        r'\s*<div class=\\"page-sub\\">\s*Schedule and projections remain workbook-driven\..*?</div>',
        '',
        txt,
        flags=re.S | re.I
    )

    # Add Last Updated placeholder after brand.
    if 'id="last-updated-sub"' not in txt:
        txt = txt.replace(
            '<div class="brand">2026 NCAA<br/>Football</div>',
            '<div class="brand">2026 NCAA<br/>Football</div>\n<div id="last-updated-sub" class="last-updated-sub"></div>',
            1
        )

    # Add CSS/script once.
    if 'id="sidebar-last-updated-style"' not in txt:
        txt = txt.replace("</head>", STYLE + "\n</head>", 1)

    if 'id="sidebar-last-updated-script"' not in txt:
        txt = txt.replace("</body>", SCRIPT + "\n</body>", 1)

    p.write_text(txt)
    print(f"Cleaned {p}")
