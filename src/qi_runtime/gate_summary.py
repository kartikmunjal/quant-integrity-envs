"""Faithful E6 round-two gate criteria over infrastructure-attempt records.

Missing outcomes retain a fixed denominator and never become synthetic rewards.
This module only summarizes recorded evidence; it does not score submissions.
"""
from collections import Counter, defaultdict
from pathlib import Path
import yaml

TIERS=('T1','T2','T3','T4')
NEAR=('near_miss','near_small')
CONCEPTUAL=('flag_large_moves','ignore_identifiers','ignore_splits','ticker_only')


def _value(row):
    return row.get('value') if row.get('complete') else None


def _reward(row):
    value=_value(row)
    return value.get('reward') if value else None


def _false_positive(row):
    value=_value(row)
    return bool(value and (value.get('flagged') or any(value.get(s,{}).get('false_positive',False) for s in ('primary','replay'))))


def fractions(rows):
    n=len(rows)
    rewards=[_reward(r) for r in rows]
    numeric=Counter(dict.fromkeys(('within_full_tolerance','in_partial_band','at_or_beyond_zero_scale','invalid_or_flagged'),0))
    for row in rows:
        errors=(_value(row) or {}).get('primary',{}).get('errors')
        key=('invalid_or_flagged' if errors is None else 'within_full_tolerance' if errors[0]<=1e-4 else 'in_partial_band' if errors[0]<.01 else 'at_or_beyond_zero_scale')
        numeric[key]+=1
    def ratio(count):return count/n if n else None
    return {'full_reward':ratio(sum(v is not None and abs(v-1)<=1e-10 for v in rewards)),
            'partial_reward':ratio(sum(v is not None and 0<v<1-1e-10 for v in rewards)),
            'zero_reward':ratio(sum(v==0 for v in rewards)),
            'missing_reward':ratio(sum(v is None for v in rewards)),
            'primary_numeric_error_fractions':{key:ratio(count) for key,count in numeric.items()}}


def _mean(rows):
    rewards=[_reward(r) for r in rows]
    return sum(rewards)/len(rewards) if rewards and all(v is not None for v in rewards) else None


def _all(rows,predicate):
    return bool(rows) and all(_value(r) is not None and predicate(r) for r in rows)


def _flag_count(row):
    primary=(_value(row) or {}).get('primary',{})
    if 'anomaly_ids' in primary:return str(len(primary['anomaly_ids']))
    answer=primary.get('answer')
    return str(len(answer['anomalies'])) if answer else 'missing'


def _containers(rows):
    """One owner per row/attempt/stage; repeated create/remove events are one ID."""
    owners=defaultdict(set)
    for index,row in enumerate(rows):
        stage_ids={v.get('container_id') for s in ('solver','primary','replay') if (v:=(row.get('value') or {}).get(s,{})).get('container_id')}
        seen=set()
        for attempt_index,attempt in enumerate(row.get('attempts',[])):
            ids={r['container_id'] for r in attempt.get('resources',[]) if r.get('container_id')}
            for identity in ids:owners[identity].add((index,attempt_index))
            seen.update(ids)
        for identity in stage_ids-seen:owners[identity].add((index,'untracked'))
        # Stages must be distinct even when an attempt's event list deduplicates.
        ids=[(row.get('value') or {}).get(s,{}).get('container_id') for s in ('solver','primary','replay')]
        ids=[v for v in ids if v]
        if len(ids)!=len(set(ids)):
            return len(owners),False
    return len(owners),all(len(v)==1 for v in owners.values())


def summarize_gate(rows,wrong,attacks):
    limits=yaml.safe_load((Path(__file__).resolve().parents[2]/'prereg.yaml').read_text())['verifier_gates']
    names={'oracle','random',*wrong,*attacks,*NEAR,'near_false_flag','never_flag',*(f'find_{k}' for k in range(7))}
    tiers={}
    for tier in TIERS:
        grouped=defaultdict(list)
        for row in sorted(rows,key=lambda r:(r.get('seed',0),r.get('index',0))):
            if row.get('tier')==tier:grouped[row['policy']].append(row)
        stats={}
        for name in sorted(names):
            cell=grouped[name][:50];known=[_reward(r) for r in cell if _reward(r) is not None]
            stats[name]={'n':len(cell),'complete':len(known),'mean_reward':_mean(cell),
                         'flagged':sum(bool((_value(r) or {}).get('flagged')) for r in cell),
                         'false_positives':sum(_false_positive(r) for r in cell),
                         'errors':sum(not r.get('complete') or 'error' in (r.get('value') or {}) for r in cell),
                         'reward_distribution':dict(Counter(format(v,'.16g') for v in known)),
                         'fractions':fractions(cell)}
        all_tier=[r for group in grouped.values() for r in group]
        diagnostics=[r['diagnostics'] for r in all_tier if r.get('diagnostics')]
        oracles=grouped['oracle'];oracle_mean=_mean(oracles)
        def mean(name):return stats[name]['mean_reward']
        def bounded(name,lo=None,hi=None):
            value=mean(name)
            return value is not None and (lo is None or value>=lo) and (hi is None or value<=hi)
        n={'T1':1,'T2':2,'T3':6,'T4':0}[tier]
        expected={k:(2*min(k,n)/(n+min(k,n)))**3 if n else 1. for k in range(7)}
        checks={
            'planned_cells':set(grouped)==names and all(len(grouped[name])==(500 if name=='oracle' else 50) for name in names),
            'find_k_expected':all(_all(grouped[f'find_{k}'],lambda r,k=k:abs(_reward(r)-expected[k])<=1e-8) for k in range(7)),
            'five_of_six_floor':tier!='T3' or bounded('find_5',lo=.5),
            'one_false_flag_floor':bounded('near_false_flag',lo={'T1':.2,'T3':.5}.get(tier,0)),
            'oracle_all_episodes':oracle_mean is not None and oracle_mean>=limits['oracle_policy_min_mean_reward'],
            'oracle':bounded('oracle',lo=limits['oracle_policy_min_mean_reward']),
            'random':bounded('random',hi=limits['random_policy_max_mean_reward']),
            'wrong_individual':all(bounded(name,hi=limits['wrong_solution_max_mean_reward']) for name in wrong),
            'wrong_aggregate':bool(wrong) and all(mean(name) is not None for name in wrong) and sum(mean(name) for name in wrong)/len(wrong)<=limits['wrong_solution_max_mean_reward'],
            'cheaters':all(bounded(name,hi=limits['cheater_policy_max_mean_reward']) for name in attacks),
            'complete_rollouts':_all(all_tier,lambda r:r['value'].get('lifecycle')==['setup','solver','finalize','score'] and 'error' not in r['value']),
            'conceptual_separation':bool(all_tier) and len(diagnostics)==len(all_tier) and all(all(d.get('conceptual_gaps',{}).get(k,0)>=.02 for k in CONCEPTUAL) for d in diagnostics),
            'near_miss_partial':all(mean(name) is not None and 0<mean(name)<1 for name in NEAR),
            'false_flag_partial':_all(grouped['near_false_flag'],lambda r:0<_reward(r)<1),
            'never_flag_clean_semantics':_all(grouped['never_flag'],lambda r:_reward(r)==(1 if tier=='T4' else 0)),
            'oracle_truth_recorded':_all(all_tier,lambda r:type(r['value'].get('oracle_sha256')) is str and len(r['value']['oracle_sha256'])==64),
            'source_binding':_all(all_tier,lambda r:bool(r['value'].get('source_sha256')) and all(r['value'].get(s,{}).get('source_sha256')==r['value']['source_sha256'] for s in ('solver','primary','replay') if r['value'].get(s,{}).get('container_id')))}
        if tier=='T4':
            checks['clean_false_positive']=len(grouped['oracle'][:50])==50 and stats['oracle']['false_positives']/50<=limits['clean_episode_false_positive_ceiling']
            checks['clean_false_positive_all_oracles']=len(oracles)==500 and all(_value(r) for r in oracles) and sum(_false_positive(r) for r in oracles)/len(oracles)<=limits['clean_episode_false_positive_ceiling']
        total=len(all_tier)
        tiers[tier]={'policies':stats,'checks':checks,
            'find_k_counts':{k:{'requested_k':k,'n_corruptions':dict(Counter(str(r['diagnostics']['corruptions']) if r.get('diagnostics') else 'missing' for r in grouped[f'find_{k}'])), 'retained_flags':dict(Counter(_flag_count(r) for r in grouped[f'find_{k}'])),'expected_retained':min(k,n)} for k in range(7)},
            'minimum_gaps':{k:min((d.get('conceptual_gaps',{}).get(k,0) for d in diagnostics),default=None) for k in CONCEPTUAL},
            'composition':{'all_rollouts':{'n':total,'oracle_fraction':len(oracles)/total if total else None,'near_miss_fraction':sum(len(grouped[n]) for n in NEAR)/total if total else None},'policy_cells_first_50':{'n':sum(len(grouped[name][:50]) for name in names),'oracle_fraction':1/len(names),'near_miss_fraction':len(NEAR)/len(names)}},
            'oracle_all_episode_fractions':fractions(oracles)}
    comparisons=[r for r in rows if 'checker_agrees' in r and r.get('complete')]
    units=[r for r in rows if 'unit_checker_agrees' in r and r.get('complete')]
    agreement=sum(bool(r['checker_agrees']) for r in comparisons)/len(rows) if rows else 0
    unit_agreement=sum(bool(r['unit_checker_agrees']) for r in units)/len(units) if units else 0
    oracle_cases=sum(r.get('complete',False) and r.get('policy')=='oracle' for r in rows)
    count,unique=_containers(rows)
    passed=all(all(t['checks'].values()) for t in tiers.values()) and oracle_cases>=2000 and agreement>=limits['dual_checker_min_agreement'] and len(units)>=2000 and unit_agreement>=limits['dual_checker_min_agreement'] and unique
    return {'tiers':tiers,'checker_agreement':agreement,'checker_compared':len(comparisons),'unit_comparisons':len(units),'unit_agreement':unit_agreement,
            'second_checker':{'oracle_cases':oracle_cases,'real_comparisons':len(rows),'agreement':agreement,'unit_comparisons':len(units),'unit_agreement':unit_agreement,'failures':[{'index':r.get('index'),'seed':r.get('seed'),'tier':r.get('tier'),'policy':r.get('policy'),'terminal_kind':r.get('terminal_kind')} for r in rows if not r.get('complete')]},
            'container_count':count,'containers_unique':unique,'partial_credit_band':{'full_tolerance':.0001,'zero_scale':.01,'width_relative':.0099},'reward_gate_passed':passed}
