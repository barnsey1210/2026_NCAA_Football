# Historical Betting Analytics Forensic Repair, 2021-2025

## Root cause and disposition

The frozen timestamped Spread study joined market evidence by event ID while assuming provider home/away orientation matched the canonical game orientation. Nine event mappings were reversed. This corrupted selected-team lines, edges, grading, and CLV in 183 frozen derived model/checkpoint rows. Immutable source files were not rewritten; affected derived rows are quarantined and rebuilt from preserved atomic bookmaker outcomes oriented by team identity.

The early-window builder also independently aggregated line, price, and book. It now consumes one atomic outcome row selected by best bettor line, then best price, then deterministic book order. Matched decay now keeps the origin team and wager fixed.

## Audit totals

- Spread rows audited: 246,045
- Total rows audited: 32,013
- Reversed events: 9
- Frozen Spread derived rows quarantined: 183
- Invalid rows remaining in corrected Spread analytics: 0
- Invalid Total rows: 0
- Spread extreme observations reviewed: 5,803
- Total extreme observations reviewed: 281
- Duplicate game/model/checkpoint rows: 0
- Duplicate atomic event/checkpoint/side rows: 0
- Maximum ROI reconciliation difference: 0.000000000000

## Corrected 3+ checkpoint results

| market | model_id | checkpoint | threshold | n | record | win_pct | roi | avg_clv | avg_edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spread | standard_spread_4src_equal_v1 | CLOSE | 3 | 934 | 467-459-8 | 0.5043 | -0.0369 | 0.0000 | 4.5755 |
| spread | standard_spread_4src_equal_v1 | FRI_2PM_ET | 3 | 981 | 536-425-20 | 0.5578 | 0.0660 | 1.7482 | 5.1305 |
| spread | standard_spread_4src_equal_v1 | MON_3PM_ET | 3 | 1048 | 565-474-9 | 0.5438 | 0.0436 | 1.5964 | 5.0145 |
| spread | standard_spread_4src_equal_v1 | MON_9AM_ET | 3 | 1055 | 578-465-12 | 0.5542 | 0.0621 | 1.6374 | 4.9515 |
| spread | standard_spread_4src_equal_v1 | SAT_11PM_ET | 3 | 126 | 74-51-1 | 0.5920 | 0.1266 | 1.7262 | 4.4678 |
| spread | standard_spread_4src_equal_v1 | SUN_12PM_ET | 3 | 480 | 299-177-4 | 0.6282 | 0.2192 | 3.3302 | 5.8922 |
| spread | standard_spread_4src_equal_v1 | SUN_2PM_ET | 3 | 555 | 310-242-3 | 0.5616 | 0.0711 | 1.1793 | 4.4429 |
| spread | standard_spread_4src_equal_v1 | SUN_4PM_ET | 3 | 1025 | 577-436-12 | 0.5696 | 0.0917 | 1.9390 | 5.0622 |
| spread | standard_spread_4src_equal_v1 | SUN_9AM_ET | 3 | 324 | 193-130-1 | 0.5975 | 0.1385 | 1.4028 | 4.4086 |
| spread | standard_spread_4src_equal_v1 | SUN_9PM_ET | 3 | 903 | 480-413-10 | 0.5375 | 0.0242 | 0.6955 | 4.3860 |
| spread | standard_spread_4src_equal_v1 | THU_2PM_ET | 3 | 1138 | 612-511-15 | 0.5450 | 0.0432 | 1.5773 | 5.0410 |
| spread | standard_spread_4src_equal_v1 | TUE_2PM_ET | 3 | 1079 | 573-494-12 | 0.5370 | 0.0291 | 1.5070 | 4.9932 |
| spread | standard_spread_4src_equal_v1 | WED_2PM_ET | 3 | 1095 | 572-511-12 | 0.5282 | 0.0129 | 1.5009 | 5.0056 |
| spread | standard_spread_5src_legacy_v1 | CLOSE | 3 | 900 | 442-449-9 | 0.4961 | -0.0524 | 0.0000 | 4.5496 |
| spread | standard_spread_5src_legacy_v1 | FRI_2PM_ET | 3 | 927 | 500-412-15 | 0.5482 | 0.0482 | 1.7918 | 5.0931 |
| spread | standard_spread_5src_legacy_v1 | MON_3PM_ET | 3 | 1010 | 539-459-12 | 0.5401 | 0.0363 | 1.5941 | 4.9402 |
| spread | standard_spread_5src_legacy_v1 | MON_9AM_ET | 3 | 963 | 527-427-9 | 0.5524 | 0.0586 | 1.6599 | 4.9606 |
| spread | standard_spread_5src_legacy_v1 | SAT_11PM_ET | 3 | 109 | 61-48-0 | 0.5596 | 0.0644 | 1.7339 | 4.5754 |
| spread | standard_spread_5src_legacy_v1 | SUN_12PM_ET | 3 | 444 | 271-169-4 | 0.6159 | 0.1974 | 3.4561 | 5.8913 |
| spread | standard_spread_5src_legacy_v1 | SUN_2PM_ET | 3 | 498 | 284-211-3 | 0.5737 | 0.0933 | 1.0863 | 4.3772 |
| spread | standard_spread_5src_legacy_v1 | SUN_4PM_ET | 3 | 935 | 515-408-12 | 0.5580 | 0.0702 | 1.9460 | 5.0407 |
| spread | standard_spread_5src_legacy_v1 | SUN_9AM_ET | 3 | 287 | 164-122-1 | 0.5734 | 0.0913 | 1.3380 | 4.3753 |
| spread | standard_spread_5src_legacy_v1 | SUN_9PM_ET | 3 | 821 | 429-383-9 | 0.5283 | 0.0060 | 0.6303 | 4.3655 |
| spread | standard_spread_5src_legacy_v1 | THU_2PM_ET | 3 | 1079 | 573-492-14 | 0.5380 | 0.0303 | 1.6427 | 5.0075 |
| spread | standard_spread_5src_legacy_v1 | TUE_2PM_ET | 3 | 1015 | 537-467-11 | 0.5349 | 0.0258 | 1.5429 | 4.9798 |
| spread | standard_spread_5src_legacy_v1 | WED_2PM_ET | 3 | 1040 | 545-486-9 | 0.5286 | 0.0140 | 1.5356 | 4.9837 |
| total | total_sp50_massey50_v1 | CLOSE | 3 | 1726 | 911-797-18 | 0.5334 | 0.0181 | 0.0000 | 5.5657 |
| total | total_sp50_massey50_v1 | SUN_2PM_ET | 3 | 661 | 377-281-3 | 0.5729 | 0.0934 | 0.5136 | 4.9118 |
| total | total_sp50_massey50_v1 | SUN_9AM_ET | 3 | 455 | 250-204-1 | 0.5507 | 0.0511 | 0.4967 | 4.9430 |
| total | total_sp50_massey50_v1 | SUN_9PM_ET | 3 | 1560 | 835-720-5 | 0.5370 | 0.0251 | 0.3413 | 5.2908 |
| total | standard_total_40_40_20_sagarin_legacy_v1 | CLOSE | 3 | 1104 | 590-503-11 | 0.5398 | 0.0302 | 0.0000 | 5.5092 |
| total | standard_total_40_40_20_sagarin_legacy_v1 | SUN_2PM_ET | 3 | 397 | 233-163-1 | 0.5884 | 0.1230 | 0.8615 | 5.0141 |
| total | standard_total_40_40_20_sagarin_legacy_v1 | SUN_9AM_ET | 3 | 259 | 149-110-0 | 0.5753 | 0.0983 | 1.0425 | 5.0474 |
| total | standard_total_40_40_20_sagarin_legacy_v1 | SUN_9PM_ET | 3 | 1017 | 565-446-6 | 0.5589 | 0.0665 | 0.3928 | 5.1257 |

## Sunday 9 AM 3+

| market | model_id | checkpoint | threshold | n | record | win_pct | roi | avg_clv | avg_edge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spread | standard_spread_4src_equal_v1 | SUN_9AM_ET | 3 | 324 | 193-130-1 | 0.5975 | 0.1385 | 1.4028 | 4.4086 |
| spread | standard_spread_5src_legacy_v1 | SUN_9AM_ET | 3 | 287 | 164-122-1 | 0.5734 | 0.0913 | 1.3380 | 4.3753 |
| total | total_sp50_massey50_v1 | SUN_9AM_ET | 3 | 455 | 250-204-1 | 0.5507 | 0.0511 | 0.4967 | 4.9430 |
| total | standard_total_40_40_20_sagarin_legacy_v1 | SUN_9AM_ET | 3 | 259 | 149-110-0 | 0.5753 | 0.0983 | 1.0425 | 5.0474 |

## Comparison and decay

The independent four-source and five-source tables remain valid descriptions of each model's own signals. Head-to-head claims must use `spread_common_sample_comparison.csv`, which contains four-source-selected, five-source-selected, intersection, and union cohorts. Matched decay uses the original selected team at every later checkpoint and records threshold persistence, positive-edge persistence, same-side status, and reversal.

## Totals

Over CLV is `closing total - entry total`; Under CLV is `entry total - closing total`. Existing Total rows passed side, grading, threshold, duplicate, and extreme-value review. No Tuesday-Friday Total history was fabricated.

## Prediction-first selection

The OOS MAE selection remains `spread_4src_25_25_25_25_v1` for Spread and `total_sp50_massey50_v1` for Total. Betting analytics corrections do not alter that prediction-first decision.

## Provenance limitations

Friday remains `RETROSPECTIVE_TIMING_UNVERIFIED`; Friday 2021 remains unavailable. Small tail rows remain visible but are classified by sample strength. DRatings Total history remains limited and is not treated as equivalent to the full historical Total cohorts.
