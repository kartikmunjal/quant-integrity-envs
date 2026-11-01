# P5b — process-allowance exhaustion hardening
**PASS — STOP after this phase.** All prescribed corrected-runtime and P5a rerun cohorts passed independent raw-record audit.
All episode measurements concern E1/E2/E5/E6 synthetic development cases and generator version `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`. Exact counts, per-environment/tier results, file hashes, test invocations, wall times and raw-storage sizes are reproduced in [report facts](../results/p5b_report_facts.json). No sealed evaluation, training, provider call, GPU job or paid pilot occurred. API/GPU spend is $0.

## Mechanism and authorization

The owner authorized one shared-runtime failure class in P2B_PROMPT15.md: exhaustion of the unchanged 32-process container allowance. Before each command, the host inspects the exact owned Docker container ID and init PID, resolves its cgroup-v2 membership through `/proc/PID/cgroup`, and reads its host-side `pids.max` and cumulative `pids.events:max`. A second snapshot must retain the same container ID, PID, cgroup path and actual limit of 32, with a strictly positive event delta. Stale lifetime counts, unmatched identities, malformed/unreadable counters and unsupported cgroup layouts cannot authorize a policy zero. No process is started inside the container to collect this evidence.

A fresh successful daemon-version probe is additionally required. On verified exhaustion, the host removes the container and confirms removal before setting the policy flag/ledger marker and returning a nonzero result. The unchanged native verifier then produces its hard zero; no infrastructure retry occurs. A narrow read guard rejects further transfer only after this confirmed exhaustion outcome, preventing native finalization from trying another exec inside a destroyed solver. This applies equally to solver, primary, replay and E2 poison containers.

The check also catches a submitted program that handles fork failure and prints a valid answer. If positive exhaustion evidence exists but fresh daemon health fails or is unavailable, the outcome is infrastructure: preserve the original infrastructure exception, or raise infrastructure when the child otherwise returned success. Genuine failures without valid exhaustion proof retain their original classification. Failed cleanup cannot become a confirmed policy zero or trigger a retry before cleanup is established.

The original command body is byte-identical after undoing only the authorized wrapper/name/import/read-guard additions. All other existing runtime modules (`infrastructure.py`, `phase.py`, `experiments.py`, `gate_summary.py`) remain byte-identical. Numerical reward functions, verifiers, generators, mutation logic, thresholds, tiers, seed partitions, privileges and frozen historical artifacts are untouched. [Independent scope review](../results/p5b_runtime_scope_review_v2.json) verifies this reconstruction. [AMENDMENTS.md](../AMENDMENTS.md) records the dated authorization and explicitly acknowledges that the P5a round-2 boundary failure had been seen.

Rejected alternatives were reviewed but not implemented:

- A lower per-user process limit can count the shared nobody UID across neighboring containers and create interference.
- Fork-syntax blocking is bypassable and supplies no trustworthy evidence of actual exhaustion.
- Blanket process prohibition would break legitimate subprocess behavior, including existing E2 policies.

## Runtime identities and host assumptions

| Identity | SHA-256 |
| --- | --- |
| Historical init source | `0a5d2a09968ed8e707c818c32ab8b3e468ff4fdeaa427043a359e7ad84a0bb41` |
| Historical three-file runtime hash | `fad402d113ca9e19f082ac45e3e0904edb128b9e672c351fe3a2d62eb699a827` |
| Corrected init source | `987bbe2d1b4e7984026b49a279ae81e84c5945685ab86e8de60aa86a5defcdfe` |
| Corrected three-file runtime hash | `b4be638a1b970a3243ddfd947774c4751d8f9377cb9691a061cfa785ebcf0760` |
| Corrected full runtime bundle | `772332ba1639c44e9a2c96fda4115ac0da9e46df429d93e0d212202fc7cdb407` |
| New host-evidence helper | `add6a9bd3460e4337b57c5e4cdf636edac26d2ed5ec84742f226747291684c25` |

The unchanged legacy hash function covers three existing runtime files. The new helper is bound separately and by the full runtime bundle and every execution plan; old results keep their original hashes. Candidate one (`1db65e193bf3c6b489ebfd26b4f3bad21102a4827dd15f02deac34b82b1bf374`) remains separately retained in [its manifest](../results/p5b_runtime_version.json); its results are not relabelled as corrected-source measurements.

Observed host: local Docker on Ubuntu 26.04.1 LTS, WSL2 kernel `6.18.54.1-microsoft-standard-WSL2`, cgroup v2. The mechanism requires the daemon's inspected init PID/cgroup to be visible in the host namespace and the owned kernel counters to be readable. A remote daemon or Docker Desktop VM with a different namespace is unsupported unless that binding can be established; unavailable evidence cannot produce a policy zero. The live counter-write tests confirm the solver cannot change these counters. No host-counter mount or privilege was added to a container.

Unchanged boundaries: network none, read-only root, one declared work mount, solver UID nobody, existing capabilities/no-new-privileges, 32 processes, 128 MiB and 1 CPU. Docker implicit system mounts remain as previously documented. Existing command and host transfer timeouts remain unchanged.

The P5a round-2 deadline interpretation also remains: setup/model turns/tools spend the model clock; solver artifact capture/removal precedes native finalization, and primary/replay/poison grading is joined to completion outside that clock. A stalled Docker daemon during grading can exceed nominal wall time. This phase does not implement the earlier general lifecycle redesign. The retained simulated late-creation cancellation diagnostic remains a known limitation, not a newly closed gate. This validation certifies the specified local mock/scripted cohorts, not hosted execution or real-model performance.

## Separation, tests first and every retained development failure

Independent validation author `/root/e1_review` owns the tests, cohort/comparison drivers and raw archive audits. Root owns the production runtime changes. The independent auditors re-check actual historical rewards/replay seeds, target-stage host evidence, source bindings, raw and exception hashes, cleanup, container identity uniqueness and parent-plan immutability. No human agreement or trajectory-label statistic is invented.

- Two prospective missing-API invocations each recorded 29 failures before implementation; both logs remain. After implementation and reader tests, 44 contracts passed.
- A new cleanup contract exposed policy evidence being set before removal: the failing attempt looked complete despite failed cleanup. Policy state now changes only after confirmed removal. The failed test remains in `logs/p5b_cleanup_before.xml`; 45 process contracts then passed.
- Pure E6 regression-plan construction exposed a nested historical `value` record rather than a flat reward field. The extraction was corrected without dropping a row or changing expected values. The failed test and correction record remain; seven final driver contracts pass.
- Supplementary review found that successful child output plus positive exhaustion and unusable daemon health could incorrectly return success. Four independent mock cases reproduced it. Tests/evidence were committed in `5fc55a8c` before the two-line correction in `dd533988`. All 49 final process contracts pass. An initial test-authoring collection error is separately retained, not called a runtime failure.
- Candidate-one live probes (68), mixed C8 (32), mixed C12 (48), and E1 exact regression (1,000) all passed under that candidate's source. Its 3,031-container audit remains intact. After the health correction, unchanged rows were recommitted under the new source and all nine required native runtime cohorts were rerun. No candidate-one result substitutes for corrected-source certification.
- The earlier P5a boundary v1 failure remains unchanged: 16 fork-heavy infrastructure failures, 160 passing cases, confirmed cleanup and no retries. Corrected boundary v2 is a separate live run. No historical failure was converted retroactively into a zero.

Every retained JUnit invocation follows (passed / failures / collection or other errors / skips). Long original XML is retained losslessly in hashed gzip archives where display XML needed bounding.

| Run | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| [p5b_audit_contract.xml](../logs/p5b_audit_contract.xml) | 1 | 0 | 0 | 0 |
| [p5b_cleanup_before.xml](../logs/p5b_cleanup_before.xml) | 0 | 1 | 0 | 0 |
| [p5b_driver_contracts.xml](../logs/p5b_driver_contracts.xml) | 4 | 0 | 0 | 0 |
| [p5b_driver_contracts_v2.xml](../logs/p5b_driver_contracts_v2.xml) | 5 | 0 | 0 | 0 |
| [p5b_driver_contracts_v3.xml](../logs/p5b_driver_contracts_v3.xml) | 6 | 0 | 0 | 0 |
| [p5b_driver_final.xml](../logs/p5b_driver_final.xml) | 7 | 0 | 0 | 0 |
| [p5b_e6_plan_before.xml](../logs/p5b_e6_plan_before.xml) | 0 | 1 | 0 | 0 |
| [p5b_health_guard_before.xml](../logs/p5b_health_guard_before.xml) | 0 | 0 | 1 | 0 |
| [p5b_health_guard_red.xml](../logs/p5b_health_guard_red.xml) | 0 | 4 | 0 | 0 |
| [p5b_parent_envelope_contracts.xml](../logs/p5b_parent_envelope_contracts.xml) | 6 | 0 | 0 | 0 |
| [p5b_phase_audit_contract.xml](../logs/p5b_phase_audit_contract.xml) | 1 | 0 | 0 | 0 |
| [p5b_process_contracts_before.xml](../logs/p5b_process_contracts_before.xml) | 0 | 29 | 0 | 0 |
| [p5b_process_contracts_with_reader.xml](../logs/p5b_process_contracts_with_reader.xml) | 44 | 0 | 0 | 0 |
| [p5b_process_red.xml](../logs/p5b_process_red.xml) | 0 | 29 | 0 | 0 |
| [p5b_component_suite_v1.xml](../results/p5b_component_suite_v1.xml) | 837 | 0 | 0 | 38 |
| [p5b_component_suite_v2.xml](../results/p5b_component_suite_v2.xml) | 844 | 0 | 0 | 38 |
| [p5b_full_suite.xml](../results/p5b_full_suite.xml) | 850 | 0 | 0 | 38 |
| [p5b_full_suite_v2.xml](../results/p5b_full_suite_v2.xml) | 854 | 0 | 0 | 38 |
| [p5b_main_suite.xml](../results/p5b_main_suite.xml) | 668 | 0 | 0 | 38 |
| [p5b_process_v1.xml](../results/p5b_process_v1.xml) | 29 | 0 | 0 | 0 |
| [p5b_process_v2.xml](../results/p5b_process_v2.xml) | 45 | 0 | 0 | 0 |
| [p5b_process_v3.xml](../results/p5b_process_v3.xml) | 49 | 0 | 0 | 0 |

The final full local suite is **854 passed, 38 skipped**. Skips are existing Docker-gated pytest cases; the separately opted-in cohorts below used actual local Docker. GitHub Actions status is unverified; local test success is not reported as remote CI success. The project paid runner remains unchanged and refusing paid execution.

## Committed cohorts and corrected-source results

All exact native lists and initial execution plans were committed before runs in `fff2e039`. The health correction's nine new plans were committed in `066e7e44`; independent [plan audit](../results/p5b_v2_plan_audit.json) proves every original row remained unchanged. The four final P5a envelopes preserve the original committed P14 rows, seeds, policies, counts, concurrency and windows byte-for-byte. Only prospective execution-source bindings differ; [envelope audit](../results/p5b_p5a_final_envelope_audit.json) checks the original parent hashes. Old unrun envelopes are retained. The `v2_final` suffix distinguishes the final source envelope; boundary v2 is the first live rerun after failed boundary v1.

| Corrected-source batch | Cases or pairs | Concurrency | Passed | Failures | Retries | Wall seconds | Evidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| p5b_probes_v2 | 68/68 | 8 | 68 | 0 | 0 | 253.261 | [summary](../results/p5b_probes_v2.json) |
| p5b_mixed_c8_v2 | 32/32 | 8 | 32 | 0 | 0 | 99.100 | [summary](../results/p5b_mixed_c8_v2.json) |
| p5b_mixed_c12_v2 | 48/48 | 12 | 48 | 0 | 0 | 107.422 | [summary](../results/p5b_mixed_c12_v2.json) |
| p5b_regression_e1_v2 | 1000/1000 | 8 | 1000 | 0 | 0 | 784.504 | [summary](../results/p5b_regression_e1_v2.json) |
| p5b_regression_e5_v2 | 1000/1000 | 8 | 1000 | 0 | 0 | 844.081 | [summary](../results/p5b_regression_e5_v2.json) |
| p5b_regression_e6_v2 | 1000/1000 | 8 | 1000 | 0 | 0 | 851.110 | [summary](../results/p5b_regression_e6_v2.json) |
| p5b_regression_e2_v2 | 1000/1000 | 8 | 1000 | 0 | 0 | 1338.653 | [summary](../results/p5b_regression_e2_v2.json) |
| p5b_e2_stress_c8_v2 | 2000/2000 | 8 | 2000 | 0 | 0 | 1478.092 | [summary](../results/p5b_e2_stress_c8_v2.json) |
| p5b_e2_stress_c12_v2 | 2000/2000 | 12 | 2000 | 0 | 0 | 1279.374 | [summary](../results/p5b_e2_stress_c12_v2.json) |
| p5b_p5a_boundary_v2_final | 176/176 | 8 | 176 | 0 | 0 | 402.378 | [summary](../results/p5b_p5a_boundary_v2_final.json) |
| p5b_p5a_sentinel_v2_final | 16/16 | 8 | 16 | 0 | 0 | 23.990 | [summary](../results/p5b_p5a_sentinel_v2_final.json) |
| p5b_p5a_equivalence_v2_final | 3120/3120 | 8 | 3120 | 0 | 0 | 6385.944 | [summary](../results/p5b_p5a_equivalence_v2_final.json) |
| p5b_p5a_stress_v2_final | 1000/1000 | 8 | 1000 | 0 | 0 | 1444.874 | [summary](../results/p5b_p5a_stress_v2_final.json) |

Live runtime probes comprise 52 bomb cases: solver/primary/replay for every E1/E5/E6 tier and solver/primary/replay/poison for every E2 tier, plus 16 counter-write checks. Each bomb must carry positive proof on its actual target stage, a zero reward, confirmed cleanup and no retry. Mixed C8 has 16 bombs + 16 normal neighbors; mixed C12 has 24 + 24. All normal oracle neighbors satisfy the unchanged oracle criterion and have no exhaustion proof. Independent interval checks verify concurrent overlap rather than merely sequential success.

The E1/E5/E6 regression lists are the exact 1,000-row lists in `results/p3a2_regression_plan.json.gz`. E2's 1,000-row historical cohort was committed before its first execution: 250/tier, all 32 policies, selecting 7 or 8 rows/policy/tier using metadata order rather than rewards. Every reward **and** every replay seed matches the hash-checked historical raw value exactly, with **no tolerance**. Existing historical routing contexts are installed once per batch to reproduce the original dev admission/replay semantics; no generator or verifier source changes. The two E2 stress cohorts each use 2,000 rows from the pre-existing screened design schedule, with no newly selected/rejected seed based on policy results. [Native audit](../results/p5b_runtime_validation_audit.json) validates all nine native cohorts against raw records.

### Boundary v2 by environment and tier

Each cell is passed/attempted across all 11 attack types; every cell passes. The attack roster, source, primary dev seeds and criteria are unchanged from boundary v1.

| Environment | T1 | T2 | T3 | T4 | Total |
| --- | --- | --- | --- | --- | --- |
| E1 | 11/11 | 11/11 | 11/11 | 11/11 | 44/44 |
| E2 | 11/11 | 11/11 | 11/11 | 11/11 | 44/44 |
| E5 | 11/11 | 11/11 | 11/11 | 11/11 | 44/44 |
| E6 | 11/11 | 11/11 | 11/11 | 11/11 | 44/44 |

The 16 host-sentinel checks pass, one per environment/tier; the planted fake host value never appears in solver-visible messages. This is an exposure check with a deliberate fake variable, not a claim to detect every getenv operation.

### Semantic equivalence by environment and tier

All 3,120 pairs pass both reward and semantic native evidence comparison (6,240 native episode records). Scalars use absolute tolerance `1e-12`. Answers, status, flags, source/input identity, replay seeds and E2 poison/patch findings remain compared. Only the declared operational fields are excluded: container IDs, trace hashes, timing, elapsed/duration seconds and UTC timestamps, outside answer payloads. The original comparison implementation and assertions are unchanged.

| Environment | T1 | T2 | T3 | T4 | Pairs passed/total |
| --- | --- | --- | --- | --- | --- |
| E1 | 200/200 | 200/200 | 200/200 | 200/200 | 800/800 |
| E2 | 180/180 | 180/180 | 180/180 | 180/180 | 720/720 |
| E5 | 200/200 | 200/200 | 200/200 | 200/200 | 800/800 |
| E6 | 200/200 | 200/200 | 200/200 | 200/200 | 800/800 |

Each environment has 50 oracle episodes/tier (200/environment), five wrong policies at 10/tier each, and every existing cheater at 10/tier. E1/E5/E6 each have 10 cheaters, giving 800 pairs/environment; E2 has 8 cheaters, giving 720. These are mock tool-path controls, not measured language-model difficulty or real research performance.

## Final audit, accounting, compute and limitations

[Final cross-version audit](../results/p5b_phase_audit.json): integrity **True**, complete final-runtime coverage **True**, complete P5a coverage **True**, phase acceptance **True**. It checks 13,784 unique raw archives, 7,140 exception metadata files and 7,140 trace parts, with 0 errors. Across final and explicitly historical cohorts, 43,722 unique containers were created and 43,722 removed; there are no unremoved recorded IDs. Historical coverage cannot substitute for final-source coverage.

[Read-only live container check](../results/p5b_final_container_check.json) independently queries the audit's 43,722 exact owned IDs and finds **0 remaining**. This is separate from offline journal accounting.

[Report facts](../results/p5b_report_facts.json) record summed completed final-batch wall time of 15292.783 seconds and candidate-one historical-batch wall time of 1236.128 seconds. These are observed elapsed times, not metered CPU time. Container limits stay at one CPU/128 MiB; no GPU compute was requested. Full raw records and exception journals remain locally retained behind committed hashes; compact proof shards and generated-source pools are committed.

[Repository-size snapshot](../results/p5b_repo_size.json) at evidence commit `7a23bf41ec81db999fa99845c95a7acce01b8101`: 18,470 tracked files / 705,403,480 bytes, `.git` 169,398,709 bytes, new phase files 18,658,709 bytes. The snapshot precedes this final report/size record and excludes package caches and ignored raw artifacts.

API and GPU spend is **$0**; no provider call or GPU job occurred and `logs/spend.csv` does not exist. Fake loopback HTTP/unit ledger fixtures are explicitly synthetic. No real API key, owner terms file or file under ~/private was read. No paid pilot unlock, package/Hub publication, license/rename, training or sealed evaluation occurred. No prior report, freeze, gate marker or baseline value was rewritten.

## Commits and disposition

- `a5cac342`: main-only limitation bullet, committed roster review, README regeneration/table check and 668-pass local suite; pushed once, then merged into model-harness.
- `44410c41`: prospective owner scope/mechanism before implementation.
- `939e0a1c`: initial narrow implementation/amendment and independent tests.
- `fff2e039`: original independent native plans before any live run.
- `5fc55a8c`: supplementary health tests and retained failures before correction.
- `dd533988`: final two-line health correction, 49 contracts and 854-pass suite.
- `066e7e44`: identical-row native plans and final P5a envelopes tied to corrected source.
- `6b9aa1b0`, `d0c95b9c`: retained candidate-one live and exact E1 evidence.
- `9be9fbea`, `41677af1`, `4dfd5502`, `fab736fc`, `4408a8d3`, `bcd1249a`: corrected live, exact regression and screened stress evidence.
- `dcfe999b`, `2643ca2b`, `ec06c334`: passing boundary, sentinel and all semantic pairs.
- `7a23bf41`: final passing stress, complete independent audits and zero-remaining live container check.

The commit containing the final audit/report is identified by `git log -1 -- reports/P5b.md` and the owner's completion message. No history was rewritten or squashed. Main is not pushed again. The final branch push and deletion of only P2B_PROMPT15.md occur after the report/audit is complete; P2B_PROMPT1.md is preserved.

**STOP.** P5b passed the specified local validation scope. Do not begin the paid pilot or next phase without the owner.
