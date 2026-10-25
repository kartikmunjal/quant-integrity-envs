# P2b STOP report: E1 incomplete; gate failed

Date: 2026-10-25. Existing E5/E6 code was untouched; their P2b conversion and P3 were not started.

## Built and committed

- `1734288`: real-sandbox validation contracts before implementation.
- `bbc7563`: concrete Verifiers v1 E1 Task/Taskset, inspected DockerRuntime subclass,
  primary/fresh-seed source execution, as-of restatement oracle, partial numeric
  credit, Dockerfile, runtime schema, tests, E1-only dev gate and CI integration.
- `c142530`: committed measurements, test logs, image/source provenance and independent
  agent review. This report and STATE.md are committed separately.

The tracked tree initially matched this project and was clean; only the owner's
P2B_PROMPT.md was untracked. STATE.md correctly recorded incomplete P2, and the
history and preregistration identified quant-integrity-envs. The initial unchanged
suite passed after installing locked dependencies: **73 passed in 2.09 seconds**.
The final full suite, with actual Docker tests enabled, passed: **80 passed in
27.87 seconds**. See `logs/p2b_session.json`, `logs/p2b_tests.xml` and
`results/p2b_runtime_provenance.json`. CI was configured to run these Docker tests;
remote CI was not run or claimed to pass.

## Measured gates

All numbers below are for **E1**, generator version
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.
Runtime version hash:
`f748a1b690b5615fdccf303115be2586d8f28e91446824b6a8a952aeb7215eec`.
The source is `results/p2b_gate.json`; exact image identity and file hashes are in
`results/p2b_runtime_provenance.json`. Dev seeds only; no baseline or sealed-test
result was computed.

Each tier uses 50 primary cases per policy. Ten plausible wrong policies and five
scripted cheaters are retained, with individual means and reward distributions.

| Criterion | Frozen threshold | T1 | T2 | T3 | T4 |
|---|---|---|---|---|---|
| Oracle mean | >=0.95 | 1.0 PASS | 1.0 PASS | 1.0 PASS | 1.0 PASS |
| Schema-valid random mean | <=0.05 | 0 PASS | 0 PASS | 0 PASS | 0 PASS |
| Wrong-policy aggregate mean | <=0.10 | 0.26 FAIL | 0.16 FAIL | 0.16 FAIL | 0.2608 FAIL |
| Worst individual wrong mean | <=0.10 | 1.0 FAIL | 0.4 FAIL | 0.4 FAIL | 1.0 FAIL |
| Each scripted cheater mean | <=0.05 | 0 PASS | 0 PASS | 0 PASS | 0 PASS |
| Clean false-positive rate | <=0.02 | N/A | N/A | N/A | 0 PASS |

The aggregate agreement check passes: **1.0 over 8,000 comparisons across 2,000
generated cases**, 500 cases per tier, against the >=0.999 threshold. It independently
recomputes numeric truth using scalar asset-major scans. Its scope is limited to
valid unflagged answers with matched primary/replay patterns; it is not broad
schema/tamper/replay agreement certification.

Real boundary tests and the gate record PASS for network none, read-only root
filesystem, no privileged mode, one declared work mount, private oracle path
unreachable, canary detection, harness tamper detection and a failed actual socket
connection. The initial-session canary regression also passes through the actual
Task setup/finalize/score lifecycle. These are tested properties, not a claim of
complete sandbox security.

Overall **FAIL / incomplete**: the wrong-policy criterion fails in every tier.
No threshold was changed, no episode was dropped, and all failures remain in the
committed result. The gate command exited 1 as expected for this finding.

## Partial credit and surprises

For each tier, equal-weight, long-only, annualized-return and reversed-position
answers each have a distribution of **50 rewards at 0.4**, while the oracle has
**50 rewards at 1.0**. Partial credit is therefore demonstrated, but these plausible
mistakes exceed the wrong-policy ceiling. Retaining partial credit and satisfying
that ceiling requires further design work, not threshold relaxation.

Ignoring availability dates earns **1.0 in T1 and T4**, exposing insufficient
availability stress in those case constructions. T2/T3 score that policy at zero.
The independent reviewer also reproduced a pre-existing core exploit: a valid zero
answer asserting availability=True earns 0.2. The new runtime path uses replay
evidence, while the legacy pure core remains unchanged and is not certified.

## Independent review and remaining blockers

An independent reviewer session, `/root/e1_review`, was started as requested.
The initial core exploit was executed by that reviewer; later runtime reviews
were read-only. This is independent agent review, not human agreement labels.
Full findings are in `reports/P2b_review.md`.

Remaining blockers include an inherited untraced read API, source-size enforcement
after transfer, uncertified standard Env/CLI runtime selection, and incomplete
adversarial checker coverage. Bulk gates share public inputs and an interpreter
within a tier/policy batch and attach trusted host evidence before invoking real
Task.score hooks. Separate lifecycle tests exist, but the bulk measurements do
not certify independent complete rollouts for every case. Consequently this phase
does not establish the full real-taskset release boundary requested by the owner.

## Interpretations and compatibility

The installed pinned verifiers wheel does not contain the IsolatedVerifierEnv
claimed in the earlier COMPAT.md. The implementation uses its available Taskset,
Task.score and Runtime APIs instead, and documents that mismatch. Generic CLI
integration is not claimed. Initial host tests needed uv sync --locked; no
preregistration or dependency lock values changed.

The owner explicitly requested work/private directories outside the repository;
those two paths were created with approval and used only for this phase. The sole
bind mount is a unique directory under ~/qi-sandbox, mounted at /work; ~/qi-private
is never mounted. Existing sealed manifests remain untouched. OS, Docker and
observed VM resources are recorded in COMPAT.md; Windows-side configuration was
not inspected. Docker implicit system mounts are distinguished from declared
application mounts. The tracer parent has only SYS_PTRACE/SETUID/SETGID added;
submitted programs run as nobody under no-new-privileges.

Fresh replay seeds are deterministic hashes of seed, tier and source. They differ
from primary seeds, but are predictable and are not a sealed holdout. The runtime
oracle explicitly selects revisions available by cutoff; unlike the legacy core,
it does not silently ignore restatements. Wrong-policy gates are checked both
individually and in aggregate; both interpretations fail, so this choice does not
change the outcome. The owner prompt file was deleted at phase end as requested.

## Spend and compute

From `logs/p2b_session.json` and `results/p2b_gate.json`: **$0 API, $0 GPU**, no paid
calls and no training. Local CPU/Docker gate wall time was **324.510037681 seconds**;
final suite time was 27.87 seconds. Dependency installation and image-build time
were not separately metered. No release/push/publish action was taken.

STOP. P2b remains incomplete and awaiting owner; do not begin E5/E6 conversion or P3.
