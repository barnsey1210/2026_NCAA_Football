#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- polish-home-command-center-week-tabs-start -->"
END = "<!-- polish-home-command-center-week-tabs-end -->"

BLOCK = r'''
<!-- polish-home-command-center-week-tabs-start -->
<style id="polish-home-command-center-week-tabs-css">
.home-week-tabs{
  display:flex;
  gap:7px;
  overflow-x:auto;
  margin:0 0 16px;
  padding:4px 0 8px;
  scrollbar-width:none;
}
.home-week-tabs::-webkit-scrollbar{display:none}
.home-week-tabs button{
  flex:0 0 auto;
  border:1px solid rgba(96,165,250,.28);
  border-radius:999px;
  padding:8px 12px;
  background:rgba(15,23,42,.55);
  color:#cbd5e1;
  font-weight:950;
  cursor:pointer;
}
.home-week-tabs button.active,
.home-week-tabs button:hover{
  background:rgba(37,99,235,.78);
  color:#fff;
  border-color:rgba(147,197,253,.70);
}
</style>
<!-- polish-home-command-center-week-tabs-end -->
'''

for path in TARGETS:
    if not path.exists():
        continue
    s = path.read_text(errors="ignore")
    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: BLOCK, s, flags=re.S)
    else:
        s = s.replace("</body>", BLOCK + "\n</body>")
    path.write_text(s, encoding="utf-8")
    print(path, "injected home week tabs polish")
