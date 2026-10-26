"""Prospective real lifecycle and replay contracts, before E6 runtime code."""
import os
import pytest
from envs.e6_data_traps.runtime import reference_program,replay_seed
from envs.e6_data_traps.v1_taskset import run_policy
from qi_runtime import CheckedRuntime

pytestmark=pytest.mark.skipif(os.environ.get('QI_REAL_SANDBOX')!='1',reason='real Docker required')

@pytest.mark.asyncio
async def test_oracle_real_lifecycle_shared_runtime_and_source_binding():
    from envs.e6_data_traps.v1_taskset import E6Runtime
    assert E6Runtime is CheckedRuntime
    v=await run_policy(1007000,'T4',reference_program())
    assert v['reward']==1 and not v['flagged']
    assert v['lifecycle']==['setup','solver','finalize','score']
    assert len({v[s]['container_id'] for s in ('solver','primary','replay')})==3
    assert all(v[s]['source_sha256']==v['source_sha256'] for s in ('solver','primary','replay'))

@pytest.mark.asyncio
async def test_wrong_identity_and_flagged_replay_fail():
    wrong=await run_policy(1007000,'T1',reference_program('ignore_identifiers'))
    assert wrong['reward']==0
    from scripts.e6_policies import policies,source_for
    p,_,_=policies()
    v=await run_policy(1007000,'T4',source_for('flagged_replay',1007000,'T4',p))
    assert v['reward']==0 and v['flagged'] and not v['primary']['flagged']
