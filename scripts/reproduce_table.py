"""Render M0 documentation from recorded evidence; never run an experiment."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
import yaml

ROOT=Path(__file__).resolve().parents[1]
TIERS=('T1','T2','T3','T4')
GATES={'E1':'results/p2b2_gate.json','E5':'results/p2c_gate.json','E6':'results/p2d3-gate-E6-c12.json'}
WRONG={
 'E1':set('ignore_availability ignore_period_cutoff ignore_restatements use_all_restatements ignore_active_universe equal_weights long_only percentage_units annualize_daily_return reverse_positions'.split()),
 'E5':set('ignore_costs gross_not_net ignore_spread ignore_impact half_turnover double_turnover positions_as_turnover omit_terminal_close full_spread linear_impact ignore_capacity renormalize_after_capacity'.split()),
 'E6':set('flag_large_moves ignore_identifiers ignore_splits ticker_only ignore_delistings reverse_split_adjustment drop_inactive flag_all raw_price_returns drop_identifier_history'.split())}

def read_json(path):
    return json.loads((ROOT/path).read_text())

def generator_hash():
    return read_json('results/p1_followup_fresh_diagnostics.json')['generator_version_hash']

def categories(env):
    legacy='legacy_schema' if env=='E6' else 'legacy_attestation'
    return WRONG[env],set(['hardcoded',legacy,'oracle_read','canary_read','harness_tamper','network_use','schema_forgery','divergent_replay','malformed_replay','flagged_replay'])

def fmt(value):return f'{value:.6f}'
def count(value):return f'{value:,}'
def status(value):return 'PASS' if value else 'FAIL'

def table(headers,rows,sources):
    text='| '+' | '.join(headers)+' |\n|'+ '|'.join('---' for _ in headers)+'|\n'
    text+='\n'.join('| '+' | '.join(map(str,row))+' |' for row in rows)
    return text+'\n\nSources: '+', '.join(f'[{Path(p).name}]({p})' for p in sources)+'.'

def policies(env):
    path=GATES[env];data=read_json(path);wrong,attacks=categories(env)
    near={'E1':['near_miss'],'E5':['near_miss','near_sharpe_only'],'E6':['near_miss','near_small','near_false_flag']}[env]
    rows=[]
    for tier in TIERS:
        p=data['tiers'][tier]['policies']
        if any(v['n']!=50 for v in p.values()):raise ValueError('policy-cell population changed')
        rows.append([tier,fmt(p['oracle']['mean_reward']),fmt(p['random']['mean_reward']),fmt(max(p[n]['mean_reward'] for n in wrong)),fmt(max(p[n]['mean_reward'] for n in attacks))]+[fmt(p[n]['mean_reward']) for n in near])
    return table(['Tier','Oracle','Random',f'Worst wrong ({len(wrong)} policies)',f'Worst cheater ({len(attacks)} policies)']+near,rows,[path])

def gates():
    rows=[]
    for env,path in GATES.items():
        x=read_json(path);c=x['second_checker'];p=x['tiers']['T4']['policies']['oracle']
        rows.append([env,count(x.get('rollouts',x.get('planned'))),count(c['real_comparisons']),fmt(c['agreement']),f"{p['flagged']} / {p['n']}",status(x['passed'])])
    return table(['Environment','Gate rollouts','Real checker comparisons','Agreement','Clean oracle flags (policy cell)','Gate'],rows,list(GATES.values()))

def partial():
    x=read_json('results/p3a-gate.json');s=x['sensitivity'][0];groups=s['per_policy_tier']
    for policy in ('oracle','random'):
        if len({(groups[policy+'/'+t]['mean'],groups[policy+'/'+t]['count']) for t in TIERS})!=1:raise ValueError('partial per-tier results no longer uniform; expand the table')
    worst=max(v['mean'] for k,v in groups.items() if k.startswith('wrong_') and v['mean'] is not None)
    wrong_cells=[v for k,v in groups.items() if k.startswith('wrong_')]
    wrong_count=len({k.split('/')[0] for k in groups if k.startswith('wrong_')})
    if len({v['count'] for v in wrong_cells})!=1:raise ValueError('wrong-policy counts no longer uniform')
    wrong_n=wrong_cells[0]['count'];clean_n=groups['oracle/T4']['count']
    rows=[['Planned rollouts',count(x['planned'])],['Completed rollouts',count(x['rows']-x['terminal'])],['Terminal failures',x['terminal']],['Unexecuted rollouts',count(x['planned']-x['rows'])],['Retries',x['retries']],['Scripted oracle mean reward',f"{fmt(groups['oracle/T1']['mean'])} in each tier; {groups['oracle/T1']['count']} completed per tier"],['Random mean reward',f"{fmt(groups['random/T1']['mean'])} in each tier; {groups['random/T1']['count']} completed per tier"],['Largest conceptual wrong-policy mean',f"{fmt(worst)}; all {wrong_count} policies completed {wrong_n} cases per tier"],['Clean oracle false-positive rate',f"{round(s['clean_oracle_false_positive_rate']*clean_n)} / {clean_n}"],['Independent scalar-checker agreement',f"{fmt(s['second_checker_agreement'])} on {count(x['rows']-x['terminal'])} completed records"]]
    return table(['Partial observation','Recorded result'],rows,['results/p3a-gate.json'])

def e2_infrastructure():
    paths=['results/p3a2-r2-stress-c8.json','results/p3a2-r2-stress-c12.json'];rows=[]
    for p in paths:
        x=read_json(p);rows.append([x['concurrency'],count(x['rows']),count(x['complete_rows']),x['rows']-x['complete_rows'],x['telemetry']['timeouts'],x['retries'],status(x['passed'])])
    return table(['Concurrency','Rows recorded','Complete','Admission failures','Host timeouts','Retries','Stress'],rows,paths)

def generator():
    paths=['results/p1_diagnostics.json','results/p1_addendum_diagnostics.json','results/p1_followup_fresh_diagnostics.json'];rows=[]
    for label,p in zip(['Initial diagnostic','Original per-seed screen','Fresh amended-criterion cohort'],paths):
        x=read_json(p);s=x['summary'];n=len(x['cases'])
        passed=sum(bool(c['passed']) for c in x['cases'])
        if 'aggregate_checks' in s:
            t=x['thresholds']
            passed=sum(c['excess_kurtosis']>=t['min_excess_kurtosis'] and c['absolute_return_autocorrelation']>=t['min_absolute_return_autocorrelation'] and c['ic_absolute_error']<=t['max_ic_absolute_error'] and c['top_three_eigenvalue_share']>=t['min_per_seed_top_three_eigenvalue_share'] for c in x['cases'])
            if passed/n!=s['pass_rates']['all_per_seed_checks']:raise ValueError('fresh diagnostic counts disagree with recorded summary')
            criterion=f"median factor share >= {t['min_median_top_three_eigenvalue_share']:.2f}; per-seed floor >= {t['min_per_seed_top_three_eigenvalue_share']:.2f}"
        else:criterion=f"per-seed factor share >= {x['thresholds']['min_top_three_eigenvalue_share']:.2f}"
        rows.append([label,n,passed,n-passed,criterion])
    return table(['Cohort','Dev seeds','Per-seed passes','Per-seed failures','Factor criterion'],rows,paths)

def curves():
    p='results/p2d2_reward_sensitivity.json';q='results/p2d2_revision_sensitivity.json';x=read_json(p)['numeric_sensitivity'];y=read_json(q)['numeric'];assert [r['relative_error'] for r in x]==[r['relative_error'] for r in y]
    rows=[[f"{r['relative_error']:.6f}",fmt(r['single_numeric_quality']),fmt(r['both_executions']['E1_both_fields']),fmt(r['both_executions']['E5_both_claims']),fmt(t['paired_reward'])] for r,t in zip(x,y)]
    return table(['Relative error','Single numeric quality','E1: both fields, both executions','E5: both claims, both executions','E6: numeric error, exact flags'],rows,[p,q])

def detection():
    p='results/p2d2_revision_sensitivity.json';x=read_json(p)
    rows=[[r['n'],r['k'],r['false_flags'],fmt(r['f1']),fmt(r['reward'])] for r in x['detection'] if (r['n']==6 and r['k'] in (0,1,3,5,6) and r['false_flags']==0) or (r['n']==0 and r['false_flags']<=2)]
    return table(['True anomalies','Found','False flags','F1','Reward with exact numeric output'],rows,[p])

def stress():
    rows=[];paths=[]
    for env in ('E1','E5','E6'):
        for concurrency in (12,24):
            p=f'results/p2d3-r2-stress-{env}-c{concurrency}.json';x=read_json(p);paths.append(p)
            rows.append([env,x['concurrency'],count(x['planned']),count(x['complete']),x['terminal_failures'],x['retry_count'],status(x['passed'])])
    return table(['Environment','Concurrency','Planned','Complete','Terminal failures','Retries','Stress'],rows,paths)

def difference_count(value):
    """Stored comparisons may contain a count or a list of differing records."""
    if isinstance(value,list):return len(value)
    if type(value) is int and value>=0:return value
    raise ValueError('difference evidence must be a nonnegative count or record list')


def at_a_glance():
    gates_=[read_json(p) for p in GATES.values()]
    if not all(x['passed'] for x in gates_):raise ValueError('headline cannot claim failed gates as validated')
    tier_sets={tuple(sorted(x['tiers'])) for x in gates_}
    if len(tier_sets)!=1:raise ValueError('headline requires a common validated tier set')
    total=sum(x.get('rollouts',x.get('planned')) for x in gates_)
    regressions=[read_json(f'results/p3a2-regression-{env.lower()}.json') for env in GATES]
    if not all(x['passed'] and x['rows']==x['exact_matches'] for x in regressions):raise ValueError('headline requires exact recorded regressions')
    exact=sum(x['exact_matches'] for x in regressions)
    return f'''## At a glance

- Synthetic quantitative research-integrity tasksets with deterministic verifiers.
- Validated locally: generator, checked runtime and E1/E5/E6 across **{len(next(iter(tier_sets)))} tiers**; **{count(total)}** scripted numerical-gate rollouts.
- Corrected-runtime regression: **{count(exact)}** exact reward matches.
- E2: the first gate failed on infrastructure classification; a fix is implemented, and a separate case-admission problem on heavy-tail seeds was found.
- Planned: E3, E4, model baselines, training and transfer studies.
- No model results are claimed.'''


def determinism():
    rows=[];paths=[]
    for env in ('E1','E5','E6'):
        p=f'results/p2d3-r2-determinism-{env}-c24.json';x=read_json(p);paths.append(p)
        rows.append(['Historical gate replay',env,count(x['complete']),difference_count(x['reward_differences']),difference_count(x['replay_differences']),status(x['passed'])])
    for env in ('E1','E5','E6'):
        p=f'results/p3a2-regression-{env.lower()}.json';x=read_json(p);paths.append(p)
        rows.append(['Corrected shared runtime',env,count(x['rows']),x['rows']-x['exact_matches'],'see independent audit',status(x['passed'])])
    return table(['Cohort','Environment','Rows','Reward differences','Replay-seed differences','Regression'],rows,paths)

TABLES={'e1':lambda:policies('E1'),'e5':lambda:policies('E5'),'e6':lambda:policies('E6'),'gates':gates,'e2_partial':partial,'e2_infrastructure':e2_infrastructure,'generator':generator,'curves':curves,'e6_detection':detection,'stress':stress,'determinism':determinism}
def render_table(name):return TABLES[name]()

def replacements():
    x=read_json('results/p3a2_final_audit.json');y=read_json('results/p1_followup_fresh_diagnostics.json');config=yaml.safe_load((ROOT/'prereg.yaml').read_text())
    return {'at_glance':at_a_glance(),'generator_hash':generator_hash(),'image_hash':read_json('results/p2b2_gate.json')['freeze']['image'],'runtime_hash':x['runtime_version_hash'],
     'numeric_runtime_hash':read_json('results/p2d3-gate-E6-c12.json')['runtime_version_hash'],
     'e2_implementation':x['implementation_commit'],'first_e2_implementation':read_json('results/p3a_freeze.json')['implementation_commit'],
     'generator_tail':fmt(y['summary']['maximum_single_day_absolute_return']),
     'ranges':f"{config['generator']['n_assets'][0]} to {config['generator']['n_assets'][1]} assets and {config['generator']['n_days'][0]} to {config['generator']['n_days'][1]} sessions",
     'versions':f"Python `{__import__('tomllib').loads((ROOT/'pyproject.toml').read_text())['project']['requires-python']}`; `"+next(d for d in __import__('tomllib').loads((ROOT/'pyproject.toml').read_text())['project']['dependencies'] if d.startswith('verifiers=='))+'`, pinned in [uv.lock](uv.lock).'}

def render_readme():
    text=(ROOT/'docs/README.template.md').read_text()
    for name in TABLES:text=text.replace('{{table:'+name+'}}',f'<!-- table:{name} -->\n'+render_table(name)+f'\n<!-- /table:{name} -->')
    for name,value in replacements().items():text=text.replace('{{'+name+'}}',value)
    if re.search(r'{{[A-Za-z_][^}]*}}',text):raise ValueError('unexpanded README token')
    if '\u2014' in text:raise ValueError('em dash forbidden')
    return text

def check_readme(text=None):
    if text is None:text=(ROOT/'README.md').read_text()
    if text!=render_readme():raise ValueError('README differs from evidence-backed rendering; run --write')

def render_resume():
    gates_=[read_json(p) for p in GATES.values()];total=sum(x.get('rollouts',x.get('planned')) for x in gates_)
    batches=[read_json(f'results/p2d3-r2-stress-{env}-c{c}.json') for env in ('E1','E5','E6') for c in (12,24)]
    exact_values=[read_json(f'results/p3a2-regression-{e.lower()}.json')['exact_matches'] for e in ('E1','E5','E6')]
    if len(set(exact_values))!=1:raise ValueError('regression cohorts differ; do not average per-taskset counts')
    exact=sum(exact_values)
    assert all(x['passed'] for x in gates_+batches)
    return f'''# Resume bullets: validated synthetic infrastructure only

- Built and locally validated {len(gates_)} synthetic quantitative-integrity tasksets across {len(TIERS)} tiers, completing {count(total)} scripted numerical-gate rollouts with independent checker agreement of {min(x['second_checker']['agreement'] for x in gates_):.0%}. Sources: `results/p2b2_gate.json`, `results/p2c_gate.json`, `results/p2d3-gate-E6-c12.json`.
- Validated checked Docker execution across {count(sum(x['complete'] for x in batches))} E1/E5/E6 stress rollouts at concurrency {min(x['concurrency'] for x in batches)} and {max(x['concurrency'] for x in batches)}, retaining every planned row and recording {sum(x['retry_count'] for x in batches)} retries. Sources: `results/p2d3-r2-stress-{{E1,E5,E6}}-c{{12,24}}.json`.
- Verified exact reward preservation on {count(exact)} stratified historical rows after shared-runtime infrastructure corrections, with {count(exact//len(gates_))} comparisons per taskset. Sources: `results/p3a2-regression-e1.json`, `results/p3a2-regression-e5.json`, `results/p3a2-regression-e6.json`.

These describe scripted local validation, not model performance, training or real-market profitability. Mutation-engine/E2 validation remains blocked and is not claimed as completed. All measurements use generator `{generator_hash()}`. Gate and original stress runtime provenance is in each named result; corrected-runtime regressions use `{read_json('results/p3a2_final_audit.json')['runtime_version_hash']}`.
'''

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--table',choices=TABLES);p.add_argument('--check',action='store_true');p.add_argument('--write',action='store_true');a=p.parse_args()
    if a.table:print(render_table(a.table));return
    if a.write:
        (ROOT/'README.md').write_text(render_readme());(ROOT/'docs/resume_bullets.md').write_text(render_resume())
    if a.check:
        check_readme()
        if (ROOT/'docs/resume_bullets.md').read_text()!=render_resume():raise ValueError('resume bullets differ from recorded results')
        print('PASS: README and resume bullets match recorded evidence')
    elif not a.write:print(render_readme(),end='')
if __name__=='__main__':main()
