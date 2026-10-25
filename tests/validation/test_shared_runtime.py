"""Contracts written before extracting the shared E1/E5 container implementation."""
import asyncio
import os
from pathlib import Path
import tempfile
import pytest


def test_e1_uses_the_single_shared_runtime_implementation():
    from qi_runtime import CheckedRuntime
    from envs.e1_pit_backtest.runtime import E1Runtime
    assert E1Runtime is CheckedRuntime
    assert E1Runtime.__module__.startswith('qi_runtime')


@pytest.mark.skipif(os.environ.get('QI_REAL_SANDBOX')!='1',reason='requires Docker')
def test_shared_runtime_keeps_checked_mount_and_read_bounds():
    from qi_runtime import CheckedRuntime,WORK
    async def run():
        with tempfile.TemporaryDirectory(prefix='shared-',dir=WORK) as directory:
            work=Path(directory);work.chmod(0o777);runtime=CheckedRuntime(work)
            try:
                await runtime.start()
                assert runtime.snapshot['HostConfig']['NetworkMode']=='none'
                assert runtime.snapshot['HostConfig']['ReadonlyRootfs']
                assert not runtime.snapshot['HostConfig']['Privileged']
                assert len(runtime.snapshot['Mounts'])==1
                await runtime.write('/work/program.py',b'print(1)')
                assert await runtime.read('/work/program.py',max_bytes=100000)==b'print(1)'
                with pytest.raises(ValueError): await runtime.read('/work/program.py',max_bytes=1)
            finally:await runtime.stop()
    asyncio.run(run())
