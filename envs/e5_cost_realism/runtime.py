"""E5-specific policy programs and adapters over the shared checked runtime."""
from __future__ import annotations
import hashlib
from qi_runtime import CheckedRuntime,WORK,PRIVATE,IMAGE,MAX_SOURCE,execute_program
from .reward import check_answer


def reference_program(mode='exact'):
    prefix='MODE='+repr(mode)+'\n'
    return prefix+'''import json,sys,math
x=json.load(open(sys.argv[1])); n=len(x['capacity_usd']); caps=[c/x['notional'] for c in x['capacity_usd']]
def clip(v,c):return max(-c,min(c,v))
old=[0.]*n; weights=[]
for signal in x['signals']:
    mean=sum(signal)/n; centered=[v-mean for v in signal]; scale=sum(abs(v) for v in centered)
    target=[v/scale if scale else 0. for v in centered]
    if MODE=='ignore_capacity': row=target
    else: row=[clip(p+clip(t-p,c),c) for p,t,c in zip(old,target,caps)]
    if MODE=='renormalize_after_capacity':
        gross=sum(abs(v) for v in row);row=[v/gross if gross else 0. for v in row]
    weights.append(row);old=row

def cost(delta):
    result=0.
    for i,v in enumerate(delta):
        mag=abs(v); part=mag*x['notional']/x['adv_usd'][i]
        spread=x['spread_bps'][i]/20000
        impact=x['impact_coefficient'][i]*math.sqrt(part)/100
        if MODE=='ignore_spread':spread=0.
        if MODE=='ignore_impact':impact=0.
        if MODE=='full_spread':spread*=2
        if MODE=='linear_impact':impact=x['impact_coefficient'][i]*part/100
        result+=mag*(spread+impact)
    return result
old=[0.]*n; gross=[]; net=[]; roundtrips=[]
for row,returns in zip(weights,x['returns']):
    pnl=sum(w*r for w,r in zip(row,returns));gross.append(pnl)
    delta=[w-p for w,p in zip(row,old)]
    charge=cost(row if MODE=='positions_as_turnover' else delta)
    if MODE=='half_turnover':charge*=.5
    if MODE=='double_turnover':charge*=2
    net.append(pnl-charge);roundtrips.append(2*cost(row));old=row
if MODE!='omit_terminal_close':
    closing=cost(old)
    if MODE=='half_turnover':closing*=.5
    if MODE=='double_turnover':closing*=2
    net[-1]-=closing
if MODE=='half_turnover':roundtrips=[v*.5 for v in roundtrips]
if MODE=='double_turnover':roundtrips=[v*2 for v in roundtrips]
def sharpe(v):
    m=sum(v)/len(v);std=math.sqrt(sum((a-m)**2 for a in v)/len(v));return math.sqrt(252)*m/max(std,1e-12)
edge=sum(gross)/len(gross);holding=sum(roundtrips)/len(roundtrips)/edge if edge>0 else float('inf')
s=sharpe(net)
if MODE in ('ignore_costs','gross_not_net'):s=sharpe(gross)
if MODE=='ignore_costs':holding=0.
if MODE in ('near_miss','near_sharpe_only'):s*=1.00505
if MODE=='near_miss':holding*=1.00505
print(json.dumps({'weights':weights,'net_sharpe':s,'breakeven_holding_days':holding}))
'''


def replay_seed(seed,tier,source):
    start,width=(1004000,1000) if seed<1005000 else (1006000,4000)
    value=start+int.from_bytes(hashlib.sha256(f'E5:{seed}:{tier}:{source}'.encode()).digest()[:8],'big')%width
    return start+(value-start+1)%width if value==seed else value


async def execute_once(data,program):
    return await execute_program(data,program,lambda output:check_answer(output,data),namespace='e5')


async def evaluate_program(seed,tier,program):
    from .v1_taskset import run_policy
    return await run_policy(seed,tier,program)
