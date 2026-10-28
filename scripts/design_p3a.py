"""Design-only real mutation exercise; never uses fresh primary/replay seeds."""
import asyncio
import base64
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.p3a_support import Archive,canonical,shards
from qi.mutate.catalogue import CATALOGUE,witness_groups
from qi.mutate.cases import make_case,AdmissionFailure
from qi.mutate.reference import evaluate,relative_error
from qi.mutate.render import render_source
from qi_runtime import execute_program

BUNDLE='''import base64,gzip,json,subprocess,sys
x=json.load(open(sys.argv[1]))
json.dump(x['data'],open('/work/data.json','w'))
rows=[]
for source in x['programs']:
 open('/work/child.py','w').write(source)
 p=subprocess.run(['python','-I','-B','/work/child.py','/work/data.json'],capture_output=True,text=True,timeout=10)
 rows.append({'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
print(base64.b64encode(gzip.compress(json.dumps(rows).encode(),mtime=0)).decode())
'''


def sources():
    paths=list((ROOT/'src/qi/mutate').glob('*.py'))+list((ROOT/'envs/e2_leakage_audit').glob('*.py'))+[Path(__file__)]
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


async def main():
    started=time.monotonic();version=sources();archive=Archive('mutation-design-v1')
    rows=[];failures=[]
    semaphore=asyncio.Semaphore(8)
    def parse(out):return json.loads(gzip.decompress(base64.b64decode(out)))
    async def one(seed):
        async with semaphore:
            if sources()!=version:raise ValueError('source drift during design exercise')
            try:case=make_case(seed,'T4')
            except AdmissionFailure as e:
                row={'seed':seed,'status':'ADMISSION_FAILURE','attempts':e.attempts};failures.append(row);rows.append(row)
                archive.add(str(seed),row);print(json.dumps({'seed':seed,'status':'ADMISSION_FAILURE'}),flush=True);return
            programs=[];labels=[]
            for realization in range(3):
                for decoys in (True,False):
                    programs.append(render_source(realization=realization,presentation_seed=seed,decoys=decoys))
                    labels.append({'operator':None,'realization':realization,'decoys':decoys})
                for m in CATALOGUE:
                    programs.append(render_source((m.id,),realization,seed,True))
                    labels.append({'operator':m.id,'family':m.family,'realization':realization,'decoys':True})
            result=await execute_program({'data':case['data'],'programs':programs},BUNDLE,parse,namespace='e2-mutation-design')
            metrics=[]
            if result['flagged'] or result['exit_code'] or not result['answer'] or len(result['answer'])!=len(labels):
                raise ValueError('mutation bundle execution failed')
            for label,record,source in zip(labels,result['answer'],programs):
                actual=json.loads(record['stdout']) if record['exit_code']==0 else None
                expected=evaluate(case['data'],(label['operator'],) if label['operator'] else ())
                error=relative_error(actual,expected)
                effects={}
                if label['operator']:
                    m=next(m for m in CATALOGUE if m.id==label['operator'])
                    effects={g:relative_error(actual[g],case['clean'][g]) for g in witness_groups(m)} if isinstance(actual,dict) else {}
                passed=error<=.0001 and all(v>=.05 for v in effects.values()) and (bool(effects) if label['operator'] else relative_error(actual,case['clean'])<=.0001)
                row=dict(label,seed=seed,passed=passed,oracle_error=error,effects=effects,source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                         output_sha256=hashlib.sha256(canonical(actual)).hexdigest(),container_id=result['container_id'],generator_version_hash=case['generator_version_hash'])
                metrics.append(row);rows.append(row)
                if not passed:failures.append(row)
            # All gold restorations are the executed corresponding clean variant;
            # equality is checked for every variant, not inferred from source text.
            archive.add(str(seed),{'seed':seed,'case':case,'programs':programs,'labels':labels,'execution':result,'metrics':metrics})
            print(json.dumps({'seed':seed,'executions':len(metrics),'failures':sum(not r['passed'] for r in metrics)}),flush=True)
    await asyncio.gather(*(one(s) for s in range(1000000,1000050)))
    if sources()!=version:raise ValueError('source drift at design completion')
    compact=shards(sorted(rows,key=lambda r:(r['seed'],str(r.get('operator')),r.get('realization',-1))),ROOT/'results/p3a_mutation_design/rows')
    manifest=archive.manifest()
    Path('results/p3a_mutation_design_manifest.json').write_bytes(canonical(manifest)+b'\n')
    summary={'environment':'E2','sources':version,'generator_version_hash':case_hash(),'executions':len(rows),
             'mutant_executions':sum(r.get('operator') is not None for r in rows),'failures':failures,
             'passed':not failures,'compact_shards':compact,'local_manifest':'results/p3a_mutation_design_manifest.json',
             'wall_seconds':time.monotonic()-started,'model_api_spend_usd':0,'gpu_spend_usd':0,
             'execution_note':'Each generated script executes as a separate Python subprocess in a checked design-validation bundle. Each seed has a fresh container; this is not the fresh v1 gate.'}
    Path('results/p3a_mutation_design.json').write_bytes(canonical(summary)+b'\n')
    print(json.dumps({'complete':True,'executions':len(rows),'failures':len(failures)}),flush=True)
    if failures:raise SystemExit(1)


def case_hash():
    from qi.gen import generator_version_hash
    return generator_version_hash()

if __name__=='__main__':asyncio.run(main())
