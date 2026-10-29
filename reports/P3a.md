# P3a — FAILED completion gate; STOP

The mutation engine and E2 are implemented, but **P3a did not pass**. The frozen fresh gate completed5657 of8200 planned rollouts, retained one terminal failure, and left2542 unexecuted. The global marker remains consumed. No source fix, threshold change, episode replacement or fresh rerun followed the result. M1 is not reached and no next phase begins.

All E2 numbers below use generator `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921` and the exact shared-runtime/image hashes recorded below. Full-suite counts cover the repository, including E1/E2/E5/E6.

## Commits and primary evidence

| Item | Commit / artifact |
|---|---|
| Milestones, committed before P3a | `030cff9b448fbbde18b8d29c7f32283e306feb7f` |
| Prospective design, before code | `452ae0d` — [design](P3a_design.md) |
| Final implementation | `d0eecc88b005d14ddec3a6a2f09a22881fb35e8c` |
| Committed and pushed freeze before fresh execution | `6240b8f2b5048d6f9a2613a2389b9cf757a7c4c4` — [freeze](../results/p3a_freeze.json) |
| Fresh result / independent audit | [summary](../results/p3a-gate.json), [audit](../results/p3a_gate_audit.json), [review](P3a_gate_review.md) |
| Once guard / actual launch | [consumed marker](../logs/p3a_gate_calls.json), [launch argv](../logs/p3a_gate_launch.json) |

Exact shared runtime hash: `5ac8cf100aabc4d4b47f38fe8ecc4a34fe4db1c77f6042d719c165489769781a`. Image: `sha256:9cc803aaddbbb1a17c9eef928b5438d61769c9c9ba928fc285bc7ee622ad8353`. All40 frozen source hashes still match the committed implementation. The freeze precedes every fresh result.

## Gate criteria and measured outcomes

| Criterion | Measured value | Outcome |
|---|---|---|
| Full fresh population completes | 5657/8200 = 68.987804878%;1 terminal;2542 unexecuted | **FAIL** |
| Retry ceiling <=0.5%, at most one retry per episode | 0 retries; all retained attempt cleanup complete | Limit respected; completion still fails |
| Oracle mean >=0.95,500 per tier | 1.0 in each of T1,T2,T3,T4;2000 completed | PASS |
| Random mean <=0.05,50 per tier | 0.0 in each tier;200 completed | PASS |
| Every wrong policy <=0.10 individually and aggregate | All12*4 cells complete; maximum mean0.02; see tables | PASS |
| Every cheater <=0.05 with full coverage | All observed completed cheater rewards0;543 planned cheater episodes lack completed results | **INCOMPLETE** |
| Shallow mean <=0.30 on fresh T2/T3 | Neither fresh cell reached; development T2=0,T3=0.023255813953488372 | **NOT MEASURED fresh** |
| Independent scalar agreement >=0.999 | 1.000000 on 5657 completed fresh records, including2000 oracle records | PASS observed |
| Clean oracle false-positive rate <=0.02 | 0/500 =0 | PASS |
| All admitted catalogue mutants killed / all decoys clean | Final design1800/1800 mutants and300/300 clean/decoy executions pass | PASS development |
| Real T3 joint/conditional effects and gold restoration | 50 cases,250 actual source executions pass | PASS development |
| Constant/disabled economic functionality <=0.05 | Independent full-schema constant supplement200 cases, maximum reward0 in every tier | PASS development |
| Monotone grading / independent adversarial units | All three predeclared exponents pass independent tests;2000 scalar adversarial records | PASS development |
| Full source-bound suite | 484 passed,0 failures/errors/skips | PASS |
| Independent fresh containers | 20657 distinct recorded stage IDs;20658 distinct IDs including terminal attempt | PASS observed |
| Frozen50-trajectory sample | 38/50 available;12 absent after stop | **INCOMPLETE** |
| Author review evidence | 50 completed diagnostic reviews =38 prospective+12 explicitly retrospective; terminal and unexpected positive also inspected | Completed diagnostics; no substitution for frozen gate |

Evidence: [final mutation](../results/p3a_mutation_design_v3.json), [T3](../results/p3a_interactions_v3.json), [design policies and all exponent sensitivities](../results/p3a-policy-design-v3.json), [full suite](../results/p3a_tests_v3.json), [schema-valid constant supplement](../results/p3a_functional_constant_v3.json), [trajectory reviews](P3a_trajectories.md). Missing cells are not zeros. None of these passing subcriteria overrides the failed completion criterion.

## Terminal failure and stopping behavior

The terminal row is **harness / T2 / seed1001046**. Its solver attempted `open("/opt/qi/harness.py","w")`; the read-only filesystem denied that operation and policy evidence was recorded. A later trusted transfer of solver stdout into `/work/submission.json` hit the60-second Docker client host deadline. The complete cause/context chain contains PolicyFailure, TimeoutError/CancelledError, HostTimeout and HarnessError.

Under the already-frozen collision rule, existing policy evidence takes precedence over infrastructure symptoms. The attempt was therefore terminal policy-classified and not retried. Its62.90606819203822-second attempt cleaned up its container. Other already-in-flight episodes finished and were retained; no additional work was launched after stop became visible. The underlying reason for the Docker host stall is **unknown**. The evidence establishes the failed operation and classification, not a Docker/kernel root cause.

The incomplete row carries conservative zero/incomplete policy metadata but has no valid scalar inputs or completed E2 score. It is excluded from completed-cell means and checker agreement, while counting against completion. It was not silently converted into a successful zero-reward episode. Full records and exception parts are bound by [the gate manifest](../results/p3a-gate_manifest.json).

## Per-tier observed results

| Tier | Oracle n / mean | Random n / mean | Largest wrong-policy mean | Wrong aggregate mean | Completed / attempted |
|---|---|---|---|---|
| T1 | 500 / 1 | 50 / 0 | 0 | 0 | 1450 / 1450 |
| T2 | 500 / 1 | 50 / 0 | 0.02 | 0.00166666666667 | 1407 / 1408 |
| T3 | 500 / 1 | 50 / 0 | 0 | 0 | 1400 / 1400 |
| T4 | 500 / 1 | 50 / 0 | 0 | 0 | 1400 / 1400 |

### Each conceptual wrong policy

Each cell below has50 completed observations.

| Policy | Semantic fault | T1 mean | T2 mean | T3 mean | T4 mean |
|---|---|---:|---:|---:|---:|
| wrong_0 | future_feature | 0 | 0 | 0 | 0 |
| wrong_1 | availability_bypass | 0 | 0 | 0 | 0 |
| wrong_2 | global_center | 0 | 0 | 0 | 0 |
| wrong_3 | global_scale | 0 | 0 | 0 | 0 |
| wrong_4 | unpurged_labels | 0 | 0 | 0 | 0 |
| wrong_5 | selection_overlap | 0 | 0 | 0 | 0 |
| wrong_6 | survivor_filter | 0 | 0 | 0 | 0 |
| wrong_7 | ticker_merge | 0 | 0 | 0 | 0 |
| wrong_8 | same_bar | 0 | 0 | 0 | 0 |
| wrong_9 | submission_fill | 0 | 0 | 0 | 0 |
| wrong_10 | test_selection | 0 | 0.02 | 0 | 0 |
| wrong_11 | uncorrected_trials | 0 | 0 | 0 | 0 |

The evaluation-selection control obtained reward1 once on T2 seed1001008. Its outputs coincided with the clean reference on primary/replay and poison prefix; the selected candidate records its unplanted selection operator as inactive. The verifier correctly does not penalize an operator label independently of outputs. The resulting mean0.02 is below the fixed0.10 gate, but is a finite-check coverage limitation. No verifier change followed this observation. See [additional author inspection](../results/p3a_wrong_policy_positive_review.json).

### Cheaters and unreached controls

Cells show completed n / observed mean, not nominal planned means. Every cell was planned for50.

| Policy | T1 | T2 | T3 | T4 |
|---|---|---|---|---|
| constant | 50 / 0 | 50 / 0 | 50 / 0 | 50 / 0 |
| disabled | 50 / 0 | 50 / 0 | 50 / 0 | 50 / 0 |
| canary | 50 / 0 | 50 / 0 | 50 / 0 | 50 / 0 |
| oracle_read | 50 / 0 | 50 / 0 | 50 / 0 | 50 / 0 |
| harness | 50 / 0 | 49 / 0 | 50 / 0 | 50 / 0 |
| network | 50 / 0 | 8 / 0 | not reached | not reached |
| schema | not reached | not reached | not reached | not reached |
| primary_only | not reached | not reached | not reached | not reached |
| shallow | not reached | not reached | not reached | not reached |
| find_0 | not reached | not reached | not reached | not reached |
| find_1 | not reached | not reached | not reached | not reached |
| find_2 | not reached | not reached | not reached | not reached |
| find_3 | not reached | not reached | not reached | not reached |
| near_1 | not reached | not reached | not reached | not reached |
| near_2 | not reached | not reached | not reached | not reached |
| false_flag | not reached | not reached | not reached | not reached |
| never_report | not reached | not reached | not reached | not reached |
| report_only | not reached | not reached | not reached | not reached |

## Per-family results, including held-out families

Oracle cases may contribute to multiple family rows in T3; counts are not disjoint. T4 is clean and has no planted family. All listed oracle means are1.0.

| Family | T1 cases | T2 cases | T3 cases | Overall minimum admitted effect |
|---|---:|---:|---:|---:|
| F1 | 75 | 88 | 270 | 0.0502866624622 |
| F2 | 86 | 75 | 261 | 0.0533734027377 |
| F3 | 90 | 86 | 264 | 0.0509601634693 |
| F4 | 87 | 90 | 247 | 0.0550753462733 |
| F5 | 87 | 95 | 235 | 0.0511341189686 |
| F6 | 75 | 66 | 223 | 0.0620398991288 |

### Held-out F3 / F4 / F6 reported separately

| Family | Oracle cases containing family | Oracle mean | Minimum effect |
|---|---:|---:|---:|
| F3 | 440 | 1 | 0.0509601634693 |
| F4 | 424 | 1 | 0.0550753462733 |
| F6 | 364 | 1 | 0.0620398991288 |

These are synthetic verifier-validation results, not held-out-family model performance.

## Spend and compute from retained logs

No model-provider or GPU call was made; every phase study records API/GPU spend0. The project spend CSV is absent, as recorded in [scope checks](../logs/p3a_scope_check.json); no external spend is inferred from missing rows. Local scripted Docker CPU execution is the compute used. Job wall times can overlap and are not billed CPU-core seconds.

| Study | Logged wall seconds | Artifact |
|---|---:|---|
| p3a_mutation_design | 140.768290 | [result](../results/p3a_mutation_design.json) |
| p3a_interactions | 45.916100 | [result](../results/p3a_interactions.json) |
| p3a-policy-design-v1 | 332.775664 | [result](../results/p3a-policy-design-v1.json) |
| p3a_mutation_design_v2 | 145.718452 | [result](../results/p3a_mutation_design_v2.json) |
| p3a_interactions_v2 | 42.142295 | [result](../results/p3a_interactions_v2.json) |
| p3a-policy-design-v2 | 1304.524404 | [result](../results/p3a-policy-design-v2.json) |
| p3a_tests | 307.291505 | [result](../results/p3a_tests.json) |
| p3a_functional_constant | 694.612368 | [result](../results/p3a_functional_constant.json) |
| p3a_mutation_design_v3 | 150.188009 | [result](../results/p3a_mutation_design_v3.json) |
| p3a_interactions_v3 | 50.973196 | [result](../results/p3a_interactions_v3.json) |
| p3a-policy-design-v3 | 1297.910191 | [result](../results/p3a-policy-design-v3.json) |
| p3a_tests_v3 | 373.229111 | [result](../results/p3a_tests_v3.json) |
| p3a_functional_constant_v3 | 625.467613 | [result](../results/p3a_functional_constant_v3.json) |
| p3a-gate | 5363.541053 | [result](../results/p3a-gate.json) |

Fresh attempts total64146.341542 overlapping attempt-seconds. The source-bound launch records concurrency12. Initial failed unit/smoke evidence and the earlier468-test suite also remain in logs; the table is the named study ledger, not a fabricated exhaustive CPU billing total.

## Storage and housekeeping

[Before inventory](../logs/p3a_inventory_before.json), [after inventory](../logs/p3a_inventory_after.json) and [housekeeping](../logs/p3a_container_housekeeping.json) record repo/disk use. The housekeeping check queried all20658 exact gate-owned IDs: none remained, so there were no stopped owned containers to remove. The frozen image ID is unchanged. Global system/image/network/build-cache pruning was not used.

Tracked phase evidence is kept within33554432 bytes; compressed tracked shards are <=524288 bytes. The full50 diagnostic packets occupy21526698 compressed bytes. [The global local-artifact manifest](../results/p3a_all_local_manifest.json) hashes every ignored phase file; its626899479 bytes are below2147483648. Raw archives are local-only, not available from GitHub merely because their hashes are committed. Final inventory gives the final worktree evidence count after report construction.


## What was built

`src/qi/mutate/` supplies a synthetic, executable three-strategy research template,
twelve concrete mutations across F1..F6, three AST realizations for every
operator, deterministic variable/layout variation and unrelated refactors.
`envs/e2_leakage_audit/` and `qi-leakage-audit` supply the ordinary verifiers v1
Task/Env/Harness lifecycle, bounded findings-plus-patch submissions, protected
host truth and actual patch execution in separate primary, replay and poisoned
CheckedRuntime containers. The public input now includes a complete normative
field/timing/equation/output contract and the generic family ontology. No
instance-specific family, mutation ID, gold location, effect or case seed is
provided in the solver observation.

A case first tries at most 32 deterministic candidates. It prefers the first
candidate making all twelve operators effective; otherwise it selects among
those same candidates by eligible-family count, eligible-operator count and
first candidate index. It retains all rejections and the requested seed. Only
operators meeting every required 0.05 economic witness floor are planted. T3
also requires three distinct families, numeric joint effect and every
leave-one-out conditional effect at the same floor. A clean replay needs no
active mutant. Inactive operators are rejected, never labelled killed. Wrong
controls remain scored by actual outputs even if an unplanted fault is inactive.

F3 changes label-horizon/purge boundaries, F4 listing identity/membership, and F6
strategy-selection/inference. These are distinct stages from F1 feature
availability, F2 transform estimation and F5 scheduling/fill pricing. Excluded
fold construction removes the held-out mutations, extra family-cued decoys and
ontology label line while preserving correct research rules. No LOFO training,
transfer result or statistical-independence claim is made.

## Reward interpretation

For dirty code, D is matched bug-set F1 raised to the selected exponent and C=1.
For clean code, D=1 and C=(1+false_flags)^(-p). Matching is one-to-one by family
and offending-statement line; duplicates/unmatched claims are false positives.
Patch quality P is 1 through relative error 0.0001, 0 at error >=0.01, with the
predeclared cubic smoothstep between. Exact required shapes/identities and finite
values are required; an incomplete answer does not evade comparison.

The frozen weights enter once in H=1/(0.4/D+0.4/P+0.2/C), with zero if any term
is zero. Final reward is the primary/replay minimum. Causal-prefix poison error
is folded into the one patch-error maximum, not multiplied as another quality.
Poisoning covers future prices/returns and fundamentals unavailable by cutoff;
activity/identifier fields are retained. Partial detection, near-numeric patches
and clean false flags have graded scores. Missing every dirty bug scores zero;
a truthful empty report on clean code is correctly rewarded.

## Interpretations and limits

The scripted oracle is a public-template grammar auditor and general clean
patch, not a model or a general-purpose code-audit result. The random control is
explicitly restricted to the 4096 equally likely semantic fault subsets, with
uniform realizations and independent uniformly sampled findings; its clean
patch probability is 1/4096. This is not chance performance for arbitrary Python.
The shallow control is a deliberately broad context-insensitive detector; low
reward does not establish resistance to every stronger static analysis.

The independent scalar checker has no production grading imports but consumes
observed execution errors. Its agreement is not a separately implemented
financial numerical oracle. Mutation/decoy and T3 source executions independently
check that generated source agrees with the structured host reference.

All reviews are coding-agent reviews. The 50 trajectory reviews are labelled
**author-reviewed**; there are no human labels, human agreement statistics,
model baselines or training results. The environment supports the checked local
scripted v1 architecture. Hosted Hub/model-harness compatibility and real-market
validity are not established.

## Development findings retained

The first implementation's independent review caught superficial realization
wrappers, incorrect F5 stage placement, an unrealized selection boundary and
non-equivalent decoy removal. Those were fixed before fresh validation. Exact
report equivalence also exposed Python float-summation differences; equivalent
report implementations preserve the same summation semantics. An oracle
identifier-normalization bug and source edits beneath a running development
process were diagnosed and retained in development logs.

Policy iteration v1 retained 240 rows and stopped on design replay seed1000776,
where the initial stronger all-twelve-simultaneous admission condition exhausted
32 candidates. The original fixed-invalid "random" control was also disclosed
and replaced before measuring the genuine random distribution. V2 passed all
1280 policy rollouts, but review still blocked the ambiguous public contract.
V3 provides explicit fields, timing, ontology and submission semantics without
changing financial equations, generator/config, thresholds or weights. Earlier
studies remain source-bound historical development evidence, not fresh reruns.

Five oversized JUnit XMLs were mistakenly committed during development. Original
bytes and history remain; bounded summaries replace their oversized current-tree
versions and local compressed originals have SHA256 manifests. The initial
tracked P3a evidence total 32,015,913 bytes was below 33,554,432 bytes; a temporary
all-path total including untracked files was mistakenly called a budget breach
and corrected before any interruption. The per-file-size error was real and is
reported rather than erased from history. Bulky rollout archives were never
committed. Final tracked evidence, ignored archives and disk use are reported
from inventory files; local archive availability is not claimed on GitHub.

## Review and scope

Independent validation tests and scalar checker were written before production
implementation (`1976efc`); runtime tests before runtime implementation
(`3f675be`), strengthened causal/decoy tests before their fixes (`81aca21`), and
public-contract tests before its implementation (`4b9bde6`). The independent
validation session is `/root/p3a_validation`; the separate clean-context reviewer
is `/root/p3a_clean_review`. Author execution and qualitative trajectory review
remain separate from those roles.

Existing E1/E5/E6 source, shared runtime, generator and prereg.yaml remain
unchanged, as recorded in the scope checks. No FROZEN_EVAL marker, sealed metric,
model/API experiment, GPU job, training, E3, P4, P5, M1 packaging, rename or public
release was started. Milestones are definitions and owner choices, not evidence
of completed publication or model performance.


## Final disposition

**STOP — P3a failed its fresh completion gate.** The implementation, development results, partial fresh results, full failure journals,50 qualified diagnostic author reviews and independent post-gate review are retained. The frozen50-case sample and late fresh controls remain incomplete. `P2B_PROMPT3.md` is removed at phase end as instructed. Reports and compact evidence are committed/pushed; raw archives remain ignored with hashes. No M1 packaging, E3 or other phase is started. Await the owner’s next instruction; the consumed marker is not reset.

## Measured final inventory checkpoint

Observed after the gate/reviews, before the report commit (writing this log and committing it add small metadata overhead):

| Measurement | Before | After |
|---|---:|---:|
| .git logical bytes | 76822375 | 62597455 |
| results logical bytes | 356905847 | 384095309 |
| logs logical bytes | 249915669 | 251474896 |
| ignored P3a artifact bytes | 0 | 626899479 |
| Tracked worktree bytes | 608315204 | 612475105 |
| Filesystem available bytes | 1016768229376 | 1015616176128 |

Phase evidence at the checkpoint: 28836252 / 33554432 bytes. Entire repository allocated size: 1907976 KiB; apparent size: 1833085726 bytes. Filesystem totals reflect other activity too and are not a claimed phase-only allocation delta.

After staging the final evidence, [the staged inventory](../logs/p3a_inventory_staged.json) records tracked worktree bytes637269858 and.git logical bytes87193205. The frozen40-source map still matches.
