#!/usr/bin/env python3
"""Run the reproducible P1 generator gate on preregistered dev seeds only."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from qi.gen import GeneratorConfig, generate_market, generator_version_hash
from qi.gen.diagnostics import DiagnosticThresholds, run_diagnostics
from qi.oracle import build_manifest, validate_manifest


DEV_SEEDS = tuple(range(1_000_000, 1_000_005))


def run_gate() -> dict[str, object]:
    started = time.perf_counter()
    version = generator_version_hash()
    config = GeneratorConfig(n_assets=240, n_days=700, force_alpha=True)
    thresholds = DiagnosticThresholds()
    rows: list[dict[str, object]] = []
    canonical_hashes: list[str] = []
    oracle_consistent = True
    for seed in DEV_SEEDS:
        market = generate_market(seed, version, config)
        payload = market.to_bytes()
        repeated = generate_market(seed, version, config).to_bytes()
        deterministic = payload == repeated
        canonical_hash = hashlib.sha256(payload).hexdigest()
        canonical_hashes.append(canonical_hash)
        manifest = build_manifest(market)
        try:
            validate_manifest(manifest)
            consistent = (
                manifest["seed"] == market.truth["seed"]
                and manifest["alpha"]["present"] == market.truth["alpha_present"]
                and manifest["universe"]["final_active_assets"] == market.truth["final_active_assets"]
                and manifest["corporate_actions"]["splits"] == market.truth["splits"]
                and manifest["correct_answers"] == market.truth["correct_answers"]
            )
        except ValueError:
            consistent = False
        oracle_consistent &= consistent
        diagnostics = run_diagnostics(market, thresholds)
        rows.append(
            {
                "seed": seed,
                "canonical_sha256": canonical_hash,
                "deterministic_repeat": deterministic,
                "oracle_self_consistent": consistent,
                **diagnostics.as_dict(),
            }
        )

    different_seeds_differ = len(set(canonical_hashes)) == len(canonical_hashes)
    diagnostics_pass = all(bool(row["passed"]) for row in rows)
    determinism_pass = all(bool(row["deterministic_repeat"]) for row in rows) and different_seeds_differ
    elapsed = time.perf_counter() - started
    return {
        "schema_version": 1,
        "generator_version_hash": version,
        "environment": "shared-generator",
        "seed_partition": "dev",
        "seeds": list(DEV_SEEDS),
        "config": {"n_assets": 240, "n_days": 700, "force_alpha": True},
        "thresholds": {
            "min_excess_kurtosis": thresholds.min_excess_kurtosis,
            "min_absolute_return_autocorrelation": thresholds.min_absolute_return_autocorrelation,
            "min_top_three_eigenvalue_share": thresholds.min_top_three_eigenvalue_share,
            "max_ic_absolute_error": thresholds.max_ic_absolute_error,
        },
        "cases": rows,
        "summary": {
            "same_seed_same_bytes": determinism_pass,
            "different_seeds_differ": different_seeds_differ,
            "stylized_fact_diagnostics_pass": diagnostics_pass,
            "oracle_self_consistency": oracle_consistent,
            "minimum_excess_kurtosis": min(float(row["excess_kurtosis"]) for row in rows),
            "minimum_absolute_return_autocorrelation": min(
                float(row["absolute_return_autocorrelation"]) for row in rows
            ),
            "minimum_top_three_eigenvalue_share": min(
                float(row["top_three_eigenvalue_share"]) for row in rows
            ),
            "maximum_ic_absolute_error": max(float(row["ic_absolute_error"]) for row in rows),
            "elapsed_seconds": elapsed,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/p1_diagnostics.json"))
    args = parser.parse_args()
    report = run_gate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    summary = report["summary"]
    return 0 if all(
        bool(summary[key])
        for key in (
            "same_seed_same_bytes",
            "different_seeds_differ",
            "stylized_fact_diagnostics_pass",
            "oracle_self_consistency",
        )
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
