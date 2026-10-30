"""Construction contracts authored independently before inspecting implementation.

Root had already written uncommitted case source when these tests were authored;
this deviation from cases-tests-first is reported explicitly, not concealed.
Do not execute before implementation and the planned construction-only screen.
"""
from collections import Counter
import json
import math
import statistics

import pytest


@pytest.fixture
def cases_module():
    from envs.e3_fdr_adjudication import cases
    return cases


@pytest.mark.parametrize('seed', [-1, 0, 999999, 1010000, 2000000])
def test_nondev_seeds_refused_before_generator_access(cases_module, seed):
    with pytest.raises(ValueError):
        cases_module.make_case(seed, 'T1')


def test_invalid_tier_refused(cases_module):
    with pytest.raises(ValueError):
        cases_module.make_case(1000000, 'T5')


def test_inactive_nan_assets_never_poison_active_portfolios(cases_module, monkeypatch):
    """Independent synthetic regression fixture, no shared generator execution."""
    import numpy as np
    from types import SimpleNamespace
    days, assets = np.arange(500)[:,None], np.arange(200)[None,:]
    returns = .01*np.sin(.7*days+.31*assets)+.002*np.cos(.2*days-.17*assets)
    signal = np.ones_like(returns)
    # Permanent delisting, rather than imputing an inactive asset to a fake zero.
    returns[100:,0] = np.nan
    signal[100:,0] = np.nan
    market = SimpleNamespace(returns=returns, signal=signal,
                             active=np.isfinite(returns))
    monkeypatch.setattr(cases_module,'market_for',lambda seed:market)
    case = cases_module.make_case(1000000,'T1')
    assert len(case['public']['candidates']) == 20
    for candidate in case['public']['candidates']:
        assert np.isfinite(candidate['returns']).all()
        assert np.isfinite(candidate['t_stat'])
    assert all(np.isfinite(value) for value in case['effects'].values())


def test_null_trials_have_diversified_portfolio_risk(cases_module, monkeypatch):
    """Pre-fix synthetic orthogonal-asset fixture; no generator/policy execution.

    Distinct Fourier frequencies make asset paths nearly orthogonal over 499
    sessions. Static signed equal-weight null portfolios should diversify their
    risk; signed single-asset paths should fail this prospective regression.
    """
    import numpy as np
    from types import SimpleNamespace
    days, assets = np.arange(500)[:,None], np.arange(200)[None,:]
    returns = .01*np.cos(2*np.pi*(days+1)*(assets+1)/499)
    signal = np.ones_like(returns)
    market = SimpleNamespace(returns=returns,signal=signal,active=np.ones_like(returns,dtype=bool))
    monkeypatch.setattr(cases_module,'market_for',lambda seed:market)
    case = cases_module.make_case(1000000,'T1')
    null_paths = [candidate['returns'] for candidate in case['public']['candidates']
                  if case['truth'][candidate['id']] == 0]
    # The design's common scale makes market std=.01. Diversification by 200
    # assets should comfortably reduce null risk, even with rho=.1 group mixing.
    average_null_risk = float(np.mean([np.std(path,ddof=1) for path in null_paths]))
    assert average_null_risk < .003


def test_cross_process_blas_thread_count_preserves_public_bytes():
    """Construction-only determinism regression on one development seed."""
    import os
    from pathlib import Path
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[2]
    source = ('from envs.e3_fdr_adjudication.cases import make_case; '
              'print(make_case(1000000,"T3")["data_sha256"])')
    hashes=[]
    for threads in ('1','2'):
        environment = os.environ.copy()
        environment.update(OPENBLAS_NUM_THREADS=threads,OMP_NUM_THREADS=threads,
                           MKL_NUM_THREADS=threads,VECLIB_MAXIMUM_THREADS=threads)
        hashes.append(subprocess.check_output([sys.executable,'-c',source],cwd=root,
                                               env=environment,text=True).strip())
    assert len(hashes[0]) == 64
    assert hashes[0] == hashes[1]


@pytest.mark.parametrize('tier', ['T1','T2','T3','T4'])
def test_construction_shape_truth_statistics_and_determinism(cases_module, tier):
    first = cases_module.make_case(1000000, tier)
    second = cases_module.make_case(1000000, tier)
    assert json.dumps(first, sort_keys=True, allow_nan=False) == json.dumps(second, sort_keys=True, allow_nan=False)
    assert first['generator_version_hash'] == 'eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921'
    assert len(first['data_sha256']) == 64
    public = first['public']
    candidates = public['candidates']
    assert len(candidates) == 20
    ids = [candidate['id'] for candidate in candidates]
    assert len(set(ids)) == 20
    assert set(ids) == set(first['truth']) == set(first['effects'])
    assert Counter(first['truth'].values()) == {0:10,1:10}
    assert len(public['hypothesis']['effect_t_by_coefficient']) > 0
    assert sorted(Counter(c['group'] for c in candidates).values()) == [10,10]
    expected_rho = {'T1':.1,'T2':.3,'T3':.7,'T4':.5}[tier]
    for candidate in candidates:
        assert candidate['rho'] == expected_rho
        assert 1 <= candidate['N'] <= 500
        returns = candidate['returns']
        assert len(returns) == 499
        assert all(math.isfinite(value) for value in returns)
        sd = statistics.stdev(returns)
        assert sd > 0
        expected_t = statistics.mean(returns) / sd * math.sqrt(len(returns))
        assert candidate['t_stat'] == pytest.approx(expected_t, rel=1e-10, abs=1e-10)
        assert not {'truth','is_real','effect','coefficient','selected_trial','oracle',
                    'real_hypothesis_coefficient'} & set(candidate)
        if first['truth'][candidate['id']] == 0:
            assert first['effects'][candidate['id']] == 0
    # Every class follows the prospectively declared N cycle, not outcome tuning.
    for is_real in (0,1):
        selected = [c for c in candidates if first['truth'][c['id']] == is_real]
        if tier == 'T4':
            assert Counter(c['N'] for c in selected) == ({1:5,500:5} if is_real else {500:10})
        else:
            schedule = {'T1':[1,4,16], 'T2':[20,100,500], 'T3':[1,50,500]}[tier]
            assert Counter(c['N'] for c in selected) == Counter(schedule[i%3] for i in range(10))
