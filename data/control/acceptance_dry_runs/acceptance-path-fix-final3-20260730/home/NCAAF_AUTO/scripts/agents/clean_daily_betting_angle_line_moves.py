#!/usr/bin/env python3
from pathlib import Path
import re
import pandas as pd

CSV = Path("data/agents/daily_betting_angles.csv")

def s(x):
    if pd.isna(x):
        return ""
    return str(x)

def is_price_only_line_move(row):
    category = s(row.get("category")).lower()
    title = s(row.get("title")).lower()
    reason = s(row.get("reason")).lower()

    is_game_line = "game line" in category or "line move" in category or "line move" in title

    if not is_game_line:
        return False

    price_market_patterns = [
        " spread price",
        " total over price",
        " total under price",
        " over price",
        " under price",
        " moneyline price",
        " price "
    ]

    if any(p in f" {title} " for p in price_market_patterns):
        return True

    if re.search(r"\bprice\s+[+-]?\d+(?:\.\d+)?\s*→\s*[+-]?\d+(?:\.\d+)?\b", title):
        return True

    if "price nan" in reason and "moved" in reason:
        return True

    return False

def current_price_from_reason(reason):
    txt = s(reason)

    m = re.search(r"\bprice\s+([+-]?\d+(?:\.\d+)?|nan)\s*→\s*([+-]?\d+(?:\.\d+)?|nan)", txt, flags=re.I)
    if not m:
        return None

    cur = m.group(2)
    if cur.lower() == "nan":
        return None

    try:
        n = float(cur)
        return str(int(n)) if n.is_integer() else str(n)
    except Exception:
        return cur

def clean_reason(row):
    reason = s(row.get("reason"))

    current_price = current_price_from_reason(reason)

    reason = re.sub(
        r"\s*·\s*price\s+([+-]?\d+(?:\.\d+)?|nan)\s*→\s*([+-]?\d+(?:\.\d+)?|nan)",
        "",
        reason,
        flags=re.I,
    )

    if current_price:
        reason = re.sub(
            r"(Moved\s+[+-]?\d+(?:\.\d+)?\s*point\(s\))",
            rf"\1 · current price {current_price}",
            reason,
            flags=re.I,
        )

    reason = re.sub(r"\s+·\s+·\s+", " · ", reason)
    reason = re.sub(r"\s{2,}", " ", reason).strip()
    return reason

def main():
    if not CSV.exists():
        raise SystemExit(f"missing {CSV}")

    df = pd.read_csv(CSV)
    if df.empty:
        print("daily betting angles empty")
        return

    before = len(df)

    mask_remove = df.apply(is_price_only_line_move, axis=1)
    removed = int(mask_remove.sum())

    df = df[~mask_remove].copy()

    if "reason" in df.columns:
        df["reason"] = df.apply(clean_reason, axis=1)

    df.to_csv(CSV, index=False)

    print(f"cleaned {CSV}")
    print(f"rows before: {before}")
    print(f"removed price-only line moves: {removed}")
    print(f"rows after: {len(df)}")

    if "category" in df.columns:
        print(df["category"].value_counts().to_string())

if __name__ == "__main__":
    main()
