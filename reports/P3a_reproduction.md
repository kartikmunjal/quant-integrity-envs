# P3a retained-evidence analysis recipes

These recipes analyze existing evidence; they do not launch policy rollouts or reset the consumed gate. Raw paths require the local ignored archives. The packet selection is explicitly retrospective where noted. Do not overwrite existing packet shards; use a separate scratch output prefix for a reproduction. Docker cleanup, if requested, is restricted to exact owned stopped identifiers and preserves the frozen image.

## Interrupted-gate diagnostic packet preparation

```python
import gzip,json,pathlib,hashlib,sys
ROOT=pathlib.Path.cwd();sys.path.insert(0,str(ROOT))
from scripts.review_p3a import sample_plan
from scripts.run_p3a_gate import freeze_check
from scripts.p3a_support import canonical,sha,shards,ensure_tracked_capacity
from qi.mutate.cases import make_case
from qi.mutate.render import source_locations
from envs.e2_leakage_audit.runtime import poison,reference_program,replay_seed
rows=[json.loads(line) for p in sorted((ROOT/'results/p3a-gate').glob('rows-*.gz')) for line in gzip.decompress(p.read_bytes()).splitlines()]
lookup={(r['policy'],r['tier'],r['seed']):r for r in rows}
fixed=[k for k in sample_plan() if k in lookup and lookup[k]['complete']]
missing=[k for k in sample_plan() if k not in fixed]
remaining=[k for k,r in lookup.items() if r['complete'] and k not in fixed]
key=lambda k:sha(('P3a interrupted-gate diagnostic:'+k[0]+'/'+k[1]+'/'+str(k[2])).encode())
supplement=sorted(remaining,key=key)[:50-len(fixed)]
plan={'environment':'E2','prospective_completed':fixed,'prospective_missing':missing,'retrospective_supplements':supplement,
      'selection':'Keep every completed prospective case; add ascending SHA256(P3a interrupted-gate diagnostic:policy/tier/seed) completed cases. Availability/identity only, no reward filter. Supplements do not replace missing validation or make the gate pass.',
      'fixed_sample_passed':False,'frozen_total':50,'fixed_completed_count':len(fixed),'diagnostic_completed_total':50}
(ROOT/'results/p3a_interrupted_review_selection.json').write_bytes(canonical(plan)+b'\n')
freeze=freeze_check();cards=[];packets=[]
for i,k in enumerate(fixed+supplement,1):
 row=lookup[k];policy,tier,seed=k;raw=(ROOT/row['archive']['path']).read_bytes();full=json.loads(gzip.decompress(raw));r=full['run']['value']
 case=make_case(seed,tier);solver=reference_program(policy)
 assert sha(solver.encode())==r['solver']['source_sha256']
 inputs={'solver':case['public']}
 if r.get('patched_source') is not None:
  poisoned,cutoff=poison(case['data'],seed)
  inputs.update(primary=case['data'],replay=make_case(r['replay_seed'],'T4')['data'],poison=poisoned)
  assert replay_seed(seed,tier,r['patched_source'])==r['replay_seed']
  for stage in ('primary','replay','poison'):
   assert sha(json.dumps(inputs[stage],sort_keys=True).encode())==r[stage]['input_sha256']
 try:operators=list(source_locations(r.get('patched_source','')))
 except (SyntaxError,ValueError,StopIteration):operators=[]
 lines=case['source'].splitlines()
 card={'review_id':i,'selection':'prospective' if k in fixed else 'retrospective diagnostic',
       'policy':policy,'tier':tier,'seed':seed,'reward':r['reward'],'schema_ok':r['schema_ok'],'security_ok':r['security_ok'],
       'findings':r['findings'],'truth':r['truth'],'patch_operators':operators,
       'errors':{x:r[x] for x in ('primary_error','replay_error','poison_error')},
       'contexts':[{'operator':t['operator'],'family':t['family'],'line':t['line'],'source':lines[max(0,t['line']-2):t['end_line']+1]} for t in r['truth']],
       'container_ids':{s:r[s]['container_id'] for s in ('solver','primary','replay','poison')},'lifecycle':r['lifecycle'],
       'attempt_kinds':[a['kind'] for a in full['run']['attempts']],'archive':row['archive']}
 cards.append(card);packets.append({'card':card,'inputs':inputs,'solver_source':solver,'full_rollout':full,'freeze':freeze})
entries=shards(packets,ROOT/'results/p3a_interrupted_review_packet/rows')
(ROOT/'results/p3a_interrupted_review_cards.json').write_bytes(canonical(cards)+b'\n')
(ROOT/'results/p3a_interrupted_review_packet.json').write_bytes(canonical({'environment':'E2','selection':plan,'packet_shards':entries,'author_reviewed':False,'note':'Preparation is not review; 12 frozen selections remain unavailable. Author conclusions are recorded separately.'})+b'\n')
print({'fixed':len(fixed),'missing':len(missing),'diagnostic_total':len(cards),'packet_bytes':sum(e['bytes'] for e in entries)})

```

## Post-gate audit and ownership-scoped housekeeping

```python
import gzip,json,pathlib,hashlib,subprocess,sys,time,collections
ROOT=pathlib.Path.cwd();sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests/validation'))
from scripts.p3a_support import canonical,sha,shards,verify_entries,phase_evidence_bytes,inventory
from scripts.run_p3a_gate import source_files,statistics
from p3a_scalar_checker import check_record
from qi_runtime import IMAGE
from qi_runtime.phase import runtime_version_hash
from qi.gen import generator_version_hash
summary=json.loads((ROOT/'results/p3a-gate.json').read_text());freeze=json.loads((ROOT/'results/p3a_freeze.json').read_text())
verify_entries(summary['compact_shards'])
rows=[json.loads(line) for e in summary['compact_shards'] for line in gzip.decompress((ROOT/e['path']).read_bytes()).splitlines()]
qualified=[r for r in rows if r['complete']]
expected=json.loads((ROOT/'artifacts/p3a/p3a-gate/plan.json').read_text())['plan']
actual={(r['policy'],r['tier'],r['seed']) for r in rows}
assert len(actual)==len(rows) and actual<=set(map(tuple,expected))
all_ids={};completed_ids=[];attempt_seconds=0.;retries=0;failures=[];positive=[]
for row in rows:
 verify_entries([row['archive']]);full=json.loads(gzip.decompress((ROOT/row['archive']['path']).read_bytes()));run=full['run']
 assert run['complete']==row['complete']
 for attempt in run['attempts']:
  attempt_seconds+=attempt['elapsed_seconds']
  ids={r['container_id'] for r in attempt['resources'] if r.get('container_id')}
  for cid in ids:
   assert cid not in all_ids
   all_ids[cid]={'policy':row['policy'],'tier':row['tier'],'seed':row['seed'],'attempt':attempt['attempt']}
  assert attempt['cleanup_complete'] and not attempt['resource_overlap']
 retries+=run['retried']
 if run['complete']:
  r=run['value'];assert abs(r['reward']-check_record(r,freeze['exponent']))<=1e-12
  completed_ids.extend(cid for cid in row['container_ids'].values() if cid)
 else:failures.append({'policy':row['policy'],'tier':row['tier'],'seed':row['seed'],'terminal_kind':run['terminal_kind'],'attempts':run['attempts'],'archive':row['archive']})
assert len(completed_ids)==len(set(completed_ids))
family_tier={}
for f in ('F1','F2','F3','F4','F5','F6'):
 family_tier[f]={}
 for t in ('T1','T2','T3','T4'):
  group=[r for r in qualified if r['policy']=='oracle' and r['tier']==t and any(x['family']==f for x in r['truth'])]
  family_tier[f][t]={'cases':len(group),'oracle_mean':sum(r['reward'] for r in group)/len(group) if group else None,
   'minimum_effect':min((x['effect'] for r in group for x in r['truth'] if x['family']==f),default=None)}
audit={'environment':'E2','generator_version_hash':generator_version_hash(),'runtime_version_hash':runtime_version_hash(),'image':IMAGE,
 'implementation_commit':freeze['implementation_commit'],'source_matches':source_files()==freeze['sources']==summary['sources'],
 'planned':len(expected),'attempted_rows':len(rows),'completed':len(qualified),'terminal':len(failures),'unexecuted':len(expected)-len(rows),
 'complete_fraction':len(qualified)/len(expected),'retries':retries,'retry_rate':retries/len(expected),'stage_container_count':len(completed_ids),
 'unique_stage_container_count':len(set(completed_ids)),'all_attempt_container_count':len(all_ids),'all_attempt_container_ids_unique':True,
 'all_attempt_cleanup_complete':True,'independent_scalar_agreement':1.,'independent_scalar_records':len(qualified),'aggregate_attempt_seconds':attempt_seconds,
 'per_family_tier':family_tier,'terminal_records':failures,'final_status':'FAILED: incomplete frozen one-shot gate','frozen_sample_completed':38,'frozen_sample_missing':12,
 'author_diagnostic_reviews':50,'api_spend_usd':0,'gpu_spend_usd':0}
(ROOT/'results/p3a_gate_audit.json').write_bytes(canonical(audit)+b'\n')
# Scope cleanup to exact identifiers belonging to this gate. No global pruning.
before=subprocess.check_output(['docker','image','inspect',IMAGE,'--format','{{.Id}}'],text=True).strip()
existing=[];removed=[]
ids=sorted(all_ids)
for offset in range(0,len(ids),256):
 args=['docker','ps','-a','--no-trunc','--format','{{.ID}} {{.State}} {{.Image}}']
 for cid in ids[offset:offset+256]:args.extend(['--filter','id='+cid])
 run=subprocess.run(args,text=True,capture_output=True,check=True)
 for line in run.stdout.splitlines():
  if not line.strip():continue
  cid,state,image=line.split();assert cid in all_ids;existing.append({'container_id':cid,'state':state,'image':image})
  if state in ('exited','dead'):
   subprocess.check_call(['docker','rm',cid],stdout=subprocess.DEVNULL);removed.append(cid)
after=subprocess.check_output(['docker','image','inspect',IMAGE,'--format','{{.Id}}'],text=True).strip();assert before==after==IMAGE
cleanup={'environment':'E2','image_before':before,'image_after':after,'inspected_owned_ids':len(ids),'existing_owned':existing,'removed_stopped_owned':removed,
 'global_system_prune_used':False,'method':'Only exact gate-owned stopped IDs are eligible; no image/network/build-cache or other-project prune.'}
(ROOT/'logs/p3a_container_housekeeping.json').write_bytes(canonical(cleanup)+b'\n')
# Hash every ignored phase artifact, including original JUnit and development packets.
entries=[]
for path in sorted((ROOT/'artifacts/p3a').rglob('*')):
 if path.is_file():
  raw=path.read_bytes();entries.append({'path':str(path.relative_to(ROOT)),'bytes':len(raw),'sha256':sha(raw)})
manifest={'environment':'E2','generator_version_hash':generator_version_hash(),'local_only':True,'entry_count':len(entries),'local_bytes':sum(e['bytes'] for e in entries),
 'entry_shards':shards(entries,ROOT/'results/p3a_all_local_manifest/entries'),'note':'All bulky raw evidence remains local and ignored. This committed manifest binds every file; it does not publish the raw files.'}
assert manifest['local_bytes']<=2*1024**3
(ROOT/'results/p3a_all_local_manifest.json').write_bytes(canonical(manifest)+b'\n')
print(json.dumps({'completed':len(qualified),'all_attempt_containers':len(all_ids),'cleanup':cleanup,'local_bytes':manifest['local_bytes'],'tracked_evidence_bytes':phase_evidence_bytes()}))

```

