# P3b: E3 design preflight blocked

STOP before implementation. E3 (`qi-fdr-adjudication`) was not built, screened, stressed, frozen or gated. The requested all-null construction and per-case separation requirements conflict. No frozen requirement was relaxed to produce a passing result. This is a mathematical preflight failure, not a failed or consumed one-shot gate.

## Work and provenance

Baseline: `2f614c5a8ba06928dbc71bf13153269bde31a93b`. Design and dated amendment committed first at `fa305dfffd5b703c37e58a7aa48111b357e16e6e`. The later report commit contains the independent diagnostic tests, checker, recorded mathematical results, partial seed inventory and this report; its hash is available from `git log -1 -- reports/P3b.md`.

Read [design](../docs/e3_design.md) and [independent feasibility review](../docs/e3_feasibility_review.md). Independent validation author `/root/p3b_validation` reviewed the mathematics and authored the diagnostic tests/checker after the design commit. The proposed implementation author did not edit those tests/checker. No production verifier was authored, so this does not constitute independent validation of an E3 environment.

All phase evidence concerns mathematical fixtures or historical seed records, not environment performance. Generator identity remains `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`; it was not executed. Shared runtime, generator, existing environment sources, historical freezes and thresholds remain unchanged.

## Blocking findings

On required all-null truth, reject-all submits the optimum probability vector. An honest reference cannot beat that optimum by 0.02 on the same constructed case. Identical reports cannot receive different rewards based on policy labels under the requested output score. Giving every all-null report zero also leaves separation zero. This contradiction does not depend on how rare all-null episodes are. Oracle and wrong-policy mean gates alone are not claimed to be contradictory at every possible tier composition.

The requested clipped reject-all-relative normalization also does not preserve strict propriety for the usual continuous finite-endpoint additive proper scores. With eight candidates and complementary half-null truth states, a sufficiently confident deterministic report has higher expected clipped reward than truthful marginal probabilities. The independent diagnostic checker records an exact rational counterexample for the illustrative asymmetric weighted proper loss. Raw loss propriety and the 3:1 Bayes threshold can hold while final reward propriety fails. This is not a universal impossibility theorem for every conceivable nonadditive scoring rule; the all-null separation conflict already blocks the supplied contract independently.

## Gate disposition

| Criterion | Required value | Measured / disposition |
| --- | --- | --- |
| All-null per-case honest vs reject-all gap | >=0.02 | Impossible under proper scoring; at most 0 |
| Raw propriety and 3:1 threshold | Truthful optimum; admit above .75 | Analytic derivation and independent mathematical diagnostics; illustrative rule only |
| Final clipped reward propriety | Strictly proper | Counterexample documented; no rule adopted |
| Oracle, T1/T2/T3/T4 | >=.95 each | NOT RUN |
| Random, T1/T2/T3/T4 | <=.05 each | NOT RUN |
| Each of >=12 wrong policies, each tier | <=.10 | NOT RUN |
| Each of eight cheaters, each tier | <=.05 | NOT RUN |
| Honest reference, each tier | Predeclared justified floor | NOT ADOPTED / NOT RUN |
| Shallow detector, T2/T3 | <=.30 | NOT RUN |
| Independent execution/reward checker | >=.999 agreement | NOT RUN; diagnostic mathematical checker is not this gate |
| Oracle and honest clean false positives | <=.02 | NOT RUN |
| Honest reliability calibration | Design-seed test | NOT RUN |
| Construction admission screen | Before any policy execution | NOT RUN; no admitted/excluded population or rejection count |
| Stress C8 and C12 | 5000 each, zero retries expected | NOT RUN |
| Fixed 50 trajectory author reviews | Selected before freeze | NOT RUN; no trajectories or reviews fabricated |
| Source/design/image freeze and one-shot gate | Committed before gate | NOT CREATED / NOT RUN |
| Independent raw execution reward audit | Stored gate executions | NOT RUN |

No episodes were dropped or seeds rejected. No all-null exception, score, tier frequency, effect parameter, honest floor or E3 seed range was adopted. The dated AMENDMENTS entry records only this preflight disposition and explicitly changes no frozen value.

## Diagnostic validation

The independent [evidence](../results/p3b_preflight_math.json) records 2,100 strict raw-loss grid comparisons and 206/206 exact agreements with the separate mathematical checker. For the K=8 asymmetric weighted-score fixture, truthful expected clipped reward is 221409/250000 (0.885636), below the deterministic report's 9/10 (0.9). These are mathematical fixture values, not policy performance. Reproduction: `.venv/bin/python tests/validation/test_e3_preflight_math.py`; verification: `.venv/bin/python -m pytest tests/validation/test_e3_preflight_math.py -q`. Both tests passed; [JUnit record](../logs/p3b_preflight_junit.xml). Initial use of bare `python` failed because that executable is absent; the independent author also recorded an initial missing-evidence-file test failure before generating the fixture with the repository interpreter. These were tooling/order failures, not hidden E3 rollouts. No full regression suite was run because production code was unchanged.

## Seed review

[Partial inventory](../results/p3b_prior_seed_inventory.json) retains source hashes and observed seeds from one historical shard in each listed prior gate. For example, an E1 shard contains replay seeds spanning 1003042 through 1009938, and an E6 shard contains primary seeds 1008000 through 1008049. These are observed endpoints, not a claim that every intervening integer was used. This establishes that simply choosing the high development partition is unsafe. This partial inventory does not prove that no valid unused subranges exist. An exhaustive inventory and reservation remain required after the scoring contract is resolved. No prior seed routing was changed.

## Interpretations, limitations and next decision

The construction gap was read literally as a per-case requirement applying to each listed wrong policy, including reject-all on required all-null cases. Strict propriety was evaluated separately for the raw rule and its final clipped transform. The owner must specify any intended exception for optimal constant controls and whether propriety applies only to the raw score or also the final reward. Possible alternatives in the design note are proposals, not adopted amendments. No full return-generation design can honestly be called approved yet.

The surprise was that feasibility fails before data generation or execution, despite the earlier phase workflow being usable. Predictable replay, a single synthetic candidate template, scripted rather than model solvability, and local Docker would remain limitations of a future implementation; none has been empirically validated here.

## Spend and compute

[Activity record](../logs/p3b_preflight_activity.json): paid spend $0, model calls 0, GPU calls 0, Docker rollouts 0, sealed evaluations 0. `logs/spend.csv` does not exist; no paid call was made, so no model spend ledger entry is fabricated. Compute was local file inspection and mathematical diagnostics; total session wall time was not metered. At the design-commit snapshot tracked files totalled 681,915,900 bytes and `.git` measured 131,212,278 bytes. These snapshot values exclude subsequent report artifacts and are not final repository-size claims.

The requested prompt file is deleted at completion; owner file P2B_PROMPT1.md is preserved. Commit and push record the blocked work. No next phase begins.

## P3b round 2 — 2026-10-30

**FAIL: development construction and incentive checks. STOP before stress, freeze and the one-shot gate.** The owner’s revised scoring contract resolves the earlier mathematical preflight blockers. This round implemented and tested an E3 prototype, but its fixed construction does not meet the requested control separation. No universal impossibility of the revised contract is claimed. The preflight section above is retained verbatim as historical evidence.

The phase could not validly carry through the remaining stages: 119 of 172 screened design cases fail the required .02 gap; some wrong controls are exactly optimal on both executions; the shallow T2 ceiling and the T1/T4 incentive checks also fail. The adopted design provides no effect/search/correlation tuning after policy measurements. Dropping failed seeds, changing named controls to make them worse, or freezing this invalid construction would not satisfy the prompt. A new prospective construction design is needed; none was silently substituted.

### Built and source identity

Implemented `envs/e3_fdr_adjudication/` (generator-derived cases, host truth/effect records, strict schema/proper raw loss, content-derived presentation IDs, checked execution and ordinary v1 lifecycle), the `qi_fdr_adjudication` plugin/config, construction screen, prospective model calibration, twelve wrong controls, eight cheaters, honest/shallow/random/oracle scripts, and independent mathematical/execution checkers and audits. It remains an uncertified development prototype, not a completed E3 taskset or released package.

Environment: E3 `qi-fdr-adjudication`. Generator: `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`. E3 source fingerprint: `b092ebe7bdad6c8895a3e51bac544e245aed9db910c5ddcdd17fb10efda5a738` (definition/inventory in [activity record](../logs/p3b2_activity.json)). Shared runtime remains `fad402d113ca9e19f082ac45e3e0904edb128b9e672c351fe3a2d62eb699a827` and the immutable local image remains `sha256:9cc803aaddbbb1a17c9eef928b5438d61769c9c9ba928fc285bc7ee622ad8353`. Shared runtime, generator, E1/E2/E5/E6 sources, frozen YAML/thresholds, README and historical freezes are unchanged.

| Milestone | Commit |
| --- | --- |
| Owner-authorized round-two design/amendment | `cef48b1` |
| Independent score/checker tests before score implementation | `dec0e29` |
| Score and fixed construction schedule | `163129a` |
| Independent inactive-asset regression before correction | `b114d41` |
| Active-asset correction | `c0333c7` |
| Diversified null correction, after independent failing regression | `06484ee` |
| Presentation ID tests / implementation | `248c669` / `c635767` |
| Structural populations committed before policy measurement | `8559c86` |
| Honest floors and false-admit ceilings adopted before measurements | `4b8c190` |
| Failed development evidence and fixed smoke plan | `0be0be8` |

The final report/audits commit is identified by `git log -1 -- reports/P3b.md` and the completion message. No source/design/image gate freeze was committed.

### Development measurements, not one-shot gate results

All values below come from 43 screened design primary/replay pairs per tier. Trusted policy-vector calculations on actual synthetic episode data are retained in [design summary](../results/p3b2_design_vectors.json) and hashed gzip shards. They are not container rollouts or a gate of 500/50 episodes. The hardcoded-ID calculation models a fixed primary snapshot and invalid replay; it does not substitute a constant policy. Values are rounded to six decimals.

| Tier | Oracle (>=.95) | Random (<=.05) | Worst wrong (<=.10) | Honest / adopted floor | Shallow | Failed .02 case gaps |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | 1.000000 PASS | 0.000523 PASS | 0.620155 FAIL (`bonferroni_trials_ignore_correlation`) | 0.490569 / 0.42 PASS | 0.596899 no ceiling | 38/43 FAIL |
| T2 | 1.000000 PASS | 0.000000 PASS | 0.534884 FAIL (`top_k`) | 0.502964 / 0.38 PASS | 0.534884 FAIL | 34/43 FAIL |
| T3 | 1.000000 PASS | 0.000000 PASS | 0.273902 FAIL (`bonferroni_trials_ignore_correlation`) | 0.334173 / 0.26 PASS | 0.240310 PASS | 31/43 FAIL |
| T4 | 1.000000 PASS | 0.002984 PASS | 0.390181 FAIL (`bonferroni_trials_ignore_correlation`) | 0.492626 / 0.22 PASS | 0.000000 no ceiling | 16/43 FAIL |

Every wrong control is disclosed below. Each number is a development mean; **F** marks a mean above .10.

| Wrong control | T1 | T2 | T3 | T4 |
| --- | --- | --- | --- | --- |
| `admit_all` | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| `reject_all` | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| `uncorrected_t` | 0.439276 F | 0.020672 | 0.165375 F | 0.005168 |
| `top_k` | 0.596899 F | 0.534884 F | 0.240310 F | 0.000000 |
| `ignore_N` | 0.576032 F | 0.000000 | 0.099857 | 0.000000 |
| `bonferroni_candidates` | 0.509044 F | 0.284238 F | 0.229974 F | 0.121447 F |
| `bonferroni_trials_ignore_correlation` | 0.620155 F | 0.472868 F | 0.273902 F | 0.390181 F |
| `constant_half` | 0.027778 | 0.027778 | 0.027778 | 0.027778 |
| `overconfident` | 0.266150 F | 0.002584 | 0.100775 F | 0.000000 |
| `inverted_ranking` | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| `probability_proportional_N` | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| `hardcoded_ids` | 0.000000 | 0.000000 | 0.000000 | 0.000000 |

[Independent vector audit](../results/p3b2_independent_vector_audit.json) reproduced all 2,752 final policy values, 5,504 stage values and 2,064 gaps from the stored vectors. The independent scalar comparison agreed on 5,332/5,332 valid numerical stage comparisons; the other stages are invalid replay-ID snapshots. These are mathematical comparisons, not the requested full-gate execution checker denominator.

[Exact-optimal-control audit](../results/p3b2_exact_wrong_audit.json) found 32 distinct design cases (50 wrong-policy/case matches) where a named wrong policy reports the exact truth on both executions: T1/T2/T3/T4 counts 16/13/1/2. For example, seed1000000/T1/replay1005276, `bonferroni_trials_ignore_correlation` is exactly correct. Its mathematical reward is1; bounded reward makes the maximum possible honest-minus-control gap0, below.02. Improving the solver alone cannot repair those fixed cases. This proves a defect of this construction, not impossibility of all constructions allowed by the owner.

### Propriety, incentives, calibration and false admits

Raw Beta(4,2) weight is proportional to q^3(1-q), with mode.75. The independent exact grid checks 21 true probabilities by101 reports (2,100 strict inequalities), supported by the analytic derivative (q-p)w(q). Admission cost3(1-p) versus rejection costp gives thresholdp>.75; the endpoint loss ratio itself is not asserted to equal3. Fixed L_ref=3/400 is truth-independent. Constant.5 gives1/36, admit-all/reject-all give0 at K20/r10. The independent quadrature upper bound for uniform reports is.0211930121. Strict propriety is claimed only for raw loss.

The retained exact K8 fixed-reference fixture gives truthful expected clipped reward22101/25000 (.88404), below deterministic9/10 (.9). It documents the reason for the owner’s measured incentive test; it is not a new contract contradiction. The old preflight fixture remains unchanged.

| Tier | Largest transform gain (<=.02) | Honest null false admits / null executions | Adopted honest ceiling | Oracle null false admits | Reliability ECE (descriptive) |
| --- | --- | --- | --- | --- | --- |
| T1 | 0.031836 FAIL | 18/860 = 0.020930 | 0.04 PASS | 0/860 PASS (ceiling.02) | 0.117105 |
| T2 | 0.014250 PASS | 18/860 = 0.020930 | 0.05 PASS | 0/860 PASS (ceiling.02) | 0.103493 |
| T3 | 0.014982 PASS | 22/860 = 0.025581 | 0.06 PASS | 0/860 PASS (ceiling.02) | 0.155344 |
| T4 | 0.094058 FAIL | 6/860 = 0.006977 | 0.04 PASS | 0/860 PASS (ceiling.02) | 0.124496 |

All19 predeclared transforms per tier and ten-bin reliability tables are in [sensitivity evidence](../results/p3b2_sensitivity.json), separately reproduced by [independent sensitivity audit](../results/p3b2_independent_sensitivity_audit.json). Best gain in every tier is the .75 contraction toward1. Approximate-reference miscalibration and the clip/min transformation can both contribute; these measurements do not isolate their causes. No reliability ceiling was invented after observing the results.

Honest floors/false-admit ceilings were adopted before policy measurements from [construction-parameter model calibration](../results/p3b2_model_calibration.json). The normal-effective-max approximation gave a model paired-reward bound; floor is half that bound rounded down.01, null ceiling is model rate+.02 rounded up.01. The model is not a rigorous bound for the actual heavy-tailed correlated returns. Adopted values were never lowered.

### Actual checked smoke and raw-record audit

[Committed smoke plan](../results/p3b2_smoke_plan.json) selects the first design seed1000000, all24 policies and all4 tiers, before execution. All96 full v1 checked Docker rollouts completed at concurrency4 with zero retries. This is an engineering smoke, not C8/C12 stress and not the one-shot gate. Every planned row remains in [smoke summary](../results/p3b2_smoke.json) with a hashed compressed raw record.

| Tier | Smoke rows | Oracle | Worst wrong | Worst cheater | Honest |
| --- | --- | --- | --- | --- | --- |
| T1 | 24 | 1.000000 | 1.000000 | 0.000000 | 0.422922 |
| T2 | 24 | 1.000000 | 0.666667 | 0.000000 | 0.504531 |
| T3 | 24 | 1.000000 | 0.111111 | 0.000000 | 0.058438 |
| T4 | 24 | 1.000000 | 0.444444 | 0.000000 | 0.249032 |

[Independent smoke audit](../results/p3b2_independent_smoke_audit.json) verifies96/96 rewards from raw parsed answers, schema/security/exit evidence and primary/replay minimum, plus source/image/manifest hashes. All232 containers are unique and recorded removed. All eight cheaters score0 in every smoke tier. Primary-only succeeds on primary and fails replay IDs; the honest primary-snapshot wrong control likewise fails replay. Protected canary/oracle/harness/network attacks are flagged at solver stage. The audit does not reconstruct edited source bytes: their transferred hash and observed outputs are retained, while the initial source is stored. This remains a local trusted-host runtime audit, not hosted execution certification.

### Screen and engineering record

| Population | Candidate window | Inspected | Structural successes | Rejected |
| --- | --- | --- | --- | --- |
| design | 1000000..1000099 | 100 | 43 | 57 |
| primary | 1001000..1004999 | 1071 | 500 | 571 |
| replay | 1005000..1009999 | 1115 | 500 | 615 |

Primary inspection stops at1002070; replay at1006114. Uninspected suffixes are neither rejected nor admitted. Populations are disjoint within E3, with cross-environment reuse explicitly owner-authorized. Null fraction over design episodes is a point mass at.5:172 tier cases, each10/20 null. K is fixed20; counts8..19 and other fractions are not certified. Structural screen checks decoy ordering and finite paths only. It did not prove the required policy gaps and must not be called a passed final construction gate. No screened case was dropped after policy measurement.

Failures/fixes retained: v1 inactive-asset NaNs (design0/100, primary4/4000, replay9/5000 structural successes); an independent failing regression preceded the active-asset correction. V2 admitted100/500/500 but its single-asset null noise made the planted portfolio effect weak; a diversified-risk regression failed before switching nulls to static random signed active-universe portfolios. [V1 lossless evidence](../results/p3b2_screen_v1_failed.json.gz), [storage hashes](../results/p3b2_screen_v1_storage.json), [superseded v2 screen](../results/p3b2_screen_v2_superseded.json) and [final structural screen](../results/p3b2_screen.json) are preserved. Seed-derived IDs were then removed from the solver presentation with independently tested identity-only remapping; expensive finite-window generator enumeration remains possible in principle.

Validation separation: independent author `/root/p3b_validation` owns the validation tests, scripted controls, second checker and audits; implementation author did not edit those files. **Ordering deviation:** initial case-generation and runtime-specific implementation existed before their corresponding detailed tests. Raw-score/checker tests preceded score implementation; each inactive-asset/diversification/presentation repair had independent tests before the repair. This is not claimed as perfect compliance with the requested tests-first process.

Full local suite: **664 passed,38 skipped,0 failed/errors** (702 collected),28.571s. The38 Docker-gated tests were skipped in the default local suite; the separately planned96 E3 rollouts actually used checked Docker. [Compact JUnit](../logs/p3b2_full_suite_junit.xml), [original-byte archive metadata](../results/p3b2_junit_storage.json). No full E1/E2/E5/E6 numeric replay regression was run: their financial/runtime sources were unchanged; the shared build metadata only adds the E3 package. CI remains configured for the full suite, but remote CI was not independently queried or claimed passed.

### Remaining phase criteria and disposition

| Required stage/criterion | Result |
| --- | --- |
| Per-case honest vs every wrong gap>=.02 | FAIL development:119/172 cases |
| Every wrong mean<=.10 | FAIL development in all tiers |
| Shallow<=.30 on T2/T3 | FAIL T2; PASS T3 development |
| Incentive gain<=.02 each tier | FAIL T1/T4; PASS T2/T3 development |
| Honest floors, null false admits, raw propriety | PASS measured design checks; not a fresh gate |
| Oracle>=.95, random<=.05, cheaters<=.05, checker>=.999, oracle FP<=.02 at full gate counts | NOT RUN; design/smoke evidence above does not replace it |
| Stress C8/C12,5000 each | NOT RUN — invalid construction prerequisites |
| Source/design/image freeze | NOT CREATED |
| One-shot gate,oracle500/tier,others50/tier | NOT RUN / NOT CONSUMED |
| Fixed50 author-reviewed trajectories before freeze | NOT SELECTED / NOT RUN; no review labels fabricated |
| Independent full-gate raw-record audit | NOT RUN;96 smoke records audited instead |

Interpretations: K20/r10 was chosen inside the permitted ranges to satisfy the fixed-score constant/random controls. “Uniform random<=.05” means expected/mean reward, not every draw. Replay uses the same tier,K,real count,search-count multiset and group/rho construction, with fresh candidate assignments/IDs/returns; it is predictable and not sealed. E3 clean FP means per-null-candidate false admission. Common generating-magnitude metadata is a privileged synthetic-template assumption. No final-score propriety or model-performance claim is made.

A concrete T4 metadata shortcut remains: every N=1 candidate is real under the adopted schedule. The algebraic rule “admit exactly N=1” receives4/9 on T4 by missing the other five real candidates; this is an [exact construction fixture](../results/p3b2_t4_shortcut_fixture.json), not an additional executed policy or gate result. Content-derived IDs remove direct seed-hash inversion, but their visible numerical content still depends on the seed.

Limitations: one synthetic selected-portfolio template, approximate normal selection/correlation model, imperfect reliability, simple policies sometimes optimal, privileged common effect metadata, finite predictable development replay and local scripted Docker only. Scripted reference performance shows limited prototype solvability, not model ability or transfer. The public package/Hub/model harness and final E3 gates remain uncertified.

### Spend, compute and repository snapshot

[Activity record](../logs/p3b2_activity.json): spend $0; model/GPU calls0; sealed evaluations0; actual checked rollouts96; stress/gate rollouts0. Screen wall seconds v1/v2/v3:326.022/379.665/328.788; trusted design-vector calculation27.180s; checked smoke121.124s. Total session CPU/elapsed compute was not metered, and overlapping activity times must not be added as total compute. No paid call occurred and no fictitious spend-ledger row was written.

Before the final report/evidence commit, tracked working files measured 683,789,691 bytes and `.git` 132,532,307 bytes at recorded HEAD `0be0be866bde4cd2eb73af67ed5f39711dcb3028`. Snapshot scope is explicit; it excludes subsequently staged proof/report artifacts. Full JUnit original bytes are losslessly retained in compressed form to respect the tracked-file size cap.

P2B_PROMPT11.md is deleted at completion; owner P2B_PROMPT1.md is preserved. Commit/push record this failed development round. No next phase begins.
