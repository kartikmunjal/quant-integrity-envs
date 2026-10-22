from __future__ import annotations

from scripts.run_p1_addendum import DEV_SEEDS, FRESH_DEV_SEEDS, dimension_for_seed, summarize


def test_addendum_uses_200_dev_seeds_and_frozen_dimension_ranges() -> None:
    assert len(DEV_SEEDS) == 200
    assert DEV_SEEDS == tuple(range(1_000_000, 1_000_200))
    dimensions = [dimension_for_seed(seed) for seed in DEV_SEEDS]
    assert all(200 <= n_assets <= 1_000 for n_assets, _ in dimensions)
    assert all(500 <= n_days <= 1_500 for _, n_days in dimensions)
    assert len(set(dimensions)) == len(dimensions)
    assert FRESH_DEV_SEEDS == tuple(range(1_000_200, 1_000_400))
    assert set(DEV_SEEDS).isdisjoint(FRESH_DEV_SEEDS)


def test_summary_reports_pass_rates_and_min_median_max() -> None:
    rows = [
        {
            "excess_kurtosis": 1.0,
            "absolute_return_autocorrelation": 0.04,
            "top_three_eigenvalue_share": 0.3,
            "ic_absolute_error": 0.02,
        },
        {
            "excess_kurtosis": 3.0,
            "absolute_return_autocorrelation": 0.06,
            "top_three_eigenvalue_share": 0.5,
            "ic_absolute_error": 0.0,
        },
        {
            "excess_kurtosis": 2.0,
            "absolute_return_autocorrelation": 0.08,
            "top_three_eigenvalue_share": 0.4,
            "ic_absolute_error": 0.01,
        },
    ]
    result = summarize(rows)
    assert result["pass_rates"] == {
        "excess_kurtosis": 1.0,
        "absolute_return_autocorrelation": 2 / 3,
        "top_three_eigenvalue_share_floor": 1.0,
        "ic_absolute_error": 2 / 3,
        "all_per_seed_checks": 2 / 3,
    }
    assert result["aggregate_checks"]["top_three_eigenvalue_share_median"] is True
    assert result["passed"] is False
    assert result["distributions"]["excess_kurtosis"] == {
        "min": 1.0,
        "median": 2.0,
        "max": 3.0,
    }

