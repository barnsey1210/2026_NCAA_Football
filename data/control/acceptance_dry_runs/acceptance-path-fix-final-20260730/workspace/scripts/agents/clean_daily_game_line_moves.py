#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import math
import re
import sys
import pandas as pd

CSV = Path('data/agents/daily_betting_angles.csv')
AUDIT = Path('data/audits/daily_game_line_move_cleaning.csv')
NUMBER_MOVE_RE = re.compile(r'(?P<label>\bSpread\b|\bTotal\b)\s+(?P<old>[+-]?\d+(?:\.\d+)?)\s*(?:→|->|=>|to)\s*(?P<new>[+-]?\d+(?:\.\d+)?)', re.I)
PRICE_ONLY_RE = re.compile(r'\b(?:Spread|Total)\b.*?\b(?:Price|Over\s+Price|Under\s+Price)\b', re.I)

def clean_text(value):
    if value is None: return ''
    try:
        if pd.isna(value): return ''
    except Exception: pass
    text = str(value).strip()
    text = re.sub(r'\bnan\b', '', text, flags=re.I)
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\s+([,.;:])', r'\1', text)
    return text.strip(' ·|')

def valid_game_line_move(title):
    if PRICE_ONLY_RE.search(title): return False, 'price_only'
    match = NUMBER_MOVE_RE.search(title)
    if not match: return False, 'no_spread_or_total_number_move'
    old, new = float(match.group('old')), float(match.group('new'))
    if not (math.isfinite(old) and math.isfinite(new)): return False, 'nonfinite_line'
    if abs(new-old) < 1e-9: return False, 'unchanged_line'
    return True, 'actual_line_move'

def main():
    if not CSV.exists():
        print(f'WARNING: missing {CSV}; nothing to clean'); return
    df = pd.read_csv(CSV, low_memory=False)
    if df.empty:
        print('Daily betting angles CSV is empty; nothing to clean'); return
    for col in ['category','title','team','grade','score','reason','action','source','research_query']:
        if col not in df.columns: df[col] = ''
    for col in ['category','title','team','grade','reason','action','source','research_query']:
        df[col] = df[col].map(clean_text)
    game_mask = df['category'].str.casefold().eq('game line move')
    keep = pd.Series(True, index=df.index)
    audit_rows = []
    for idx, row in df.loc[game_mask].iterrows():
        valid, audit_reason = valid_game_line_move(clean_text(row['title']))
        keep.loc[idx] = valid
        audit_rows.append({'kept':valid,'audit_reason':audit_reason,'category':clean_text(row.get('category','')),'title':clean_text(row.get('title','')),'reason':clean_text(row.get('reason','')),'source':clean_text(row.get('source',''))})
    cleaned = df.loc[keep].copy()
    before = len(cleaned)
    cleaned['_key'] = cleaned.apply(lambda r: re.sub(r'\s+', ' ', f"{clean_text(r.get('title','')).lower()}|{clean_text(r.get('reason','')).lower()}").strip(), axis=1)
    cleaned = cleaned.drop_duplicates('_key', keep='first').drop(columns=['_key'])
    dupes = before - len(cleaned)
    cleaned['score'] = cleaned['score'].where(cleaned['score'].notna(), '')
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(audit_rows).to_csv(AUDIT, index=False)
    cleaned.to_csv(CSV, index=False)
    initial = int(game_mask.sum())
    retained = int(cleaned['category'].str.casefold().eq('game line move').sum())
    print('DAILY GAME-LINE MOVE CLEANING')
    print('='*88)
    print(f'Rows before: {len(df)}')
    print(f'Game-line move rows before: {initial}')
    print(f'Valid spread/total line moves retained: {retained}')
    print(f'Price-only/invalid game moves removed: {initial-retained}')
    print(f'Exact duplicate rows removed: {dupes}')
    print(f'Wrote: {CSV}')
    print(f'Audit: {AUDIT}')

if __name__ == '__main__':
    try: main()
    except Exception as exc:
        print(f'ERROR: {exc}', file=sys.stderr); raise
