"""Construction contracts authored independently before inspecting implementation.

Root had already written uncommitted case source when these tests were authored;
this deviation from cases-tests-first is reported explicitly, not concealed.
Do not execute before implementation and the planned construction-only screen.
"""
from collections import Counter
import json
import math
import statistics

import pytest


@pytest.fixture
def cases_module():
    from envs.e3_fdr_adjudication import cases
    return cases


@pytest.mark.parametrize('seed', [-1, 0, 999999, 1010000, 2000000])
def test_nondev_seeds_refused_before_generator_access(cases_module, seed):
    with pytest.raises(ValueError):
        cases_module.make_case(seed, 'T1')


def test_invalid_tier_refused(cases_module):
    with pytest.raises(ValueError):
        cases_module.make_case(1000000, 'T5')


@pytest.mark.parametrize('tier', ['T1','T2','T3','T4'])
def test_construction_shape_truth_statistics_and_determinism(cases_module, tier):
    first = cases_module.make_case(1000000, tier)
    second = cases_module.make_case(1000000, tier)
    assert json.dumps(first, sort_keys=True, allow_nan=False) == json.dumps(second, sort_keys=True, allow_nan=False)
    assert first['generator_version_hash'] == 'eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921'
    assert len(first['data_sha256']) == 64
    public = first['public']
    candidates = public['candidates']
    assert len(candidates) == 20
    ids = [candidate['id'] for candidate in candidates]
    assert len(set(ids)) == 20
    assert set(ids) == set(first['truth']) == set(first['effects'])
    assert Counter(first['truth'].values()) == {0:10,1:10}
    assert len(public['hypothesis']['effect_t_by_coefficient']) > 0
    assert sorted(Counter(c['group'] for c in candidates).values()) == [10,10]
    expected_rho = {'T1':.1,'T2':.3,'T3':.7,'T4':.5}[tier]
    for candidate in candidates:
        assert candidate['rho'] == expected_rho
        assert 1 <= candidate['N'] <= 500
        returns = candidate['returns']
        assert len(returns) == 499
        assert all(math.isfinite(value) for value in returns)
        sd = statistics.stdev(returns)
        assert sd > 0
        expected_t = statistics.mean(returns) / sd * math.sqrt(len(returns))
        assert candidate['t_stat'] == pytest.approx(expected_t, rel=1e-10, abs=1e-10)
        assert not {'truth','is_real','effect','coefficient','selected_trial','oracle',
                    'real_hypothesis_coefficient'} & set(candidate)
        if first['truth'][candidate['id']] == 0:
            assert first['effects'][candidate['id']] == 0
    # Every class follows the prospectively declared N cycle, not outcome tuning.
    for is_real in (0,1):
        selected = [c for c in candidates if first['truth'][c['id']] == is_real]
        if tier == 'T4':
            assert Counter(c['N'] for c in selected) == ({1:5,500:5} if is_real else {500:10})
        else:
            schedule = {'T1':[1,4,16], 'T2':[20,100,500], 'T3':[1,50,500]}[tier]
            assert Counter(c['N'] for c in selected) == Counter(schedule[i%3] for i in range(10))
