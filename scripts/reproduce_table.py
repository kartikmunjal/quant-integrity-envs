"""Render M1 documentation from recorded evidence; never run an experiment."""
from __future__ import annotations
import argparse
import json
import gzip
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

E2_GATE='results/p3a3-gate.json'
E2_CHEATERS=('constant','disabled','canary','oracle_read','harness','network','schema','primary_only')


def e2_gate():
    x=read_json(E2_GATE)
    if not x['passed'] or not x['complete'] or not x['statistics']['passed'] or not all(x['statistics']['criteria'].values()):
        raise ValueError('E2 validation requires a passing complete fresh gate')
    if not x['planned']==x['rows']==x['complete_rows']==x['infrastructure_ok_rows']:
        raise ValueError('E2 population is incomplete or inconsistent')
    if x['generator_version_hash']!=generator_hash():raise ValueError('E2 generator differs')
    return x


def e2_policies():
    x=e2_gate();groups=x['statistics']['per_policy_tier'];rows=[]
    for tier in TIERS:
        cells={k.split('/')[0]:v for k,v in groups.items() if k.endswith('/'+tier)}
        if any(v['count']!=(500 if k=='oracle' else 50) for k,v in cells.items()):raise ValueError('E2 cell population drift')
        wrong=[v['mean'] for k,v in cells.items() if k.startswith('wrong_')]
        rows.append([tier,fmt(cells['oracle']['mean']),fmt(cells['random']['mean']),fmt(max(wrong)),
                     fmt(max(cells[p]['mean'] for p in E2_CHEATERS)),fmt(cells['shallow']['mean'])])
    return table(['Tier','Oracle','Random','Worst wrong','Worst cheater','Shallow detector'],rows,[E2_GATE])


def e2_families(heldout=False):
    stats=e2_gate()['statistics'];families=stats['per_family'];reserved=stats['heldout_families']
    if any(families[k]!=v for k,v in reserved.items()):raise ValueError('held-out family summary mismatch')
    selected=reserved if heldout else {k:v for k,v in families.items() if k not in reserved}
    rows=[[k,v['count'],fmt(v['oracle_mean']),fmt(v['minimum_planted_effect'])] for k,v in sorted(selected.items())]
    return table(['Family','Oracle episodes involving family','Oracle mean','Minimum planted effect'],rows,[E2_GATE])


def mutation_footprint():
    x=read_json('results/p3a_mutation_design_v3.json');gate=e2_gate()
    if not x['passed'] or x['failures']:raise ValueError('mutation validation failed')
    for name,digest in x['sources'].items():
        if name.startswith('src/qi/mutate/') and gate['sources'][name]!=digest:raise ValueError('mutation source identity differs')
    rows=[json.loads(line) for shard in x['compact_shards'] for line in gzip.decompress((ROOT/shard['path']).read_bytes()).splitlines()]
    by_operator={}
    for row in rows:
        if not row['passed']:raise ValueError('mutation/decoy evidence failed')
        if row['operator'] is not None:by_operator.setdefault(row['operator'],set()).add(row['realization'])
    sets=list(by_operator.values())
    if not sets or any(v!=sets[0] for v in sets):raise ValueError('nonuniform realization coverage')
    return set(by_operator),sets[0]


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
    gates_=[read_json(p) for p in GATES.values()];e2=e2_gate()
    if not all(x['passed'] for x in gates_):raise ValueError('headline cannot claim failed gates as validated')
    tier_sets={tuple(sorted(x['tiers'])) for x in gates_}
    if len(tier_sets)!=1:raise ValueError('headline requires a common validated tier set')
    total=sum(x.get('rollouts',x.get('planned')) for x in gates_)
    regressions=[read_json(f'results/p3a2-regression-{env.lower()}.json') for env in GATES]
    if not all(x['passed'] and x['rows']==x['exact_matches'] for x in regressions):raise ValueError('headline requires exact recorded regressions')
    exact=sum(x['exact_matches'] for x in regressions)
    screen=read_json('results/p3a3_screen.json')['ranges']['design']
    return f'''## At a glance

- Synthetic quantitative research-integrity tasksets with deterministic verifiers.
- Validated locally: generator, checked runtime and E1/E5/E6 across **{len(next(iter(tier_sets)))} tiers**; **{count(total)}** scripted numerical-gate rollouts.
- Mutation engine and E2 validated on **{count(e2['rows'])}** screened synthetic gate rollouts; **{count(exact)}** exact E1/E5/E6 regression matches.
- History: first E2 gate failed on infrastructure classification; its fix preceded a heavy-tail admission failure. Construction-only screening rejected **{screen['rejected_count']} of {count(screen['count'])}** design seeds and excludes extreme-tail episodes.
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

TABLES={'e2':e2_policies,'e2_families':e2_families,'e2_heldout':lambda:e2_families(True),'e1':lambda:policies('E1'),'e5':lambda:policies('E5'),'e6':lambda:policies('E6'),'gates':gates,'e2_partial':partial,'e2_infrastructure':e2_infrastructure,'generator':generator,'curves':curves,'e6_detection':detection,'stress':stress,'determinism':determinism}
def render_table(name):return TABLES[name]()

def replacements():
    x=read_json('results/p3a2_final_audit.json');y=read_json('results/p1_followup_fresh_diagnostics.json');config=yaml.safe_load((ROOT/'prereg.yaml').read_text())
    e2=e2_gate();operators,realizations=mutation_footprint();screen=read_json('results/p3a3_screen.json')['ranges']['design']
    reviews=read_json('results/p3a3_author_review.json')
    return {'mutation_count':str(len(operators)),'realization_count':str(len(realizations)),'family_count':str(len(e2['statistics']['per_family'])),
     'e2_rows':count(e2['rows']),'e2_checker':fmt(e2['statistics']['second_checker_agreement']),'e2_fp':fmt(e2['statistics']['clean_oracle_false_positive_rate']),
     'e2_exponent':str(e2['statistics']['exponent']),'e2_false_flag':fmt(e2['statistics']['per_policy_tier']['false_flag/T4']['mean']),
     'e2_fresh_implementation':read_json('results/p3a3_freeze.json')['implementation_commit'],'e2_review_count':str(reviews['count']),
     'screen_rejected':str(screen['rejected_count']),'screen_count':count(screen['count']),
     'at_glance':at_a_glance(),'generator_hash':generator_hash(),'image_hash':read_json('results/p2b2_gate.json')['freeze']['image'],'runtime_hash':x['runtime_version_hash'],
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
    gates_=[read_json(p) for p in GATES.values()];e2=e2_gate()
    total=sum(x.get('rollouts',x.get('planned')) for x in gates_)+e2['rows']
    operators,realizations=mutation_footprint()
    batches=[read_json(f'results/p3a3-stress-c{c}.json') for c in (8,12)]
    if not all(x['passed'] for x in gates_+batches):raise ValueError('resume requires passing validation')
    regressions=[read_json(f'results/p3a2-regression-{e.lower()}.json') for e in GATES]
    if not all(x['passed'] and x['rows']==x['exact_matches'] for x in regressions):raise ValueError('resume requires zero reward differences')
    exact=sum(x['exact_matches'] for x in regressions)
    agreement=min([x['second_checker']['agreement'] for x in gates_]+[e2['statistics']['second_checker_agreement']])
    return f'''# Resume bullets: validated synthetic infrastructure only

- Built and locally validated {len(gates_)+1} synthetic quantitative-integrity tasksets across {len(TIERS)} tiers, completing {count(total)} scripted gate rollouts with second-checker agreement of {agreement:.0%}. Sources: `results/p2b2_gate.json`, `results/p2c_gate.json`, `results/p2d3-gate-E6-c12.json`, `results/p3a3-gate.json`.
- Implemented {len(operators)} mutation operators across {len(e2['statistics']['per_family'])} bug families in {len(realizations)} realizations each within one synthetic script template; validated E2 on {count(e2['rows'])} fresh scripted rollouts with oracle mean {e2['statistics']['per_policy_tier']['oracle/T1']['mean']:.1f} in every tier and clean-oracle false-positive rate {e2['statistics']['clean_oracle_false_positive_rate']:.0%}. Sources: `results/p3a_mutation_design_v3.json` and its compact shards, `results/p3a3-gate.json`.
- Validated checked Docker execution across {count(sum(x['complete_rows'] for x in batches))} screened E2 stress rollouts at concurrency {min(x['concurrency'] for x in batches)} and {max(x['concurrency'] for x in batches)}, recording {sum(x['retries'] for x in batches)} retries; verified {count(exact)} E1/E5/E6 rollouts re-run under the corrected runtime with zero reward differences. Sources: `results/p3a3-stress-c8.json`, `results/p3a3-stress-c12.json`, `results/p3a3_regression_reuse.json`.

These describe synthetic scripted local verifier validation, not model performance, training or real-market profitability. E2 excludes extreme-tail construction failures through a prospective construction-only screen (`results/p3a3_screen.json`); replay is predictable, execution is local Docker only, and the clean false-flag penalty is soft. All measurements use generator `{generator_hash()}`. Runtime/source identities remain in the named original results; E2 uses runtime `{e2['runtime_version_hash']}`.
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
