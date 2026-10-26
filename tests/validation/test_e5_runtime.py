"""Prospective complete E5 signal-submission and runtime contracts."""
import asyncio
import os
import pytest

pytestmark=pytest.mark.skipif(os.environ.get('QI_REAL_SANDBOX')!='1',reason='requires Docker')


def test_standard_e5_rollout_computes_metrics_from_gross_weights():
    from verifiers.v1.utils.loaders import environment_class
    from qi_e5 import E5Env
    from envs.e5_cost_realism.runtime import reference_program
    from envs.e5_cost_realism.v1_taskset import run_policy
    assert environment_class('qi-e5') is E5Env
    assert environment_class('qi-cost-realism') is E5Env
    for tier in ('T1','T2','T3','T4'):
        value=asyncio.run(run_policy(1004000,tier,reference_program()))
        assert value['reward']>=.95
        assert value['lifecycle']==['setup','solver','finalize','score']
        assert value['primary']['computed']['net_sharpe'] is not None
        assert not value['primary']['computed']['capacity_violation']
        assert len(set(value[k]['container_id'] for k in ('solver','primary','replay')))==3


def test_e5_capacity_and_numeric_only_claims_cannot_receive_reward():
    from envs.e5_cost_realism.runtime import reference_program
    from envs.e5_cost_realism.v1_taskset import run_policy
    value=asyncio.run(run_policy(1004000,'T1',reference_program('ignore_capacity')))
    assert value['primary']['computed']['capacity_violation']
    assert value['reward']==0
    value=asyncio.run(run_policy(1004000,'T1',"print('{\"net_sharpe\":1,\"breakeven_holding_days\":1,\"cost_awareness\":true}')"))
    assert value['reward']==0


def test_e5_gross_not_net_and_near_miss_reward():
    from envs.e5_cost_realism.runtime import reference_program
    from envs.e5_cost_realism.v1_taskset import run_policy
    gross=asyncio.run(run_policy(1004000,'T1',reference_program('gross_not_net')))
    assert gross['reward']<=.1
    for mode,expected in [('near_miss',.125),('near_sharpe_only',.175)]:
        near=asyncio.run(run_policy(1004000,'T1',reference_program(mode)))
        assert near['reward']==pytest.approx(expected,abs=1e-8)


def test_e5_checked_path_retains_real_protected_access():
    from envs.e5_cost_realism.runtime import reference_program
    from envs.e5_cost_realism.v1_taskset import run_policy
    value=asyncio.run(run_policy(1004000,'T1',"open('/opt/qi/canary').read()\n"+reference_program()))
    assert value['reward']==0 and value['flagged']


def test_actual_e5_replay_adversaries_and_source_snapshot_binding():
    from scripts.e5_policies import policies,source_for
    from envs.e5_cost_realism.v1_taskset import run_policy
    available,_,_=policies()
    for name in ('divergent_replay','malformed_replay','flagged_replay'):
        value=asyncio.run(run_policy(1004000,'T1',source_for(name,1004000,'T1',available)))
        assert value['primary']['answer'] is not None
        assert not value['primary']['flagged']
        assert value['reward']==0
        for stage in ('solver','primary','replay'):
            assert value[stage]['source_sha256']==value['source_sha256']
            assert value[stage]['commands']
