"""Independent sensitivity audit using retained probabilities, no new rollouts."""
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path


def audit():
    root=Path(__file__).resolve().parents[2]
    path=root/'results/p3b2_sensitivity.json'
    stored=json.loads(path.read_text())
    source=root/'scripts/p3b2_sensitivity.py'
    assert hashlib.sha256(source.read_bytes()).hexdigest()==stored['source_sha256']
    summary_path=root/'results/p3b2_design_vectors.json'
    assert hashlib.sha256(summary_path.read_bytes()).hexdigest()==stored['design_summary_sha256']
    summary=json.loads(summary_path.read_text())
    rows=[]
    for shard in summary['row_shards']:
        raw=(root/shard['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==shard['sha256']
        rows.extend(json.loads(line) for line in gzip.decompress(raw).splitlines())
    checker_path=Path(__file__).with_name('e3_round2_checker.py')
    spec=importlib.util.spec_from_file_location('sensitivity_exact_checker',checker_path)
    checker=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    results={}
    for tier,reported in stored['tiers'].items():
        selected=[row for row in rows if row['tier']==tier]
        observed=[(q,truth[key]) for row in selected for probability,truth in
                  zip(row['probabilities']['honest'],row['truth'],strict=True)
                  for key,q in probability.items()]
        nulls=sum(y==0 for q,y in observed)
        false_admits=sum(y==0 and q>.75 for q,y in observed)
        assert nulls==reported['null_candidate_executions']
        assert false_admits==reported['honest_null_false_admits']
        ece=0.
        for index,reported_bin in enumerate(reported['reliability']):
            members=[(q,y) for q,y in observed if min(9,math.floor(q*10))==index]
            assert len(members)==reported_bin['count']
            if members:
                probability=sum(q for q,y in members)/len(members)
                frequency=sum(y for q,y in members)/len(members)
                assert abs(probability-reported_bin['mean_probability'])<1e-12
                assert frequency==reported_bin['real_fraction']
                ece+=len(members)*abs(probability-frequency)/len(observed)
        assert abs(ece-reported['expected_calibration_error'])<1e-12
        means={}
        for label,reported_mean in reported['transformed_means'].items():
            kind,amount=label.split(':')
            amount=float(amount)
            def mapped(q):
                if kind=='toward_zero': return q*amount
                if kind=='toward_one': return 1-(1-q)*amount
                if amount==0: return .5
                if q in (0,1): return q
                log_ratio=amount*math.log(q/(1-q))
                log_ratio=min(700,max(-700,log_ratio))
                return 1/(1+math.exp(-log_ratio))
            values=[]
            for row in selected:
                stages=[]
                for probabilities,truth in zip(row['probabilities']['honest'],row['truth'],strict=True):
                    stages.append(float(checker.execution([mapped(probabilities[key]) for key in truth],list(truth.values()))))
                values.append(min(stages))
            means[label]=sum(values)/len(values)
            assert abs(means[label]-reported_mean)<1e-11,(tier,label)
        baseline=means['temperature:1.0']
        best=max(means,key=means.get)
        gain=means[best]-baseline
        assert abs(gain-reported['maximum_gain'])<1e-11
        assert (gain<=.02)==reported['incentive_pass']
        results[tier]={'verified_transforms':len(means),'best_transform':best,
                       'maximum_gain':gain,'incentive_pass':gain<=.02,
                       'false_admits':false_admits,'null_candidate_executions':nulls,
                       'false_admit_rate':false_admits/nulls,'expected_calibration_error':ece}
    return {'environment':'E3','generator_version_hash':stored['generator_version_hash'],
            'kind':'independent retained-vector sensitivity audit; not gate results',
            'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'audit_pass':True,'tiers':results,'new_episodes_or_policy_runs':0,'api_usd':0,'gpu_usd':0}


if __name__=='__main__':
    destination=Path(__file__).resolve().parents[2]/'results/p3b2_independent_sensitivity_audit.json'
    destination.write_text(json.dumps(audit(),indent=2,sort_keys=True)+'\n')
    print(destination.name)
