# AMENDMENTS.md

Dated changes to frozen values. Each entry: date, what changed, why, commit hash, attestation that no sealed-test or baseline result had been seen.

| Date | Change | Why | Commit | Attestation |
|---|---|---|---|---|
| 2026-10-21 | Set `generator.version_hash` from `null` to `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`. | Expected P1 fill after implementing and hashing `src/qi/gen/`. | `8367496cf88d252e00665133a0650bf591314a82` | No sealed-test result or baseline result had been seen; P1 diagnostics used dev seeds only. |
| 2026-10-21 | Replace the factor-structure diagnostic criterion of top-three eigenvalue share >= 0.30 on every seed with an across-seed median >= 0.30 and a per-seed floor >= 0.15. | Made after seeing diagnostics on 200 dev seeds: 33 failed the old per-seed criterion and the observed minimum was 0.196. The original criterion confounded sample-specific factor-strength variation with the generator's aggregate factor structure; the amended criterion retains both an aggregate target and a catastrophic per-seed floor. Generator data-producing code and all other diagnostic criteria are unchanged. | `70230db` | This amendment was made after seeing the stated 200-seed dev diagnostic result. No environment, verifier, baseline, or sealed-test result exists or had been seen. |

| 2026-10-27 (UTC) | Revise E6 combination to min of per-execution min(U,A)*(0.6*U+0.4), with A=F1^3 on corrupt cases and (1+false_flags)^(-3) on clean cases; correct the T4 clean-gap diagnostic; reserve E6 round-two design/primary/replay dev ranges 1002000..1002999 / 1003000..1003499 / 1004000..1004999. Frozen weights, thresholds, tolerance and generator remain unchanged; E1/E5 are unchanged. | Owner-authorized P2d round2 follows the first E6 gate result and the sensitivity audit: repeated anomaly-quality multiplication excessively suppressed near-correct answers. The prospective modest exponent grid selected3 using design seeds only. | `09214c7b446efbfe5c00fec4b6cce41ca31c8a98` | The first E6 dev gate and the documented design studies had been seen. No baseline, sealed-test or model-evaluation result exists or had been seen when this amendment was made. No model API or GPU run occurred. |

| 2026-10-28 (UTC) | P2d3 changes shared runtime infrastructure only: full causal exception journals, serialized cleanup, separate solver/host deadlines, at most one whole-rollout infrastructure retry in fresh containers, a fixed 0.5% retry ceiling, and a global one-shot gate reservation. Reserve E6 round-three primary 1005000..1005499 and replay 1006000..1006999 through seed-admission plumbing. E1/E5/E6 rewards, tiers, thresholds, weights, exponents, case-construction algorithms and the generator are unchanged. | The round-two E6 gate failed on one incomplete infrastructure rollout, T4/random/1003044. Its initiating cause was not retained; the guard-masking mechanism is reproduced, but that old initiating cause remains unknown. Preserve the failed round-two artifact and all development evidence. The fixed runtime completed 30000 design stress rollouts and 20400 exact historical reward/replay comparisons before this new fresh gate. | `4a381f28d00632acea36703121351326586b1cb9` (final orchestration); `1b7234f0bb45893a69c7ef50be7ae7b2ebfadd6e` (core runtime) | Prior scripted dev gates and the documented P2d3 runtime validation results had been seen. No baseline, sealed-test or model-evaluation result exists or had been seen when this amendment was made. No project model API or GPU run occurred. No fresh P2d3 E6 gate result had been seen. |

## 2026-10-28 — P3a shallow-detector diagnostic and bounded evidence storage

Prospective design commit: `452ae0d` (following milestone `030cff9`). Add a
context-insensitive shallow source detector to E2 validation, with mean reward
ceiling **0.30 separately on T2 and T3**. Exceeding it fails the design and
requires better decoys/realizations before freeze; the ceiling cannot be raised.
This diagnostic checks shortcut susceptibility of the mutation catalogue. It
changes no frozen threshold, family, tier, generator value or financial reward
weight. P3a tracked evidence is limited to 32 MiB, compressed shards to 512 KiB,
and local raw evidence to 2 GiB, with committed SHA256 manifests; historical
artifacts remain untouched. These additions were stated in the committed design
before mutation effects or reward measurements. No sealed-test result, model
baseline result, model training result or paid API/GPU result has been seen.
Only synthetic dev-seed scripted validation is authorized in this phase.

## 2026-10-28 — P3a development admission/control correction, before freeze

Evidence: implementation `1ed18e553f45d818d4ac5bbbd41234ce2ff9c6c0`, failed
policy iteration `results/p3a-policy-design-v1.json`, full rejected-candidate
record `results/p3a_design_admission_failure_1000776.json`. A clean replay was
unnecessarily required to support all twelve effective mutations simultaneously.
The dated design revision retains the same seed and32 candidates, prefers the
all-effective candidate, otherwise ranks by eligible-family/operator coverage,
and plants only individually/conditionally effective mutations at unchanged0.05
floors. Inactive operators remain rejected and are never counted as killed.
Also replace the falsely named fixed-invalid `random` control with the declared
uniform4096-subset public-grammar random policy before its first measurement.
Keep all earlier evidence, rerun affected studies under new source hashes, and
bind freeze prerequisites to actual semantic sources and manifests. No frozen
threshold, weight, generator code/config, tier or held-out family changes. No
sealed-test/model-baseline/training or paid API/GPU result has been seen.

## 2026-10-28 — P3a public-contract clarification, development only

Source/evidence commit `a64a20e8bffcf0f2ac02309efa594f1593d373c8`; independent
public-contract tests committed first in `4b9bde64011b0326fad1eb3cc042ac4f68de82ee`.
V2 scripted validation passed, but review found public instructions ambiguous
about fundamental tuple indices and signal/fill clocks. Add a uniform explicit
field/equation/timing legend, independently crosschecked against the existing
clean reference. No instance truth or planted locations are exposed. Preserve
all v2 evidence and repeat affected source-bound studies asv3 before any fresh
gate. Public hash-derived random samples change with the clarified input; their
sampling distribution is unchanged and no draw is selected by reward. This is
interface metadata only: no frozen generator code/config/range, threshold,
weight, tier, held-out family, seed partition or research equation changes.
Scripted dev validation has been seen and is named above; no sealed-test result,
preregistered model-baseline result, training result or paid API/GPU result has
been seen. No frozen preregistration value is amended by this clarification.
