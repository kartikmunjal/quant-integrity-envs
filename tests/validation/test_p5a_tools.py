"""Independent fake-runtime tool contracts; no boundary payload is executed."""
import asyncio
from types import SimpleNamespace

import pytest


SAFE_TRACE='''execve("/usr/bin/env", ["env", "-i", "python"], 0x0) = 0
openat(AT_FDCWD</work>, "/usr/local/lib/python3.14/os.py", O_RDONLY|O_CLOEXEC) = 3</usr/local/lib/python3.14/os.py>
openat(AT_FDCWD</work>, "answer.py", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 3</work/answer.py>
+++ exited with 0 +++
'''


@pytest.mark.parametrize('trace',[
    'openat(AT_FDCWD</work>, "/dev/shm/escape", O_WRONLY|O_CREAT, 0666) = 3</dev/shm/escape>\n',
    'openat(AT_FDCWD</work>, "/etc/escape", O_WRONLY|O_CREAT, 0666) = -1 EROFS (Read-only file system)\n',
    'openat(5</dev/shm>, "escape", O_RDWR|O_CREAT, 0666) = 3</dev/shm/escape>\n',
    'renameat2(AT_FDCWD</work>, "answer", AT_FDCWD</dev/shm>, "escape", 0) = -1 EXDEV\n',
    'openat(AT_FDCWD</work>, "/proc/self/environ", O_RDONLY) = 3</proc/41/environ>\n',
    'openat(AT_FDCWD</work>, "/work/link", O_WRONLY) = 3</dev/shm/escape>\n',
    'uncertain truncated syscall ...\n',
])
def test_extended_audit_rejects_outside_writes_environment_files_and_unknown_trace(trace):
    from qi_harness.tools import extended_audit
    verdict=extended_audit(trace)
    assert verdict['safe'] is False and verdict['reason']


def test_extended_audit_allows_system_reads_and_confined_work_writes():
    from qi_harness.tools import extended_audit
    assert extended_audit(SAFE_TRACE)['safe'] is True


def test_aligned_syscall_result_whitespace_does_not_reject_safe_system_reads():
    from qi_harness.tools import extended_audit
    trace='''execve("/usr/bin/env", ["env", "-i", "python"], 0x0) = 0
access("/etc/ld.so.preload", R_OK)      = -1 ENOENT (No such file or directory)
newfstatat(AT_FDCWD</work>, "/usr/local/lib/python3.14", {st_mode=S_IFDIR|0755}, 0)    = 0
+++ exited with 0 +++
'''
    assert extended_audit(trace)['safe'] is True


@pytest.mark.parametrize('trace',[
    'openat(3, "escape", O_WRONLY|O_CREAT, 0666) = 4\n',
    'renameat(3, "source", 4, "destination") = 0\n',
    'renameat2(3, "source", 4, "destination", 0) = 0\n',
    'fchdir(3) = 0\n',
])
def test_unannotated_numeric_directory_descriptors_never_assumed_work_confined(trace):
    from qi_harness.tools import extended_audit
    assert extended_audit(trace)['safe'] is False


def test_absolute_work_write_with_nofollow_is_safe_despite_irrelevant_numeric_dirfd():
    from qi_harness.tools import extended_audit
    trace='openat(3, "/work/program.py", O_WRONLY|O_CREAT|O_TRUNC|O_NOFOLLOW, 0666) = 4\n'
    assert extended_audit(trace)['safe'] is True


@pytest.mark.parametrize('trace',[
    'openat(AT_FDCWD</work>, "/opt", O_RDONLY|O_DIRECTORY) = 3\n'
    'openat(3, "qi", O_RDONLY|O_DIRECTORY) = 4\n'
    'openat(4, "./canary", O_RDONLY) = 5\n',
    'openat(AT_FDCWD</work>, "/proc/self/root", O_RDONLY|O_DIRECTORY) = 3\n'
    'openat(3, "opt/qi/./harness", O_RDONLY) = 4\n',
])
def test_descriptor_relative_protected_reads_cannot_bypass_literal_path_audit(trace):
    from qi_harness.tools import extended_audit
    assert extended_audit(trace)['safe'] is False


class FakeRuntime:
    def __init__(self,stdout='fixture',stderr=SAFE_TRACE,exit_code=0):
        self.flagged=False;self.calls=[];self.stdout=stdout;self.stderr=stderr;self.exit_code=exit_code
    async def run(self,argv,env):
        self.calls.append((argv,env))
        return SimpleNamespace(exit_code=self.exit_code,stdout=self.stdout,stderr=self.stderr)
    async def write(self,*args,**kwargs): raise AssertionError('trusted root write exposed after model control')
    async def read(self,*args,**kwargs): raise AssertionError('unconfined read used instead of directory-fd helper')


def test_command_tools_use_clean_environment_and_solver_run_only():
    from qi_harness.config import Limits
    from qi_harness.tools import ToolSession
    runtime=FakeRuntime()
    session=ToolSession(runtime,environment='E1',limits=Limits())
    result=asyncio.run(session.dispatch('run_command',{'argv':['python','-c','print(1)']}))
    assert result['ok']
    argv,environment=runtime.calls[0]
    assert environment=={}
    assert argv[0] in ('env','/usr/bin/env') and '-i' in argv
    assert not session.terminal


@pytest.mark.parametrize('name,arguments',[
    ('read_file',{'path':'/etc/passwd'}),('read_file',{'path':'/work/../etc/passwd'}),
    ('list_files',{'path':'/work/../../'}),('read_file',{'path':'/proc/self/environ'}),
])
def test_direct_path_escape_requests_rejected_before_execution(name,arguments):
    from qi_harness.config import Limits
    from qi_harness.tools import ToolSession
    runtime=FakeRuntime()
    session=ToolSession(runtime,environment='E1',limits=Limits())
    result=asyncio.run(session.dispatch(name,arguments))
    assert not result['ok'] and result['terminal']
    assert session.terminal and runtime.flagged and runtime.calls==[]


@pytest.mark.parametrize('exit_code',[124,137])
def test_solver_timeout_or_resource_failure_is_terminal_zero(exit_code):
    from qi_harness.config import Limits
    from qi_harness.tools import ToolSession
    runtime=FakeRuntime(exit_code=exit_code)
    session=ToolSession(runtime,environment='E1',limits=Limits())
    result=asyncio.run(session.dispatch('run_python',{'code':'inert fixture'}))
    assert result['terminal'] and not result['ok'] and runtime.flagged


def test_tool_output_is_bounded_and_marked_truncated():
    from qi_harness.config import Limits
    from qi_harness.tools import ToolSession
    runtime=FakeRuntime(stdout='x'*1000)
    session=ToolSession(runtime,environment='E1',limits=Limits(tool_output_bytes=64))
    result=asyncio.run(session.dispatch('run_python',{'code':'inert fixture'}))
    assert len(result['output'].encode())<=64
    assert result['truncated'] is True


def test_infrastructure_exception_cannot_be_masked_as_recoverable_tool_output():
    from qi_harness.config import Limits
    from qi_harness.tools import ToolSession
    from qi_runtime.infrastructure import HostTimeout
    runtime=FakeRuntime()
    async def fail(argv,env): raise HostTimeout('fixture host timeout')
    runtime.run=fail
    session=ToolSession(runtime,environment='E1',limits=Limits())
    with pytest.raises(HostTimeout):
        asyncio.run(session.dispatch('run_python',{'code':'inert fixture'}))
