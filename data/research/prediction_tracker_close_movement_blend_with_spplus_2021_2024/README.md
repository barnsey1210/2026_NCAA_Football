# Weekly SP+ opener-to-close test

SP+ values are aligned without lookahead: Week W games use the latest ESPN rating table published after Week W-1 or earlier. 2024 is untouched validation because historical weekly 2025 tables are not yet reliably archived.

```json
{
  "design": {
    "development": "2021-2023",
    "validation": "2024 untouched",
    "spplus_timing": "game week W uses latest ESPN snapshot <= W-1",
    "home_field_adjustment": 2.5,
    "target": "closing home line",
    "formula": "open + response * (weighted projection - open)"
  },
  "coverage": {
    "joined_games": 2085,
    "development": 1562,
    "validation_2024": 523,
    "missing_from_full_rows": 1052
  },
  "results": {
    "four_system": {
      "weights": {
        "FPI": 0.4,
        "TeamRankings": 0.6,
        "Sagarin Predictor": 0.0,
        "Massey": 0.0
      },
      "response": 0.15000000000000002,
      "development": {
        "n": 1562,
        "close_mae": 1.4567142125480155,
        "opener_mae": 1.5179257362355953,
        "movement_direction_accuracy_called": 0.6670616113744076,
        "direction_n_called": 844
      },
      "validation_2024": {
        "n": 523,
        "close_mae": 1.3492608030592732,
        "opener_mae": 1.3690248565965584,
        "movement_direction_accuracy_called": 0.6311787072243346,
        "direction_n_called": 263
      }
    },
    "four_system_plus_spplus": {
      "weights": {
        "FPI": 0.4,
        "TeamRankings": 0.6,
        "Sagarin Predictor": 0.0,
        "Massey": 0.0,
        "SP+": 0.0
      },
      "response": 0.15000000000000002,
      "development": {
        "n": 1562,
        "close_mae": 1.4567142125480155,
        "opener_mae": 1.5179257362355953,
        "movement_direction_accuracy_called": 0.6670616113744076,
        "direction_n_called": 844
      },
      "validation_2024": {
        "n": 523,
        "close_mae": 1.3492608030592732,
        "opener_mae": 1.3690248565965584,
        "movement_direction_accuracy_called": 0.6311787072243346,
        "direction_n_called": 263
      }
    }
  }
}
```
