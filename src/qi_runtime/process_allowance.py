"""Host-only, per-command cgroup-v2 PID-exhaustion evidence.

Requires a local Docker daemon sharing the host PID/cgroup namespace. A missing
or unsupported observation never authorizes policy classification. Only kernel
counter files bound to the inspected full container ID are read, never /work.
"""
import asyncio
import json
from pathlib import Path, PurePosixPath
import re


async def cli(*args, **kwargs):
    # Call-time import avoids the checked runtime's initialization cycle.
    from qi_runtime import _cli
    return await _cli(*args, **kwargs)


def _read_host_text(path):
    return Path(path).read_text(encoding='ascii')


def _valid(snapshot):
    if not isinstance(snapshot,dict):return False
    identity=snapshot.get('container_id');pid=snapshot.get('init_pid')
    path=snapshot.get('cgroup_path');events=snapshot.get('max_events')
    if not isinstance(identity,str) or not re.fullmatch('[0-9a-f]{64}',identity):return False
    if type(pid) is not int or pid<=0:return False
    if type(snapshot.get('pids_max')) is not int or snapshot['pids_max']!=32:return False
    if type(events) is not int or events<0:return False
    if not isinstance(path,str):return False
    parts=PurePosixPath(path).parts
    return (path.startswith('/sys/fs/cgroup/') and '..' not in parts and
            any(part in (identity,'docker-'+identity+'.scope') for part in parts))


def process_allowance_exhausted(before,after,health):
    if not _valid(before) or not _valid(after):return False
    if not isinstance(health,dict) or health.get('success') is not True:return False
    if any(before[k]!=after[k] for k in ('container_id','init_pid','cgroup_path','pids_max')):return False
    return after['max_events']>before['max_events']


async def host_pids_snapshot(runtime):
    """Read kernel evidence without running any process inside the container."""
    try:
        async with asyncio.timeout(5):
            code,output,_=await cli('inspect',runtime.name,limit=65536)
        if code:return None
        inspection=json.loads(output)
        if not isinstance(inspection,list) or len(inspection)!=1:return None
        entry=inspection[0];identity=entry['Id'];pid=entry['State']['Pid']
        if identity!=runtime.info.id or not entry['State']['Running']:return None
        if type(pid) is not int or pid<=0:return None
        if type(entry['HostConfig']['PidsLimit']) is not int or entry['HostConfig']['PidsLimit']!=32:return None
        membership=_read_host_text(f'/proc/{pid}/cgroup').splitlines()
        if len(membership)!=1 or not membership[0].startswith('0::/'):return None
        relative=membership[0][3:];parts=PurePosixPath(relative).parts
        if '..' in parts or not relative.startswith('/'):return None
        if not any(part in (identity,'docker-'+identity+'.scope') for part in parts):return None
        directory='/sys/fs/cgroup'+relative.rstrip('/')
        maximum=_read_host_text(directory+'/pids.max').strip()
        if maximum!='32':return None
        counters={}
        for line in _read_host_text(directory+'/pids.events').splitlines():
            key,value=line.split()
            if key in counters:return None
            if not value.isdecimal():return None
            counters[key]=int(value)
        result={'container_id':identity,'init_pid':pid,'cgroup_path':directory,
                'pids_max':32,'max_events':counters['max']}
        return result if _valid(result) else None
    except (OSError,ValueError,KeyError,TypeError,AttributeError,TimeoutError,RuntimeError):
        return None
