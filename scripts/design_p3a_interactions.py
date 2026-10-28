"""Real T3 joint/leave-one-out and gold executions, design seeds only."""
import asyncio
import json
import time
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.design_p3a import BUNDLE
from scripts.p3a_support import Archive,canonical,sha,shards
from scripts.run_p3a_gate import source_files
from qi_runtime import execute_program,IMAGE
from qi_runtime.phase import runtime_version_hash
from qi.mutate.cases import make_case,AdmissionFailure
from qi.mutate.catalogue import BY_ID,witness_groups
from qi.mutate.render import render_source
from qi.mutate.reference import evaluate,relative_error

async def main():
    version=source_files();archive=Archive('interaction-design-v2');rows=[];started=time.monotonic();semaphore=asyncio.Semaphore(8)
    async def one(seed):
        import base64,gzip
        async with semaphore:
            if source_files()!=version:raise ValueError('source drift')
            try:case=make_case(seed,'T3')
            except AdmissionFailure as e:
                row={'seed':seed,'passed':False,'admission_failure':e.attempts};rows.append(row);archive.add(str(seed),row);return
            choices=[case['mutations']]+[[j for j in case['mutations'] if j!=m] for m in case['mutations']]+[[]]
            programs=[render_source(c,seed%3,seed,True) for c in choices]
            result=await execute_program({'data':case['data'],'programs':programs},BUNDLE,lambda out:json.loads(gzip.decompress(base64.b64decode(out))),namespace='e2-interaction-design')
            answers=[json.loads(r['stdout']) if r['exit_code']==0 else None for r in result['answer']] if result['answer'] else [None]*len(choices)
            errors=[relative_error(a,evaluate(case['data'],c)) for a,c in zip(answers,choices)]
            conditional={m:{g:relative_error(answers[0][g],answers[i+1][g]) for g in witness_groups(BY_ID[m])} for i,m in enumerate(case['mutations'])} if all(isinstance(a,dict) for a in answers) else {}
            economic_keys=[k for k in case['clean'] if k not in ('selected_strategy','training_label_mean','descriptive_mean')]
            joint=max(relative_error(answers[0][k],case['clean'][k]) for k in economic_keys)
            passed=not result['flagged'] and not result['exit_code'] and max(errors)<=.0001 and joint>=.05 and bool(conditional) and all(v>=.05 for groups in conditional.values() for v in groups.values())
            row={'seed':seed,'mutations':case['mutations'],'generator_version_hash':case['generator_version_hash'],
                 'passed':passed,'errors':errors,'conditional':conditional,'joint_effect':joint,'gold_error':errors[-1],
                 'container_id':result['container_id'],'candidate_attempts':case['candidate_attempts'],'interaction_attempts':case['interaction_attempts']}
            archive.add(str(seed),{'case':case,'programs':programs,'execution':result,'metric':row});rows.append(row)
            print(json.dumps({'seed':seed,'passed':passed}),flush=True)
    await asyncio.gather(*(one(s) for s in range(1000000,1000050)))
    if source_files()!=version:raise ValueError('source drift')
    summary={'runtime_version_hash':runtime_version_hash(),'image':IMAGE,'host_python':sys.version,'environment':'E2','sources':version,'cases':len(rows),'executions':len(rows)*5,'passed':len(rows)==50 and all(r['passed'] for r in rows),'wall_seconds':time.monotonic()-started,
             'compact_shards':shards(sorted(rows,key=lambda r:r['seed']),ROOT/'results/p3a_interactions_v2/rows'),'api_spend_usd':0,'gpu_spend_usd':0}
    Path('results/p3a_interactions_v2.json').write_bytes(canonical(summary)+b'\n');Path('results/p3a_interactions_v2_manifest.json').write_bytes(canonical(archive.manifest())+b'\n')
    print(json.dumps({'complete':True,'passed':summary['passed']}),flush=True)
    if not summary['passed']:raise SystemExit(1)

if __name__=='__main__':asyncio.run(main())
