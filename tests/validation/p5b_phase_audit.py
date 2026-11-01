"""Independent cross-version P15 archive/resource/parent-plan audit.

Read completed summaries only. No Docker command, model client, key lookup or
experiment is invoked. Coverage and final acceptance are distinct from faithful
retention of superseded or failed historical attempts.
"""
from __future__ import annotations
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]


def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def local(name):
    path=Path(name);path=path if path.is_absolute() else ROOT/path
    if not path.resolve().is_relative_to(ROOT):raise ValueError('artifact outside repository')
    return path
def load(name):return json.loads(local(name).read_bytes())
def auditor(filename):
    path=Path(__file__).with_name(filename)
    spec=importlib.util.spec_from_file_location(filename.replace('.','_'),path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def required_coverage():
    runtime={('probes','E1/E2/E5/E6',8):68,('mixed','E1/E2/E5/E6',8):32,
             ('mixed','E1/E2/E5/E6',12):48,('e2-stress','E2',8):2000,('e2-stress','E2',12):2000}
    runtime.update({('regression',env,8):1000 for env in ('E1','E2','E5','E6')})
    p5a={('boundary',8):176,('environment-data',8):16,('equivalence',8):3120,('stress',8):1000}
    return runtime,p5a


def audit(runtime,p5a,history_runtime,history_p5a,version_path):
    groups={'runtime_final':runtime,'p5a_final':p5a,'runtime_history':history_runtime,'p5a_history':history_p5a}
    flattened=[name for names in groups.values() for name in names]
    if len(set(flattened))!=len(flattened):raise ValueError('duplicate supplied summary would double-count episodes')
    version=load(version_path);final_source=version['new_runtime_source_sha256']
    rb=auditor('p5b_audit.py');ab=auditor('p5a2_audit.py')
    runtime_audit=rb.audit(runtime+history_runtime)
    p5a_audit=ab.audit(p5a+history_p5a)
    errors=[];error_count=0
    def check(condition,where,kind):
        nonlocal error_count
        if not condition:
            error_count+=1
            if len(errors)<200:errors.append({'location':where,'kind':kind})
    check(runtime_audit['audit_integrity_passed'],'runtime_archives','independent_runtime_archive_audit')
    check(p5a_audit['audit_integrity_passed'],'p5a_archives','independent_p14_archive_audit')
    created=set();removed=set();owner={};raw_seen=set();exceptions_seen=set();trace_parts_seen=set()
    cohort_rows=[];group_totals={};coverage_runtime={};coverage_p5a={}
    for group,names in groups.items():
        totals=Counter()
        for name in names:
            summary=load(name);is_p5a=group.startswith('p5a')
            if is_p5a:
                plan_path=summary['execution_plan'];plan=load(plan_path)
                parent=plan.get('parent_plan')
                if group=='p5a_final':
                    check(isinstance(parent,dict),name,'explicit_original_parent_plan')
                if parent is not None:
                    parent_raw=local(parent['path']).read_bytes();original=json.loads(parent_raw)
                    check(sha(parent_raw)==parent['sha256'],name,'parent_sha256')
                    check(ab.git('show','HEAD:'+parent['path'])==parent_raw,name,'original_parent_committed_unchanged')
                    check(all(plan[k]==original[k] for k in ('mode','concurrency','windows_path','window_manifest_sha256','rows')),
                          name,'exact_original_population_and_scale')
                check(set(summary['semantic_exclusions'])==ab.OPERATIONAL,name,'unchanged_semantic_exclusions')
            else:
                path=local(name);plan_path=str(path.with_name(path.stem+'_plan.json.gz').relative_to(ROOT))
                plan=json.loads(gzip.decompress(local(plan_path).read_bytes()))
            if group.endswith('_final'):
                check(summary['sources']['src/qi_runtime/__init__.py']==final_source,name,'final_runtime_version')
                check(summary['sources']['src/qi_runtime/process_allowance.py']==version['source_sha256']['src/qi_runtime/process_allowance.py'],
                      name,'final_helper_version')
            compact=[]
            for shard in summary['row_shards']:
                compact.extend(json.loads(line) for line in gzip.decompress(local(shard['path']).read_bytes()).splitlines())
            referenced_raw=set();referenced_exception_meta=set();sum_attempts=0;cohort_created=set();cohort_removed=set()
            native_episodes=0
            for row in compact:
                ref=row['raw'];raw_path=local(ref['path']);key=str(raw_path.relative_to(ROOT))
                check(key not in raw_seen,name+':'+str(row['index']),'raw_record_not_reused_across_cohorts')
                raw_seen.add(key);referenced_raw.add(raw_path.resolve())
                packed=raw_path.read_bytes();check(sha(packed)==ref['sha256'],key,'raw_reference_sha256')
                raw=json.loads(gzip.decompress(packed));result=raw.get('result') or {}
                attempts=result.get('attempts') or [];sum_attempts+=len(attempts)
                value={**(raw.get('retained_evidence') or {}),**(result.get('value') or {})}
                if is_p5a:
                    native_episodes+=int(value.get('baseline') is not None)+int(value.get('model') is not None)
                else:
                    native_episodes+=int(value.get('evidence') is not None)
                for index,attempt in enumerate(attempts):
                    check(attempt['cleanup_complete'],key,'confirmed_attempt_cleanup')
                    a_created=[r['container_id'] for r in attempt['resources'] if r['event']=='created']
                    a_removed=[r['container_id'] for r in attempt['resources'] if r['event']=='removed' and r['container_id']]
                    check(Counter(a_created)==Counter(a_removed),key,'every_created_id_removed')
                    for identity in a_created:
                        check(identity not in owner,key,'resource_identity_unique_across_all_versions_and_modes')
                        owner[identity]=(group,name,row['index'],index)
                    created.update(a_created);removed.update(a_removed)
                    cohort_created.update(a_created);cohort_removed.update(a_removed)
                    for item in attempt.get('exceptions',[]):
                        parts=[local(p) for p in item['full_traceback_parts']]
                        check(bool(parts),key,'exception_has_retained_trace_parts')
                        body=b''.join(p.read_bytes() for p in parts)
                        check(sha(body)==item['traceback_sha256'],key,'full_exception_trace_sha256')
                        if parts:
                            meta=parts[0].parent/(item['id']+'.json')
                            check(json.loads(meta.read_bytes())==item,key,'exception_metadata_matches_raw_attempt')
                            referenced_exception_meta.add(meta.resolve());exceptions_seen.add(str(meta.relative_to(ROOT)))
                        trace_parts_seen.update(str(p.relative_to(ROOT)) for p in parts)
            directory=local(summary['raw_directory'])
            actual_raw={p.resolve() for p in directory.iterdir() if p.is_file() and re.fullmatch(r'\d+\.json\.gz',p.name)}
            check(actual_raw==referenced_raw,name,'no_unreferenced_or_missing_attempt_row_archive')
            exception_root=directory/'exceptions'
            actual_meta={p.resolve() for p in exception_root.rglob('*.json')
                         if re.fullmatch(r'[0-9a-f]{32}\.json',p.name)} if exception_root.exists() else set()
            check(actual_meta==referenced_exception_meta,name,'no_unreferenced_or_missing_exception_metadata')
            totals.update(rows=len(compact),attempts=sum_attempts,containers=len(cohort_created),
                          retries=summary['retries'],native_episode_records=native_episodes)
            cohort_rows.append({'group':group,'summary':name,'sha256':sha(local(name).read_bytes()),
                                'mode':summary['mode'],'environment':summary['environment'],
                                'concurrency':summary['concurrency'],'planned':summary['planned'],'rows':summary['rows'],
                                'accepted':summary['passed'],'created':len(cohort_created),'removed':len(cohort_removed),
                                'attempts':sum_attempts,'native_episode_records':native_episodes,
                                'runtime_source_sha256':summary['sources']['src/qi_runtime/__init__.py']})
            if group=='runtime_final':
                identity=(summary['mode'],summary['environment'],summary['concurrency'])
                check(identity not in coverage_runtime,name,'unique_final_runtime_cohort')
                coverage_runtime[identity]=(summary['rows'],summary['planned'],summary['passed'])
            if group=='p5a_final':
                identity=(summary['mode'],summary['concurrency'])
                check(identity not in coverage_p5a,name,'unique_final_p5a_cohort')
                coverage_p5a[identity]=(summary['rows'],summary['planned'],summary['passed'])
        group_totals[group]=dict(totals)
    required_runtime,required_p5a=required_coverage()
    complete_runtime=set(coverage_runtime)==set(required_runtime) and all(
        coverage_runtime[k]==(v,v,True) for k,v in required_runtime.items() if k in coverage_runtime)
    complete_p5a=set(coverage_p5a)==set(required_p5a) and all(
        coverage_p5a[k]==(v,v,True) for k,v in required_p5a.items() if k in coverage_p5a)
    check(created==removed,'phase','all_created_resources_accounted_removed')
    return {'kind':'independent P15 cross-version raw/archive/resource/parent audit','independent_author':'/root/e1_review',
            'environment':'E1/E2/E5/E6','generator_version_hash':version['generator_version_hash'],
            'audit_source_sha256':sha(Path(__file__).read_bytes()),'runtime_version_manifest':version_path,
            'runtime_version_manifest_sha256':sha(local(version_path).read_bytes()),'final_runtime_source_sha256':final_source,
            'component_audits':{'runtime':runtime_audit,'p5a':p5a_audit},'cohorts':cohort_rows,'group_totals':group_totals,
            'audit_integrity_passed':error_count==0,'error_count':error_count,'errors':errors,
            'final_runtime_coverage_complete':complete_runtime,'final_p5a_coverage_complete':complete_p5a,
            'phase_acceptance_passed':error_count==0 and complete_runtime and complete_p5a,
            'unique_created':len(created),'unique_removed':len(removed),'unremoved_recorded_ids':sorted(created-removed),
            'owned_container_ids':sorted(created),'unique_raw_archives_checked':len(raw_seen),
            'exception_metadata_files_checked':len(exceptions_seen),'exception_trace_parts_checked':len(trace_parts_seen),
            'live_docker_inspection':False,'model_or_api_calls_in_audit':0,'api_usd':0,'gpu_usd':0,
            'limitations':'No live-daemon or provider-billing query. Historical accepted cohorts are retained but cannot certify the corrected source. Partial coverage never becomes a full phase pass.'}


def store(result,output):
    output=local(output);ids=result.pop('owned_container_ids');shards=[]
    for start in range(0,len(ids),1000):
        block=ids[start:start+1000];packed=gzip.compress(canonical(block),mtime=0)
        path=output.with_name(output.stem+f'_owned_ids_{len(shards):03d}.json.gz')
        path.write_bytes(packed);shards.append({'path':str(path.relative_to(ROOT)),'sha256':sha(packed),'rows':len(block),'bytes':len(packed)})
    result['owned_id_shards']=shards
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


def test_required_coverage_keeps_all_nine_runtime_and_four_p5a_cohorts():
    runtime,p5a=required_coverage()
    assert len(runtime)==9 and sum(runtime.values())==8148
    assert len(p5a)==4 and p5a[('equivalence',8)]==3120 and p5a[('boundary',8)]==176


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('runtime','p5a','history-runtime','history-p5a'):parser.add_argument('--'+name,nargs='*',default=[])
    parser.add_argument('--version',default='results/p5b_runtime_version_v2.json');parser.add_argument('--output',required=True)
    args=parser.parse_args();result=audit(args.runtime,args.p5a,args.history_runtime,args.history_p5a,args.version)
    store(result,args.output)
    print(json.dumps({k:result[k] for k in ('audit_integrity_passed','error_count','unique_created','unique_removed','phase_acceptance_passed')}))
    raise SystemExit(0 if result['audit_integrity_passed'] else 1)
