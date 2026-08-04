#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- fix-home-command-center-value-layout-start -->"
END = "<!-- fix-home-command-center-value-layout-end -->"

BLOCK = r'''
<!-- fix-home-command-center-value-layout-start -->
<style id="fix-home-command-center-value-layout-css">
.home-cmd-row{
  grid-template-columns:auto minmax(0,1fr)!important;
  align-items:center!important;
  overflow:hidden!important;
}

.home-cmd-row-main{
  min-width:0!important;
}

.home-cmd-row-topline{
  display:flex!important;
  align-items:center!important;
  justify-content:space-between!important;
  gap:12px!important;
  min-width:0!important;
}

.home-cmd-row-label{
  min-width:0!important;
  max-width:none!important;
  white-space:normal!important;
  overflow:visible!important;
  text-overflow:clip!important;
}

.home-cmd-row-value{
  display:inline-flex!important;
  align-items:center!important;
  justify-content:center!important;
  flex:0 0 auto!important;
  max-width:260px!important;
  white-space:nowrap!important;
  overflow:visible!important;
  overflow-wrap:normal!important;
  word-break:normal!important;
  text-align:right!important;
  line-height:1.05!important;
  font-size:17px!important;
  font-weight:950!important;
}

.home-cmd-row-note{
  max-width:none!important;
  white-space:normal!important;
  overflow:visible!important;
  text-overflow:clip!important;
}

@media(max-width:800px){
  .home-cmd-row-topline{
    display:block!important;
  }
  .home-cmd-row-value{
    margin-top:5px!important;
    justify-content:flex-start!important;
    text-align:left!important;
  }
}
</style>
<!-- fix-home-command-center-value-layout-end -->
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
    print(path, "fixed home command center value layout")
