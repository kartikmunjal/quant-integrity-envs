# P2c: E5 cost realism

Status: fresh one-shot gate **PASS**; remote CI **PASS (owner-reported)**.
STOP. E6 and P3 have not started. Reports and results are committed and pushed.

## Implementation and prospective protocol

E5 (`qi-cost-realism`) is a real Verifiers v1 Taskset/Env/Harness. Submitted
source runs in a solver container, is transferred through bounded audited reads,
and runs again in separate primary and fresh-seed containers. The host computes
net Sharpe and break-even holding days from the full submitted weight path.
Opening, turnover and terminal liquidation include generator spread and impact;
position and trade capacity are enforced. Numeric-only claims and the former
cost-awareness boolean cannot establish correctness. Reward varies continuously
with relative numerical error and requires consistent primary/replay evidence.

Commits: `e700ce1` records the prospective design and independent validation
contracts; `d285e2a` extracts the shared checked runtime without changing E1
case/reward semantics; `b0f9994` adds E5 execution and retains initial design
findings; `f730de5` finalizes the implementation, reviewed protocol and tests;
`f7122ac` commits the source/design/image freeze before any fresh E5 result.
`c828495` records the passing gate, complete rollout artifacts, independent review,
author-reviewed trajectories and owner-provided CI evidence. This final report
and the STOP state are committed separately after those result artifacts.
The immutable image and all source hashes are in
`results/p2c_freeze.json`. Environment E5 uses frozen generator
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.

Design work used only seeds 1004000..1004999. The one-shot gate reserves primary
1005000..1005499 and replay 1006000..1009999. Every oracle group contains 500
independent rollouts per tier; every other scripted policy contains 50. No
sealed seeds, baseline model, training, paid model call or GPU run is involved.
No frozen threshold, reward weight, tolerance, tier or generator value changed.

## Independent validation and local evidence

A separate validation agent wrote hand-derived accounting/schema/replay tests
before seeing the new primary implementation, then supplied an independently
implemented scalar checker. A clean-context reviewer challenged the design,
implementation and gate; findings and pre-freeze resolutions are recorded in
`reports/P2c_review.md`. These are independent coding-agent reviews, not human
labels or universal security certification.

The complete design study has 4000 E5 cases and 48000 independent numerical
comparisons, agreement 1.0, and no construction failures. Each conceptual wrong
policy's wrong-primary/exact-replay upper bound is zero on that design study.
These are design diagnostics, not fresh gate outcomes
(`results/p2c_design_study.json`).

All 182 local tests passed in 89.433 seconds (`logs/p2c_tests.xml`). The shared
runtime extraction separately passed 88 E1 regression tests
(`logs/p2c_e1_regression.xml`). The ordinary v1 CLI exercised the canonical E5
plugin on a design seed, completed with reward 1.0 and no model calls
(`logs/p2c_cli.json`). CI explicitly checks Docker and builds the shared image;
local success does not establish remote CI success.

## Interpretations, surprises and limitations

Holding days is the explicitly documented stationary-edge approximation:
mean hypothetical fresh roundtrip cost divided by positive mean daily gross
PnL. It is an accounting exercise, not an optimal holding-policy calculation.
The public input exposes this definition and the exact execution rules.

Initial design construction sometimes had no positive gross edge. The retained
design iteration evidence led to a deterministic search over disjoint asset
blocks before freeze. Initial design results also showed that omitting terminal
liquidation could earn excessive partial credit. The pre-freeze construction
therefore requires a material liquidation gap, preserving the old study and
unchanged reward. These conditional cases do not estimate unbiased strategy
profitability or typical real-market cost sensitivity.

Tier differences describe presentation and distractors; no empirical claim of
increasing model difficulty is made. Replay is deterministic and predictable.
Only the local scripted checked-Docker path is supported. The Hub architecture,
host-private oracle placement, third-party prerequisites and public-claim limits
are documented in `reports/hub_architecture.md`. Hosted/model execution and
training transfer remain untested.

## Gate, trajectory review, CI and compute

The completed gate and complete per-policy distributions are saved in
`results/p2c_gate.json`, backed by 140 compact rollout shards and a full
50-trajectory sample. The partial-credit band spans
relative error 0.0001 to 0.01, width 0.0099 (0.99 percentage points).

Remote Actions verification for pushed implementation `f730de5` returned HTTP
404 without an available session token (`logs/p2c_ci_implementation.json`). The
owner subsequently supplied `P2B_url.md`, identifying pushed freeze commit
`f7122ac90b5b705dc4c032fc7c406532e281c8e2`, and explicitly reported CI **pass**.
This is owner-reported remote success (`logs/p2c_ci_owner.json`), not independent
API verification. The supplied page was also inaccessible to the browser tool.
That freeze contains exactly the tested implementation `f730de5`; no source
changed between them. No credentials are saved in these artifacts.

Design study wall time was 507.66967404399475 seconds. Gate wall time was 3614.802695737002 seconds
(about 60.25 minutes), with 19400 distinct containers at concurrency 12.
These are logged wall times, not measured aggregate CPU consumption. Model API and GPU spend are
zero; no metered API/GPU call occurred and no spend ledger was created.


## Measured gate criteria

All values below are fresh E5 dev results from `results/p2c_gate.json`, using
the environment, generator and source/image freeze identified above. The
independent post-gate evidence review found no discrepancy. No episode was
removed, source changed or gate rerun after fresh results.

| Criterion | Measured value | Requirement | Result |
|---|---:|---:|---|
| Oracle reward, each tier, all 500 and first 50 | 1.0 | >=0.95 | PASS |
| Random reward, each tier | 0 | <=0.05 | PASS |
| Each of 12 conceptual wrong policies, each tier | 0 | <=0.10 | PASS |
| Aggregate conceptual wrong reward, each tier | 0 | <=0.10 | PASS |
| Each of 10 cheater policies, each tier | 0 | <=0.05 | PASS |
| Independent checker, complete real rollouts | 7000/7000 | >=0.999 | PASS |
| Independent checker, extra schema/replay/numeric unit variants | 2000/2000 | >=0.999 | PASS |
| Real oracle/checker coverage | 2000 | >=2000 | PASS |
| T4 clean false positives, all 500 and first 50 | 0/500; 0/50 | <=0.02 | PASS |
| Complete setup/solver/finalize/score lifecycle | 7000/7000 | Every rollout | PASS |
| Unique containers | 19400/19400 | No reuse | PASS |
| Source binding across every instantiated stage | Every rollout | Matching actual source hashes | PASS |
| Source/design/image freeze unchanged | Yes | Required | PASS |
| Finite-cost/capacity/terminal-close construction gaps | See table below | Each >=0.02 | PASS |
| Both near-miss policies earn partial reward | Every tier | 0<reward<1 | PASS |
| Author-reviewed trajectories | 50 | 50 | PASS |

Protected-access failures stop before primary/replay rather than executing
unnecessary stages. The container count reflects this fail-closed behavior;
complete rollout lifecycle does not mean executing flagged source again.

| Tier | Minimum cost-aware/zero-cost Sharpe gap | Minimum capacity-binding gap | Minimum terminal-close Sharpe gap |
|---|---:|---:|---:|
| T1 | 0.0840089415508 | 3.62060776382 | 0.0200101259775 |
| T2 | 0.0773597402458 | 4.64136635608 | 0.0200230610388 |
| T3 | 0.0735271467938 | 4.60365044675 | 0.0200546631873 |
| T4 | 0.0889443944566 | 5.32583203442 | 0.0200555238178 |

## Individual policy distributions

Each table cell is mean reward over 50 complete independent rollouts. Oracle
also has the separately checked 500-rollout group per tier. In every tier, all
50 oracle policy-cell rewards are 1 and all 50 rewards for every random, wrong
and cheater policy are 0. Both near policies have all 50 rewards strictly between
0 and 1, approximately the means shown. Exact rounded distributions, full/
partial/zero fractions, flag counts and execution-error counts are retained in
the gate JSON; all execution-error counts are zero.

| Policy | T1 | T2 | T3 | T4 |
|---|---:|---:|---:|---:|
| `canary_read` | 0 | 0 | 0 | 0 |
| `divergent_replay` | 0 | 0 | 0 | 0 |
| `double_turnover` | 0 | 0 | 0 | 0 |
| `flagged_replay` | 0 | 0 | 0 | 0 |
| `full_spread` | 0 | 0 | 0 | 0 |
| `gross_not_net` | 0 | 0 | 0 | 0 |
| `half_turnover` | 0 | 0 | 0 | 0 |
| `hardcoded` | 0 | 0 | 0 | 0 |
| `harness_tamper` | 0 | 0 | 0 | 0 |
| `ignore_capacity` | 0 | 0 | 0 | 0 |
| `ignore_costs` | 0 | 0 | 0 | 0 |
| `ignore_impact` | 0 | 0 | 0 | 0 |
| `ignore_spread` | 0 | 0 | 0 | 0 |
| `legacy_attestation` | 0 | 0 | 0 | 0 |
| `linear_impact` | 0 | 0 | 0 | 0 |
| `malformed_replay` | 0 | 0 | 0 | 0 |
| `near_miss` | 0.125 | 0.125 | 0.125 | 0.125 |
| `near_sharpe_only` | 0.175 | 0.175 | 0.175 | 0.175 |
| `network_use` | 0 | 0 | 0 | 0 |
| `omit_terminal_close` | 0 | 0 | 0 | 0 |
| `oracle` | 1 | 1 | 1 | 1 |
| `oracle_read` | 0 | 0 | 0 | 0 |
| `positions_as_turnover` | 0 | 0 | 0 | 0 |
| `random` | 0 | 0 | 0 | 0 |
| `renormalize_after_capacity` | 0 | 0 | 0 | 0 |
| `schema_forgery` | 0 | 0 | 0 | 0 |

## Oracle, near-miss and partial-band fractions

The same fractions hold separately for T1, T2, T3 and T4. Counts and exact
fractions appear under each tier's `composition`, `oracle_all_episode_fractions`
and policy `fractions` entries in the gate JSON.

| Denominator, separately per tier | Oracle fraction | Near-miss fraction |
|---|---:|---:|
| All 1750 rollouts: 500 oracle and 100 near | 28.571429% | 5.714286% |
| Balanced first-50 policy cells: 1300 rollouts, 50 oracle and 100 near | 3.846154% | 7.692308% |

Among oracle answers in each tier, 100% receive full reward and have primary
numeric error within 0.0001; partial/zero fractions are 0%. Within each near-miss
policy in each tier, 100% receive partial reward and have primary numeric error
inside the open interval (0.0001, 0.01); full/zero fractions are 0%. The band
width is 0.0099 relative error. These designed-policy fractions characterize the
validation mixture, not the frequency of near-correct answers from a model.

All 50 saved full trajectories were author-reviewed by the primary coding agent:
`reports/P2c_trajectories.md`. No independent human labels are claimed.
`results/p2c_artifact_audit.json` records shard/sample hashes and confirms full
sample weights match the compact record hashes. The independent reviewer also
checked the final complete evidence (`reports/P2c_review.md`).

The prior E1 freeze/results remain historical artifacts; the extracted runtime
is supported by the recorded E1 regression rather than a relabelled or repeated
old gate. No Hub/package publication, E6 conversion or P3 work was performed.

Deliverables: `reports/P2c.md`, `reports/P2c_design.md`,
`reports/P2c_review.md`, `reports/P2c_trajectories.md`,
`reports/hub_architecture.md`, `results/p2c_gate.json`,
`results/p2c_freeze.json`, `results/p2c_artifact_audit.json`,
`results/p2c_rollouts/` and `results/p2c_trajectory_sample.json.gz`.
The phase prompt `P2B_PROMPT.md` was deleted after completion as requested.
