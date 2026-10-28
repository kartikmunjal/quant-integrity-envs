"""Prepare a prospectively fixed 50-trajectory packet; never claim author review."""
import gzip
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.p3a_support import canonical,sha,shards,ensure_tracked_capacity
from scripts.run_p3a_gate import freeze_check,source_files
from qi.mutate.cases import make_case
from qi.mutate.render import source_locations
from envs.e2_leakage_audit.runtime import poison,reference_program,replay_seed


def sample_plan():
    tiers=('T1','T2','T3','T4')
    plan=[('oracle',tier,1001000+i) for tier in tiers for i in range(5)]
    plan += [(f'wrong_{i}',tiers[i%4],1001000) for i in range(12)]
    plan += [(policy,tiers[i%4],1001000) for i,policy in enumerate(('constant','disabled','canary','oracle_read','harness','network','schema','primary_only'))]
    plan += [('shallow',t,1001000) for t in ('T2','T3')]
    plan += [(f'find_{i}','T3',1001000) for i in range(4)]
    plan += [(p,'T2',1001000) for p in ('near_1','near_2')]
    plan += [('false_flag','T4',1001000),('never_report','T4',1001000)]
    assert len(plan)==len(set(plan))==50
    return plan


def main():
    freeze=freeze_check();version=source_files()
    if not json.loads((ROOT/'results/p3a-gate.json').read_text())['complete']:raise ValueError('gate incomplete')
    cards=[];packets=[]
    for i,(policy,tier,seed) in enumerate(sample_plan(),1):
        path=ROOT/'artifacts/p3a/p3a-gate'/f'{policy}-{tier}-{seed}.json.gz'
        raw=path.read_bytes();full=json.loads(gzip.decompress(raw));run=full['run'];r=run['value']
        case=make_case(seed,tier)
        if not run['complete']:raise ValueError('selected trajectory incomplete')
        solver_source=reference_program(policy)
        if r['solver']['source_sha256']!=sha(solver_source.encode()):raise ValueError('solver source mismatch')
        inputs={'solver':case['public']}
        if r.get('patched_source') is not None:
            replay=make_case(r['replay_seed'],'T4')['data'];poisoned,cutoff=poison(case['data'],seed)
            inputs.update(primary=case['data'],replay=replay,poison=poisoned)
            if replay_seed(seed,tier,r['patched_source'])!=r['replay_seed']:raise ValueError('replay provenance')
            for stage in ('primary','replay','poison'):
                observed=sha(json.dumps(inputs[stage],sort_keys=True).encode())
                if observed!=r[stage]['input_sha256']:raise ValueError('input provenance '+stage)
        try:patch_operators=source_locations(r.get('patched_source',''))
        except (ValueError,SyntaxError,StopIteration):patch_operators={}
        cid={s:r[s].get('container_id') for s in ('solver','primary','replay','poison')}
        source_lines=case['source'].splitlines()
        contexts=[{'family':t['family'],'operator':t['operator'],'line':t['line'],
                   'context':source_lines[max(0,t['line']-2):t['end_line']+1]} for t in r['truth']]
        card={'review_id':i,'policy':policy,'tier':tier,'seed':seed,'reward':r['reward'],'schema_ok':r['schema_ok'],'security_ok':r['security_ok'],
              'findings':r['findings'],'truth_contexts':contexts,'patch_operators':list(patch_operators),
              'errors':{k:r[k] for k in ('primary_error','replay_error','poison_error')},'containers':cid,
              'lifecycle':r['lifecycle'],'attempt_kinds':[a['kind'] for a in run['attempts']],
              'raw_archive':{'path':str(path.relative_to(ROOT)),'bytes':len(raw),'sha256':sha(raw)}}
        cards.append(card);packets.append({'card':card,'inputs':inputs,'solver_source':solver_source,'full_rollout':full,'freeze':freeze})
    packet_shards=shards(packets,ROOT/'results/p3a_review_packet/rows')
    summary={'environment':'E2','selection':'fixed before freeze in sample_plan(), independent of observed rewards','count':50,
             'sources':version,'packet_shards':packet_shards,'author_reviewed':False,'requires':'Author must read cards and source/output evidence and record conclusions separately. Preparation is not review.'}
    ensure_tracked_capacity(len(canonical(cards))+len(canonical(summary))+2)
    (ROOT/'results/p3a_review_cards.json').write_bytes(canonical(cards)+b'\n');(ROOT/'results/p3a_review_packet.json').write_bytes(canonical(summary)+b'\n')
    print(json.dumps({'prepared':50,'packet_bytes':sum(e['bytes'] for e in packet_shards)}))

if __name__=='__main__':main()
