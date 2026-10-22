"""Synthetic market with planted, fully recorded ground truth."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray


SEED_PARTITIONS = {
    "train": (0, 999_999),
    "dev": (1_000_000, 1_009_999),
    "sealed_test": (2_000_000, 2_009_999),
}


def seed_partition(seed: int) -> str:
    matches = [name for name, (low, high) in SEED_PARTITIONS.items() if low <= seed <= high]
    if len(matches) != 1:
        raise ValueError(f"seed {seed} is not in exactly one registered partition")
    return matches[0]


@dataclass(frozen=True)
class GeneratorConfig:
    """Generation controls; defaults are sampled inside frozen preregistered ranges."""

    n_assets: int | None = None
    n_days: int | None = None
    force_alpha: bool | None = None
    n_factors: int = 3
    tail_df: float = 4.0
    regime_persistence: float = 0.98

    def validate(self, *, enforce_preregistered_ranges: bool = False) -> None:
        if self.n_assets is not None and self.n_assets < 2:
            raise ValueError("n_assets must be at least 2")
        if self.n_days is not None and self.n_days < 3:
            raise ValueError("n_days must be at least 3")
        if self.n_factors != 3:
            raise ValueError("n_factors must equal the preregistered value 3")
        if self.tail_df != 4:
            raise ValueError("tail_df must equal the preregistered value 4")
        if self.regime_persistence != 0.98:
            raise ValueError("regime_persistence must equal the preregistered value 0.98")
        if enforce_preregistered_ranges:
            if self.n_assets is None or not 200 <= self.n_assets <= 1_000:
                raise ValueError("n_assets must be inside preregistered range [200, 1000]")
            if self.n_days is None or not 500 <= self.n_days <= 1_500:
                raise ValueError("n_days must be inside preregistered range [500, 1500]")


@dataclass(frozen=True)
class MarketData:
    seed: int
    version_hash: str
    config: dict[str, Any]
    returns: NDArray[np.float64]
    factors: NDArray[np.float64]
    factor_loadings: NDArray[np.float64]
    volatility: NDArray[np.float64]
    regime: NDArray[np.int8]
    signal: NDArray[np.float64]
    active: NDArray[np.bool_]
    delisting_day: NDArray[np.int64]
    id_change_day: NDArray[np.int64]
    split_day: NDArray[np.int64]
    split_factor: NDArray[np.float64]
    fundamental_period_end: NDArray[np.int64]
    fundamental_initial: NDArray[np.float64]
    fundamental_restated: NDArray[np.float64]
    fundamental_available_day: NDArray[np.int64]
    fundamental_restatement_day: NDArray[np.int64]
    spread_bps: NDArray[np.float64]
    adv_usd: NDArray[np.float64]
    impact_coefficient: NDArray[np.float64]
    capacity_usd: NDArray[np.float64]
    truth: dict[str, Any]

    def arrays(self) -> dict[str, np.ndarray[Any, Any]]:
        return {
            name: getattr(self, name)
            for name in (
                "returns",
                "factors",
                "factor_loadings",
                "volatility",
                "regime",
                "signal",
                "active",
                "delisting_day",
                "id_change_day",
                "split_day",
                "split_factor",
                "fundamental_period_end",
                "fundamental_initial",
                "fundamental_restated",
                "fundamental_available_day",
                "fundamental_restatement_day",
                "spread_bps",
                "adv_usd",
                "impact_coefficient",
                "capacity_usd",
            )
        }

    def to_bytes(self) -> bytes:
        """Canonical, architecture-independent bytes used by determinism tests."""
        chunks: list[bytes] = []
        descriptors: list[dict[str, Any]] = []
        for name, value in self.arrays().items():
            canonical = np.ascontiguousarray(value.astype(value.dtype.newbyteorder("<"), copy=False))
            payload = canonical.tobytes(order="C")
            descriptors.append(
                {"name": name, "dtype": canonical.dtype.str, "shape": list(canonical.shape), "nbytes": len(payload)}
            )
            chunks.append(payload)
        header = json.dumps(
            {
                "schema_version": 1,
                "seed": self.seed,
                "version_hash": self.version_hash,
                "config": self.config,
                "truth": self.truth,
                "arrays": descriptors,
            },
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return b"QIGEN1\0" + struct.pack("<Q", len(header)) + header + b"".join(chunks)


def _source_files() -> list[Path]:
    directory = Path(__file__).resolve().parent
    return sorted(path for path in directory.glob("*.py") if path.is_file())


def generator_version_hash() -> str:
    digest = hashlib.sha256()
    for path in _source_files():
        digest.update(path.name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _rng(seed: int, version_hash: str) -> np.random.Generator:
    material = hashlib.sha256(f"{seed}:{version_hash}".encode()).digest()
    words = np.frombuffer(material, dtype="<u4")
    return np.random.default_rng(np.random.SeedSequence(words.tolist()))


def _standardize_cross_section(values: NDArray[np.float64]) -> NDArray[np.float64]:
    centered = values - values.mean(axis=1, keepdims=True)
    scale = centered.std(axis=1, keepdims=True)
    return centered / np.where(scale > 0, scale, 1.0)


def _realized_ic(signal: NDArray[np.float64], returns: NDArray[np.float64], active: NDArray[np.bool_]) -> float:
    values: list[float] = []
    for day in range(signal.shape[0] - 1):
        valid = active[day] & active[day + 1] & np.isfinite(returns[day + 1])
        if valid.sum() >= 3:
            values.append(float(np.corrcoef(signal[day, valid], returns[day + 1, valid])[0, 1]))
    return float(np.mean(values))


def generate_market(
    seed: int,
    version_hash: str | None = None,
    config: GeneratorConfig | None = None,
) -> MarketData:
    """Generate one deterministic synthetic market for a registered seed."""
    partition = seed_partition(seed)
    config = config or GeneratorConfig()
    config.validate()
    version_hash = version_hash or generator_version_hash()
    rng = _rng(seed, version_hash)

    n_assets = config.n_assets or int(rng.integers(200, 1_001))
    n_days = config.n_days or int(rng.integers(500, 1_501))
    n_factors = config.n_factors

    regime = np.empty(n_days, dtype=np.int8)
    regime[0] = np.int8(rng.integers(0, 2))
    for day in range(1, n_days):
        regime[day] = regime[day - 1] if rng.random() < config.regime_persistence else 1 - regime[day - 1]

    log_vol = np.empty(n_days, dtype=np.float64)
    log_vol[0] = rng.normal(0.0, 0.08)
    for day in range(1, n_days):
        log_vol[day] = 0.97 * log_vol[day - 1] + rng.normal(0.0, 0.08)
    regime_scale = np.where(regime == 0, 0.007, 0.016)
    volatility = regime_scale * np.exp(log_vol)

    t_scale = math.sqrt(config.tail_df / (config.tail_df - 2.0))
    factor_shocks = rng.standard_t(config.tail_df, size=(n_days, n_factors)) / t_scale
    factors = factor_shocks * volatility[:, None]
    loadings = rng.normal(0.0, 0.9, size=(n_assets, n_factors))

    idio_vol = rng.uniform(0.01, 0.03, size=n_assets)
    idio_shocks = rng.standard_t(config.tail_df, size=(n_days, n_assets)) / t_scale
    volatility_multiplier = volatility / np.median(volatility)
    idiosyncratic = idio_shocks * idio_vol[None, :] * volatility_multiplier[:, None]
    returns = factors @ loadings.T + idiosyncratic

    halflife = float(rng.uniform(5.0, 40.0))
    decay = math.exp(-math.log(2.0) / halflife)
    signal = np.empty((n_days, n_assets), dtype=np.float64)
    signal[0] = rng.normal(size=n_assets)
    innovation_scale = math.sqrt(1.0 - decay**2)
    for day in range(1, n_days):
        signal[day] = decay * signal[day - 1] + innovation_scale * rng.normal(size=n_assets)
    signal = _standardize_cross_section(signal)

    alpha_present = bool(config.force_alpha) if config.force_alpha is not None else bool(rng.random() >= 0.40)
    target_ic = float(rng.uniform(0.01, 0.04)) if alpha_present else 0.0
    if alpha_present:
        multiplier = target_ic / math.sqrt(1.0 - target_ic**2)
        for day in range(1, n_days):
            cross_sectional_scale = float(np.std(returns[day]))
            returns[day] += multiplier * cross_sectional_scale * signal[day - 1]

    annual_delisting_rate = float(rng.uniform(0.01, 0.05))
    horizon_years = n_days / 252.0
    delisting_probability = 1.0 - math.exp(-annual_delisting_rate * horizon_years)
    delisting_day = np.full(n_assets, -1, dtype=np.int64)
    selected = rng.random(n_assets) < delisting_probability
    if n_days > 40:
        delisting_day[selected] = rng.integers(20, n_days, size=int(selected.sum()))
    active = np.ones((n_days, n_assets), dtype=np.bool_)
    for asset, day in enumerate(delisting_day):
        if day >= 0:
            active[day:, asset] = False
            returns[day:, asset] = np.nan

    id_change_day = np.full(n_assets, -1, dtype=np.int64)
    id_change_selected = rng.random(n_assets) < min(0.20, 0.03 * horizon_years)
    id_change_day[id_change_selected] = rng.integers(1, n_days, size=int(id_change_selected.sum()))
    split_day = np.full(n_assets, -1, dtype=np.int64)
    split_factor = np.ones(n_assets, dtype=np.float64)
    split_selected = rng.random(n_assets) < min(0.25, 0.04 * horizon_years)
    split_day[split_selected] = rng.integers(1, n_days, size=int(split_selected.sum()))
    if split_selected.any():
        split_factor[split_selected] = rng.choice(np.array([0.5, 2.0, 3.0]), size=int(split_selected.sum()))

    period_end = np.arange(0, n_days, 63, dtype=np.int64)
    n_periods = len(period_end)
    latent_fundamental = np.empty((n_periods, n_assets), dtype=np.float64)
    latent_fundamental[0] = rng.normal(0.0, 1.0, size=n_assets)
    for period in range(1, n_periods):
        latent_fundamental[period] = latent_fundamental[period - 1] + rng.normal(0.0, 0.15, size=n_assets)
    fundamental_initial = latent_fundamental + rng.normal(0.0, 0.08, size=latent_fundamental.shape)
    fundamental_restated = latent_fundamental + rng.normal(0.0, 0.02, size=latent_fundamental.shape)
    lags = rng.integers(1, 61, size=(n_periods, n_assets), dtype=np.int64)
    available_day = period_end[:, None] + lags
    restatement_day = available_day + rng.integers(10, 121, size=(n_periods, n_assets), dtype=np.int64)

    spread_bps = np.clip(rng.lognormal(mean=math.log(8.0), sigma=0.55, size=n_assets), 1.0, 50.0)
    adv_usd = rng.lognormal(mean=math.log(20_000_000.0), sigma=1.0, size=n_assets)
    impact_coefficient = rng.uniform(0.05, 0.30, size=n_assets)
    capacity_usd = adv_usd * rng.uniform(0.01, 0.10, size=n_assets)

    id_changes = [
        {"asset": int(asset), "day": int(day), "old_id": f"A{asset:05d}", "new_id": f"N{asset:05d}"}
        for asset, day in enumerate(id_change_day)
        if day >= 0
    ]
    splits = [
        {"asset": int(asset), "day": int(day), "factor": float(split_factor[asset])}
        for asset, day in enumerate(split_day)
        if day >= 0
    ]

    config_record = {
        **asdict(config),
        "n_assets": n_assets,
        "n_days": n_days,
        "daily_ic": target_ic,
        "halflife_days": halflife,
        "annual_delisting_rate": annual_delisting_rate,
        "idio_daily_vol_min": float(idio_vol.min()),
        "idio_daily_vol_max": float(idio_vol.max()),
    }
    realized_ic = _realized_ic(signal, returns, active)
    daily_market = np.nanmean(returns, axis=1)
    gross_sharpe = float(np.mean(daily_market) / np.std(daily_market) * math.sqrt(252.0))
    truth: dict[str, Any] = {
        "seed": seed,
        "partition": partition,
        "alpha_present": alpha_present,
        "target_daily_ic": target_ic,
        "realized_daily_ic": realized_ic,
        "alpha_halflife_days": halflife,
        "final_active_assets": np.flatnonzero(active[-1]).astype(int).tolist(),
        "delisting_days": delisting_day.astype(int).tolist(),
        "identifier_changes": id_changes,
        "splits": splits,
        "bug_set": [],
        "bug_locations": [],
        "correct_answers": {
            "realized_daily_ic": realized_ic,
            "gross_market_sharpe": gross_sharpe,
            "median_spread_bps": float(np.median(spread_bps)),
            "total_final_active_assets": int(active[-1].sum()),
        },
    }
    return MarketData(
        seed=seed,
        version_hash=version_hash,
        config=config_record,
        returns=returns,
        factors=factors,
        factor_loadings=loadings,
        volatility=volatility,
        regime=regime,
        signal=signal,
        active=active,
        delisting_day=delisting_day,
        id_change_day=id_change_day,
        split_day=split_day,
        split_factor=split_factor,
        fundamental_period_end=period_end,
        fundamental_initial=fundamental_initial,
        fundamental_restated=fundamental_restated,
        fundamental_available_day=available_day,
        fundamental_restatement_day=restatement_day,
        spread_bps=spread_bps,
        adv_usd=adv_usd,
        impact_coefficient=impact_coefficient,
        capacity_usd=capacity_usd,
        truth=truth,
    )
