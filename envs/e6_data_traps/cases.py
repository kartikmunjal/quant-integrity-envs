"""Task-layer corruptions over unchanged frozen synthetic generator output."""
import copy
import hashlib
import random
from functools import lru_cache
import numpy as np
from qi.gen import GeneratorConfig,generate_market,generator_version_hash
from .repair import reconstruct
from .reward import error_terms

FAMILIES=('duplicate','price_sign_or_scale','unadjusted_split','missing_delisting_return','stale_price','identifier_collision')
CONCEPTUAL=('flag_large_moves','ignore_identifiers','ignore_splits','ticker_only')

@lru_cache(maxsize=8)
def market(seed):
    return generate_market(seed,generator_version_hash(),GeneratorConfig(n_assets=1000,n_days=500))

@lru_cache(maxsize=128)
def _case(seed,tier):
    if not (1007000<=seed<=1008499 or 1009000<=seed<=1009999) or tier not in ('T1','T2','T3','T4'):raise ValueError('E6 reserved dev partitions only')
    m=market(seed);chosen=[];used=set()
    for kind,days in [('split',m.split_day),('identifier',m.id_change_day),('delisting',m.delisting_day)]:
        options=[(i,int(d)) for i,d in enumerate(days) if d>=0 and i not in used and (kind=='delisting' or m.delisting_day[i]<0 or d<m.delisting_day[i])]
        if not options:raise ValueError('missing required generated '+kind+' event')
        i,d=options[0];used.add(i);chosen.append((kind,i,d))
    ranked=[]
    for i in range(m.returns.shape[1]):
        if i in used:continue
        valid=np.flatnonzero(np.isfinite(m.returns[:,i]))
        d=int(valid[np.argmax(np.abs(m.returns[valid,i]))]);ranked.append((abs(float(m.returns[d,i])),i,d))
    ranked.sort(reverse=True)
    for kind,(_,i,d) in zip(('stale_target','large_decoy'),ranked[:2]):
        if abs(float(m.returns[d,i]))<.12:raise ValueError('missing sufficiently large legitimate return')
        chosen.append((kind,i,d))
    selected_assets={i for _,i,_ in chosen}
    alias=next(i for i in range(m.returns.shape[1]) if i not in selected_assets and m.delisting_day[i]<0)
    chosen.append(('ticker_decoy',alias,chosen[0][2]))
    data={'listings':[],'audits':[],'actions':[],'quotes':[],
          'rules':'Use stable listing_id and audit returns; split prices and adjust cumulatively from window anchor; apply identifier actions and delisting settlement. Duplicate keys retain lexically smallest record_id. Flag only quote discrepancies (>1e-8 relative) or extra copies, never legitimate actions. Output exactly universe and anomalies. Each universe row has listing_id, day, identifier, ticker, active (boolean), price, adjusted_price, total_return. Output one row per audit listing/day, excluding anchors. Start active with anchor price and cumulative split factor 1. On active days: price=previous_price*gross_return/split_factor, total_return=gross_return-1, adjusted_price=price*cumulative_split_factor. Apply new identifier on its action day. On delisting day set active false, price/adjusted_price zero, total_return=notice.return; later returns zero. Flag quote record_ids, not corporate actions. Ordering is immaterial.'}
    central={}
    for kind,i,d in chosen:
        key=f'L{i:05d}';start=max(0,d-2);end=min(499,d+2);anchor=start-1
        identifier=f'N{i:05d}' if 0<=m.id_change_day[i]<=anchor else f'A{i:05d}'
        data['listings'].append(dict(listing_id=key,ticker='SHARED',initial_identifier=identifier,anchor_day=anchor,anchor_price=100.+i%37+(seed%97)/100))
        central[kind]=(key,d)
        for day in range(start,end+1):
            raw=m.returns[day,i];gross=max(1+float(raw),.05) if np.isfinite(raw) else 1.
            data['audits'].append(dict(listing_id=key,day=day,gross_return=gross))
        if start<=m.split_day[i]<=end:data['actions'].append(dict(kind='split',listing_id=key,day=int(m.split_day[i]),factor=float(m.split_factor[i])))
        if start<=m.id_change_day[i]<=end:data['actions'].append(dict(kind='identifier',listing_id=key,day=int(m.id_change_day[i]),new_identifier=f'N{i:05d}'))
        if start<=m.delisting_day[i]<=end:data['actions'].append(dict(kind='delisting',listing_id=key,day=int(m.delisting_day[i]),**{'return':-.35-float(m.spread_bps[i])/1000}))
    pristine=reconstruct(data)['universe']
    for row in pristine:
        key=f"{row['listing_id']}:{row['day']}";rid=hashlib.sha256(f'{seed}:{key}'.encode()).hexdigest()[:16]
        data['quotes'].append(dict(record_id=rid,**{k:row[k] for k in ('listing_id','day','identifier','ticker','price','total_return')}))
    bykey={(r['listing_id'],r['day']):r for r in data['quotes']};reserved=set(central.values())
    safe=[r for r in data['quotes'] if (r['listing_id'],r['day']) not in reserved and r['price']>0 and r['listing_id']!=central['large_decoy'][0]]
    duplicate,scale=safe[:2]
    originals={r['record_id']:copy.deepcopy(r) for r in data['quotes']}
    planted=[];flags=[]
    selected=[] if tier=='T4' else [seed%6] if tier=='T1' else [seed%6,(seed+1)%6] if tier=='T2' else list(range(6))
    for index in selected:
        name=FAMILIES[index]
        if index==0:
            before=copy.deepcopy(duplicate);after=copy.deepcopy(before);after['record_id']+='x';data['quotes'].append(after)
        else:
            target=scale if index==1 else bykey[central[{2:'split',3:'delisting',4:'stale_target',5:'identifier'}[index]]]
            before=copy.deepcopy(target)
            if index==1:target['price']*=(-1 if tier=='T1' else 1.03 if tier=='T2' else 1.5)
            if index==2:
                action=next(a for a in data['actions'] if a['kind']=='split' and (a['listing_id'],a['day'])==central['split']);target['price']*=action['factor']
            if index==3:target['total_return']=None
            if index==4:
                prev=bykey.get((target['listing_id'],target['day']-1));target['price']=originals[prev['record_id']]['price'] if prev else next(a['anchor_price'] for a in data['listings'] if a['listing_id']==target['listing_id'])
            if index==5:target['identifier']=next(r['initial_identifier'] for r in data['listings'] if r['listing_id']!=target['listing_id'])
            after=copy.deepcopy(target)
        if before==after:raise ValueError('ineffective corruption '+name)
        planted.append(dict(family=name,record_id=after['record_id'],before=before,after=after));flags.append(after['record_id'])
    random.Random(f'E6:{seed}:{tier}').shuffle(data['quotes'])
    truth={'universe':pristine,'anomalies':sorted(flags),'corruptions':planted}
    if reconstruct(data)!={'universe':pristine,'anomalies':sorted(flags)}:raise ValueError('planted truth not recoverable')
    gaps={}
    for mode in CONCEPTUAL:
        answer=reconstruct(data,mode);terms=error_terms({'answer':answer,'flagged':False,'exit_code':0},truth)
        gaps[mode]=max(terms[0],1-terms[2])
    if min(gaps.values())<.02:raise ValueError('conceptual gap below .02: '+str(gaps))
    return {'public':data,'truth':truth,'diagnostics':{'conceptual_gaps':gaps,'corruptions':len(planted)}}

def make_case(seed,tier):return copy.deepcopy(_case(seed,tier))
def public_input(seed,tier):return make_case(seed,tier)['public']
