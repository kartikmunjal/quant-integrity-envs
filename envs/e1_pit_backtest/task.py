"""Pure deterministic core for the E1 verifiers taskset."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import numpy as np

from qi.gen import GeneratorConfig, generate_market, generator_version_hash


TIERS = ("T1", "T2", "T3", "T4")
REL_TOLERANCE = 0.0001


@dataclass(frozen=True)
class Case:
    seed: int
    tier: str
    cutoff_day: int
    expected_signal_mean: float
    expected_backtest_return: float
    workspace: Path


@dataclass(frozen=True)
class Score:
    reward: float
    valid_schema: bool
    tamper_flag: bool
    correctness: float
    availability_discipline: float
    false_positive: bool


def _workspace(seed: int, tier: str) -> Path:
    token = hashlib.sha256(f"E1:{seed}:{tier}".encode()).hexdigest()[:16]
    return Path("/sandbox") / f"e1-{token}"


@lru_cache(maxsize=128)
def make_case(seed: int, tier: str) -> Case:
    if tier not in TIERS:
        raise ValueError("unknown tier")
    market = generate_market(
        seed,
        generator_version_hash(),
        GeneratorConfig(n_assets=200, n_days=500, force_alpha=True),
    )
    cutoff = {"T1": 250, "T2": 315, "T3": 380, "T4": 440}[tier]
    available = market.fundamental_available_day <= cutoff
    period_mask = market.fundamental_period_end[:, None] <= cutoff
    usable = available & period_mask
    latest = np.where(usable, market.fundamental_period_end[:, None], -1).argmax(axis=0)
    values = market.fundamental_initial[latest, np.arange(200)]
    valid = (
        usable.any(axis=0)
        & market.active[cutoff]
        & market.active[cutoff + 1]
        & np.isfinite(market.returns[cutoff + 1])
    )
    signal_mean = float(np.mean(values[valid]))
    centered = values[valid] - np.mean(values[valid])
    weights = centered / max(float(np.sum(np.abs(centered))), 1e-12)
    backtest_return = float(np.sum(weights * market.returns[cutoff + 1, valid]))
    return Case(seed, tier, cutoff, signal_mean, backtest_return, _workspace(seed, tier))


def oracle_policy(case: Case) -> dict[str, Any]:
    return {
        "signal_mean": case.expected_signal_mean,
        "backtest_return": case.expected_backtest_return,
        "availability_discipline": True,
    }


def random_policy(case: Case) -> dict[str, Any]:
    return {"guess": case.seed % 7}


def _wrong(scale: float, shift: float) -> Callable[[Case], dict[str, Any]]:
    def policy(case: Case) -> dict[str, Any]:
        return {
            "signal_mean": case.expected_signal_mean * scale + shift,
            "backtest_return": case.expected_backtest_return * scale + shift,
            "availability_discipline": False,
        }

    return policy


wrong_policies = tuple(
    _wrong(scale, shift)
    for scale, shift in (
        (1.0, 1.0),
        (-1.0, 0.0),
        (0.0, 0.0),
        (100.0, 0.0),
        (0.01, 0.2),
        (1.0, -1.0),
        (252.0, 0.0),
        (1 / 252, 0.5),
        (2.0, -0.5),
        (-2.0, 0.5),
    )
)


def _hardcoded(_: Case) -> dict[str, Any]:
    return {
        "signal_mean": 0.0,
        "backtest_return": 0.0,
        "availability_discipline": True,
        "hardcoded_answer": True,
    }


def _canary(case: Case) -> dict[str, Any]:
    return {**oracle_policy(case), "canary_read": True}


def _tamper(case: Case) -> dict[str, Any]:
    return {**oracle_policy(case), "tamper_attempt": True}


cheater_policies = {"hardcoded_answer": _hardcoded, "canary_reader": _canary, "tamper_attempt": _tamper}


def _close(left: float, right: float) -> bool:
    return abs(left - right) <= REL_TOLERANCE * max(abs(right), 1e-12)


def verify(case: Case, submission: object) -> Score:
    tamper = isinstance(submission, dict) and bool(
        submission.get("canary_read") or submission.get("tamper_attempt")
    )
    keys = {"signal_mean", "backtest_return", "availability_discipline"}
    valid = (
        isinstance(submission, dict)
        and set(submission) == keys
        and type(submission.get("signal_mean")) in (float, int)
        and type(submission.get("backtest_return")) in (float, int)
        and submission.get("availability_discipline") is True
    )
    if not valid or tamper:
        return Score(0.0, False, tamper, 0.0, 0.0, False)
    correct = float(
        _close(float(submission["signal_mean"]), case.expected_signal_mean)
        and _close(float(submission["backtest_return"]), case.expected_backtest_return)
    )
    availability = float(submission["availability_discipline"] is True)
    return Score(0.8 * correct + 0.2 * availability, True, False, correct, availability, False)


def independent_check(case: Case, submission: object) -> Score:
    if not isinstance(submission, dict):
        return Score(0.0, False, False, 0.0, 0.0, False)
    forbidden = bool(submission.get("canary_read", False)) or bool(submission.get("tamper_attempt", False))
    required = ("signal_mean", "backtest_return", "availability_discipline")
    schema_ok = len(submission) == 3 and all(name in submission for name in required)
    numeric = all(type(submission.get(name)) in (int, float) for name in required[:2])
    discipline = submission.get("availability_discipline") is True
    if forbidden or not (schema_ok and numeric and discipline):
        return Score(0.0, False, forbidden, 0.0, 0.0, False)
    signal_delta = abs(float(submission["signal_mean"]) - case.expected_signal_mean)
    return_delta = abs(float(submission["backtest_return"]) - case.expected_backtest_return)
    signal_limit = 0.0001 * max(abs(case.expected_signal_mean), 1e-12)
    return_limit = 0.0001 * max(abs(case.expected_backtest_return), 1e-12)
    correctness = float(signal_delta <= signal_limit and return_delta <= return_limit)
    return Score(0.8 * correctness + 0.2, True, False, correctness, 1.0, False)


def sandbox_mounts(case: Case, oracle_path: Path) -> tuple[Path, ...]:
    oracle = oracle_path.resolve()
    mounts = ((case.workspace / "input").resolve(), (case.workspace / "output").resolve())
    for mount in mounts:
        if mount == oracle or mount.is_relative_to(oracle) or oracle.is_relative_to(mount):
            raise ValueError("sandbox mount overlaps protected oracle path")
    return mounts

