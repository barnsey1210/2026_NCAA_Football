#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- fix-home-command-center-table-expansion-start -->"
END = "<!-- fix-home-command-center-table-expansion-end -->"

BLOCK = r'''
<!-- fix-home-command-center-table-expansion-start -->
<style id="fix-home-command-center-table-expansion-css">
.home-cmd-table .home-cmd-extra-row{
  display:none!important;
}

.home-cmd-card.expanded .home-cmd-table .home-cmd-extra-row{
  display:table-row!important;
}

.home-cmd-table-card{
  overflow:hidden!important;
}

.home-cmd-table{
  table-layout:fixed!important;
}

.home-cmd-table th:nth-child(1),
.home-cmd-table td:nth-child(1){
  width:39%!important;
}

.home-cmd-table th:nth-child(2),
.home-cmd-table td:nth-child(2){
  width:29%!important;
}

.home-cmd-table th:nth-child(3),
.home-cmd-table td:nth-child(3){
  width:32%!important;
}

.home-cmd-table th,
.home-cmd-table td{
  box-sizing:border-box!important;
}

.hc-team-line{
  gap:7px!important;
  font-size:16px!important;
  line-height:1.06!important;
}

.hc-team-line span{
  font-size:16px!important;
  line-height:1.06!important;
}

.hc-team-line em{
  font-size:12px!important;
  min-width:34px!important;
  text-align:right!important;
}

.hc-bet-cell{
  font-size:15px!important;
  line-height:1.12!important;
  white-space:normal!important;
}

.hc-note-cell{
  font-size:12.5px!important;
  line-height:1.18!important;
}

.hc-rank-cell{
  white-space:normal!important;
  font-size:14px!important;
  line-height:1.15!important;
}

.home-cmd-table .team-logo-wrap{
  margin-right:0!important;
}

@media(max-width:900px){
  .home-cmd-card.expanded .home-cmd-table .home-cmd-extra-row{
    display:block!important;
  }
}
</style>
<!-- fix-home-command-center-table-expansion-end -->
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
    print(path, "fixed command center table expansion")
