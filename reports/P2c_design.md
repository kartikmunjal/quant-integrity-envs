# P2c prospective E5 reward, cases and execution design

Written before E5 implementation, new validation, design studies or fresh gates.
Scope: E5 only; extract existing E1 runtime into src/qi_runtime without changing
E1 reward/case semantics. Do not begin E6 or P3. P1 generator remains
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.

## Existing core decomposition and deficiencies

The old E5 core takes submitted numbers and a cost_awareness boolean, not a gross
signal. Reward is 0.5 times an exact-within-1e-4 net-Sharpe hit, plus 0.4 times a
holding-period hit, plus 0.1 for cost_awareness=True. Thus a false self-attestation
alone can earn 0.1; one correct field retains 0.5 or 0.4 despite a conceptual
mistake in the other. Its random policy is schema-invalid, and its cheaters
self-report extra forbidden fields rather than execute actual actions.

Its oracle averages market returns, subtracts a single constant daily roundtrip
cost, and divides that cost by max(mean gross return,1e-12) for holding days.
Spread and square-root impact are present, but notional is only selected from
median capacity; positions and turnover are never checked against capacity.
There is no agent-submitted signal, actual turnover path, terminal liquidation,
or fresh-source replay. These are substantive content gaps, not passing evidence
for the requested taskset. Retire direct numeric/self-attestation scoring.

## Gross-signal task and canonical financial computation

Each public task specifies a deterministic gross strategy over 48 sessions and
8 assets selected from the frozen 200-asset, 500-day generated market. It exposes
lagged signals, next-session returns, generator spread_bps, impact_coefficient,
adv_usd and capacity_usd, plus synthetic portfolio notional. All values are
synthetic. Agent code must submit a full **weights[session][asset]** path as well
as net_sharpe and breakeven_holding_days; submitted numeric claims alone fail.

For each session: demean the supplied lagged signal, divide by its gross absolute
sum, then enforce per-asset position and trade capacity. With c_i=capacity_usd_i /
notional, let target_i be the normalized signal; choose
w_ti=clip(w_(t-1)i+clip(target_i-w_(t-1)i,-c_i,c_i),-c_i,c_i), starting at zero.
Do not renormalize after clipping. This is the unique reference strategy, not an
unconstrained portfolio optimization problem. All submitted weights are checked
against that strategy and the public capacity constraints.

The verifier independently executes source and computes metrics from submitted
weights. For each trade, q_i=abs(delta_weight_i)*notional and
one_way_rate_i=spread_bps_i/(2*10000) +
impact_coefficient_i*sqrt(q_i/adv_usd_i)/100.
Trade cost as a fraction of portfolio notional is
sum_i abs(delta_weight_i)*one_way_rate_i. Initial opening and **terminal closing**
are included. Daily gross PnL is sum_i w_ti*r_ti; daily net PnL subtracts actual
turnover cost, with final closing charged to the last session. Net Sharpe is
sqrt(252)*mean(net)/max(population_std(net),1e-12).

Break-even holding days is defined prospectively as average hypothetical fresh
roundtrip cost of each daily target portfolio divided by its mean daily gross
PnL. Each hypothetical roundtrip enters from zero and exits to zero using the
same spread/impact formula. This is a stationary-edge approximation, not a claim
about future alpha decay or realized stopping times. The constructor requires a
strictly positive reference gross mean; a submitted strategy with nonpositive
gross mean has no finite break-even period and cannot match the finite oracle.

Capacity is an enforced physical constraint: abs(w_ti)*notional and
abs(w_ti-w_(t-1)i)*notional may not exceed capacity_usd_i (small machine-roundoff
allowance only). The trusted calculator clips infeasible execution to the same
limits and records the violation; any violation makes the submission invalid.
Terminal liquidation is feasible because abs(w_last_i)<=c_i. No cost-awareness
boolean, submitted flag or claimed ledger establishes trusted evidence.

## Prospective continuous reward and fixed scales

Frozen weights remain E5 net_sharpe=0.5, holding_period=0.4, cost_awareness=0.1.
Frozen full-credit relative tolerance is tau=1e-4. New zero-credit error scale is
E=0.01. Define s(e)=1 for e<=tau, s(e)=0 for e>=E; otherwise with
u=(e-tau)/(E-tau), s(e)=1-3*u*u+2*u*u*u. The partial-credit band width is
**0.0099 relative error**, i.e. 0.99 percentage points. This introduces no change
to any preregistered gate threshold, reward weight or full-credit tolerance.

For each primary/replay execution, e_S is the maximum relative discrepancy of
reported Sharpe versus trusted computed Sharpe and trusted computed Sharpe versus
the canonical oracle. e_H is defined analogously for holding days. Denominators
are max(abs(truth),1e-12). e_W is max absolute deviation from canonical weights,
divided by max(max abs(canonical weights),1e-12). Let P=s(max(e_S,e_H,e_W)) for
primary and R for replay, and C=P*R. The three terms are
S=C*s(e_S_primary), H=C*s(e_H_primary), A=C*R. Final reward is
**0.5*S+0.4*H+0.1*A**. Coupling prevents an unchanged component or a correct first
answer from earning substantial reward after a conceptual/replay failure.

Schema/runtime/protected-access failures, absent replay, nonfinite metrics or
capacity violations give zero. Conceptual errors >=0.01 on either execution
therefore give zero. Near-miss reports scaling both numeric claims by 1.00505,
with exact feasible weights, have a prospective reward of 0.125; single-field
near misses also retain positive partial credit. Include near/far boundary tests.

## Construction, tiers, separation and design/gate split

Design seeds: **1004000..1004999** only. Fresh primary seeds start at **1005000**;
policy-cell statistics use 1005000..1005049 per tier, and oracle/checker coverage
uses 1005000..1005499 per tier. Gate replay seeds are **1006000..1009999**,
deterministically derived from primary seed, tier and actual transferred source,
and distinct from primary. Design replay stays inside the design range.
These are the owner's round-specific ranges; prior E1 dev replay may have used
some of the same integers, so freshness here means no E5-design tuning on them,
not a claim that no other environment ever generated those market seeds.

The constructor deterministically searches predefined windows/notional choices
and requires **at least 0.02 relative net-Sharpe gap** between cost-aware and
zero-cost naive execution in every emitted case. It also requires binding
capacity (at least one raw target exceeds capacity by >=0.02 relatively), finite
nonzero oracle metrics and positive reference gross edge. A missing candidate
is an explicit failed gate episode, never a dropped seed. Candidate choices and
any revisions are documented using design seeds before the committed freeze.
The generator itself, tiers and preregistration remain unchanged.

Initial candidate starts: T1 80..120, T2 160..200, T3 240..280, T4 320..360;
48 sessions, first 8 assets active across the chosen window, and notional factors
2,4,8 times n_assets*median(capacity). T1 gives explicit one-way/roundtrip hints;
T2 has subtler turnover conventions; T3 combines binding capacity and descriptive
summary decoys; T4 is clean/correct with harmless reorderings/units annotations.
Empirical model/human tier difficulty is not asserted.

## Protocol, independent validation and reporting

An independent validation agent writes its checker tests from SPEC and this note
**before seeing the new implementation**. Primary and independent checkers share
no financial/reward helpers. Write runtime tests before extracting shared code.
Use src/qi_runtime for inspected Docker execution, bounded audited reads, immutable
source transfer, sandbox flags and single-case execution. E1 imports the shared
implementation through its compatibility wrapper; retain E1 regression tests.

Each gate case goes through a complete normal v1 Env/Agent/Task rollout and its
own solver, primary and replay containers, never a shared interpreter or caller-
attached evidence. Unsupported harness/runtime choices fail closed. Protect
oracle data outside mounts. Source/design/image/generator hashes are committed
before a one-shot call marker and any fresh E5 result; no tuning or rerun follows.
At least 2000 real oracle/checker cases, all policy-cell controls and separate
schema/tamper/replay adversaries are retained, with individual distributions.
Agreement allows at most 1e-8 absolute reward difference for floating evaluation
order; frozen agreement proportion remains >=0.999.

Report (a) policy-plan composition fractions for oracle and near-miss episodes,
(b) within-policy full/partial/zero reward fractions, and (c) numeric-error band
fractions, each per tier, to make the requested fractions unambiguous. Save all
measurements with E5 and generator/task version provenance. Record local tests,
actual remote CI status for pushed commits, spend/CPU wall time and an author-
reviewed 50-trajectory sample. Obtain a separate clean-context review before the
gate. Write reports/hub_architecture.md from current official primary docs,
including oracle placement, third-party boundaries and explicit unknowns. Commit
and push reports/results, delete the phase prompt at completion as previously
requested, update STATE and STOP before E6/P3. No paid model/GPU run is authorized.

### Design-stage construction revision, before any fresh result

The initial first-eight-assets construction failed on design seed 1004000/T3:
all 123 candidate window/notional combinations had negative reference gross
mean (maximum -0.0007453483430403677). Evidence is saved in
results/p2c_design_iterations.json. Instead of dropping the seed or inventing a
finite holding period, search consecutive disjoint eight-asset blocks of the
eligible universe at each candidate start, in asset-id order, followed by the
predefined notional factors. Retain the first candidate meeting the unchanged
conditions. This is explicit conditional task construction for a finite-horizon
accounting exercise, not a claim of unbiased strategy profitability. Only design
data informed this revision; the frozen P1 generator and all gate thresholds are
unchanged.
