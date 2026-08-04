# Postgame PBP -> next market rating update

Target: team-perspective innovation in its next closing spread after removing 2.5 points of home field and both teams' rolling six-week market ratings. Garbage-time-filtered PBP is tested incrementally over final score and the prior closing spread. Development is 2021-23; 2024 is validation; 2025 remains untouched unless the frozen validation rule passes.

```json
{
  "design": {
    "development": "2021-2023",
    "validation": "2024",
    "holdout": "2025 untouched unless validation passes",
    "hfa": 2.5,
    "rating_window_weeks": 6,
    "rating_ridge": 8.0,
    "model_ridge": 20.0
  },
  "score_only": {
    "n": 1361,
    "baseline_mae": 7.429532217849789,
    "model_mae": 6.937085470307228,
    "mae_improvement_pct": 6.6282335563393175,
    "direction_accuracy": 0.6252755326965467,
    "prediction_target_correlation": 0.3876001736657347
  },
  "score_plus_pbp": {
    "n": 1361,
    "baseline_mae": 7.429532217849789,
    "model_mae": 6.913306637064534,
    "mae_improvement_pct": 6.948291839222388,
    "direction_accuracy": 0.6267450404114622,
    "prediction_target_correlation": 0.3977211932770506
  },
  "pbp_incremental_mae_vs_score_pct": 0.3427784383582254,
  "validation_pass": true,
  "holdout_2025_score_only": {
    "n": 1385,
    "baseline_mae": 7.854020370685854,
    "model_mae": 7.3555114694666655,
    "mae_improvement_pct": 6.3471811593436955,
    "direction_accuracy": 0.6180505415162455,
    "prediction_target_correlation": 0.35247677631416713
  },
  "holdout_2025_score_plus_pbp": {
    "n": 1385,
    "baseline_mae": 7.854020370685854,
    "model_mae": 7.392681463978709,
    "mae_improvement_pct": 5.8739204246150685,
    "direction_accuracy": 0.628158844765343,
    "prediction_target_correlation": 0.344526681216076
  },
  "holdout_2025_pbp_incremental_mae_vs_score_pct": -0.505335280440246,
  "holdout_pass": false
}
```
