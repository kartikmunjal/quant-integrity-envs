from scripts.run_p2b_gate import policies, independent_expected, independent_score
from envs.e1_pit_backtest.runtime import expected, public_input, score_pair


def test_gate_policies_and_independent_checker():
    all_policies, wrong, attacks = policies()
    assert len(wrong)>=10
    assert {'canary_read','oracle_read','harness_tamper','network_use','hardcoded'}<=attacks
    data=public_input(1_000_400,'T1')
    a=expected(data); b=independent_expected(data)
    assert all(abs(a[k]-b[k])<1e-12 for k in a)
    evidence={'answer':a,'flagged':False}
    assert independent_score(evidence,evidence,b,b)==score_pair(evidence,evidence,a,a)
