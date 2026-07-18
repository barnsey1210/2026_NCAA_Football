# Weekly SP+ fair-line and opener-to-close test

SP+ values are aligned without lookahead: Week W games use the latest ESPN rating table published after Week W-1 or earlier. Weights and convergence were selected on 2021-23, checked on 2024, and evaluated once on the recovered weekly 2025 archive.

```json
{
  "design": {
    "development": "2021-2023",
    "validation": "2024",
    "holdout": "2025 untouched",
    "spplus_timing": "game week W uses latest ESPN snapshot <= W-1",
    "home_field_adjustment": 2.5,
    "line_convention": "positive means home favored",
    "fair_line_target": "closing home line",
    "movement_formula": "open + response * (independent fair line - open)"
  },
  "coverage": {
    "joined_games": 2580,
    "development": 1562,
    "validation_2024": 523,
    "holdout_2025": 495,
    "missing_from_full_rows": 1318
  },
  "results": {
    "four_system": {
      "fair_line_weights": {
        "FPI": 0.2,
        "TeamRankings": 0.5,
        "Sagarin Predictor": 0.15,
        "Massey": 0.15
      },
      "convergence_response": 0.15000000000000002,
      "development": {
        "fair_line_vs_close": {
          "n": 1562,
          "close_mae": 2.5351654929577463,
          "opener_mae": 1.5179257362355953,
          "movement_direction_accuracy_called": 0.601755786113328,
          "direction_n_called": 1253
        },
        "opening_gap_signal": {
          "eligible_n": 1150,
          "direction_accuracy": 0.6069565217391304,
          "mean_abs_opening_gap": 2.5467307938540333,
          "mean_abs_actual_move": 1.5179257362355953
        },
        "predicted_close": {
          "n": 1562,
          "close_mae": 1.472947999359795,
          "opener_mae": 1.5179257362355953,
          "movement_direction_accuracy_called": 0.6463878326996197,
          "direction_n_called": 789
        }
      },
      "validation_2024": {
        "fair_line_vs_close": {
          "n": 523,
          "close_mae": 2.4450478011472274,
          "opener_mae": 1.3690248565965584,
          "movement_direction_accuracy_called": 0.5752427184466019,
          "direction_n_called": 412
        },
        "opening_gap_signal": {
          "eligible_n": 383,
          "direction_accuracy": 0.5848563968668408,
          "mean_abs_opening_gap": 2.2792141491395794,
          "mean_abs_actual_move": 1.3690248565965584
        },
        "predicted_close": {
          "n": 523,
          "close_mae": 1.3637932122370937,
          "opener_mae": 1.3690248565965584,
          "movement_direction_accuracy_called": 0.6081632653061224,
          "direction_n_called": 245
        }
      },
      "holdout_2025": {
        "fair_line_vs_close": {
          "n": 495,
          "close_mae": 1.9613878787878791,
          "opener_mae": 1.3727272727272728,
          "movement_direction_accuracy_called": 0.6230366492146597,
          "direction_n_called": 382
        },
        "opening_gap_signal": {
          "eligible_n": 355,
          "direction_accuracy": 0.6366197183098592,
          "mean_abs_opening_gap": 2.1057191919191918,
          "mean_abs_actual_move": 1.3727272727272728
        },
        "predicted_close": {
          "n": 495,
          "close_mae": 1.330051616161616,
          "opener_mae": 1.3727272727272728,
          "movement_direction_accuracy_called": 0.6666666666666666,
          "direction_n_called": 207
        }
      }
    },
    "four_system_plus_spplus": {
      "fair_line_weights": {
        "FPI": 0.15,
        "TeamRankings": 0.3,
        "Sagarin Predictor": 0.2,
        "Massey": 0.1,
        "SP+": 0.25
      },
      "convergence_response": 0.2,
      "development": {
        "fair_line_vs_close": {
          "n": 1562,
          "close_mae": 2.3616600512163894,
          "opener_mae": 1.5179257362355953,
          "movement_direction_accuracy_called": 0.6203335980937251,
          "direction_n_called": 1259
        },
        "opening_gap_signal": {
          "eligible_n": 1162,
          "direction_accuracy": 0.6256454388984509,
          "mean_abs_opening_gap": 2.45142509603073,
          "mean_abs_actual_move": 1.5179257362355953
        },
        "predicted_close": {
          "n": 1562,
          "close_mae": 1.451840588988476,
          "opener_mae": 1.5179257362355953,
          "movement_direction_accuracy_called": 0.6461366181410975,
          "direction_n_called": 893
        }
      },
      "validation_2024": {
        "fair_line_vs_close": {
          "n": 523,
          "close_mae": 2.4177609942638623,
          "opener_mae": 1.3690248565965584,
          "movement_direction_accuracy_called": 0.5728155339805825,
          "direction_n_called": 412
        },
        "opening_gap_signal": {
          "eligible_n": 388,
          "direction_accuracy": 0.5824742268041238,
          "mean_abs_opening_gap": 2.304944550669216,
          "mean_abs_actual_move": 1.3690248565965584
        },
        "predicted_close": {
          "n": 523,
          "close_mae": 1.3686191204588911,
          "opener_mae": 1.3690248565965584,
          "movement_direction_accuracy_called": 0.6038961038961039,
          "direction_n_called": 308
        }
      },
      "holdout_2025": {
        "fair_line_vs_close": {
          "n": 495,
          "close_mae": 2.01149696969697,
          "opener_mae": 1.3727272727272728,
          "movement_direction_accuracy_called": 0.6096256684491979,
          "direction_n_called": 374
        },
        "opening_gap_signal": {
          "eligible_n": 343,
          "direction_accuracy": 0.6209912536443148,
          "mean_abs_opening_gap": 2.1055474747474747,
          "mean_abs_actual_move": 1.3727272727272728
        },
        "predicted_close": {
          "n": 495,
          "close_mae": 1.3272060606060607,
          "opener_mae": 1.3727272727272728,
          "movement_direction_accuracy_called": 0.6377952755905512,
          "direction_n_called": 254
        }
      }
    },
    "equal_fpi_teamrankings_spplus": {
      "fair_line_weights": "equal",
      "convergence_response": 0.2,
      "development": {
        "fair_line_vs_close": {
          "n": 1562,
          "close_mae": 2.520926163038839,
          "opener_mae": 1.5179257362355953,
          "movement_direction_accuracy_called": 0.6384676775738228,
          "direction_n_called": 1253
        },
        "opening_gap_signal": {
          "eligible_n": 1170,
          "direction_accuracy": 0.6452991452991453,
          "mean_abs_opening_gap": 2.6916944088775074,
          "mean_abs_actual_move": 1.5179257362355953
        },
        "predicted_close": {
          "n": 1562,
          "close_mae": 1.43339052496799,
          "opener_mae": 1.5179257362355953,
          "movement_direction_accuracy_called": 0.6666666666666666,
          "direction_n_called": 942
        }
      },
      "validation_2024": {
        "fair_line_vs_close": {
          "n": 523,
          "close_mae": 2.6898024219247927,
          "opener_mae": 1.3690248565965584,
          "movement_direction_accuracy_called": 0.5734597156398105,
          "direction_n_called": 422
        },
        "opening_gap_signal": {
          "eligible_n": 392,
          "direction_accuracy": 0.5790816326530612,
          "mean_abs_opening_gap": 2.6108476736775015,
          "mean_abs_actual_move": 1.3690248565965584
        },
        "predicted_close": {
          "n": 523,
          "close_mae": 1.3699222434671767,
          "opener_mae": 1.3690248565965584,
          "movement_direction_accuracy_called": 0.60625,
          "direction_n_called": 320
        }
      },
      "holdout_2025": {
        "fair_line_vs_close": {
          "n": 495,
          "close_mae": 2.1853535353535354,
          "opener_mae": 1.3727272727272728,
          "movement_direction_accuracy_called": 0.6111111111111112,
          "direction_n_called": 378
        },
        "opening_gap_signal": {
          "eligible_n": 353,
          "direction_accuracy": 0.6175637393767706,
          "mean_abs_opening_gap": 2.382053872053872,
          "mean_abs_actual_move": 1.3727272727272728
        },
        "predicted_close": {
          "n": 495,
          "close_mae": 1.3054909090909093,
          "opener_mae": 1.3727272727272728,
          "movement_direction_accuracy_called": 0.6534296028880866,
          "direction_n_called": 277
        }
      }
    },
    "equal_all_five": {
      "fair_line_weights": "equal",
      "convergence_response": 0.15000000000000002,
      "development": {
        "fair_line_vs_close": {
          "n": 1562,
          "close_mae": 2.4138604353393083,
          "opener_mae": 1.5179257362355953,
          "movement_direction_accuracy_called": 0.6092233009708737,
          "direction_n_called": 1236
        },
        "opening_gap_signal": {
          "eligible_n": 1138,
          "direction_accuracy": 0.6151142355008787,
          "mean_abs_opening_gap": 2.4405877080665817,
          "mean_abs_actual_move": 1.5179257362355953
        },
        "predicted_close": {
          "n": 1562,
          "close_mae": 1.4736444942381561,
          "opener_mae": 1.5179257362355953,
          "movement_direction_accuracy_called": 0.6512820512820513,
          "direction_n_called": 780
        }
      },
      "validation_2024": {
        "fair_line_vs_close": {
          "n": 523,
          "close_mae": 2.3745850860420648,
          "opener_mae": 1.3690248565965584,
          "movement_direction_accuracy_called": 0.5783132530120482,
          "direction_n_called": 415
        },
        "opening_gap_signal": {
          "eligible_n": 389,
          "direction_accuracy": 0.5809768637532133,
          "mean_abs_opening_gap": 2.230630975143403,
          "mean_abs_actual_move": 1.3690248565965584
        },
        "predicted_close": {
          "n": 523,
          "close_mae": 1.3594160611854684,
          "opener_mae": 1.3690248565965584,
          "movement_direction_accuracy_called": 0.5968992248062015,
          "direction_n_called": 258
        }
      },
      "holdout_2025": {
        "fair_line_vs_close": {
          "n": 495,
          "close_mae": 1.9796080808080807,
          "opener_mae": 1.3727272727272728,
          "movement_direction_accuracy_called": 0.5910290237467019,
          "direction_n_called": 379
        },
        "opening_gap_signal": {
          "eligible_n": 345,
          "direction_accuracy": 0.6115942028985507,
          "mean_abs_opening_gap": 2.0558262626262627,
          "mean_abs_actual_move": 1.3727272727272728
        },
        "predicted_close": {
          "n": 495,
          "close_mae": 1.3370854545454545,
          "opener_mae": 1.3727272727272728,
          "movement_direction_accuracy_called": 0.6368159203980099,
          "direction_n_called": 201
        }
      }
    }
  }
}
```
