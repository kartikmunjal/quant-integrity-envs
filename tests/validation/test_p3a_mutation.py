"""Tests first: semantic mutation contracts from SPEC and prospective design.

Trusted structured reference calls only; generated source must be executed by
separate CheckedRuntime mutation-kill exercise, never by these host tests.
"""
import ast
from collections import Counter
import pytest
from qi.mutate.catalogue import CATALOGUE
from qi.mutate.cases import make_case
from qi.mutate.reference import evaluate
from qi.mutate.render import render_source, source_locations


def shape(source):
    tree=ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node,ast.Name): node.id='identifier'
        if isinstance(node,ast.arg): node.arg='argument'
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)): node.name='function'
    return ast.dump(tree,include_attributes=False)


def numeric_leaves(value):
    if isinstance(value,dict):
        return [x for key in sorted(value) for x in numeric_leaves(value[key])]
    if isinstance(value,(tuple,list)):
        return [x for item in value for x in numeric_leaves(item)]
    if isinstance(value,(int,float)) and not isinstance(value,bool): return [float(value)]
    return []


def relative_change(a,b):
    aa,bb=numeric_leaves(a),numeric_leaves(b)
    assert len(aa)==len(bb)
    return max((abs(x-y) for x,y in zip(aa,bb)), default=0)/max(1e-8,max(map(abs,aa),default=0))


def test_twelve_operators_two_per_family_and_prospective_effect_floor():
    assert len(CATALOGUE)==12
    assert len({m.id for m in CATALOGUE})==12
    assert Counter(m.family for m in CATALOGUE)=={f'F{i}':2 for i in range(1,7)}
    assert all(m.min_effect==.05 for m in CATALOGUE)


@pytest.mark.parametrize('operator',CATALOGUE,ids=lambda m:m.id)
def test_operator_has_three_actual_ast_realizations_and_no_labels(operator):
    sources=[render_source(mutations=(operator.id,),realization=r,presentation_seed=1000000,decoys=True) for r in range(3)]
    assert len({shape(s) for s in sources})==3
    for s in sources:
        assert operator.id not in s
        assert 'bug_enabled' not in s
        assert not any(f'"F{i}"' in s or f"'F{i}'" in s for i in range(1,7))
        locations=source_locations(s)
        assert operator.id in locations


@pytest.mark.parametrize('tier,n',[('T1',1),('T2',1),('T3',3),('T4',0)])
def test_tier_contract_determinism_and_nonconstant_reference(tier,n):
    case=make_case(1000000,tier)
    assert case==make_case(1000000,tier)
    assert len(case['mutations'])==len(case['truth'])==n
    assert len({t['family'] for t in case['truth']})==n
    clean=evaluate(case['data'])
    for key in ('holdings','returns'):
        values=numeric_leaves(clean[key])
        assert len(set(values))>1
        assert max(map(abs,values))>1e-8
    assert isinstance(case['source'],str) and isinstance(case['clean_source'],str)
    for t in case['truth']:
        assert t['line']>0 and t.get('end_line',t['line'])>=t['line']


@pytest.mark.parametrize('family',['F3','F4','F6'])
def test_lofo_excludes_mutations_and_family_cued_decoys(family):
    for tier in ('T1','T2','T3','T4'):
        case=make_case(1000001,tier,excluded_families=(family,))
        assert all(t['family'] != family for t in case['truth'])
        assert family not in case['decoy_families']
        assert all(next(m.family for m in CATALOGUE if m.id==ident)!=family for ident in case['mutations'])


def test_presentations_are_semantic_not_public_truth():
    sources=[render_source(presentation_seed=s,decoys=True) for s in (1000000,1000001,1000002)]
    assert len(set(sources))==3
    assert all('1000000' not in s and 'true_bug' not in s and 'oracle_manifest' not in s for s in sources)


def test_mutant_economic_kill_and_gold_restore_trusted_path():
    # Actual source execution across 50x12x3 belongs to the design-runtime gate;
    # this smaller test separately rejects a reference implementation that makes
    # all mutations diagnostic-only or returns a constant economic path.
    case=make_case(1000002,'T4')
    clean=evaluate(case['data'])
    for m in CATALOGUE:
        mutant=evaluate(case['data'],mutations=(m.id,))
        assert mutant != clean, m.id
        assert evaluate(case['data'],mutations=())==clean


def test_f5_scheduler_moves_preformed_signals_and_keeps_fill_prices():
    data=make_case(1000000,'T4')['data']
    clean=evaluate(data)
    early=evaluate(data,('same_bar',))
    assert early['fill_prices']==clean['fill_prices']
    # Advance existing signals by one bar: the feature fit itself is identical.
    for actual,expected in zip(early['holdings'],clean['holdings']):
        assert actual[:-1]==expected[1:]
    alternate_fill=evaluate(data,('submission_fill',))
    assert alternate_fill['holdings']==clean['holdings']
    assert alternate_fill['fill_prices']!=clean['fill_prices']


def test_clean_selection_does_not_see_evaluation_or_unrealized_boundary_returns():
    import copy
    data=make_case(1000000,'T4')['data']
    baseline=evaluate(data)
    altered=copy.deepcopy(data)
    start=data['bounds'][2]
    for t in range(start,len(data['prices'])):
        altered['prices'][t]=[p*(2 if i%2 else .1) for i,p in enumerate(data['prices'][t])]
        altered['returns'][t]=[.5 if i%2 else -.4 for i in range(len(data['returns'][t]))]
    assert evaluate(altered)['selected_strategy']==baseline['selected_strategy']


def test_economic_witnesses_contain_only_evaluation_sessions():
    data=make_case(1000000,'T4')['data']
    output=evaluate(data)
    count=data['bounds'][3]-data['bounds'][2]
    for key in ('holdings','fill_prices','strategy_returns','turnover'):
        assert len(output[key])==3
        assert all(len(path)==count for path in output[key])
    assert len(output['returns'])==len(output['equity'])==count


def test_decoy_exclusion_changes_actual_source_assignments():
    from qi.mutate.render import canonical_function
    def assigned(source,name):
        fn=canonical_function(source)
        return next(n.value for n in ast.walk(fn) if isinstance(n,ast.Assign)
                    and isinstance(n.targets[0],ast.Name) and n.targets[0].id==name)
    clean=render_source(decoys=True)
    no_labels=render_source(decoys=('F2',))
    no_moments=render_source(decoys=('F1',))
    # Removed decoys must use alternate live computations, never constants.
    original_labels=assigned(clean,'labels')
    alternative_labels=assigned(no_labels,'labels')
    original_moment=assigned(clean,'descriptive')
    alternative_moment=assigned(no_moments,'descriptive')
    assert ast.dump(original_labels,include_attributes=False) != ast.dump(alternative_labels,include_attributes=False)
    assert ast.dump(original_moment,include_attributes=False) != ast.dump(alternative_moment,include_attributes=False)
    assert not isinstance(alternative_labels,ast.Constant)
    assert not isinstance(alternative_moment,ast.Constant)
    assert shape(clean)!=shape(no_labels)!=shape(no_moments)


@pytest.mark.parametrize('realization',[0,1,2])
def test_normalization_locations_exact_for_all_mutant_and_clean_forms(realization):
    from qi.mutate.render import audit
    assert source_locations(render_source(realization=realization))=={}
    for seed in (1000000,1000001):
        for operator in CATALOGUE:
            source=render_source((operator.id,),realization,seed)
            locations=source_locations(source)
            assert set(locations)=={operator.id}
            assert audit(source)==[{'family':operator.family,'line':locations[operator.id][0]}]
            for start,end in locations.values():
                assert 1<=start<=end<=len(source.splitlines())


@pytest.mark.parametrize('seed',[1000000,1000001,1000002])
def test_decoy_report_variants_preserve_every_clean_and_mutant_output(seed):
    # All fields count, including legitimate diagnostic reports. Changing the
    # answer contract is not an admissible way to remove a suspicious surface.
    data=make_case(seed,'T4')['data']
    for mutations in [()]+[(m.id,) for m in CATALOGUE]:
        original=evaluate(dict(data,label_report=True,moment_report=True),mutations)
        for labels,moments in ((False,True),(True,False),(False,False)):
            alternate=evaluate(dict(data,label_report=labels,moment_report=moments),mutations)
            assert alternate==original, (seed,mutations,labels,moments)


def test_no_decoy_source_has_no_original_explicit_decoy_subtrees():
    from qi.mutate.render import canonical_function,normalized
    def decoy_value(source,name):
        fn=canonical_function(source)
        return next(n.value for n in ast.walk(fn) if isinstance(n,ast.Assign)
                    and isinstance(n.targets[0],ast.Name) and n.targets[0].id==name)
    on=render_source(decoys=True)
    off=render_source(decoys=False)
    off_tree=canonical_function(off)
    for name in ('labels','descriptive'):
        original=decoy_value(on,name)
        # The old expression must not survive in an unused hidden branch.
        if isinstance(original,ast.IfExp): original=original.body
        fingerprint=normalized(original)
        assert all(normalized(n)!=fingerprint for n in ast.walk(off_tree))


def test_fixed_seed_fallback_admits_only_effective_plants_and_preserves_rejections():
    """Prospective revision test, written before fallback implementation.

    The historical failed seed stays fixed. Inactive operators remain disclosed;
    they are never falsely counted as economic mutants or silently replanted.
    """
    from qi.mutate.cases import admitted_data
    data,clean,attempts=admitted_data(1000776)
    assert 1<=len(attempts)<=32
    selected=[a for a in attempts if a.get('selected')]
    assert len(selected)==1
    def eligible(a):
        return {ident for ident,groups in a.get('effect_groups',{}).items()
                if groups and all(value>=.05 for value in groups.values())}
    def rank(a):
        ids=eligible(a)
        return (len({m.family for m in CATALOGUE if m.id in ids}),len(ids),-a['candidate'])
    valid=[a for a in attempts if a.get('effect_groups')]
    assert selected[0]==max(valid,key=rank)
    assert selected[0]['candidate']<32
    assert any(a.get('rejected') for a in attempts)
    assert len({a['candidate'] for a in attempts})==len(attempts)
    assert all(0<=a['candidate']<32 for a in attempts)
    allowed=eligible(selected[0])
    rejected={m.id for m in CATALOGUE}-allowed
    assert rejected
    assert rejected <= set(selected[0]['rejected'])
    for tier in ('T1','T2','T3','T4'):
        case=make_case(1000776,tier)
        assert case==make_case(1000776,tier)
        assert case['seed']==1000776
        assert all(case['data'][key]==value for key,value in data.items())
        assert set(case['mutations'])<=allowed
        assert set(case['mutations']).isdisjoint(rejected)
        for truth in case['truth']:
            assert truth['effect']>=.05
        if tier=='T3':
            assert len(case['truth'])==3
            assert all(effect>=.05 for effect in case['conditional_effects'].values())
        assert case['candidate_attempts']==attempts
    for group in ('holdings','returns'):
        values=numeric_leaves(clean[group])
        assert len(set(values))>1 and max(map(abs,values))>1e-8
