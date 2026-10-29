"""Evidence writer tests: deterministic content and budget integrity."""
import gzip,json
import pytest
from scripts import p3a3_support as s


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
    p=tmp_path/'results/p3a3-test/rows.gz';p.parent.mkdir(parents=True);p.write_bytes(b'x'*100)
    ignored=tmp_path/'artifacts/p3a3/rows';ignored.parent.mkdir(parents=True);ignored.write_bytes(b'x'*1000)
    assert s.phase_evidence_bytes()==100
    monkeypatch.setattr(s,'TRACKED_BUDGET',110)
    assert s.ensure_tracked_capacity(10)==100
    with pytest.raises(ValueError):s.ensure_tracked_capacity(11)
    with pytest.raises(ValueError):s.ensure_tracked_capacity(-1)

