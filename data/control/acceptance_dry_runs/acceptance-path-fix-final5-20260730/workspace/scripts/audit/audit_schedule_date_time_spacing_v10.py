#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/'NCAAF_AUTO'
p=(ROOT/'schedule_v2.html').read_text(errors='ignore')
assert 'scheduleDateTimeCell' in p
assert 'gap:8px' in p
assert 'white-space:nowrap' in p
print('PASS: Schedule date/time spacing v10')
