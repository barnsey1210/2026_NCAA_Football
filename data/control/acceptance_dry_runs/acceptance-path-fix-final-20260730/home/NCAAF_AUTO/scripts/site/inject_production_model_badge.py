#!/usr/bin/env python3
from pathlib import Path
import sys
import re
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.ncaaf_config import model_summary, production_model

TARGETS = [Path("index.html"), Path("index_auto_market.html"), Path("index_publish.html"), Path("matchup.html")]
START = "<!-- production-model-badge-start -->"
END = "<!-- production-model-badge-end -->"


def block():
    model = production_model()
    label = f"Model: {model_summary(short=True)} · Updated {model['updated']}"
    title = f"Production composite: {model_summary()}. Active teams are reweighted across available approved sources when coverage is incomplete."
    return f'''{START}
<style id="production-model-badge-style">
#production-model-badge{{position:fixed;z-index:2147483000;top:10px;right:14px;padding:7px 11px;border:1px solid rgba(34,197,94,.42);border-radius:999px;background:rgba(5,18,38,.94);color:#bbf7d0;font:800 11px/1.2 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;box-shadow:0 5px 20px rgba(0,0,0,.24);white-space:nowrap}}
@media(max-width:760px){{#production-model-badge{{position:static;display:block;margin:8px 12px;text-align:center;white-space:normal}}}}
</style>
<div id="production-model-badge" title="{title}">{label}</div>
{END}'''


for path in TARGETS:
    if not path.exists():
        continue
    s = path.read_text(errors="ignore")
    b = block()
    if START in s and END in s:
        s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: b, s, flags=re.S)
    else:
        s = s.replace("</body>", b + "\n</body>", 1)
    path.write_text(s, encoding="utf-8")
    print(path, "production model badge injected")
