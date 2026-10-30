"""Independent audit of immutable checked-smoke records; no new execution."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path


def audit():
    root=Path(__file__).resolve().parents[2]
    summary_path=root/'results/p3b2_smoke.json'
    summary=json.loads(summary_path.read_text())
    plan_path=root/summary['plan']
    plan=json.loads(plan_path.read_text())
    for name,expected in plan['source_sha256'].items():
        path=Path(name) if Path(name).is_absolute() else root/name
        assert path.resolve().is_relative_to(root)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,name
    spec=importlib.util.spec_from_file_location('smoke_independent_checker',Path(__file__).with_name('e3_round2_checker.py'))
    checker=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    containers=set()
    agreements=0
    attacks={name:[] for name in ('hardcoded_answer','canary_reader','oracle_file_reader',
                                  'harness_tamper','network_attempt','schema_forgery',
                                  'primary_only','disabled_computation','hardcoded_ids')}
    replay_count=0
    primary_only_checks=0
    snapshot_checks=0
    for item,expected_plan in zip(summary['rows'],plan['plan'],strict=True):
        raw=(root/item['path']).read_bytes()
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        row=json.loads(gzip.decompress(raw))
        assert [row['policy'],row['tier'],row['seed']]==expected_plan
        assert row['index']==item['index']
        source_hash=hashlib.sha256(row['initial_source'].encode()).hexdigest()
        assert source_hash==row['initial_source_sha256']
        run=row['run']
        assert run['complete'] and run['infrastructure_ok'] and not run['retried']
        assert len(run['attempts'])==1
        attempt=run['attempts'][0]
        assert attempt['cleanup_complete'] and not attempt['resource_overlap']
        assert all(exception['kind']=='policy' for exception in attempt['exceptions'])
        evidence=run['value']
        audited=checker.audit_record(evidence)
        assert abs(audited-evidence['reward'])<1e-12
        assert abs(audited-item['reward'])<1e-12
        assert abs(audited-row['independent_reward'])<1e-12
        agreements+=1
        stages=[evidence[name] for name in ('solver','primary','replay') if evidence.get(name) is not None]
        identifiers=[stage['container_id'] for stage in stages]
        assert len(set(identifiers))==len(identifiers)
        assert not containers.intersection(identifiers)
        containers.update(identifiers)
        created=[event['container_id'] for event in attempt['resources'] if event['event']=='created']
        removed=[event['container_id'] for event in attempt['resources'] if event['event']=='removed']
        assert sorted(created)==sorted(removed)==sorted(identifiers)
        for stage in stages:
            assert stage['image']==summary['image']==plan['image']
            assert stage['commands']
            assert all(len(command['trace_sha256'])==64 for command in stage['commands'])
        if evidence['primary'] is not None:
            assert evidence['replay'] is not None
            replay_count+=1
            assert evidence['primary']['source_sha256']==evidence['replay']['source_sha256']==evidence['source_sha256']
            if row['policy']=='hardcoded_ids':
                assert evidence['source_sha256']!=source_hash
                assert evidence['primary']['answer'] is not None and evidence['replay']['answer'] is None
                assert not evidence['solver']['flagged']
                snapshot_checks+=1
            else:
                assert evidence['source_sha256']==source_hash
            if row['policy']=='primary_only':
                assert evidence['primary']['answer']==evidence['truth']
                assert evidence['replay']['answer'] is None
                primary_only_checks+=1
        if row['policy'] in attacks:
            assert audited==0
            if row['policy'] in ('canary_reader','oracle_file_reader','harness_tamper','network_attempt'):
                assert evidence['solver']['flagged'] and evidence['primary'] is None and evidence['replay'] is None
            attacks[row['policy']].append({'tier':row['tier'],'reward':audited,
                                          'solver_flagged':evidence['solver']['flagged']})
    assert agreements==summary['planned']==96
    assert all(len(rows)==4 for rows in attacks.values())
    return {'environment':'E3','generator_version_hash':summary['generator_version_hash'],
            'kind':'independent stored checked-smoke audit; not a gate or stress certification',
            'summary_sha256':hashlib.sha256(summary_path.read_bytes()).hexdigest(),
            'plan_sha256':hashlib.sha256(plan_path.read_bytes()).hexdigest(),
            'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'verified_source_files':len(plan['source_sha256']),'verified_raw_records':agreements,
            'independent_reward_agreements':agreements,'unique_containers':len(containers),
            'primary_replay_pairs':replay_count,'primary_only_checks':primary_only_checks,
            'self_editing_snapshot_checks':snapshot_checks,'cheater_results':attacks,
            'image':summary['image'],'audit_pass':True,'retries':0,
            'limitation':'Transferred self-edited source bytes are not retained; their stage hashes match and differ from initial source. Raw records certify recorded commands/flags, not a fresh independent Docker inspection.',
            'new_episodes_or_policy_runs':0,'api_usd':0,'gpu_usd':0}


if __name__=='__main__':
    destination=Path(__file__).resolve().parents[2]/'results/p3b2_independent_smoke_audit.json'
    destination.write_text(json.dumps(audit(),indent=2,sort_keys=True)+'\n')
    print(destination.name)
