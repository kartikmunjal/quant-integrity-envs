"""Independent prospective tests for the public E2 normative contract.

Authored before qi.mutate.contract implementation. These tests inspect public
instructions and host-generated public material, never execute submitted source.
They preserve the existing economic semantics rather than introduce new ones.
"""
import re
import pytest
from qi.mutate.contract import PUBLIC_RESEARCH_CONTRACT
from qi.mutate.cases import make_case


def compact():
    return re.sub(r'\s+', '', PUBLIC_RESEARCH_CONTRACT.lower()).replace('`','')


def test_public_contract_defines_fundamental_triples_and_partition_bounds():
    text=PUBLIC_RESEARCH_CONTRACT.lower()
    dense=compact()
    assert 'fundamentals' in text
    assert '[period_end,available_day,value]' in dense
    assert 'available_day' in text and 'period_end' in text
    assert '[train_start,train_end,select_end,eval_end]' in dense
    assert 'half-open' in text or 'half open' in text
    for interval in ('[train_start,train_end)', '[train_end,select_end)', '[select_end,eval_end)'):
        assert interval in dense


def test_public_contract_states_exact_fit_and_label_rules():
    dense=compact()
    assert 't+horizon<train_end' in dense
    assert 'training' in dense and 'purge' in dense
    assert 'lag' in dense
    assert any(form in dense for form in ('[1,3,7]','(1,3,7)','1/3/7'))
    assert 'available_day<=t' in dense or 'available_day<=day' in dense


def test_public_contract_defines_signal_fill_realization_and_selection_clocks():
    text=PUBLIC_RESEARCH_CONTRACT.lower()
    dense=compact()
    for word in ('signal','close','fill','realiz','selection'):
        assert word in text
    assert 't+1' in dense and 't+2' in dense
    # Require explicit temporal ordering rather than a vague "no lookahead".
    assert 'signalclose' in dense or 'signalatclose' in dense or 'signalformedatclose' in dense
    assert 'fillatcloseoft+1' in dense or 'fillatcloset+1' in dense or 'nextclose(t+1)' in dense
    assert 'realizedbeforeselect_end' in dense or 'realization<select_end' in dense
    assert 'day<select_end-2' in dense or 't<select_end-2' in dense


def test_public_contract_defines_listing_identity_and_missing_ticker_owner():
    text=PUBLIC_RESEARCH_CONTRACT.lower()
    dense=compact()
    assert 'listing_id' in text and 'stable' in text
    assert 'active[t]' in dense or 'active[day]' in dense
    assert 'ticker_owner' in text and '-1' in text
    assert 'missing' in text
    assert 'lastasset' in dense or 'lastlisting' in dense
    assert 'mustnot' in dense or 'never' in dense


def test_public_contract_names_every_required_output_and_evaluation_scope():
    text=PUBLIC_RESEARCH_CONTRACT
    required={'holdings','fill_prices','strategy_returns','returns','equity','turnover',
              'selected_strategy','net_mean','net_std','adjusted_p','training_label_mean','descriptive_mean'}
    assert all(name in text for name in required)
    dense=compact()
    assert 'evaluation' in dense
    assert 'bonferroni' in dense
    assert '3' in dense and 'trial' in dense
    assert 'strategy' in dense and 'selection' in dense


def test_public_contract_is_uniform_and_contains_no_instance_truth():
    assert isinstance(PUBLIC_RESEARCH_CONTRACT,str) and len(PUBLIC_RESEARCH_CONTRACT)>500
    lower=PUBLIC_RESEARCH_CONTRACT.lower()
    for forbidden in ('gold_patch','gold_span','oracle_manifest','effect_size','min_effect','true_bug','1000000','1000776'):
        assert forbidden not in lower
    from qi.mutate.catalogue import CATALOGUE
    assert all(m.id not in PUBLIC_RESEARCH_CONTRACT for m in CATALOGUE)
    for seed,tier in ((1000000,'T1'),(1000001,'T2'),(1000002,'T3'),(1000000,'T4')):
        public=make_case(seed,tier)['public']
        assert public['contract']==PUBLIC_RESEARCH_CONTRACT
        assert not ({'seed','truth','mutations','effects','gold_patch'} & public.keys())
