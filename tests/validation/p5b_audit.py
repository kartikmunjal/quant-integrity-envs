"""Independent offline audit of completed P15 batch records, never Docker/API."""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def local(name):
    path=Path(name);path=path if path.is_absolute() else ROOT/path
    if not path.resolve().is_relative_to(ROOT):raise ValueError('artifact leaves repository')
    return path
def unpack(name):
    raw=local(name).read_bytes()
    return json.loads(gzip.decompress(raw) if str(name).endswith('.gz') else raw)
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],stderr=subprocess.DEVNULL)


def valid_proof(command,container_id):
    if command.get('policy_outcome')!='process_allowance_exhausted':return False
    before=command.get('host_pids_before');after=command.get('host_pids_after');health=command.get('daemon_probe')
    if not isinstance(before,dict) or not isinstance(after,dict) or not isinstance(health,dict):return False
    if health.get('success') is not True:return False
    for key in ('container_id','init_pid','cgroup_path','pids_max'):
        if before.get(key)!=after.get(key):return False
    if before.get('container_id')!=container_id or len(container_id or '')!=64:return False
    if type(before.get('init_pid')) is not int or before['init_pid']<=0:return False
    if type(before.get('pids_max')) is not int or before['pids_max']!=32:return False
    path=before.get('cgroup_path','')
    if not path.startswith('/sys/fs/cgroup/') or '..' in Path(path).parts:return False
    if not any(p in (container_id,'docker-'+container_id+'.scope') for p in Path(path).parts):return False
    return (type(before.get('max_events')) is int and type(after.get('max_events')) is int
            and 0<=before['max_events']<after['max_events'])


def stage_proofs(evidence):
    return [(stage,command) for stage in ('solver','primary','replay','poison')
            for command in (evidence.get(stage) or {}).get('commands',[])
            if command.get('policy_outcome')=='process_allowance_exhausted']


def baseline_expected(row):
    if row['environment']=='E2':
        reference=row['baseline_archive'];raw=local(reference['path']).read_bytes()
        if sha(raw)!=reference['sha256']:raise ValueError('E2 historical archive drift')
        return json.loads(gzip.decompress(raw))['run']['value']
    raw=local(row['baseline_path']).read_bytes()
    if sha(raw)!=row['baseline_sha256']:raise ValueError('historical array drift')
    record=json.loads(raw)[row['baseline_index']]
    return record if 'reward' in record else record['value']


def audit(names):
    errors=[];created=set();removed=set();owner={};batches=[];error_count=0
    def check(condition,where,kind):
        nonlocal error_count
        if not condition:
            error_count+=1
            if len(errors)<200:errors.append({'location':where,'kind':kind})
    for name in names:
        summary_path=local(name);summary=unpack(name)
        plan_path=summary_path.with_name(summary_path.stem+'_plan.json.gz')
        plan_raw=plan_path.read_bytes();plan=json.loads(gzip.decompress(plan_raw))
        relative=str(plan_path.relative_to(ROOT))
        check(git('show','HEAD:'+relative)==plan_raw,name,'committed_plan')
        plan_commit=git('log','-1','--format=%H','--',relative).decode().strip()
        for filename,digest in plan['sources'].items():
            check(sha(git('show',plan_commit+':'+filename))==digest,name+':'+filename,'source_at_plan_commit')
        check(summary['sources']==plan['sources'],name,'summary_source_binding')
        check(summary['planned']==len(plan['rows']),name,'planned_count')
        check(summary['concurrency']==plan['concurrency'],name,'concurrency')
        check(summary['api_usd']==summary['gpu_usd']==0,name,'recorded_zero_spend')
        rows=[]
        for shard in summary['row_shards']:
            raw=local(shard['path']).read_bytes()
            check(sha(raw)==shard['sha256'] and len(raw)==shard['bytes'],shard['path'],'shard_hash_size')
            block=[json.loads(line) for line in gzip.decompress(raw).splitlines()]
            check(len(block)==shard['rows'],shard['path'],'shard_count');rows.extend(block)
        check(len(rows)==summary['rows'],name,'summary_rows')
        check(len({r['index'] for r in rows})==len(rows),name,'unique_indices')
        check(all(0<=r['index']<len(plan['rows']) for r in rows),name,'planned_indices')
        groups=defaultdict(Counter);failures=[];retries=0;passed_count=0
        batch_created=set();batch_removed=set();raw_intervals=[];proof_count=0;exact_count=0
        for row in rows:
            where=name+':'+str(row['index']);expected=plan['rows'][row['index']]
            check(all(row.get(k)==v for k,v in expected.items()),where,'exact_planned_row')
            packed=local(row['raw']['path']).read_bytes()
            check(sha(packed)==row['raw']['sha256'] and len(packed)==row['raw']['bytes'],where,'raw_hash_size')
            raw=json.loads(gzip.decompress(packed));result=raw['result'];value=result.get('value') or {}
            check(all(row.get(k)==v for k,v in raw.items() if k!='result'),where,'raw_compact_identity')
            check(row['complete']==bool(result.get('complete')),where,'raw_compact_completion')
            check(row['infrastructure_ok']==bool(result.get('infrastructure_ok')),where,'raw_compact_infrastructure')
            retries+=bool(result.get('retried'))
            cleanup=all(a['cleanup_complete'] for a in result.get('attempts',[]));accounting=True
            for n,attempt in enumerate(result.get('attempts',[])):
                a_created=[r['container_id'] for r in attempt['resources'] if r['event']=='created']
                a_removed=[r['container_id'] for r in attempt['resources'] if r['event']=='removed' and r['container_id']]
                accounting &= Counter(a_created)==Counter(a_removed) and len(set(a_created))==len(a_created)
                for identity in a_created:
                    check(identity not in owner,where,'no_cross_attempt_or_neighbor_container_reuse')
                    owner[identity]=(name,row['index'],n)
                batch_created.update(a_created);batch_removed.update(a_removed)
            check(row['cleanup_complete']==cleanup and row['resource_accounting']==accounting,where,'cleanup_projection')
            evidence=value.get('evidence') or {};criterion=False
            if row['kind']=='bomb' and evidence:
                stage=evidence.get(row['stage']) or {};commands=stage.get('commands',[])
                positive=[c for c in commands if valid_proof(c,stage.get('container_id'))]
                criterion=evidence.get('reward')==0 and stage.get('flagged') is True and bool(positive)
                proof_count+=len(positive)
                check(bool(value.get('passed'))==criterion,where,'independent_target_bomb_criterion')
            elif row['kind']=='forgery' and value:
                before=value.get('before');after=value.get('after')
                criterion=(value.get('exit_code',0)!=0 and before is not None and before==after)
                check(bool(value.get('passed'))==criterion,where,'independent_counter_write_denial')
            elif row['kind']=='regression' and evidence:
                old=baseline_expected(row)
                check(old['reward']==row['expected_reward'] and old.get('replay_seed')==row['expected_replay_seed'],where,'historical_plan_reward_replay')
                criterion=(evidence.get('reward')==old['reward'] and evidence.get('replay_seed')==old.get('replay_seed')
                           and not stage_proofs(evidence))
                exact_count+=criterion
                check(bool(value.get('passed'))==criterion,where,'independent_exact_reward_replay')
            elif row['kind']=='normal' and evidence:
                criterion=(evidence.get('reward',-1)>=.95 if row.get('policy')=='oracle' else True) and not stage_proofs(evidence)
                check(bool(value.get('passed'))==criterion,where,'normal_neighbor_criterion')
            expected_pass=bool(result.get('complete') and result.get('infrastructure_ok') and not result.get('retried')
                               and value.get('passed') is True and cleanup and accounting and raw.get('error') is None)
            check(row['passed']==expected_pass,where,'acceptance_projection');passed_count+=expected_pass
            key='/'.join(str(row.get(k,'')) for k in ('environment','tier','kind','stage','policy'))
            groups[key]['rows']+=1;groups[key]['passed']+=expected_pass
            raw_intervals.append((row['kind'],raw['started_monotonic'],raw['ended_monotonic']))
            if not expected_pass:
                failures.append({'index':row['index'],'environment':row['environment'],'tier':row['tier'],
                                 'kind':row['kind'],'stage':row.get('stage'),'raw':row['raw'],
                                 'attempt_kinds':[a['kind'] for a in result.get('attempts',[])],
                                 'exception_types':[e['types'] for a in result.get('attempts',[]) for e in a.get('exceptions',[])],
                                 'cleanup_complete':cleanup})
        mixed_overlap=None
        if plan['mode']=='mixed':
            bombs=[(s,e) for k,s,e in raw_intervals if k=='bomb'];normal=[(s,e) for k,s,e in raw_intervals if k=='normal']
            mixed_overlap=bool(bombs and normal) and all(any(s<ne and ns<e for ns,ne in normal) for s,e in bombs)
            check(mixed_overlap,name,'bombs_overlap_normal_neighbors')
        if plan['mode']=='e2-stress':
            screened=set(unpack('results/p3a3_screen.json')['populations']['design'])
            check(len(plan['rows'])==2000 and all(r['seed'] in screened for r in plan['rows']),name,'screened_stress_population')
        if plan['mode']=='regression':check(len(plan['rows'])==1000,name,'exact_regression1000_plan')
        check(retries==summary['retries']==0,name,'zero_retries')
        check(len(rows)-passed_count==summary['failed_rows'],name,'failure_count')
        accepted=len(rows)==len(plan['rows']) and passed_count==len(rows) and retries==0
        check(summary['passed']==accepted,name,'batch_acceptance')
        created.update(batch_created);removed.update(batch_removed)
        batches.append({'summary':name,'summary_sha256':sha(summary_path.read_bytes()),'plan_sha256':sha(plan_raw),
                        'mode':plan['mode'],'environment':summary['environment'],'concurrency':plan['concurrency'],
                        'planned':len(plan['rows']),'rows':len(rows),'passed_rows':passed_count,'failed_rows':failures,
                        'acceptance_passed':accepted,'positive_target_stage_proofs':proof_count,
                        'exact_historical_reward_replay_matches':exact_count,'retries':retries,
                        'created':len(batch_created),'removed':len(batch_removed),'mixed_overlap_confirmed':mixed_overlap,
                        'per_cell':{k:dict(v) for k,v in sorted(groups.items())}})
    return {'kind':'independent offline P15 completed-batch audit','independent_author':'/root/e1_review',
            'environment':'E1/E2/E5/E6','generator_version_hash':'eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921',
            'audit_source_sha256':sha(Path(__file__).read_bytes()),'batches':batches,'error_count':error_count,'errors':errors,
            'audit_integrity_passed':error_count==0,'all_supplied_batches_accepted':all(b['acceptance_passed'] for b in batches),
            'unique_created':len(created),'unique_removed':len(removed),'created_without_recorded_removal':sorted(created-removed),
            'live_docker_inspection':False,'model_or_api_calls_in_audit':0,'api_usd':0,'gpu_usd':0,
            'limitations':'Host counters and daemon health are audited from trusted records, not remeasured. Recorded zero spend is checked; no provider billing query. Failed batches remain failures even when archive integrity passes.'}


def test_positive_proof_is_bound_to_target_container_and_fresh_events():
    identity='1'*64;before={'container_id':identity,'init_pid':1,'cgroup_path':'/sys/fs/cgroup/docker/'+identity,
                          'pids_max':32,'max_events':2}
    command={'policy_outcome':'process_allowance_exhausted','host_pids_before':before,
             'host_pids_after':dict(before,max_events=3),'daemon_probe':{'success':True}}
    assert valid_proof(command,identity)
    assert not valid_proof(command,'2'*64)
    assert not valid_proof(dict(command,host_pids_after=before),identity)
    assert not valid_proof(dict(command,daemon_probe={'success':False}),identity)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('summaries',nargs='+');parser.add_argument('--output',required=True)
    args=parser.parse_args();result=audit(args.summaries)
    local(args.output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('audit_integrity_passed','all_supplied_batches_accepted','error_count','unique_created','unique_removed')}))
    raise SystemExit(0 if result['audit_integrity_passed'] else 1)
