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
