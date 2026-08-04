#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/'NCAAF_AUTO'
p=(ROOT/'schedule_v2.html').read_text(errors='ignore')
assert 'data-sort="status"' in p
assert "sortKey==='status'" in p
assert "dataStatus(x,shadowFor(x)).label" in p
print('PASS: Schedule Data Status sort v12')
