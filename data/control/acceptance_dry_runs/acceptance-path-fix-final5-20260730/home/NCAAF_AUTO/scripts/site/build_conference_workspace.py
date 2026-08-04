#!/usr/bin/env python3
"""Build current and projected conference standings with schedule and market context."""
from pathlib import Path
from datetime import datetime, timezone
import json,re,sys
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from scripts.lib.ncaaf_config import canonical_team

def main():
 s=(ROOT/'v1.html').read_text(); db=json.loads(re.search(r'<script id="db" type="application/json">(.*?)</script>',s,re.S).group(1))
 fv=json.loads((ROOT/'data/site/futures_view.json').read_text()); markets={canonical_team(x['team']):x for x in fv['rows']}
 teams={canonical_team(x['team']):x for x in db['teams']}; games=db['games']; rows=[]
 for key,t in teams.items():
  played=[g for g in games if g.get('cfbd_completed') and key in {canonical_team(g.get('away_team')),canonical_team(g.get('home_team'))}]
  remaining=[g for g in games if not g.get('cfbd_completed') and key in {canonical_team(g.get('away_team')),canonical_team(g.get('home_team'))}]
  wins=losses=cwins=closses=0
  for g in played:
   home=canonical_team(g.get('home_team'))==key; tp=g.get('home_points') if home else g.get('away_points'); op=g.get('away_points') if home else g.get('home_points')
   if tp is None or op is None: continue
   won=tp>op; wins+=won; losses+=not won
   if g.get('is_conference_game'): cwins+=won; closses+=not won
  opp=[]; conf_opp=[]; remaining_conf_opp=[]
  for g in played+remaining:
   other=g['away_team'] if canonical_team(g.get('home_team'))==key else g['home_team']; rating=teams.get(canonical_team(other),{}).get('combo')
   if rating is not None: opp.append(rating)
   if rating is not None and g.get('is_conference_game'): conf_opp.append(rating)
  for g in remaining:
   other=g['away_team'] if canonical_team(g.get('home_team'))==key else g['home_team']; rating=teams.get(canonical_team(other),{}).get('combo')
   if rating is not None and g.get('is_conference_game'): remaining_conf_opp.append(rating)
  m=markets.get(key,{})
  rows.append({'team':t['team'],'slug':t['slug'],'conference':t['conference'],'rank':t['rank'],'rating':t['combo'],
   'current_wins':wins,'current_losses':losses,'current_conf_wins':cwins,'current_conf_losses':closses,
   'projected_wins':t.get('avg_total_wins'),'projected_conf_wins':t.get('avg_conference_wins'),
   'projected_losses':len(played)+len(remaining)-(t.get('avg_total_wins') or 0),'projected_conf_losses':sum(bool(g.get('is_conference_game')) for g in played+remaining)-(t.get('avg_conference_wins') or 0),
   'make_title_game_pct':t.get('make_title_game_pct'),'title_pct':t.get('conference_title_pct'),
   'overall_sos':sum(opp)/len(opp) if opp else None,'conf_sos':sum(conf_opp)/len(conf_opp) if conf_opp else None,'remaining_sos':sum(remaining_conf_opp)/len(remaining_conf_opp) if remaining_conf_opp else None,
   'market_win_total':m.get('market_win_total'),'win_edge':m.get('win_edge'),'title_market_prob':m.get('title_market_prob'),
   'title_edge':m.get('title_edge'),'title_price':m.get('title_price'),'title_book':m.get('title_book'),'open_wagers':m.get('open_wagers',[])})
 conferences=[]
 for c in db['conferences']:
  cr=sorted([x for x in rows if x['conference']==c['conference']],key=lambda x:x['projected_conf_wins'] or -1,reverse=True)
  for i,x in enumerate(cr,1): x['projected_finish']=i
  for field,rank_field in [('conf_sos','conf_sos_rank'),('remaining_sos','remaining_sos_rank')]:
   ranked=sorted((x for x in cr if x.get(field) is not None),key=lambda x:x[field],reverse=True)
   for i,x in enumerate(ranked,1): x[rank_field]=i
  average_team_rating=sum(x['rating'] for x in cr if x.get('rating') is not None)/sum(x.get('rating') is not None for x in cr)
  conferences.append({'conference':c['conference'],'slug':c['slug'],'average_strength':c.get('average_strength'),'average_team_rating':average_team_rating,'championship_game':c.get('championship_game'),'teams':cr})
 for i,c in enumerate(sorted(conferences,key=lambda x:x['average_team_rating'],reverse=True),1): c['conference_rank']=i
 out={'schema_version':'conference-workspace-v1','built_at':datetime.now(timezone.utc).isoformat(),'conferences':conferences}
 (ROOT/'data/site/conference_workspace.json').write_text(json.dumps(out,separators=(',',':'))+'\n');print(len(conferences),sum(len(x['teams']) for x in conferences))
if __name__=='__main__':main()
