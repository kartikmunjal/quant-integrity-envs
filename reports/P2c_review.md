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
