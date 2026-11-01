"""Prospective locked pilot and fake-price projection contracts, no live calls."""
from decimal import Decimal
import socket

import pytest


def test_pilot_stays_locked_even_with_confirmation_before_key_or_socket(monkeypatch):
    from scripts import run_pilot
    def forbidden(*args,**kwargs): raise AssertionError('locked pilot accessed key/network')
    monkeypatch.setattr(socket,'socket',forbidden)
    monkeypatch.setattr(run_pilot,'read_key',forbidden)
    with pytest.raises(RuntimeError,match='P5a|locked|disabled'):
        run_pilot.main(['--model','fake','--confirm-spend'])


def test_pilot_rejects_spend_cap_override_without_any_call():
    from scripts import run_pilot
    with pytest.raises((SystemExit,ValueError,RuntimeError)):
        run_pilot.main(['--model','fake','--spend-cap','999999','--confirm-spend'])


def observations(api_costs=(10,10),open_costs=(10,10)):
    result={}
    for kind,costs,category in [('api',api_costs,'api'),('open',open_costs,'gpu')]:
        for index,tokens in enumerate(costs):
            result[kind+str(index)]={'input_tokens':tokens,'output_tokens':0,'episodes':1,
                                     'kind':kind,'category':category}
    return result


def prices(models,input_price='1000000',output_price='1000000'):
    from qi_harness.budget import PriceBook
    return PriceBook({name:{'input_per_million':input_price,'output_per_million':output_price}
                      for name in models})


def test_projection_uses_observed_token_means_and_does_not_invent_training_cost():
    from qi_harness.pilot import project_cost
    observed=observations()
    for row in observed.values(): row.update(input_tokens=100,output_tokens=50,episodes=2)
    result=project_cost(observed,prices(observed,'.10','.20'),episodes_per_model=10)
    assert float(result['baseline_api_usd'])==pytest.approx(.0002)
    assert float(result['baseline_gpu_usd'])==pytest.approx(.0002)
    assert result['training_gpu_usd'] is None
    assert result['training_projection_available'] is False
    assert set(result['selected_models'])==set(observed)


def test_projection_drops_costliest_removable_models_before_training_seeds():
    from qi_harness.pilot import project_cost
    observed=observations((80,50,20,10),(5,5))
    result=project_cost(observed,prices(observed),episodes_per_model=1)
    assert 'api0' not in result['selected_models']
    assert sum(name.startswith('api') for name in result['selected_models'])>=2
    assert sum(name.startswith('open') for name in result['selected_models'])>=2
    assert result['training_seeds']==3 and result['affordable']
    assert result['fallbacks'][0]=='fewer_baseline_models'


def test_training_seed_fallback_requires_measured_gpu_cost_and_preserves_floors():
    from qi_harness.pilot import project_cost
    observed=observations()
    result=project_cost(observed,prices(observed),episodes_per_model=1,training_seeds=3,
                        training_gpu_per_seed=Decimal('60'))
    assert set(result['selected_models'])==set(observed)
    assert result['training_seeds']==2
    assert float(result['training_gpu_usd'])==120
    assert result['training_projection_available'] and result['affordable']
    assert 'fewer_training_seeds' in result['fallbacks']


def test_api_over_cap_cannot_be_repaired_by_fewer_training_seeds():
    from qi_harness.pilot import project_cost
    observed=observations((100,100),(1,1))
    result=project_cost(observed,prices(observed),episodes_per_model=1)
    assert not result['affordable']
    assert result['training_seeds']==3 and result['training_gpu_usd'] is None
    assert set(result['selected_models'])==set(observed)


def test_missing_price_and_zero_observations_do_not_yield_fabricated_projection():
    from qi_harness.pilot import project_cost
    from qi_harness.budget import PriceBook
    observed=observations()
    with pytest.raises(ValueError): project_cost(observed,PriceBook({}),episodes_per_model=1)
    observed['api0']['episodes']=0
    with pytest.raises(ValueError): project_cost(observed,prices(observed),episodes_per_model=1)


def test_pilot_record_summary_keeps_zero_episodes_and_exact_cost_totals():
    from qi_harness.pilot import summarize_records
    records=[
        {'environment':'E1','tier':'T1','reward':1.,'cost_usd':'.01',
         'harness':{'turns':2,'input_tokens':10,'output_tokens':5,
                    'hack_monitors':{'canary_reads':0,'tamper_flags':False}}},
        {'environment':'E1','tier':'T1','reward':.5,'cost_usd':'.02',
         'harness':{'turns':4,'input_tokens':20,'output_tokens':5,
                    'hack_monitors':{'canary_reads':2,'tamper_flags':True}}},
        {'environment':'E1','tier':'T1','reward':0.,'cost_usd':'0',
         'harness':{'turns':0,'input_tokens':0,'output_tokens':0,'hack_monitors':{}}},
        {'environment':'E5','tier':'T4','reward':0.,'cost_usd':'.04',
         'harness':{'turns':3,'input_tokens':7,'output_tokens':2,
                    'hack_monitors':{'reexecution_failures':1}}},
    ]
    output=summarize_records(records)
    cells={(cell['environment'],cell['tier']):cell for cell in output['cells']}
    assert set(cells)=={('E1','T1'),('E5','T4')}
    first=cells['E1','T1']
    assert first['episodes']==3 and first['mean_reward']==pytest.approx(.5)
    assert first['reward_density']==pytest.approx(2/3)
    assert first['mean_turns']==2
    assert (first['input_tokens'],first['output_tokens'],first['total_tokens'])==(30,10,40)
    assert float(first['cost_usd'])==pytest.approx(.03)
    assert first['hack_monitors']['canary_reads']==2
    assert first['hack_monitors']['tamper_flags']==1
    assert cells['E5','T4']['episodes']==1 and cells['E5','T4']['reward_density']==0
    assert cells['E5','T4']['hack_monitors']['reexecution_failures']==1


def test_fake_pilot_summary_table_renderer_never_requires_real_pilot_artifacts():
    from qi_harness.pilot import summarize_records,render_pilot_table
    value=summarize_records([{'environment':'E2','tier':'T3','reward':0.,'cost_usd':'0',
                             'harness':{'turns':1,'input_tokens':2,'output_tokens':3,'hack_monitors':{}}}])
    table=render_pilot_table(value)
    assert isinstance(table,str) and 'E2' in table and 'T3' in table
    assert 'density' in table.lower() and 'reward' in table.lower()
