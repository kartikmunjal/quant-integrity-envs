"""Evidence writer tests: deterministic content and budget integrity."""
import gzip,json
import pytest
from scripts import p3a_support as s


def test_shards_roundtrip_bounded_and_no_overwrite(tmp_path,monkeypatch):
    monkeypatch.setattr(s,'ROOT',tmp_path)
    rows=[{'seed':i,'value':'x'*50} for i in range(251)]
    entries=s.shards(rows,tmp_path/'results/compact')
    s.verify_entries(entries)
    restored=[]
    for e in entries:
        assert e['bytes']<=s.SHARD_BUDGET
        restored.extend(json.loads(line) for line in gzip.decompress((tmp_path/e['path']).read_bytes()).splitlines())
    assert restored==rows
    with pytest.raises(FileExistsError):s.shards(rows,tmp_path/'results/compact')
    (tmp_path/entries[0]['path']).write_bytes(b'corrupt')
    with pytest.raises(ValueError):s.verify_entries(entries)


def test_archive_budget_never_erases_existing_evidence(tmp_path,monkeypatch):
    monkeypatch.setattr(s,'ROOT',tmp_path)
    archive=s.Archive('design')
    entry=archive.add('first',{'evidence':1})
    monkeypatch.setattr(s,'LOCAL_BUDGET',entry['bytes'])
    with pytest.raises(ValueError):archive.add('second',{'evidence':2})
    s.verify_entries([entry])
    assert archive.manifest()['local_only']


def test_tracked_budget_includes_new_phase_files_and_reservations(tmp_path,monkeypatch):
    monkeypatch.setattr(s,'ROOT',tmp_path)
    p=tmp_path/'results/p3a-test/rows.gz';p.parent.mkdir(parents=True);p.write_bytes(b'x'*100)
    ignored=tmp_path/'artifacts/p3a/rows';ignored.parent.mkdir(parents=True);ignored.write_bytes(b'x'*1000)
    assert s.phase_evidence_bytes()==100
    monkeypatch.setattr(s,'TRACKED_BUDGET',110)
    assert s.ensure_tracked_capacity(10)==100
    with pytest.raises(ValueError):s.ensure_tracked_capacity(11)
    with pytest.raises(ValueError):s.ensure_tracked_capacity(-1)


def test_junit_compaction_preserves_original_and_result_counts(tmp_path):
    import hashlib,xml.etree.ElementTree as ET
    from scripts.compact_junit import compact
    path=tmp_path/'tests.xml'
    raw=('<testsuites><testsuite tests="1" failures="0"><testcase name="'+'x'*600000+'"/></testsuite></testsuites>').encode()
    path.write_bytes(raw)
    entry=compact(path,tmp_path/'raw')
    assert gzip.decompress(__import__('pathlib').Path(entry['path']).read_bytes())==raw
    assert entry['original_sha256']==hashlib.sha256(raw).hexdigest()
    assert path.stat().st_size<512*1024
    assert ET.parse(path).find('testsuite').get('tests')=='1'
    assert compact(path,tmp_path/'raw') is None


def test_review_sample_is_fixed_stratified_and_unique_before_results():
    from scripts.review_p3a import sample_plan
    sample=sample_plan()
    assert len(sample)==len(set(sample))==50
    assert all(1001000<=s<=1001499 for _,_,s in sample)
    assert sum(p=='oracle' for p,_,_ in sample)==20
    assert {t for p,t,_ in sample if p=='oracle'}=={'T1','T2','T3','T4'}
    assert {p for p,_,_ in sample if p.startswith('wrong_')}=={f'wrong_{i}' for i in range(12)}
