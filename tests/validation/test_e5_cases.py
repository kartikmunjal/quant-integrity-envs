"""Prospective design-seed contracts for meaningful cost and capacity cases."""
import json
import math
import pytest


def test_e5_case_determinism_cost_gap_and_capacity_binding():
    from envs.e5_cost_realism.cases import public_input,case_diagnostics
    from envs.e5_cost_realism.finance import canonical_weights,metrics
    for tier in ('T1','T2','T3','T4'):
        for seed in (1004000,1004001,1004017):
            data=public_input(seed,tier)
            assert data==public_input(seed,tier)
            assert len(data['signals'])==48 and len(data['capacity_usd'])==8
            json.dumps(data,allow_nan=False)
            result=metrics(data,canonical_weights(data));diagnostic=case_diagnostics(data)
            assert math.isfinite(result['breakeven_holding_days'])
            assert not result['capacity_violation']
            assert diagnostic['cost_gap']>=.02
            assert diagnostic['capacity_binding_gap']>=.02
            assert data['context']


def test_e5_case_rejects_other_partitions():
    from envs.e5_cost_realism.cases import public_input
    for seed in (0,1003999,2000000):
        with pytest.raises(ValueError):public_input(seed,'T1')
