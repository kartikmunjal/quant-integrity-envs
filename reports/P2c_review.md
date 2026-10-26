# Independent clean-context P2c review

Reviewer scope: ordinary numerical, correctness and protocol review of E5 and
the shared E1 runtime extraction. This reviewer did not implement the verifier
or the independent scalar checker. Reviewed the prospective design, standing
rules, phase prompt, implementation, policies, gate, validation tests and Hub
architecture note. Initial source base was `b0f9994d22bed8095dad4d69430aec127fa975ab`
with the ongoing pre-freeze working changes. This report is separate from the
required author-reviewed trajectory sample.

No fresh E5 cases, Docker execution, network/security probes, paid calls, sealed
seeds or E6/P3 work were performed. Selected existing tests used synthetic hand
fixtures and the permitted design partition. The command
`.venv/bin/python -m pytest tests/validation/test_e5_p2c.py tests/validation/test_e5_cases.py tests/test_p2c_protocol.py -q`
completed successfully. This is a source/design review, not certification of
fresh gate outcomes or remote CI.

## Findings sent before freeze

1. Gate coverage: the initial gate computed the oracle mean and clean-control
   false-positive criterion from the first policy-cell subset while conducting
   additional oracle/checker rollouts. Their reward fractions were reported but
   did not determine those criteria. Require the complete oracle coverage for
   the oracle threshold and clean-control criterion; retain subset statistics
   explicitly as policy-cell statistics.
2. Failure reporting: the initial gate used an unguarded minimum over case
   diagnostics. Complete construction failure in a tier could abort reporting
   instead of emitting a failed gate artifact. Empty diagnostics should yield
   explicit unavailable minima and a failed separation criterion.
3. Compact audit evidence: output weight hashes identify the answer but do not
   identify actual transferred source. The initial compactor also removed all
   command statuses and trace hashes. Preserve the transferred source hash and
   bounded command audit records so source/replay/status claims can be checked
   from the compact artifacts. No full arrays are needed for that addition.

These findings were communicated to the implementation author before the source
freeze. Their resolution must be checked in the frozen implementation; they do
not authorize post-result tuning or a gate rerun.

Pre-freeze follow-up inspection: all three findings are addressed in source.
`oracle_checks` now evaluates the complete oracle group and contributes both
the full-group reward check and the T4 full-group false-positive check to gate
success, alongside the policy-cell checks. `minimum_gaps` returns explicit null
values for absent diagnostics while separation fails. Compact stages retain
command exit statuses and trace hashes. E5 hashes the actual bounded source
read; primary and replay execution record the submitted byte hash; the gate
requires matching hashes for every instantiated stage. Prospective unit tests
exercise complete-oracle coverage, absent diagnostics and retained provenance.
This follow-up used source inspection only; it generated no fresh cases or gate
results and made no numeric reward changes. No unresolved blocker from this
review remains before freeze.

## Numerical and content assessment

No additional financial correctness defect was identified. The primary NumPy
calculator and separately implemented scalar checker use full submitted gross
weights, position and trade capacity, zero initial holdings, half-spread and
square-root impact on actual trade sizes, and terminal liquidation charged to
the final session. The holding-period formula uses the mean hypothetical fresh
roundtrip cost of each session's executed portfolio over positive mean gross
PnL. That definition is explicit and should continue to be called a
stationary-edge accounting approximation.

Numeric claims are compared with host-computed values and canonical execution;
full weights are additionally compared with the canonical path. Missing replay,
failed execution, exact-type status failures, malformed/nonfinite answers and
capacity violations receive zero. Coupling prevents an unchanged numeric field
from retaining a large independent component after a material conceptual or
replay mistake. Prospective boundary and partial-credit examples agree with the
implemented formula and independent checker.

The design study saved in `results/p2c_design_study.json` is design evidence,
with frozen-generator provenance, rather than a fresh-runtime gate. The explicit
conditional search for positive gross edge and distinguishable terminal costs
is an accounting-exercise distribution. It supports neither an unbiased
profitability estimate nor general claims about strategy cost sensitivity.

## Execution and public-claim assessment

E1 imports the single shared runtime implementation; E5 does not copy the
runtime. Source inspection shows separate solver/primary/replay provisioning,
solver destruction before protected scoring, and host-side financial metrics.
This review did not revalidate container behavior and makes no security claim.
Existing runtime integration and E1 regression results remain necessary.

The Hub note correctly distinguishes package installation, trusted host
execution and the repository's particular checked Docker boundary. It states
the host-private oracle placement, predictable replay, unsupported model/remote
harnesses, and uncertainties about hosted execution. This reviewer did not
re-fetch the upstream links; current-source verification remains the primary
author's responsibility. Public claims should cite measured frozen artifacts
and avoid describing the local scripted harness as a certified hosted/model
evaluation.

Freeze and fresh-gate execution were pending at review time. Retain the
prospective source/design/image freeze and one-shot marker, record all failed
episodes, and do not change construction or reward after fresh outcomes.

## Partial frozen-gate evidence inspection

Subsequent read-only inspection occurred during the one-shot gate, after freeze
commit `f7122ac90b5b705dc4c032fc7c406532e281c8e2`, implementation
`f730de501ce11f221b716f31be3c46d64402626a`. Only already saved rollout shards,
protocol source, freeze metadata and the existing CI evidence were inspected;
no cases were generated or executed by this reviewer.

At that inspection, `results/p2c_rollouts/T1-oracle-000.json` through
`T1-oracle-009.json` contained the complete T1 oracle group: 500 unique
policy/tier/seed records covering primary seeds 1005000..1005499, mean reward
1.0, and no flagged records. All 1500 recorded solver/primary/replay container IDs
were distinct. Every record had the expected lifecycle, matching source hashes
across stages, and command trace hashes. Recorded replay seeds stayed inside the
reserved replay partition. Recorded primary minimum relative cost gap was
0.08400894155076896, terminal-close gap 0.020010125977462715, and capacity-binding
gap 3.6206077638211234. These figures derive solely from those E5 shards and the
freeze's generator version
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.

This is partial evidence: it establishes neither remaining tiers/policies nor
overall checker agreement or gate success. Compact weights are represented by
hash and shape; this inspection checks accounting/provenance consistency, not
an independent recalculation of absent full weight arrays.

`logs/p2c_ci_owner.json` records a passing remote CI result for the freeze commit
as **owner-reported**, with `independently_fetched: false` and an explicit fetch
limitation. Reports must preserve that distinction and must not call this an
independently verified CI pass. No further reporting discrepancy was identified
in the available partial shards.

## Final saved-evidence review

After gate completion, this reviewer inspected only saved JSON/gzip artifacts
and frozen-source bytes. No new cases, execution, evaluation, mutation or gate
rerun occurred. The provenance is the same E5 implementation/freeze/generator
identified above, with complete evidence in `results/p2c_gate.json`,
`results/p2c_rollouts/` and `results/p2c_trajectory_sample.json.gz`.

The 140 shards contain 7000 unique tier/policy/seed records in 104 policy-tier
groups. Each tier has 500 oracle rollouts and 50 for each remaining policy.
Recomputed first-policy-cell means, flag counts and complete reward
distributions match the summary for every group. All 2000 oracle rewards equal
1.0; random, every individual conceptual-wrong policy, and every cheater reward
equal zero. Both near-miss policies receive partial credit throughout, within
floating-point roundoff of 0.125 and 0.175 respectively. Thus the oracle
criterion is satisfied using all oracle episodes, not merely the policy-cell
subset. T4 false-positive rate is zero both in its first 50 oracle records and
in its complete 500-record oracle group.

All 19400 recorded instantiated container IDs are distinct. Every record has
the expected lifecycle and matching source hashes across instantiated stages;
all recorded container images match the freeze. Primary and recorded replay
seeds remain in their prescribed partitions. Every frozen file hash still
matches, and the result's embedded freeze equals the saved freeze. Missing
primary/replay stages for flagged solver failures explain why container count
is below three times rollout count; these are retained zero-reward episodes.
Recorded case-separation minima reproduce from the shards and exceed the
prospective requirements in every tier.

The gate reports 7000 real checker comparisons and 2000 unit comparisons, both
with agreement 1.0 and no execution failures. This reviewer verified summary
and compact-record consistency, not a second execution or financial
recalculation of every compact record. The 50 saved full sample records match
their corresponding compact rewards, and full submitted weight arrays hash to
the compact weight hashes. The primary author separately performs the required
author-reviewed trajectory review; at this inspection the gzip label still
said `author-reviewed sample pending`, so its completion should be documented
in the author's review artifact.

Per-tier composition is consistent: oracle episodes form 500/1750 of all
rollouts and near misses 100/1750; in equal-sized policy-cell subsets the
corresponding fractions are 1/26 and 2/26. Oracle rewards are entirely full
credit, both near-miss policies entirely partial credit, and the remaining
policies entirely zero credit. This describes the fixed scripted plan, not a
model's accuracy. The recorded partial-error band remains 0.0099 relative error.

The saved gate reports `passed: true`, elapsed time
3614.802695737002 seconds, and API/GPU spend zero. Those values are gate-log
evidence, not a separate resource measurement by this reviewer. No unresolved
reporting or accounting discrepancy was found. Remote CI remains an
owner-reported pass with the previously stated independent-fetch limitation.
