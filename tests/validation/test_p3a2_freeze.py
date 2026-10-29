"""Independent prospective freeze prerequisite integrity tests, synthetic files only."""
import gzip
import json

import pytest
from scripts import freeze_p3a2 as freeze, p3a2_support as support


@pytest.fixture
def evidence(monkeypatch, tmp_path):
    monkeypatch.setattr(freeze, 'ROOT', tmp_path)
    monkeypatch.setattr(freeze, 'ARTIFACTS', {name:name for name in freeze.PREREQUISITES}, raising=False)
    monkeypatch.setattr(support, 'ROOT', tmp_path)
    monkeypatch.setattr(freeze, 'source_files', lambda: {'source.py': 'frozen-source'})
    for folder in ('results', 'logs', 'reports', 'artifacts/p3a2'):
        (tmp_path / folder).mkdir(parents=True, exist_ok=True)
    (tmp_path / 'reports/P3a2_clean_review.md').write_text('READY FOR FREEZE\n')
    plan = gzip.compress(json.dumps({'environments': {env: [{'seed': 1000000+i, 'tier': 'T1', 'policy': 'oracle', 'reward': 1.} for i in range(1000)] for env in ('E1','E5','E6')}}).encode(), mtime=0)
    (tmp_path / 'results/p3a2_regression_plan.json.gz').write_bytes(plan)
    xml = ('<testsuites><testsuite tests="509" failures="0" errors="0" skipped="0">' + ''.join('<testcase name="t%d"/>'%i for i in range(509)) + '</testsuite></testsuites>').encode()
    (tmp_path / 'logs/p3a2_tests.xml').write_bytes(xml)
    rows = {}
    for name in freeze.PREREQUISITES:
        row = dict(passed=True, sources={'source.py': 'frozen-source'})
        if name == 'p3a2_tests':
            row.update(counts=dict(tests=509, failures=0, errors=0, skipped=0), junit_path='logs/p3a2_tests.xml', junit_sha256=support.sha(xml), exit_code=0)
        else:
            raw = tmp_path / ('artifacts/p3a2/' + name + '.json')
            raw.write_text('{"synthetic":true}')
            entry = dict(path=str(raw.relative_to(tmp_path)), bytes=raw.stat().st_size, sha256=support.sha(raw.read_bytes()))
            shard = tmp_path / ('results/' + name + '-manifest.jsonl.gz')
            shard.write_bytes(gzip.compress((json.dumps(entry)+'\n').encode(), mtime=0))
            manifest = dict(local_only=True, entry_count=1, compressed_bytes=entry['bytes'], entry_shards=[dict(path=str(shard.relative_to(tmp_path)), bytes=shard.stat().st_size, sha256=support.sha(shard.read_bytes()), rows=1)])
            mp = tmp_path / ('results/' + name + '_manifest.json')
            mp.write_text(json.dumps(manifest))
            row.update(environment='E2', mode='stress', planned=5000, rows=5000, concurrency=8 if name.endswith('c8') else 12, compact_shards=[], local_manifest=str(mp.relative_to(tmp_path)))
            if 'regression' in name:
                row.update(environment=name.rsplit('-',1)[1], mode='regression', planned=1000, rows=1000, exact_matches=1000, baseline_plan_sha256=support.sha(plan))
        rows[name] = row
    def save():
        for name, row in rows.items():
            (tmp_path / ('results/' + name + '.json')).write_text(json.dumps(row))
    save()
    return tmp_path, rows, save


def test_complete_consistent_prerequisites_are_accepted(evidence):
    assert freeze.verify_prerequisites()


@pytest.mark.parametrize('name,field,value', [
    ('p3a2-stress-c8','concurrency',12), ('p3a2-stress-c12','concurrency',8),
    ('p3a2-stress-c8','planned',4999), ('p3a2-stress-c12','rows',4999),
    ('p3a2-regression-E1','environment','E5'), ('p3a2-regression-E5','planned',999),
    ('p3a2-regression-E6','rows',999), ('p3a2-regression-E1','baseline_plan_sha256','bad'),
    ('p3a2-stress-c8','passed',False), ('p3a2-stress-c8','sources',{}),
    ('p3a2_tests','junit_sha256','bad'),
])
def test_rejects_wrong_population_identity_source_or_junit(evidence, name, field, value):
    _, rows, save = evidence
    rows[name][field] = value
    save()
    with pytest.raises((ValueError, AssertionError)):
        freeze.verify_prerequisites()


@pytest.mark.parametrize('counts', [dict(tests=0, failures=0, errors=0, skipped=0),
                                    dict(tests=508, failures=0, errors=0, skipped=0),
                                    dict(tests=510, failures=0, errors=0, skipped=0),
                                    dict(tests=509, failures=1, errors=0, skipped=0),
                                    dict(tests=509, failures=0, errors=1, skipped=0),
                                    dict(tests=509, failures=0, errors=0, skipped=1)])
def test_rejects_empty_small_inconsistent_or_nonpassing_test_counts(evidence, counts):
    _, rows, save = evidence
    rows['p3a2_tests']['counts'] = counts
    save()
    with pytest.raises((ValueError, AssertionError)):
        freeze.verify_prerequisites()


@pytest.mark.parametrize('target,mutation', [('manifest','missing'),('manifest','invalid-json'),
                                           ('shard','missing'),('shard','tampered'),
                                           ('raw','missing'),('raw','tampered')])
def test_rejects_missing_or_tampered_local_manifest_chain(evidence, target, mutation):
    root, rows, _ = evidence
    name = 'p3a2-stress-c8'
    manifest_path = root / rows[name]['local_manifest']
    manifest = json.loads(manifest_path.read_text())
    shard = root / manifest['entry_shards'][0]['path']
    entry = json.loads(gzip.decompress(shard.read_bytes()))
    path = {'manifest': manifest_path, 'shard': shard, 'raw': root / entry['path']}[target]
    if mutation == 'missing':
        path.unlink()
    else:
        path.write_bytes(b'invalid or tampered')
    with pytest.raises((ValueError, OSError, AssertionError)):
        freeze.verify_prerequisites()


def test_current_prerequisites_use_corrected_runtime_stress_and_suite():
    assert freeze.ARTIFACTS['p3a2-stress-c8']=='p3a2-r2-stress-c8'
    assert freeze.ARTIFACTS['p3a2-stress-c12']=='p3a2-r2-stress-c12'
    assert freeze.ARTIFACTS['p3a2_tests']=='p3a2_tests_r2'
