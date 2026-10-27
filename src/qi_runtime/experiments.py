"""Infrastructure-only stress, historical determinism, and frozen E6 gate runner."""
from __future__ import annotations
import argparse,asyncio,contextlib,gzip,hashlib,importlib,json,logging,subprocess,time
from collections import Counter,defaultdict
from pathlib import Path
import yaml
from qi_runtime import IMAGE
from qi_runtime.infrastructure import RetryBudget,run_with_retry,record_exception
from qi_runtime.phase import runtime_version_hash,e6_fresh_context,historical_e6_context,ROOT

TIERS=('T1','T2','T3','T4')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def financial_hashes():
    paths=[*Path('envs').glob('e[156]*/*.py'),*Path('src/qi/gen').glob('*.py'),Path('prereg.yaml')]
    return {str(p):sha(p) for p in sorted(paths)}
def frozen_sources():
    paths=[*Path('src/qi_runtime').glob('*.py'),*Path('src/qi_data_traps').rglob('*.py'),Path('scripts/e6_policies.py'),Path('scripts/run_p2d2_gate.py'),Path('envs/e6_data_traps/schema.json'),Path('.github/workflows/ci.yml'),Path('configs/e6_scripted.toml'),Path('reports/P2d3_design.md'),Path('AMENDMENTS.md'),Path('prereg.yaml'),Path('uv.lock'),Path('pyproject.toml'),Path('envs/e1_pit_backtest/container/Dockerfile')]
    return {**financial_hashes(),**{str(p):sha(p) for p in paths}}

def binding(env):
    family={'E1':'e1_pit_backtest','E5':'e5_cost_realism','E6':'e6_data_traps'}[env]
    task=importlib.import_module('envs.'+family+'.v1_taskset');policies=importlib.import_module('scripts.'+{'E1':'e1','E5':'e5','E6':'e6'}[env]+'_policies')
    available,wrong,attacks=policies.policies()
    return task,policies,available,wrong,attacks

def historical_rows(env):
    if env=='E1':folder=Path('results/p2b2_rollouts')
    elif env=='E5':folder=Path('results/p2c_rollouts')
    else:folder=Path('results/p2d_rollouts')
    return [row for p in sorted(folder.glob('*.json')) for row in json.loads(p.read_text())]

def plan_for(mode,env,count):
    task,policies,available,wrong,attacks=binding(env)
    if mode=='stress':
        names=list(available);seed={'E1':1001000,'E5':1004000,'E6':1002000}[env]
        return [dict(seed=seed,tier=TIERS[((i-2)//len(names))%4],policy=names[(i-2)%len(names)]) if i>=2 else dict(seed=seed,tier='T4',policy=('solver_timeout' if i==0 else 'solver_crash')) for i in range(count)]
    if mode=='determinism':
        return [dict(seed=r['seed'],tier=r['tier'],policy=r['policy'],historical_reward=r['reward'],historical_source_sha256=r.get('source_sha256'),historical_replay_seed=r.get('replay_seed')) for r in historical_rows(env)]
    return [dict(seed=seed,tier=tier,policy=name) for tier in TIERS for name in available for seed in (range(1005000,1005500) if name=='oracle' else range(1005000,1005050))]

def compact_value(value):
    if value is None:return None
    out={k:value[k] for k in ('reward','flagged','replay_seed','lifecycle','source_sha256','oracle_sha256') if k in value}
    for stage in ('solver','primary','replay'):
        v=value.get(stage,{})
        out[stage]={k:x for k,x in v.items() if k!='answer'}
        a=v.get('answer')
        if a is not None:
            out[stage]['answer_sha256']=hashlib.sha256(json.dumps(a,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if 'anomalies' in a:out[stage]['anomaly_ids']=a['anomalies'];out[stage]['universe_rows']=len(a['universe'])
    return out

class Shards:
    def __init__(self,folder):self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=True);self.parts=[];self.chunk=[];self.size=0
    def append(self,row):
        n=len(json.dumps(row,sort_keys=True,allow_nan=False).encode())
        if self.chunk and (len(self.chunk)>=50 or self.size+n>600000):self.flush()
        self.chunk.append(row);self.size+=n
    def flush(self):
        if not self.chunk:return
        p=self.folder/f'{len(self.parts):05d}.json';p.write_text(json.dumps(self.chunk,sort_keys=True,indent=1,allow_nan=False)+'\n');self.parts.append(str(p));self.chunk=[];self.size=0

async def run_batch(mode,env,concurrency,count=5000,tag=None):
    initial_sources=frozen_sources() if mode=='gate' else None
    tag=tag or f'{mode}-{env}-c{concurrency}'
    prefix='p2d3-'+tag;marker=Path('logs')/(prefix+'_calls.json')
    plan=plan_for(mode,env,count);planned=len(plan);ledger=RetryBudget(planned)
    with marker.open('x') as f:json.dump({'status':'started','mode':mode,'environment':env,'concurrency':concurrency,'planned':planned,'runtime_version_hash':runtime_version_hash()},f,indent=2)
    Path('results').mkdir(exist_ok=True)
    Path('results',prefix+'_plan.json.gz').write_bytes(gzip.compress(json.dumps({'environment':env,'mode':mode,'planned':planned,'rows':plan},sort_keys=True,separators=(',',':')).encode(),mtime=0))
    task,policies,available,wrong,attacks=binding(env);sem=asyncio.Semaphore(concurrency);stop=asyncio.Event();rows=[];samples={};done=0;started=time.perf_counter()
    expected_samples=set(round(i*(planned-1)/49) for i in range(50)) if mode=='gate' else set()
    journal=Path('logs')/(prefix+'_exceptions');shards=Shards(Path('results')/(prefix+'_rollouts'))
    async def execute_one(index,meta):
        nonlocal done
        async with sem:
            if stop.is_set():return dict(index=index,**meta,started=False,complete=False,terminal_kind='not_started_retry_limit',value=None,attempts=[])
            source_error=None
            try:source=('import time;time.sleep(30)' if meta['policy']=='solver_timeout' else "raise RuntimeError('synthetic solver crash')" if meta['policy']=='solver_crash' else policies.source_for(meta['policy'],meta['seed'],meta['tier'],available))
            except Exception as error:source_error=error;source=''
            source_hash=hashlib.sha256(source.encode()).hexdigest()
            async def call():
                if source_error is not None:raise source_error
                if meta.get('historical_source_sha256') and source_hash!=meta['historical_source_sha256']:raise RuntimeError('historical submitted source bytes changed')
                return await task.run_policy(meta['seed'],meta['tier'],source)
            evidence=await run_with_retry(call,metadata=dict(meta,index=index,environment=env,experiment=tag,submitted_source_sha256=source_hash),ledger=ledger,journal_root=journal)
            if evidence['terminal_kind']=='retry_limit':stop.set()
            raw=evidence['value'];record=dict(index=index,**meta,started=True,**{k:v for k,v in evidence.items() if k!='value'},value=None)
            try:record['value']=compact_value(raw)
            except Exception as error:
                error._qi_completed_record=record
                raise
            if mode=='determinism':
                record['reward_identical']=bool(evidence['complete'] and raw['reward']==meta['historical_reward'])
                record['replay_identical']=bool(evidence['complete'] and raw.get('replay_seed')==meta['historical_replay_seed'])
            try:
                if mode=='gate' and evidence['complete']:
                    from envs.e6_data_traps.cases import make_case
                    from envs.e6_data_traps import checker
                    from scripts.run_p2d2_gate import unit_comparison
                    primary=make_case(meta['seed'],meta['tier']);fresh=make_case(raw['replay_seed'],meta['tier']) if raw['replay_seed'] else primary
                    truth=primary['truth'];other=fresh['truth']
                    record['diagnostics']=primary['diagnostics']
                    record['checker_agrees']=abs(checker.score_pair(raw['primary'],raw['replay'],truth,other)-raw['reward'])<=1e-8
                    if meta['policy']=='oracle':record['unit_checker_agrees']=unit_comparison(raw,truth,other,index)
                    if index in expected_samples:samples[index]=dict(**meta,evidence=raw,attempts=evidence['attempts'],host_truth=truth,replay_host_truth=other)
            except Exception as error:
                error._qi_completed_record=record
                raise
            done+=1
            if done%50==0:print(f'{tag}: completed {done}/{planned}, retries {ledger.used}',flush=True)
            return record
    async def one(index,meta):
        try:row=await execute_one(index,meta)
        except Exception as error:
            exception=record_exception(error,root=journal,metadata=dict(meta,index=index,environment=env,origin='experiment orchestration'))
            # Preserve any completed rollout evidence even if a later checker fails.
            row=getattr(error,'_qi_completed_record',dict(index=index,**meta,started=True,complete=False,terminal_kind='orchestrator',value=None,attempts=[]))
            row.update(complete=False,terminal_kind='orchestrator',orchestration_exception=exception)
        rows.append(row);shards.append(row)
        return row
    interrupted=False
    try:
        for offset in range(0,planned,200):
            await asyncio.gather(*(one(i,plan[i]) for i in range(offset,min(planned,offset+200))))
    except asyncio.CancelledError as error:
        interrupted=True;stop.set()
        record_exception(error,root=journal,metadata={'environment':env,'experiment':tag,'origin':'batch interruption'})
        retained={row['index'] for row in rows}
        for index,meta in enumerate(plan):
            if index not in retained:
                row=dict(index=index,**meta,started=False,complete=False,terminal_kind='not_started_interrupted',value=None,attempts=[])
                rows.append(row);shards.append(row)
    finally:shards.flush()
    rows.sort(key=lambda row:row['index'])
    complete=sum(v['complete'] for v in rows);retry_count=sum(len(v['attempts'])==2 for v in rows)
    exception_attempts=sum(bool(a['exceptions']) for v in rows for a in v['attempts'])
    result={'environment':env,'mode':mode,'tag':tag,'interrupted':interrupted,'generator_version_hash':'eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921','runtime_version_hash':runtime_version_hash(),'orchestrator_sha256':sha(__file__),'concurrency':concurrency,'planned':planned,'started':sum(v['started'] for v in rows),'complete':complete,'terminal_failures':planned-complete,'retry_count':retry_count,'retry_rate':retry_count/planned,'exception_attempts':exception_attempts,'policy_execution_failures':sum(any(a['policy_evidence'] for a in v['attempts']) for v in rows),'zero_reward_rows':sum(v['complete'] and v['value']['reward']==0 for v in rows),'elapsed_seconds':time.perf_counter()-started,'shards':shards.parts,'api_usd':0,'gpu_usd':0}
    result['passed']=not interrupted and complete==planned and retry_count/planned<=.005
    if mode=='determinism':
        result['reward_differences']=[{k:v.get(k) for k in ('index','seed','tier','policy','historical_reward','value','terminal_kind')} for v in rows if not v.get('reward_identical',False)]
        result['replay_differences']=sum(not v.get('replay_identical',False) for v in rows)
        result['passed'] &= not result['reward_differences'] and result['replay_differences']==0
    if mode=='gate':
        from qi_runtime.gate_summary import summarize_gate
        result.update(summarize_gate(rows,wrong,attacks))
        result['source_hashes_unchanged']=initial_sources==frozen_sources()
        result['passed'] &= result['reward_gate_passed'] and result['source_hashes_unchanged']
        payload={'environment':'E6','generator_version_hash':result['generator_version_hash'],'runtime_version_hash':result['runtime_version_hash'],'label':'author-review pending','samples':[samples[k] for k in sorted(samples)]}
        Path('results/p2d3_trajectory_sample.json.gz').write_bytes(gzip.compress(json.dumps(payload,sort_keys=True,allow_nan=False).encode(),mtime=0))
        result['sample_count']=len(samples)
        result['passed'] &= len(samples)==50
    Path('results',prefix+'.json').write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    marker.write_text(json.dumps(dict(status='complete',passed=result['passed'],runtime_version_hash=result['runtime_version_hash'],elapsed_seconds=result['elapsed_seconds']),sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('shards','tiers','reward_differences')},indent=2),flush=True)
    return result

def verify_gate_freeze():
    path=Path('results/p2d3_freeze.json');saved=json.loads(path.read_text())
    assert saved['sources']==frozen_sources() and saved['runtime_version_hash']==runtime_version_hash() and saved['image']==IMAGE,'changed runtime/source after freeze'
    assert subprocess.check_output(['git','show','HEAD:results/p2d3_freeze.json'])==path.read_bytes(),'freeze must be committed'
    for name in saved['prerequisite_results']:
        r=json.loads(Path(name).read_text());assert r['passed'],'prerequisite experiment did not pass'
    return saved

async def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('stress','determinism','gate','stress-suite','determinism-suite'));parser.add_argument('--env',choices=('E1','E5','E6'),default='E6');parser.add_argument('--concurrency',type=int,default=12);parser.add_argument('--count',type=int,default=5000);parser.add_argument('--tag');args=parser.parse_args()
    logging.disable(logging.CRITICAL)
    if args.concurrency not in (12,24):raise ValueError('prospective concurrency12/24 only')
    if args.mode=='stress' and args.count<5000 and not (args.tag or '').startswith('smoke'):raise ValueError('stress requires5000; use explicit smoke tag for development')
    if args.mode.endswith('-suite'):
        mode=args.mode.removesuffix('-suite')
        for concurrency in ((12,24) if mode=='stress' else (24,)):
            for env in ('E1','E5','E6'):
                with historical_e6_context() if mode=='determinism' and env=='E6' else contextlib.nullcontext():
                    result=await run_batch(mode,env,concurrency,tag=f'{args.tag}-{mode}-{env}-c{concurrency}' if args.tag else None)
                if not result['passed']:raise SystemExit(1)
        return
    context=e6_fresh_context() if args.mode=='gate' else historical_e6_context() if args.mode=='determinism' and args.env=='E6' else contextlib.nullcontext()
    if args.mode=='gate':verify_gate_freeze()
    with context:result=await run_batch(args.mode,args.env,args.concurrency,args.count,args.tag)
    raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':asyncio.run(main())
