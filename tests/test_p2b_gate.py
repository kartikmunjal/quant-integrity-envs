from scripts.e1_policies import policies
from envs.e1_pit_backtest.checker import expected as independent_expected, score_pair as independent_score
from envs.e1_pit_backtest.runtime import expected, public_input, score_pair


def test_gate_policies_and_independent_checker():
    all_policies, wrong, attacks = policies()
    assert len(wrong)>=10
    assert {'canary_read','oracle_read','harness_tamper','network_use','hardcoded'}<=attacks
    data=public_input(1_001_000,'T1')
    a=expected(data); b=independent_expected(data)
    assert all(abs(a[k]-b[k])<1e-12 for k in a)
    evidence={'answer':a,'flagged':False,'exit_code':0}
    assert independent_score(evidence,evidence,b,b)==score_pair(evidence,evidence,a,a)


def test_replay_adversaries_are_full_source_policies_with_public_fingerprints():
    from scripts.e1_policies import source_for
    available,wrong,attacks=policies()
    for name in ('divergent_replay','malformed_replay','flagged_replay'):
        assert name in attacks
        source=source_for(name,1001000,'T1',available)
        assert '__PRIMARY_INPUT_SHA256__' not in source
        compile(source,'policy','exec')
        assert source==source_for(name,1001000,'T1',available)
