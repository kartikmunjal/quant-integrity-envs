"""Independent prospective Env adapter contracts, no provisioning or policies."""
import asyncio
import hashlib
from pathlib import Path

import pytest


def test_bindings_only_include_supported_main_branch_tasksets():
    from qi_harness.environments import bindings
    assert set(bindings())=={'E1','E2','E5','E6'}


@pytest.mark.parametrize('environment,seed',[
    ('E3',1002500),('E1',2000000),('E2',2000000),('E5',2000000),('E6',2000000),
    ('E1',0),('E1',1000000),('E2',1000000),('E5',1000000),('E6',1000000),
])
def test_rejects_unsupported_or_outside_window_before_client_or_runtime(monkeypatch,environment,seed):
    from qi_harness import environments
    from qi_harness.config import Limits
    class Client:
        async def complete(self,*args,**kwargs): raise AssertionError('invalid seed/environment contacted model')
    def forbidden(*args,**kwargs): raise AssertionError('invalid seed/environment provisioned runtime')
    monkeypatch.setattr(environments,'CheckedRuntime',forbidden)
    with pytest.raises(ValueError):
        asyncio.run(environments.run_model_episode(environment,seed,'T1',Client(),Limits()))


def test_validation_context_preserves_frozen_sources_and_rejects_e3():
    from qi_harness.environments import validation_context
    root=Path(__file__).resolve().parents[2]
    files=[root/'prereg.yaml',*(root/'src/qi_runtime').glob('*.py'),*(root/'src/qi/gen').glob('*.py')]
    files.extend(path for pattern in ('e1*','e2*','e5*','e6*')
                 for folder in (root/'envs').glob(pattern) for path in folder.glob('*.py'))
    fingerprint=lambda:{str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    before=fingerprint()
    for environment in ('E1','E2','E5','E6'):
        with validation_context(environment): pass
    assert fingerprint()==before
    with pytest.raises(ValueError):
        with validation_context('E3'): pass


def test_native_factory_exports_model_harness_and_env_without_replacing_old_classes():
    import verifiers.v1 as vf
    from qi_harness import ModelEnv,ModelHarness
    from envs.e1_pit_backtest.v1_taskset import E1Env,E1Harness
    assert issubclass(ModelEnv,vf.Env) and issubclass(ModelHarness,vf.Harness)
    assert ModelEnv is not E1Env and ModelHarness is not E1Harness
