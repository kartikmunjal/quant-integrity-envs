"""Prospective gate/evidence contracts; no fresh evaluations."""
import json
from pathlib import Path
from scripts import run_p2d_gate as gate
from scripts.e6_policies import policies,source_for

def test_freeze_binds_e6_design_and_runtime_schema():
    paths=gate.frozen_sources()
    assert 'reports/P2d_design.md' in paths
    assert 'envs/e6_data_traps/schema.json' in paths
    assert 'src/qi_runtime/__init__.py' in paths
    assert 'src/qi_data_traps/__init__.py' in paths


def test_complete_policy_sources_and_explicit_clean_diagnostic():
    allp,wrong,attacks=policies()
    assert {'flag_large_moves','ignore_identifiers','ignore_splits','ticker_only'}<=wrong
    assert len(wrong)>=10
    assert 'never_flag' not in wrong|attacks
    for name in allp:compile(source_for(name,1007000,'T4',allp),'policy','exec')


def test_fraction_uses_numeric_error_not_anomaly_quality():
    r=gate.fractions([{'reward':1.,'primary':{'errors':[0.,1.,1.]}}])
    assert r['primary_numeric_error_fractions']['within_full_tolerance']==1


def test_empty_diagnostics_report_missing_and_clean_false_flags_count():
    assert all(v is None for v in gate.minimum_gaps([]).values())
    assert gate.false_positive({'flagged':False,'primary':{'false_positive':True},'replay':{}})
