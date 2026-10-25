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
