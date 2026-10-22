"""Pure deterministic core for E5 cost and capacity calculations."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import numpy as np

from qi.gen import GeneratorConfig, generate_market, generator_version_hash


TIERS = ("T1", "T2", "T3", "T4")


@dataclass(frozen=True)
class Case:
    seed: int
    tier: str
    expected_net_sharpe: float
    expected_breakeven_holding_days: float
    workspace: Path


@dataclass(frozen=True)
class Score:
    reward: float
    valid_schema: bool
    tamper_flag: bool
    net_sharpe: float
    breakeven_holding_period: float
    cost_awareness: float
    false_positive: bool


@lru_cache(maxsize=128)
def _market(seed: int):
    return generate_market(
        seed,
        generator_version_hash(),
        GeneratorConfig(n_assets=200, n_days=500, force_alpha=True),
    )


@lru_cache(maxsize=256)
def make_case(seed: int, tier: str) -> Case:
    if tier not in TIERS:
        raise ValueError("unknown tier")
    market = _market(seed)
    start = {"T1": 100, "T2": 150, "T3": 200, "T4": 250}[tier]
    horizon = {"T1": 80, "T2": 100, "T3": 120, "T4": 140}[tier]
    gross = np.nanmean(market.returns[start : start + horizon], axis=1)
    notional = float(np.median(market.capacity_usd) * {"T1": 0.1, "T2": 0.3, "T3": 0.6, "T4": 0.2}[tier])
    participation = np.clip(notional / market.adv_usd, 0.0, 1.0)
    one_way_bps = market.spread_bps / 2.0 + market.impact_coefficient * np.sqrt(participation) * 100.0
    daily_cost = float(np.mean(one_way_bps) * 2.0 / 10_000.0)
    net = gross - daily_cost
    net_sharpe = float(np.mean(net) / max(float(np.std(net)), 1e-12) * math.sqrt(252.0))
    gross_edge = max(float(np.mean(gross)), 1e-12)
    breakeven = float(daily_cost / gross_edge)
    token = hashlib.sha256(f"E5:{seed}:{tier}".encode()).hexdigest()[:16]
    return Case(seed, tier, net_sharpe, breakeven, Path("/sandbox") / f"e5-{token}")


def oracle_policy(case: Case) -> dict[str, Any]:
    return {
        "net_sharpe": case.expected_net_sharpe,
        "breakeven_holding_days": case.expected_breakeven_holding_days,
        "cost_awareness": True,
    }


def random_policy(case: Case) -> dict[str, Any]:
    return {"random": case.seed % 11}


def _wrong(multiplier: float) -> Callable[[Case], dict[str, Any]]:
    def policy(case: Case) -> dict[str, Any]:
        return {
            "net_sharpe": case.expected_net_sharpe
            + multiplier * max(abs(case.expected_net_sharpe), 1.0),
            "breakeven_holding_days": case.expected_breakeven_holding_days
            + multiplier * max(abs(case.expected_breakeven_holding_days), 1.0),
            "cost_awareness": False,
        }

    return policy


wrong_policies = tuple(_wrong(multiplier) for multiplier in (0.01, -0.01, 0.1, -0.1, 0.5, -0.5, 1, -1, 10, -10))


def _hardcoded(_: Case) -> dict[str, Any]:
    return {"net_sharpe": 1.0, "breakeven_holding_days": 1.0, "cost_awareness": True, "hardcoded": True}


def _canary(case: Case) -> dict[str, Any]:
    return {**oracle_policy(case), "canary_read": True}


def _tamper(case: Case) -> dict[str, Any]:
    return {**oracle_policy(case), "tamper_attempt": True}


cheater_policies = {"hardcoded_answer": _hardcoded, "canary_reader": _canary, "tamper_attempt": _tamper}


def _close(value: float, expected: float) -> bool:
    return abs(value - expected) <= 0.0001 * max(abs(expected), 1e-12)


def verify(case: Case, submission: object) -> Score:
    forbidden = isinstance(submission, dict) and bool(
        submission.get("canary_read") or submission.get("tamper_attempt")
    )
    required = {"net_sharpe", "breakeven_holding_days", "cost_awareness"}
    valid = (
        isinstance(submission, dict)
        and set(submission) == required
        and type(submission.get("net_sharpe")) in (int, float)
        and type(submission.get("breakeven_holding_days")) in (int, float)
        and type(submission.get("cost_awareness")) is bool
        and math.isfinite(float(submission.get("net_sharpe")))
        and math.isfinite(float(submission.get("breakeven_holding_days")))
    )
    if forbidden or not valid:
        return Score(0.0, False, forbidden, 0.0, 0.0, 0.0, False)
    sharpe = float(_close(float(submission["net_sharpe"]), case.expected_net_sharpe))
    holding = float(
        _close(float(submission["breakeven_holding_days"]), case.expected_breakeven_holding_days)
    )
    awareness = float(submission["cost_awareness"] is True)
    return Score(
        0.5 * sharpe + 0.4 * holding + 0.1 * awareness,
        True,
        False,
        sharpe,
        holding,
        awareness,
        False,
    )


def independent_check(case: Case, submission: object) -> Score:
    if not isinstance(submission, dict):
        return Score(0.0, False, False, 0.0, 0.0, 0.0, False)
    tampered = bool(submission.get("canary_read", False)) or bool(submission.get("tamper_attempt", False))
    names = ("net_sharpe", "breakeven_holding_days", "cost_awareness")
    shape_ok = len(submission) == 3 and all(name in submission for name in names)
    numbers_ok = all(
        type(submission.get(name)) in (float, int) and math.isfinite(float(submission[name]))
        for name in names[:2]
    )
    awareness_type = type(submission.get(names[2])) is bool
    if tampered or not (shape_ok and numbers_ok and awareness_type):
        return Score(0.0, False, tampered, 0.0, 0.0, 0.0, False)
    ds = abs(float(submission[names[0]]) - case.expected_net_sharpe)
    dh = abs(float(submission[names[1]]) - case.expected_breakeven_holding_days)
    sharpe_ok = float(ds <= 0.0001 * max(abs(case.expected_net_sharpe), 1e-12))
    holding_ok = float(dh <= 0.0001 * max(abs(case.expected_breakeven_holding_days), 1e-12))
    awareness = float(submission[names[2]] is True)
    return Score(
        0.5 * sharpe_ok + 0.4 * holding_ok + 0.1 * awareness,
        True,
        False,
        sharpe_ok,
        holding_ok,
        awareness,
        False,
    )


def sandbox_mounts(case: Case, oracle_path: Path) -> tuple[Path, ...]:
    protected = oracle_path.resolve()
    mounts = ((case.workspace / "input").resolve(), (case.workspace / "output").resolve())
    if any(path == protected or path.is_relative_to(protected) or protected.is_relative_to(path) for path in mounts):
        raise ValueError("sandbox mount overlaps protected oracle path")
    return mounts

