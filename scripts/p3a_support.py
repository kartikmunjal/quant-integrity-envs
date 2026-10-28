"""P3a bounded, hash-addressed local evidence and small committed shards."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import subprocess
import time

ROOT=Path(__file__).resolve().parents[1]
TRACKED_BUDGET=32*1024**2
LOCAL_BUDGET=2*1024**3
SHARD_BUDGET=512*1024


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(data):return hashlib.sha256(data).hexdigest()

def shards(rows,prefix):
    prefix=Path(prefix);prefix.parent.mkdir(parents=True,exist_ok=True)
    pending=[];result=[]
    def flush(batch):
        payload=gzip.compress(b'\n'.join(canonical(r) for r in batch)+b'\n',mtime=0)
        if len(payload)>SHARD_BUDGET:
            if len(batch)==1:raise ValueError('single compact row exceeds shard budget')
            mid=len(batch)//2;flush(batch[:mid]);flush(batch[mid:]);return
        path=prefix.parent/(prefix.name+f'-{len(result):04d}.jsonl.gz')
        if path.exists():raise FileExistsError(path)
        path.write_bytes(payload)
        result.append({'path':str(path.relative_to(ROOT)),'bytes':len(payload),'sha256':sha(payload),'rows':len(batch)})
    for row in rows:
        pending.append(row)
        if len(pending)>=100:flush(pending);pending=[]
    if pending:flush(pending)
    return result


class Archive:
    def __init__(self,tag):
        if not tag or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in tag):raise ValueError('tag')
        self.root=ROOT/'artifacts/p3a'/tag
        self.root.mkdir(parents=True,exist_ok=False)
        self.entries=[];self.bytes=0
        self.prior_bytes=sum(p.stat().st_size for p in (ROOT/"artifacts/p3a").rglob("*") if p.is_file())
    def add(self,label,row):
        if not label or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in label):raise ValueError('label')
        payload=gzip.compress(canonical(row),mtime=0)
        total=self.prior_bytes+self.bytes
        if total+len(payload)>LOCAL_BUDGET:raise ValueError('local evidence storage budget exceeded; existing evidence retained')
        path=self.root/(label+'.json.gz')
        with path.open('xb') as stream:stream.write(payload)
        entry={'path':str(path.relative_to(ROOT)),'bytes':len(payload),'sha256':sha(payload)}
        self.entries.append(entry);self.bytes+=len(payload)
        return entry
    def manifest(self):return {'entries':self.entries,'compressed_bytes':self.bytes,'local_only':True,'reconstruction':'Run declared seed/template policy in the frozen local checked runtime. Archives are retained locally, not published in Git; paths and SHA256 bind audit evidence.'}


def inventory():
    def size(root):return sum(p.stat().st_size for p in (ROOT/root).rglob('*') if p.is_file())
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).split(b'\0')
    st=os.statvfs(ROOT)
    return {'phase':'P3a','time_unix':time.time(),'sizes_bytes':{k:size(k) for k in ('.git','logs','results','artifacts/p3a')},
        'tracked_worktree_bytes':sum((ROOT/os.fsdecode(p)).stat().st_size for p in tracked if p and (ROOT/os.fsdecode(p)).is_file()),
        'git_objects':subprocess.check_output(['git','count-objects','-vH'],cwd=ROOT,text=True),
        'filesystem':{'total_bytes':st.f_blocks*st.f_frsize,'available_bytes':st.f_bavail*st.f_frsize}}


def verify_entries(entries):
    for e in entries:
        p=ROOT/e['path']
        if not p.resolve().is_relative_to(ROOT):raise ValueError('manifest escape')
        raw=p.read_bytes()
        if len(raw)!=e['bytes'] or sha(raw)!=e['sha256']:raise ValueError('manifest mismatch '+e['path'])
