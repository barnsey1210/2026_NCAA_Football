import unittest

import pandas as pd

from scripts.history.build_matchup_line_history_clean import build_chart


class IncrementalLineHistoryTests(unittest.TestCase):
    def test_affected_game_merge_equals_clean_full_rebuild(self):
        columns = {
            "source_file": "data/odds/game_book_line_history.csv",
            "source": "The Odds API",
            "game_date": "2026-09-05",
            "week": 1,
            "conference": "Test",
            "away_team": "Away",
            "home_team": "Home",
            "market_spread_open_home": None,
            "market_spread_text": None,
            "market_spread_price": -110,
            "market_spread_book": "DraftKings",
            "market_spread_last_update": None,
            "market_total_open": None,
            "market_total_book": "DraftKings",
            "market_total_over_price": -110,
            "market_total_under_price": -110,
            "market_total_last_update": None,
            "projected_margin_home": None,
            "model_spread_home": None,
            "projected_total": None,
            "books_available": "DraftKings",
        }
        rows=[]
        for game_id, spread in (("g1",-3.5),("g2",2.5)):
            for day,total in (("2026-08-24",51.5),("2026-08-25",52.0)):
                rows.append({**columns,"game_id":game_id,"snapshot_date":day,
                    "snapshot_ts":day+"T12:00:00Z","market_spread_home":spread,
                    "market_total":total})
        db={"games":[{"game_id":"g1","projected_margin_home":4,"projected_total":53},
                     {"game_id":"g2","projected_margin_home":-2,"projected_total":49}]}
        full=build_chart(db,[pd.DataFrame(rows)]).reset_index(drop=True)
        affected={"g1"}
        rebuilt=build_chart(db,[pd.DataFrame([r for r in rows if r["game_id"] in affected])])
        merged=pd.concat([full[~full.game_id.astype(str).isin(affected)],rebuilt],ignore_index=True)
        merged=merged.sort_values(["game_id","snapshot_date"]).reset_index(drop=True)
        pd.testing.assert_frame_equal(full,merged,check_dtype=False)


if __name__ == "__main__":
    unittest.main()
