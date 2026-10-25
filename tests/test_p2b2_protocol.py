"""Design-side tests of gate freezing and diagnostic policy definitions."""
import json
from pathlib import Path
import subprocess
import pytest
from scripts import run_p2b2_gate as gate
from scripts.design_p2b2 import alternative
from envs.e1_pit_backtest.cases import public_input,expected


def test_freeze_rejects_source_change(tmp_path,monkeypatch):
    path=tmp_path/'freeze.json';monkeypatch.setattr(gate,'FREEZE',path)
    path.write_text(json.dumps({'image':gate.IMAGE,'sources':{'bad':'hash'}}))
    with pytest.raises(RuntimeError):gate.verify_freeze()


def test_design_policy_has_real_numeric_effect():
    data=public_input(1001000,'T1');truth=expected(data)
    assert alternative(data,'annualize_daily_return')['backtest_return']==pytest.approx(truth['backtest_return']*252)
    assert alternative(data,'reverse_positions')['backtest_return']==pytest.approx(-truth['backtest_return'])
    assert alternative(data,'ignore_availability')!=truth
