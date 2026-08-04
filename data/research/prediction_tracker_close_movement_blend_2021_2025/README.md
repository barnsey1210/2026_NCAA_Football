# Rating-system blend for opener-to-close movement

The opener is market-history data and remains the starting price. FPI, TeamRankings, Sagarin Predictor, and Massey game forecasts are blended to estimate the direction and fraction of convergence by close. Weights were frozen on 2021-23, validated on 2024, and evaluated unchanged on 2025. Prediction Tracker does not timestamp each system forecast, so this supports use once the weekly system forecasts are posted; it does not prove all inputs were available at the Sunday opener.

```json
{
  "design": {
    "development": "2021-23",
    "validation": "2024",
    "holdout": "2025 untouched",
    "target": "Prediction Tracker closing home line",
    "formula": "open + response * (weighted system projection - open)",
    "system_weight_grid": "5-point increments; nonnegative; sums to 1",
    "response_grid": "0.00 to 1.50 in 0.05 increments"
  },
  "selected_weights": {
    "FPI": 0.35,
    "TeamRankings": 0.65,
    "Sagarin Predictor": 0.0,
    "Massey": 0.0
  },
  "selected_response": 0.2,
  "results": {
    "development": {
      "frozen_model": {
        "n": 2331,
        "close_mae": 1.4437835692835692,
        "close_rmse": 2.167628107724589,
        "mean_predicted_move": 0.53863993993994,
        "mean_actual_move": 1.5126555126555126,
        "movement_direction_accuracy_all_moved": 0.6156156156156156,
        "direction_n_all_moved": 1998,
        "movement_direction_accuracy_called": 0.6597122302158274,
        "direction_n_called": 1390
      },
      "opener_no_change": {
        "n": 2331,
        "close_mae": 1.5126555126555126,
        "close_rmse": 2.3753795785996275,
        "mean_predicted_move": 0.0,
        "mean_actual_move": 1.5126555126555126,
        "movement_direction_accuracy_all_moved": 0.0,
        "direction_n_all_moved": 1998,
        "movement_direction_accuracy_called": null,
        "direction_n_called": 0
      },
      "equal_system_full_adjustment": {
        "n": 2331,
        "close_mae": 2.598345130845131,
        "close_rmse": 3.37558232380352,
        "mean_predicted_move": 2.510753968253968,
        "mean_actual_move": 1.5126555126555126,
        "movement_direction_accuracy_all_moved": 0.5815815815815816,
        "direction_n_all_moved": 1998,
        "movement_direction_accuracy_called": 0.5905427189682966,
        "direction_n_called": 1861
      },
      "midweek_timing_benchmark": {
        "n": 2331,
        "close_mae": 0.4092664092664093,
        "close_rmse": 0.8092398623826899,
        "mean_predicted_move": 1.407121407121407,
        "mean_actual_move": 1.5126555126555126,
        "movement_direction_accuracy_all_moved": 0.8918918918918919,
        "direction_n_all_moved": 1998,
        "movement_direction_accuracy_called": 0.9590958019375673,
        "direction_n_called": 1858
      }
    },
    "validation": {
      "frozen_model": {
        "n": 798,
        "close_mae": 1.39484335839599,
        "close_rmse": 1.9010620265253688,
        "mean_predicted_move": 0.499059649122807,
        "mean_actual_move": 1.3991228070175439,
        "movement_direction_accuracy_all_moved": 0.5808823529411765,
        "direction_n_all_moved": 680,
        "movement_direction_accuracy_called": 0.6038961038961039,
        "direction_n_called": 462
      },
      "opener_no_change": {
        "n": 798,
        "close_mae": 1.3991228070175439,
        "close_rmse": 1.9462546771094542,
        "mean_predicted_move": 0.0,
        "mean_actual_move": 1.3991228070175439,
        "movement_direction_accuracy_all_moved": 0.0,
        "direction_n_all_moved": 680,
        "movement_direction_accuracy_called": null,
        "direction_n_called": 0
      },
      "equal_system_full_adjustment": {
        "n": 798,
        "close_mae": 2.4226785714285715,
        "close_rmse": 3.106683424499937,
        "mean_predicted_move": 2.1790758145363407,
        "mean_actual_move": 1.3991228070175439,
        "movement_direction_accuracy_all_moved": 0.5544117647058824,
        "direction_n_all_moved": 680,
        "movement_direction_accuracy_called": 0.5661881977671451,
        "direction_n_called": 627
      },
      "midweek_timing_benchmark": {
        "n": 798,
        "close_mae": 0.5845864661654135,
        "close_rmse": 0.9750971932791378,
        "mean_predicted_move": 1.2644110275689222,
        "mean_actual_move": 1.3991228070175439,
        "movement_direction_accuracy_all_moved": 0.825,
        "direction_n_all_moved": 680,
        "movement_direction_accuracy_called": 0.9136807817589576,
        "direction_n_called": 614
      }
    },
    "holdout": {
      "frozen_model": {
        "n": 761,
        "close_mae": 1.2614076215505914,
        "close_rmse": 1.9481512865523725,
        "mean_predicted_move": 0.44752851511169517,
        "mean_actual_move": 1.3199737187910643,
        "movement_direction_accuracy_all_moved": 0.6059654631083202,
        "direction_n_all_moved": 637,
        "movement_direction_accuracy_called": 0.6826923076923077,
        "direction_n_called": 416
      },
      "opener_no_change": {
        "n": 761,
        "close_mae": 1.3199737187910643,
        "close_rmse": 2.2087955821633867,
        "mean_predicted_move": 0.0,
        "mean_actual_move": 1.3199737187910643,
        "movement_direction_accuracy_all_moved": 0.0,
        "direction_n_all_moved": 637,
        "movement_direction_accuracy_called": null,
        "direction_n_called": 0
      },
      "equal_system_full_adjustment": {
        "n": 761,
        "close_mae": 2.141938239159001,
        "close_rmse": 2.709650602867263,
        "mean_predicted_move": 2.109710906701708,
        "mean_actual_move": 1.3199737187910643,
        "movement_direction_accuracy_all_moved": 0.5934065934065934,
        "direction_n_all_moved": 637,
        "movement_direction_accuracy_called": 0.5916955017301038,
        "direction_n_called": 578
      },
      "midweek_timing_benchmark": {
        "n": 761,
        "close_mae": 0.5670170827858082,
        "close_rmse": 3.477211337543284,
        "mean_predicted_move": 1.3337713534822602,
        "mean_actual_move": 1.3199737187910643,
        "movement_direction_accuracy_all_moved": 0.8712715855572999,
        "direction_n_all_moved": 637,
        "movement_direction_accuracy_called": 0.9536082474226805,
        "direction_n_called": 582
      }
    }
  }
}
```
