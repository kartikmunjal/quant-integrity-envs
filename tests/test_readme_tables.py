"""M0 documentation numbers must be regenerated from immutable evidence."""
from pathlib import Path
import pytest


def api():
    from scripts import reproduce_table
    return reproduce_table


def test_readme_is_exactly_reproduced():
    m=api()
    assert (m.ROOT/'README.md').read_text()==m.render_readme()


@pytest.mark.parametrize('old,new',[('1.000000','0.123456'),('8,200','8,201'),('0.225000','0.225001')])
def test_checker_rejects_changed_readme_number(old,new):
    m=api();text=m.render_readme()
    assert old in text
    with pytest.raises(ValueError):m.check_readme(text.replace(old,new,1))


def test_changed_source_value_invalidates_document(monkeypatch):
    m=api();expected=m.render_readme();original=m.read_json
    def altered(path):
        value=original(path)
        if str(path)=='results/p2b2_gate.json':value['tiers']['T1']['policies']['near_miss']['mean_reward']=.314159
        return value
    monkeypatch.setattr(m,'read_json',altered)
    with pytest.raises(ValueError):m.check_readme(expected)


def test_every_table_has_a_generator_and_no_unmanaged_table():
    m=api();text=m.render_readme()
    assert text.count('<!-- table:')==len(m.TABLES)
    for name in m.TABLES:
        assert m.render_table(name) in text
    assert sum(line.startswith('|---') for line in text.splitlines())==len(m.TABLES)


def test_curves_match_current_reward_definitions():
    m=api()
    from envs.e1_pit_backtest.reward import quality
    from envs.e5_cost_realism.reward import quality as q5
    from envs.e6_data_traps.reward import quality as q6,ANOMALY_EXPONENT
    original=m.read_json('results/p2d2_reward_sensitivity.json')['numeric_sensitivity']
    revised=m.read_json('results/p2d2_revision_sensitivity.json')
    assert revised['exponent']==ANOMALY_EXPONENT
    for row in original:
        e=row['relative_error'];q=quality({'x':1+e},{'x':1})
        assert row['both_executions']['E1_both_fields']==pytest.approx(.8*q*q+.2*q*q*q,abs=1e-12)
        assert row['both_executions']['E5_both_claims']==pytest.approx(q5(e)**3,abs=1e-12)
    for row in revised['numeric']:
        q=q6(row['relative_error'])
        assert row['paired_reward']==pytest.approx(q*(.6*q+.4),abs=1e-12)


def test_source_generator_hash_and_policy_population():
    m=api()
    for env,path in m.GATES.items():
        data=m.read_json(path)
        assert data['passed'] and data['generator_version_hash']==m.generator_hash()
        for tier in m.TIERS:
            p=data['tiers'][tier]['policies']
            assert all(p[n]['n']==50 for n in m.categories(env)[0]|m.categories(env)[1]|{'oracle','random','near_miss'})


def test_resume_bullets_are_generated_and_supported():
    m=api()
    assert (m.ROOT/'docs/resume_bullets.md').read_text()==m.render_resume()
    assert sum(line.startswith('- ') for line in m.render_resume().splitlines())==3


def test_no_em_dash_in_authored_documents():
    m=api()
    for name in ['README.md','docs/README.template.md','docs/MILESTONES.md','docs/resume_bullets.md','scripts/reproduce_table.py']:
        assert '\u2014' not in (m.ROOT/name).read_text()


def test_control_categories_match_frozen_policy_rosters():
    from scripts import e1_policies,e5_policies,e6_policies
    m=api()
    for env,module in [('E1',e1_policies),('E5',e5_policies),('E6',e6_policies)]:
        _,wrong,attacks=module.policies()
        assert m.categories(env)==(wrong,attacks)


def test_readme_local_links_exist():
    import re
    m=api()
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',m.render_readme()):
        if '://' not in target:
            assert (m.ROOT/target.split('#')[0]).exists(),target


def test_cli_table_is_read_only(monkeypatch,capsys):
    import sys
    m=api();before=(m.ROOT/'README.md').read_bytes()
    monkeypatch.setattr(sys,'argv',['reproduce_table.py','--table','e6'])
    m.main()
    assert capsys.readouterr().out.rstrip()==m.render_table('e6')
    assert (m.ROOT/'README.md').read_bytes()==before


def test_generator_followup_uses_amended_checks_not_legacy_case_flags():
    m=api();x=m.read_json('results/p1_followup_fresh_diagnostics.json')
    n=len(x['cases']);assert x['summary']['passed']
    assert x['summary']['pass_rates']['all_per_seed_checks']==1.
    assert sum(c['passed'] for c in x['cases'])<n  # Legacy flags use the original criterion.
    assert f'| Fresh amended-criterion cohort | {n} | {n} | 0 |' in m.generator()


def test_numeric_prose_parameters_match_configuration_and_recorded_band():
    import re
    import yaml
    from qi_runtime.infrastructure import RetryBudget
    m=api();text=m.render_readme();config=yaml.safe_load((m.ROOT/'prereg.yaml').read_text())
    w=config['reward']['weights']
    assert f"`{w['E1']['correctness']}*p*r + {w['E1']['availability_discipline']}*p*r*r`" in text
    assert f"`p*r*({w['E5']['net_sharpe']}*s + {w['E5']['breakeven_holding_period']}*h + {w['E5']['cost_awareness']}*r)`" in text
    assert f"`min(u,a)*({w['E6']['universe_reconciliation']}*u+{w['E6']['anomaly_f1']})`" in text
    low,high=re.search(r'full through relative error `([0-9.]+)`, zero from `([0-9.]+)`',text).groups()
    band=m.read_json('results/p2c_gate.json')['partial_credit_band']
    assert float(low)==config['reward']['numeric_tolerance_relative']==band['full_tolerance']
    assert float(high)==band['zero_scale']
    ceiling=float(re.search(r'at most ([0-9.]+)% retries',text).group(1))/100
    assert ceiling==RetryBudget(10000).max_retries/10000
    n=int(re.search(r'\*\*(\d+) episodes per policy\*\*',text).group(1))
    assert all(cell['n']==n for path in m.GATES.values() for t in m.read_json(path)['tiers'].values() for cell in t['policies'].values())


def test_at_a_glance_is_short_and_uses_recorded_headlines():
    m=api();text=m.render_readme();section=text.split('## At a glance\n',1)[1].split('\n\n',1)[0]
    assert len(('## At a glance\n'+section).splitlines())<=10
    gates=[m.read_json(p) for p in m.GATES.values()]
    total=sum(x.get('rollouts',x.get('planned')) for x in gates)
    exact=sum(m.read_json(f'results/p3a2-regression-{env.lower()}.json')['exact_matches'] for env in m.GATES)
    assert f'{total:,}' in section and f'{exact:,}' in section
    assert 'No model results' in section
    assert 'heavy-tail' in section and 'classification' in section
    assert text.index('## At a glance')<text.index('A synthetic testbed')


def test_changed_headline_source_invalidates_readme(monkeypatch):
    m=api();text=m.render_readme();original=m.read_json
    def altered(path):
        value=original(path)
        if str(path)=='results/p2b2_gate.json':value['rollouts']+=1
        return value
    monkeypatch.setattr(m,'read_json',altered)
    with pytest.raises(ValueError):m.check_readme(text)


@pytest.mark.parametrize('value,expected',[(0,0),([],0),([{'seed':'synthetic'}],1),(2,2)])
def test_difference_counts_do_not_render_raw_lists(value,expected):
    assert api().difference_count(value)==expected


def test_determinism_table_normalizes_empty_difference_records(monkeypatch):
    m=api();original=m.read_json
    def records(path):
        value=original(path)
        if 'p2d3-r2-determinism-' in str(path):value.update(reward_differences=[],replay_differences=[])
        return value
    monkeypatch.setattr(m,'read_json',records)
    output=m.determinism()
    assert '[]' not in output
    assert output.count('| 0 | 0 | PASS |')==3


def test_hosted_sandbox_plan_does_not_claim_implementation():
    text=api().render_readme().split('## Planned work\n',1)[1].split('\n## ',1)[0]
    assert 'A hosted-sandbox runtime backend is under consideration, not started, with unknown feasibility.' in text
