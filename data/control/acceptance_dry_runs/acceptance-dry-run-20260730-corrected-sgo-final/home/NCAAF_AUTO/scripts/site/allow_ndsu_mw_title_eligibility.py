from pathlib import Path
import csv

RULES = Path("conference_eligibility_rules_2026.csv")

def main():
    if not RULES.exists():
        print("no eligibility rules file found")
        return

    rows = []
    with RULES.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for r in reader:
            team = str(r.get("team") or "").strip().lower()
            conf = str(r.get("conference") or "").strip().upper()
            if conf == "MW" and team in {"north dakota state", "ndsu"}:
                print("removed NDSU MW title exclusion rule")
                continue
            rows.append(r)

    with RULES.open("w", newline="", encoding="utf-8") as f:
        if fieldnames:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    print(f"wrote {RULES}: {len(rows)} rule rows")

if __name__ == "__main__":
    main()
