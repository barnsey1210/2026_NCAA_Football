#!/usr/bin/env python3
from pathlib import Path
ROOT=Path.home()/"NCAAF_AUTO"
p=(ROOT/"openers_v2.html").read_text(errors="ignore")
for token in (
    "SCHEDULE_ENRICHMENT=new Map()",
    "schedule_live_enrichment.json",
    "function shadowImpactPairHtml",
    "Current<br>model",
    "Best market",
    "Spread<br>impact",
    "Total<br>impact",
    "function shadowStatusHtml",
):
    assert token in p, f"Missing {token}"
print("PASS: Openers shadow model/market/impacts v6")
