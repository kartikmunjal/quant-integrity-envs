# P3a3 clean-context review

Status: PROVISIONAL — NOT APPROVED FOR FREEZE.

Independent reviewer session, 2026-10-29 UTC. This is a pre-stress source review, not a completed gate review. The implementation author did not conduct this review. No Docker command, policy rollout, model API, GPU job, sealed evaluation or outside-repository read was performed by this reviewer.

Reviewed AGENTS.md, SPEC.md, prereg.yaml, AMENDMENTS.md, COMPAT.md, BRIEF.md, P2B_PROMPT7.md, reports/P3a3_design.md, scripts/*p3a3*.py, tests/validation/*p3a3*.py, and the referenced construction, source-inventory and gate-statistics functions. Review baseline HEAD: 5908143. Round-three changes were uncommitted and the population screen was still in progress when reviewed. E2 generator identity remains eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921.

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
