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
