# P2d round 2: E6 single-anomaly reward revision

Status: fresh one-shot gate **FAILED** because one rollout lacks complete
runtime/provenance evidence. Reward-sensitivity objectives passed. STOP before P3. E1/E5 code, rewards,
gates and freezes remain unchanged under the explicit owner decision in
P2B_PROMPT1.md. The prior stop audit and sensitivity tables remain historical
documentation; this report covers the authorized continuation from step 3.

## What changed and why

The first E6 reward applied F1^32 in both execution couplings and again in the
weighted sum. With exact reconciliation and equal F1=f, its effective reward
was 0.6*f^64+0.4*f^96. Thus a T1 correct detection plus one false flag yielded
about 3.22e-12. The read-only E1/E5 sensitivity findings remain documentation;
no corresponding implementation, gate or freeze was changed.

The revised E6 reward computes numeric quality U as before. For corrupt cases,
A=F1^3; for clean cases A=(1+false_flags)^(-3). Per execution use B=min(U,A),
S=B*(0.6*U+0.4), then R=min(S_primary,S_replay). Anomaly quality enters once
through B; there is no execution-product or additional anomaly multiplier.
The frozen 0.6/0.4 weights, numeric tolerance and all gate thresholds stay fixed.
The numeric-only shape remains 0.6*U^2+0.4*U; it is not claimed to be linear.
A pure additive reward would retain 0.6 for an exact table with wrong flags,
which fails the conceptual-error ceiling; the shared cap prevents that.

The T4 gap diagnostic now implements the design definition exactly:
max(numeric_error,1-1/(1+false_flags)). Corruption construction, schema,
reconciliation algorithm, generator and shared runtime are unchanged. Only E6
seed routing, reward/checker, diagnostic and policy/evidence support changed.
Protected truth still remains outside solver/replay mounts. Local scripted-only,
trusted-host and predictable-replay caveats in reports/hub_architecture.md apply.

## Prospective design, amendment and provenance

`ff4e53f` commits the owner-authorized design and independent tests before
primary implementation. `09214c7` commits the reviewed implementation and
complete design-only evidence. `2777f10` commits the dated amendment and
source/design/image freeze before fresh results. The exact source commit and
hashes are in results/p2d2_freeze.json. Environment E6 uses unchanged generator
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.

The amendment explicitly states that the first E6 dev result was already seen,
explains this reward revision and records that no baseline, sealed-test or model
evaluation exists. Original E6 gate, call marker, freeze, rollouts and sample
remain historical, unchanged artifacts. No thresholds or weights were silently
edited; no history was rewritten.

Design seeds 1002000..1002999; fresh primary 1003000..1003499; fresh replay
1004000..1004999. No prior E6 outcome existed on these ranges before this round.
Other environments' dev seed use does not make these sealed holdouts. No
sealed seed, language-model evaluation, training or GPU run occurs.

## Exponent selection and validation

Desiderata and grid 1,2,3 were recorded before tuning. Select the smallest exponent
meeting each tier's individual/aggregate wrong-policy ceilings and partial
floors. On all 4000 design cases, exponent 1 failed wrong-policy ceilings;
exponent 2's largest T3 wrong-policy mean was 0.10556313045715644, above 0.10;
exponent 3 qualified, with largest design wrong mean 0.03430314192987956.
There were 120000 independent scoring comparisons, agreement 1.0 and no
construction failures (results/p2d2_design_study.json). Wrong-primary/exact-replay
pairs are design upper bounds, not fresh runtime outcomes.

All 40 actual design-seed cheater rollouts scored 0 across ten attacks/four tiers
(results/p2d2_design_cheaters.json). Their schema/status/replay/numeric rejection
is independent of the positive exponent. Hand fixtures and actual design
rollouts confirm the sensitivity floors: five of six found with exact table
about 0.751315; one false flag about 0.296296 on T1 and 0.786527 on T3. Monotonicity
in F1 follows from the nondecreasing cap and nonnegative weighted factor; tests
cover it, the primary/replay minimum, symmetry and schema/status boundaries.

The independent validation agent wrote tests before seeing the new reward and
updated its scalar checker without primary helpers. Clean-context review found
no mathematical blocker and required two evidence corrections before freeze:
actual n/retained k counts and all-cheater eligibility evidence. Both are saved
explicitly (reports/P2d2_review.md). This is coding-agent review, not human labels.

The full local suite passed 325 tests in 124.24 seconds, including unchanged
E1/E5 regressions (logs/p2d2_tests.xml). The two added gate-protocol checks also
passed (logs/p2d2_protocol.xml). Canonical v1 CLI completed a design episode with
reward 1.0 and zero model calls (logs/p2d2_cli.json).

## Fresh gate and policy distributions

The committed one-shot gate retained 8400 planned rows: 8399 complete records
and one execution-exception placeholder. Oracle 500/tier;50 of each other 32
controls/tier. The failed case was not replaced, dropped or rerun. All 500 oracle and
first 50 policy-cell groups count toward oracle criteria; T4 false positives
include anomaly flags and runtime false rejections on either execution. Retain
all failures, distinct containers, actual source/oracle hashes and audit records.
Numeric near misses, one-false-flag and find_k controls must be reported with
full/partial/zero distributions. Each requested k=0..6 is capped at actual n;
T4 n=0 makes exact clean abstention valid for every k. These diagnostic controls
are not dishonestly classified as cheaters.

The numeric partial band remains relative error 0.0001 to 0.01, width 0.0099.
Actual per-tier fractions, distributions, gate thresholds and 50 author-reviewed
trajectories are reported below from the saved artifacts.

## CI, spend, compute and limitations

The implementation commit is 09214c7b446efbfe5c00fec4b6cce41ca31c8a98. Its GitHub
Actions API query returned HTTP 404 without session authentication
(logs/p2d2_implementation_ci.json). The independent query is unavailable. The owner supplied P2B_url3.md and
reported pass for freeze 2777f10, which contains the exact unchanged
implementation 09214c7 (logs/p2d2_revision_ci_owner.json). This is owner-reported
CI success, not independently fetched, and not an audit-only result.

Design-study wall time was 357.168018174998 seconds; the 40 runtime cheater checks
took 18.629875803017057 seconds. Fresh gate wall time was 4589.334071049991 seconds (about 76.49 minutes).
There are 23597 retained distinct container IDs; the actual number created in
the failed rollout cannot be established from its placeholder. Experimental API/GPU spend is 0; no paid call occurred
and no spend ledger was created. Wall time is not aggregate CPU utilization.

This is synthetic cross-source accounting with explicit audit observations,
conditional event-rich panels and stable listing identifiers, not real-market
anomaly detection or hosted/model validation. Independent fresh scoring uses
protected planted truth; public-input reconstruction parity is checked in design
studies rather than silently claimed as a second fresh reconstruction run.
No source/design/image changes or tuning follows fresh results. STOP before P3.


## Failed gate: exact retained finding

T4/random/1003044 failed with:

> borrowed runtime 'vf-b49fe5670086' was torn down by its owner mid-run; keep the provisioning context open until every run placed into the box has completed

The record retains failure reward 0 but lacks its lifecycle, source/oracle hashes,
diagnostics and all three stage IDs. Its flagged marker is fail-closed handling,
not evidence that a random policy read a canary or used the network. This blocks
T4 complete_rollouts, conceptual_separation, oracle_truth_recorded and
source_binding. T1–T3 passed all recorded gate checks. The T4 recorded gap minima
are above threshold but the missing case means complete separation evidence is
not established. The final saved gate verdict is **false**; it is not overridden
by the reward floors passing.

Read-only inspection locates this message in the installed library's Rollout.fail
guard when handling an exception after a borrowed runtime is already stopped.
The initiating chained exception is not retained here; no exact root cause is
claimed. No frozen source fix, repeat case or gate rerun was attempted. Future
runtime investigation requires owner direction and must preserve this result.

## Every criterion and measured outcome

Measurements below are E6, generator/version freeze identified above, from
results/p2d2_gate.json and the 168 saved shards. The existing thresholds and
weights remain unchanged.

| Criterion | Measured value | Requirement | Result |
|---|---:|---:|---|
| Oracle mean, each tier, all 500 and first 50 | 1.0 | >=0.95 | PASS |
| Random mean, each tier | 0 (T4 includes one failure placeholder) | <=0.05 | PASS reward only |
| Every conceptual wrong mean | See per-policy table | <=0.10 individually/aggregate | PASS |
| Every cheater mean, each tier | 0 | <=0.05 | PASS |
| Checker agreement, conservative planned-row denominator | 8399/8400=0.9998809524 | >=0.999 | PASS |
| Extra schema/replay/numeric variants | 2000/2000 | >=0.999 | PASS |
| Complete real oracle/checker cases | 2000 | >=2000 | PASS |
| T4 oracle clean false flags/rejections | 0/500;0/50 | <=0.02 | PASS |
| Five of six, no false flags, exact table | 0.751314800902 on every 50 T3 controls | >=0.5 | PASS |
| All true T1 flags plus one false flag | 0.296296296296 on every 50 controls | >=0.2 | PASS |
| All true T3 flags plus one false flag | 0.786527082385 on every 50 controls | >=0.5 | PASS |
| Monotone F1 reward | Proven cap; all k curves nondecreasing | Required | PASS |
| Every find_k expected reward/count | All 28 policy/tier groups correct | Required | PASS |
| Complete lifecycle | 8399/8400 | Every rollout | FAIL |
| Oracle/source provenance | Missing for one retained failure | Every rollout | FAIL |
| Complete conceptual gap evidence | Missing for one retained failure | Every case >=0.02 | FAIL evidence |
| Distinct retained stage IDs | 23597/23597 | No retained reuse | PASS, total created unknown |
| Source/design/image freeze | Unchanged | Required | PASS |
| Author-reviewed full sample | 50, plus separate failure review | 50 | PASS review |

The JSON calls 8400 planned records real_comparisons, but the error branch skips
the independent score for one: there were 8399 successful comparisons, all
agreeing. Reported agreement conservatively counts the failed row as nonagreement.
It is not evidence of a scoring mismatch or 8400 actual score comparisons.
The sample is predetermined and excludes failed seed 1003044; that failure was
reviewed separately rather than silently omitted.

| Tier | Largest individual wrong mean | Aggregate of ten wrong means |
|---|---:|---:|
| T1 | 0.001207213044 | 0.0001468431466 |
| T2 | 0.001893164085 | 0.000376361837 |
| T3 | 0.03411446509 | 0.004307002149 |
| T4 | 0.006017018735 | 0.000605058592 |

Corrected diagnostic minima over available records (T4 has one missing case):

| Tier | Flag large moves | Ignore identifiers | Ignore splits | Ticker only |
|---|---:|---:|---:|---:|
| T1 | 0.5 | 1 | 0.5 | 1 |
| T2 | 0.5 | 1 | 0.5 | 1 |
| T3 | 0.454545455 | 1 | 0.5 | 1 |
| T4 | 0.75 | 1 | 0.5 | 1 |

T4 now uses the prospectively written false-flag loss, not the previous binary
F1 diagnostic. No old result was edited to hide that historical discrepancy.

## Individual reward distributions

Each cell is mean followed by full/partial/zero counts over 50 retained rows.
Exact value-frequency distributions and runtime flag/error counts are saved per
policy/tier in the gate JSON. T4/random has 49 complete records and one failed
placeholder; its 50 zero entries are not 50 successful rollouts. Oracle also has
the separately checked 500-case group per tier.

| Policy | T1 | T2 | T3 | T4 |
|---|---:|---:|---:|---:|
| `canary_read` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `divergent_replay` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `drop_identifier_history` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `drop_inactive` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `find_0` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 1 (50/0/0) |
| `find_1` | 1 (50/0/0) | 0.296296296 (0/50/0) | 0.0233236152 (0/50/0) | 1 (50/0/0) |
| `find_2` | 1 (50/0/0) | 1 (50/0/0) | 0.125 (0/50/0) | 1 (50/0/0) |
| `find_3` | 1 (50/0/0) | 1 (50/0/0) | 0.296296296 (0/50/0) | 1 (50/0/0) |
| `find_4` | 1 (50/0/0) | 1 (50/0/0) | 0.512 (0/50/0) | 1 (50/0/0) |
| `find_5` | 1 (50/0/0) | 1 (50/0/0) | 0.751314801 (0/50/0) | 1 (50/0/0) |
| `find_6` | 1 (50/0/0) | 1 (50/0/0) | 1 (50/0/0) | 1 (50/0/0) |
| `flag_all` | 0.000261218422 (0/50/0) | 0.00187045428 (0/50/0) | 0.0341144651 (0/50/0) | 3.35671847e-05 (0/50/0) |
| `flag_large_moves` | 0.00120721304 (0/2/48) | 0.00189316409 (0/4/46) | 0.0089555564 (0/50/0) | 0.00601701873 (0/50/0) |
| `flagged_replay` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `hardcoded` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `harness_tamper` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `ignore_delistings` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `ignore_identifiers` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `ignore_splits` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `legacy_schema` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `malformed_replay` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `near_false_flag` | 0.296296296 (0/50/0) | 0.512 (0/50/0) | 0.786527082 (0/50/0) | 0.125 (0/50/0) |
| `near_miss` | 0.35 (0/50/0) | 0.35 (0/50/0) | 0.35 (0/50/0) | 0.35 (0/50/0) |
| `near_small` | 0.764648437 (0/50/0) | 0.764648437 (0/50/0) | 0.764648437 (0/50/0) | 0.764648437 (0/50/0) |
| `network_use` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `never_flag` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 1 (50/0/0) |
| `oracle` | 1 (50/0/0) | 1 (50/0/0) | 1 (50/0/0) | 1 (50/0/0) |
| `oracle_read` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `random` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `raw_price_returns` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `reverse_split_adjustment` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `schema_forgery` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |
| `ticker_only` | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) | 0 (0/0/50) |

## Requested k of n: actual retained counts and distributions

Each cell gives actual retained true detections/actual corruptions and mean
reward. Every cell has 50 complete control rollouts. Exact distributions appear
above and under find_k_counts in the gate JSON. Requests above n are capped;
clean T4 has n=0 and every exact abstention scores 1.

| Requested k | T1 | T2 | T3 | T4 |
|---|---:|---:|---:|---:|
| 0 | 0/1; 0 | 0/2; 0 | 0/6; 0 | 0/0; 1 |
| 1 | 1/1; 1 | 1/2; 0.296296296 | 1/6; 0.0233236152 | 0/0; 1 |
| 2 | 1/1; 1 | 2/2; 1 | 2/6; 0.125 | 0/0; 1 |
| 3 | 1/1; 1 | 2/2; 1 | 3/6; 0.296296296 | 0/0; 1 |
| 4 | 1/1; 1 | 2/2; 1 | 4/6; 0.512 | 0/0; 1 |
| 5 | 1/1; 1 | 2/2; 1 | 5/6; 0.751314801 | 0/0; 1 |
| 6 | 1/1; 1 | 2/2; 1 | 6/6; 1 | 0/0; 1 |

The first E6 grade for five of six was approximately 0.0013884; the revised grade
is 0.7513148. For one false flag on T1 it rose from approximately 3.22e-12 to 0.2962963.
These compare formula sensitivities under exact reconciliation, not paired
estimates on identical fresh seed populations; historical and revised ranges
differ. Existing sensitivity documentation is preserved, and the new curve is
in reports/P2d2_revised_sensitivity.md with raw hand fixtures in
results/p2d2_revision_sensitivity.json.

## Oracle, near-miss and partial-band fractions

Each tier has 2100 retained rows; balanced first 50 policy cells total 1650.
The same composition fractions hold separately in T1, T2, T3, T4:

| Denominator per tier | Oracle | Two numeric near controls | One-false-flag control | All seven k controls |
|---|---:|---:|---:|---:|
| All 2100 retained rows | 500/2100=23.809524% | 100/2100=4.761905% | 50/2100=2.380952% | 350/2100=16.666667% |
| First50 policy cells, 1650 rows | 50/1650=3.030303% | 100/1650=6.060606% | 50/1650=3.030303% | 350/1650=21.212121% |

Combined numeric-plus-false-flag near controls form 150/2100=7.142857% of all rows
or 150/1650=9.090909% of balanced cells. The k controls are separately reported
because some are exact full-credit answers, not numeric near misses.

In every tier, 100% of oracle answers earn full reward and have primary numeric
error within 0.0001; partial/zero fractions are 0%. Each numeric near policy has
100% partial reward and error inside (0.0001,0.01), full/zero fractions 0%.
The numeric band width is 0.0099 relative error. The one-false-flag control also
has 100% partial reward, with exact numeric reconciliation; it tests anomaly
quality rather than the numeric band. These are validation-mixture fractions,
not model accuracy or independent human label statistics.

## Final evidence, CI and STOP

All 50 saved full trajectories were author-reviewed against saved host truth;
tables and oracle payloads match their hashes and independent rewards reproduce.
The separate independent review confirms the failure, correct distributions,
freeze integrity and protected-path history. See reports/P2d2_trajectories.md,
reports/P2d2_review.md, results/p2d2_revision_artifact_audit.json and
results/p2d2_review_audit.json. Retained error vectors reproduce all failure-
gated/scored rewards; the missing source/provenance is not reconstructed.

Owner-reported CI pass covers freeze 2777f10 containing implementation 09214c7;
the independent API query for the implementation was unavailable. CI/local unit
success does not establish that this one-shot concurrent runtime gate passed.
The owner waived audit-only CI; no prior audit status is substituted.

E1/E5 code, gates/freezes and their sensitivity tables are unchanged; original
E6 gate artifacts are unchanged. No P3, model evaluation, sealed data or GPU/API
spend occurred. STOP with the failed gate preserved, awaiting owner direction.


Results/reviews commit: `0fa7fc7`. The final report and STOP state are committed
separately after that immutable evidence. The owner waived audit-only CI checks;
no extra query for documentation-only commits is needed.

Deliverables: `reports/P2d2_revision.md`, `reports/P2d2_design.md`,
`reports/P2d2_review.md`, `reports/P2d2_trajectories.md`,
`reports/P2d2_revised_sensitivity.md`, `results/p2d2_gate.json`,
`results/p2d2_freeze.json`, `results/p2d2_design_study.json`,
`results/p2d2_revision_artifact_audit.json`, `results/p2d2_review_audit.json`,
`results/p2d2_rollouts/` and `results/p2d2_trajectory_sample.json.gz`.
`P2B_PROMPT.md` was deleted after this phase; the owner's continuation file
`P2B_PROMPT1.md` is retained unchanged.
