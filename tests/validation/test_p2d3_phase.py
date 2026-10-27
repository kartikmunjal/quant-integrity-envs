"""Seed plumbing only: no case or reward changes in source files."""
import hashlib,json
from pathlib import Path
import pytest
from qi_runtime.phase import e6_fresh_context,historical_e6_context

def test_fresh_admission_preserves_existing_bytes_and_uses_exact_new_seed():
    from envs.e6_data_traps.cases import public_input
    from envs.e6_data_traps import runtime
    before=json.dumps(public_input(1002000,'T4'),sort_keys=True)
    with pytest.raises(ValueError):public_input(1005000,'T4')
    with e6_fresh_context():
        assert json.dumps(public_input(1002000,'T4'),sort_keys=True)==before
        value=public_input(1005000,'T4')
        assert value['quotes']
        assert 1006000<=runtime.replay_seed(1005000,'T4','source')<=1006999
        with pytest.raises(ValueError):public_input(1005500,'T4')
    with pytest.raises(ValueError):public_input(1005000,'T4')

def test_historical_reward_context_restores_current_function():
    from envs.e6_data_traps import v1_taskset
    original=v1_taskset.score_pair
    with historical_e6_context():assert v1_taskset.score_pair is not original
    assert v1_taskset.score_pair is original
