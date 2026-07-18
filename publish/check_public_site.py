#!/usr/bin/env python3
from pathlib import Path
import json, sys
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'build/public_site'
modern=['index.html','dashboard.html','openers.html','matchups.html','futures.html','conferences.html','betting.html','team.html','ratings.html','simulations.html']
required=modern+['legacy.html','matchup.html','v1.html']; errors=[]
for name in required:
 p=OUT/name
 minimum=100 if name=='legacy.html' else 1000
 if not p.exists() or p.stat().st_size<minimum: errors.append(f'missing or too small: {name}'); continue
 if name in modern:
  s=p.read_text(errors='ignore')
  if 'class="top"' not in s or 'href="openers.html"' not in s or 'href="matchups.html"' not in s: errors.append(f'top navigation missing: {name}')
  if '_v2.html' in s: errors.append(f'prototype link leaked: {name}')
shadow=ROOT/'data/site/postgame_shadow_updates.json'
if not shadow.exists(): errors.append('postgame shadow artifact missing')
else:
 d=json.loads(shadow.read_text())
 if d.get('applied_to_ratings') or d.get('applied_to_projections'): errors.append('shadow artifact marked as applied')
if errors:
 print('PUBLIC SITE VALIDATION FAILED'); print('\n'.join('- '+x for x in errors)); sys.exit(1)
print(f'PUBLIC SITE VALIDATION PASSED: {len(required)} pages; shadow artifact isolated')
