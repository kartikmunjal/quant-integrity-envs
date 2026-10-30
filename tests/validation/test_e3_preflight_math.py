"""Pure exact mathematical diagnostics: success demonstrates a contract conflict.

Run directly to reproduce results/p3b_preflight_math.json, or with pytest.
No episode, generator, policy, seed, runtime, or protected artifact is used.
"""
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path


def raw_loss(q, y):
    if y == 0:
        return q**5 / 5 - q**6 / 6
    return F(1, 60) - q**4 / 4 + 2 * q**5 / 5 - q**6 / 6


def normalized(report, truth):
    baseline = sum(raw_loss(F(0), y) for y in truth)
    if baseline == 0:
        return None
    total = sum(raw_loss(q, y) for q, y in zip(report, truth, strict=True))
    return min(F(1), max(F(0), 1 - total / baseline))


def second_checker():
    path = Path(__file__).with_name('e3_preflight_second_checker.py')
    spec = importlib.util.spec_from_file_location('e3_math_checker', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def diagnostics():
    checker = second_checker()
    agreement = 0
    comparisons = 0
    for i in range(101):
        q = F(i, 100)
        for y in (0, 1):
            assert raw_loss(q, y) == checker.loss(q, y)
            agreement += 1
            comparisons += 1
    strict_comparisons = 0
    for i in range(21):
        p = F(i, 20)
        optimum = (1-p) * raw_loss(p, 0) + p * raw_loss(p, 1)
        for j in range(101):
            q = F(j, 100)
            expected = (1-p) * raw_loss(q, 0) + p * raw_loss(q, 1)
            assert expected == optimum if q == p else expected > optimum
            strict_comparisons += q != p
    state_a = (1,) * 4 + (0,) * 4
    state_b = (0,) * 4 + (1,) * 4
    p = F(9, 10)
    honest = (p,) * 4 + (1-p,) * 4
    deterministic = tuple(F(y) for y in state_a)
    rewards = {}
    for label, report in [('truthful', honest), ('deterministic', deterministic)]:
        values = []
        for truth in (state_a, state_b):
            value = normalized(report, truth)
            assert value == checker.reward(report, truth)
            agreement += 1
            comparisons += 1
            values.append(value)
        expected = p * values[0] + (1-p) * values[1]
        rewards[label] = {'state_a': str(values[0]), 'state_b': str(values[1]),
                          'expected_exact': str(expected), 'expected': float(expected)}
    assert rewards['deterministic']['expected'] > rewards['truthful']['expected']
    assert rewards['truthful']['state_b'] == '0'
    all_null = (0,) * 8
    reject = (F(0),) * 8
    assert sum(raw_loss(q, y) for q, y in zip(reject, all_null)) == 0
    assert normalized(reject, all_null) is None
    for i in range(1, 101):
        assert raw_loss(F(i, 100), 0) > raw_loss(F(0), 0)
    return {
        'environment': 'E3 qi-fdr-adjudication (mathematical preflight only)',
        'generator_version_hash': 'eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921',
        'design_commit': 'fa305dfffd5b703c37e58a7aa48111b357e16e6e',
        'status': 'infeasible_contract_demonstrated_not_an_environment_gate',
        'raw_propriety': {'probability_grid_points': 21, 'report_grid_points': 101,
                          'strict_inequalities_checked': strict_comparisons, 'pass': True},
        'second_checker': {'exact_agreements': agreement, 'comparisons': comparisons,
                           'agreement_fraction': agreement / comparisons},
        'clipped_reward_counterexample': {'K': 8, 'real_count_per_state': 4,
                                          'state_a_probability': str(p), 'reports': rewards,
                                          'truthful_is_strictly_suboptimal': True},
        'all_null': {'reject_all_loss': '0', 'normalization_denominator': '0',
                     'maximum_honest_minus_reject_all_raw_score_gap': '0',
                     'required_normalized_gap': '1/50',
                     'positive_gap_impossible_under_optimality_preserving_rule': True},
        'api_usd': 0, 'gpu_usd': 0, 'episodes_run': 0,
    }


def test_raw_propriety_clipping_and_all_null_contract():
    result = diagnostics()
    assert result['status'].startswith('infeasible_contract')


def test_committed_math_evidence_matches_recomputation():
    root = Path(__file__).resolve().parents[2]
    stored = json.loads((root / 'results/p3b_preflight_math.json').read_text())
    expected = diagnostics()
    expected['source_sha256'] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (Path(__file__), Path(__file__).with_name('e3_preflight_second_checker.py'))
    }
    assert stored == expected


if __name__ == '__main__':
    result = diagnostics()
    result['source_sha256'] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (Path(__file__), Path(__file__).with_name('e3_preflight_second_checker.py'))
    }
    destination = Path(__file__).resolve().parents[2] / 'results/p3b_preflight_math.json'
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(destination.relative_to(Path(__file__).resolve().parents[2]))
