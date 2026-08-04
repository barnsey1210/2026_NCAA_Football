#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html")]

START = "<!-- polish-home-command-center-tables-start -->"
END = "<!-- polish-home-command-center-tables-end -->"

BLOCK = r'''
<!-- polish-home-command-center-tables-start -->
<script id="polish-home-command-center-tables-js">
(function(){
  function renameDashboardNav(){
    document.querySelectorAll('.nav button').forEach(btn => {
      if (String(btn.textContent || '').trim() === 'Home') btn.textContent = 'Dashboard';
    });
  }
  document.addEventListener('DOMContentLoaded', renameDashboardNav);
  window.addEventListener('hashchange', () => setTimeout(renameDashboardNav, 100));
  setTimeout(renameDashboardNav, 100);
  setTimeout(renameDashboardNav, 500);
})();
</script>

<style id="polish-home-command-center-tables-css">
.home-cmd-table-card{
  min-height:auto!important;
}

.home-cmd-table{
  width:100%;
  border-collapse:collapse;
  table-layout:fixed;
}

.home-cmd-table th{
  font-size:11px!important;
  color:#b9c7e5!important;
  text-transform:uppercase;
  letter-spacing:.08em;
  padding:8px 6px!important;
  border-bottom:1px solid rgba(255,255,255,.16)!important;
}

.home-cmd-table td{
  padding:11px 6px!important;
  border-bottom:1px solid rgba(255,255,255,.09)!important;
  vertical-align:middle!important;
}

.home-cmd-table th:nth-child(1),
.home-cmd-table td:nth-child(1){width:38%;}

.home-cmd-table th:nth-child(2),
.home-cmd-table td:nth-child(2){width:27%;}

.home-cmd-table th:nth-child(3),
.home-cmd-table td:nth-child(3){width:35%;}

.hc-team-line{
  display:flex;
  align-items:center;
  gap:8px;
  min-width:0;
  margin:2px 0;
  font-weight:950;
  color:#f8fafc;
}

.hc-team-line .team-logo-wrap{
  width:28px!important;
  height:28px!important;
  flex:0 0 28px!important;
}

.hc-team-line .team-logo{
  width:25px!important;
  height:25px!important;
  object-fit:contain!important;
}

.hc-team-line span{
  min-width:0;
  white-space:normal;
  overflow:visible;
  text-overflow:clip;
  line-height:1.1;
}

.hc-team-line em{
  font-style:normal;
  color:#9fb0d0;
  font-size:12px;
  font-weight:900;
  margin-left:auto;
  flex:0 0 auto;
}

.hc-bet-cell{
  font-size:16px!important;
  font-weight:950!important;
  line-height:1.15!important;
  white-space:normal!important;
  overflow-wrap:normal!important;
  word-break:normal!important;
}

.hc-bet-cell.good{
  color:#4ade80!important;
}

.hc-rank-cell{
  font-size:16px!important;
  font-weight:950!important;
  color:#dbeafe!important;
  white-space:nowrap!important;
}

.hc-note-cell{
  color:#aebddd!important;
  font-size:13px!important;
  line-height:1.22!important;
  white-space:normal!important;
  overflow:visible!important;
}

@media(max-width:900px){
  .home-cmd-table,
  .home-cmd-table thead,
  .home-cmd-table tbody,
  .home-cmd-table tr,
  .home-cmd-table th,
  .home-cmd-table td{
    display:block;
    width:100%!important;
  }
  .home-cmd-table thead{display:none;}
  .home-cmd-table tr{
    padding:10px 0;
    border-bottom:1px solid rgba(255,255,255,.10);
  }
  .home-cmd-table td{
    border-bottom:0!important;
    padding:5px 0!important;
  }
}
</style>
<!-- polish-home-command-center-tables-end -->
'''

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    # Static replacement with flexible spacing.
    s = re.sub(r"navBtn\('#home'\s*,\s*'Home'\)", "navBtn('#home','Dashboard')", s)

    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: BLOCK, s, flags=re.S)
    else:
        s = s.replace("</body>", BLOCK + "\n</body>")

    path.write_text(s, encoding="utf-8")
    print(path, "polished home command center tables")
