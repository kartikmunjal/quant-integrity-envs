from __future__ import annotations

from qi.gen import GeneratorConfig, generate_market
from qi.gen.diagnostics import DiagnosticThresholds, run_diagnostics


def test_stylized_fact_diagnostics_pass_on_dev_seed() -> None:
    market = generate_market(
        1_000_021,
        "test-version",
        GeneratorConfig(n_assets=120, n_days=700, force_alpha=True),
    )
    report = run_diagnostics(market, DiagnosticThresholds())
    assert report.passed, report.as_dict()
    assert report.excess_kurtosis >= 1.0
    assert report.absolute_return_autocorrelation >= 0.05
    assert report.top_three_eigenvalue_share >= 0.30
    assert report.ic_absolute_error <= 0.01
