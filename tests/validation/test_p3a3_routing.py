"""Prospective list routing and fixed stress population tests."""
import pytest
from scripts import run_p3a3 as run


def test_screened_stress_preserves_policy_mix(monkeypatch):
    monkeypatch.setattr(run,'populations',lambda:{'design':[1000000,1000002],'primary':list(range(1003000,1003500)),'replay':[1004000,1004002]})
    plan=run.stress_plan()
    assert len(plan)==5000
    assert {s for _,_,s in plan}=={1000000,1000002}
    assert sum(p in ('harness','network','canary') for p,_,_ in plan)>=2500
    assert {t for _,t,_ in plan}==set(run.TIERS)


def test_routing_is_scoped_and_list_only(monkeypatch):
    monkeypatch.setattr(run,'populations',lambda:{'design':[1000000,1000002],'primary':[1003000,1003500],'replay':[1004000,1004002]})
    old_guard=run.e2.guard;old_replay=run.e2.replay_seed;old_design=run.e2.design_replay_seed
    with run.fresh_context():
        with pytest.raises(ValueError):run.e2.guard(1003000)
        token=run.e2.FRESH_AUTHORIZED.set(True)
        try:
            run.e2.guard(1003500)
            with pytest.raises(ValueError):run.e2.guard(1003001)
            assert run.e2.replay_seed(1003500,'T2','patch') in (1004000,1004002)
            assert run.e2.design_replay_seed(1000000,'T1','patch') in (1000000,1000002)
        finally:run.e2.FRESH_AUTHORIZED.reset(token)
    assert (run.e2.guard,run.e2.replay_seed,run.e2.design_replay_seed)==(old_guard,old_replay,old_design)


def test_fixed_review_matches_gate_population(monkeypatch):
    monkeypatch.setattr(run,'populations',lambda:{'primary':[1003000+2*i for i in range(500)]})
    rows=run.review_plan()
    assert len(rows)==len(set(rows))==50
    assert all(s in range(1003000,1004000,2) for _,_,s in rows)


def test_design_replay_always_distinct(monkeypatch):
    seeds=[1000000,1000002]
    monkeypatch.setattr(run,'populations',lambda:{'design':seeds,'primary':[1003000],'replay':[1004000]})
    with run.fresh_context():
        assert all(run.e2.design_replay_seed(s,'T1',str(p))!=s for s in seeds for p in range(20))
