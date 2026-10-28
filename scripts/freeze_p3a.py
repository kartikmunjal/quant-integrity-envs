"""Write a prospective E2 source freeze after design/independent checks pass."""
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.run_p3a_gate import source_files,POLICIES
from scripts.p3a_support import canonical,sha,verify_entries,ensure_tracked_capacity
from qi_runtime import IMAGE
from qi_runtime.phase import runtime_version_hash
from qi.gen import generator_version_hash


def main():
    path=ROOT/'results/p3a_freeze.json'
    if path.exists() or (ROOT/'logs/p3a_gate_calls.json').exists():raise ValueError('freeze/gate already consumed')
    mutation=json.loads((ROOT/'results/p3a_mutation_design_v2.json').read_text())
    interactions=json.loads((ROOT/'results/p3a_interactions_v2.json').read_text())
    design=json.loads((ROOT/'results/p3a-policy-design-v2.json').read_text())
    if not mutation['passed'] or mutation['mutant_executions']!=1800 or not interactions['passed'] or not design['passed'] or design['selected_exponent'] not in (1,2,3):raise ValueError('design prerequisites failed')
    versions=source_files()
    for summary in (mutation,interactions,design):
        if summary['sources']!=versions:raise ValueError('stale design source evidence')
        verify_entries(summary['compact_shards'])
    for name in ('p3a_mutation_design_v2_manifest','p3a_interactions_v2_manifest','p3a-policy-design-v2_manifest'):
        manifest=json.loads((ROOT/'results'/(name+'.json')).read_text())
        if 'entry_shards' in manifest:
            import gzip
            verify_entries(manifest['entry_shards'])
            entries=[json.loads(line) for e in manifest['entry_shards'] for line in gzip.decompress((ROOT/e['path']).read_bytes()).splitlines()]
        else:entries=manifest['entries']
        verify_entries(entries)
    tests=json.loads((ROOT/'results/p3a_tests.json').read_text())
    if not tests['passed'] or tests['sources']!=versions:raise ValueError('stale/failed full-suite evidence')
    if sha((ROOT/tests['junit_path']).read_bytes())!=tests['junit_sha256']:raise ValueError('test summary bytes changed')
    ensure_tracked_capacity(1024*1024)
    review=ROOT/'reports/P3a_clean_review.md'
    if not review.exists() or 'READY FOR FREEZE' not in review.read_text():raise ValueError('clean-context review not ready')
    implementation=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    versions=source_files()
    for name,digest in versions.items():
        raw=subprocess.check_output(['git','show',implementation+':'+name],cwd=ROOT)
        if __import__('hashlib').sha256(raw).hexdigest()!=digest:raise ValueError('uncommitted source '+name)
    import yaml
    if generator_version_hash()!=yaml.safe_load((ROOT/'prereg.yaml').read_text())['generator']['version_hash']:raise ValueError('frozen generator changed')
    if runtime_version_hash()!='5ac8cf100aabc4d4b47f38fe8ecc4a34fe4db1c77f6042d719c165489769781a':raise ValueError('shared runtime changed')
    image=subprocess.check_output(['docker','image','inspect',IMAGE,'--format','{{.Id}}'],text=True).strip()
    if image!=IMAGE:raise ValueError('immutable image not found')
    value={'phase':'P3a','environment':'E2','implementation_commit':implementation,'sources':versions,'image':IMAGE,
           'runtime_version_hash':runtime_version_hash(),'generator_version_hash':generator_version_hash(),'exponent':design['selected_exponent'],
           'policies':POLICIES,'planned_rollouts':8200,'concurrency':12,'fresh_primary':[1001000,1001499],'fresh_replay':[1002000,1002999],
           'design_summary':'results/p3a-policy-design-v2.json','mutation_summary':'results/p3a_mutation_design_v2.json','interaction_summary':'results/p3a_interactions_v2.json',
           'tracked_budget_bytes':32*1024**2,'local_budget_bytes':2*1024**3,'compressed_shard_budget_bytes':512*1024}
    with path.open('xb') as stream:stream.write(canonical(value)+b'\n')
    print(json.dumps({'freeze_written':str(path.relative_to(ROOT)),'implementation_commit':implementation,'source_count':len(versions)}))

if __name__=='__main__':main()
