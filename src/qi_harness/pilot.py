"""Observed-token projections with frozen model/seed floors, no experiment calls."""
from decimal import Decimal
from pathlib import Path
import yaml


def project_cost(observations,prices,*,episodes_per_model,training_seeds=3,training_gpu_per_seed=None,prereg_path=Path('prereg.yaml')):
    if type(episodes_per_model) is not int or episodes_per_model<=0:raise ValueError('positive planned episode count required')
    if type(training_seeds) is not int or training_seeds<=0:raise ValueError('positive training seed count required')
    config=yaml.safe_load(Path(prereg_path).read_text());budgets=config['budgets'];floor=config['baselines']
    minimum={'api':floor['min_api_models'],'open':floor['min_open_models']}
    minimum_seeds=config['statistics']['min_training_seeds']
    if training_seeds<minimum_seeds:raise ValueError('training seeds below frozen floor')
    costs={};kinds={};categories={}
    for model,row in observations.items():
        n=row['episodes']
        if type(n) is not int or n<=0:raise ValueError('nonempty observed episodes required')
        if row['kind'] not in minimum or row['category'] not in ('api','gpu'):raise ValueError('invalid observed model category')
        costs[model]=prices.cost(model,row['input_tokens'],row['output_tokens'])/n*episodes_per_model
        kinds[model]=row['kind'];categories[model]=row['category']
    if any(sum(k==kind for k in kinds.values())<n for kind,n in minimum.items()):raise ValueError('model roster below frozen floors')
    per_seed=None if training_gpu_per_seed is None else Decimal(str(training_gpu_per_seed))
    if per_seed is not None and (not per_seed.is_finite() or per_seed<0):raise ValueError('invalid measured GPU per-seed cost')
    selected=list(observations);fallbacks=[];seeds=training_seeds
    limits={k:Decimal(str(budgets[k+'_usd_cap']))*Decimal(str(budgets['stop_and_report_at_fraction'])) for k in ('api','gpu','total')}
    def sums():
        api=sum((costs[m] for m in selected if categories[m]=='api'),Decimal(0))
        gpu=sum((costs[m] for m in selected if categories[m]=='gpu'),Decimal(0))
        train=None if per_seed is None else per_seed*seeds
        total=api+gpu+(train or 0)
        affordable=api<limits['api'] and gpu+(train or 0)<limits['gpu'] and total<limits['total']
        return api,gpu,train,total,affordable
    while not sums()[-1]:
        removable=[m for m in selected if sum(kinds[x]==kinds[m] for x in selected)>minimum[kinds[m]]]
        if not removable:break
        chosen=max(removable,key=lambda m:(costs[m],m));selected.remove(chosen)
        if not fallbacks:fallbacks.append('fewer_baseline_models')
    while not sums()[-1] and per_seed is not None and per_seed>0 and seeds>minimum_seeds:
        seeds-=1
        if 'fewer_training_seeds' not in fallbacks:fallbacks.append('fewer_training_seeds')
    api,gpu,train,total,affordable=sums()
    return {'baseline_api_usd':api,'baseline_gpu_usd':gpu,'training_gpu_usd':train,'total_usd':total,
            'selected_models':selected,'training_seeds':seeds,'affordable':affordable,'fallbacks':fallbacks,
            'training_projection_available':per_seed is not None,'episodes_per_model':episodes_per_model,
            'scope':'baseline costs from observed tokens; separate training estimate only when supplied; 80 percent stopping bounds'}


def render_pilot_table(result):
    lines=['| Environment | Tier | Episodes | Mean reward | Reward density | Mean turns | Tokens | Cost USD |',
           '|---|---|---|---|---|---|---|---|']
    for row in result.get('cells',[]):
        fields=[row[key] for key in ('environment','tier','episodes','mean_reward','reward_density','mean_turns','total_tokens','cost_usd')]
        lines.append('| '+' | '.join(map(str,fields))+' |')
    return '\n'.join(lines)+'\n'
