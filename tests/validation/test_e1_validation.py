from __future__ import annotations

from pathlib import Path

import pytest

from envs.e1_pit_backtest import (
    TIERS,
    cheater_policies,
    independent_check,
    make_case,
    oracle_policy,
    random_policy,
    sandbox_mounts,
    verify,
    wrong_policies,
)


DEV_SEEDS = range(1_000_400, 1_000_410)


@pytest.mark.parametrize("tier", TIERS)
def test_e1_oracle_random_wrong_and_cheater_policies(tier: str) -> None:
    cases = [make_case(seed, tier) for seed in DEV_SEEDS]
    assert sum(verify(case, oracle_policy(case)).reward for case in cases) / len(cases) >= 0.95
    assert sum(verify(case, random_policy(case)).reward for case in cases) / len(cases) <= 0.05
    assert len(wrong_policies) >= 10
    for policy in wrong_policies:
        assert sum(verify(case, policy(case)).reward for case in cases) / len(cases) <= 0.10
    for policy in cheater_policies.values():
        assert sum(verify(case, policy(case)).reward for case in cases) / len(cases) <= 0.05


@pytest.mark.parametrize("tier", TIERS)
def test_e1_checker_agreement_and_clean_false_positive(tier: str) -> None:
    for seed in DEV_SEEDS:
        case = make_case(seed, tier)
        submissions = [oracle_policy(case), random_policy(case)]
        submissions.extend(policy(case) for policy in wrong_policies)
        submissions.extend(policy(case) for policy in cheater_policies.values())
        assert all(verify(case, value) == independent_check(case, value) for value in submissions)
        if tier == "T4":
            assert not verify(case, oracle_policy(case)).false_positive


@pytest.mark.parametrize("tier", TIERS)
def test_e1_sandbox_mounts_never_include_or_overlap_oracle(tier: str, tmp_path: Path) -> None:
    oracle = (tmp_path / "protected" / "oracle").resolve()
    mounts = sandbox_mounts(make_case(1_000_400, tier), oracle)
    assert mounts
    for mount in mounts:
        resolved = mount.resolve()
        assert resolved != oracle
        assert not resolved.is_relative_to(oracle)
        assert not oracle.is_relative_to(resolved)

