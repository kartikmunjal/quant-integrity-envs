"""Construction-only, policy-independent deterministic E2 admission screen."""
import json
from collections import Counter
from pathlib import Path
import time
from concurrent.futures import ProcessPoolExecutor
from qi.mutate.cases import AdmissionFailure,make_case,TIERS,admitted_data
from qi.gen import generator_version_hash
from scripts.p3a2_support import canonical,sha

ROOT=Path(__file__).resolve().parents[1]


def screen_range(start,end,*,construct=make_case):
    if not 1000000<=start<=end<=1009999:raise ValueError('dev range only')
    accepted=[];rejected=[]
    for seed in range(start,end+1):
        try:
            for tier in TIERS:construct(seed,tier)
        except AdmissionFailure as exc:
            attempts=exc.attempts
            causes=Counter(a['error'] for a in attempts if 'error' in a)
            rejected.append({'seed':seed,'exhausted_32':len(attempts)==32 and all('error' in a for a in attempts),
                             'causes':dict(causes),'attempts':attempts})
        else:accepted.append(seed)
    return {'range':[start,end],'admissible':accepted,'rejected':rejected,'count':end-start+1,
            'exhausted_32':sum(r['exhausted_32'] for r in rejected),'rejected_count':len(rejected)}


def first_population(screen,count):
    if len(screen['admissible'])<count:raise ValueError('insufficient admissible seeds')
    return screen['admissible'][:count]


def _chunk(bounds):
    result=screen_range(*bounds)
    admitted_data.cache_clear()
    return result


def main():
    started=time.monotonic();ranges={}
    with ProcessPoolExecutor(max_workers=8) as pool:
        jobs=[(name,start,end) for name,start,end in [('design',1000000,1000999),('primary',1003000,1003999),('replay',1004000,1004999)]]
        futures={name:[pool.submit(_chunk,(first,min(first+24,end))) for first in range(start,end+1,25)] for name,start,end in jobs}
        for name,start,end in jobs:
            chunks=[]
            for future in futures[name]:
                chunks.append(future.result())
                print(json.dumps({'range':name,'through':chunks[-1]['range'][1],'rejected':sum(c['rejected_count'] for c in chunks)}),flush=True)
            ranges[name]={'range':[start,end],'admissible':sum((c['admissible'] for c in chunks),[]),'rejected':sum((c['rejected'] for c in chunks),[]),
                          'count':end-start+1,'exhausted_32':sum(c['exhausted_32'] for c in chunks),'rejected_count':sum(c['rejected_count'] for c in chunks)}
    replay=list(ranges['replay']['admissible']);extra=[];seed=1005000
    while len(replay)<1000 and seed<=1009999:
        row=screen_range(seed,seed);extra.append(row);replay.extend(row['admissible']);seed+=1
        admitted_data.cache_clear()
    if len(replay)<1000:raise ValueError('replay population exhausted dev range')
    populations={'design':ranges['design']['admissible'],'primary':first_population(ranges['primary'],500),'replay':replay[:1000]}
    if max(populations['primary'])>=1004000:raise ValueError('primary overlaps replay')
    sources={str(p.relative_to(ROOT)):sha(p.read_bytes()) for folder in ('src/qi/gen','src/qi/mutate') for p in sorted((ROOT/folder).glob('*.py'))}
    sources['scripts/p3a3_screen.py']=sha(Path(__file__).read_bytes())
    value={'environment':'E2','generator_version_hash':generator_version_hash(),'sources':sources,'ranges':ranges,'replay_extension':extra,
           'populations':populations,'wall_seconds':time.monotonic()-started,'api_usd':0,'gpu_usd':0,
           'limitation':'Construction-inadmissible extreme-tail episodes excluded; no policy outcome used.'}
    path=ROOT/'results/p3a3_screen.json'
    with path.open('xb') as f:f.write(canonical(value)+b'\n')

if __name__=='__main__':main()
