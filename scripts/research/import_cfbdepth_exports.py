#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, shutil
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

TEAM_OVERRIDES = {
    "App State": "Appalachian State",
    "Florida International": "FIU",
    "Hawai'i": "Hawaii",
    "Massachusetts": "UMass",
    "Miami": "Miami FL",
    "Miami (OH)": "Miami OH",
    "San José State": "San Jose State",
    "UConn": "Connecticut",
    "UL Monroe": "Louisiana-Monroe",
}
PLAYER_POSITIONS = ("qb","rb","wr","te","ol","dl","lb","db")
ROTATION_SIZE = {"QB":1,"RB":3,"WR":5,"TE":3,"OL":7,"DL":7,"LB":5,"DB":7}
TEAM_DATASETS = {
    "air-ratings":"cfbdepth_air_ratings_2026.csv",
    "coaching":"cfbdepth_coaching_impacts_2026.csv",
    "depth":"cfbdepth_depth_grades_2026.csv",
    "rotation":"cfbdepth_rotation_talent_2026.csv",
    "injury":"cfbdepth_team_injury_impact_2026.csv",
    "offense-profile":"cfbdepth_offense_profile_2026.csv",
    "defense-profile":"cfbdepth_defense_profile_2026.csv",
}
def slug(s): return re.sub(r"[^a-z0-9]+","_",str(s).strip().lower()).strip("_")
def find_one(raw_dir:Path, token:str)->Path:
    hits=sorted(raw_dir.glob(f"cfbdepth-{token}_*.csv"))
    if len(hits)!=1: raise SystemExit(f"Expected exactly one {token} CSV in {raw_dir}; found {len(hits)}")
    return hits[0]
def normalize_team_name(name):
    value=str(name or "").strip()
    return TEAM_OVERRIDES.get(value,value)
def clean_columns(df):
    out=df.copy()
    out.columns=[slug(c) for c in out.columns]
    return out
def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--raw-dir",required=True,type=Path)
    ap.add_argument("--repo-root",default=".",type=Path)
    ap.add_argument("--as-of",default="2026-08-05")
    args=ap.parse_args()
    root=args.repo_root.resolve(); raw=args.raw_dir.resolve()
    canonical=root/"data/canonical"; audits=root/"data/audits"
    dated=root/"data/raw/cfbdepth"/args.as_of
    canonical.mkdir(parents=True,exist_ok=True); audits.mkdir(parents=True,exist_ok=True); dated.mkdir(parents=True,exist_ok=True)
    crosswalk_path=root/"config/cfbdepth_player_school_crosswalk.csv"
    if not crosswalk_path.exists(): raise SystemExit(f"Missing {crosswalk_path}")
    xw=pd.read_csv(crosswalk_path,dtype=str).fillna("")
    mapping=dict(zip(xw["cfbdepth_school"],xw["site_team"]))
    audit={"schema_version":"cfbdepth-import-audit-v1","as_of":args.as_of,"built_at": f"{args.as_of}T00:00:00+00:00","inputs":{},"outputs":{},"warnings":[]}
    team_sets={}
    # team-level datasets
    for token,outname in TEAM_DATASETS.items():
        src=find_one(raw,token)
        destination = dated / src.name
        if src.resolve() != destination.resolve():
            shutil.copy2(src, destination)
        df=pd.read_csv(src)
        if "School" not in df.columns: raise SystemExit(f"{src.name}: missing School")
        df.insert(0,"as_of",args.as_of)
        df["team"]=df["School"].map(normalize_team_name)
        cols=["as_of","team"]+[c for c in df.columns if c not in {"as_of","team","School"}]
        out=clean_columns(df[cols])
        outpath=canonical/outname; out.to_csv(outpath,index=False)
        teams=set(out["team"].dropna().astype(str)); team_sets[token]=teams
        audit["inputs"][src.name]={"rows":len(df),"columns":list(df.columns),"sha256":sha256(src)}
        audit["outputs"][str(outpath.relative_to(root))]={"rows":len(out),"teams":len(teams)}
    base=team_sets["air-ratings"]
    for token,teams in team_sets.items():
        if teams!=base:
            audit["warnings"].append({"dataset":token,"missing_vs_air":sorted(base-teams),"extra_vs_air":sorted(teams-base)})
    # players
    frames=[]; unmapped=set()
    for pos in PLAYER_POSITIONS:
        src=find_one(raw,f"{pos}-ratings")
        destination = dated / src.name
        if src.resolve() != destination.resolve():
            shutil.copy2(src, destination)
        df=pd.read_csv(src)
        required={"Name","School","Overall"}
        if not required.issubset(df.columns): raise SystemExit(f"{src.name}: missing {sorted(required-set(df.columns))}")
        df.insert(0,"as_of",args.as_of); df.insert(1,"position_group",pos.upper())
        df["team"]=df["School"].astype(str).map(mapping)
        unmapped.update(df.loc[df["team"].isna(),"School"].dropna().astype(str))
        df["team"]=df["team"].fillna("")
        df["source_school"]=df["School"].astype(str)
        df["player"]=df["Name"].astype(str).str.strip()
        cols=["as_of","team","source_school","position_group","player"]+[c for c in df.columns if c not in {"as_of","team","source_school","position_group","player","School","Name"}]
        frames.append(clean_columns(df[cols]))
        audit["inputs"][src.name]={"rows":len(df),"columns":list(df.columns),"sha256":sha256(src)}
    players=pd.concat(frames,ignore_index=True)
    players["overall"]=pd.to_numeric(players["overall"],errors="coerce")
    players["team_mapping_status"]=players["team"].map(lambda x:"mapped" if str(x).strip() else "unmapped")
    players_out=canonical/"cfbdepth_players_2026.csv"; players.to_csv(players_out,index=False)
    audit["outputs"][str(players_out.relative_to(root))]={"rows":len(players),"mapped_rows":int((players.team_mapping_status=="mapped").sum()),"unmapped_rows":int((players.team_mapping_status=="unmapped").sum())}
    if unmapped: audit["warnings"].append({"unmapped_player_school_codes":sorted(unmapped)})
    mapped=players[players.team_mapping_status=="mapped"].copy()
    # top players
    top_payload={"schema_version":"cfbdepth-team-top-players-v1","as_of":args.as_of,"teams":{}}
    for team,g in mapped.sort_values(["team","overall","player"],ascending=[True,False,True]).groupby("team"):
        items=[]
        for _,r in g.head(5).iterrows():
            comps={k:(None if pd.isna(v) else float(v)) for k,v in r.items() if k not in {"as_of","team","source_school","position_group","player","conference","overall","team_mapping_status"} and pd.notna(pd.to_numeric(pd.Series([v]),errors="coerce").iloc[0])}
            items.append({"player":r.player,"position_group":r.position_group,"overall":None if pd.isna(r.overall) else float(r.overall),"components":comps})
        top_payload["teams"][team]=items
    top_out=canonical/"cfbdepth_team_top_players_2026.json"; top_out.write_text(json.dumps(top_payload,indent=2)+"\n")
    audit["outputs"][str(top_out.relative_to(root))]={"teams":len(top_payload["teams"]),"players":sum(len(v) for v in top_payload["teams"].values())}
    # position groups
    component_exclude={"as_of","team","source_school","position_group","player","conference","team_mapping_status"}
    rows=[]
    for (team,pos),g in mapped.groupby(["team","position_group"]):
        g=g.sort_values(["overall","player"],ascending=[False,True])
        n=ROTATION_SIZE[pos]; rot=g.head(n); depth=g.iloc[n:]
        row={"as_of":args.as_of,"team":team,"position_group":pos,"players":len(g),"rotation_size_target":n,"rotation_players":len(rot),
             "best_player":g.iloc[0].player if len(g) else "","best_overall":g.iloc[0].overall if len(g) else None,
             "rotation_overall_avg":rot.overall.mean(),"depth_overall_avg":depth.overall.mean() if len(depth) else None,
             "rotation_to_depth_dropoff":rot.overall.mean()-depth.overall.mean() if len(depth) else None,
             "players_15_plus":int((g.overall>=15).sum()),"players_12_plus":int((g.overall>=12).sum())}
        for col in g.columns:
            if col in component_exclude or col=="overall": continue
            vals=pd.to_numeric(rot[col],errors="coerce")
            if vals.notna().any(): row[f"rotation_{col}_avg"]=vals.mean()
        rows.append(row)
    groups=pd.DataFrame(rows).sort_values(["team","position_group"])
    groups_out=canonical/"cfbdepth_position_groups_2026.csv"; groups.to_csv(groups_out,index=False)
    audit["outputs"][str(groups_out.relative_to(root))]={"rows":len(groups),"teams":groups.team.nunique()}
    # crosswalk audit
    used=sorted(set(players.source_school.astype(str)))
    xwa=pd.DataFrame({"cfbdepth_school":used})
    xwa["site_team"]=xwa.cfbdepth_school.map(mapping)
    xwa["mapped"]=xwa.site_team.notna()
    xwa["in_138_team_set"]=xwa.site_team.isin(base)
    xwa_out=audits/"cfbdepth_team_crosswalk_audit.csv"; xwa.to_csv(xwa_out,index=False)
    audit["outputs"][str(xwa_out.relative_to(root))]={"rows":len(xwa),"unmapped":int((~xwa.mapped).sum()),"outside_team_set":int((xwa.mapped & ~xwa.in_138_team_set).sum())}
    audit_out=audits/"cfbdepth_import_audit.json"; audit_out.write_text(json.dumps(audit,indent=2)+"\n")
    print("CFBDepth import complete")
    print("team datasets:",len(TEAM_DATASETS),"players:",len(players),"mapped:",int((players.team_mapping_status=="mapped").sum()))
    print("teams with top-five:",len(top_payload["teams"]),"position groups:",len(groups))
    print("warnings:",len(audit["warnings"]))
    print("audit:",audit_out)
if __name__=="__main__": main()
