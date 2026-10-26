"""Shared checked Docker execution extracted from E1 for numeric tasksets."""
from __future__ import annotations
import asyncio
import base64
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path,PurePosixPath
from verifiers.v1.runtimes.docker import DockerConfig,DockerRuntime
from verifiers.v1.runtimes.base import ProgramResult

WORK=Path('/home/kartik/qi-sandbox')
PRIVATE=Path('/home/kartik/qi-private')
IMAGE=os.environ.get('QI_RUNTIME_IMAGE_DIGEST',os.environ.get('QI_E1_IMAGE_DIGEST','sha256:9cc803aaddbbb1a17c9eef928b5438d61769c9c9ba928fc285bc7ee622ad8353'))
MAX_SOURCE=100_000


async def cli(*args,limit=2_000_000):
    proc=await asyncio.create_subprocess_exec('docker',*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
    async def bounded(stream):
        result=bytearray()
        while chunk:=await stream.read(65536):
            result.extend(chunk)
            if len(result)>limit: raise ValueError('container output limit exceeded')
        return result.decode(errors='replace')
    jobs=[asyncio.create_task(bounded(proc.stdout)),asyncio.create_task(bounded(proc.stderr)),asyncio.create_task(proc.wait())]
    try:
        out,err,code=await asyncio.wait_for(asyncio.gather(*jobs),20)
        return code,out,err
    finally:
        for task in jobs:
            if not task.done(): task.cancel()
        if proc.returncode is None: proc.kill()
        await proc.wait()
        await asyncio.gather(*jobs,return_exceptions=True)


def audit(trace):
    return any(path in trace for path in ('/opt/qi','"canary"','"harness"','qi-private','AF_INET'))


class CheckedRuntime(DockerRuntime):
    """Network-none, read-only-root, single-mount runtime with audited solver APIs."""
    def __init__(self,workspace):
        super().__init__(DockerConfig(image=IMAGE,workdir='/work',allow=[]))
        if not re.fullmatch(r'sha256:[0-9a-f]{64}',IMAGE): raise ValueError('immutable local image ID required')
        workspace=Path(workspace)
        if workspace.is_symlink(): raise ValueError('workspace symlink rejected')
        self.workspace=workspace.resolve()
        if self.workspace.parent!=WORK: raise ValueError('unexpected workspace')
        self.flagged=False;self.snapshot=None;self.commands=[]

    async def start(self):
        self._container=self.name
        code,out,err=await cli('run','-d','--name',self.name,'--network','none','--read-only',
            '--cap-drop','ALL','--cap-add','SYS_PTRACE','--cap-add','SETUID','--cap-add','SETGID',
            '--security-opt','no-new-privileges','--pids-limit','32','--memory','128m','--cpus','1',
            '--mount',f'type=bind,source={self.workspace},target=/work','--workdir','/work',IMAGE,'sleep','infinity')
        if code: raise RuntimeError(err)
        self.info.id=out.strip()
        code,out,err=await cli('inspect',self.name)
        if code: raise RuntimeError(err)
        self.snapshot=json.loads(out)[0];cfg=self.snapshot['HostConfig'];mounts=self.snapshot['Mounts']
        if not (cfg['NetworkMode']=='none' and cfg['ReadonlyRootfs'] and not cfg['Privileged']
            and len(mounts)==1 and mounts[0]['Source']==str(self.workspace) and mounts[0]['Destination']=='/work'):
            raise RuntimeError('container boundary inspection failed')
        code,out,err=await cli('exec',self.name,'sha256sum','/opt/qi/harness')
        if code: raise RuntimeError(err)
        self._harness_hash=out

    async def prepare_execution(self,routes):
        # Framework routes are host-side bookkeeping; none is opened in this netns.
        # Only checked scripted harnesses are accepted by the project Envs, and it makes no model call.
        return None

    async def teardown(self):
        if self._container and not self._stopped:
            await cli('rm','-f',self._container)
            self._stopped=True

    async def run(self,argv,env):
        if env: raise ValueError('solver environment injection rejected')
        try:
            code,out,err=await cli('exec',self.name,'strace','-f','-yy','-s','512','-e','trace=%file,%network',
                                  '-u','nobody',*argv)
            self.flagged |= audit(err)
            status,current,_=await cli('exec',self.name,'sha256sum','/opt/qi/harness')
            self.flagged |= bool(status or current!=self._harness_hash)
            self.commands.append({'exit_code':code,'trace_sha256':hashlib.sha256(err.encode()).hexdigest()})
            return ProgramResult(code,out,err)
        except (TimeoutError,ValueError):
            self.flagged=True
            return ProgramResult(-1,'','bounded execution failed')

    async def execute(self):
        result=await self.run(['python','-I','-B','/work/program.py','/work/input.json'],{})
        return result.exit_code,result.stdout,result.stderr

    async def read(self,path,max_bytes=None):
        cap=MAX_SOURCE if max_bytes is None else min(max_bytes,2_000_000)
        if type(cap) is not int or cap<0: raise ValueError('invalid read bound')
        # O_NOFOLLOW+NONBLOCK and fstat reject symlinks, FIFOs/devices and oversized
        # files before transfer. A second bounded read catches growth after fstat.
        script='''import os,sys,stat,base64
fd=os.open(sys.argv[1],os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
s=os.fstat(fd); limit=int(sys.argv[2])
if not stat.S_ISREG(s.st_mode) or s.st_size>limit: sys.exit(3)
with os.fdopen(fd,'rb') as stream: data=stream.read(limit+1)
if len(data)>limit: sys.exit(4)
print(base64.b64encode(data).decode())
'''
        result=await self.run(['python','-I','-B','-c',script,path,str(cap)],{})
        if result.exit_code:
            self.flagged=True
            raise ValueError('unsafe, missing or oversized source/read')
        data=base64.b64decode(result.stdout,validate=False)
        if len(data)>cap:
            self.flagged=True
            raise ValueError('transfer exceeded read cap')
        return data

    async def _read(self,path):
        return await self.read(path,max_bytes=MAX_SOURCE)

    async def open_process(self,argv,env):
        raise ValueError('live processes unsupported; use bounded run')

    async def run_background(self,argv,env,log):
        raise ValueError('background services unsupported')

    async def write(self,path,data):
        target=PurePosixPath(path)
        if not target.is_absolute() or '..' in target.parts or not target.is_relative_to('/work'):
            raise ValueError('writes must target /work')
        if target.name=='program.py' and len(data)>MAX_SOURCE:
            self.flagged=True
            raise ValueError('source too large before upload')
        # Trusted setup transfer, not execution of solver source. The declared bind
        # is the only writable filesystem; a symlink cannot expose host private data.
        await super().write(path,data)



async def execute_program(data,program,answer_parser,namespace='task'):
    if len(program.encode())>MAX_SOURCE:
        return {'answer':None,'flagged':True,'exit_code':-1,'container_id':None}
    with tempfile.TemporaryDirectory(prefix=namespace+'-',dir=WORK) as directory:
        work=Path(directory);work.chmod(0o777)
        runtime=CheckedRuntime(work)
        try:
            await runtime.start()
            await runtime.write('/work/input.json',json.dumps(data,sort_keys=True).encode())
            await runtime.write('/work/program.py',program.encode())
            code,out,err=await runtime.execute()
            return {'answer':answer_parser(out) if code==0 else None,'flagged':runtime.flagged,
                    'exit_code':code,'container_id':runtime.info.id,'image':runtime.snapshot['Image'],
                    'source_sha256':hashlib.sha256(program.encode()).hexdigest(),
                    'input_sha256':hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),
                    'commands':runtime.commands}
        finally: await runtime.stop()

