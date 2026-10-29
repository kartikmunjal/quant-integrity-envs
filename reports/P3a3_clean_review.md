# P3a3 clean-context review

Status: READY FOR FREEZE

Independent reviewer session, 2026-10-29 UTC. This is a pre-stress source review, not a completed gate review. The implementation author did not conduct this review. No Docker command, policy rollout, model API, GPU job, sealed evaluation or outside-repository read was performed by this reviewer.

Reviewed AGENTS.md, SPEC.md, prereg.yaml, AMENDMENTS.md, COMPAT.md, BRIEF.md, P2B_PROMPT7.md, reports/P3a3_design.md, scripts/*p3a3*.py, tests/validation/*p3a3*.py, and the referenced construction, source-inventory and gate-statistics functions. Pre-phase comparison baseline: 5908143 (not the later audit HEAD). Round-three changes were uncommitted and the population screen was still in progress when reviewed. E2 generator identity remains eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921.

## Finding corrected during review

The original clean-review prerequisite used substring membership for its positive readiness phrase. A negative statement containing that phrase could satisfy it. The author corrected this to an exact standalone status line in require_review_approval and added prospective negative/positive validation tests in tests/validation/test_p3a3_freeze.py. I reviewed the correction and ran these four tests successfully; this finding is resolved. This provisional report deliberately omits the literal positive token.

The author subsequently identified that screened design replay could select the primary seed, losing the historical distinct-replay guarantee. I reviewed the retained failing test output in `.cache/p3a3_distinct_before.txt` and the correction: when SHA256 selects the primary seed, advance one position in the ordered admissible list, wrapping deterministically; fewer than two design seeds is rejected. Given unique committed seeds this guarantees distinct construction-admissible replay without financial changes. The fresh gate primary/replay ranges are disjoint and need no collision fallback. This finding is resolved.

## Source findings

- The screen calls unchanged make_case for every tier, admits only construction successes, catches AdmissionFailure while retaining candidate diagnostics, and propagates unexpected exceptions. It imports no policy outcome, reward or Docker function. The frozen make_case admission machinery necessarily computes construction effects; this is part of the existing construction predicate, not policy-based selection.
- Chunk collection and seed iteration preserve ascending order. Primary selection is the first 500 admissible seeds strictly below the replay range. Replay extends the original reserved block only as needed, inside the development partition. Population loading checks committed bytes and construction source hashes before policy execution. SHA256 routing is deterministic and scoped, and previous routing functions are restored afterward.
- The source inventory inherited from run_p3a_gate includes the round-three scripts and validation tests through its wildcard patterns. Screen bytes and design are also bound. Fresh gate execution requires a committed freeze and consumes an exclusive marker before initialization.
- Relative to historical financial baseline 34be7561edcb01c69e971a88d638b01f33b610c0, generator, mutation, E2 runtime/reward and prereg files show no changes. Historical runtime and E1/E5/E6 task wrappers have prior infrastructure changes, so their exact historical regression proofs and source/runtime matching remain necessary; the freeze checks retain those requirements.
- Stress summary acceptance requires all planned rows complete and infrastructure healthy, retries at most 0.5 percent, unique container identifiers and no worker/fatal errors. Freeze checks require both 5000-row stress summaries with the expected concurrency and current source hashes. A failed stress must end the phase; it cannot be repaired by selecting a different population or rerunning toward a passing result under this prompt.
- The screen report must explicitly retain exclusion rates and causes and state that findings concern construction-admissible episodes, excluding extreme-tail failures. No measured population rate is asserted here because screen evidence was not yet available.

## Validation and remaining prerequisites

Pure targeted validation completed: `.venv/bin/python -m pytest tests/validation/test_p3a3_screen.py tests/validation/test_p3a3_routing.py -q` exited 0 with eight tests passing. This was a reviewer check, not a source-bound full-suite proof; its console result was returned to the implementation session. No phase gate performance number is claimed from it.

Before a final readiness review: commit the exact construction-screen evidence and implementation; obtain both required stress passes without a phase-stopping failure; obtain the source-bound full suite; verify the unchanged-runtime historical regressions and evidence hashes. The fresh gate, scalar-checker measurements, shallow T2/T3 measurement and 50 author-reviewed trajectories remain later obligations. No final freeze authorization is granted by this provisional review.

Reviewer compute: three local pure unit-test invocations; no paid calls or GPU work. No spend-ledger entry was added because no paid operation occurred.

## Independent evidence audit before c12 completion

Audit HEAD: bb9c1ed5742df153fbca121fc30f3a01d8c1d337; core implementation commit: 9d57169d309088f3d0be85c52057205d91fe2c59. This supplements the initial pre-stress review and remains provisional, without freeze approval while concurrency-12 stress is pending.

Independently checked committed screen bytes and every recorded construction source hash, complete ascending accepted/rejected range partitions, and exact first-admissible population selection. E2 screen evidence in results/p3a3_screen.json has design rejection 1/1000 (0.1 percent), seed 1000075 with 32 invalid price-return-domain candidates; primary and replay reserved blocks each reject 0/1000. Extreme-tail construction failures remain an explicit population limitation. These are construction counts, not policy metrics.

Verified the source inventory matches results/p3a3_tests.json, the compact JUnit hash, retained original compressed archive/hash/length, and both XML testcase counts: 576 tests, zero failures/errors/skips. Verified concurrency-8 stress source identity and exact 5000-row plan, all complete/infrastructure-healthy with zero retries, every compact shard, all 10837 local manifest entries and their hashes/lengths, and full rollout archive consistency with compact identity, completion, cleanup and reward fields. This supports only the concurrency-8 prerequisite.

Independently rechecked historical E1/E5/E6 regression summary identities, matching current runtime and relevant financial/runtime source hashes, all 1000 exact compact matches per environment, and every local manifest and referenced archive hash (1785/1695/1545 entries respectively). Historical proofs remain labelled round two rather than relabelled as new runs. New freeze implementation retains source/design/image binding, committed-proof requirements, current-source stress/full-suite prerequisites, historical regression source matching and explicit reviewer approval status.

No additional blocker found in the audited available evidence. Concurrency-12 completion and its independent final audit remain required before readiness. Reviewer activity here was read-only local evidence verification; no Docker, policy execution, paid call or GPU work occurred.

## Final independent pre-freeze readiness audit

This final section supersedes the earlier provisional status and pending-prerequisite statements, retained above as review history. Approval is limited to creating the P3a3 source/design/image freeze and proceeding with the authorized one-shot scripted E2 gate. It does not assert gate success, completed author trajectory review, model performance or sealed-test validity.

At audit HEAD bb9c1ed5742df153fbca121fc30f3a01d8c1d337, all 88 current source inventory hashes match the source-bound full-suite and both stress proofs. Core implementation commit remains 9d57169d309088f3d0be85c52057205d91fe2c59. Generator hash: eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921. Runtime hash: fad402d113ca9e19f082ac45e3e0904edb128b9e672c351fe3a2d62eb699a827. Screen SHA256: 71789eea90e7733f6ddbe40d052d1d55b8f630cf7ad947a0c2ceba1c2868bf4c.

Independently verified concurrency-12 exact screened plan, all 5000 compact rows, all 5000 full rollout archives and the complete manifest chain of 10837 local entries. All rows are complete and infrastructure healthy; retries and transfer timeouts are zero; each full record agrees with compact policy/tier/seed, completion, cleanup, resource non-overlap and reward. All 9998 created container identifiers are distinct. Summary SHA256: 4cca8de6c66dc79328bb5399cde9febee7e4c0b61462af5444a5b7acad29382d.

Repeated the same full archive/manifest/plan checks for concurrency eight: 5000 complete healthy rows, zero retries/timeouts, 10837 manifest entries, 9998 distinct containers. Summary SHA256: a9fdfda9f901b61bc5473cc95b0dacb041dafe61cc3c106d92cd6f9ab0792664. Both satisfy the unchanged 100-percent-completion and <=0.5-percent-retry requirements. Full-suite and historical regression verification recorded above remain applicable to unchanged current sources; the final read-only freeze prerequisite check reconfirms their hashes, counts and runtime/source identity.

No unresolved blocker remains for freeze creation. The actual freeze must still perform its committed-proof/source checks and immutable-image inspection. This reviewer did not run the freeze, Docker or policies. Local audit reads only; zero paid API or GPU work.
