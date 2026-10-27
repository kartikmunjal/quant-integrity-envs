# P2d: E6 corrupted-record reconciliation

Status: one-shot fresh gate **PASS**; source-freeze CI **PASS (owner-reported)**.
STOP before P3. A T4 diagnostic-definition discrepancy is disclosed below.
Reports and results are committed and pushed.

## What was built and frozen

E6 `qi-data-traps` is a real Verifiers v1 Taskset/Env/scripted Harness using the
unchanged shared qi_runtime and immutable E1/E5 Docker image. Submitted source
produces a full reconciled listing/session table and quote-record anomaly IDs.
The bounded source is transferred, solver destroyed, then independently executed
in primary and fresh-seed containers. Protected host truth records every
corruption's original/altered records before the solver runs, including rejected
submissions. No oracle or sealed manifest enters an agent-facing mount.

The previous core compared final active identifier sets and called legitimate
generated splits/identifier changes anomalies. It did not repair corrupted
records and could retain 0.6 despite entirely wrong flags. Its direct score is
now retired. The replacement plants genuine duplicates, sign-flipped/scaled
prices, unadjusted splits, missing delisting returns, stale prices and identifier
collisions. T1/T2/T3 contain one/two/six corruptions; T4 contains zero, with
legitimate corporate actions, shared tickers and large moves as clean decoys.

`1006387` commits design and prospective validation before primary implementation.
`7fb9c52` commits the reviewed implementation and design-only evidence.
`1e40d58` commits the source/design/image freeze before any fresh E6 result.
`8bc2919` records the complete passing gate, independent and author reviews,
owner-supplied CI status and the disclosed clean-gap diagnostic discrepancy.
The final report and STOP state follow in a separate documentation commit.
The exact image, file hashes and source commit are in `results/p2d_freeze.json`.
Environment E6 uses frozen generator
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.
No frozen threshold, reward weight, tolerance, generator source or tier changed.
E1/E5 historical experiments remain unchanged.

## Protocol and independent validation

Design seeds: 1007000..1007999 only. Fresh primary: 1008000..1008499;
fresh replay: 1009000..1009999. These numerical dev ranges were previously used
by other environments; fresh here means no prior E6 gate outcome. No sealed
seed, baseline, model evaluation, training, API or GPU run occurs. Source-aware
replay is deterministic and predictable, not a sealed holdout.

A separate validation agent wrote hand-derived schema/reward/accounting tests
before seeing new primary code, then wrote an independent scalar checker with
no primary helpers. A clean-context reviewer challenged the implementation,
controls and evidence protocol. The checker validates parsed dictionary records;
raw JSON and duplicate-key parsing are the runtime parser's responsibility.
This is independent numerical/structural validation, not two independent raw
serialization parsers or independent human labels.

The first review caught a freeze manifest pointing at the prior E5 design and
a checker accepting bool/float exit codes. Both were corrected before freeze,
with adversarial status/bounds tests. No unresolved pre-freeze blocker remained
(`reports/P2d_review.md`). Design study: 4000 E6 cases, 40000 independent numeric
comparisons, agreement 1.0, no construction failures
(`results/p2d_design_study.json`). These are design results, not fresh outcomes.

All 288 tests passed in the final full local suite, including E1/E5 runtime
regressions (`logs/p2d_tests.xml`). Additional checker and actual source-policy
runtime evidence is in `logs/p2d_checker_final.xml` and
`logs/p2d_runtime_tests.xml`. The canonical v1 CLI completed a design episode
with reward 1.0 and zero model calls (`logs/p2d_cli.json`).

## Reward and interpretations

Numeric reconciliation quality U is smoothstep in maximum relative cell error:
full credit through 0.0001, zero from 0.01, partial band width 0.0099 (0.99
percentage points). Missing/extra rows or incorrect identity/status contribute
error 1. For corrupt cases anomaly quality A=F1^32; on clean cases A=(1+false
flags)^(-4). This steep but continuous transform prevents many false flags from
retaining substantial credit. No flags on a correctly reconciled clean case
earns full reward; every additional false flag strictly reduces reward.

With C=U*A per execution, reward is
C_primary*C_replay*(0.6*U_primary+0.4*A_primary), retaining frozen 0.6/0.4
weights. Invalid schema, nonfinite values, runtime flags and absent replay
hard-zero. The max-cell error and steep F1 transform are strict accounting
choices, not smooth evidence of general anomaly-detector quality. Both numeric
near misses and a separate false-flag diagnostic are retained in gate results.
Never-flag with correct reconciliation is intentionally correct on T4 and wrong
on corrupted tiers, so it is a diagnostic rather than a dishonest cheater test.

Public independent audited returns, price anchors, registry and action notices
make repairs identifiable. This is cross-source accounting, not recovery of
unknowable prices from one damaged feed. Positive price construction uses
max(1+generated_return,0.05); adjusted prices are relative to each window's anchor.
The generator has no delisting return, so the task layer supplies an explicit
synthetic settlement return -0.35-spread_bps/1000 on the generated delisting day,
recorded publicly in its notice and privately in truth. The generator is unchanged.

## Surprises and preserved design findings

Initial tests found that disjoint quote windows could let ticker-only grouping
retain all rows. An additional distinct listing now shares the split listing's
sessions and ticker, making the identity mistake distinguishable. Initial
200-asset design data lacked any usable delisting on seeds 1007521, 1007561 and
1007962; these failures are retained in `results/p2d_design_study_initial.json`.
No seed was dropped. E6 now uses 1000 assets/500 sessions, inside frozen ranges,
with deterministic event-rich windows and explicit construction failure.

Two selected assets supply large genuine moves: one may receive a stale-price
corruption and another stays clean. The shared ticker is a legitimate listing
ambiguity. These conditional exercises do not estimate population anomaly rates,
real-market event prevalence or empirical ordering of model difficulty by tier.
The local checked-Docker, trusted-host oracle, predictable replay and unsupported
hosted/model execution limitations in `reports/hub_architecture.md` apply.

## Gate, CI, spend and compute

Fresh gate measurements are complete: 7000 independent rollouts in 19400
distinct containers. All gate checks passed. Individual distributions and
fractions appear below; all 50 full sample records were author-reviewed
(`reports/P2d_trajectories.md`).
The one-shot call marker is `logs/p2d_gate_calls.json`. Source/design/image remain
frozen and no tuning or rerun follows fresh results.

The GitHub Actions API returned HTTP 404 without available session authentication
for pushed freeze `1e40d5812d75a6dd4da20f1c814ad98cade19ece`
(`logs/p2d_ci.json`). This independent query was unavailable. The owner subsequently supplied
`P2B_url2.md`, identifying this exact freeze commit, and reported CI **passed**
(`logs/p2d_ci_owner.json`). The commit page was also inaccessible to the browser
tool. Remote success is therefore owner-reported, not independently fetched.
Local Docker/test success is
reported separately from remote CI. No credentials are recorded.

The final design study took 322.4614991209819 wall seconds. Gate wall time was
3769.115322675003 seconds (about 62.82 minutes) at concurrency 12.
The final full suite took 115.36 seconds (`logs/p2d_tests.xml`).
Experimental model API/GPU spend is zero; no paid call occurred, so no spend
ledger was created. Wall times do not measure aggregate CPU utilization.


## Measured gate criteria

All measurements below are E6 fresh dev results, generator and source/image
freeze as identified above. Complete evidence is in `results/p2d_gate.json`,
140 rollout shards, the full trajectory sample and artifact audits. No episode
was dropped and no source/design/image changed or gate rerun after fresh results.

| Criterion | Measured value | Requirement | Result |
|---|---:|---:|---|
| Oracle reward, each tier, all 500 and first 50 | 1.0 | >=0.95 | PASS |
| Random reward, each tier | 0 | <=0.05 | PASS |
| Each of ten conceptual controls, each tier | See individual table | <=0.10 | PASS |
| Aggregate wrong-control reward, each tier | See tier summary | <=0.10 | PASS |
| Each of ten cheaters, each tier | 0 | <=0.05 | PASS |
| Independent parsed-record scoring agreement | 7000/7000 | >=0.999 | PASS |
| Extra schema/replay/numeric unit comparisons | 2000/2000 | >=0.999 | PASS |
| Real oracle/checker cases | 2000 | >=2000 | PASS |
| T4 clean false flags/runtime false rejections | 0/500;0/50 | <=0.02 | PASS |
| Complete setup/solver/finalize/score lifecycle | 7000/7000 | Every rollout | PASS |
| Distinct instantiated containers | 19400/19400 | No reuse | PASS |
| Actual transferred-source binding | Every instantiated stage | Matching hashes | PASS |
| Protected primary truth recorded | Every rollout | Content-addressed oracle hash | PASS |
| Numeric near misses and false-flag diagnostic | Positive partial reward in every tier | 0<reward<1 | PASS |
| Never-flag diagnostic | 0 on T1–T3;1 on T4 | Correct clean semantics | PASS |
| Required conceptual separation | See gap discussion | >=0.02 in every case | PASS with diagnostic caveat |
| Author-reviewed trajectories | 50 | 50 | PASS |
| Frozen sources/image | Unchanged | Required | PASS |

Flagged solvers fail closed before primary/replay; this explains why container
count is below three times rollout count. There are zero execution exceptions.
Fresh scoring agreement uses protected planted truth; independent reconstruction
from public observations was established on all 4000 design cases, not rerun as
a second fresh gate. See the independent review for the exact scope.

| Tier | Largest individual wrong mean | Aggregate of ten wrong means |
|---|---:|---:|
| T1 | 5.153960755e-25 | 5.153960755e-26 |
| T2 | 5.154181128e-25 | 5.154181128e-26 |
| T3 | 3.706119773e-32 | 3.734259448e-33 |
| T4 | 3.76529314e-06 | 3.765293854e-07 |

## Gap measurements and post-gate reporting discrepancy

The frozen diagnostic reports minima of max(numeric_error,1-F1) in every tier:

| Tier | Flag large moves | Ignore identifiers | Ignore splits | Ticker only |
|---|---:|---:|---:|---:|
| T1 | 0.5 | 1 | 0.5 | 1 |
| T2 | 0.4285714286 | 1 | 0.5 | 1 |
| T3 | 0.4545454545 | 1 | 0.5 | 1 |
| T4 | 1 | 1 | 1 | 1 |

The design note instead specifies max(numeric_error,1-1/(1+false_flags)) for
**clean T4**. This is a diagnostic-definition discrepancy discovered during
post-gate reporting; it does not change the actual reward or any threshold.
The raw frozen source/design/results are preserved without correction or rerun.
Do not interpret T4's recorded 1.0 values as measurements of the written clean
false-flag loss.

A separate arithmetic check of existing saved control records gives written-gap
minima 0.75,1.0,0.75,1.0 respectively (50 records per policy). For all constructed
clean cases, frozen construction supplies conservative lower bounds 0.5,1.0,0.5,
1.0: at least one genuine large-move false flag; an actual identifier change;
a positive-price split with factor 0.5,2 or 3; and overlapping shared-ticker
listings. Thus the required 0.02 floor still holds under the written metric.
This source reasoning/saved-record audit is in `results/p2d_clean_gap_audit.json`,
not a new evaluation or a silently replaced gate result. The owner should retain
this discrepancy when deciding any subsequent phase.

## Individual policy distributions

Each cell is **mean (full/partial/zero counts)** over 50 independent rollouts.
Exact reward-value distributions, flag counts and fractions are retained per
policy/tier in the gate JSON. Tiny positive rewards are intentionally shown in
scientific notation. Oracle additionally has the checked500-episode group.

| Policy | T1 | T2 | T3 | T4 |
|---|---:|---:|---:|---:|
| `canary_read` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `divergent_replay` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `drop_identifier_history` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `drop_inactive` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `flag_all` | 4.6795123e-77 (0/50/0) | 9.520228e-59 (0/50/0) | 3.7061198e-32 (0/50/0) | 7.1406526e-13 (0/50/0) |
| `flag_large_moves` | 5.1539608e-25 (0/1/49) | 5.1541811e-25 (0/7/43) | 2.8139676e-34 (0/50/0) | 3.7652931e-06 (0/50/0) |
| `flagged_replay` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `hardcoded` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `harness_tamper` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `ignore_delistings` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `ignore_identifiers` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `ignore_splits` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `legacy_schema` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `malformed_replay` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `near_false_flag` | 3.2233788e-12 (0/50/0) | 3.7682503e-07 (0/50/0) | 0.0037598605 (0/50/0) | 0.0024414062 (0/50/0) |
| `near_miss` | 0.175 (0/50/0) | 0.175 (0/50/0) | 0.175 (0/50/0) | 0.175 (0/50/0) |
| `near_small` | 0.64517212 (0/50/0) | 0.64517212 (0/50/0) | 0.64517212 (0/50/0) | 0.64517212 (0/50/0) |
| `network_use` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `never_flag` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 1 (50/0/0) |
| `oracle` | 1 (50/0/0) | 1 (50/0/0) | 1 (50/0/0) | 1 (50/0/0) |
| `oracle_read` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `random` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `raw_price_returns` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `reverse_split_adjustment` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `schema_forgery` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `ticker_only` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |

## Oracle, near-miss and partial-band fractions

The following composition fractions hold separately in T1, T2, T3, T4. Numerical
near misses are `near_miss` and `near_small`; the one-false-flag diagnostic is
reported separately and combined to make the denominator explicit.

| Denominator per tier | Oracle | Numeric near misses | One-false-flag | All three near controls |
|---|---:|---:|---:|---:|
| All 1750 rollouts | 500/1750=28.571429% | 100/1750=5.714286% | 50/1750=2.857143% | 150/1750=8.571429% |
| Balanced first 50 cells, 1300 rollouts | 50/1300=3.846154% | 100/1300=7.692308% | 50/1300=3.846154% | 150/1300=11.538462% |

In every tier, 100% of oracle answers earn full credit and have primary numeric
error within 0.0001; partial/zero fractions are 0%. Within each numeric near-miss
policy,100% earn partial credit and fall inside the numeric partial band
(0.0001,0.01); full/zero fractions are 0%. Its width is0.0099 relative error.
The one-false-flag diagnostic also has 100% partial reward, while its numeric
reconciliation is exact; it tests anomaly quality, not the numeric error band.
There is no additional finite-width anomaly band: F1^32 is continuous throughout
(0,1), and the clean false-flag penalty decreases strictly for additional flags.
These fractions characterize designed scripted controls, not model accuracy.

## Review, provenance and STOP

The primary author reviewed all 50 full records against saved host truth and
recomputed their independent scores. Their full tables match compact hashes;
planted truth matches protected oracle hashes. All 7000 rewards reproduce from
saved error vectors (`results/p2d_artifact_audit.json`). The independent reviewer
checked complete saved evidence (`reports/P2d_review.md`,
`results/p2d_review_audit.json`). No independent human labels are claimed.

The owner-reported CI pass covers source-freeze `1e40d58`. Subsequent report/artifact
commits have no changed implementation, but their remote CI is not inferred from
that pass. Final commit query availability is reported separately. No Hub
publication, sealed evaluation, API/GPU spending or P3 work occurred.

Deliverables: `reports/P2d.md`, `reports/P2d_design.md`,
`reports/P2d_review.md`, `reports/P2d_trajectories.md`,
`reports/hub_architecture.md`, `results/p2d_gate.json`,
`results/p2d_freeze.json`, `results/p2d_artifact_audit.json`,
`results/p2d_review_audit.json`, `results/p2d_clean_gap_audit.json`,
`results/p2d_rollouts/` and `results/p2d_trajectory_sample.json.gz`.
`P2B_PROMPT.md` was deleted after completion as requested.
