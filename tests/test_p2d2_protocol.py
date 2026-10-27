"""Round-two freeze and graded-policy evidence contracts."""
from scripts import run_p2d2_gate as gate
from scripts.e6_policies import policies,source_for

def test_round2_freeze_binds_design_study_amendment_and_cheaters():
    paths=gate.frozen_sources()
    for p in ('reports/P2d2_design.md','results/p2d2_design_study.json','results/p2d2_design_cheaters.json','AMENDMENTS.md'):
        assert p in paths

def test_all_k_sources_are_independent_programs():
    available,wrong,attacks=policies()
    assert len(available)==33 and len(wrong)>=10
    for k in range(7):
        source=source_for(f'find_{k}',1002000,'T3',available)
        compile(source,'policy','exec')
        assert "result['anomalies']=result['anomalies'][:"+str(k)+']' in source
        assert f'find_{k}' not in wrong|attacks
