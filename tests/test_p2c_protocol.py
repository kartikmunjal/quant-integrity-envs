"""Design-side checks of freezing, compact evidence and policy coverage."""
import json
import pytest
from scripts import run_p2c_gate as gate
from scripts.e5_policies import policies,source_for,WRONG
from envs.e5_cost_realism.cases import public_input
from envs.e5_cost_realism.finance import canonical_weights,metrics


def test_source_freeze_rejects_uncommitted_or_changed_source(tmp_path,monkeypatch):
    path=tmp_path/'freeze.json';path.write_text(json.dumps({'sources':{},'image':gate.IMAGE}))
    monkeypatch.setattr(gate,'FREEZE',path)
    with pytest.raises(RuntimeError):gate.verify_freeze()


def test_policies_include_physical_cost_errors_and_real_replay_sources():
    available,wrong,attacks=policies()
    assert len(wrong)>=10 and set(WRONG)==wrong
    for name,source in available.items():
        source=source_for(name,1004000,'T1',available)
        compile(source,'policy','exec')
        assert '__PRIMARY_INPUT_SHA256__' not in source
    assert {'divergent_replay','malformed_replay','flagged_replay'}<=attacks


def test_compact_weights_are_identified_without_committing_large_arrays():
    data=public_input(1004000,'T1');weights=canonical_weights(data);value=metrics(data,weights)
    raw={'answer':dict(weights=weights,net_sharpe=value['net_sharpe'],breakeven_holding_days=value['breakeven_holding_days']),
         'flagged':False,'exit_code':0,'container_id':'fixture','computed':value,'errors':[0.,0.,0.]}
    out=gate.summarize_stage(raw)
    assert out['answer']['weights_shape']==[48,8]
    assert len(out['answer']['weights_sha256'])==64
    assert 'weights' not in out['answer']
    assert raw['answer']['weights']==weights


def test_fraction_definitions_are_explicit():
    rows=[{'reward':1.,'primary':{'errors':[0.,0.,0.]}},
          {'reward':.125,'primary':{'errors':[.00505,.00505,0.]}},
          {'reward':0.,'primary':{'errors':None}}]
    result=gate.fractions(rows)
    assert result['full_reward']==pytest.approx(1/3)
    assert result['partial_reward']==pytest.approx(1/3)
    assert result['primary_numeric_error_fractions']['in_partial_band']==pytest.approx(1/3)


def test_oracle_gate_checks_extra_checker_episodes_too():
    limits={'oracle_policy_min_mean_reward':.95,'clean_episode_false_positive_ceiling':.02}
    rows=[{'reward':1.,'flagged':False} for _ in range(50)]+[{'reward':0.,'flagged':True} for _ in range(450)]
    result=gate.oracle_checks(rows,limits)
    assert not result['mean_passed']
    assert not result['false_positive_passed']


def test_empty_case_diagnostics_produce_missing_values_instead_of_crashing():
    assert all(value is None for value in gate.minimum_gaps([]).values())


def test_compact_stage_keeps_source_and_audit_provenance():
    record={'answer':None,'source_sha256':'a'*64,'commands':[{'exit_code':0,'trace_sha256':'b'*64}]}
    out=gate.summarize_stage(record)
    assert out['source_sha256']==record['source_sha256']
    assert out['commands']==record['commands']
