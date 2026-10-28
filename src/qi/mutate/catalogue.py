"""Prospectively fixed economic mutation catalogue (host-only labels)."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Mutation:
    id: str
    family: str
    target: str
    clean: str
    faulty: str
    witness: str
    min_effect: float = .05

CATALOGUE = (
    Mutation('future_feature','F1','feature_day','day-1','day+1','holdings'),
    Mutation('availability_bypass','F1','eligible','record[1] <= day','record[0] <= day','holdings'),
    Mutation('global_center','F2','center_end','train_end','len(returns)','holdings'),
    Mutation('global_scale','F2','scale_end','train_end','len(returns)','holdings'),
    Mutation('unpurged_labels','F3','fit_end','train_end-horizon','train_end','holdings'),
    Mutation('selection_overlap','F3','fit_stop','fit_end','select_end','holdings'),
    Mutation('survivor_filter','F4','member','active[day][asset]','active[-1][asset]','holdings'),
    Mutation('ticker_merge','F4','identity','asset','ticker_owner[asset]','holdings'),
    Mutation('same_bar','F5','signal_day','day','day+1','holdings'),
    Mutation('submission_fill','F5','fill_day','day+1','day','fill_prices'),
    Mutation('test_selection','F6','choose_stop','select_end','eval_end','returns'),
    Mutation('uncorrected_trials','F6','adjustment','len(paths)','1','adjusted_p'),
)
BY_ID = {m.id:m for m in CATALOGUE}


def witness_groups(mutation):
    if mutation.family in ('F1','F2','F3'):return ('holdings','strategy_returns')
    if mutation.family=='F4':return ('holdings','turnover','strategy_returns')
    if mutation.id=='same_bar':return ('holdings','strategy_returns')
    if mutation.id=='submission_fill':return ('fill_prices','strategy_returns')
    return (mutation.witness,)
