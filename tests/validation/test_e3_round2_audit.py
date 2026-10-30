"""Independent raw-record audit tests using arithmetic fixtures only."""
import copy
import importlib.util
from pathlib import Path

import pytest


def checker():
    path = Path(__file__).with_name('e3_round2_checker.py')
    spec = importlib.util.spec_from_file_location('e3_independent_audit',path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture():
    truth = {'p'+str(i):i%2 for i in range(20)}
    replay_truth = {'r'+str(i):i%2 for i in range(20)}
    return {'solver':{'flagged':False},'schema_ok':True,'security_ok':True,
            'truth':truth,'replay_truth':replay_truth,
            'primary':{'answer':dict(truth),'flagged':False,'exit_code':0},
            'replay':{'answer':dict(replay_truth),'flagged':False,'exit_code':0}}


def test_audit_ignores_reported_reward_and_combines_min():
    module = checker()
    record = fixture()
    record['reward'] = -.7  # Deliberately wrong stored summary, never consumed.
    assert module.audit_record(record) == pytest.approx(1)
    record['replay']['answer'] = dict.fromkeys(record['replay_truth'],.5)
    assert module.audit_record(record) == pytest.approx(1/36)
    record['primary']['answer'] = dict.fromkeys(record['truth'],.5)
    assert module.audit_record(record) == pytest.approx(1/36)  # not product


@pytest.mark.parametrize('failure', ['solver_flag','primary_flag','replay_flag',
                                   'schema_flag','security_flag','exit_primary','exit_replay',
                                   'missing_id','extra_id','nonfinite','bool','out_of_range',
                                   'missing_primary','missing_truth','missing_solver',
                                   'missing_security_evidence'])
def test_audit_all_hardzero_failures(failure):
    record = copy.deepcopy(fixture())
    if failure == 'solver_flag': record['solver']['flagged']=True
    elif failure == 'primary_flag': record['primary']['flagged']=True
    elif failure == 'replay_flag': record['replay']['flagged']=True
    elif failure == 'schema_flag': record['schema_ok']=False
    elif failure == 'security_flag': record['security_ok']=False
    elif failure == 'exit_primary': record['primary']['exit_code']=1
    elif failure == 'exit_replay': record['replay']['exit_code']=1
    elif failure == 'missing_id': del record['replay']['answer']['r0']
    elif failure == 'extra_id': record['replay']['answer']['foreign']=.5
    elif failure == 'nonfinite': record['primary']['answer']['p0']=float('nan')
    elif failure == 'bool': record['primary']['answer']['p0']=False
    elif failure == 'out_of_range': record['primary']['answer']['p0']=1.1
    elif failure == 'missing_primary': record['primary']=None
    elif failure == 'missing_truth': record['replay_truth']=None
    elif failure == 'missing_solver': del record['solver']
    elif failure == 'missing_security_evidence': del record['replay']['flagged']
    assert checker().audit_record(record) == 0
