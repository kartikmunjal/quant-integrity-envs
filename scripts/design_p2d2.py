"""Prospective E6 exponent grid on reserved design seeds; no untrusted code."""
import json,time
from pathlib import Path
from qi.gen import generator_version_hash
from envs.e6_data_traps.cases import make_case
from envs.e6_data_traps.repair import reconstruct
from envs.e6_data_traps import reward,checker
from scripts.e6_policies import WRONG

start=time.perf_counter();grid={p:{} for p in (1,2,3)};failures=[];comparisons=0;agreements=0
for tier in ('T1','T2','T3','T4'):
    values={p:{mode:[] for mode in WRONG} for p in grid};gaps=[]
    for seed in range(1002000,1003000):
        try:
            c=make_case(seed,tier);data=c['public'];truth=c['truth'];answer=checker.reconstruct(data)
            assert answer=={'universe':truth['universe'],'anomalies':truth['anomalies']}
            exact={'answer':answer,'flagged':False,'exit_code':0};gaps.append(min(c['diagnostics']['conceptual_gaps'].values()))
            for mode in WRONG:
                bad={'answer':reconstruct(data,mode),'flagged':False,'exit_code':0}
                for p in grid:
                    x=reward.score_pair(bad,exact,truth,truth,exponent=p);y=checker.score_pair(bad,exact,truth,truth,exponent=p)
                    comparisons+=1;agreements+=abs(x-y)<=1e-8;values[p][mode].append(x)
            # Pure-function rejection controls, not substituted runtime gate evidence.
            assert reward.score_pair(dict(exact,flagged=True),exact,truth,truth)==0
        except Exception as error:failures.append({'tier':tier,'seed':seed,'error':str(error)})
    for p in grid:
        stats={mode:{'mean':sum(v)/len(v) if v else None,'maximum':max(v,default=None),'n':len(v)} for mode,v in values[p].items()}
        grid[p][tier]={'wrong':stats,'aggregate':sum(v['mean'] for v in stats.values())/len(stats) if gaps else None,'minimum_gap':min(gaps,default=None)}
    print(tier,'cases',len(gaps),'failures',len(failures),flush=True)
eligible=[]
for p,tiers in grid.items():
    numerical=(10/11)**p>=.5 and (2/3)**p>=.2 and (12/13)**p>=.5
    if not failures and numerical and all(all(v['mean']<=.1 for v in t['wrong'].values()) and t['aggregate']<=.1 and t['minimum_gap']>=.02 for t in tiers.values()):eligible.append(p)
r={'environment':'E6','generator_version_hash':generator_version_hash(),'scope':'4000 reserved design cases; wrong primary paired with exact replay upper bounds; no submitted code on host','seed_range':[1002000,1002999],'grid':grid,'eligible':eligible,'selected':min(eligible) if eligible else None,'failures':failures,'comparisons':comparisons,'agreement':agreements/comparisons if comparisons else 0,'elapsed_seconds':time.perf_counter()-start}
Path('results/p2d2_design_study.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n');print('selected',r['selected'],'agreement',r['agreement'],'seconds',r['elapsed_seconds'],flush=True)
