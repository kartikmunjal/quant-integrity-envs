#!/usr/bin/env python3
"""Run the P2 policy and independent-checker gates on dev seeds only."""

from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


ENVIRONMENTS = {
    "E1": ("envs.e1_pit_backtest", 1_000_400),
    "E5": ("envs.e5_cost_realism", 1_000_900),
    "E6": ("envs.e6_data_traps", 1_001_400),
}


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def run_environment(module_name: str, first_seed: int) -> dict[str, Any]:
    module = importlib.import_module(module_name)
    tier_results: dict[str, Any] = {}
    agreements = 0
    comparisons = 0
    generated_cases = 0
    for tier in module.TIERS:
        policy_cases = [module.make_case(seed, tier) for seed in range(first_seed, first_seed + 50)]
        oracle_mean = _mean([module.verify(case, module.oracle_policy(case)).reward for case in policy_cases])
        random_mean = _mean([module.verify(case, module.random_policy(case)).reward for case in policy_cases])
        wrong_mean = _mean(
            [module.verify(case, policy(case)).reward for case in policy_cases for policy in module.wrong_policies]
        )
        cheater_mean = _mean(
            [
                module.verify(case, policy(case)).reward
                for case in policy_cases
                for policy in module.cheater_policies.values()
            ]
        )
        clean_cases = policy_cases if tier == "T4" else []
        clean_false_positive_rate = (
            _mean(
                [
                    float(module.verify(case, module.oracle_policy(case)).false_positive)
                    for case in clean_cases
                ]
            )
            if clean_cases
            else 0.0
        )
        tier_results[tier] = {
            "oracle_mean_reward": oracle_mean,
            "random_mean_reward": random_mean,
            "wrong_mean_reward": wrong_mean,
            "cheater_mean_reward": cheater_mean,
            "clean_false_positive_rate": clean_false_positive_rate,
            "passed": oracle_mean >= 0.95
            and random_mean <= 0.05
            and wrong_mean <= 0.10
            and cheater_mean <= 0.05
            and clean_false_positive_rate <= 0.02,
        }
        for seed in range(first_seed, first_seed + 500):
            case = module.make_case(seed, tier)
            generated_cases += 1
            submissions = [module.oracle_policy(case), module.random_policy(case)]
            submissions.extend(policy(case) for policy in module.wrong_policies)
            submissions.extend(policy(case) for policy in module.cheater_policies.values())
            for submission in submissions:
                comparisons += 1
                agreements += int(
                    module.verify(case, submission) == module.independent_check(case, submission)
                )
    agreement = agreements / comparisons
    return {
        "generated_cases": generated_cases,
        "checker_comparisons": comparisons,
        "checker_agreement": agreement,
        "checker_agreement_passed": agreement >= 0.999,
        "tiers": tier_results,
        "passed": generated_cases >= 2_000
        and agreement >= 0.999
        and all(row["passed"] for row in tier_results.values()),
    }


def main() -> int:
    started = time.perf_counter()
    report = {
        "schema_version": 1,
        "seed_partition": "dev",
        "generator_version_hash": "eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921",
        "environments": {
            env_id: run_environment(module_name, first_seed)
            for env_id, (module_name, first_seed) in ENVIRONMENTS.items()
        },
    }
    report["elapsed_seconds"] = time.perf_counter() - started
    report["passed"] = all(row["passed"] for row in report["environments"].values())
    output = Path("results/p2_gate.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
