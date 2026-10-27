"""Prospective summary regressions, synthetic records only."""
import copy
from qi_runtime.gate_summary import summarize_gate


def record(index=0, reward=.5, complete=True):
    stages={s:{'container_id':f'{index}-{s}','source_sha256':'s','errors':[.001],
               'anomaly_ids':['a'],'answer_sha256':'a'} for s in ('solver','primary','replay')}
    return dict(index=index,seed=1005000+index,tier='T3',policy='find_5',complete=complete,
                attempts=[],checker_agrees=True,value=dict(reward=reward,flagged=False,
                lifecycle=['setup','solver','finalize','score'],source_sha256='s',oracle_sha256='a'*64,**stages),
                diagnostics={'conceptual_gaps':dict.fromkeys(('flag_large_moves','ignore_identifiers','ignore_splits','ticker_only'),.03),'corruptions':6})


def test_find_k_per_row_cannot_hide_compensating_deviations():
    expected=(10/11)**3
    rows=[record(i,expected+(-.01 if i%2 else .01)) for i in range(50)]
    result=summarize_gate(rows,{'wrong'},{'attack'})
    assert not result['tiers']['T3']['checks']['find_k_expected']


def test_incomplete_is_missing_and_not_fabricated_zero():
    row=record(complete=False)
    result=summarize_gate([row],{'wrong'},{'attack'})
    stats=result['tiers']['T3']['policies']['find_5']
    assert stats['mean_reward'] is None
    assert stats['reward_distribution']=={}
    assert stats['fractions']['zero_reward']==0
    assert stats['fractions']['missing_reward']==1
    assert not result['reward_gate_passed']


def test_compact_anomaly_counts_and_attempt_container_uniqueness():
    rows=[record(0),record(1)]
    for row in rows:
        row['attempts']=[{'resources':[{'container_id':'shared','event':'created'}]}]
    result=summarize_gate(rows,{'wrong'},{'attack'})
    assert result['tiers']['T3']['find_k_counts'][5]['retained_flags']=={'1':2}
    assert not result['containers_unique']


def test_repeated_events_in_one_attempt_are_not_reused_containers():
    row=record()
    row['attempts']=[{'resources':[{'container_id':'id','event':'created'},
                                 {'container_id':'id','event':'removed'}]}]
    result=summarize_gate([row],{'wrong'},{'attack'})
    assert result['containers_unique']


def test_missing_source_and_bad_lifecycle_are_blocking():
    row=record();row['value']['primary']['source_sha256']='different'
    row['value']['lifecycle']=[]
    checks=summarize_gate([row],{'wrong'},{'attack'})['tiers']['T3']['checks']
    assert not checks['source_binding'] and not checks['complete_rollouts']


def full_plan():
    names=['oracle','random','wrong','attack','near_miss','near_small','near_false_flag','never_flag',*(f'find_{k}' for k in range(7))]
    rows=[]
    for tier,n in [('T1',1),('T2',2),('T3',6),('T4',0)]:
        for name in names:
            for seed_index in range(500 if name=='oracle' else 50):
                reward=1. if name=='oracle' else .6 if name.startswith('near_') else (1. if tier=='T4' else 0.) if name=='never_flag' else 0.
                if name.startswith('find_'):
                    k=int(name[5:]);reward=(2*min(k,n)/(n+min(k,n)))**3 if n else 1.
                row=record(len(rows),reward)
                row.update(tier=tier,policy=name,seed=1005000+seed_index)
                row['diagnostics']['corruptions']=n
                if name=='oracle':row['unit_checker_agrees']=True
                rows.append(row)
    return rows


def test_complete_protocol_passes_and_all_oracles_are_checked():
    rows=full_plan()
    result=summarize_gate(rows,{'wrong'},{'attack'})
    assert result['reward_gate_passed']
    assert result['second_checker']['oracle_cases']==2000
    stats=result['tiers']['T4']
    assert stats['policies']['oracle']['n']==50
    assert stats['oracle_all_episode_fractions']['full_reward']==1
    # The first fifty remain perfect, but all-oracle population must fail.
    for row in rows:
        if row['tier']=='T4' and row['policy']=='oracle' and row['seed']>=1005050:
            row['value']['reward']=0
    result=summarize_gate(rows,{'wrong'},{'attack'})
    assert result['tiers']['T4']['checks']['oracle']
    assert not result['tiers']['T4']['checks']['oracle_all_episodes']
    assert not result['reward_gate_passed']
