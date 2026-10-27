"""Design-only E6 accounting study; no submitted code executes on host."""
import argparse,json,time
from pathlib import Path
from qi.gen import generator_version_hash
from envs.e6_data_traps.cases import make_case,CONCEPTUAL
from envs.e6_data_traps.repair import reconstruct
from envs.e6_data_traps import checker
from envs.e6_data_traps.reward import score_pair
from scripts.e6_policies import WRONG

def main(count):
    start=time.perf_counter();tiers={};agree=0;comparisons=0
    for tier in ('T1','T2','T3','T4'):
        failures=[];bounds={k:[] for k in WRONG};gaps={k:[] for k in CONCEPTUAL};samples=0
        for seed in range(1007000,1007000+count):
            try:
                c=make_case(seed,tier);truth=c['truth'];data=c['public'];actual=checker.reconstruct(data)
                assert actual=={'universe':truth['universe'],'anomalies':truth['anomalies']}
                exact={'answer':actual,'flagged':False,'exit_code':0};samples+=1
                for mode in WRONG:
                    answer=reconstruct(data,mode);p={'answer':answer,'flagged':False,'exit_code':0}
                    primary=score_pair(p,exact,truth,truth);independent=checker.score_pair(p,exact,truth,truth)
                    comparisons+=1;agree+=abs(primary-independent)<=1e-8;bounds[mode].append(primary)
                for mode,v in c['diagnostics']['conceptual_gaps'].items():gaps[mode].append(v)
            except Exception as error:failures.append({'seed':seed,'error':str(error)})
        tiers[tier]={'n':samples,'construction_failures':failures,'minimum_gaps':{k:min(v,default=None) for k,v in gaps.items()},
            'wrong_primary_exact_replay_upper_bounds':{k:{'mean':sum(v)/len(v) if v else None,'maximum':max(v,default=None)} for k,v in bounds.items()}}
        print(tier,samples,'failures',len(failures),flush=True)
    result={'environment':'E6','generator_version_hash':generator_version_hash(),'seed_start':1007000,'count_per_tier':count,'comparisons':comparisons,'independent_agreement':agree/comparisons if comparisons else 0,'tiers':tiers,'elapsed_seconds':time.perf_counter()-start,'scope':'Design-only numerical study; wrong primary paired with exact replay upper bound; no untrusted code on host'}
    Path('results/p2d_design_study.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('agreement',result['independent_agreement'],'seconds',result['elapsed_seconds'],flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--count',type=int,default=1000);a=p.parse_args()
    if not 1<=a.count<=1000:raise ValueError('design partition only')
    main(a.count)
