# P2b round 2: decomposition and prospective design

Recorded before implementation changes or round-2 gate execution. Scope: E1 only.
Existing results are E1, generator hash
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`,
from `results/p2b_gate.json` and runtime version
`f748a1b690b5615fdccf303115be2586d8f28e91446824b6a8a952aeb7215eec`.

## Required diagnosis of the old reward

The old runtime reward is `0.4*signal_hit + 0.4*return_hit + 0.2*replay_both_hit`.
The last term requires both numbers on replay; it is not independent evidence of
availability discipline. An incorrect algorithm can retain an unchanged signal
mean and receive 0.4 even when its portfolio return is wrong on both seeds.

| Wrong policy | Old term attribution and observed means |
|---|---|
| ignore_availability | T1/T4: both primary hits (0.8) and both replay hits (0.2), total 1.0, because those cutoffs failed to expose unavailable latest observations. T2/T3: neither primary hit nor replay-both hit, total 0. |
| ignore_period_cutoff | T1/T2/T3: 0. T4 aggregate 0.008: one of 50 cases retains one primary hit (0.4/50); the stored aggregate does not identify that hit, so its field must not be invented. No replay credit can yield a 0.4 singleton. |
| ignore_restatements | Both primary numbers differ; replay also fails: 0. |
| use_all_restatements | Both primary numbers differ; replay also fails: 0. |
| ignore_active_universe | No numeric credit; includes failed arithmetic on inactive assets with null returns. These failures must remain recorded, rather than being described as valid numeric wrong answers. |
| equal_weights | Signal mean unchanged: 0.4 correctness credit. Return wrong: 0. Replay-both wrong: 0. Total 0.4 in every tier. |
| long_only | Signal mean unchanged: 0.4. Return and replay-both wrong: 0. Total 0.4. |
| percentage_units | Both primary outputs scaled: no primary or replay credit, total 0. |
| annualize_daily_return | Signal mean unchanged: 0.4. Annualized rather than daily return fails return and replay-both checks: total 0.4. |
| reverse_positions | Signal mean unchanged: 0.4. Reversed return fails return and replay-both checks: total 0.4. |

These statements describe existing logs, not a new experiment. The legacy core
also accepted `availability_discipline=True` as evidence and could award 0.2 to a
schema-valid zero answer. That path must become fail-closed for direct answer
submissions; successful E1 scoring requires protected execution evidence.

## Prospective numeric reward (fixed before any round-2 gate)

Retain frozen weights 0.8 correctness / 0.2 availability discipline and frozen
relative full-credit tolerance `tau=1e-4`. For each output use
`e_k=abs(pred_k-truth_k)/max(abs(truth_k),1e-12)`; combine with `e=max(e_mean,e_return)`.
Set the zero-credit scale **E=0.01** (one percent relative error). Define

- `s(e)=1` for `e<=tau`;
- `s(e)=0` for `e>=E`;
- otherwise `u=(e-tau)/(E-tau)` and `s(e)=1-3*u^2+2*u^3`.

This function is continuous with a continuous first derivative at both endpoints.
Define **`C=s(e_primary)*s(e_fresh_replay)`** and
**`A=C*s(e_fresh_replay)`**, then use the frozen weights **`R=0.8*C+0.2*A`**.
The replay factor is present in both terms so that copying a correct primary
answer cannot retain 0.8 after failing replay. Schema failure, protected-path
access, canary read, harness mutation, runtime failure, absent replay, or evidence
not produced by the checked lifecycle gives zero.
No independently additive credit remains for an unchanged output or a submitted
availability flag. Near-miss errors inside (tau,E) retain smooth partial credit.
Conceptual mistakes at or above one percent on either execution score zero;
individual and aggregate wrong-policy ceilings remain 0.10 without alteration.

## Prospective case construction and split

Only design seeds **1001000..1001999** may inform implementation choices.
Gate seeds are **1002000..1009999**, with primary policy cases 1002000..1002049
per tier and numeric checker cases 1002000..1002499 per tier. Fresh replay seeds
are deterministically derived into 1003000..1009999 and must differ from primary.
No sealed seeds are permitted. The round-2 gate is run once after a committed
freeze of code/design; no changes follow its result.

Task construction may deterministically search dates in a tier-specific candidate
window before emitting a case, rather than accepting the old single cutoff.
The minimum required relative gap between availability-aware and naive outputs
is **0.02**, measured as the maximum component relative error using the same
truth denominators above. This is twice the zero-credit scale and applies to
**every emitted case in every tier**, including clean/decoy T4. Fail construction
explicitly if no candidate can satisfy the rule; never drop a gate episode.
Any additional selection rule or task-level synthetic challenge transformation
must be documented here using design seeds before freezing. The frozen P1 market
generator and preregistration are unchanged. Difficulty tiers retain their
meaning; T4 contains correct as-of data plus harmless decoys, not permission to
ignore availability.

## Execution and validation plan

Write validation tests before implementing the new verifier. All public runtime
read and command APIs must execute as the solver UID under trusted tracing.
Transfer source with a strict byte limit applied while streaming, and check the
size again after transfer; reject symlinks and special files. Carry audit flags
from initial solver setup/execution through scoring. Stop the initial container
before replay; transfer source bytes only. No batch interpreter, cached
`_batch_result`, or caller-supplied reward evidence is allowed. The normal Env
and CLI factory must select this checked path or refuse unsupported runtimes.

Use independent implementations for oracle/scoring checks; include malformed
schemas, nonfinite/huge numbers, flagged primary/replay, divergent replay,
near-tolerance numeric errors, and absent evidence. Record full per-policy/per-tier
statistics and near-miss reward distributions. A new clean-context reviewer must
inspect the implementation before the gate. Failed gates remain failures.

Correct compatibility claims from current official upstream sources only.
Document Hub installation versus execution runtime selection without claiming
that installation alone enforces this custom Docker boundary. No model/API/GPU
run, baseline, publication or next-phase work is authorized here. Commit and push
reports/results at STOP as requested.

### Initial construction implementation choice (design stage, before gate)

Candidate windows are T1 days 190..230, T2 253..293, T3 316..356, T4 379..419.
These overlap the first part of a new reporting period's availability window,
so unavailable latest records can matter even in clean T4. Select the first
candidate with the required 0.02 availability gap. Full raw synthetic tables,
including future rows and revision dates, remain visible; correct as-of filtering
is required. There is no market-generator edit, answer-dependent reward bonus,
or omitted gate seed. A construction failure is an explicit failed episode.

### Design-stage observations and final validation scope

The full 1000-seed design study is in `results/p2b2_design_study.json`: all four
tiers emit cases and satisfy the availability-gap rule. Some other wrong
algorithms occasionally coincide closely with the correct numeric answer (the
study retains these collisions); the joint fresh-replay reward must be measured,
not assumed to reject every conceptual error on every possible input. No
reward-scale or gate threshold was changed after this study.

The active-universe wrong policy now explicitly imputes missing inactive returns
as zero, making it a numeric survivorship mistake rather than an accidental
TypeError. Its source is fixed before the fresh gate. Additional wrong/replay
policies deliberately give correct primary output but divergent, malformed, or
flagged replay. They embed a **public input fingerprint**, not an oracle answer,
and execute as complete independent rollouts. Agreement on those real execution
records is measured separately from pure-function schema/error perturbation unit
checks. No perturbed record is attached to a task as scoring evidence.

The normal v1 `eval` CLI has been exercised on a design seed with no uploads and
no model calls. Only the bundled scripted harness is supported in this phase;
unsupported model/remote harnesses and generic runtime bypasses fail closed.
Every valid rollout creates separate solver, primary-reexecution and replay
containers. A flagged or invalid solver submission may stop before replay and
receive zero, with that absence retained in the record. Source transfer and
runtime read APIs are bounded and traced. Protected directory/name accesses are
reserved and flag the attempt, including relative failed harness writes.

### Tier context and initial-execution status, finalized before gate

The initial source command's nonzero exit is retained as a hard-zero solver
failure, even if later executions might succeed. It is not discarded as harmless
harness status. A dedicated design-seed lifecycle regression checks this.

Tier context now varies without changing any numeric oracle rule: T1 supplies an
explicit single-availability filtering hint; T2 groups vintages by asset in reverse
period order with less guidance; T3 adds valid but non-authoritative summary views
alongside interacting revision/tradability requirements; T4 is explicitly clean,
with harmless newest-first ordering and legitimate future records/revisions as
decoys. These presentation transformations preserve numeric answers and the
minimum availability gap. They are construction choices, not a claim of measured
human/model difficulty separation. All raw market values and frozen generator
parameters remain unchanged.

Checker reward agreement uses an absolute difference at most `1e-8`, fixed before
the gate to allow harmless floating-point evaluation-order differences between
independent implementations. This does not change the preregistered 0.999
agreement requirement or the `1e-4` relative numeric full-credit tolerance.
