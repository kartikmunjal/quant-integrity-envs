"""A smoke is always the full roster at the first screened design seed."""
import pytest
from scripts.run_p3b2_smoke import plan


def test_plan_uses_first_seed_and_keeps_all_policies_in_every_tier():
    actual=plan([1000007,1000002],['wrong'],['cheater'])
    assert len(actual)==24
    assert {row[2] for row in actual}=={1000002}
    assert set(actual)=={(mode,tier,1000002) for mode in ('oracle','random','honest','shallow','wrong','cheater') for tier in ('T1','T2','T3','T4')}
    with pytest.raises(ValueError):
        plan([],['wrong'],['cheater'])
