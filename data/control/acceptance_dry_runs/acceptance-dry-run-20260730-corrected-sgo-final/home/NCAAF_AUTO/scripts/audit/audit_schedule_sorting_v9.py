#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/'NCAAF_AUTO'
p=(ROOT/'schedule_v2.html').read_text(errors='ignore')
for token in ('data-sort="kickoff"','data-sort="away"','data-sort="home"',"sortKey='kickoff'","if(sortKey==='away')","sortDir=sortKey===next?-sortDir:1",'id="schedule-sort-css"'):
    assert token in p, f'Missing {token}'
print('PASS: Schedule sorting v9')
