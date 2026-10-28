"""Trusted numerical reference; source is rendered without fault switches.

Only structured catalogue choices reach this host function. Submitted source is
never imported, evaluated or executed here.
"""
import math
from .catalogue import BY_ID


def forward_label(rows,t,horizon,asset):
    return sum(rows[u][asset] for u in range(t+1,t+horizon+1))


def training_report(rows,start,stop,horizon):
    labels=[]
    for timestamp in range(start,stop-horizon):
        labels.append(forward_label(rows,timestamp,horizon,0))
    return labels


def moment_report(rows):
    return sum(map(lambda row:row[0],rows))/len(rows)


def research(data, faults=()):
    returns = data['returns']
    prices = data['prices']
    active = data['active']
    ticker_owner = data['ticker_owner']
    train_start, train_end, select_end, eval_end = data['bounds']
    horizon = data['horizon']
    n = len(returns[0])
    center_end = len(returns) if 'global_center' in faults else train_end
    scale_end = len(returns) if 'global_scale' in faults else train_end
    centers = [sum(returns[t][a] for t in range(train_start, center_end))/(center_end-train_start) for a in range(n)]
    scales = [max(1e-8, (sum((returns[t][a]-centers[a])**2 for t in range(train_start, scale_end))/(scale_end-train_start))**.5) for a in range(n)]
    fit_end = train_end if 'unpurged_labels' in faults else train_end-horizon
    fit_stop = select_end if 'selection_overlap' in faults else fit_end
    coefficients = []
    for lag in (1, 3, 7):
        numerator, denominator = 0., 1e-8
        for t in range(train_start+7, fit_stop):
            for a in range(n):
                feature = (returns[t-lag][a]-centers[a])/scales[a]
                label = forward_label(returns,t,horizon,a)
                numerator += feature*label
                denominator += feature*feature
        coefficients.append(numerator/denominator)
    # These are legitimate forward-looking labels used only in purged training.
    labels = [sum(returns[u][0] for u in range(t+1,t+horizon+1)) for t in range(train_start,train_end-horizon)] if data.get('label_report', True) else training_report(returns,train_start,train_end,horizon)
    # Full-history moments are descriptive reporting, never fitted features.
    descriptive = sum(row[0] for row in returns)/len(returns) if data.get('moment_report', True) else moment_report(returns)
    paths, all_holdings, all_fills, all_turnover = [], [], [], []
    for strategy, lag in enumerate((1, 3, 7)):
        signals = {}
        for day in range(train_end-1, eval_end+2):
            exposures = []
            for asset in range(n):
                member = active[-1][asset] if 'survivor_filter' in faults else active[day][asset]
                identity = ticker_owner[asset] if 'ticker_merge' in faults else asset
                feature_day = day+1 if 'future_feature' in faults else day-1
                recent = returns[feature_day-(lag-1)][identity]
                value = 0.
                for record in data['fundamentals'][identity]:
                    eligible = record[0] <= day if 'availability_bypass' in faults else record[1] <= day
                    if eligible:
                        value = record[2]
                raw = coefficients[strategy]*(recent-centers[identity])/scales[identity] + .01*value
                exposures.append(math.tanh(10.*raw) if member else 0.)
            norm = max(1., sum(abs(v) for v in exposures))
            signals[day] = [v/norm for v in exposures]
        # Signals are fully formed above; the order scheduler must delay them.
        path, holdings, fills, turnovers = [], [], [], []
        previous = [0.]*n
        for day in range(train_end, eval_end):
            signal_day = day+1 if 'same_bar' in faults else day
            weights = signals[signal_day]
            fill_day = day if 'submission_fill' in faults else day+1
            fill = prices[fill_day]
            pnl = sum(weights[a]*(prices[day+2][a]/fill[a]-1.) for a in range(n))
            path.append(pnl)
            holdings.append(weights)
            fills.append(fill)
            turnovers.append(sum(abs(v-w) for v,w in zip(weights,previous)))
            previous = weights
        paths.append(path)
        all_holdings.append(holdings[select_end-train_end:])
        all_fills.append(fills[select_end-train_end:])
        all_turnover.append(turnovers[select_end-train_end:])
    choose_stop = eval_end if 'test_selection' in faults else select_end
    selected = max(range(len(paths)),key=lambda j:sum(paths[j][:choose_stop-train_end-2]))
    selected_path = paths[selected][select_end-train_end:]
    equity, wealth = [], 1.
    for r in selected_path:
        wealth *= 1.+r
        equity.append(wealth)
    mean = sum(selected_path)/len(selected_path)
    std = max(1e-12,(sum((v-mean)**2 for v in selected_path)/len(selected_path))**.5)
    pvalue = math.erfc(abs(mean)/std*len(selected_path)**.5/2**.5)
    adjustment = 1 if 'uncorrected_trials' in faults else len(paths)
    adjusted = min(1.,pvalue*adjustment)
    return {'holdings':all_holdings,'fill_prices':all_fills,'strategy_returns':[p[select_end-train_end:] for p in paths],
            'returns':selected_path,'equity':equity,'turnover':all_turnover,
            'selected_strategy':selected,'net_mean':mean,'net_std':std,
            'adjusted_p':adjusted,'training_label_mean':sum(labels)/len(labels),
            'descriptive_mean':descriptive}


def evaluate(data, mutations=()):
    unknown=set(mutations)-BY_ID.keys()
    if unknown:
        raise ValueError('unknown structured mutation')
    return research(data, tuple(mutations))


def relative_error(actual, expected):
    """Max group-relative error; exact shape/identity and finite numeric leaves."""
    if isinstance(expected,dict):
        if not isinstance(actual,dict) or actual.keys()!=expected.keys(): return 1.
        return max((relative_error(actual[k],v) for k,v in expected.items()),default=0.)
    def leaves(value):
        if isinstance(value,list):
            return [v for item in value for v in leaves(item)]
        if type(value) not in (float,int) or not math.isfinite(value): raise ValueError('nonfinite numeric')
        return [float(value)]
    def shape(v):
        return [shape(x) for x in v] if isinstance(v,list) else None
    try:
        if shape(actual)!=shape(expected): return 1.
        a,b=leaves(actual),leaves(expected)
        return min(1e300,max((abs(x-y) for x,y in zip(a,b)),default=0.)/max(1e-8,max(map(abs,b),default=0.)))
    except (TypeError,ValueError,OverflowError): return 1.
