"""Independent round-2 prospective validation; synthetic fixtures only."""
import json
import math

import pytest

from envs.e1_pit_backtest import checker


TRUTH = {'signal_mean': 2.0, 'backtest_return': .125}


def record(error=0.0, key='backtest_return'):
    answer = dict(TRUTH)
    answer[key] *= 1 + error
    return {'answer': answer, 'flagged': False, 'exit_code': 0}


def test_exact_and_tolerance():
    assert checker.score_pair(record(), record(), TRUTH, TRUTH) == 1
    assert checker.score_pair(record(.000099), record(), TRUTH, TRUTH) == 1


def test_continuous_joint_formula_and_max_component_error():
    midpoint = (.01 + .0001) / 2
    for key in TRUTH:
        assert checker.score_pair(record(midpoint, key), record(), TRUTH, TRUTH) == pytest.approx(.5)
        assert checker.score_pair(record(), record(midpoint, key), TRUTH, TRUTH) == pytest.approx(.45)
    assert checker.score_pair(record(midpoint), record(midpoint), TRUTH, TRUTH) == pytest.approx(.225)
    samples = [checker.score_pair(record(x), record(), TRUTH, TRUTH) for x in [.0001, .001, .003, .005, .009, .01]]
    assert all(a > b for a, b in zip(samples, samples[1:]))
    for edge in [.0001, .01]:
        a = checker.score_pair(record(edge - 1e-9), record(), TRUTH, TRUTH)
        b = checker.score_pair(record(edge + 1e-9), record(), TRUTH, TRUTH)
        assert abs(a - b) < 1e-10


@pytest.mark.parametrize('bad', [None, [], True, 42, 'null', '[]', '{bad', {}, {'signal_mean': 1},
    {'signal_mean': True, 'backtest_return': 1},
    {'signal_mean': math.nan, 'backtest_return': 1},
    {'signal_mean': math.inf, 'backtest_return': 1},
    {'signal_mean': 10**10000, 'backtest_return': 1},
    {**TRUTH, 'availability_discipline': True}])
def test_schema_fail_closed(bad):
    assert checker.check_answer(bad) is None


def test_answer_parsing():
    assert checker.check_answer(TRUTH) == TRUTH
    assert checker.check_answer(json.dumps(TRUTH)) == TRUTH
    assert checker.check_answer('{"signal_mean":2,"signal_mean":3,"backtest_return":0.125}') is None


@pytest.mark.parametrize('bad', [None, {}, {'answer': TRUTH},
    {'answer': TRUTH, 'flagged': True, 'exit_code': 0},
    {'answer': TRUTH, 'flagged': False, 'exit_code': 1},
    {'answer': TRUTH, 'flagged': 0, 'exit_code': 0},
    {'answer': {**TRUTH, 'availability_discipline': True}, 'flagged': False, 'exit_code': 0}])
def test_schema_tamper_and_absent_replay_gates(bad):
    assert checker.score_pair(bad, record(), TRUTH, TRUTH) == 0
    assert checker.score_pair(record(), bad, TRUTH, TRUTH) == 0


def test_conceptual_error_and_replay_divergence_are_zero():
    for error in [.011, 1, 251, -2]:
        assert checker.score_pair(record(error), record(), TRUTH, TRUTH) == 0
        assert checker.score_pair(record(), record(error), TRUTH, TRUTH) == 0


def test_zero_truth_denominator_and_overflow():
    zero = {key: 0.0 for key in TRUTH}
    tiny = {'answer': {key: 1e-17 for key in TRUTH}, 'flagged': False, 'exit_code': 0}
    assert checker.score_pair(tiny, tiny, zero, zero) == 1
    huge = {'answer': {key: 1e308 for key in TRUTH}, 'flagged': False, 'exit_code': 0}
    negative = {key: -1e308 for key in TRUTH}
    assert checker.score_pair(huge, huge, negative, negative) == 0


def test_scalar_oracle_enforces_availability_vintage_and_active_universe():
    data = {'cutoff': 10, 'active': [True, True, False], 'returns': [.1, -.2, None],
            'rows': [[0, 1, 2, 1, 20, 100], [0, 5, 11, 1000, 20, 2000],
                     [0, 12, 2, 2000, 20, 3000], [1, 1, 2, 2, 9, 3],
                     [2, 1, 2, 9, 20, 100]]}
    assert checker.expected(data) == pytest.approx({'signal_mean': 2, 'backtest_return': -.15})


def test_legacy_self_attestation_is_retired():
    from envs.e1_pit_backtest.task import Case, independent_check, verify
    from pathlib import Path
    case = Case(1001000, 'T1', 250, 2, .125, Path('/sandbox/test'))
    for answer in [dict(TRUTH, availability_discipline=True),
                   {'signal_mean': 0., 'backtest_return': 0., 'availability_discipline': True}]:
        assert verify(case, answer).reward <= .05
        assert independent_check(case, answer).reward <= .05
