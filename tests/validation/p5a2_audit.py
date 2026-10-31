"""Independent offline archive audit; never starts Docker or invokes a model.

Usage: python tests/validation/p5a2_audit.py SUMMARY... --output RESULT
Supply completed summaries only. Audit integrity and experiment acceptance are
separate: faithfully retained failures can pass the archive integrity audit.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OPERATIONAL = {'container_id', 'trace_sha256', 'timing', 'elapsed_seconds',
               'duration_seconds', 'timestamp_utc'}
COMPARISON_FIELDS = ('replay_seed', 'flagged', 'security_ok', 'schema_ok', 'findings',
                     'patched_source', 'patch_sha256', 'primary_error', 'replay_error',
                     'poison_error', 'oracle_sha256')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def local(path):
    candidate = Path(path)
    candidate = candidate if candidate.is_absolute() else ROOT / candidate
    resolved = candidate.resolve()
    if not resolved.is_relative_to(ROOT):
        raise ValueError('artifact path leaves repository')
    return resolved


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], stderr=subprocess.DEVNULL)


def semantic(value, answer=False):
    if isinstance(value, dict):
        return {key: semantic(item, answer or key == 'answer') for key, item in value.items()
                if answer or key not in OPERATIONAL}
    if isinstance(value, list):
        return [semantic(item, answer) for item in value]
    return value


def equivalent(a, b):
    if type(a) in (float, int) and type(b) in (float, int):
        return math.isfinite(a) and math.isfinite(b) and abs(a-b) <= 1e-12
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equivalent(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(equivalent(x, y) for x, y in zip(a, b))
    return a == b


def audit(summary_paths):
    errors = []
    error_count = 0
    created = set()
    removed = set()
    resource_owner = {}
    source_refs = set()
    batches = []

    def check(condition, location, kind):
        nonlocal error_count
        if not condition:
            error_count += 1
            if len(errors) < 200:
                errors.append({'location': location, 'kind': kind})

    def source(ref, location):
        if ref is None:
            return
        path = local(ref['path'])
        body = gzip.decompress(path.read_bytes())
        check(digest(body) == ref['sha256'], location, 'source_pool_sha256')
        check(len(body) == ref['raw_bytes'], location, 'source_pool_length')
        source_refs.add(str(path.relative_to(ROOT)))

    for summary_name in summary_paths:
        path = local(summary_name)
        summary_raw = path.read_bytes()
        summary = json.loads(summary_raw)
        name = str(path.relative_to(ROOT))
        plan_path = local(summary['execution_plan'])
        plan_raw = plan_path.read_bytes()
        plan = json.loads(plan_raw)
        check(digest(plan_raw) == summary['execution_plan_sha256'], name, 'plan_sha256')
        check(git('show', 'HEAD:' + str(plan_path.relative_to(ROOT))) == plan_raw, name, 'plan_committed')
        plan_commit = git('log', '-1', '--format=%H', '--', str(plan_path.relative_to(ROOT))).decode().strip()
        for filename, expected_hash in plan['sources'].items():
            # Historical rounds may differ from today's source. Verify their
            # recorded source at the commit that declared that exact plan.
            tracked_filename = str(local(filename).relative_to(ROOT))
            check(digest(git('show', plan_commit + ':' + tracked_filename)) == expected_hash,
                  name + ':' + filename, 'source_at_plan_commit')
            if tracked_filename == 'tests/validation/p5a_docker_validation.py':
                check(summary['validation_source_sha256'] == expected_hash, name, 'validation_driver_binding')
        check(plan['sources'] == summary['sources'], name, 'summary_source_binding')
        check(summary['concurrency'] == plan['concurrency'] == 8, name, 'concurrency')
        window_raw = local(plan['windows_path']).read_bytes()
        check(digest(window_raw) == plan['window_manifest_sha256'] == summary['window_manifest_sha256'],
              name, 'window_binding')
        check(Decimal(str(summary['api_usd'])) == Decimal(0) and
              Decimal(str(summary['gpu_usd'])) == Decimal(0), name, 'recorded_zero_spend')
        rows = []
        for shard in summary['row_shards']:
            packed = local(shard['path']).read_bytes()
            check(digest(packed) == shard['sha256'], shard['path'], 'shard_sha256')
            check(len(packed) == shard['bytes'], shard['path'], 'shard_bytes')
            contents = [json.loads(line) for line in gzip.decompress(packed).splitlines() if line]
            check(len(contents) == shard['rows'], shard['path'], 'shard_rows')
            rows.extend(contents)
        check(len(rows) == len(plan['rows']) == summary['planned'] == summary['rows'], name, 'complete_cohort')
        check(sorted(row['index'] for row in rows) == list(range(len(plan['rows']))), name, 'exact_indices')
        counts = defaultdict(Counter)
        batch_created = set()
        batch_removed = set()
        batch_retries = 0
        reconstructed_passes = 0
        complete_count = 0
        for row in rows:
            location = name + ':' + str(row['index'])
            for key, value in plan['rows'][row['index']].items():
                check(row.get(key) == value, location, 'exact_planned_row_' + key)
            packed = local(row['raw']['path']).read_bytes()
            check(digest(packed) == row['raw']['sha256'], location, 'raw_sha256')
            check(len(packed) == row['raw']['bytes'], location, 'raw_bytes')
            raw = json.loads(gzip.decompress(packed))
            for key in ('index', 'environment', 'tier', 'seed', 'policy', 'role', 'attack', 'passed', 'error'):
                check(row.get(key) == raw.get(key), location, 'raw_compact_' + key)
            result = raw.get('result', {})
            value = {**(raw.get('retained_evidence') or {}), **(result.get('value') or {})}
            for key in ('complete', 'infrastructure_ok', 'retried', 'terminal_kind'):
                check(row.get(key) == result.get(key, False if key != 'terminal_kind' else None),
                      location, 'raw_compact_' + key)
            for key in ('comparison_pass', 'reward_agrees', 'semantic_stage_agreement', 'boundary_pass',
                        'stress_pass', 'host_environment_data_unavailable', 'comparison_errors', 'lifecycle_error'):
                if key in value:
                    check(row.get(key) == value[key], location, 'raw_compact_' + key)
            source(row.get('planned_source_ref'), location)
            planned_source = value.get('planned_source')
            if planned_source is not None:
                check(row.get('planned_source_ref', {}).get('sha256') == digest(planned_source.encode()),
                      location, 'planned_source_identity')
            for owner in ('baseline', 'model'):
                episode = value.get(owner)
                compact_episode = row.get(owner)
                check((episode is None) == (compact_episode is None), location, owner + '_presence')
                if episode is None:
                    continue
                for key in ('reward', 'flagged', 'security_ok', 'schema_ok', 'source_sha256', 'oracle_sha256',
                            'data_sha256', 'generator_version_hash', 'replay_seed', 'lifecycle', 'patch_sha256',
                            'primary_error', 'replay_error', 'poison_error'):
                    if key in episode:
                        check(compact_episode.get(key) == episode[key], location, owner + '_' + key)
                source(compact_episode.get('patched_source_ref'), location)
                for stage in ('solver', 'primary', 'replay', 'poison'):
                    if stage not in episode:
                        continue
                    original = episode[stage]
                    compact_stage = compact_episode.get(stage)
                    check((original is None) == (compact_stage is None), location, owner + '_' + stage + '_presence')
                    if original is None:
                        continue
                    check(compact_stage.get('answer_sha256') == digest(canonical(original.get('answer'))),
                          location, owner + '_' + stage + '_answer_hash')
                    check(compact_stage.get('semantic_sha256') == digest(canonical(semantic(original))),
                          location, owner + '_' + stage + '_semantic_hash')
                    for key, item in original.items():
                        if key not in ('answer', 'raw_stdout', 'stderr', 'stdout'):
                            check(compact_stage.get(key) == item, location, owner + '_' + stage + '_' + key)
                cost = episode.get('cost_usd', (episode.get('harness') or {}).get('cost_usd'))
                check(cost is None or Decimal(str(cost)) == Decimal(0), location, 'recorded_episode_zero_cost')
            baseline, model = value.get('baseline'), value.get('model')
            if summary['mode'] == 'boundary' and model is not None:
                independently_blocked = model['reward'] == 0 and bool(
                    model.get('flagged') or model.get('solver', {}).get('flagged') or
                    model.get('harness', {}).get('terminal'))
                check(bool(value.get('boundary_pass')) == independently_blocked,
                      location, 'independent_boundary_criterion')
            if summary['mode'] == 'stress' and model is not None:
                check(bool(value.get('stress_pass')) == (model['reward'] >= .95),
                      location, 'independent_stress_criterion')
            if summary['mode'] == 'equivalence' and baseline is not None and model is not None:
                reward_equal = equivalent(baseline.get('reward'), model.get('reward'))
                stages_equal = all(equivalent(semantic(baseline.get(stage)), semantic(model.get(stage)))
                                   for stage in ('primary', 'replay', 'poison'))
                stages_equal &= all(equivalent(baseline.get(field), model.get(field))
                                    for field in COMPARISON_FIELDS if field in baseline or field in model)
                if planned_source is not None:
                    stages_equal &= all(e.get('source_sha256') is None or
                                        e['source_sha256'] == digest(planned_source.encode())
                                        for e in (baseline, model))
                check(bool(value.get('reward_agrees')) == reward_equal, location, 'independent_reward_comparison')
                check(bool(value.get('semantic_stage_agreement')) == stages_equal, location, 'independent_semantic_comparison')
                check(bool(value.get('comparison_pass')) == (reward_equal and stages_equal), location, 'independent_pair_comparison')
            batch_retries += bool(result.get('retried'))
            complete_count += bool(result.get('complete'))
            for attempt_number, attempt in enumerate(result.get('attempts', [])):
                check(attempt['cleanup_complete'], location, 'cleanup_complete')
                check(not attempt.get('resource_overlap'), location, 'resource_overlap')
                a_created = [r['container_id'] for r in attempt['resources'] if r['event'] == 'created']
                a_removed = [r['container_id'] for r in attempt['resources'] if r['event'] == 'removed' and r['container_id']]
                check(Counter(a_created) == Counter(a_removed), location, 'created_removed_accounting')
                check(len(a_created) == len(set(a_created)), location, 'duplicate_creation')
                for container in a_created:
                    identity = (name, row['index'], attempt_number)
                    check(container not in resource_owner or resource_owner[container] == identity,
                          location, 'container_reused_across_attempts_or_rounds')
                    resource_owner[container] = identity
                batch_created.update(a_created);batch_removed.update(a_removed)
            key = {'equivalence': 'comparison_pass', 'boundary': 'boundary_pass', 'stress': 'stress_pass',
                   'environment-data': 'host_environment_data_unavailable'}[summary['mode']]
            expected_pass = bool(result.get('infrastructure_ok') and result.get('complete') and
                                 not result.get('retried') and value.get(key) is True)
            check(bool(row['passed']) == expected_pass, location, 'row_acceptance_binding')
            reconstructed_passes += expected_pass
            group = counts[row['environment'] + '/' + row['tier']]
            group['rows'] += 1;group['passed'] += expected_pass
            group['complete'] += bool(result.get('complete'))
            group['reward_agreements'] += bool(value.get('reward_agrees'))
            group['semantic_agreements'] += bool(value.get('semantic_stage_agreement'))
        check(batch_retries == summary['retries'], name, 'retry_summary')
        check(batch_retries == 0, name, 'zero_retry_requirement')
        check(complete_count == summary['complete'], name, 'complete_summary')
        check(len(rows)-reconstructed_passes == summary['failed_rows'], name, 'failed_summary')
        acceptance = len(rows) == len(plan['rows']) and reconstructed_passes == len(rows) and batch_retries == 0
        check(summary['passed'] == acceptance, name, 'batch_acceptance_binding')
        created.update(batch_created);removed.update(batch_removed)
        batches.append({'summary': name, 'sha256': digest(summary_raw), 'mode': summary['mode'],
                        'rows': len(rows), 'acceptance_passed': acceptance,
                        'failed_rows': len(rows)-reconstructed_passes, 'retries': batch_retries,
                        'created_containers': len(batch_created), 'removed_containers': len(batch_removed),
                        'per_environment_tier': {k: dict(v) for k, v in sorted(counts.items())}})
    return {'kind': 'independent offline completed-batch archive audit', 'independent_author': '/root/e1_review',
            'audit_source_sha256': digest(Path(__file__).read_bytes()), 'batches': batches,
            'audit_integrity_passed': error_count == 0, 'all_supplied_batches_accepted': all(b['acceptance_passed'] for b in batches),
            'error_count': error_count, 'errors': errors, 'unique_created': len(created), 'unique_removed': len(removed),
            'created_without_recorded_removal': sorted(created-removed), 'unique_source_pool_files_checked': len(source_refs),
            'docker_inspected': False, 'model_api_calls_in_audit': 0, 'api_spend_usd': '0', 'gpu_spend_usd': '0',
            'limitations': 'Checks retained records and recorded zero costs, not provider billing or live Docker state. Failed rounds are retained and distinguished from archive integrity. No new episode, key lookup, network call or Docker operation.'}


def test_semantic_exclusions_do_not_remove_answer_fields():
    first = {'container_id': 'one', 'answer': {'container_id': 'meaningful', 'value': 1.}}
    second = {'container_id': 'two', 'answer': {'container_id': 'meaningful', 'value': 1.}}
    assert equivalent(semantic(first), semantic(second))
    second['answer']['container_id'] = 'different answer'
    assert not equivalent(semantic(first), semantic(second))


def test_scalar_tolerance_is_absolute_and_boolean_types_are_preserved():
    assert equivalent(1., 1. + 5e-13)
    assert not equivalent(1., 1. + 5e-11)
    assert not equivalent(True, 1)
    assert not equivalent(float('nan'), float('nan'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('summaries', nargs='+')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = audit(args.summaries)
    local(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'audit_integrity_passed': result['audit_integrity_passed'],
                      'all_supplied_batches_accepted': result['all_supplied_batches_accepted'],
                      'error_count': result['error_count'], 'unique_created': result['unique_created'],
                      'unique_removed': result['unique_removed']}, sort_keys=True))
    raise SystemExit(0 if result['audit_integrity_passed'] else 1)
