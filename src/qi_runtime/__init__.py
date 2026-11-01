"""Shared checked Docker execution extracted from E1 for numeric tasksets."""
from __future__ import annotations
import asyncio
import contextlib
import base64
import hashlib
import json
import shlex
import os
import re
import tempfile
import uuid
import time
from pathlib import Path,PurePosixPath
from .infrastructure import DockerFailure,HostTimeout,record_exception,note_policy,note_resource,PolicyFailure,PolicyOutputLimit,journal_boundary,track_runtime,_CURRENT
from verifiers.v1.runtimes.docker import DockerConfig,DockerRuntime
from verifiers.v1.runtimes.base import ProgramResult
from .process_allowance import host_pids_snapshot,process_allowance_exhausted

WORK=Path('/home/kartik/qi-sandbox')
PRIVATE=Path('/home/kartik/qi-private')
IMAGE=os.environ.get('QI_RUNTIME_IMAGE_DIGEST',os.environ.get('QI_E1_IMAGE_DIGEST','sha256:9cc803aaddbbb1a17c9eef928b5438d61769c9c9ba928fc285bc7ee622ad8353'))
MAX_SOURCE=100_000


async def _cli(*args,limit=2_000_000,policy_output=False,input_data=None):
    proc=await asyncio.create_subprocess_exec('docker',*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,stdin=asyncio.subprocess.PIPE if input_data is not None else None)
    async def bounded(stream):
        result=bytearray()
        while chunk:=await stream.read(65536):
            result.extend(chunk)
            if len(result)>limit:
                if policy_output:raise PolicyOutputLimit('container output limit exceeded')
                raise DockerFailure('trusted Docker output limit exceeded')
        return result.decode(errors='replace')
    jobs=[asyncio.create_task(bounded(proc.stdout)),asyncio.create_task(bounded(proc.stderr)),asyncio.create_task(proc.wait())]
    async def feed():
        proc.stdin.write(input_data);await proc.stdin.drain();proc.stdin.close()
    if input_data is not None:jobs.append(asyncio.create_task(feed()))
    try:
        values=await asyncio.wait_for(asyncio.gather(*jobs),60)
        out,err,code=values[:3]
        return code,out,err
    except TimeoutError as error:
        wrapped=HostTimeout('Docker client host deadline exceeded: '+str(args[0]))
        record_exception(error);raise wrapped from error
    finally:
        for task in jobs:
            if not task.done(): task.cancel()
        if proc.returncode is None:
            with contextlib.suppress(ProcessLookupError):proc.kill()
        await proc.wait()
        await asyncio.gather(*jobs,return_exceptions=True)


async def daemon_probe():
    started=time.monotonic()
    try:
        code,_,_=await asyncio.wait_for(_cli('version','--format','{{.Server.Version}}',limit=4096),5.)
        return {'success':code==0,'duration_seconds':time.monotonic()-started,
                'exception_type':None if code==0 else 'DockerFailure'}
    except Exception as error:
        return {'success':False,'duration_seconds':time.monotonic()-started,'exception_type':type(error).__name__}


async def cli(*args,limit=2_000_000,policy_output=False,input_data=None):
    started=time.monotonic();success=False;exception_type=None;output_bytes=0
    try:
        result=await _cli(*args,limit=limit,policy_output=policy_output,input_data=input_data)
        success=result[0]==0;output_bytes=sum(len(v.encode()) for v in result[1:])
        return result
    except BaseException as error:
        exception_type=type(error).__name__
        raise
    finally:
        duration=time.monotonic()-started
        current=_CURRENT.get()
        if current is not None:
            try:probe=await daemon_probe()
            except BaseException as probe_error:
                probe={'success':False,'duration_seconds':0.,'exception_type':type(probe_error).__name__}
                if isinstance(probe_error,asyncio.CancelledError) and exception_type is None:raise
            current.transfers.append({'operation':str(args[0]) if args else '',
                'input_bytes':len(input_data) if input_data is not None else 0,
                'output_bytes':output_bytes,'duration_seconds':duration,'success':success,
                'exception_type':exception_type,'daemon_probe':probe})


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
        self.flagged=False;self.snapshot=None;self.commands=[];self._teardown_lock=asyncio.Lock()
        track_runtime(self)

    @journal_boundary
    async def start(self):
        self._container=self.name
        note_resource(self.name,event="provisioning")
        code,out,err=await cli('run','-d','--name',self.name,'--network','none','--read-only',
            '--cap-drop','ALL','--cap-add','SYS_PTRACE','--cap-add','SETUID','--cap-add','SETGID',
            '--security-opt','no-new-privileges','--pids-limit','32','--memory','128m','--cpus','1',
            '--mount',f'type=bind,source={self.workspace},target=/work','--workdir','/work',IMAGE,'sleep','infinity')
        if code: raise DockerFailure(err)
        self.info.id=out.strip()
        note_resource(self.name,self.info.id)
        code,out,err=await cli('inspect',self.name)
        if code: raise DockerFailure(err)
        self.snapshot=json.loads(out)[0];cfg=self.snapshot['HostConfig'];mounts=self.snapshot['Mounts']
        if not (cfg['NetworkMode']=='none' and cfg['ReadonlyRootfs'] and not cfg['Privileged']
            and len(mounts)==1 and mounts[0]['Source']==str(self.workspace) and mounts[0]['Destination']=='/work'):
            raise RuntimeError('container boundary inspection failed')
        code,out,err=await cli('exec',self.name,'sha256sum','/opt/qi/harness')
        if code: raise DockerFailure(err)
        self._harness_hash=out

    async def prepare_execution(self,routes):
        # Framework routes are host-side bookkeeping; none is opened in this netns.
        # Only checked scripted harnesses are accepted by the project Envs, and it makes no model call.
        return None

    @journal_boundary
    async def teardown(self):
        async with self._teardown_lock:
            if self._container and not self._stopped:
                code,out,err=await cli('rm','-f',self._container)
                if code and 'No such container' not in err:raise DockerFailure('Docker cleanup failed: '+err)
                self._stopped=True
                note_resource(self.name,self.info.id,event='removed')

    @journal_boundary
    async def run(self,argv,env):
        # Only fresh host-kernel exhaustion evidence may override a command's
        # infrastructure outcome. Normal command records remain unchanged.
        if env:return await self._run_command(argv,env)
        if getattr(self,'_process_allowance_violation',False):
            return ProgramResult(1,'','process allowance exhausted')
        before=await host_pids_snapshot(self)
        result=None;failure=None
        try:result=await self._run_command(argv,env)
        except (DockerFailure,HostTimeout) as error:failure=error
        after=await host_pids_snapshot(self)
        if process_allowance_exhausted(before,after,{'success':True}):
            health=await daemon_probe()
            if process_allowance_exhausted(before,after,health):
                evidence={'exit_code':1,'policy_outcome':'process_allowance_exhausted_pending_cleanup',
                    'host_pids_before':before,'host_pids_after':after,'daemon_probe':health}
                self.commands.append(evidence)
                await self.stop()
                if not self.stopped:raise DockerFailure('process-exhaustion cleanup not confirmed')
                self.flagged=True;self._process_allowance_violation=True;note_policy()
                evidence['policy_outcome']='process_allowance_exhausted'
                return ProgramResult(1,'','process allowance exhausted')
            if failure is None:
                raise DockerFailure('daemon health unconfirmed after positive process-exhaustion evidence')
        if failure is not None:raise failure
        return result

    async def _run_command(self,argv,env):
        if env:
            note_policy();raise ValueError('solver environment injection rejected')
        try:
            # Docker exec status overlaps ordinary solver exits (including
            # 125/126/127). A root wrapper records the traced child status in a
            # private directory on Docker's sticky /dev/shm tmpfs. The solver
            # UID cannot read, replace, rename or remove this evidence.
            status_dir='/dev/shm/qi-status-'+uuid.uuid4().hex
            wrapper='''import json,os,subprocess,sys
folder=sys.argv[1]
os.mkdir(folder,0o700)
result=subprocess.run(sys.argv[2:])
with open(folder+'/exit.json','x') as stream:
 json.dump({'exit_code':result.returncode},stream)
 stream.flush();os.fsync(stream.fileno())
'''
            transport,out,err=await cli('exec',self.name,'python','-I','-B','-c',wrapper,status_dir,
                                  'strace','-f','-yy','-s','512','-e','trace=%file,%network',
                                  '-u','nobody','timeout','--signal=TERM','--kill-after=1','20s',*argv,policy_output=True)
            # Preserve observed policy evidence before any subsequent trusted
            # status retrieval can fail. Preserve it independently of host errors.
            self.flagged |= audit(err)
            if self.flagged:
                note_policy()
                record_exception(PolicyFailure(err),metadata={'origin':'solver_audit','runtime':self.name})
                exits=re.findall(r'\+\+\+ exited with (\d+) \+\+\+',err)
                code=int(exits[-1]) if exits else 1
                self.commands.append({'exit_code':code,'exit_status_source':'audit_trace','trace_sha256':hashlib.sha256(err.encode()).hexdigest(),'policy_outcome':'audit_violation'})
                if transport:raise DockerFailure('Docker exec transport failed after audited policy outcome')
                return ProgramResult(code,out,err)
            reader='''import os,sys
folder=sys.argv[1]
with open(folder+'/exit.json') as stream: print(stream.read())
os.unlink(folder+'/exit.json');os.rmdir(folder)
'''
            marker,body,problem=await cli('exec',self.name,'python','-I','-B','-c',reader,status_dir)
            if marker:
                probe,body,problem=await cli('inspect',self.name)
                if probe:raise DockerFailure('Docker status inspection failed: '+problem)
                state=json.loads(body)[0]['State']
                if state.get('OOMKilled'):
                    code=137;note_policy()
                else:raise DockerFailure('Docker exec lacks protected solver completion status')
            else:
                status_record=json.loads(body)
                code=status_record['exit_code']
                if type(code) is not int:raise DockerFailure('invalid protected solver exit status')
                if transport:
                    # A completed child remains a policy outcome even if the
                    # Docker client subsequently reports a transport failure.
                    if code or audit(err):note_policy()
                    raise DockerFailure('Docker exec transport failed after solver completion')
            self.flagged |= audit(err)
            if self.flagged:note_policy()
            if code:
                note_policy()
                record_exception(PolicyFailure(err),metadata={'origin':'solver_command','runtime':self.name,'exit_code':code})
                probe,body,problem=await cli('inspect',self.name)
                if probe:raise DockerFailure('Docker failed after solver command: '+problem)
                state=json.loads(body)[0]['State']
                if not state.get('Running') and not state.get('OOMKilled'):raise DockerFailure('Container unexpectedly stopped')
                note_policy()
            status,current,_=await cli('exec',self.name,'sha256sum','/opt/qi/harness')
            if status:
                probe,body,problem=await cli('inspect',self.name)
                if probe:raise DockerFailure('Docker harness check failed: '+problem)
                raise DockerFailure('Trusted Docker harness probe failed')
            self.flagged |= bool(status or current!=self._harness_hash)
            if self.flagged:note_policy()
            self.commands.append({'exit_code':code,'trace_sha256':hashlib.sha256(err.encode()).hexdigest(),'policy_outcome':('solver_timeout' if code in (124,137) else 'solver_crash' if code else 'audit_violation' if self.flagged else None)})
            return ProgramResult(code,out,err)
        except PolicyOutputLimit as error:
            self.flagged=True;note_policy();record_exception(error)
            return ProgramResult(-1,'','bounded execution failed')

    async def execute(self):
        result=await self.run(['python','-I','-B','/work/program.py','/work/input.json'],{})
        return result.exit_code,result.stdout,result.stderr

    @journal_boundary
    async def read(self,path,max_bytes=None):
        if getattr(self,'_process_allowance_violation',False):raise ValueError('process-exhausted solver has no trusted transfer')
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
            self.flagged=True;note_policy()
            raise ValueError('unsafe, missing or oversized source/read')
        data=base64.b64decode(result.stdout,validate=False)
        if len(data)>cap:
            self.flagged=True;note_policy()
            raise ValueError('transfer exceeded read cap')
        return data

    async def _read(self,path):
        return await self.read(path,max_bytes=MAX_SOURCE)

    async def open_process(self,argv,env):
        raise ValueError('live processes unsupported; use bounded run')

    async def run_background(self,argv,env,log):
        raise ValueError('background services unsupported')

    @journal_boundary
    async def write(self,path,data):
        target=PurePosixPath(path)
        if not target.is_absolute() or '..' in target.parts or not target.is_relative_to('/work'):
            note_policy();raise ValueError('writes must target /work')
        if target.name=='program.py' and len(data)>MAX_SOURCE:
            self.flagged=True;note_policy()
            raise ValueError('source too large before upload')
        # Trusted setup transfer, not execution of solver source. The declared bind
        # is the only writable filesystem; a symlink cannot expose host private data.
        parent=shlex.quote(str(target.parent));dest=shlex.quote(path)
        code,out,err=await cli('exec','-i','--workdir','/work',self._container,'sh','-c',f'mkdir -p {parent} && cat > {dest}',input_data=data)
        if code:raise DockerFailure('trusted Docker transfer failed: '+err)



@journal_boundary
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


from .infrastructure import install_rollout_diagnostics
install_rollout_diagnostics()
