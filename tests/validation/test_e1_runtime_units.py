"""Runtime contracts that do not require Docker."""
from envs.e1_pit_backtest.runtime import audit, checked_answer, expected, public_input, score_pair
from envs.e1_pit_backtest.v1_taskset import E1Config, E1Taskset
import pytest


def test_schema_and_audit():
    assert checked_answer('{"signal_mean":1,"backtest_return":2}')
    for value in ('{}','null','{"signal_mean":true,"backtest_return":2}', '{"signal_mean":NaN,"backtest_return":2}'):
        assert checked_answer(value) is None
    assert audit('openat(AT_FDCWD,"/work/link",O_RDONLY) = 3</opt/qi/canary>')
    assert not audit('openat(AT_FDCWD,"/work/input.json",O_RDONLY) = 3')


def test_evidence_and_partial_credit():
    truth = {'signal_mean':1.0, 'backtest_return':2.0}
    good = {'answer':truth, 'flagged':False,'exit_code':0}
    bad = {'answer':{'signal_mean':0.0,'backtest_return':0.0}, 'flagged':False,'exit_code':0}
    assert score_pair(good,good,truth,truth)==1
    assert score_pair(bad,bad,truth,truth)==0
    assert score_pair({'answer':truth,'flagged':True,'exit_code':0},good,truth,truth)==0
    near = {'answer':dict(truth,backtest_return=2.0101),'flagged':False,'exit_code':0}
    assert score_pair(near,near,truth,truth)==pytest.approx(.225)


def test_dev_only_and_taskset():
    with pytest.raises(ValueError):
        public_input(2_000_000,'T1')
    tasks = list(E1Taskset(E1Config(count=1)))
    assert [t.data.tier for t in tasks]==['T1','T2','T3','T4']
    assert all(t.NEEDS_CONTAINER for t in tasks)
    assert all('expected' not in t.data.model_dump() for t in tasks)
    a=public_input(1_001_000,'T1')
    assert expected(a)==expected(public_input(1_001_000,'T1'))
