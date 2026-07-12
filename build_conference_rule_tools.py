from pathlib import Path
from datetime import datetime
import csv, json, re
from collections import defaultdict, Counter

ROOT = Path('.')
INDEX = ROOT / 'index.html'

EXPECTED_CONFERENCE_GAMES_2026 = {
    'American': 8,
    'B12': 9,
    'B1G': 9,
    'CUSA': 8,
    'MAC': 8,
    'MW': 8,
    'PAC12': 8,
    'SEC': 9,
    'Sun Belt': 8,
}

ACC_EIGHT_GAME_TEAMS_2026 = {
    'Boston College',
    'Clemson',
    'Florida State',
    'Georgia Tech',
    'North Carolina',
}

def expected_conference_games_2026(conf, team):
    if conf == 'ACC':
        return 8 if team in ACC_EIGHT_GAME_TEAMS_2026 else 9
    return EXPECTED_CONFERENCE_GAMES_2026.get(conf)


ELIGIBILITY_DEFAULT_ROWS = [
    {
        'conference': 'MW',
        'team': 'North Dakota State',
        'title_game_eligible': 'FALSE',
        'title_winner_eligible': 'FALSE',
        'counts_in_standings': 'TRUE',
        'notes': 'First-year Mountain West member; keep schedule/standings/SOS but exclude from 2026 MW title game/title odds.'
    }
]


def load_db(index_path: Path = INDEX):
    html = index_path.read_text(encoding='utf-8')
    m = re.search(r'(<script id="db" type="application/json">)(.*?)(</script>)', html, re.S)
    if not m:
        raise SystemExit(f'Could not find embedded DB in {index_path}')
    return html, m, json.loads(m.group(2))


def norm_bool(x):
    if x is None:
        return None
    s = str(x).strip().lower()
    if s in {'true', '1', 'yes', 'y'}:
        return True
    if s in {'false', '0', 'no', 'n'}:
        return False
    return None


def game_key(g):
    return (
        str(g.get('week', '')).strip(),
        str(g.get('date', '')).strip(),
        str(g.get('away_team', '')).strip(),
        str(g.get('home_team', '')).strip(),
    )


def audit_counts(db):
    counts = defaultdict(lambda: defaultdict(int))
    team_games = defaultdict(list)
    games = db.get('games', [])
    for g in games:
        if bool(g.get('is_conference_game')):
            for side in ('away', 'home'):
                team = g.get(f'{side}_team')
                conf = g.get(f'{side}_conference')
                counts[conf][team] += 1
                team_games[(conf, team)].append(g)
    return counts, team_games


def write_count_audit(db, out_path='conference_game_count_audit_2026.csv'):
    counts, _ = audit_counts(db)
    rows = []
    for conf in sorted(counts):
        values = sorted(set(counts[conf].values()))
        for team, cnt in sorted(counts[conf].items()):
            expected = expected_conference_games_2026(conf, team)
            delta = (cnt - expected) if expected is not None else ''
            rows.append({
                'conference': conf,
                'team': team,
                'current_conf_games': cnt,
                'expected_conf_games': expected if expected is not None else '',
                'delta_vs_expected': delta,
                'conference_unique_counts': '|'.join(map(str, values)),
                'issue_flag': 'TRUE' if (expected is not None and cnt != expected) else 'FALSE',
            })
    write_csv(out_path, rows)
    return rows


def build_review_candidates(db):
    counts, team_games = audit_counts(db)
    over_by_conf = {}
    for conf, d in counts.items():
        over = set()
        for team, cnt in d.items():
            expected = expected_conference_games_2026(conf, team)
            if expected is not None and cnt > expected:
                over.add(team)
        over_by_conf[conf] = over

    rows = []
    for g in db.get('games', []):
        if not bool(g.get('is_conference_game')):
            continue
        away = g.get('away_team')
        home = g.get('home_team')
        away_conf = g.get('away_conference')
        home_conf = g.get('home_conference')
        if away_conf != home_conf:
            continue
        conf = away_conf
        expected_away = expected_conference_games_2026(conf, away)
        expected_home = expected_conference_games_2026(conf, home)
        expected = expected_away if expected_away == expected_home else '' or ''
        away_count = counts[conf].get(away, 0)
        home_count = counts[conf].get(home, 0)
        away_over = away in over_by_conf.get(conf, set())
        home_over = home in over_by_conf.get(conf, set())
        if away_over or home_over or conf in {'ACC', 'American', 'CUSA', 'MW'}:
            priority = 'medium'
            suggested = ''
            reason = ''
            if away_over and home_over:
                priority = 'high'
                reason = 'Both teams currently exceed expected conference-game count; if this is non-conference, it fixes both teams.'
                suggested = 'FALSE?'
            elif away_over or home_over:
                priority = 'review'
                reason = 'One team currently exceeds expected conference-game count.'
            if conf == 'American' and {away, home} == {'Army', 'Navy'}:
                priority = 'high'
                suggested = 'FALSE?'
                reason = 'Army-Navy often should not count toward AAC title selection/regular conference-game count.'
            if conf == 'MW' and {away, home} == {'North Dakota State', 'San Jose State'}:
                priority = 'high'
                suggested = 'FALSE?'
                reason = 'Only NDSU and San Jose State are at 9 MW games; this one game explains both over-counts.'
            if conf == 'CUSA' and {away, home} == {'New Mexico State', 'Sam Houston'}:
                priority = 'high'
                suggested = 'FALSE?'
                reason = 'Only New Mexico State and Sam Houston are at 8 CUSA games; this one game explains both over-counts.'
            if conf == 'ACC' and int(g.get('week') or -1) == 0:
                priority = 'high'
                reason = 'Week 0 same-conference game; verify whether it counts in ACC standings.'
            rows.append({
                'priority': priority,
                'conference': conf,
                'week': g.get('week'),
                'date': g.get('date'),
                'away_team': away,
                'home_team': home,
                'current_is_conference_game': g.get('is_conference_game'),
                'cfbd_conference_game': g.get('cfbd_conference_game'),
                'away_current_conf_games': away_count,
                'home_current_conf_games': home_count,
                'expected_conf_games': expected,
                'away_over_expected': 'TRUE' if away_over else 'FALSE',
                'home_over_expected': 'TRUE' if home_over else 'FALSE',
                'suggested_override_conf_game': suggested,
                'override_conf_game': '',
                'notes': reason,
                'game_id': g.get('game_id'),
            })
    order = {'high': 0, 'review': 1, 'medium': 2}
    rows.sort(key=lambda r: (order.get(r['priority'], 9), r['conference'], int(r['week'] or 99), r['away_team'], r['home_team']))
    return rows


def write_csv(path, rows):
    path = Path(path)
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def ensure_rule_files(db):
    elig_path = Path('conference_eligibility_rules_2026.csv')
    if not elig_path.exists():
        write_csv(elig_path, ELIGIBILITY_DEFAULT_ROWS)

    overrides_path = Path('conference_game_overrides_2026.csv')
    if not overrides_path.exists():
        candidates = build_review_candidates(db)
        # Keep a starter override file with only the highest-priority review rows.
        high = [r for r in candidates if r['priority'] == 'high']
        override_rows = []
        for r in high:
            override_rows.append({
                'week': r['week'],
                'date': r['date'],
                'away_team': r['away_team'],
                'home_team': r['home_team'],
                'current_is_conference_game': r['current_is_conference_game'],
                'override_conf_game': '',
                'notes': r['notes'],
            })
        write_csv(overrides_path, override_rows)


def apply_game_overrides(db, override_path='conference_game_overrides_2026.csv'):
    p = Path(override_path)
    if not p.exists() or not p.read_text(encoding='utf-8').strip():
        return []
    by_key = {game_key(g): g for g in db.get('games', [])}
    changed = []
    with p.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            val = norm_bool(r.get('override_conf_game'))
            if val is None:
                continue
            k = (str(r.get('week','')).strip(), str(r.get('date','')).strip(), str(r.get('away_team','')).strip(), str(r.get('home_team','')).strip())
            g = by_key.get(k)
            if not g:
                changed.append({'status':'not_found', **r})
                continue
            old = bool(g.get('is_conference_game'))
            g['is_conference_game'] = val
            g['conference_game_override'] = True
            g['conference_game_override_note'] = r.get('notes','')
            changed.append({'status':'changed', 'old': old, 'new': val, **r})
    return changed


def apply_eligibility_rules(db, elig_path='conference_eligibility_rules_2026.csv'):
    p = Path(elig_path)
    if not p.exists():
        return []
    rules = defaultdict(dict)
    with p.open(newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            conf = r.get('conference')
            team = r.get('team')
            if not conf or not team:
                continue
            title_game_eligible = norm_bool(r.get('title_game_eligible'))
            title_winner_eligible = norm_bool(r.get('title_winner_eligible'))
            if title_game_eligible is False or title_winner_eligible is False:
                rules[conf][team] = r

    def fnum(x):
        try: return float(x or 0)
        except Exception: return 0.0

    changes = []
    for conf_obj in db.get('conferences', []):
        conf = conf_obj.get('conference')
        ineligible = rules.get(conf, {})
        if not ineligible:
            continue
        teams = conf_obj.get('teams', [])
        eligible = [t for t in teams if t.get('team') not in ineligible]
        for t in teams:
            if t.get('team') in ineligible:
                changes.append({'conference': conf, 'team': t.get('team'), 'old_make_title_game_pct': t.get('make_title_game_pct'), 'old_conference_title_pct': t.get('conference_title_pct')})
                t['make_title_game_pct'] = 0.0
                t['conference_title_pct'] = 0.0
                t['lose_title_game_pct'] = 0.0
                t['conference_title_ineligible'] = True
                t['conference_title_ineligible_note'] = ineligible[t.get('team')].get('notes') or 'Ineligible for conference championship/title odds.'
        title_sum = sum(fnum(t.get('conference_title_pct')) for t in eligible)
        if title_sum > 0:
            for t in eligible:
                t['conference_title_pct'] = fnum(t.get('conference_title_pct')) / title_sum
        make_sum = sum(fnum(t.get('make_title_game_pct')) for t in eligible)
        if make_sum > 0:
            for t in eligible:
                t['make_title_game_pct'] = fnum(t.get('make_title_game_pct')) * (2.0 / make_sum)
        for t in eligible:
            t['lose_title_game_pct'] = max(0.0, fnum(t.get('make_title_game_pct')) - fnum(t.get('conference_title_pct')))
        ranked = sorted(eligible, key=lambda t: (fnum(t.get('make_title_game_pct')), fnum(t.get('conference_title_pct')), fnum(t.get('avg_conference_wins')), fnum(t.get('combo'))), reverse=True)
        cg = conf_obj.get('championship_game')
        if cg and len(ranked) >= 2:
            cg['projected_matchup'] = {'away_team': ranked[1].get('team'), 'home_team': ranked[0].get('team')}
            cg['eligibility_note'] = '; '.join([r.get('notes','') for r in ineligible.values() if r.get('notes')])
    return changes


def save_db(html, m, db, out_path=INDEX):
    new = json.dumps(db, separators=(',', ':'))
    out_path.write_text(html[:m.start(2)] + new + html[m.end(2):], encoding='utf-8')


def main():
    html, m, db = load_db(INDEX)
    ensure_rule_files(db)
    candidates = build_review_candidates(db)
    write_csv('conference_game_review_candidates_2026.csv', candidates)
    write_count_audit(db, 'conference_game_count_audit_before_rules_2026.csv')

    backup = Path(f'index_before_conference_rules_{datetime.now():%Y%m%d_%H%M%S}.html')
    backup.write_text(html, encoding='utf-8')

    game_changes = apply_game_overrides(db)
    eligibility_changes = apply_eligibility_rules(db)
    save_db(html, m, db, INDEX)
    write_count_audit(db, 'conference_game_count_audit_after_rules_2026.csv')

    print(f'Backup: {backup}')
    print('Wrote: conference_game_count_audit_before_rules_2026.csv')
    print('Wrote: conference_game_count_audit_after_rules_2026.csv')
    print('Wrote: conference_game_review_candidates_2026.csv')
    print('Ensured: conference_game_overrides_2026.csv')
    print('Ensured: conference_eligibility_rules_2026.csv')
    print(f'Applied game overrides: {len(game_changes)}')
    print(f'Applied eligibility changes: {len(eligibility_changes)}')

if __name__ == '__main__':
    main()
