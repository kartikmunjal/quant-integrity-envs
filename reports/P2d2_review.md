# P2d2 clean-context pre-freeze review

Reviewed 2026-10-26 in a separate reviewer agent, following the owner continuation
in `P2B_PROMPT1.md`. This is a source/protocol review before the new freeze and
fresh gate, not a claim that the runtime gate has passed. The reviewer did not
implement or modify the verifier. No Docker, network, model, paid call or fresh
case generation was performed for this review.

The working-tree reward and scalar checker both implement
`min(S_primary,S_replay)`, with `S=min(U,A)*(0.6*U+0.4)` and exponent 3 by
default. Dirty A is F1 cubed; clean A is `(1+FP)^-3`. At exact reconciliation
the stage score equals A, including when both executions are imperfect. The
minimum makes the two execution roles symmetric and prevents a stronger replay
from repairing a weak primary. The remaining numeric shape is explicitly stated
in the design. Monotonicity in F1 follows from the nonnegative factor and the
monotone minimum. The hand fixtures exercise mixed numeric/anomaly errors,
execution symmetry, clean penalties, sensitivity floors and boundary cases.

The clean-gap fix uses numeric relative error and direct clean false-flag loss,
independent of the reward exponent. Case construction otherwise retains its
earlier semantics. Round-two primary replay routing stays in 1004000..1004999;
design replay stays in 1002000..1002999 and differs from its primary. The gate
plan uses 500 oracle cases per tier and 50 per other policy/tier, with distinct
round-two artifacts, a committed source/design/image freeze check and exclusive
one-shot call marker. Actual parsed primary/replay records feed the separate
checker; oracle records additionally receive hard-gate perturbations. Failed
rollouts remain failures rather than being dropped. The 50-sample selection
contains distinct tier/policy/index tuples.

Read-only checks found no changes since `c2910b5` in E1/E5 implementation paths
or the original E6 gate, freeze and call-marker files. The new design and
independent prospective fixtures were committed in `ff4e53f` before the current
implementation changes. The full design-study artifact reports 4000 cases,
120000 checker comparisons, agreement 1.0, no failures, eligible exponents [3]
and selection 3. Those are inspected artifact contents, not a new study run by
this reviewer. Generator version remains
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.

Local hand-fixture verification: `.venv/bin/python -m pytest
tests/validation/test_e6_p2d2.py tests/validation/test_e6_p2d.py -q` passed.
No implementation correctness blocker was found in the inspected delta.

Two protocol/reporting items were sent to the implementation agent before
freeze. First, the candidate-study eligibility code evaluates wrong policies
and sensitivity but only one flagged-record rejection assertion for cheaters;
the design promises all cheater checks. Supply separate evidence that every
cheater fails independently of exponent, or include those checks before freeze.
Second, explicitly report corruption count n and actual retained count
min(k,n) for find_k policies, rather than requiring readers to infer them from
the tier and policy name. The final amendment, implementation commit, source
freeze, fresh gate, remote CI status and 50 author-reviewed trajectories remain
the implementation agent's responsibilities. This review does not certify
those subsequent actions.

Reviewer spend: API $0, GPU $0. Compute was limited to source inspection and the
above pure-function pytest run (approximately 0.31 seconds command wall time).

## Pre-freeze follow-up: both review items resolved

Reinspected the updated gate source and
`results/p2d2_design_cheaters.json` before freeze. The artifact contains 40
design-control rollout records: each of the ten attack policies in all four
tiers, all with reward zero. The attack sources fail through runtime/schema
rejection, absent valid replay, or numeric quality zero; these mechanisms do
not depend on the positive anomaly exponent. This supplies the missing
all-cheater evidence without extending the exponent grid. The source freeze
now binds that evidence file.

The gate now records `find_k_counts` separately for each tier and requested k,
including the actual diagnostic corruption-count distribution, retained primary
flag-count distribution and expected `min(k,n)`. Failed records use a missing
label. Sample truth-construction errors preserve the sample with null truth
and an error instead of aborting report generation. Both previously raised
items are resolved; no additional pre-freeze blocker was found. This follow-up
used artifact/source inspection only and did not generate or execute cases.
