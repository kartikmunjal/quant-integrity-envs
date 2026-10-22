"""Pure deterministic core for E6 universe reconciliation and anomaly scoring."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from qi.gen import GeneratorConfig, generate_market, generator_version_hash


TIERS = ("T1", "T2", "T3", "T4")


@dataclass(frozen=True)
class Case:
    seed: int
    tier: str
    expected_active_ids: tuple[str, ...]
    expected_anomalies: tuple[str, ...]
    workspace: Path


@dataclass(frozen=True)
class Score:
    reward: float
    valid_schema: bool
    tamper_flag: bool
    universe_reconciliation: float
    anomaly_f1: float
    false_positive: bool


@lru_cache(maxsize=128)
def _market(seed: int):
    return generate_market(
        seed,
        generator_version_hash(),
        GeneratorConfig(n_assets=200, n_days=500, force_alpha=None),
    )


@lru_cache(maxsize=256)
def make_case(seed: int, tier: str) -> Case:
    if tier not in TIERS:
        raise ValueError("unknown tier")
    market = _market(seed)
    changed = {int(item["asset"]): str(item["new_id"]) for item in market.truth["identifier_changes"]}
    active_ids = tuple(
        sorted(changed.get(asset, f"A{asset:05d}") for asset in market.truth["final_active_assets"])
    )
    events = [f"split:{item['asset']}:{item['day']}" for item in market.truth["splits"]]
    events.extend(
        f"id_change:{item['asset']}:{item['day']}" for item in market.truth["identifier_changes"]
    )
    count = {"T1": 1, "T2": 2, "T3": 4, "T4": 0}[tier]
    anomalies = tuple(sorted(events[:count]))
    token = hashlib.sha256(f"E6:{seed}:{tier}".encode()).hexdigest()[:16]
    return Case(seed, tier, active_ids, anomalies, Path("/sandbox") / f"e6-{token}")


def oracle_policy(case: Case) -> dict[str, Any]:
    return {"active_ids": list(case.expected_active_ids), "anomalies": list(case.expected_anomalies)}


def random_policy(case: Case) -> dict[str, Any]:
    return {"guess": case.seed % 13}


def _wrong(mode: int) -> Callable[[Case], dict[str, Any]]:
    def policy(case: Case) -> dict[str, Any]:
        return {"active_ids": [f"BAD{mode}"], "anomalies": [f"false:{mode}"]}

    return policy


wrong_policies = tuple(_wrong(mode) for mode in range(10))


def _hardcoded(_: Case) -> dict[str, Any]:
    return {"active_ids": ["A00000"], "anomalies": [], "hardcoded": True}


def _canary(case: Case) -> dict[str, Any]:
    return {**oracle_policy(case), "canary_read": True}


def _tamper(case: Case) -> dict[str, Any]:
    return {**oracle_policy(case), "tamper_attempt": True}


cheater_policies = {"hardcoded_answer": _hardcoded, "canary_reader": _canary, "tamper_attempt": _tamper}


def _f1(predicted: set[str], expected: set[str]) -> float:
    if not predicted and not expected:
        return 1.0
    if not predicted or not expected:
        return 0.0
    true_positive = len(predicted & expected)
    return 2.0 * true_positive / (len(predicted) + len(expected))


def verify(case: Case, submission: object) -> Score:
    forbidden = isinstance(submission, dict) and bool(
        submission.get("canary_read") or submission.get("tamper_attempt")
    )
    valid = (
        isinstance(submission, dict)
        and set(submission) == {"active_ids", "anomalies"}
        and isinstance(submission.get("active_ids"), list)
        and isinstance(submission.get("anomalies"), list)
        and all(type(value) is str for value in submission.get("active_ids", []))
        and all(type(value) is str for value in submission.get("anomalies", []))
        and len(set(submission.get("active_ids", []))) == len(submission.get("active_ids", []))
        and len(set(submission.get("anomalies", []))) == len(submission.get("anomalies", []))
    )
    if forbidden or not valid:
        return Score(0.0, False, forbidden, 0.0, 0.0, False)
    predicted_ids = set(submission["active_ids"])
    predicted_anomalies = set(submission["anomalies"])
    reconciliation = float(predicted_ids == set(case.expected_active_ids))
    anomaly = _f1(predicted_anomalies, set(case.expected_anomalies))
    false_positive = case.tier == "T4" and bool(predicted_anomalies)
    return Score(0.6 * reconciliation + 0.4 * anomaly, True, False, reconciliation, anomaly, false_positive)


def independent_check(case: Case, submission: object) -> Score:
    if not isinstance(submission, dict):
        return Score(0.0, False, False, 0.0, 0.0, False)
    attacked = bool(submission.get("canary_read", False)) or bool(submission.get("tamper_attempt", False))
    shape = len(submission) == 2 and "active_ids" in submission and "anomalies" in submission
    lists = shape and type(submission["active_ids"]) is list and type(submission["anomalies"]) is list
    strings = lists and all(type(item) is str for item in submission["active_ids"] + submission["anomalies"])
    unique = strings and len(submission["active_ids"]) == len(set(submission["active_ids"])) and len(
        submission["anomalies"]
    ) == len(set(submission["anomalies"]))
    if attacked or not unique:
        return Score(0.0, False, attacked, 0.0, 0.0, False)
    ids = set(submission["active_ids"])
    flags = set(submission["anomalies"])
    universe = float(ids == set(case.expected_active_ids))
    truth = set(case.expected_anomalies)
    if len(flags) + len(truth) == 0:
        f_score = 1.0
    else:
        f_score = 2.0 * len(flags.intersection(truth)) / (len(flags) + len(truth))
    fp = case.tier == "T4" and len(flags) > 0
    return Score(0.6 * universe + 0.4 * f_score, True, False, universe, f_score, fp)


def sandbox_mounts(case: Case, oracle_path: Path) -> tuple[Path, ...]:
    secret = oracle_path.resolve()
    mounts = ((case.workspace / "input").resolve(), (case.workspace / "output").resolve())
    for path in mounts:
        if path == secret or path.is_relative_to(secret) or secret.is_relative_to(path):
            raise ValueError("sandbox mount overlaps protected oracle path")
    return mounts

