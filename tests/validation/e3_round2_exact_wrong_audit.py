"""Find immutable wrong-policy/oracle coincidences in stored design vectors."""
import gzip
import hashlib
import json
from pathlib import Path


def audit():
    root=Path(__file__).resolve().parents[2]
    summary_path=root/'results/p3b2_design_vectors.json'
    summary=json.loads(summary_path.read_text())
    matches=[]
    cases=[]
    counts={tier:0 for tier in ('T1','T2','T3','T4')}
    for shard in summary['row_shards']:
        packed=(root/shard['path']).read_bytes()
        assert hashlib.sha256(packed).hexdigest()==shard['sha256']
        for line in gzip.decompress(packed).splitlines():
            row=json.loads(line)
            case_matches=[]
            for policy in row['honest_minus_wrong_gaps']:
                predictions=row['probabilities'][policy]
                if all(prediction==truth for prediction,truth in zip(predictions,row['truth'],strict=True)):
                    case_matches.append(policy)
                    matches.append({'seed':row['seed'],'tier':row['tier'],
                                    'replay_seed':row['replay_seed'],'policy':policy,
                                    'public_hashes':row['data_sha256'],
                                    'truth':row['truth'],'predictions':predictions,
                                    'stored_wrong_reward':row['scores'][policy],
                                    'stored_honest_reward':row['scores']['honest'],
                                    'evidence_shard':shard['path'],
                                    'evidence_row_sha256':hashlib.sha256(line).hexdigest()})
            if case_matches:
                cases.append({'seed':row['seed'],'tier':row['tier'],'policies':case_matches})
                counts[row['tier']]+=1
    first=matches[0] if matches else None
    return {'environment':'E3','generator_version_hash':summary['generator_version_hash'],
            'kind':'stored-vector exact wrong/oracle coincidence audit; not new policy execution',
            'input_summary_sha256':hashlib.sha256(summary_path.read_bytes()).hexdigest(),
            'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'unique_case_count':len(cases),'matching_wrong_policy_case_count':len(matches),
            'unique_cases_by_tier':counts,'first_match':first,
            'unique_cases':cases,'matches':matches,
            'implication':'On each matched fixed case the named wrong output is the oracle output on both stages. Its reward is 1, so every honest reward in [0,1] has honest-minus-wrong gap at most 0; the required .02 gap cannot be repaired by changing only the honest solver. This concerns the current fixed construction, not all possible revised constructions.',
            'api_usd':0,'gpu_usd':0,'new_episodes_or_policy_runs':0}


if __name__=='__main__':
    destination=Path(__file__).resolve().parents[2]/'results/p3b2_exact_wrong_audit.json'
    destination.write_text(json.dumps(audit(),indent=2,sort_keys=True)+'\n')
    print(destination.name)
