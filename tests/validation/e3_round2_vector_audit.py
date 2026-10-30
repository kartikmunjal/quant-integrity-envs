"""Independent stored-vector audit; no policies, generator or runtime invoked."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path


def audit():
    root=Path(__file__).resolve().parents[2]
    summary_path=root/'results/p3b2_design_vectors.json'
    summary=json.loads(summary_path.read_text())
    checker_path=Path(__file__).with_name('e3_round2_checker.py')
    spec=importlib.util.spec_from_file_location('independent_vector_checker',checker_path)
    checker=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    source_checks=[]
    for name,expected in summary['source_sha256'].items():
        path=Path(name) if Path(name).is_absolute() else root/name
        assert path.resolve().is_relative_to(root)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected, name
        source_checks.append(name)
    rows=[]
    for shard in summary['row_shards']:
        packed=(root/shard['path']).read_bytes()
        assert len(packed)==shard['bytes']
        assert hashlib.sha256(packed).hexdigest()==shard['sha256']
        batch=[json.loads(line) for line in gzip.decompress(packed).splitlines()]
        assert len(batch)==shard['rows']
        rows.extend(batch)
    groups={}
    failed=0
    failed_by_tier={tier:0 for tier in ('T1','T2','T3','T4')}
    stage_checks=0
    score_checks=0
    gap_checks=0
    for row in rows:
        recomputed={}
        assert row['seed'] in summary['screened_design_population']
        for mode,vectors in row['probabilities'].items():
            stage_rewards=[]
            for vector,truth in zip(vectors,row['truth'],strict=True):
                if set(vector)!=set(truth):
                    stage_rewards.append(0.)
                else:
                    stage_rewards.append(float(checker.execution([vector[key] for key in truth],list(truth.values()))))
                stage_checks+=1
            value=min(stage_rewards)
            assert abs(value-row['scores'][mode])<1e-12,(row['seed'],row['tier'],mode)
            score_checks+=1
            recomputed[mode]=value
            groups.setdefault(mode+'/'+row['tier'],[]).append(value)
        passed=True
        for mode,gap in row['honest_minus_wrong_gaps'].items():
            actual=recomputed['honest']-recomputed[mode]
            assert abs(actual-gap)<1e-12
            gap_checks+=1
            passed=passed and actual>=.02
        assert passed==row['all_gaps_pass']
        if not passed:
            failed+=1
            failed_by_tier[row['tier']]+=1
    means={key:sum(values)/len(values) for key,values in groups.items()}
    for key,values in groups.items():
        reported=summary['per_policy_tier'][key]
        assert reported['count']==len(values)
        assert abs(reported['mean']-means[key])<1e-12
    assert failed==summary['failed_case_count']
    assert len(rows)==4*len(summary['screened_design_population'])
    assert score_checks==summary['policy_rows']
    worst={}
    wrong_names=set(rows[0]['honest_minus_wrong_gaps'])
    for tier in failed_by_tier:
        name=max(wrong_names,key=lambda mode:means[mode+'/'+tier])
        worst[tier]={'policy':name,'mean':means[name+'/'+tier],
                     'ceiling':.1,'passes':means[name+'/'+tier]<=.1}
    return {'environment':'E3','generator_version_hash':summary['generator_version_hash'],
            'kind':'independent stored design-vector audit; not an environment gate',
            'input_summary_sha256':hashlib.sha256(summary_path.read_bytes()).hexdigest(),
            'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'verified_source_files':source_checks,'verified_shards':len(summary['row_shards']),
            'verified_cases':len(rows),'verified_stage_rewards':stage_checks,
            'verified_policy_rewards':score_checks,'verified_gaps':gap_checks,
            'failed_case_count':failed,'failed_by_tier':failed_by_tier,
            'worst_wrong_per_tier':worst,
            'shallow_diagnostic':{tier:{'mean':means['shallow/'+tier],
                                        'ceiling':.3,'passes':means['shallow/'+tier]<=.3}
                                  for tier in ('T2','T3')},
            'audit_pass':True,'construction_separation_pass':False,
            'api_usd':0,'gpu_usd':0,'new_episodes_or_policy_runs':0}


if __name__=='__main__':
    destination=Path(__file__).resolve().parents[2]/'results/p3b2_independent_vector_audit.json'
    destination.write_text(json.dumps(audit(),indent=2,sort_keys=True)+'\n')
    print(destination.name)
