"""Transformation edge cases and identity preserve the submitted probability."""
import pytest
from scripts.p3b2_sensitivity import transform


def test_identity_and_constant_endpoints():
    for q in (0.,.01,.5,.99,1.):
        assert transform(q,'temperature',1)==pytest.approx(q)
        assert transform(q,'toward_zero',1)==q
        assert transform(q,'toward_one',1)==pytest.approx(q)
        assert transform(q,'temperature',0)==.5
        assert transform(q,'toward_zero',0)==0
        assert transform(q,'toward_one',0)==1


def test_extreme_temperatures_remain_valid_and_ordered():
    for amount in (.25,4.,100.):
        values=[transform(q,'temperature',amount) for q in (0.,1e-300,.1,.5,.9,1.-1e-15,1.)]
        assert values==sorted(values)
        assert all(0<=value<=1 for value in values)
