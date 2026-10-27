"""Prospective real lifecycle and replay contracts, before E6 runtime code."""
import os
import asyncio
import pytest
from envs.e6_data_traps.runtime import reference_program,replay_seed
from envs.e6_data_traps.v1_taskset import run_policy
from qi_runtime import CheckedRuntime

pytestmark=pytest.mark.skipif(os.environ.get('QI_REAL_SANDBOX')!='1',reason='real Docker required')

def test_oracle_real_lifecycle_shared_runtime_and_source_binding():
    from envs.e6_data_traps.v1_taskset import E6Runtime
    assert E6Runtime is CheckedRuntime
    v=asyncio.run(run_policy(1007000,'T4',reference_program()))
    assert v['reward']==1 and not v['flagged']
    assert len(v['oracle_sha256'])==64
    assert v['lifecycle']==['setup','solver','finalize','score']
    assert len({v[s]['container_id'] for s in ('solver','primary','replay')})==3
    assert all(v[s]['source_sha256']==v['source_sha256'] for s in ('solver','primary','replay'))

def test_wrong_identity_and_flagged_replay_fail():
    wrong=asyncio.run(run_policy(1007000,'T1',reference_program('ignore_identifiers')))
    assert wrong['reward']==0
    from scripts.e6_policies import policies,source_for
    p,_,_=policies()
    v=asyncio.run(run_policy(1007000,'T4',source_for('flagged_replay',1007000,'T4',p)))
    assert v['reward']==0 and v['flagged'] and not v['primary']['flagged']


@pytest.mark.parametrize('name,tier,expected',[
    ('random','T1','zero'),('near_miss','T2','partial'),
    ('near_small','T3','partial'),('near_false_flag','T4','partial'),
    ('never_flag','T1','zero'),('never_flag','T4','full')])
def test_runtime_policy_semantics_on_design_only(name,tier,expected):
    from scripts.e6_policies import policies,source_for
    available,_,_=policies()
    value=asyncio.run(run_policy(1007000,tier,source_for(name,1007000,tier,available)))
    if expected=='zero':assert value['reward']==0
    elif expected=='full':assert value['reward']==1
    else:assert 0<value['reward']<1
