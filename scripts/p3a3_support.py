"""P3a3 bounded, hash-addressed local evidence and small committed shards."""
from pathlib import Path
import gzip
import hashlib
import json
import os
import subprocess
import time
from functools import lru_cache

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
        ensure_tracked_capacity(len(payload))
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
        self.root=ROOT/'artifacts/p3a3'/tag
        self.root.mkdir(parents=True,exist_ok=False)
        self.entries=[];self.bytes=0
        self.prior_bytes=sum(p.stat().st_size for p in (ROOT/"artifacts/p3a3").rglob("*") if p.is_file())
    def add(self,label,row):
        if not label or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in label):raise ValueError('label')
        payload=gzip.compress(canonical(row),mtime=0)
        total=self.local_bytes()
        if total+len(payload)>LOCAL_BUDGET:raise ValueError('local evidence storage budget exceeded; existing evidence retained')
        path=self.root/(label+'.json.gz')
        with path.open('xb') as stream:stream.write(payload)
        entry={'path':str(path.relative_to(ROOT)),'bytes':len(payload),'sha256':sha(payload)}
        self.entries.append(entry);self.bytes+=len(payload)
        return entry
    def local_bytes(self):
        return sum(p.stat().st_size for p in (ROOT/'artifacts/p3a3').rglob('*') if p.is_file())
    def ensure_local_capacity(self,additional=0):
        if self.local_bytes()+additional>LOCAL_BUDGET:raise ValueError('local evidence storage reserve exhausted')
    def manifest(self):return {'entries':self.entries,'compressed_bytes':self.bytes,'local_only':True,'reconstruction':'Run declared seed/template policy in the frozen local checked runtime. Archives are retained locally, not published in Git; paths and SHA256 bind audit evidence.'}


def inventory():
    def size(root):return sum(p.stat().st_size for p in (ROOT/root).rglob('*') if p.is_file())
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).split(b'\0')
    st=os.statvfs(ROOT)
    return {'phase':'P3a3','time_unix':time.time(),'sizes_bytes':{k:size(k) for k in ('.git','logs','results','artifacts/p3a3')},
        'tracked_worktree_bytes':sum((ROOT/os.fsdecode(p)).stat().st_size for p in tracked if p and (ROOT/os.fsdecode(p)).is_file()),
        'git_objects':subprocess.check_output(['git','count-objects','-vH'],cwd=ROOT,text=True),
        'filesystem':{'total_bytes':st.f_blocks*st.f_frsize,'available_bytes':st.f_bavail*st.f_frsize}}


def verify_entries(entries):
    for e in entries:
        p=ROOT/e['path']
        if not p.resolve().is_relative_to(ROOT):raise ValueError('manifest escape')
        raw=p.read_bytes()
        if len(raw)!=e['bytes'] or sha(raw)!=e['sha256']:raise ValueError('manifest mismatch '+e['path'])


@lru_cache(maxsize=2)
def _legacy_phase_evidence(root):
    root=Path(root)
    if not (root/'.git').exists():return ()
    return tuple(subprocess.check_output(['git','diff','--name-only','2c54171c7c9f2d97bb990c36d9bf68513a1a8e72','HEAD'],cwd=root,text=True).splitlines())


def phase_evidence_bytes():
    """Count eligible P3a3 tracked evidence, including new untracked phase paths."""
    paths=set()
    for folder in ('logs','results','reports'):
        directory=ROOT/folder
        if directory.exists():
            for top in directory.iterdir():
                if not top.name.lower().startswith('p3a3'):continue
                if top.is_file():paths.add(top)
                elif top.is_dir():paths.update(p for p in top.rglob('*') if p.is_file())
    return sum(p.stat().st_size for p in paths)


def ensure_tracked_capacity(additional=0):
    if type(additional) is not int or additional<0:raise ValueError('nonnegative evidence reservation')
    used=phase_evidence_bytes()
    if used+additional>TRACKED_BUDGET:raise ValueError(f'P3a3 tracked evidence budget exceeded: {used}+{additional}>{TRACKED_BUDGET}')
    return used


async def execute_plan(plan,call,concurrency,ledger,journal_root):
    import asyncio
    from qi_runtime.infrastructure import run_with_retry
    if not 1<=concurrency<=24:raise ValueError('bounded concurrency')
    rows=[None]*len(plan);iterator=iter(enumerate(plan))
    async def worker():
        for index,item in iterator:
            rows[index]=await run_with_retry(lambda:call(item),metadata={'index':index},ledger=ledger,journal_root=journal_root)
    await asyncio.gather(*(worker() for _ in range(concurrency)))
    return rows
