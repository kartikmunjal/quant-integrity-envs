"""Independent tests written before the E3 round-two production implementation."""
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path

import pytest


def independent_checker():
    path = Path(__file__).with_name('e3_round2_checker.py')
    spec = importlib.util.spec_from_file_location('independent_e3_round2', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def production():
    from envs.e3_fdr_adjudication import reward
    return reward


def test_raw_weight_mode_and_propriety_grid():
    check = independent_checker()
    weight = lambda q: q**3 * (1-q)
    assert all(weight(F(3, 4)) >= weight(F(i, 100)) for i in range(101))
    assert 3 * (1-F(3, 4)) == F(3, 4)
    for i in range(21):
        p = F(i, 20)
        minimum = (1-p) * check.candidate_loss(p, 0) + p * check.candidate_loss(p, 1)
        for j in range(101):
            q = F(j, 100)
            candidate = (1-p) * check.candidate_loss(q, 0) + p * check.candidate_loss(q, 1)
            assert candidate == minimum if q == p else candidate > minimum


def test_uniform_expectation_mathematical_quadrature():
    # This ceiling is an expectation, not a claim about every random report.
    upper_bound = independent_checker().uniform_expectation_upper_bound()
    assert 0.02 < upper_bound < 0.05 - 1e-8


def test_fixed_reference_clipping_counterexample_fixture():
    check = independent_checker()
    p = F(9, 10)
    truth_a, truth_b = [1]*4+[0]*4, [0]*4+[1]*4
    truthful = [p]*4+[1-p]*4
    honest_expected = p*check.execution(truthful, truth_a)+(1-p)*check.execution(truthful, truth_b)
    deterministic_expected = p*check.execution(truth_a, truth_a)+(1-p)*check.execution(truth_a, truth_b)
    assert honest_expected < deterministic_expected == p


def test_production_raw_score_matches_independent_integrals(production):
    check = independent_checker()
    for i in range(101):
        q = F(i, 100)
        for y in (0, 1):
            assert production.raw_loss(float(q), y) == pytest.approx(float(check.candidate_loss(q, y)), abs=2e-14)


@pytest.mark.parametrize('q,y', [(-.1,0), (1.1,1), (float('nan'),0),
                                  (float('inf'),1), (True,0), (.5,2), (.5,-1)])
def test_raw_loss_invalid_arguments_rejected(production, q, y):
    with pytest.raises(ValueError):
        production.raw_loss(q, y)


@pytest.mark.parametrize('report,truth', [([],[]), ([.5],[0,1]), ([.5,.5],[0])])
def test_reward_rejects_empty_or_unmatched_vectors(production, report, truth):
    with pytest.raises(ValueError):
        production.execution_reward(report, truth)


def test_k20_half_real_controls_and_oracle(production):
    truth = [0]*10+[1]*10
    assert production.execution_reward(truth, truth) == pytest.approx(1)
    assert production.execution_reward([0]*20, truth) == 0
    assert production.execution_reward([1]*20, truth) == 0
    assert production.execution_reward([.5]*20, truth) == pytest.approx(1/36)


def test_reference_is_fixed_not_reject_all_truth_dependent(production):
    # Artificial mathematical vectors only; construction will use r=10.
    check = independent_checker()
    for real_count in (1, 9, 10, 11, 19):
        truth = [1]*real_count+[0]*(20-real_count)
        for value in (F(1, 4), F(1, 2), F(3, 4)):
            probabilities = [value]*20
            actual = production.execution_reward([float(value)]*20, truth)
            assert actual == pytest.approx(float(check.execution(probabilities, truth)), abs=2e-13)


def test_nonconstant_vectors_checker_agreement(production):
    check = independent_checker()
    # Deterministic arithmetic fixtures, no data seeds or policy executions.
    for shift in range(40):
        report = [F((7*i+shift)%101, 100) for i in range(20)]
        truth = [int((i+shift)%2 == 0) for i in range(20)]
        assert production.execution_reward([float(q) for q in report], truth) == pytest.approx(float(check.execution(report, truth)), abs=3e-13)


@pytest.mark.parametrize('primary,replay', [(1,.4), (.3,1), (.8,.6), (0,1)])
def test_primary_replay_min_not_product(production, primary, replay):
    assert production.combine_executions(primary, replay) == min(primary, replay)


@pytest.mark.parametrize('flags', [{'valid_schema':False}, {'safe_execution':False}, {'tamper':True}])
def test_security_and_schema_flags_hard_zero(production, flags):
    assert production.combine_executions(1, 1, **flags) == 0


def test_submission_exact_ids_numeric_probabilities(production):
    ids = ['s'+str(i) for i in range(20)]
    probabilities = {name: i/20 for i, name in enumerate(ids)}
    assert production.parse_submission(json.dumps(probabilities), ids) == probabilities


@pytest.mark.parametrize('kind', ['missing', 'extra', 'bool', 'negative', 'above_one',
                                 'nan', 'infinity', 'string', 'list', 'null', 'duplicate'])
def test_submission_rejects_invalid_output(production, kind):
    ids = ['s'+str(i) for i in range(20)]
    payload = dict.fromkeys(ids, .5)
    if kind == 'missing':
        del payload['s0']
    elif kind == 'extra':
        payload['unexpected'] = .5
    elif kind in {'bool', 'negative', 'above_one', 'nan', 'infinity', 'string', 'null'}:
        payload['s0'] = {'bool':True, 'negative':-.01, 'above_one':1.01,
                         'nan':float('nan'), 'infinity':float('inf'), 'string':'.5', 'null':None}[kind]
    encoded = json.dumps(payload)
    if kind == 'list':
        encoded = json.dumps([.5]*20)
    if kind == 'duplicate':
        encoded = encoded[:-1]+', "s0": 0.9}'
    with pytest.raises(ValueError):
        production.parse_submission(encoded, ids)
