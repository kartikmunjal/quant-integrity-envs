"""Fixed first-design-seed checked smoke, explicitly not stress or a fresh gate."""
import asyncio
import gzip
import hashlib
import json
from pathlib import Path
import time

from envs.e3_fdr_adjudication import v1_taskset as taskset
from envs.e3_fdr_adjudication.presentation import make_case
from envs.e3_fdr_adjudication.cases import TIERS
from qi_runtime import IMAGE
from qi_runtime.infrastructure import RetryBudget,run_with_retry
from scripts.p3b2_diagnostics import load_independent


def plan(population,wrong,cheaters):
    if not population:
        raise ValueError('empty design population')
    seed=min(population)
    modes=('oracle','random','honest','shallow')+tuple(wrong)+tuple(cheaters)
    return [(mode,tier,seed) for tier in TIERS for mode in modes]


def source_hashes():
    paths=[Path(__file__),*Path('envs/e3_fdr_adjudication').glob('*.py'),Path('tests/validation/e3_round2_checker.py'),Path('tests/validation/e3_round2_policies.py')]
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def source_for(mode,seed,tier,policies):
    truth=None
    if mode in ('oracle','primary_only'):
        truth=dict(make_case(seed,tier)['truth'])
        if mode=='oracle':
            truth.update(make_case(taskset.replay_seed(seed,tier),tier)['truth'])
    return policies.submitted_source(mode,truth)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


async def main():
    policies=load_independent('e3_round2_policies')
    checker=load_independent('e3_round2_checker')
    planned=plan(taskset.populations()['design'],policies.WRONG_POLICIES,policies.CHEATER_POLICIES)
    sources=source_hashes()
    plan_path=Path('results/p3b2_smoke_plan.json')
    plan_value={'environment':'E3','kind':'first-design-seed full-roster smoke; not stress or gate','plan':planned,'source_sha256':sources,'concurrency':4,'image':IMAGE}
    if not plan_path.exists():
        plan_path.write_bytes(canonical(plan_value)+b'\n')
        raise SystemExit('Plan written. Commit it before executing the smoke.')
    import subprocess
    if subprocess.check_output(['git','show','HEAD:results/p3b2_smoke_plan.json'])!=canonical(plan_value)+b'\n':
        raise ValueError('smoke plan/source hashes must be committed before execution')
    folder=Path('results/p3b2_smoke')
    folder.mkdir(exist_ok=False)
    journal=Path('artifacts/p3b2/smoke/exceptions')
    journal.mkdir(parents=True,exist_ok=False)
    ledger=RetryBudget(len(planned));iterator=iter(enumerate(planned));rows=[];started=time.monotonic()
    async def worker():
        for index,(mode,tier,seed) in iterator:
            if source_hashes()!=sources:
                raise ValueError('source drift during smoke')
            source=source_for(mode,seed,tier,policies)
            result=await run_with_retry(lambda:taskset.run_policy(seed,tier,source),metadata={'environment':'E3','policy':mode,'tier':tier,'seed':seed,'index':index},ledger=ledger,journal_root=journal)
            value=result['value'] or {}
            reward=checker.audit_record(value)
            row={'index':index,'policy':mode,'tier':tier,'seed':seed,'run':result,'independent_reward':reward,'audit_agrees':result['complete'] and abs(reward-value.get('reward',-1))<=1e-12,'initial_source':source,'initial_source_sha256':hashlib.sha256(source.encode()).hexdigest()}
            packed=gzip.compress(canonical(row),mtime=0)
            if len(packed)>1024*1024:
                raise ValueError('smoke proof exceeds tracked file size')
            path=folder/f'{index:04d}.json.gz'
            path.write_bytes(packed)
            rows.append({'index':index,'policy':mode,'tier':tier,'seed':seed,'complete':result['complete'],'infrastructure_ok':result['infrastructure_ok'],'retried':result['retried'],'reward':value.get('reward'),'audit_agrees':row['audit_agrees'],'path':str(path),'sha256':hashlib.sha256(packed).hexdigest(),'bytes':len(packed)})
            print(json.dumps({'rows':len(rows),'planned':len(planned),'policy':mode,'tier':tier,'complete':result['complete']}),flush=True)
    outcomes=await asyncio.gather(*(worker() for _ in range(4)),return_exceptions=True)
    rows.sort(key=lambda row:row['index'])
    from qi.gen import generator_version_hash
    summary={'environment':'E3','kind':'checked first-design-seed smoke only; not a gate','generator_version_hash':generator_version_hash(),'plan':'results/p3b2_smoke_plan.json','planned':len(planned),'rows':rows,'row_count':len(rows),'complete_count':sum(row['complete'] for row in rows),'audit_agreement_count':sum(row['audit_agrees'] for row in rows),'retries':ledger.used,'errors':[repr(item) for item in outcomes if isinstance(item,BaseException)],'wall_seconds':time.monotonic()-started,'image':IMAGE,'api_usd':0,'gpu_usd':0}
    Path('results/p3b2_smoke.json').write_bytes(canonical(summary)+b'\n')
    print(json.dumps({key:summary[key] for key in ('planned','row_count','complete_count','audit_agreement_count','retries','errors','wall_seconds')}),flush=True)

if __name__=='__main__':
    asyncio.run(main())
