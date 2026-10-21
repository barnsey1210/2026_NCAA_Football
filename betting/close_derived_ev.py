#!/usr/bin/env python3
"""Canonical close-derived expected value for settled NCAAF wagers."""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from betting.key_aware_spread_ev import SpreadEVCalculator, american_profit, num
from lib.ncaaf_config import canonical_team

ASSUMED_COUNTERPART_PRICE = -110.0
TOTAL_EXACT_PRIOR_N = 100.0
TOTAL_PUSH_PRIOR_N = 200.0
TEAM_TOTAL_CENTS_PER_HALF = 10.0
ACTION_BOOK_IDS = {
    "DraftKings": "2031", "FanDuel": "2028", "BetMGM": "1665", "MGM": "1665",
    "Caesars": "2029", "Caesers": "2029",
}


def team_name(value):
    return canonical_team(str(value or "").replace("Hawai'i", "Hawaii"))


def team_key(value):
    return team_name(value).casefold()


def implied_probability(price):
    price = num(price)
    if price is None or price == 0:
        return None
    return 100.0 / (price + 100.0) if price > 0 else abs(price) / (abs(price) + 100.0)


def fair_probability(selected_price, opposite_price):
    selected = implied_probability(selected_price)
    opposite = implied_probability(opposite_price)
    if selected is None or opposite is None or selected + opposite <= 0:
        return None
    return selected / (selected + opposite)


def fair_american(p):
    if p is None or not 0 < p < 1:
        return None
    return -100.0 * p / (1.0 - p) if p >= 0.5 else 100.0 * (1.0 - p) / p


def ev_result(ticket_price, risk, p_win, p_loss, p_push=0.0, **meta):
    profit = american_profit(ticket_price)
    if profit is None:
        return None
    ev = p_win * profit - p_loss
    return {
        "close_ev_pct": ev,
        "close_ev_expected_pl": (risk or 0.0) * ev,
        "close_ev_fair_probability": p_win / (p_win + p_loss) if p_win + p_loss else None,
        "close_ev_fair_price": fair_american(p_win / (p_win + p_loss)) if p_win + p_loss else None,
        "close_ev_win_probability": p_win,
        "close_ev_loss_probability": p_loss,
        "close_ev_push_probability": p_push,
        **meta,
    }


def outcome(actual, line, side):
    value = actual - line if side == "Over" else line - actual
    return (1.0, 0.0, 0.0) if value > 1e-9 else (0.0, 1.0, 0.0) if value < -1e-9 else (0.0, 0.0, 1.0)


class TotalCurve:
    def __init__(self, path):
        self.rows = []
        self.by_close = defaultdict(list)
        with Path(path).open(newline="") as handle:
            for row in csv.DictReader(handle):
                close, actual = num(row.get("closing_total")), num(row.get("actual_total"))
                if close is not None and actual is not None:
                    self.rows.append((close, actual))
                    self.by_close[round(close * 2) / 2].append(actual)
        if not self.rows:
            raise RuntimeError("Total EV calibration has no rows")
        self.global_push = sum(abs(a - c) < 1e-9 for c, a in self.rows) / len(self.rows)

    @staticmethod
    def means(actuals, reference, ticket, side):
        base, target = [outcome(a, reference, side) for a in actuals], [outcome(a, ticket, side) for a in actuals]
        return tuple(sum(v[i] for v in base) / len(base) for i in range(3)), tuple(sum(v[i] for v in target) / len(target) for i in range(3))

    def probabilities(self, reference, ticket, side, conditional_win):
        reference, ticket = round(reference * 2) / 2, round(ticket * 2) / 2
        exact = self.by_close.get(reference, [])
        pushes = sum(abs(a - reference) < 1e-9 for a in exact)
        push = (pushes + TOTAL_PUSH_PRIOR_N * self.global_push) / (len(exact) + TOTAL_PUSH_PRIOR_N)
        base = ((1 - push) * conditional_win, (1 - push) * (1 - conditional_win), push)
        pooled = [reference + actual - close for close, actual in self.rows]
        pr, pt = self.means(pooled, reference, ticket, side)
        pooled_delta = tuple(pt[i] - pr[i] for i in range(3))
        if exact:
            er, et = self.means(exact, reference, ticket, side)
            exact_delta = tuple(et[i] - er[i] for i in range(3))
            weight = len(exact) / (len(exact) + TOTAL_EXACT_PRIOR_N)
        else:
            exact_delta, weight = pooled_delta, 0.0
        delta = tuple(weight * exact_delta[i] + (1 - weight) * pooled_delta[i] for i in range(3))
        values = [max(0.0, base[i] + delta[i]) for i in range(3)]
        scale = sum(values)
        return tuple(v / scale for v in values), len(exact)


class CloseDerivedEV:
    def __init__(self, root, games):
        self.root = Path(root)
        self.spread = SpreadEVCalculator(root)
        self.total = TotalCurve(self.root / "data/research/historical_totals/master_totals_game_matrix_2021_2025.csv")
        self.games = games
        self.action = self._load_action()

    def _load_action(self):
        index = {}
        for path in sorted((self.root / "data/odds/actionnetwork_scoreboard_raw").glob("week_*.json")):
            payload = json.loads(path.read_text())
            for game in payload.get("games", []):
                teams = {str(t.get("id")): team_name(t.get("location") or t.get("display_name")) for t in game.get("teams", [])}
                away, home = teams.get(str(game.get("away_team_id"))), teams.get(str(game.get("home_team_id")))
                if away and home:
                    index[(away.casefold(), home.casefold())] = (game, teams)
        return index

    def _action_game(self, game, selection, week):
        if game:
            found = self.action.get((team_key(game.get("away_team")), team_key(game.get("home_team"))))
            if found:
                return found
        team = team_key(re.sub(r"\bTT\b.*$", "", selection or "", flags=re.I).strip())
        candidates = []
        for canonical_game in self.games:
            if week is not None and int(canonical_game.get("week") or -1) != int(week):
                continue
            if team in {team_key(canonical_game.get("away_team")), team_key(canonical_game.get("home_team"))}:
                found = self.action.get((team_key(canonical_game.get("away_team")), team_key(canonical_game.get("home_team"))))
                if found:
                    candidates.append(found)
        return candidates[0] if len(candidates) == 1 else None

    @staticmethod
    def _paired(event, market, selected_side=None, team_id=None):
        outcomes = event.get(market) or []
        if isinstance(outcomes, dict):
            outcomes = [outcomes]
        if team_id is not None:
            outcomes = [o for o in outcomes if str(o.get("team_id")) == str(team_id)]
        selected = next((o for o in outcomes if selected_side is None or o.get("side") == selected_side), None)
        opposite = next((o for o in outcomes if selected and o is not selected and o.get("market_id") == selected.get("market_id")), None)
        return selected, opposite

    def price(self, wager, game=None):
        base = {
            "close_ev_pct": None, "close_ev_expected_pl": None, "close_ev_fair_probability": None,
            "close_ev_fair_price": None, "close_ev_win_probability": None, "close_ev_loss_probability": None,
            "close_ev_push_probability": None, "close_ev_method": "pending" if wager.get("is_open") else "unsupported_na",
            "close_ev_status": "PENDING" if wager.get("is_open") else "N/A", "close_ev_provenance": None,
        }
        if wager.get("is_open") or not wager.get("is_graded"):
            return base
        risk, ticket_price = num(wager.get("settled_risk") or wager.get("stake")), num(wager.get("price"))
        if not risk or ticket_price is None:
            return base
        selection, market = wager.get("selection") or "", wager.get("market")
        is_team_total = bool(re.search(r"\bTT\b|team total", selection, re.I))

        if market == "Spread" and wager.get("closing_clv_frozen") and num(wager.get("closing_market_line")) is not None:
            probs = self.spread.ticket_probabilities(wager["closing_market_line"], wager["line"])
            conditional = fair_probability(wager.get("closing_market_price"), ASSUMED_COUNTERPART_PRICE)
            if probs and conditional is not None:
                shift = (conditional - .5) * (1 - probs["push_probability"])
                pw, pl, pp = probs["win_probability"] + shift, probs["loss_probability"] - shift, probs["push_probability"]
                return ev_result(ticket_price, risk, pw, pl, pp, close_ev_method="spread_curve", close_ev_status="RESOLVED", close_ev_provenance="canonical_frozen_close; ncaaf_key_aware_2021_2025; opposite_price_assumption=-110")

        if market == "Game Total" and not is_team_total and wager.get("closing_clv_frozen") and num(wager.get("closing_market_line")) is not None:
            side = str(wager.get("side") or "").title()
            conditional = fair_probability(wager.get("closing_market_price"), ASSUMED_COUNTERPART_PRICE)
            if side in {"Over", "Under"} and conditional is not None:
                (pw, pl, pp), sample = self.total.probabilities(wager["closing_market_line"], wager["line"], side, conditional)
                return ev_result(ticket_price, risk, pw, pl, pp, close_ev_method="total_curve", close_ev_status="RESOLVED", close_ev_provenance=f"canonical_frozen_close; ncaaf_total_curve_2021_2025; exact_close_n={sample}; opposite_price_assumption=-110")

        action = self._action_game(game, selection, wager.get("week"))
        book_id = ACTION_BOOK_IDS.get(wager.get("sportsbook"))
        if action and book_id:
            action_game, teams = action
            event = (((action_game.get("markets") or {}).get(book_id) or {}).get("event") or {})
            if market == "Moneyline":
                selected_team = team_key(wager.get("team") or selection)
                team_id = next((tid for tid, name in teams.items() if name.casefold() == selected_team), None)
                outcomes = event.get("moneyline") or []
                selected = next((o for o in outcomes if str(o.get("team_id")) == str(team_id)), None)
                opposite = next((o for o in outcomes if selected and o is not selected and o.get("market_id") == selected.get("market_id")), None)
                if selected and opposite:
                    p = fair_probability(selected.get("odds"), opposite.get("odds"))
                    return ev_result(ticket_price, risk, p, 1 - p, close_ev_method="moneyline_devig", close_ev_status="RESOLVED", close_ev_provenance=f"Action Network completed-game paired close; book_id={book_id}; market_id={selected.get('market_id')}; selected={selected.get('odds')}; opposite={opposite.get('odds')}", close_ev_market_line=0, close_ev_market_price=selected.get("odds"), close_ev_market_opposite_price=opposite.get("odds"), close_ev_market_book=wager.get("sportsbook"))
            if is_team_total:
                selected_team_name = team_key(re.sub(r"\bTT\b.*$", "", selection, flags=re.I).strip())
                team_id = next((tid for tid, name in teams.items() if name.casefold() == selected_team_name), None)
                side = "over" if "over" in selection.lower() or re.search(r"\bO\s*\d", selection, re.I) else "under"
                selected, opposite = self._paired(event, "core_bet_type_6_team_score", side, team_id)
                if selected and opposite:
                    p0 = fair_probability(selected.get("odds"), opposite.get("odds"))
                    close_line, ticket_line = num(selected.get("value")), num(wager.get("line"))
                    if p0 is not None and close_line is not None and ticket_line is not None:
                        favorable = close_line - ticket_line if side == "over" else ticket_line - close_line
                        steps = max(0, round(favorable * 2))
                        fair0 = fair_american(p0)
                        adjusted = -(100 + max(0, abs(fair0) - 100) + TEAM_TOTAL_CENTS_PER_HALF * steps) if steps else fair0
                        p = implied_probability(adjusted)
                        return ev_result(ticket_price, risk, p, 1 - p, close_ev_method="team_total_estimated" if steps else "team_total_devig", close_ev_status="ESTIMATED" if steps else "RESOLVED", close_ev_provenance=f"Action Network completed-game paired close; book_id={book_id}; market_id={selected.get('market_id')}; cents_per_half={TEAM_TOTAL_CENTS_PER_HALF}; steps={steps}", close_ev_market_line=close_line, close_ev_market_price=selected.get("odds"), close_ev_market_opposite_price=opposite.get("odds"), close_ev_market_book=wager.get("sportsbook"))
        return base


def aggregate_ev(rows):
    eligible = [r for r in rows if r.get("close_ev_pct") is not None and num(r.get("settled_risk") or r.get("stake"))]
    risk = sum(num(r.get("settled_risk") or r.get("stake")) for r in eligible)
    expected_pl = sum(num(r.get("close_ev_expected_pl")) or 0 for r in eligible)
    realized_pl = sum(num(r.get("realized_pl") or r.get("realized_profit")) or 0 for r in eligible)
    return {
        "close_ev_eligible": len(eligible), "close_ev_risk": round(risk, 2),
        "close_ev_expected_pl": round(expected_pl, 2),
        "close_ev_roi": round(expected_pl / risk, 4) if risk else None,
        "close_ev_realized_pl": round(realized_pl, 2),
        "close_ev_realized_roi": round(realized_pl / risk, 4) if risk else None,
        "close_ev_actual_vs_expected": round((realized_pl - expected_pl) / risk, 4) if risk else None,
    }
