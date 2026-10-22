#!/usr/bin/env python3
"""Run the owner-requested 200-dev-seed P1 diagnostic addendum."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from qi.gen import GeneratorConfig, generate_market, generator_version_hash
from qi.gen.diagnostics import DiagnosticThresholds, run_diagnostics


DEV_SEEDS = tuple(range(1_000_000, 1_000_200))
FRESH_DEV_SEEDS = tuple(range(1_000_200, 1_000_400))
MIN_MEDIAN_TOP_THREE_SHARE = 0.30
MIN_PER_SEED_TOP_THREE_SHARE = 0.15


def dimension_for_seed(seed: int) -> tuple[int, int]:
    """Sample dimensions deterministically without consuming generator randomness."""
    digest = hashlib.sha256(f"p1-addendum-dimensions:{seed}".encode()).digest()
    n_assets = 200 + int.from_bytes(digest[:8], "little") % 801
    n_days = 500 + int.from_bytes(digest[8:16], "little") % 1_001
    return n_assets, n_days


def _stats(rows: list[dict[str, Any]], key: str) -> dict[str, float]:
    values = np.asarray([float(row[key]) for row in rows])
    return {"min": float(values.min()), "median": float(np.median(values)), "max": float(values.max())}


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    thresholds = DiagnosticThresholds()
    checks = {
        "excess_kurtosis": lambda row: float(row["excess_kurtosis"]) >= thresholds.min_excess_kurtosis,
        "absolute_return_autocorrelation": lambda row: float(row["absolute_return_autocorrelation"])
        >= thresholds.min_absolute_return_autocorrelation,
        "top_three_eigenvalue_share_floor": lambda row: float(row["top_three_eigenvalue_share"])
        >= MIN_PER_SEED_TOP_THREE_SHARE,
        "ic_absolute_error": lambda row: float(row["ic_absolute_error"]) <= thresholds.max_ic_absolute_error,
    }
    pass_rates = {name: sum(check(row) for row in rows) / len(rows) for name, check in checks.items()}
    median_share = float(np.median([float(row["top_three_eigenvalue_share"]) for row in rows]))
    aggregate_checks = {
        "excess_kurtosis_all_seeds": pass_rates["excess_kurtosis"] == 1.0,
        "absolute_return_autocorrelation_all_seeds": pass_rates["absolute_return_autocorrelation"] == 1.0,
        "top_three_eigenvalue_share_floor_all_seeds": pass_rates["top_three_eigenvalue_share_floor"] == 1.0,
        "top_three_eigenvalue_share_median": median_share >= MIN_MEDIAN_TOP_THREE_SHARE,
        "ic_absolute_error_all_seeds": pass_rates["ic_absolute_error"] == 1.0,
    }
    pass_rates["all_per_seed_checks"] = sum(
        all(check(row) for check in checks.values()) for row in rows
    ) / len(rows)
    return {
        "pass_rates": pass_rates,
        "aggregate_checks": aggregate_checks,
        "passed": all(aggregate_checks.values()),
        "distributions": {
            key: _stats(rows, key)
            for key in ("excess_kurtosis", "top_three_eigenvalue_share", "ic_absolute_error")
        },
    }


def run(seeds: tuple[int, ...] = FRESH_DEV_SEEDS) -> dict[str, Any]:
    started = time.perf_counter()
    version = generator_version_hash()
    thresholds = DiagnosticThresholds()
    rows: list[dict[str, Any]] = []
    for seed in seeds:
        n_assets, n_days = dimension_for_seed(seed)
        market = generate_market(
            seed,
            version,
            GeneratorConfig(n_assets=n_assets, n_days=n_days, force_alpha=True),
        )
        report = run_diagnostics(market, thresholds)
        finite_returns = market.returns[np.isfinite(market.returns)]
        rows.append(
            {
                "seed": seed,
                "n_assets": n_assets,
                "n_days": n_days,
                **report.as_dict(),
                "maximum_single_day_absolute_return": float(np.max(np.abs(finite_returns))),
                "fraction_absolute_returns_above_50_percent": float(
                    np.mean(np.abs(finite_returns) > 0.50)
                ),
                "finite_return_count": int(finite_returns.size),
                "absolute_returns_above_50_percent_count": int(
                    np.count_nonzero(np.abs(finite_returns) > 0.50)
                ),
            }
        )
    return {
        "schema_version": 1,
        "environment": "shared-generator",
        "generator_version_hash": version,
        "seed_partition": "dev",
        "dimension_sampling": "sha256(seed), inclusive frozen ranges",
        "thresholds": {
            "min_excess_kurtosis": thresholds.min_excess_kurtosis,
            "min_absolute_return_autocorrelation": thresholds.min_absolute_return_autocorrelation,
            "min_median_top_three_eigenvalue_share": MIN_MEDIAN_TOP_THREE_SHARE,
            "min_per_seed_top_three_eigenvalue_share": MIN_PER_SEED_TOP_THREE_SHARE,
            "max_ic_absolute_error": thresholds.max_ic_absolute_error,
        },
        "cases": rows,
        "summary": {
            **summarize(rows),
            "maximum_single_day_absolute_return": max(
                float(row["maximum_single_day_absolute_return"]) for row in rows
            ),
            "fraction_absolute_returns_above_50_percent": sum(
                int(row["absolute_returns_above_50_percent_count"]) for row in rows
            )
            / sum(int(row["finite_return_count"]) for row in rows),
            "elapsed_seconds": time.perf_counter() - started,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/p1_addendum_diagnostics.json"))
    args = parser.parse_args()
    report = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    return 0 if report["summary"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
