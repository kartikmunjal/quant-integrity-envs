"""Prospective independent tests: SPEC + committed P3a design, before code."""
import random
import pytest
from p3a_scalar_checker import check_record, matching, quality
from envs.e2_leakage_audit.reward import (
    grade_record, match_findings, patch_quality, score_components,
)


def record(n=3):
    truth = [{'family': f'F{i+1}', 'line': 10*i+1, 'end_line': 10*i+3} for i in range(n)]
    return dict(truth=truth, findings=[{'family': t['family'], 'line': t['line']} for t in truth],
                primary_error=0., replay_error=0., poison_error=0., schema_ok=True, security_ok=True)


@pytest.mark.parametrize('p', [1, 2, 3])
def test_partial_detection_and_false_flag_are_graded(p):
    r = record()
    grades = []
    for k in range(4):
        candidate = dict(r, findings=r['findings'][:k])
        grades.append(grade_record(candidate, p))
    assert all(a < b for a, b in zip(grades, grades[1:]))
    assert grades[2] >= .5
    extra = dict(r, findings=r['findings']+[{'family':'F6', 'line':999}])
    assert 0 < grade_record(extra, p) < 1
    clean = dict(record(0), findings=[{'family':'F1','line':1}])
    assert 0 < grade_record(clean, p) < 1
    assert grade_record(record(0), p) == pytest.approx(1)


def test_harmonic_weights_enter_once():
    for d,p,c in ((.6,.4,.8),(.8,1,1),(1,.5,.25),(1,1,1)):
        assert score_components(d,p,c) == pytest.approx(1/(.4/d+.4/p+.2/c))
    for components in ((0,1,1),(1,0,1),(1,1,0)):
        assert score_components(*components) == 0


def test_numeric_quality_continuous_monotone_and_bounded():
    values = [patch_quality(i/100000) for i in range(1101)]
    assert values[0] == values[10] == 1
    assert values[1000] == values[1100] == 0
    assert all(0 <= v <= 1 for v in values)
    assert all(a >= b for a,b in zip(values,values[1:]))
    assert patch_quality(.00505) == pytest.approx(.5)


def test_matching_is_one_to_one_not_family_presence_or_greedy():
    truth = [{'family':'F1','line':1,'end_line':3},{'family':'F1','line':2,'end_line':2}]
    findings = [{'family':'F1','line':2},{'family':'F1','line':1}]
    assert match_findings(findings,truth) == matching(findings,truth) == (2,0,0)
    findings += [findings[0], {'family':'F2','line':1}, {'family':'F1','line':999}]
    assert match_findings(findings,truth) == (2,3,0)


@pytest.mark.parametrize('key', ['primary_error','replay_error','poison_error'])
def test_disabled_constant_incomplete_or_primary_only_patch_is_zero(key):
    r=record(); r[key]=1.
    assert grade_record(r, 1) == 0


@pytest.mark.parametrize('key', ['schema_ok','security_ok'])
def test_hard_gates(key):
    r=record(); r[key]=False
    assert grade_record(r, 1) == 0


def test_2000_independent_adversarial_scalar_records():
    rng=random.Random(1000000)
    for i in range(2000):
        r=record(i%4)
        r['findings']=r['findings'][:rng.randrange(len(r['findings'])+1)]
        r['findings'] += [{'family': f'F{rng.randrange(1,7)}', 'line':rng.randrange(1,35)} for _ in range(i%5)]
        for key in ('primary_error','replay_error','poison_error'):
            r[key]=rng.choice([0.,.0001,.00010001,.002,.00505,.009999,.01,1.])
        r['schema_ok']=i%41 != 0; r['security_ok']=i%43 != 0
        p=1+i%3
        assert grade_record(r,p) == pytest.approx(check_record(r,p),abs=1e-12)
        assert patch_quality(r['primary_error']) == pytest.approx(quality(r['primary_error']),abs=1e-12)
