"""Small retained operational smoke using independent semantic comparisons."""
import asyncio
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time
from qi_harness.client import MockClient,Reply,ToolCall
from qi_harness.config import Limits
from qi_harness.environments import run_model_episode,WINDOWS
from qi_runtime.infrastructure import run_with_retry,RetryBudget


async def main(tag):
    spec=importlib.util.spec_from_file_location('p5a_independent_smoke_comparison','tests/validation/p5a_docker_validation.py')
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    folder=Path('artifacts/p5a')/tag;folder.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();rows=[];ledger=RetryBudget(4)
    for environment in WINDOWS:
        seed=WINDOWS[environment][0];tier='T1';task,_,_,source_for=checker.policy_binding(environment)
        source=source_for('oracle',seed,tier)
        row={'environment':environment,'seed':seed,'tier':tier,'policy':'oracle'}
        async def call():
            result={**row}
            try:
                result['baseline']=await task.run_policy(seed,tier,source)
                client=MockClient([Reply(tool_calls=(ToolCall('list','list_files',{'path':'/work'}),ToolCall('read','read_file',{'path':'/work/input.json'}),ToolCall('submit','submit',{'source':source})))])
                result['model']=await run_model_episode(environment,seed,tier,client,Limits())
                checker.assert_same(result['baseline']['primary'],result['model']['primary'])
                checker.assert_same(result['baseline']['replay'],result['model']['replay'])
                assert abs(result['baseline']['reward']-result['model']['reward'])<=1e-12
                result['passed']=True
            except Exception as error:
                result.update(passed=False,error=type(error).__name__+': '+str(error))
            return result
        run=await run_with_retry(call,metadata=row,ledger=ledger,journal_root=folder/'exceptions')
        value=run['value'] or {};raw=json.dumps(run,sort_keys=True,allow_nan=False).encode();packed=gzip.compress(raw,mtime=0)
        path=folder/(environment+'.json.gz');path.write_bytes(packed)
        summary={**row,'passed':value.get('passed',False),'error':value.get('error'),'baseline_reward':value.get('baseline',{}).get('reward'),'model_reward':value.get('model',{}).get('reward'),'raw':{'path':str(path),'sha256':hashlib.sha256(packed).hexdigest()},'cleanup':all(a['cleanup_complete'] for a in run['attempts'])}
        rows.append(summary);print(json.dumps(summary),flush=True)
    Path('results/'+tag+'.json').write_text(json.dumps({'environment':'E1/E2/E5/E6','generator_version_hash':'eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921','rows':rows,'passed':all(r['passed'] and r['cleanup'] for r in rows),'wall_seconds':time.monotonic()-started,'retries':ledger.used,'api_usd':0,'gpu_usd':0},sort_keys=True,indent=2)+'\n')


if __name__=='__main__':
    import sys
    asyncio.run(main(sys.argv[1]))
