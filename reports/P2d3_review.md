# P2d3 independent infrastructure review

2026-10-27. A separate clean-context reviewer session reviewed the prospective
design and tests committed at `ad94d539b9ea94c6c90ba54de1ae4f1a7da461d7`, and the
then-uncommitted `src/qi_runtime/__init__.py` and `infrastructure.py`. The reviewer
did not author the implementation and made no implementation edits. This is an
interim review; it does not approve the fresh gate or certify subsequent edits.

## Blocking findings

1. `CheckedRuntime.run` records a nonzero solver outcome only after an additional
   Docker inspection succeeds. A solver timeout/crash followed by an inspection
   failure becomes retryable infrastructure before policy evidence is recorded.
   Trusted transport errors and solver exits need distinguishable evidence; a
   bare Docker exec status is ambiguous. A controlled regression must demonstrate
   that an established solver timeout/crash plus later daemon failure is never
   retried, while a genuine Docker exec transport failure remains infrastructure.
2. `run_with_retry` returns `complete=False`, `value=None` when policy evidence
   accompanies an exception. It avoids retry, but does not itself retain the
   required completed hard zero. The runner must explicitly retain the policy
   zero and separately report unresolved cleanup/transport failures. Otherwise
   policy-plus-cleanup failures are missing rewards rather than retained zeros.
3. The prospective tests exercise synthetic callables and mocked teardown, but
   do not exercise `Rollout.fail` compatibility. Add controlled tests proving
   original scorer exception retention only after finalized checked-runtime
   removal, preserving the upstream guard during premature shutdown and for
   foreign runtimes. Also prove the actual framework-reported error reaches
   retry classification: a framework that returns an error-bearing Episode
   normally could otherwise be accepted as complete by `run_with_retry`.
4. Unknown host JSON/inspection `ValueError` is caught by the broad execution
   handler and converted to a policy zero. This contradicts the prospective
   unknown-host-error rule. Separate known output-bound failures from parsing or
   scorer bugs, and demonstrate that unknown host failures remain terminal.

## Supported observations and remaining conditions

The reviewed diff changes infrastructure only: no E1/E5/E6 reward, case,
generator, tier, threshold, weight or exponent file changed. Runtime acceptance
can nevertheless affect observed rewards; source equality is not deterministic
replay evidence. The 60-second host deadline and 20-second in-container deadline
are distinct in code. Existing isolation flags, bounded source transfer and
auditing remain present. The teardown lock serializes concurrent removal and
failed removal leaves the runtime unstopped.

The retry ledger uses a fixed planned denominator and integer floor of 0.5%,
with one reservation before the second attempt. The caller must stop launching
new work when the shared batch budget is exhausted; this wrapper does not
enforce batch scheduling. Shared use in a single asyncio event loop has no await
inside reservation. Threaded/multiprocess sharing is not established.

Resource name/ID overlap is rejected between attempts. The wrapper cannot force
its callable to create a fresh Env, Task or workspace and does not record those
identities. The forthcoming runner must establish these properties, source
hashes and complete persisted attempt outcomes, including in-flight and
unstarted work at a budget stop. A synthetic callback test is insufficient
evidence for fresh framework resources.

Exception journals preserve traversed explicit causes, implicit contexts and
exception-group members without truncating long messages, and retain traceback
files and hashes. They do not capture locals or credentials deliberately. The
old initiating failure remains unknown; the lifetime-guard masking hypothesis
is not an established historical root cause.

Reviewer validation: `.venv/bin/python -m pytest
tests/validation/test_p2d3_infrastructure.py -q` passed all 16 collected tests.
No Docker, stress, model, API, GPU, network or sealed evaluation was run by this
reviewer. The test command output was returned to the parent session; the parent
must retain a machine-readable validation log for final numeric reporting.
Generator version remains the preregistered
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`;
these unit tests do not construct generator cases.

Approval remains pending fixes and controlled fault evidence, the six declared
stress batches, full historical per-row determinism comparisons, review of
seed-routing/historical-reward adapters and the runner, and a source/design/image
freeze before any fresh gate result. No new financial semantics are authorized
by this review.

## Second review: runner and adapters, before production stress

The reviewer re-read the revised runtime and new `phase.py`/`experiments.py`.
The broad ValueError conversion is removed. Policy-plus-infrastructure failure
now retains an explicit zero with `complete=False`, correctly keeping an
unresolved rollout from passing a completeness gate. The actual upstream
`Rollout.fail` guard was inspected in the installed pinned package. The narrow
hook changes ownership only during a closed, finalized, scoring-stage checked
runtime whose removal succeeded, then restores ownership. The new guard unit
test invokes the real upstream method and demonstrates original error retention
and continued rejection during premature shutdown. The parent reports three
real runtime controlled-fault tests passed; this reviewer did not rerun Docker.

Reviewer independently ran the infrastructure and phase unit suites: 23 tests
passed, persisted in `logs/p2d3_review_units.xml`. No production experiment was
run by the reviewer.

Remaining blockers before production execution:

1. Every nonzero `docker exec` result is now marked policy before trusted
   inspection. That fixes policy precedence but can misclassify a Docker exec
   transport failure as a solver crash. A healthy container alone does not prove
   that a solver started. Establish a trusted completion/status channel or
   otherwise distinguish daemon/client execution errors from solver return
   codes without matching untrusted stderr. Add a controlled transport failure
   regression as well as the existing solver timeout test.
2. `run_batch` gathers 200 tasks before persisting the group's records. Source
   reconstruction or gate checker/diagnostic exceptions can escape `one`, abort
   gather and lose completed attempt records in that group and the final
   summary. Record these as terminal unknown outcomes with full chains, retain
   in-flight outcomes, and flush evidence on exceptional termination. A source
   mismatch must stop rather than silently use changed source, while still
   retaining all already-computed evidence.
3. The new gate summary does not preserve the prior gate protocol. In
   `scripts/run_p2d2_gate.py`, find-k expectations are tested per rollout; the new
   runner tests means, permitting compensating deviations. Prior per-row
   false-flag partiality, never-flag clean semantics, oracle provenance, source
   binding, and exact complete lifecycle checks are missing. Restore the prior
   criteria and the all-oracle population checks. Report all requested k/n and
   retained-flag distributions, as in the prior runner. Unchanged reward source
   does not authorize weaker gate checks.

Adapter assessment: fresh E6 admission changes one asserted numeric code
constant, leaving bytecode and all other constants unchanged, excludes the
unreserved gap, and changes replay routing only for the new primary range.
Historical routing is preserved outside it. The existing-case byte comparison
currently covers one T4 seed; broaden coverage across tiers and representative
old admission bounds before claiming tested byte invariance. Historical E6
reward source is read from the committed historical freeze, hash checked, and
temporarily installed only into host task scoring; restoration uses `finally`.
No financial source file is edited. Full historical source/reward/routing
equivalence is still an empirical prerequisite, not established by the two
adapter unit tests.

Stress planning cycles policy and tier deterministically but uses one primary
seed per environment. This meets a literal design-seed restriction but gives
limited diversity; report the exact fixed mix and avoid claiming broad seed
coverage. The retry wrapper creates each attempt through a new `run_policy`
call, and tracks/removes checked runtimes before retry. Runtime resource overlap
checks are present; Env/Task/workspace identity evidence remains limited.

The freeze checks current financial/runtime/design files, runtime hash, image,
committed freeze contents and prerequisite pass flags. The phase runner hash is
recorded separately from the runtime hash. Final review and freeze must follow
the corrections above and the planned stress/determinism evidence.

## Requested runner-summary implementation

At the parent's subsequent explicit request, this session authored
`src/qi_runtime/gate_summary.py` after writing prospective tests in
`tests/validation/test_p2d3_gate_summary.py`. Consequently this session is no
longer an independent reviewer of that new summary module. Its implementation
requires review by another session before final approval; the earlier runtime
review remains independent of runtime implementation.

The new summary retains first-50 policy cells and all-500 oracle populations,
every prior per-row criterion, numeric/reward fractions, k/n and retained-flag
counts, source/oracle/lifecycle checks, full checker denominators, and container
uniqueness across all attempts. Missing outcomes retain their denominator and
are reported as missing rewards, never synthesized zeros. A planned-cell count
check additionally prevents absent or extra rows from passing. Runtime/source
freeze validation remains the caller's responsibility.

Six author-written synthetic summary regressions pass, recorded in
`logs/p2d3_gate_summary_units.xml`. They include a complete synthetic protocol
and an all-oracle failure hidden beyond the first fifty, compensating find-k
deviations, missing outcomes, compact anomaly counts, source/lifecycle failure,
and attempt resource reuse. These tests do not generate financial cases or
execute Docker. No experiment or core runtime file was changed by this session.

## Third review: protected solver status and runner durability

Reviewed the subsequent transport fix authored by the independent tests agent.
A trusted root wrapper creates a random directory with mode 0700 on the
container's sticky `/dev/shm`, executes the traced nobody-UID solver, and writes
the real child status there. A separate root reader retrieves/removes the
marker. The solver UID cannot replace or remove that directory under the
sticky parent and cannot access its contents. Thus actual child exits
125/126/127 can remain policy outcomes while an identical Docker transport
exit without a completed marker is infrastructure. This avoids trusting solver
stdout/stderr as a completion marker. The root wrapper is not tracing its own
marker accesses, so the new status channel does not itself trigger the
protected-path audit. Existing container capabilities and mounts are unchanged.

The targeted real-Docker XML `logs/p2d3_transport_runtime_tests.xml` records 35
tests with zero failures/errors/skips, including genuine solver exits and an
injected transport failure. Reviewer independently reran infrastructure/phase
units: 31 passed, one Docker-dependent test skipped, recorded in
`logs/p2d3_review_transport_units.xml`. The reviewer did not execute Docker.

One production blocker remains in the reviewed transport version: `audit(err)`
and `note_policy()` run only after protected status retrieval. A captured
canary/network trace followed by missing status or a failed status read can
therefore raise infrastructure before policy evidence is recorded and trigger
a retry. Record available audit evidence immediately after the first command
returns, before any fallible status retrieval, and test this simultaneous
policy/infrastructure case. Status-channel integrity itself is not the issue.

Runner source reconstruction now occurs inside recorded retry-call boundaries;
compaction and checker errors retain the completed record and are journaled as
terminal orchestration errors. Each returned row is appended immediately and
shards flush in `finally`. This addresses the previously identified ordinary
exception path that lost a 200-case group. Abrupt process termination remains
outside that guarantee; the started call marker must not be treated as a
completed result. Gate-summary implementation is being independently reviewed
by another session; this reviewer cannot independently approve its own module.
Stress/determinism and final freeze remain outstanding production prerequisites.

## Final pre-stress runtime recheck

The final audit-precedence correction now records `audit(err)` and policy
evidence immediately after the traced command returns, before the protected
marker reader. The new canary and network collision regressions demonstrate
one call, no retry, retained zero, and policy evidence despite a failed marker
read. Reviewer reran the infrastructure units: 31 passed and one Docker test
skipped, persisted in `logs/p2d3_review_final_units.xml`.

All runtime/runner blockers identified by this reviewer are resolved in the
current working tree. This clears the infrastructure implementation for the
prospectively specified stress and historical determinism experiments; it does
not approve a fresh gate before those prerequisites and source/design/image
freeze. Parent reports the full suite passed 371 tests in
`logs/p2d3_tests.xml` and orchestration regressions passed 14 tests in
`logs/p2d3_orchestration_tests.xml`. Those were parent-run, not reviewer-run.
The new gate-summary module still requires the separately assigned independent
review because this session authored it. Historical initiating root cause
remains unestablished, and there is no production stress evidence at this
recheck. No production experiment, Docker command or financial-source edit was
performed by this reviewer.
