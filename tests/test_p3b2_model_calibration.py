"""Analytic sanity checks for the prospective calibration approximation."""
from scripts.p3b2_model_calibration import model_posterior,expected_candidate
import pytest


def test_no_effect_model_has_no_information():
    for z in (-10.,0.,10.):
        for count in (1.,20.,500.):
            assert model_posterior(z,count,[0.]) == pytest.approx(.5)
    loss,fp=expected_candidate(20.,[0.],0.,0,cells=32)
    assert loss == pytest.approx(7/1920)
    assert fp == 0


def test_strong_signal_model_reduces_conditional_loss():
    for truth in (0,1):
        loss,fp=expected_candidate(1.,[20.],20.*truth,truth,cells=32)
        assert loss<1e-10
        assert fp==0
