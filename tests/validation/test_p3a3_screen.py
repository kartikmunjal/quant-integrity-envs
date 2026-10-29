"""Prospective screen tests: no policy outcomes or Docker calls."""
import pytest
from scripts import p3a3_screen as screen


def test_deterministic_first_admissible_and_rejections():
    def construct(seed,tier):
        if seed in (1003001,1003003):
            raise screen.AdmissionFailure(seed,[{'candidate':i,'error':'invalid price-return domain'} for i in range(32)])
        return {}
    a=screen.screen_range(1003000,1003005,construct=construct)
    assert a==screen.screen_range(1003000,1003005,construct=construct)
    assert a['admissible']==[1003000,1003002,1003004,1003005]
    assert [r['seed'] for r in a['rejected']]==[1003001,1003003]
    assert all(r['exhausted_32'] for r in a['rejected'])
    assert screen.first_population(a,3)==[1003000,1003002,1003004]


def test_all_tiers_checked_without_policy_inputs():
    calls=[]
    def construct(seed,tier):calls.append((seed,tier));return {}
    screen.screen_range(1000000,1000001,construct=construct)
    assert calls==[(s,t) for s in range(1000000,1000002) for t in screen.TIERS]


def test_unexpected_failure_not_filtered():
    def construct(seed,tier):raise RuntimeError('unexpected')
    with pytest.raises(RuntimeError):screen.screen_range(1000000,1000000,construct=construct)


def test_bounds_and_shortage():
    with pytest.raises(ValueError):screen.screen_range(2000000,2000001)
    with pytest.raises(ValueError):screen.first_population({'admissible':[1003000]},500)


def test_actual_known_tail_rejected_without_policy():
    row=screen.screen_range(1000075,1000075)
    assert not row['admissible']
    assert row['rejected'][0]['exhausted_32']
    assert row['rejected'][0]['causes']=={'invalid price-return domain':32}
