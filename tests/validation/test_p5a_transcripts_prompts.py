"""Independent bounded-secret-free artifact and prompt-manifest contracts."""
import hashlib
import json

import pytest


def test_transcript_hash_redaction_and_roundtrip(tmp_path):
    from qi_harness.transcripts import write_transcript,read_transcript
    fake='P5A_FAKE_SECRET_NOT_A_REAL_KEY_456'
    record={'messages':[{'role':'user','content':'fixture '+fake}],
            'nested':{'Authorization':'Bearer '+fake},'reward':0,
            'hack_monitors':{'canary_reads':0,'tamper_flags':False,'reexecution_failures':0}}
    path=tmp_path/'episode.json'
    manifest=write_transcript(path,record,secrets=(fake,),max_bytes=4096)
    raw=path.read_bytes()
    assert len(raw)==manifest['bytes']<=4096
    assert hashlib.sha256(raw).hexdigest()==manifest['sha256']
    assert fake not in raw.decode(errors='replace')
    restored=read_transcript(path,manifest['sha256'])
    assert restored['reward']==0 and fake not in repr(restored)
    path.write_bytes(raw+b' ')
    with pytest.raises(ValueError): read_transcript(path,manifest['sha256'])


def test_enormous_transcript_bounded_and_redacted_before_storage(tmp_path):
    from qi_harness.transcripts import write_transcript
    fake='P5A_FAKE_SECRET_NEVER_PERSIST_789'
    record={'messages':[{'content':(fake+'x'*1000)*100}], 'reward':0}
    path=tmp_path/'bounded.json'
    manifest=write_transcript(path,record,secrets=(fake,),max_bytes=512)
    assert len(path.read_bytes())<=512 and manifest['truncated']
    assert fake.encode() not in path.read_bytes()
    assert isinstance(json.loads(path.read_text()),dict)


def test_prompt_manifest_verifies_latest_version_and_rejects_drift(tmp_path):
    from qi_harness.prompts import verify_prompt_manifest
    folder=tmp_path/'prompts';folder.mkdir()
    text=folder/'e1.md';text.write_text('public synthetic task fixture\n')
    manifest=tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'entries':[{'version':1,'seed_partition':'dev',
                         'files':{'prompts/e1.md':hashlib.sha256(text.read_bytes()).hexdigest()}}]}))
    assert verify_prompt_manifest(tmp_path,manifest_path=manifest)
    text.write_text('changed without a new committed entry\n')
    with pytest.raises(ValueError): verify_prompt_manifest(tmp_path,manifest_path=manifest)


def test_prompt_manifest_forbids_nondev_or_outside_repo_files(tmp_path):
    from qi_harness.prompts import verify_prompt_manifest
    path=tmp_path/'manifest.json'
    path.write_text(json.dumps({'entries':[{'version':1,'seed_partition':'sealed',
                                           'files':{'../outside':'0'*64}}]}))
    with pytest.raises(ValueError): verify_prompt_manifest(tmp_path,manifest_path=path)


def test_committed_prompt_manifest_covers_supported_environments_and_tools():
    from pathlib import Path
    from qi_harness.prompts import verify_prompt_manifest
    root=Path(__file__).resolve().parents[2]
    path=root/'results/prompt_manifest.json'
    value=json.loads(path.read_text())
    assert verify_prompt_manifest(root,manifest_path=path)
    latest=value['entries'][-1]
    assert latest['seed_partition']=='dev'
    names=' '.join(latest['files']).lower()
    assert all(environment in names for environment in ('e1','e2','e5','e6'))
    assert 'tool' in names


def test_committed_wire_tool_schema_matches_runtime_and_prompt_manifest():
    from pathlib import Path
    from qi_harness.tools import SCHEMAS,ToolSession
    from qi_harness.config import Limits
    root=Path(__file__).resolve().parents[2]
    path=root/'prompts/tool_schema.json'
    declared=json.loads(path.read_text())
    assert declared==SCHEMAS
    names={item['function']['name'] for item in declared}
    assert names=={'list_files','read_file','run_command','run_python','submit'}
    latest=json.loads((root/'results/prompt_manifest.json').read_text())['entries'][-1]
    assert latest['seed_partition']=='dev'
    assert latest['files']['prompts/tool_schema.json']==hashlib.sha256(path.read_bytes()).hexdigest()
    # Construction has no runtime side effects; the actual wire definitions are
    # taken from the manifest-bound disk artifact rather than an unbound copy.
    session=ToolSession(object(),environment='E1',limits=Limits())
    assert session.schemas==declared


def test_runtime_schema_drift_refused_before_any_tool_execution(monkeypatch):
    from qi_harness import tools
    from qi_harness.config import Limits
    monkeypatch.setattr(tools,'SCHEMAS',[])
    with pytest.raises(ValueError):tools.ToolSession(object(),environment='E1',limits=Limits())
