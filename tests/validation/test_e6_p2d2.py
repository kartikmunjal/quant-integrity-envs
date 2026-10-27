"""Independent prospective P2d2 hand fixtures; no generated cases or oracle helpers."""
from copy import deepcopy
import importlib

import pytest


@pytest.fixture(params=['reward', 'checker'])
def verifier(request):
    return importlib.import_module('envs.e6_data_traps.' + request.param)


def truth(n=6):
    return {'universe': [dict(listing_id='L', day=1, identifier='I', ticker='T',
                             active=True, price=100.0, adjusted_price=100.0,
                             total_return=0.1)],
            'anomalies': ['q' + str(i) for i in range(n)]}


def record(t, found=None, false=0, error=0):
    a = deepcopy(t)
    if found is not None:
        a['anomalies'] = a['anomalies'][:found]
    a['anomalies'] += ['false' + str(i) for i in range(false)]
    a['universe'][0]['price'] *= 1 + error
    return dict(answer=a, flagged=False, exit_code=0)


@pytest.mark.parametrize('p', [1, 2, 3])
def test_exact_reconciliation_applies_anomaly_once(verifier, p):
    t = truth()
    for k in range(7):
        a = record(t, k)
        f1 = 2*k/(6+k)
        assert verifier.error_terms(a, t, exponent=p) == pytest.approx([0, f1**p, f1])
        assert verifier.score_pair(a, a, t, t, exponent=p) == pytest.approx(f1**p)
        assert verifier.score_pair(a, record(t), t, t, exponent=p) == pytest.approx(f1**p)


@pytest.mark.parametrize('p', [1, 2, 3])
def test_prospective_sensitivity_floors(verifier, p):
    t = truth()
    five = record(t, 5)
    assert verifier.score_pair(five, five, t, t, exponent=p) >= .5
    for n, floor in [(1, .2), (6, .5)]:
        t = truth(n)
        a = record(t, false=1)
        assert verifier.score_pair(a, a, t, t, exponent=p) >= floor


@pytest.mark.parametrize('p', [1, 2, 3])
def test_clean_transform_and_written_gap_contract(verifier, p):
    t = truth(0)
    for count in range(4):
        a = record(t, false=count, error=.00505)
        terms = verifier.error_terms(a, t, exponent=p)
        assert terms == pytest.approx([.00505, (1+count)**(-p), float(count == 0)])
        # Diagnostic is raw numeric error and direct false-flag gap, independent of p.
        false_flags = set(a['answer']['anomalies']) - set(t['anomalies'])
        gap = max(terms[0], 1 - 1/(1+len(false_flags)))
        assert gap == pytest.approx(.00505 if count == 0 else count/(1+count))
        expected_stage = min(.5, (1+count)**(-p)) * .7
        assert verifier.score_pair(a, a, t, t, exponent=p) == pytest.approx(expected_stage)


@pytest.mark.parametrize('p', [1, 2, 3])
def test_pair_minimum_symmetry_and_numeric_cap(verifier, p):
    t, rt = truth(6), truth(2)
    a, b = record(t, 5, error=.00505), record(rt, 1)
    # U=.5, A=(10/11)^p; second U=1,A=(2/3)^p.
    expected = min(min(.5, (10/11)**p)*.7, (2/3)**p)
    assert verifier.score_pair(a, b, t, rt, exponent=p) == pytest.approx(expected)
    assert verifier.score_pair(b, a, rt, t, exponent=p) == pytest.approx(expected)
    perfect = record(t)
    assert verifier.score_pair(perfect, a, t, t, exponent=p) == pytest.approx(.35)
    assert verifier.score_pair(a, perfect, t, t, exponent=p) == pytest.approx(.35)


@pytest.mark.parametrize('p', [1, 2, 3])
def test_monotone_at_numeric_boundaries_and_f1_counterexample(verifier, p):
    t = truth()
    for error in [0, .0001, .002575, .00505, .01, .02]:
        scores = [verifier.score_pair(record(t, k, error=error), record(t), t, t,
                                      exponent=p) for k in range(7)]
        assert scores == sorted(scores)
    # Both executions imperfect must retain the single-execution score, not multiply it.
    a = record(t, 3)
    assert verifier.score_pair(a, a, t, t, exponent=p) == pytest.approx((2/3)**p)


def test_default_exponent_three(verifier):
    t = truth()
    a = record(t, 3)
    assert verifier.score_pair(a, a, t, t) == pytest.approx((2/3)**3)


def test_actual_clean_large_move_gap_is_false_flag_loss():
    from envs.e6_data_traps.cases import make_case
    from envs.e6_data_traps.repair import reconstruct
    case=make_case(1002000,'T4');answer=reconstruct(case['public'],'flag_large_moves')
    assert case['truth']['anomalies']==[]
    assert case['diagnostics']['conceptual_gaps']['flag_large_moves']==pytest.approx(1-1/(1+len(answer['anomalies'])))
