# P5a — STOP: shared runtime lifecycle change required

**P5a did not pass.** The owner-authorized MIT documentation step is complete. The `model-harness` branch contains an infrastructure prototype and component tests, but the requested full model-driven validation is blocked by the unchanged shared runtime's cancellation lifecycle. No provider/model API request, real API-key lookup, paid pilot, GPU call or sealed evaluation was made. Spend is $0.

The prompt expressly requires: “STOP and report if the runtime cannot support a multi-step solver container without a shared runtime change, with a precise design for the change; do not make it.” Ordinary sequential commands work. The blocker is preserving the **whole-episode wall deadline and no-leaked-container guarantee across native primary/replay provisioning**, not a claim that all multi-step execution is impossible. The shared change below was not made. No next phase begins.

## Identity, branch and scope

Actual smoke environments: E1 point-in-time backtest, E2 leakage audit, E5 cost realism and E6 data reconciliation. Generator: `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`. Runtime: `fad402d113ca9e19f082ac45e3e0904edb128b9e672c351fe3a2d62eb699a827`. Immutable local Docker image: `sha256:9cc803aaddbbb1a17c9eef928b5438d61769c9c9ba928fc285bc7ee622ad8353`. Each smoke/result names its environment and generator; [activity/source inventory](../logs/p5a_activity.json) binds the implementation. The cancellation diagnostic generated no environment episode and correctly records a null generator identity plus the exact shared source hash.

Both required `git pull --ff-only` calls completed before work. Existing `LICENSE` was confirmed MIT and remained unchanged. Main commit `17eaea883d47bd9dd06f8651c0b82d9bd100b85c` added `License: MIT` near the template's top, regenerated README through `scripts/reproduce_table.py --write`, passed its check and the full baseline suite (664 passed, 38 skipped), and was pushed. `model-harness` was then created and pushed. There was no later push to main, merge from `e3-redesign`, dependency upgrade, rename, Hub/package publication or README pilot table.

At the initial branch check, tracked `e3-redesign` work was clean; only owner-provided `P2B_PROMPT1.md` and `P2B_PROMPT13.md` were untracked. Those inputs were not treated as unfinished implementation work. Retained local E3 evidence was preserved and ignored on the main-derived branch. E3 is skipped: main contains the unvalidated earlier prototype, and the separate redesign branch was not silently activated.

## What was built, and what remains uncertified

- `src/qi_harness/`: typed limits and client replies; a host-side tool loop; a separate native-v1 Env/Harness adapter; confined file tools; bounded command execution; additional trace auditing; prompt verification; bounded, hashed transcripts; price accounting and pure pilot summary/projection helpers. Existing task setup/finalize/rewards, source capture and fresh replay implementations are reused, not edited.
- Five tools: list files, read a work file, run a command, run a Python snippet and submit captured source. Submission is a program that emits the native environment's required answer schema; naked hardcoded numerical answers do not replace fresh-source replay. Model-influenced writes use audited solver-UID commands, not trusted root transfers after untrusted execution. File helpers use no-follow confinement; fixed submission leaves are under the immutable `/work` mount point. Unresolved descriptor access and uncertain traces fail closed.
- Commands clear inherited environment and install only fixed public PATH, LANG and bytecode settings. No host credential is mounted or placed in solver environment/arguments. This withholds host environment data; it does not claim universal detection of in-process `getenv` queries. The pinned interpreter's exact public `/proc` metadata reads are allowed; protected process-root, descriptor and environment aliases remain denied.
- Defaults committed before Docker validation: 16 turns, 2048 completion tokens per turn, 32768 total tokens, 180-second episode deadline, 16384-byte visible tool output, 2097152-byte transcript cap. Every parameter is configurable through `Limits`. Non-submission and token/turn violations are defined zeros. The outer deadline and adapter-owned startup joining have pure tests; they do not repair native grading startup.
- `CompatibleClient` exercises the compatible chat wire through an explicit loopback fake HTTP server only. Remote requests are locked before key lookup/network; loopback opts require a deliberately fake key-variable name. Redirects and proxy discovery are disabled. There is no claim of compatibility with a live provider. Key values are only looked up at dispatch, and only deliberately planted fake values were read in this task.
- Empty `configs/model_prices.json` refuses unpriced dispatch. `BudgetController` uses the unchanged `scripts/budget_gate.py` rules, Decimal prices and locked outstanding reservations. Reservations are not paid spend. The 80-percent stop boundary prevents more dispatch; the hard cap refuses authorization. Actual overrun settlement is recorded in full and stops, never concealed as a refused charge. Lost/malformed usage holds an uncertain reservation, stops and requires reconciliation. Fake-cost ledgers stay in test scratch space, not `logs/spend.csv`.
- Per-environment prompts, natural tool descriptions and actual wire schemas are under `prompts/`, bound by all three retained dev-only manifest entries in [prompt manifest](../results/prompt_manifest.json). Wire/source drift is rejected. Later prompt changes require a new dev-only entry; no sealed result may select a prompt.
- `scripts/run_pilot.py` provides model, per-cell episode, dev-window, concurrency, key-variable-name, confirmation and dry-run arguments, and always refuses paid execution during P5a. No spend-cap override exists. Pure helpers compute per-cell mean reward, reward density, turn/token statistics, cost and hack monitors, preserving zero episodes and unknown costs. The table renderer is ready for future pilot artifacts, but none was added to README. This remains a locked planning/prototype entrypoint, not a certified paid runner.
- Cost projection uses observed token totals/episode counts and supplied prices. Extra models are removed before training seeds, preserving at least two API and two open models and the frozen seed floor. Training GPU projections require a separately supplied measured per-seed amount; reducing training seeds cannot pretend to reduce baseline API cost. Missing prices/observations refuse projection. No real baseline or training cost was guessed.

The [design and boundary document](../docs/model_harness.md) distinguishes intended controls from certification. All providers and paid execution remain locked. Neither the full tool boundary matrix nor the current complete native lifecycle is certified.

## Independent tests first

`/root/p3b_validation` independently authored the P5a contracts and comparison driver before implementation; the implementation author did not edit those validation files. Tests cover clients, prices/reservations, unknown usage, redaction, no-socket/dry-run behavior, limits, file/trace guards, prompts, transcripts, projection, native Env separation and evidence retention. The driver calls the original scripted task runner independently and compares semantic primary/replay records, plus E2 poison results/findings/patches.

The validation author reached a session usage limit before the final shared-helper diagnostic. A second independent reviewer, `/root/e1_review`, inspected the unchanged helper, authored and ran [the deterministic diagnostic](../tests/validation/p5a_runtime_cancellation_diagnostic.py). That reviewer confirmed the same scope blocker. This is coding-agent separation, not independent human labels or external reproduction.

Fresh rollouts necessarily differ in container IDs, timestamps, duration and trace digests. Semantic equivalence excludes only declared operational metadata and retains answers, status, flags, input/source identity and scalar values with absolute tolerance 1e-12. Full raw provenance is retained locally with hashes. These exclusions are explicit, rather than an impossible claim that separate container IDs are literally identical.

## Mandatory blocker and independent reproduction

The unchanged `src/qi_runtime/__init__.py` contains `execute_program`: it constructs its own runtime, directly awaits `runtime.start()`, and directly awaits `runtime.stop()` in `finally`. Cancellation can terminate the client await while an already accepted daemon request remains unresolved. Removal can observe “not created” and finish before daemon creation completes. Shielding the model adapter's own startup does not cover the helper's independently created primary/replay containers.

[Independent evidence](../results/p5a_runtime_blocker.json) records the actual helper run with process-local fake directory/runtime/daemon substitutions:

```text
helper startup client cancelled
helper cleanup: remove_before_create
simulated daemon completion: created
```

The diagnostic assertions passed; **the required runtime capability did not**. Counters for writes, submitted-code execution, model actions and answer parsing are all zero. Shared source SHA-256 remains `0a5d2a09968ed8e707c818c32ab8b3e468ff4fdeaa427043a359e7ad84a0bb41`. This demonstrates an ordering permitted by the existing API under a simulated late daemon completion. **No real Docker leak was observed or claimed.** It does not measure Docker timing.

The wall-clock requirement was interpreted as covering setup, model/tools, finalization and native grading, with cleanup permitted to finish after expiry. Narrowing it to model thinking/tools would leave native grading outside the requested episode bound. Shielding an entire grading coroutine can continue primary/replay after expiry; private-field polling or monkeypatching the shared runtime is not a supported atomic lifecycle API. No such workaround or prohibited change was made.

### Precise change proposed for owner approval — not implemented

1. Introduce one shared lifecycle scope used by all owners, including `execute_program`, with retained provisioning tasks and stable resource identity through NEW/PROVISIONING/RUNNING/STOPPING/STOPPED.
2. Cancellation must join or definitively reconcile daemon-side provisioning before final removal. A single “no such container” response while creation remains unresolved must not establish cleanup completion.
3. Shield and join idempotent teardown; record confirmed removal. Cleanup/reconciliation failures remain infrastructure failures/incomplete attempts, never a fabricated clean timeout zero. Do not retry a rollout before cleanup is established.
4. Propagate a deadline/cancellation token through every shared execution stage. After expiry, allow cleanup only: no new model action, primary, replay or poison continuation. Preserve the original cancellation after cleanup.
5. On command transport/cancellation uncertainty, destroy/join the solver before source finalization or another command. Killing a Docker client alone is not proof that its daemon-side command stopped.
6. Independently specify/test cancellations at create/start/inspect/transfer/command/status/teardown first; then exercise real Docker solver and grading deadlines, all-container cleanup, the 1000-episode C8 stress and the full mock/scripted matrix. Version the approved runtime change and preserve historical freezes/results. No threshold, reward, privilege, network policy, mount or generator relaxation is needed.

The owner must authorize that shared change in a later prompt. It was not implemented here.

## Required checks and measured status

| Criterion | Requirement | Measured result |
|---|---|---|
| Step 0 tablecheck and tests | Generated README match; full suite | PASS: 664 passed / 38 skipped |
| Current local regression suite | Full suite | PASS: 774 passed / 38 skipped / 0 failures |
| Independent diagnostic | Safe cancellation order across shared grading startup | FAIL capability: remove-before-late-create reproduced; diagnostic test 1 passed |
| Oracle mock equivalence | 200/environment, every tier (50/tier) | NOT RUN full cohort; latest small smoke 1 T1 pair/environment |
| Wrong/cheater equivalence | At least five wrong plus every existing cheater, same coverage | NOT RUN; planned 12400 total policy pairs including oracles |
| Live tool boundary attacks | 11 attack types × four environments × four tiers | NOT RUN: 176 planned |
| Host-environment withholding | Fake host sentinel across every environment/tier | NOT RUN: 16 planned; no universal getenv-detection claim |
| Stress | 1000 mock episodes, C8, zero retries and leaks | NOT RUN; no substitute stress claim |
| Client/budget/limit/artifact components | Independent fake/pure contracts | PASS within 110 P5a tests in current full suite |
| No provider spend or real-key reads | $0 and no provider requests | PASS: zero; only explicit local fake-server tests |
| Protected sources and README scope | No forbidden source/threshold/freeze edits; no post-step0 README change | PASS: empty protected diff |
| P5a overall | All required lifecycle and validation criteria | STOP / NOT PASSED |


The full unexecuted roster is retained in [plan counts](../results/p5a_unexecuted_plan.json): 12400 policy pairs would require 24800 scripted/model episodes, followed separately by 176 boundary episodes, 16 host-environment checks and 1000 stress episodes. No failed seed or policy was dropped to produce a pass, and no threshold was changed. There is no passing one-shot gate/freeze claim for P5a.

Default windows are E1 1002500..1002599, E2 1000800..1000899, E5 1005500..1005599, E6 1003500..1003599. [Window evidence](../results/p5a_seed_windows.json) reports zero intersections with retained historical gate primary/replay records; [inventory](../results/p5a_gate_seed_inventory.json) and earlier declared numeric primary ranges state the exact scope. These are dev windows, not claims that no development fixture ever used them. Current paid pilot defaults are two episodes per cell, concurrency one; all execution remains locked.

## Every engineering smoke, including failures

Five small oracle-only smoke versions ran; each used one T1 pair per environment (one original scripted episode plus one mock-model episode). They are engineering comparisons, not the required 200/environment/policy validation. The final whole-lifecycle/provisioning changes were only component-tested after the STOP finding, so the earlier passing smokes do not certify the final prototype's complete lifecycle.

| Version | Pairs | Semantic pair matches | Reward matches | Retries | Wall seconds | Finding |
|---|---|---|---|---|---|---|
| [v1](../results/p5a_smoke_v1.json) | 4 | 0 | 0 | 0 | 26.881501 | Fail closed: unrecognized aligned strace syntax |
| [v2](../results/p5a_smoke_v2.json) | 4 | 0 | 0 | 0 | 26.750984 | Same parser refusal; raw trace diagnostic added |
| [v3](../results/p5a_smoke_v3.json) | 4 | 4 | 4 | 0 | 46.553781 | Functional match; intermediate FD-mode unit failures remained |
| [v4](../results/p5a_smoke_v4.json) | 4 | 0 | 0 | 0 | 36.467451 | Fail closed: interpreter metadata reads denied |
| [v5](../results/p5a_smoke_v5.json) | 4 | 4 | 4 | 0 | 45.199155 | Functional match after exact metadata allowances |


Initial v1/v2 failures exposed aligned syscall formatting. An intermediate parser run then had three failed unit tests because permission-mode integers were mistaken for directory descriptors. The v3 smoke started despite those failures; its result is retained as functional evidence only. Argument-position parsing and additional protected-path/descriptor regressions corrected that error before later checks. V4 then exposed exact public interpreter metadata reads. Every version and all failed rows remain in the record; no verifier was weakened to pass them.

Latest pre-blocker functional smoke v5, by environment/tier:

| Environment | Tier | Scripted episodes | Mock episodes | Scripted reward | Mock reward | Semantic match | Required cohort |
|---|---|---|---|---|---|---|---|
| E1 | T1 | 1 | 1 | 1.0 | 1.0 | 1/1 | NOT SATISFIED: needs 50/tier |
| E1 | T2 | 0 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT SATISFIED: needs 50/tier |
| E1 | T3 | 0 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT SATISFIED: needs 50/tier |
| E1 | T4 | 0 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT SATISFIED: needs 50/tier |
| E2 | T1 | 1 | 1 | 1.0 | 1.0 | 1/1 | NOT SATISFIED: needs 50/tier |
| E2 | T2 | 0 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT SATISFIED: needs 50/tier |
| E2 | T3 | 0 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT SATISFIED: needs 50/tier |
| E2 | T4 | 0 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT SATISFIED: needs 50/tier |
| E5 | T1 | 1 | 1 | 1.0 | 1.0 | 1/1 | NOT SATISFIED: needs 50/tier |
| E5 | T2 | 0 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT SATISFIED: needs 50/tier |
| E5 | T3 | 0 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT SATISFIED: needs 50/tier |
| E5 | T4 | 0 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT SATISFIED: needs 50/tier |
| E6 | T1 | 1 | 1 | 1.0 | 1.0 | 1/1 | NOT SATISFIED: needs 50/tier |
| E6 | T2 | 0 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT SATISFIED: needs 50/tier |
| E6 | T3 | 0 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT SATISFIED: needs 50/tier |
| E6 | T4 | 0 | 0 | NOT RUN | NOT RUN | NOT RUN | NOT SATISFIED: needs 50/tier |


[Offline smoke audit](../results/p5a_smoke_audit.json) rechecked all 20 retained pairs using the independently authored comparator, including E2 poison/findings/patch fields. There were 40 actual checked episodes, 103 unique created/removed containers, zero rollout retries, and zero remaining owned smoke containers on read-only Docker inspection. Those ordinary-smoke observations do not establish the unrun stress or cancellation guarantee. Full raw smoke/solver trace records remain under ignored `artifacts/p5a/`, bound by committed hashes. No live attack batch was executed after the mandatory STOP.

## Every logged test run

Repeated runs below are separate executions, not unique-test counts. The current full suite contains 110 P5a contract tests plus the pre-existing suite; the standalone diagnostic adds one separate reproduction test. Historical Docker integration tests are skipped by the default suite, and the required P5a Docker batches remain unrun.

| JUnit run | Passed | Failed | Errors | Skipped | Measured suite seconds |
|---|---|---|---|---|---|
| [p5a_budget_junit.xml](../logs/p5a_budget_junit.xml) | 9 | 0 | 0 | 0 | 0.049 |
| [p5a_client_budget_loop_junit.xml](../logs/p5a_client_budget_loop_junit.xml) | 11 | 0 | 0 | 0 | 0.588 |
| [p5a_client_junit.xml](../logs/p5a_client_junit.xml) | 6 | 0 | 0 | 0 | 0.552 |
| [p5a_contract_suite_junit.xml](../logs/p5a_contract_suite_junit.xml) | 71 | 0 | 0 | 0 | 2.543 |
| [p5a_env_contracts_junit.xml](../logs/p5a_env_contracts_junit.xml) | 16 | 0 | 0 | 0 | 1.889 |
| [p5a_full_suite_junit.xml](../logs/p5a_full_suite_junit.xml) | 774 | 0 | 0 | 38 | 19.834 |
| [p5a_global_deadline_junit.xml](../logs/p5a_global_deadline_junit.xml) | 18 | 0 | 0 | 0 | 1.831 |
| [p5a_hardened_contracts_junit.xml](../logs/p5a_hardened_contracts_junit.xml) | 82 | 0 | 0 | 0 | 2.435 |
| [p5a_loop_artifacts_junit.xml](../logs/p5a_loop_artifacts_junit.xml) | 9 | 0 | 0 | 0 | 0.065 |
| [p5a_pilot_junit.xml](../logs/p5a_pilot_junit.xml) | 7 | 0 | 0 | 0 | 0.098 |
| [p5a_proc_metadata_junit.xml](../logs/p5a_proc_metadata_junit.xml) | 40 | 0 | 0 | 0 | 1.752 |
| [p5a_provision_wire_junit.xml](../logs/p5a_provision_wire_junit.xml) | 13 | 0 | 0 | 0 | 1.796 |
| [p5a_runtime_blocker_junit.xml](../logs/p5a_runtime_blocker_junit.xml) | 1 | 0 | 0 | 0 | 1.748 |
| [p5a_secret_usage_pilot_junit.xml](../logs/p5a_secret_usage_pilot_junit.xml) | 32 | 0 | 0 | 0 | 3.380 |
| [p5a_step0_junit.xml](../logs/p5a_step0_junit.xml) | 664 | 0 | 0 | 38 | 21.523 |
| [p5a_tools_junit.xml](../logs/p5a_tools_junit.xml) | 17 | 0 | 0 | 0 | 1.891 |
| [p5a_trace_hardening_junit.xml](../logs/p5a_trace_hardening_junit.xml) | 25 | 0 | 0 | 0 | 1.775 |
| [p5a_trace_parser_junit.xml](../logs/p5a_trace_parser_junit.xml) | 20 | 3 | 0 | 0 | 2.400 |


Component counts in the latest full suite:

| Independent contract module | Tests |
|---|---|
| test_p5a_budget | 12 |
| test_p5a_config_client | 11 |
| test_p5a_environments | 13 |
| test_p5a_global_timeout | 6 |
| test_p5a_loop | 6 |
| test_p5a_pilot | 9 |
| test_p5a_tools | 40 |
| test_p5a_transcripts_prompts | 7 |
| test_p5a_validation_driver | 6 |


[Test-run manifest](../results/p5a_test_runs.json) hashes every JUnit file. Oversized original JUnit bytes are retained losslessly compressed alongside bounded XML summaries. [Status](../results/p5a_status.json) explicitly sets phase passed=false. No remote CI status is inferred from local test success.

## Spend, compute, size, limitations and commit record

[Activity](../logs/p5a_activity.json): provider API requests 0, real API-key values read 0, GPU calls 0, sealed evaluations 0; API spend $0, GPU spend $0. `logs/spend.csv` is absent; no paid ledger entry was invented. The explicit loopback fake-wire tests made 10 recorded test requests using planted fake credentials and fake-price scratch ledgers, never a provider. That is the prompt's fake-server exception, not an experiment. Six deliberate fake credential fixtures were scanned across 174 phase artifact files with zero matches, excluding test source that intentionally defines them. This is a tested artifact scope, not a universal secret-redaction proof.

Smoke and test times are measured above. Total session CPU/elapsed compute was not metered; overlapping activity times are not summed into a total. The runtime diagnostic performed no Docker, solver, parser or model work. No pilot reward-density/cost table was fabricated or added to README.

At the pre-report snapshot HEAD `c0b92be50a136d27c95b0b2b1e6f42646e670433`, tracked working files measured 685437776 bytes, `.git` 152275202 bytes, new P5a tracked paths 562863 bytes, and ignored local P5a raw evidence 1783485 bytes. No new tracked file exceeded 1 MiB. These scoped snapshots exclude subsequently added report/activity files; they are not self-referential final-commit sizes.

Main documentation commit: `17eaea883d47bd9dd06f8651c0b82d9bd100b85c`. Prospective contracts and implementation commits include `40925f08` (native adapter and dev-window commitment), `27abce39` (retained smoke plan), `1482b3b6` (fail-closed smoke/trace evidence), `79c2cacb` (aligned parser and unresolved-write handling), `54b3eef1` (protected read aliases), `ad69873e` (exact interpreter metadata allowances), `4072e0c2` and `22e11638` (deadline/provision/wire contracts before implementation). The complete tested prototype and diagnostic are in the ancestors of `c0b92be50a136d27c95b0b2b1e6f42646e670433`; that commit retains current checks and explicit unrun counts. The final report commit is identified by `git log -1 -- reports/P5a.md` and the completion message. No history was rewritten.

Remaining gaps are material: safe whole-episode cancellation across native grading is blocked; all-tier/full-policy equivalence, live attacks, host sentinel checks and stress are unrun; only fake compatible HTTP is tested; actual provider token/billing bounds, cached/reasoning prices, unknown-usage recovery and remote model behavior need review before unlocking. Commands that fail are terminal under current policy-failure semantics; this does not certify recovery after a failed debugging step. Finite local scripted/mock evidence does not certify remote/Hub execution, model success, training transfer, sealed performance or real-market utility.

Protected shared runtime, generator, mutation engine, environment/verifier/reward sources, thresholds, preregistration, historical freezes and LICENSE remain unchanged. README changed only in the authorized main step. Only `P2B_PROMPT13.md` is removed at completion; `P2B_PROMPT1.md` and all older evidence are preserved.

**STOP. P5a remains blocked, awaiting owner authorization of the precise shared lifecycle change. No paid pilot, baseline, training, sealed evaluation or next phase begins.**
