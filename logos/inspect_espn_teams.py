import requests
import pandas as pd

URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams?limit=1000"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(URL, headers=HEADERS, timeout=60)
r.raise_for_status()
data = r.json()

rows = []
for item in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
    team = item.get("team", {})
    logos = team.get("logos", []) or []
    rows.append({
        "espn_id": team.get("id", ""),
        "displayName": team.get("displayName", ""),
        "shortDisplayName": team.get("shortDisplayName", ""),
        "name": team.get("name", ""),
        "nickname": team.get("nickname", ""),
        "abbreviation": team.get("abbreviation", ""),
        "logo_url": logos[0].get("href", "") if logos else "",
    })

df = pd.DataFrame(rows)
df.to_csv("espn_team_lookup.csv", index=False)

print("Done.")
print(f"Rows: {len(df)}")
print("Wrote espn_team_lookup.csv")