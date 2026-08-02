# War Room data inventory

The isolated War Room prototype uses existing repository fixtures only. It does not call providers, mutate canonical data, or replace the canonical homepage. The upcoming focus is the lowest uncompleted canonical week in `matchups_view.json`, rather than an artificial “today” state.

| War Room section | Artifact | Fields used | Current readiness | Important limitation |
|---|---|---|---|---|
| System pulse | `data/site/page_health_status.json` | `pages[].status`, `status_label`, `metrics`, timestamps | Ready | Last completed daily-run status is unavailable in the source fixture. |
| Upcoming briefing | `data/site/matchups_view.json` | game week/status, teams, ranks, model, market | Ready | FCS matchups may lack model/rank coverage and are counted honestly. |
| Spread opportunities | `data/site/matchups_view.json` | model home spread, current market home spread | Ready | A raw model-market gap is value context, not confidence or a bet recommendation. |
| Total opportunities | `data/site/matchups_view.json` | model total, current market total | Ready | Same limitation as spreads; no result certainty is implied. |
| Futures opportunities | `data/site/futures_view.json` | model/market probabilities and edges | Partial | Futures feeds are currently stale/partial; displayed with warning. |
| Market inefficiencies | `data/site/odds_screen_v2.json` | multi-book spread/total quotes | Ready | Cross-book range is a shopping signal, not a model edge. |
| Model disagreement | `data/site/ratings_view.json` | source variance, high/low source | Ready | Source variance indicates uncertainty only. |
| Featured games | `data/site/matchups_view.json`, `data/history/game_line_model_history.csv` | edges, ranks, history, team/model context | Ready | Selection deliberately mixes five different rules instead of repeating “largest edge.” |
| Model performance | `data/site/model_performance_view.json` | status, predictions, settled records | Inactive | 2026 tracking is explicitly preseason-not-started; no record is fabricated. |
| Futures/simulation pulse | `data/site/playoff_model_2026.json`, `data/site/futures_view.json` | trials, playoff/title probabilities, market counts | Partial | Simulations exist, but current futures freshness remains a warning. |
| Ratings/market pulse | `data/site/ratings_view.json` | composite rank, market rank/delta, source meta | Ready | Market-Derived Ratings remain separate from the production composite. |
| Open positions count | `data/site/betting_activity_view.json` | owned open count | Ready | Individual wagers are intentionally not shown on the homepage. |
| Injury context | `data/injuries/injury_alerts.csv` | row availability | Inactive | No actionable reports have been released; this does not mean there are no injuries. |
| Explore navigation | `data/site/page_health_status.json` and canonical HTML files | URL, status, first metric | Ready | Team page is intentionally outside the current 11-page health registry. |

## Currently unavailable or intentionally omitted

- Settled 2026 ATS, totals, ROI, and CLV performance: tracking has not started.
- A trustworthy “today” slate: the fixture is preseason, so the prototype leads with upcoming Week 0.
- Actionable injuries: current injury source state is unreleased, not zero injuries.
- Personalized teams, watchlists, and alerts: reserved for a later account/personalization phase.
- A standalone opportunity score combining market edges, injuries, and schedule context: not supported by an approved shared definition and therefore not invented.
- Individual open wagers: intentionally excluded from homepage scope.

## Selection and provenance rules

- Spread value requires at least a two-point absolute model-market gap.
- Total value requires at least a three-point absolute model-market gap.
- Futures value is ranked by positive model probability minus market implied probability.
- Market inefficiency is a cross-book line range and remains separate from model opportunity.
- Featured games use distinct reasons: largest edge, ranked relevance, cross-book disagreement, retained market history, and uncertainty.
- Every detail link resolves to an existing canonical page; the prototype itself remains at `build/war_room_preview/index.html`.
