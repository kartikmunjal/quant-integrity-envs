"""Structural construction-only provisional E3 screen, without policy imports."""
import json
import time
from pathlib import Path
from envs.e3_fdr_adjudication.cases import make_case, TIERS, digest
from qi.gen import generator_version_hash


def inspect_seed(seed):
    hashes={}
    for tier in TIERS:
        case=make_case(seed,tier)
        candidates=case['public']['candidates']
        if len(candidates)!=20 or sum(case['truth'].values())!=10:
            raise ValueError('mixed membership structure')
        if tier in ('T3','T4'):
            nulls=[c for c in candidates if not case['truth'][c['id']] and c['N']==500]
            modest=[c for c in candidates if case['truth'][c['id']] and c['N']==1]
            if not nulls or not modest or max(c['t_stat'] for c in nulls)<=min(c['t_stat'] for c in modest):
                raise ValueError(tier+' lacks required high-search null / modest single-search real ordering')
        hashes[tier]=case['data_sha256']
    return hashes


def screen(start,end,target=None):
    admitted=[];rejected=[];hashes={}
    for seed in range(start,end+1):
        try:
            hashes[str(seed)]=inspect_seed(seed)
        except ValueError as exc:
            rejected.append({'seed':seed,'reason':str(exc)})
        else:
            admitted.append(seed)
        if seed%10==0:
            print(json.dumps({'seed':seed,'successes':len(admitted),'rejected':len(rejected)}),flush=True)
        if target and len(admitted)>=target:
            break
    return {'candidate_range':[start,end],'inspected_through':seed,'admissible':admitted,'rejected':rejected,'public_hashes':hashes,'inspected_count':len(admitted)+len(rejected),'rejected_count':len(rejected),'target_met':target is None or len(admitted)>=target}


def main():
    started=time.monotonic()
    result={'environment':'E3','status':'provisional structural candidates; separation not certified','generator_version_hash':generator_version_hash(),'policy_runs_before_screen':0,'api_usd':0,'gpu_usd':0}
    result['ranges']={}
    for name,start,end,target in [('design',1000000,1000099,None),('primary',1001000,1004999,500),('replay',1005000,1009999,500)]:
        result['ranges'][name]=screen(start,end,target)
    result['populations']={k:v['admissible'] for k,v in result['ranges'].items()}
    result['realized_null_fraction_distribution']={'0.5':4*len(result['populations']['design'])}
    paths=[Path(__file__),Path('envs/e3_fdr_adjudication/cases.py'),Path('docs/e3_design.md')]
    result['source_sha256']={str(p):__import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in paths}
    result['wall_seconds']=time.monotonic()-started
    with Path('results/p3b2_screen.json').open('x') as f:
        json.dump(result,f,sort_keys=True,indent=2)
        f.write('\n')

if __name__=='__main__':
    main()
