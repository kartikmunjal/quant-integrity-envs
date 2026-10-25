"""Prospective E1 checked Env/runtime contracts; design seeds only."""
import asyncio
import os
import tempfile
from pathlib import Path
import pytest

pytestmark=pytest.mark.skipif(os.environ.get('QI_REAL_SANDBOX')!='1',reason='requires Docker')


def test_standard_env_is_selected_and_runs_a_complete_rollout():
    from verifiers.v1.utils.loaders import environment_class
    from qi_e1 import E1Env
    from envs.e1_pit_backtest.runtime import reference_program
    from envs.e1_pit_backtest.v1_taskset import run_policy
    assert environment_class('qi-e1') is E1Env
    value=asyncio.run(run_policy(1001000,'T1',reference_program()))
    assert value['reward']==1
    assert value['lifecycle']==['setup','solver','finalize','score']
    ids=[value[key]['container_id'] for key in ('solver','primary','replay')]
    assert len(set(ids))==3


def test_read_api_is_audited_and_source_transfer_is_bounded():
    from envs.e1_pit_backtest.runtime import E1Runtime,WORK
    async def run():
        with tempfile.TemporaryDirectory(prefix='e1-',dir=WORK) as directory:
            work=Path(directory);work.chmod(0o777)
            r=E1Runtime(work)
            try:
                await r.start()
                await r._read('/opt/qi/canary')
                assert r.flagged
                with pytest.raises(ValueError): await r.write('/work/program.py',b'x'*100001)
                await r.run(['python','-c',"open('/work/program.py','w').write('x'*100001)"],{})
                with pytest.raises(ValueError): await r.read('/work/program.py',max_bytes=100000)
                await r.run(['sh','-c','ln -s /opt/qi/canary /work/link'],{})
                with pytest.raises(ValueError): await r.read('/work/link',max_bytes=100000)
            finally: await r.stop()
    asyncio.run(run())


def test_external_runtime_is_refused():
    from envs.e1_pit_backtest.v1_taskset import E1Task,E1Data
    class Other: pass
    with pytest.raises(ValueError):
        asyncio.run(E1Task(E1Data(seed=1001000,tier='T1')).setup(None,Other()))


def test_relative_protected_access_is_retained_even_after_catching_error():
    from envs.e1_pit_backtest.runtime import reference_program
    from envs.e1_pit_backtest.v1_taskset import run_policy
    prefixes=["import os;os.chdir('/opt/qi');open('canary').read()\n",
        "import os;os.chdir('/opt/qi')\ntry: open('harness','w').write('bad')\nexcept OSError: pass\nos.chdir('/work')\n"]
    for prefix in prefixes:
        result=asyncio.run(run_policy(1001000,'T1',prefix+reference_program()))
        assert result['flagged']
        assert result['reward']==0


def test_replay_adversaries_traverse_real_rollouts():
    from scripts.e1_policies import policies,source_for
    from envs.e1_pit_backtest.v1_taskset import run_policy
    available,_,_=policies()
    for name in ('divergent_replay','malformed_replay','flagged_replay'):
        result=asyncio.run(run_policy(1001000,'T1',source_for(name,1001000,'T1',available)))
        assert result['primary']['answer'] is not None
        assert not result['primary']['flagged']
        assert result['replay']['container_id']!=result['primary']['container_id']
        assert result['reward']==0


def test_initial_solver_failure_is_retained_and_zeroed():
    from envs.e1_pit_backtest.v1_taskset import run_policy
    result=asyncio.run(run_policy(1001000,'T1','raise SystemExit(7)'))
    assert result['solver']['flagged']
    assert result['solver']['commands'][0]['exit_code']==7
    assert result['reward']==0
