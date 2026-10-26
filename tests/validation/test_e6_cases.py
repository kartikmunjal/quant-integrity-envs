"""Prospective E6 task-layer corruption contracts; written before implementation."""
import copy
import pytest
from envs.e6_data_traps.cases import make_case,public_input
from envs.e6_data_traps.repair import reconstruct

@pytest.mark.parametrize('tier',['T1','T2','T3','T4'])
def test_corruptions_are_real_records_and_events_are_clean_decoys(tier):
    c=make_case(1007000,tier);data=c['public'];truth=c['truth']
    assert reconstruct(data)=={'universe':truth['universe'],'anomalies':truth['anomalies']}
    assert len(truth['corruptions'])=={'T1':1,'T2':2,'T3':6,'T4':0}[tier]
    assert all(x['before']!=x['after'] for x in truth['corruptions'])
    assert {a['kind'] for a in data['actions']} >= {'split','identifier','delisting'}
    assert all(v>=.02 for v in c['diagnostics']['conceptual_gaps'].values())
    assert make_case(1007000,tier)==c
    assert 'truth' not in public_input(1007000,tier)
    if tier=='T4':assert not reconstruct(data)['anomalies']


def test_no_generator_or_sealed_seed_changes_and_no_shared_mutable_input():
    c=public_input(1007000,'T1');c['quotes'].clear()
    assert public_input(1007000,'T1')['quotes']
    with pytest.raises(ValueError):public_input(2000000,'T1')
