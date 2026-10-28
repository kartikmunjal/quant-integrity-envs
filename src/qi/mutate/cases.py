"""Deterministic dev-only research cases with explicit effect admission."""
import hashlib
import json
import random
import itertools
from functools import lru_cache
from qi.gen import GeneratorConfig,generate_market,generator_version_hash
from .contract import public_contract
from .catalogue import CATALOGUE,BY_ID,witness_groups
from .reference import evaluate,relative_error
from .render import render_source,source_locations

TIERS=('T1','T2','T3','T4')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()


def _data(market,seed,candidate):
    rng=random.Random(f'e2-data:{seed}:{candidate}')
    # Delisting and identifier events come from the original generator.
    delisted=[i for i,d in enumerate(market.delisting_day) if d>=0]
    renamed=[i for i,d in enumerate(market.id_change_day) if d>=0]
    rng.shuffle(delisted);rng.shuffle(renamed)
    selected=list(dict.fromkeys(delisted[:2]+renamed[:2]))
    remaining=[i for i in range(200) if i not in selected];rng.shuffle(remaining)
    selected=(selected+remaining)[:12]
    start=rng.randrange(8,365)
    end=start+96
    rows=[[float(market.returns[t,a]) if market.active[t,a] else 0. for a in selected] for t in range(500)]
    if any(not __import__('math').isfinite(v) or v<=-1 for row in rows for v in row):raise ValueError('invalid price-return domain')
    prices=[[100.]*12]
    for row in rows[1:]: prices.append([p*(1+r) for p,r in zip(prices[-1],row)])
    fundamentals=[]
    for a in selected:
        fundamentals.append([[int(market.fundamental_period_end[k]),int(market.fundamental_available_day[k,a]),float(market.fundamental_initial[k,a])] for k in range(len(market.fundamental_period_end))])
    # A current-ticker join loses the history before a generated identifier change;
    # -1 is the ordinary missing-index fallback accidentally indexing last asset.
    owner=[(-1 if market.id_change_day[a]>start else j) for j,a in enumerate(selected)]
    return {'returns':rows,'prices':prices,'active':market.active[:,selected].tolist(),
            'ticker_owner':owner,'fundamentals':fundamentals,
            'listing_ids':[f'listing-{a}' for a in selected],
            'identifier_changes':[int(market.id_change_day[a]) for a in selected],
            'bounds':[start,start+32,start+64,end],'horizon':7}


@lru_cache(maxsize=1024)
def admitted_data(seed):
    if not 1000000<=seed<=1009999:raise ValueError('P3a dev seeds only')
    market=generate_market(seed,config=GeneratorConfig(n_assets=200,n_days=500))
    attempts=[];best=None;best_rank=None
    for candidate in range(32):
        try:
            data=_data(market,seed,candidate)
            clean=evaluate(data)
            effect_groups={}
            for m in CATALOGUE:
                output=evaluate(data,(m.id,))
                effect_groups[m.id]={g:relative_error(output[g],clean[g]) for g in witness_groups(m)}
            effects={k:min(v.values()) for k,v in effect_groups.items()}
            bad=[m.id for m in CATALOGUE if effects[m.id]<m.min_effect]
            for group in ('holdings','returns'):
                def flat(v):return [z for x in v for z in flat(x)] if isinstance(v,list) else [v]
                values=flat(clean[group])
                if len(set(values))<2 or max(map(abs,values))<=1e-8:bad.append('constant_'+group)
            attempt={'candidate':candidate,'effects':effects,'effect_groups':effect_groups,'rejected':bad}
            attempts.append(attempt)
            eligible=[m for m in CATALOGUE if effects[m.id]>=m.min_effect]
            rank=(len({m.family for m in eligible}),len(eligible),-candidate)
            if not any(k.startswith('constant_') for k in bad) and (best_rank is None or rank>best_rank):
                best=(data,clean,attempt);best_rank=rank
            if not bad:
                attempt['selected']=True
                return data,clean,attempts
        except ValueError as e:attempts.append({'candidate':candidate,'error':str(e)})
    if best is not None:
        data,clean,selected=best
        selected['selected']=True
        return data,clean,attempts
    raise AdmissionFailure(seed,attempts)


class AdmissionFailure(ValueError):
    def __init__(self,seed,attempts):
        self.seed=seed;self.attempts=attempts
        super().__init__(f'E2 seed {seed}: admission exhausted; retained attempts describe stage and rejection')
        self.add_note('Full deterministic admission diagnostics: '+json.dumps(attempts,sort_keys=True))


def make_case(seed,tier,excluded_families=()):
    if tier not in TIERS:raise ValueError('unknown tier')
    if set(excluded_families)-{f'F{i}' for i in range(1,7)}:raise ValueError('unknown excluded family')
    data,_,attempts=admitted_data(seed)
    data=dict(data,label_report='F1' not in excluded_families,moment_report='F2' not in excluded_families)
    clean=evaluate(data)
    decoy_families=[f for f in ('F1','F2') if f not in excluded_families]
    admitted=next(a for a in attempts if a.get('selected'))
    available=[m for m in CATALOGUE if m.family not in excluded_families and admitted['effects'][m.id]>=m.min_effect]
    rng=random.Random(f'e2-case:{seed}:{tier}:{tuple(sorted(excluded_families))}')
    rng.shuffle(available)
    selected=[]
    if tier!='T4':
        count=3 if tier=='T3' else 1
        for m in available:
            if m.family not in [BY_ID[k].family for k in selected]:selected.append(m.id)
            if len(selected)==count:break
        if len(selected)!=count:raise ValueError('insufficient distinct families')
    interaction_attempts=[]
    if len(selected)>1:
        for combo in itertools.combinations(available,3):
            if len({m.family for m in combo})!=3:continue
            proposed=[m.id for m in combo]
            joint=evaluate(data,proposed)
            conditional={m.id:min(relative_error(joint[g],evaluate(data,[j for j in proposed if j!=m.id])[g]) for g in witness_groups(m)) for m in combo}
            economic_keys=[k for k in clean if k not in ('selected_strategy','training_label_mean','descriptive_mean')]
            joint_effect=max(relative_error(joint[k],clean[k]) for k in economic_keys)
            interaction_attempts.append({'mutations':proposed,'joint':joint_effect,'conditional':conditional})
            if joint_effect>=.05 and all(v>=.05 for v in conditional.values()):
                selected=proposed
                break
        else:raise AdmissionFailure(seed,attempts+[{'stage':'interaction','interaction_attempts':interaction_attempts}])
    else:conditional={}
    realization=0 if tier=='T1' else rng.randrange(3)
    source=render_source(selected,realization,seed,decoys=decoy_families)
    gold=render_source((),realization,seed,decoys=decoy_families)
    spans=source_locations(source)
    truth=[{'family':BY_ID[k].family,'line':spans[k][0],'end_line':spans[k][1],
            'operator':k,'effect':admitted['effects'][k],'witness_effects':admitted['effect_groups'][k],'witness':BY_ID[k].witness} for k in selected]
    public={'data':data,'research_source':source,'contract':public_contract(excluded_families)}
    return {'seed':seed,'public':public,'data':data,'source':source,'clean_source':gold,'mutations':selected,'truth':truth,
            'clean':clean,'decoy_families':decoy_families,
            'candidate_attempts':attempts,'interaction_attempts':interaction_attempts,'conditional_effects':conditional,
            'generator_version_hash':generator_version_hash(),'data_sha256':digest(data)}
