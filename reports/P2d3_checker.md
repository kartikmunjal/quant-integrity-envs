# P2d3 independent summary and evidence review

Reviewed 2026-10-27 in a separate agent context from the authors of the new
summary and runner. Scope: infrastructure only; no financial source or runtime
edits, production experiment, fresh gate, model call, or sealed-seed computation.
Repository HEAD during review: `ad94d539b9ea94c6c90ba54de1ae4f1a7da461d7`;
new infrastructure files were uncommitted and are identified by the final phase
implementation commit. E1/E5/E6 use generator version
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.

Compared `src/qi_runtime/gate_summary.py` and the gate orchestration in
`src/qi_runtime/experiments.py` against `scripts/run_p2d2_gate.py`, the current
prompt, prospective design, and their validation tests. This is an infrastructure
review, not an independent human trajectory label or a completed experiment.

The summary retains the previous financial protocol: first-fifty policy cells,
all five hundred oracle episodes per tier, frozen preregistered thresholds,
individual and aggregate wrong-policy ceilings, cheaters, every-row find-k
expected rewards, five-of-six and false-flag floors, partial near misses,
never-flag clean semantics, conceptual gaps, lifecycle completion, oracle hashes,
source binding, and both T4 false-positive populations. Real checker agreement
uses all planned rows as denominator; missing outcomes cannot improve agreement.
Unit checker count/agreement and oracle count remain explicit. Container checks
cover distinct stages, cross-row reuse and cross-attempt reuse while allowing
repeated lifecycle events for one container. Exact cell counts are additionally
required. Incomplete outcomes retain missing rewards and a fixed denominator;
they are not fabricated numeric zeros and prevent gate passage.

Source-construction exceptions go through attempt handling and full exception
journaling; post-rollout checker exceptions retain the completed value and
attempt resources. Full cause/context chains are traversed, including suppressed
context and exception groups, and traceback bytes are split into bounded files
without truncation. Unknown failures remain terminal. An initial review concern
was that compaction could throw before attaching completed attempt evidence.
The author fixed that path and added a regression before production experiments.
Reinspection and a synthetic non-serializable-answer probe confirmed attempt
retention after the fix. Failed compaction retains attempts and full exception,
with value absent when it cannot be compacted.

Validation: `tests/validation/test_p2d3_experiments.py` and
`tests/validation/test_p2d3_gate_summary.py`: **12 passed**, recorded in
`logs/p2d3_checker_units.xml`. Fixtures cover compensating per-row deviations,
missing rewards, container reuse, repeated create/remove events, source/lifecycle
failures, first-fifty versus all-oracle checks, source/checker exceptions and
compaction failures and end-of-gate source mutation. The synthetic probe used a fake task and no container.
API/GPU spend for this review was zero; only local Python tests were run.

A second review concern was end-of-run source integrity: the old gate rechecked
frozen source hashes after all rollouts, while the initial new runner checked
only before starting. The author added an initial/end source-map comparison
that enters the final pass decision; the immutable image constant and runtime
source are included in that source map. I added independent synthetic regressions
for unchanged and mutated source maps. Both pass: the mutated case fails the gate
while retaining every completed attempt and trajectory sample. The initial full
freeze check remains before production launch. No unresolved protocol-parity
blocker was found within this review scope.

Durability limits: this review establishes exception-path retention under the
listed fixtures, not power-loss recovery. Shards buffer completed rows until
flushing; abrupt process/host loss is not certified as lossless. No claim about
the initiating historical teardown root cause follows from these tests.
