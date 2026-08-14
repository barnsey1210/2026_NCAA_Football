# Shadow Model Performance UI Plan

## Scope

This note defines the next UI task only. The current contract task does not alter HTML, page builders, or the existing Standard Models experience.

## Component hierarchy

Use a compact two-tab hierarchy inside the existing Model Performance area:

```text
Model Performance
├── Standard Models (existing content unchanged)
└── Shadow Models
    ├── Historical Shadow Spread Validation
    ├── Historical Shadow Totals Validation
    ├── Stale vs Shadow Model Quality
    └── What is Shadow? (small optional explainer)
```

The Shadow tab's first row should contain the spread and totals validation cards. A smaller stale-versus-Shadow quality card should sit below them. The explainer should be compact and collapsible if existing components support that behavior.

## Reuse

Reuse the existing Model Performance card, table, status-badge, metric, and tab styling. No new page, route, source-selection pipeline, or independent research calculation is needed. The page adapter should only format `data/site/shadow_model_performance.json`.

Keep Standard Models mounted or rendered exactly as today when selected. Shadow content should be hidden when Standard Models is active so it does not materially increase the default page height.

## Next implementation boundaries

The next task should modify only the canonical Model Performance page adapter/template and its focused validation coverage. It should:

1. load `data/site/shadow_model_performance.json` alongside the existing standard contract;
2. add the Standard Models / Shadow Models tab control;
3. render the three Shadow sections from contract fields without recalculating statistics;
4. display the contract disclaimer that labels are not automatic betting rules;
5. preserve the totals `WATCH / RESEARCH` status and avoid actionable/strong-bet language;
6. add missing-artifact and invalid-schema fallback states;
7. add the new artifact to the explicit public manifest only when UI integration is authorized;
8. extend propagation and public-site validation before publication.
