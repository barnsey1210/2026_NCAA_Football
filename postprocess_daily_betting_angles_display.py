from pathlib import Path
import re
import pandas as pd

CSV = Path("data/agents/daily_betting_angles.csv")
MD = Path("data/agents/daily_betting_angles.md")

def clean_pp_text(x):
    if pd.isna(x):
        return ""
    s = str(x)
    return re.sub(r'([+-]?\d+(?:\.\d+)?)\s*pp\b', r'\1%', s)

def max_pct_score(text):
    vals = []
    for m in re.finditer(r'([+-]?\d+(?:\.\d+)?)\s*(?:pp|%)\b', str(text), flags=re.I):
        try:
            vals.append(float(m.group(1)))
        except Exception:
            pass
    if not vals:
        return ""
    best = max(vals, key=lambda v: abs(v))
    return f"{abs(best):.1f}%"

def main():
    if not CSV.exists():
        raise SystemExit(f"missing {CSV}")

    df = pd.read_csv(CSV)

    if "category" in df.columns:
        market_mask = df["category"].astype(str).str.lower().eq("market move")
    else:
        market_mask = pd.Series(False, index=df.index)

    if "score" in df.columns and "reason" in df.columns:
        df.loc[market_mask, "score"] = df.loc[market_mask, "reason"].apply(max_pct_score)

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(clean_pp_text)

    df.to_csv(CSV, index=False)

    if MD.exists():
        txt = MD.read_text(errors="ignore")
        txt = re.sub(r'([+-]?\d+(?:\.\d+)?)\s*pp\b', r'\1%', txt)
        MD.write_text(txt)

    print(f"Postprocessed {CSV}: market move score/display uses % instead of pp")

if __name__ == "__main__":
    main()
