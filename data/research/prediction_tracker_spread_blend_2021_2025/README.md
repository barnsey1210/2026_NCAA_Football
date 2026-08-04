# Prediction Tracker spread blend

Weights were selected only on 2021-23 using contemporaneous game predictions, validated on 2024, and then evaluated on untouched 2025. The opening-line model is market-informed; the midweek model is included only as a timing benchmark and is not an early-week forecast.

```json
{
  "design": {
    "development": "2021-23",
    "validation": "2024",
    "holdout": "2025 untouched",
    "weight_grid": "nonnegative, sum to 1, 5-point increments",
    "line_convention": "positive means home favored"
  },
  "models": {
    "external_only": {
      "columns": [
        "lineespn",
        "lineteamrank",
        "linesagpred",
        "linemass"
      ],
      "weights": {
        "lineespn": 0.45,
        "lineteamrank": 0.4,
        "linesagpred": 0.0,
        "linemass": 0.15
      },
      "development_actual_margin": {
        "n": 2331,
        "mae": 12.534745817245817,
        "rmse": 15.726456362740892,
        "bias": 0.4468359073359074,
        "winner_accuracy": 0.7155727155727156
      },
      "development_closing_line": {
        "n": 2331,
        "mae": 2.531677606177606,
        "rmse": 3.2631572564709517,
        "bias": 0.11350257400257407,
        "winner_accuracy": 0.9210639210639211
      },
      "validation_actual_margin": {
        "n": 798,
        "mae": 12.36923746867168,
        "rmse": 15.586604914708994,
        "bias": -0.3164179197994986,
        "winner_accuracy": 0.7155388471177945
      },
      "validation_closing_line": {
        "n": 798,
        "mae": 2.5227562656641607,
        "rmse": 3.2185128277464456,
        "bias": 0.26127631578947386,
        "winner_accuracy": 0.9060150375939849
      },
      "holdout_actual_margin": {
        "n": 761,
        "mae": 12.08031800262812,
        "rmse": 15.343950456890875,
        "bias": -0.7603718791064389,
        "winner_accuracy": 0.7371879106438897
      },
      "holdout_closing_line": {
        "n": 761,
        "mae": 2.0942969776609726,
        "rmse": 2.637277169093697,
        "bias": -0.07508935611038095,
        "winner_accuracy": 0.9211563731931669
      }
    },
    "external_plus_open": {
      "columns": [
        "lineespn",
        "lineteamrank",
        "linesagpred",
        "linemass",
        "lineopen"
      ],
      "weights": {
        "lineespn": 0.1,
        "lineteamrank": 0.0,
        "linesagpred": 0.0,
        "linemass": 0.0,
        "lineopen": 0.9
      },
      "development_actual_margin": {
        "n": 2331,
        "mae": 12.310483912483914,
        "rmse": 15.477431690913377,
        "bias": 0.3461870441870444,
        "winner_accuracy": 0.7207207207207207
      },
      "development_closing_line": {
        "n": 2331,
        "mae": 1.4696241956241956,
        "rmse": 2.2587302065231576,
        "bias": 0.012853710853710962,
        "winner_accuracy": 0.9485199485199485
      },
      "validation_actual_margin": {
        "n": 798,
        "mae": 12.21514536340852,
        "rmse": 15.42834866621882,
        "bias": -0.45518295739348363,
        "winner_accuracy": 0.7117794486215538
      },
      "validation_closing_line": {
        "n": 798,
        "mae": 1.3800075187969927,
        "rmse": 1.9144416096323569,
        "bias": 0.12251127819548883,
        "winner_accuracy": 0.943609022556391
      },
      "holdout_actual_margin": {
        "n": 761,
        "mae": 11.896411300919844,
        "rmse": 15.149643723015302,
        "bias": -0.5843929040735872,
        "winner_accuracy": 0.7450722733245729
      },
      "holdout_closing_line": {
        "n": 761,
        "mae": 1.3237936925098555,
        "rmse": 2.101307850988401,
        "bias": 0.1008896189224706,
        "winner_accuracy": 0.961892247043364
      }
    },
    "external_plus_midweek": {
      "columns": [
        "lineespn",
        "lineteamrank",
        "linesagpred",
        "linemass",
        "linemidweek"
      ],
      "weights": {
        "lineespn": 0.0,
        "lineteamrank": 0.0,
        "linesagpred": 0.0,
        "linemass": 0.0,
        "linemidweek": 1.0
      },
      "development_actual_margin": {
        "n": 2331,
        "mae": 12.265122265122265,
        "rmse": 15.400850177382617,
        "bias": 0.32775632775632774,
        "winner_accuracy": 0.7228657228657228
      },
      "development_closing_line": {
        "n": 2331,
        "mae": 0.4092664092664093,
        "rmse": 0.8092398623826899,
        "bias": -0.005577005577005577,
        "winner_accuracy": 0.9828399828399829
      },
      "validation_actual_margin": {
        "n": 798,
        "mae": 12.084586466165414,
        "rmse": 15.375266161072124,
        "bias": -0.4956140350877193,
        "winner_accuracy": 0.7167919799498746
      },
      "validation_closing_line": {
        "n": 798,
        "mae": 0.5845864661654135,
        "rmse": 0.9750971932791378,
        "bias": 0.08208020050125313,
        "winner_accuracy": 0.9774436090225563
      },
      "holdout_actual_margin": {
        "n": 761,
        "mae": 11.992115637319317,
        "rmse": 15.482069659645752,
        "bias": -0.7726675427069645,
        "winner_accuracy": 0.7437582128777924
      },
      "holdout_closing_line": {
        "n": 761,
        "mae": 0.5670170827858082,
        "rmse": 3.477211337543284,
        "bias": -0.0873850197109067,
        "winner_accuracy": 0.9816031537450722
      }
    }
  },
  "equal_external_benchmark": {
    "validation_actual_margin": {
      "n": 798,
      "mae": 12.365059523809524,
      "rmse": 15.573713878849295,
      "bias": -0.2717888471177946,
      "winner_accuracy": 0.7105263157894737
    },
    "validation_closing_line": {
      "n": 798,
      "mae": 2.4226785714285715,
      "rmse": 3.1066834244999373,
      "bias": 0.305905388471178,
      "winner_accuracy": 0.9135338345864662
    },
    "holdout_actual_margin": {
      "n": 761,
      "mae": 12.040972404730619,
      "rmse": 15.326778527452086,
      "bias": -0.35734559789750336,
      "winner_accuracy": 0.7371879106438897
    },
    "holdout_closing_line": {
      "n": 761,
      "mae": 2.141938239159001,
      "rmse": 2.709650602867263,
      "bias": 0.3279369250985545,
      "winner_accuracy": 0.9290407358738502
    }
  }
}
```
