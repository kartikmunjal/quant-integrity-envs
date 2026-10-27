# P2d clean-context source review

Review scope: E6 task construction, public accounting reconstruction, primary
reward, independent checker, checked v1 lifecycle, scripted policies, design
study and prospective fresh-gate runner. The reviewer read the standing rules,
SPEC, preregistration, amendments, compatibility note, phase prompt and E6 design
before reviewing implementation. This is a source/protocol review, not a fresh
gate result or independent human trajectory label. No fresh E6 seeds, Docker,
network, paid calls or sealed inputs were used by this reviewer.

## Findings requiring correction before freeze

1. `scripts/run_p2d_gate.py:frozen_sources` hashes `reports/P2c_design.md`, but
   omits `reports/P2d_design.md`. The requested E6 design freeze therefore is not
   enforced. Include the P2d design in the exact committed freeze manifest before
   executing fresh cases.
2. `checker.error_terms` accepts `exit_code=False` because `False == 0`; the
   primary explicitly requires an integer and rejects it. A hand fixture with
   one exact reconciled row and clean anomalies gives primary reward zero and
   independent-checker reward one when both exit codes are False. The gate's
   existing `unit_comparison` mode 4 exercises exactly this mismatch, so this is
   an expected gate failure rather than a speculative issue. Align strict
   runtime-record validation and add a hand-derived regression test. The checker
   also omits the primary's answer row/flag count bounds and JSON-string parser;
   define and test the intended checker input contract instead of implying
   general parser agreement from ordinary numeric comparisons.

These findings were communicated to the author before source freeze. The
reviewer did not implement fixes. This document records the reviewed snapshot;
resolution evidence must be added after the author/checker owner responds.

## Accounting and evidence assessment

The new corruption truth is distinct from legitimate generated actions. The
task modifies quote observations and retains independent audit returns, anchors,
registry and corporate actions. Duplicate originals are retained deterministically;
flag lists include unknown IDs as false flags. The reconstruction applies identifier
changes, cumulative splits and explicit task-layer delisting settlements. Full
history rows and anomaly detection are checked on primary and source-dependent
replay inputs. Solver source passes through the shared bounded transfer and
disposable-runtime path; protected truth remains host side. No additional
substantive accounting defect was identified in this review.

The design evidence in `results/p2d_design_study.json` identifies E6 and generator
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.
It records the full design partition without construction failures and independent
scalar reconstruction agreement. Its wrong-policy numbers are explicitly primary
paired with exact-replay upper bounds, not completed runtime gate outcomes. The
initial construction failures remain in `results/p2d_design_study_initial.json`;
the design explains the asset-count revision rather than dropping seeds.

The reward is intentionally severe: max-cell reconciliation error, exponentiated
anomaly F1 and multiplication across both cases compress partial credit. This is
disclosed in the prospective design. Clean abstention receives full credit, and
each false flag decreases reward. The conceptual controls are evaluated separately
and the gate aggregates their means. The proposed reporting includes per-policy
distributions, per-tier fractions and the numeric partial band.

The task is a conditional, small-window accounting exercise using known-good
audit inputs. All listings share a deliberate ticker collision; event-rich asset
selection and unusually large moves make conceptual controls separable. Neither
design-policy results nor this review establishes model difficulty, population
market realism, hosted Hub execution, or training suitability. The existing local
scripted-only Hub caveats remain applicable.

## Protocol status

Do not interpret this review as permission to skip the prospective freeze or rerun
a fresh gate. Correct findings before the source/design/image commit; then retain
all one-shot outcomes. No verifier threshold, frozen generator value or protected
environment was changed by the reviewer. Reviewer API/GPU spend was zero; only
source inspection and one hand-derived local pure-function check were performed.

## Prefreeze resolution review

Reinspection confirms that `frozen_sources` now includes `reports/P2d_design.md`.
The independent checker now requires an exact integer exit code, rejects boolean
and other malformed runtime status values, and enforces the same collection
bounds as the primary. Hand-derived status and collection-bound adversaries were
added to the validation suite; the reviewer reran
`tests/validation/test_e6_p2d.py` successfully after these corrections. The prior
boolean discrepancy is resolved.

The checker module now explicitly documents its parsed-dictionary contract.
Primary runtime parsing rejects malformed raw JSON and duplicate keys before
checker invocation; the checker independently validates parsed structures and
numeric accounting. This scopes the agreement claim appropriately rather than
claiming two independent serialization parsers. Both blocking findings above are
resolved before freeze. The sampling, reward-shape and local-runtime limitations
recorded above remain. This follow-up used source inspection and pure fixture
tests only; no fresh cases, Docker, network or generation were executed.

## Final control-source additions

Inspected the added `raw_price_returns` and `drop_identifier_history` policies.
They express distinct accounting mistakes: treating raw split/delisting price
changes as total returns, and discarding history after an identifier changes.
Together with the existing controls, the source now supplies the BRIEF's minimum
wrong-policy set. The gate discovers this set dynamically and checks each wrong
policy separately as well as its aggregate; no source-level gate-count defect was
found. Completion of the revised design study and full suite remains evidence
for the author to record, rather than an outcome inferred by this review.

The random source now emits deterministic pseudorandom, schema-valid values for
each expected row and a random subset of real quote IDs. This is a meaningful
random-output control, with no oracle reconstruction hidden in its path. Its
fixed PRNG seed gives reproducibility, not independent Monte Carlo estimates.
The added runtime diagnostics cover random, numeric near misses, false flags
and clean versus corrupted abstention on the reserved design seed. Inspection
found no new blocker. The reviewer did not execute those Docker diagnostics or
generate additional markets; earlier sampling and reward limitations remain.

## Host truth provenance addition

Reviewed setup-time persistence of the primary planted truth. Its deterministic
content includes environment, generator hash, seed, tier and complete truth;
the filename derives from the exact serialized bytes. Persistence occurs on the
host before public input is written into the solver, so flagged submissions also
retain provenance. The result and compact rollout records preserve
`oracle_sha256`, including a null field on exceptional rollout records. This
adds no mount or agent-visible oracle data and changes no reward calculation.
No blocker was found in this addition. Private files remain host-side provenance;
public reproducibility still relies on committed source, generator identity and
seed evidence. The reviewer used source inspection only for this follow-up.

## Saved one-shot evidence audit

Reviewed saved E6 evidence only after gate completion. Recomputed counts,
per-policy first-50 distributions/means, sample table hashes, source binding and
frozen-file hashes without generating or reexecuting any episode. Audit output
is `results/p2d_review_audit.json`, identified by E6 and the frozen generator hash
above. All 140 shards contain 7,000 distinct case keys: 2,000 oracle rollouts
and 200 per other policy. Their 19,400 recorded container IDs are all unique;
all present container image IDs match the freeze. No frozen-file mismatch,
source-binding failure, missing primary oracle hash, distribution mismatch or
sample-table hash mismatch was found. All 50 full samples match their compact
primary/replay table hashes and anomaly lists where answers exist.

`results/p2d_gate.json` records oracle mean 1.0 for every tier, including all
500 oracle cases per tier, exceeding the 0.95 floor. All 500 T4 oracle cases
have zero runtime/false-positive flags (rate 0, ceiling 0.02). Random and every
cheater have mean zero (ceiling 0.05). Each of ten wrong-policy means is below
0.10; the largest is T4 flag-large-moves at 0.0000037652931404, so the aggregate
also passes. Numeric near-miss means are approximately 0.175 and 0.6451721191
in every tier; their partial reward is real but intentionally compressed by
the paired product. The relative numeric partial-band width remains 0.0099.
Clean never-flag achieves 1.0, while corrupted never-flag achieves zero.

Saved gate evidence reports 7,000 parsed-answer score comparisons and 2,000
adversarial unit comparisons, both with agreement 1.0 against the independent
checker (required 0.999). This establishes fresh scoring agreement against
protected truth, not independently rerun public reconstruction on fresh inputs.
Independent reconstruction parity is established by the design study, whose
final ten-control evidence records 40,000 comparisons across 4,000 design cases.
The primary author separately performs the required author-reviewed trajectory
review; this hash audit supplies no independent human labels.

Remote CI for `1e40d5812d75a6dd4da20f1c814ad98cade19ece` is owner-reported
passing in `logs/p2d_ci_owner.json`. `logs/p2d_ci.json` records independent access
unavailable with HTTP 404, not an independently verified pass. No new blocker
was identified in the saved evidence. All earlier task and hosting limitations
remain. This audit used no Docker, network, fresh generation or paid execution.

## Post-gate conceptual diagnostic discrepancy

The author identified a genuine mismatch: the written clean-case gap uses
`max(e, 1-1/(1+false_flags))`, whereas frozen case diagnostics use
`max(e, 1-F1)` in every tier. For clean cases, any false flag makes that saved
F1 zero, so saved gaps can overstate the written anomaly loss. This is a
diagnostic-definition error, not a change to numeric reward or scoring agreement.
The raw gate's conceptual-gap values must retain this qualification; they are
not literal measurements of the written clean metric.

Source inspection supports the author's lower-bound argument without new
generation. The required identifier-change window and overlapping shared-ticker
listings force identity/membership errors of one for the corresponding controls.
The split window contains a generated factor from {0.5, 2, 3}, making ignored-split
relative price error at least 0.5. The separate legitimate-large-move decoy
forces at least one false flag for the large-move control, whose written clean
loss is therefore at least 0.5. These structural bounds exceed the required
0.02, conditional on successful frozen case construction, and are not a fresh
independent reconstruction measurement across all oracle cases.

Inspection of the saved T4 first-50 wrong-policy primary records confirms the
same conclusion: identifier/ticker errors have minima one, split error has
minimum 0.5, and the large-move policy has at least three false flags per record.
The author's separate saved-record audit should report the written values and
its sampled scope. Preserve frozen source and original diagnostics; no gate
rerun or retrospective relabelling is justified. The discrepancy limits the
literal diagnostic claim but does not provide evidence that the separation
threshold failed. This follow-up inspected source and saved records only.
