#!/usr/bin/env python3
"""Production key-aware NCAAF spread EV calculator.

Runtime dependency:
    data/site/ncaaf_spread_half_point_values_2021_2025.json

The historical matrix and research CSVs are calibration inputs only and are
not required by the production runtime.
"""
from __future__ import annotations

import json
import math
from pathlib import Path


def num(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def round_half(value):
    return round(float(value) * 2.0) / 2.0


def american_profit(odds):
    odds = num(odds)

    if odds is None or odds == 0:
        return None

    if odds > 0:
        return odds / 100.0

    return 100.0 / abs(odds)


class SpreadEVCalculator:
    def __init__(self, root):
        self.root = Path(root)

        self.asset_path = (
            self.root
            / "data/site/ncaaf_spread_half_point_values_2021_2025.json"
        )

        if not self.asset_path.exists():
            raise FileNotFoundError(
                f"Missing spread EV calibration asset: {self.asset_path}"
            )

        payload = json.loads(self.asset_path.read_text())
        calibration = payload.get("runtime_calibration") or {}

        raw_push = calibration.get("reference_push_probabilities") or {}
        transition_rows = calibration.get("half_point_transitions") or []
        pooled = calibration.get("pooled_transition") or {}

        if not raw_push:
            raise RuntimeError(
                "Spread EV asset has no reference push probabilities"
            )

        if not transition_rows:
            raise RuntimeError(
                "Spread EV asset has no half-point transitions"
            )

        self.raw_push = {
            round_half(float(k)): float(v)
            for k, v in raw_push.items()
        }

        self.transitions = {}

        for r in transition_rows:
            start = num(r.get("from_spread"))
            end = num(r.get("to_spread"))

            if start is None or end is None:
                continue

            self.transitions[
                (round_half(start), round_half(end))
            ] = {
                "delta_win": float(r["delta_win"]),
                "delta_loss": float(r["delta_loss"]),
                "delta_push": float(r["delta_push"]),
                "sample_n": num(r.get("sample_n")),
            }

        self.pooled_dw = num(pooled.get("delta_win"))
        self.pooled_dl = num(pooled.get("delta_loss"))
        self.pooled_dp = num(pooled.get("delta_push"))
        self.pooled_n = num(pooled.get("independent_game_n"))
        self.global_push = num(
            pooled.get("global_push_probability")
        )

        if None in (
            self.pooled_dw,
            self.pooled_dl,
            self.pooled_dp,
            self.pooled_n,
            self.global_push,
        ):
            raise RuntimeError(
                "Spread EV asset has incomplete pooled calibration"
            )

    def ticket_probabilities(self, reference_line, ticket_line):
        reference_line = num(reference_line)
        ticket_line = num(ticket_line)

        if reference_line is None or ticket_line is None:
            return None

        reference_line = round_half(reference_line)
        ticket_line = round_half(ticket_line)

        push0 = self.raw_push.get(
            reference_line,
            self.global_push,
        )

        pw = (1.0 - push0) / 2.0
        pl = pw
        pp = push0

        if abs(ticket_line - reference_line) <= 1e-12:
            return {
                "win_probability": pw,
                "loss_probability": pl,
                "push_probability": pp,
                "weakest_half_point_sample_n": None,
            }

        direction = (
            0.5 if ticket_line > reference_line else -0.5
        )

        current = reference_line
        min_step_n = math.inf

        while (
            (
                direction > 0
                and current < ticket_line - 1e-12
            )
            or
            (
                direction < 0
                and current > ticket_line + 1e-12
            )
        ):
            nxt = round_half(current + direction)

            if direction > 0:
                tr = self.transitions.get((current, nxt))

                if tr is None:
                    dw = self.pooled_dw
                    dl = self.pooled_dl
                    dp = self.pooled_dp
                    step_n = self.pooled_n
                else:
                    dw = tr["delta_win"]
                    dl = tr["delta_loss"]
                    dp = tr["delta_push"]
                    step_n = (
                        tr["sample_n"]
                        if tr["sample_n"] is not None
                        else self.pooled_n
                    )

            else:
                # Reverse of the calibrated nxt -> current transition.
                tr = self.transitions.get((nxt, current))

                if tr is None:
                    dw = -self.pooled_dw
                    dl = -self.pooled_dl
                    dp = -self.pooled_dp
                    step_n = self.pooled_n
                else:
                    dw = -tr["delta_win"]
                    dl = -tr["delta_loss"]
                    dp = -tr["delta_push"]
                    step_n = (
                        tr["sample_n"]
                        if tr["sample_n"] is not None
                        else self.pooled_n
                    )

            pw += dw
            pl += dl
            pp += dp

            min_step_n = min(min_step_n, step_n)
            current = nxt

        # Guardrail against floating-point / extreme-path issues.
        pw = max(0.0, pw)
        pl = max(0.0, pl)
        pp = max(0.0, pp)

        total = pw + pl + pp

        if total <= 0:
            return None

        return {
            "win_probability": pw / total,
            "loss_probability": pl / total,
            "push_probability": pp / total,
            "weakest_half_point_sample_n": (
                None
                if math.isinf(min_step_n)
                else min_step_n
            ),
        }

    def ticket_ev(
        self,
        reference_line,
        ticket_line,
        ticket_price,
    ):
        probs = self.ticket_probabilities(
            reference_line,
            ticket_line,
        )

        profit = american_profit(ticket_price)

        if probs is None or profit is None:
            return None

        ev = (
            probs["win_probability"] * profit
            - probs["loss_probability"]
        )

        return {
            **probs,
            "ev_pct": ev,
        }

    def current_market_ev(
        self,
        current_line,
        current_price,
        ticket_line,
        ticket_price,
    ):
        """Relative value of an existing ticket vs the current quote."""
        ticket = self.ticket_ev(
            current_line,
            ticket_line,
            ticket_price,
        )

        market = self.ticket_ev(
            current_line,
            current_line,
            current_price,
        )

        if ticket is None or market is None:
            return None

        return {
            **ticket,
            "market_quote_ev_pct": market["ev_pct"],
            "ev_pct": (
                ticket["ev_pct"]
                - market["ev_pct"]
            ),
        }
