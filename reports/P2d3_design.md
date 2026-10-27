# P2d round3: prospective infrastructure policy

Written before runtime changes or new experiments. No reward, tier, threshold,
weight, exponent, generator or case-construction change. Preserve every previous
artifact, including the failed8400-row round-two gate. E1/E5/E6 source modules
remain unchanged; infrastructure fixes and execution support live in qi_runtime.

## Failure taxonomy and retry policy, fixed before implementation

A complete rollout may legitimately return a hard zero: tamper/canary/network
violations, solver nonzero/crash, in-container solver timeout or malformed output
are policy outcomes, never retried. Wrong numeric answers are completed outcomes,
not infrastructure exceptions. Never turn a policy failure into a retry by
matching untrusted stdout/stderr wording.

Infrastructure exceptions include trusted Docker provisioning/inspection/daemon
failures, Docker client/host-load deadlines distinct from the solver deadline,
and framework borrowed-runtime lifetime errors. Unknown host/scorer errors are
not automatically retryable; preserve them and fail rather than conceal bugs.
Classification follows the complete exception chain and trusted runtime context.
Policy evidence dominates ambiguous simultaneous infrastructure symptoms.

An infrastructure exception permits exactly one retry of the entire rollout,
using a new Env/Task/workspace and fresh solver/primary/replay container set.
Retain both attempts, full exception chains, statuses, container names/IDs,
source hashes, duration and final outcome. No partial attempt is reused. No
transparent Docker-command retry or source reexecution inside an attempt.
Cleanup is idempotent resource release, not a financial rollout retry.

Retry budget is at most0.5% of the prospectively fixed planned rollouts in each
stress batch and fresh gate, using that fixed denominator while work is running.
This avoids rejecting the first occasional retry solely because few cases have
finished. For5000 planned cases, stop launching new cases after25 retries would
be exceeded; for8400, after42. Finish/record in-flight work, label unstarted work
as unstarted, and STOP/report without reducing the denominator or hiding failures.
Final criterion:100% complete after zero/one infrastructure retry, all policy
hard zeros retained, retry fraction<=0.005. Unknown/second-attempt errors fail.

## Diagnostics and lifecycle hypothesis

The old error is insufficient to identify its initiating cause. Installed
Rollout.fail raises a new lifetime ValueError from the current exception when
its borrowed runtime is already stopped. Project finalizers intentionally stop
the solver before protected scoring, and Env cleanup stops it again. Capture
full chains before this guard, not only the later summarized episode message.
Use context-local attempt evidence; do not dump local variables or credentials.

Regression tests precede implementation: concurrent double-stop removes once;
failed cleanup does not mark an extant container removed; causal exceptions are
persisted without truncation; policy outcomes are not retried; one infrastructure
retry uses disjoint runtime resources; second/unknown errors are terminal; retry
budget cannot exceed its fixed limit. Test the legitimate post-finalize scoring
boundary separately from a genuinely premature runtime shutdown. A narrow
qi_runtime compatibility hook may preserve the original scoring exception only
for a checked, fully removed solver after finalization, while the upstream
lifetime guard remains for live harness/foreign runtimes. Do not claim the old
initiating root cause is established without reproduction/evidence.

Separate the in-container solver deadline (20s, matching the old command limit)
from a larger60s Docker-client/host deadline. A real in-container timeout is a
policy zero; host-client timeout is infrastructure. Preserve UID separation,
network-none/read-only-root/mount/capability limits and source bounds. Serialize
teardown and report non-successful daemon cleanup instead of silently setting
removed state. Capture diagnostics and classify failures without altering reward
functions or ignoring audit failures.

## Stress and deterministic replay

Run at least5000 actual mixed-policy rollouts for each of E1,E5,E6 at concurrency
12, then independently24: six fixed5000-case batches,30000 total. Design seeds
only: E1 historical design1001000..1001999; E5 design1004000..1004999; E6 current
design1002000..1002999. Deterministically cycle tiers, genuine oracle/near/wrong/
cheater controls, with explicit solver crash and timeout probes. No invalid
surrogate replaces a runtime rollout. Record exact mix and seeds before each
batch starts. Report original failures, retry counts/rates, terminal failures,
all exception chains and policy outcomes. Never rerun a completed stress batch
to discard a bad result; a code revision creates a new identified batch only
before the fresh gate, preserving prior evidence.

Determinism compares every stored historical rollout: E1 round2(6400), E5 first
runtime gate(7000), E6 round1(7000). Use the same saved primary seeds, policies,
source bytes/replay routing and each experiment's historical reward definition.
E6 round1 must use its archived F1^32 paired formula in a trusted host replay
context; using the new reward would knowingly confound a runtime regression
with an authorized reward change. Historical code is read from this repository's
git history, never another project. Current reward files are not edited. Compare
exact per-row rewards and retain every difference, never tune rewards to erase
one. Version the fixed runtime by SHA256 of its source files.

## New E6 gate and seed admission

After tests/stress/determinism and clean-context review, commit a runtime/design/
image freeze and dated amendment acknowledging the round2 infrastructure failure
and absence of baseline/sealed/model results. The revised exponent3 reward stays
unchanged. New E6 primary1005000..1005499, replay1006000..1006999,500oracle/tier,
50of each other32 existing controls/tier:8400 independent planned rollouts.

Existing E6 seed guards do not admit5000..6999 and its replay helper chooses the
old range there. Implement a scoped infrastructure replay adapter within
qi_runtime: widen only admission to the owner-authorized dev range and select
6000..6999 replay, without seed translation, data changes or edits to E6 source.
Assert the adapter changes only that guard/routing and that existing-seed public
case bytes remain identical. Historical replay uses its original routing. This
is necessary seed plumbing explicitly authorized by the new phase ranges,
not a change to corruption/window/generator algorithms.

Freeze before any new gate result; run the gate once with the declared one-retry
policy. Retain all attempts and failures, independent checker agreement, all k/n
distributions and50 author-reviewed full trajectories. No gate tuning or partial
replacement. Report CI for the implementation commit if accessible, otherwise
provide its hash to the owner. No model/API/GPU/sealed/training/publication/P3.
Commit/push reports/results, delete P2B_PROMPT2.md and STOP with file names.

## Pre-gate implementation review extension

Before any fresh gate, independent review found an uncovered genuine framework
lifetime-guard origin. Preserve the interrupted first stress development run
(1969 saved complete rows, no retries) and its full console chain; it is not a
completed5000-row stress result. Use a separately named r2 stress suite for the
corrected runtime, never overwrite/relabel the predecessor. Trusted installed
Rollout.open/fail guard origins receive typed infrastructure evidence, while the
public lifetime guard still raises and unknown post-finalize scorer errors remain
unknown. No untrusted error-message matching classifies failures.

Cancellation is terminal and never permits a financial retry, even after prior
infrastructure evidence. Persist the interrupted attempt and cleanup chain,
restore attempt context, flush retained rows and mark unstarted planned rows.
The older interrupted development runner lacked in-flight cancellation capture;
its report explicitly states that limitation rather than inventing evidence.
These additions change infrastructure coverage/evidence only; every financial
rule and the fixed retry threshold remain unchanged.
