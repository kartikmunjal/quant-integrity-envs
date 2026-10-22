"""Stylized-fact diagnostics for generated markets."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .model import MarketData


@dataclass(frozen=True)
class DiagnosticThresholds:
    min_excess_kurtosis: float = 1.0
    min_absolute_return_autocorrelation: float = 0.05
    min_top_three_eigenvalue_share: float = 0.30
    max_ic_absolute_error: float = 0.01


@dataclass(frozen=True)
class DiagnosticReport:
    excess_kurtosis: float
    absolute_return_autocorrelation: float
    top_three_eigenvalue_share: float
    realized_daily_ic: float
    target_daily_ic: float
    ic_absolute_error: float
    passed: bool

    def as_dict(self) -> dict[str, float | bool]:
        return asdict(self)


def _excess_kurtosis(values: np.ndarray) -> float:
    centered = values - np.mean(values)
    variance = np.mean(centered**2)
    return float(np.mean(centered**4) / variance**2 - 3.0)


def run_diagnostics(market: MarketData, thresholds: DiagnosticThresholds | None = None) -> DiagnosticReport:
    thresholds = thresholds or DiagnosticThresholds()
    finite_returns = market.returns[np.isfinite(market.returns)]
    excess_kurtosis = _excess_kurtosis(finite_returns)

    equal_weighted = np.nanmean(market.returns, axis=1)
    absolute = np.abs(equal_weighted)
    absolute_autocorrelation = float(np.corrcoef(absolute[:-1], absolute[1:])[0, 1])

    filled = np.where(np.isfinite(market.returns), market.returns, 0.0)
    standardized = filled - filled.mean(axis=0, keepdims=True)
    covariance = standardized.T @ standardized / max(1, standardized.shape[0] - 1)
    eigenvalues = np.linalg.eigvalsh(covariance)
    eigen_share = float(eigenvalues[-3:].sum() / eigenvalues.sum())

    target_ic = float(market.truth["target_daily_ic"])
    realized_ic = float(market.truth["realized_daily_ic"])
    ic_error = abs(realized_ic - target_ic)
    passed = (
        excess_kurtosis >= thresholds.min_excess_kurtosis
        and absolute_autocorrelation >= thresholds.min_absolute_return_autocorrelation
        and eigen_share >= thresholds.min_top_three_eigenvalue_share
        and ic_error <= thresholds.max_ic_absolute_error
    )
    return DiagnosticReport(
        excess_kurtosis=excess_kurtosis,
        absolute_return_autocorrelation=absolute_autocorrelation,
        top_three_eigenvalue_share=eigen_share,
        realized_daily_ic=realized_ic,
        target_daily_ic=target_ic,
        ic_absolute_error=ic_error,
        passed=passed,
    )
