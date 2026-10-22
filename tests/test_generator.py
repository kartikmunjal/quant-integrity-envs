from __future__ import annotations

import numpy as np
import pytest
import yaml

from qi.gen import GeneratorConfig, generate_market, generator_version_hash, seed_partition


VERSION = "test-version"


def small_config() -> GeneratorConfig:
    return GeneratorConfig(n_assets=48, n_days=260, force_alpha=True)


def test_same_seed_and_version_produce_identical_bytes() -> None:
    first = generate_market(1_000_001, VERSION, small_config())
    second = generate_market(1_000_001, VERSION, small_config())
    assert first.to_bytes() == second.to_bytes()


def test_different_seeds_produce_different_bytes() -> None:
    first = generate_market(1_000_001, VERSION, small_config())
    second = generate_market(1_000_002, VERSION, small_config())
    assert first.to_bytes() != second.to_bytes()


@pytest.mark.parametrize(
    ("seed", "expected"),
    [(0, "train"), (999_999, "train"), (1_000_000, "dev"), (1_009_999, "dev"), (2_000_000, "sealed_test"), (2_009_999, "sealed_test")],
)
def test_seed_partitions_are_disjoint(seed: int, expected: str) -> None:
    assert seed_partition(seed) == expected


@pytest.mark.parametrize("seed", [-1, 1_500_000, 3_000_000])
def test_seed_outside_partitions_is_rejected(seed: int) -> None:
    with pytest.raises(ValueError, match="registered partition"):
        seed_partition(seed)


def test_generated_truth_matches_arrays() -> None:
    market = generate_market(1_000_003, VERSION, small_config())
    assert market.truth["seed"] == 1_000_003
    assert market.truth["partition"] == "dev"
    assert market.truth["alpha_present"] is True
    assert market.returns.shape == (260, 48)
    assert market.factors.shape == (260, 3)
    assert market.signal.shape == (260, 48)
    assert market.active.shape == (260, 48)
    expected_final = np.flatnonzero(market.active[-1]).tolist()
    assert market.truth["final_active_assets"] == expected_final
    assert np.array_equal(market.truth["delisting_days"], market.delisting_day.tolist())
    assert len(market.truth["identifier_changes"]) == int(np.sum(market.id_change_day >= 0))
    assert len(market.truth["splits"]) == int(np.sum(market.split_day >= 0))
    assert np.all(market.fundamental_available_day >= market.fundamental_period_end[:, None])
    assert np.all(market.fundamental_restatement_day >= market.fundamental_available_day)


def test_config_must_stay_inside_preregistered_ranges() -> None:
    with pytest.raises(ValueError, match="n_assets"):
        GeneratorConfig(n_assets=1, n_days=500).validate(enforce_preregistered_ranges=True)


def test_source_hash_matches_preregistered_generator_version() -> None:
    prereg = yaml.safe_load(open("prereg.yaml", encoding="utf-8"))
    assert generator_version_hash() == prereg["generator"]["version_hash"]
