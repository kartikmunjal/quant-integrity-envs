"""Independent prospective E5 tests; written before new primary implementation."""
import copy
import importlib
import math

import pytest


@pytest.fixture(params=['envs.e5_cost_realism.checker', 'envs.e5_cost_realism.finance'])
def calculator(request):
    return importlib.import_module(request.param)


def example():
    return dict(signals=[[1., -1.], [-1., 1.]], returns=[[.1, -.1], [-.2, .2]],
                spread_bps=[20., 20.], impact_coefficient=[1., 1.],
                adv_usd=[1000., 1000.], capacity_usd=[25., 25.], notional=100.)


def test_capacity_clips_positions_and_trades_without_renormalizing(calculator):
    assert calculator.canonical_weights(example()) == [[.25, -.25], [0., 0.]]


def test_scalar_trade_cost_and_terminal_close(calculator):
    data = example()
    weights = [[.25, -.25], [0., 0.]]
    result = calculator.metrics(data, weights)
    # Opening and next-day closing each trade 25 USD per name.
    cost = .5 * (.001 + .01 * math.sqrt(.025))
    daily = [.05-cost, -cost]
    mean = sum(daily)/2
    std = abs(daily[0]-daily[1])/2
    assert result['net_sharpe'] == pytest.approx(math.sqrt(252)*mean/std)
    # Fresh roundtrip first day costs twice opening, second day zero.
    assert result['breakeven_holding_days'] == pytest.approx(cost/.025)
    assert not result['capacity_violation']
    terminal = copy.deepcopy(data)
    terminal['signals'] = [[1., -1.]]
    terminal['returns'] = [[.1, -.1]]
    out = calculator.metrics(terminal, [[.25, -.25]])
    assert out['net_sharpe'] == pytest.approx(math.sqrt(252)*(.05-2*cost)/1e-12)


def test_infeasible_and_nonpositive_edge(calculator):
    result = calculator.metrics(example(), [[.5, -.5], [-.5, .5]])
    assert result['capacity_violation']
    data = example()
    data['returns'] = [[0., 0.], [0., 0.]]
    assert not math.isfinite(calculator.metrics(data, calculator.canonical_weights(data))['breakeven_holding_days'])


def execution(answer):
    return {'answer': answer, 'flagged': False, 'exit_code': 0}


def test_independent_schema_and_reward_boundaries():
    from envs.e5_cost_realism import checker as c
    data = example()
    weights = c.canonical_weights(data)
    truth = c.metrics(data, weights)
    answer = dict(weights=weights, net_sharpe=truth['net_sharpe'],
                  breakeven_holding_days=truth['breakeven_holding_days'])
    assert c.check_answer(answer, data) is not None
    for bad in [None, {}, dict(answer, net_sharpe=True), dict(answer, net_sharpe=float('nan')),
                dict(answer, weights=[[True, 0.], [0., 0.]]), dict(answer, extra=1)]:
        assert c.check_answer(bad, data) is None
    assert c.score_pair(execution(answer), execution(answer), data, data) == pytest.approx(1.)
    assert c.score_pair(execution(answer), None, data, data) == 0.
    near = dict(answer, net_sharpe=truth['net_sharpe']*1.00505,
                breakeven_holding_days=truth['breakeven_holding_days']*1.00505)
    assert c.score_pair(execution(near), execution(near), data, data) == pytest.approx(.125)
    for field in ['net_sharpe', 'breakeven_holding_days']:
        far = dict(answer, **{field: answer[field]*1.02})
        assert c.score_pair(execution(far), execution(answer), data, data) == 0.
    flagged = dict(execution(answer), flagged=True)
    assert c.score_pair(flagged, execution(answer), data, data) == 0.


@pytest.fixture(params=['envs.e5_cost_realism.checker', 'envs.e5_cost_realism.reward'])
def scorer(request):
    return importlib.import_module(request.param)


def correct_answer():
    from envs.e5_cost_realism import checker
    data = example()
    weights = checker.canonical_weights(data)
    truth = checker.metrics(data, weights)
    return dict(weights=weights, net_sharpe=truth['net_sharpe'],
                breakeven_holding_days=truth['breakeven_holding_days'])


def test_json_parsing_and_invalid_values(scorer):
    import json
    answer = correct_answer()
    assert scorer.check_answer(json.dumps(answer), example()) == answer
    bad_values = [True, None, '1', float('inf'), float('-inf'), float('nan'), 10**1000]
    for value in bad_values:
        for field in ['net_sharpe', 'breakeven_holding_days']:
            assert scorer.check_answer(dict(answer, **{field: value}), example()) is None
    for raw in ['{', 'null', '[]', '{"net_sharpe":1,"net_sharpe":2}',
                json.dumps(answer)[:-1] + ',"net_sharpe":1}',
                json.dumps(answer).replace(str(answer['net_sharpe']), 'NaN')]:
        assert scorer.check_answer(raw, example()) is None
    for weights in [[], [[.25, -.25]], [[.25], [0., 0.]], [[.25, -.25, 0.], [0., 0.]],
                    [[.25, -.25], [0., 10**1000]], [[.25, -.25], [False, 0.]]]:
        assert scorer.check_answer(dict(answer, weights=weights), example()) is None


def test_execution_metadata_must_have_exact_types(scorer):
    answer = correct_answer()
    good = execution(answer)
    for flag in [0, 1, None, '', 'false', [], {}]:
        assert scorer.score_pair(dict(good, flagged=flag), good, example(), example()) == 0.
    for exit_code in [False, True, 0., '0', None]:
        assert scorer.score_pair(dict(good, exit_code=exit_code), good, example(), example()) == 0.
    for key in ['flagged', 'exit_code', 'answer']:
        bad = good.copy()
        del bad[key]
        assert scorer.score_pair(good, bad, example(), example()) == 0.


def test_reward_partial_credit_and_divergent_replay(scorer):
    answer = correct_answer()
    good = execution(answer)
    for error, expected in [(0., 1.), (.00005, 1.), (.00505, .125), (.01001, 0.)]:
        near = dict(answer, net_sharpe=answer['net_sharpe']*(1+error),
                    breakeven_holding_days=answer['breakeven_holding_days']*(1+error))
        assert scorer.score_pair(execution(near), execution(near), example(), example()) == pytest.approx(expected)
    replay_data = example()
    replay_data['returns'] = [[.2, -.2], [-.3, .3]]
    assert scorer.score_pair(good, good, example(), replay_data) == 0.
    for field in ['net_sharpe', 'breakeven_holding_days']:
        bad = dict(answer, **{field: answer[field]*1.02})
        assert scorer.score_pair(good, execution(bad), example(), example()) == 0.
        near = dict(answer, **{field: answer[field]*1.00505})
        assert 0. < scorer.score_pair(execution(near), good, example(), example()) < 1.
