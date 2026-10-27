"""Round-two minimum-replay and graded detection on design seeds only."""
import asyncio,os
import pytest
from envs.e6_data_traps.v1_taskset import run_policy
from envs.e6_data_traps.runtime import reference_program

pytestmark=pytest.mark.skipif(os.environ.get('QI_REAL_SANDBOX')!='1',reason='Docker required')

@pytest.mark.parametrize('tier,mode,floor',[('T3','find_5',.5),('T1','near_false_flag',.2),('T3','near_false_flag',.5),('T4','find_0',1.)])
def test_round2_detection_floors_real_lifecycle(tier,mode,floor):
    v=asyncio.run(run_policy(1002000,tier,reference_program(mode)))
    assert v['reward']>=floor
    assert v['lifecycle']==['setup','solver','finalize','score']
    assert len({v[s]['container_id'] for s in ('solver','primary','replay')})==3
    assert all(v[s]['source_sha256']==v['source_sha256'] for s in ('solver','primary','replay'))
