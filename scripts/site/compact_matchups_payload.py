#!/usr/bin/env python3
"""Rewrite the rich internal matchup payload compactly without changing its schema."""
from pathlib import Path
import json, os, tempfile
ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/'data/site/matchups_view.json'
MAX_BYTES=16*1024*1024
if not PATH.exists():
    raise SystemExit(f'missing {PATH}')
data=json.loads(PATH.read_text())
fd,tmp=tempfile.mkstemp(prefix='.matchups_view.',suffix='.json',dir=PATH.parent)
try:
    with os.fdopen(fd,'w',encoding='utf-8') as f:
        json.dump(data,f,separators=(',',':'),ensure_ascii=False)
        f.write('\n')
    os.replace(tmp,PATH)
except Exception:
    try:
        os.unlink(tmp)
    except FileNotFoundError:
        pass
    raise
size=PATH.stat().st_size
print(f'compacted matchup payload: {size/1024/1024:.2f} MiB')
if size>MAX_BYTES:
    raise SystemExit(f'matchups_view.json exceeds safe compact limit: {size} > {MAX_BYTES}')
