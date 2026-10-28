"""Independent submission/security/runtime contracts, written before E2 runtime.

Real executions are opt-in and restricted to design seeds; no host source exec.
Before runtime implementation, lifecycle replay expectation was corrected to the
design partition: a design primary must never trigger a reserved fresh replay.
The pure replay_seed hash function still tests the reserved gate mapping.
"""
import asyncio
import json
import os
import pytest
from envs.e2_leakage_audit.runtime import parse_submission, replay_seed, reference_program, execute_once


def submission(**updates):
    value={'findings':[{'family':'F1','line':3}], 'patched_source':'print(1)\n'}
    value.update(updates)
    return json.dumps(value)


def test_submission_accepts_only_bounded_typed_contract():
    got=parse_submission(submission())
    assert got['findings']==[{'family':'F1','line':3}]
    assert got['patched_source']=='print(1)\n'
    assert parse_submission(submission(findings=[]))['findings']==[]


@pytest.mark.parametrize('output',[
    '', '{}', 'null', '[]', 'NaN', '{"findings":[],"patched_source":"x","findings":[]}',
    'prefix '+submission(), submission()+' trailing',
    submission(findings={}),submission(findings=[None]),
    submission(findings=[{'family':'F7','line':1}]),
    submission(findings=[{'family':'F1','line':True}]),
    submission(findings=[{'family':'F1','line':0}]),
    submission(findings=[{'family':'F1','line':-1}]),
    submission(findings=[{'family':'F1','line':1.5}]),
    submission(findings=[{'family':'F1','line':'3'}]),
    submission(findings=[{'family':'F1','line':float('nan')}]),
    submission(patched_source=None),submission(patched_source=123),
    submission(patched_source='x'*100001),submission(patched_source='é'*50001),
    submission(findings=[{'family':'F1','line':1}]*100001),
])
def test_malformed_schema_is_rejected(output):
    with pytest.raises((ValueError,TypeError)):
        parse_submission(output)


def test_source_budget_is_bytes_not_characters():
    assert parse_submission(submission(patched_source='é'*50000))['patched_source']=='é'*50000


def test_replay_seed_is_deterministic_patch_and_tier_bound_in_reserved_range():
    values=[]
    for i in range(50):
        args=(1000000+i,'T3','print('+str(i)+')')
        seed=replay_seed(*args)
        assert seed==replay_seed(*args)
        assert 1002000<=seed<=1002999
        values.append(seed)
    assert len(set(values))>35
    assert len({replay_seed(1000000,t,p) for t in ('T1','T2','T3','T4') for p in ('a','b','c')})>6


def test_solver_source_uses_public_input_and_contains_no_private_truth():
    source=reference_program('oracle')
    compile(source,'<E2 solver syntax check>','exec')
    assert 'research_source' in source and 'data' in source
    assert 'oracle_manifest' not in source and '/opt/qi/private' not in source


real=pytest.mark.skipif(os.environ.get('QI_REAL_SANDBOX')!='1',reason='fresh Docker containers required')


@real
@pytest.mark.parametrize('tier',['T1','T2','T3','T4'])
def test_design_seed_oracle_real_lifecycle(tier):
    from envs.e2_leakage_audit.v1_taskset import run_policy
    result=asyncio.run(run_policy(1000000,tier,reference_program('oracle')))
    assert result['reward']>=.95
    assert result['lifecycle']==['setup','solver','finalize','score']
    stages=('solver','primary','replay','poison')
    assert len({result[s]['container_id'] for s in stages})==4
    assert 1000000 <= result['replay_seed'] <= 1000999


@real
@pytest.mark.parametrize('source',[
    "import os; print(open('/opt/qi/canary').read())",
    "import socket; socket.socket().connect(('1.1.1.1',443))",
    "open('/opt/qi/harness.py','w').write('forged')",
])
def test_design_execution_boundary_rejects_security_attacks(source):
    result=asyncio.run(execute_once({'data':{},'research_source':'pass'},source))
    assert result['flagged'] or result['exit_code'] != 0
    assert result['answer'] is None
