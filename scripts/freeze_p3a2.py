"""Prospective round-two freeze; refuses stale or missing prerequisite evidence."""
import json
import gzip
import xml.etree.ElementTree as ET
import subprocess
from pathlib import Path
from scripts.run_p3a2 import source_files,review_plan
from scripts.p3a2_support import canonical,sha,verify_entries
from qi_runtime import IMAGE
from qi_runtime.phase import runtime_version_hash
from qi.gen import generator_version_hash

ROOT=Path(__file__).resolve().parents[1]
PREREQUISITES=['p3a2-stress-c8','p3a2-stress-c12','p3a2-regression-E1','p3a2-regression-E5','p3a2-regression-E6','p3a2_tests']


def verify_prerequisites():
    sources=source_files();proof={}
    for name in PREREQUISITES:
        path=ROOT/'results'/(name+'.json');row=json.loads(path.read_text())
        if not row['passed'] or row['sources']!=sources:raise ValueError('failed or stale prerequisite '+name)
        if 'stress' in name:
            expected_concurrency=8 if name.endswith('c8') else 12
            if row['environment']!='E2' or row['mode']!='stress' or row['concurrency']!=expected_concurrency or row['planned']!=5000 or row['rows']!=5000:raise ValueError('stress identity/population')
        if 'regression' in name:
            if row['environment']!=name.rsplit('-',1)[1] or row['mode']!='regression' or row['planned']!=1000 or row['rows']!=1000 or row['exact_matches']!=1000:raise ValueError('exact regression identity/population')
            if row['baseline_plan_sha256']!=sha((ROOT/'results/p3a2_regression_plan.json.gz').read_bytes()):raise ValueError('regression selection drift')
        verify_entries(row.get('compact_shards',[]))
        if name=='p3a2_tests':
            if row['counts']['tests']<509 or any(row['counts'][k] for k in ('skipped','failures','errors')) or row['exit_code']!=0:raise ValueError('full suite missing/skipped/failed')
            junit=ROOT/row['junit_path']
            if sha(junit.read_bytes())!=row['junit_sha256']:raise ValueError('test evidence changed')
            tree=ET.parse(junit);suites=list(tree.getroot().iter('testsuite'))
            counts={key:sum(int(s.get(key,0)) for s in suites) for key in ('tests','failures','errors','skipped')}
            if counts!=row['counts'] or len(list(tree.getroot().iter('testcase')))!=counts['tests']:raise ValueError('JUnit count mismatch')
            original=row.get('original_archive')
            if original:
                verify_entries([original]);raw=gzip.decompress((ROOT/original['path']).read_bytes())
                if len(raw)!=original['original_bytes'] or sha(raw)!=original['original_sha256']:raise ValueError('original JUnit bytes changed')
                original_tree=ET.fromstring(raw)
                original_counts={key:sum(int(s.get(key,0)) for s in original_tree.iter('testsuite')) for key in counts}
                if original_counts!=counts:raise ValueError('original JUnit count mismatch')
        else:
            manifest_path=ROOT/row['local_manifest'];manifest=json.loads(manifest_path.read_text())
            verify_entries(manifest['entry_shards'])
            entries=[json.loads(line) for shard in manifest['entry_shards'] for line in gzip.decompress((ROOT/shard['path']).read_bytes()).splitlines()]
            if len(entries)!=manifest['entry_count'] or sum(e['bytes'] for e in entries)!=manifest['compressed_bytes']:raise ValueError('local manifest count/size mismatch')
            verify_entries(entries)
            proof[str(manifest_path.relative_to(ROOT))]=sha(manifest_path.read_bytes())
        proof[str(path.relative_to(ROOT))]=sha(path.read_bytes())
    review=ROOT/'reports/P3a2_clean_review.md'
    if 'READY FOR FREEZE' not in review.read_text():raise ValueError('independent clean context reviewer not ready')
    proof[str(review.relative_to(ROOT))]=sha(review.read_bytes())
    return proof


def main():
    freeze=ROOT/'results/p3a2_freeze.json'
    if freeze.exists() or (ROOT/'logs/p3a2_gate_calls.json').exists():raise ValueError('round two freeze or gate consumed')
    proofs=verify_prerequisites();implementation=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();sources=source_files()
    for path,digest in sources.items():
        if sha(subprocess.check_output(['git','show',implementation+':'+path]))!=digest:raise ValueError('uncommitted source '+path)
    for path,digest in proofs.items():
        if sha(subprocess.check_output(['git','show',implementation+':'+path]))!=digest:raise ValueError('uncommitted proof '+path)
    old=json.loads((ROOT/'results/p3a_freeze.json').read_text())
    # Explicitly require every mutation/generator/financial module unchanged from historical freeze/HEAD.
    baseline='34be7561edcb01c69e971a88d638b01f33b610c0'
    protected=[]
    for folder in ['src/qi/gen','src/qi/mutate','envs/e1_pit_backtest','envs/e5_cost_realism','envs/e6_data_traps']:
        for path in (ROOT/folder).glob('*.py'):
            if path.name=='v1_taskset.py':continue  # Cause attachment only, reviewed and exact-regressed.
            name=str(path.relative_to(ROOT));protected.append(name)
    protected+=['tests/validation/p3a_scalar_checker.py','envs/e2_leakage_audit/reward.py','envs/e2_leakage_audit/runtime.py','prereg.yaml']
    for name in protected:
        if (ROOT/name).read_bytes()!=subprocess.check_output(['git','show',baseline+':'+name]):raise ValueError('protected financial/generator source changed '+name)
    if subprocess.check_output(['docker','image','inspect',IMAGE,'--format','{{.Id}}'],text=True).strip()!=IMAGE:raise ValueError('image mismatch')
    value={'phase':'P3a2','environment':'E2','implementation_commit':implementation,'sources':sources,'prerequisites':proofs,'image':IMAGE,'runtime_version_hash':runtime_version_hash(),
           'generator_version_hash':generator_version_hash(),'exponent':old['exponent'],'concurrency':8,'deadline_seconds':60,'planned_rollouts':8200,
           'fresh_primary':[1003000,1003499],'fresh_replay':[1004000,1004999],'author_review_plan':review_plan(),'protected_sources':protected,
           'historical_gate_preserved':'results/p3a-gate.json','historical_consumed_marker':'logs/p3a_gate_calls.json',
           'tracked_budget_bytes':32*1024**2,'local_budget_bytes':2*1024**3}
    with freeze.open('xb') as f:f.write(canonical(value)+b'\n')
    print(json.dumps({'implementation_commit':implementation,'freeze':str(freeze.relative_to(ROOT))}))


if __name__=='__main__':main()
