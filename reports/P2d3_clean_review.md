# P2d3 independent clean-context prospective review

Review date: 2026-10-27. This is an independent agent source/evidence review,
not human labels or the required author trajectory review. Reviewed implementation
`1b7234f0bb45893a69c7ef50be7ae7b2ebfadd6e`, core runtime hash
`5ac8cf100aabc4d4b47f38fe8ecc4a34fe4db1c77f6042d719c165489769781a`.
Generator: `eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`.
Read standing files in their required order, then BRIEF.md and P2B_PROMPT2.md.
Read the five runtime modules, prospective design, P2d3 validation test sources,
and prior E6 gate protocol. No Docker, tests, rollout execution, fresh case
generation, model calls, sealed seeds or external sources were used. Only this
report was written by this reviewer.

## One-shot finding resolved in pre-freeze follow-up

The new runner's exclusive call marker is experiment-tag dependent:
`experiments.py` derives it from `tag` (or `gate-E6-c{concurrency}`). The CLI
accepts `--tag` and either concurrency. A second gate invocation with another
tag or concurrency can therefore pass the same committed freeze and execute
the same fresh seed population again. The earlier runner uses the fixed
`logs/p2d2_gate_calls.json` exclusive marker. This weakens the one-shot enforcement
required by P2B_PROMPT2.md. No rerun was attempted in this review.

Follow-up source review after completion of all stress batches: the working-tree
`experiments.py` correction now reserves fixed `logs/p2d3_gate_calls.json` with
exclusive creation before `plan_for`, independently of tag/concurrency. Planning
failure retains the reservation. Tagged stress markers are unchanged. The five
prospective mocked tests in `test_p2d3_gate_once.py` cover alternate tags and
concurrencies, reservation before planning, failed setup consuming the gate,
and stress isolation. `logs/p2d3_gate_once_red_console.txt` records four failures
and one pass before the correction; `logs/p2d3_gate_control_units.xml` records
20 passing gate/orchestration/summary/phase tests afterward. This resolves the
identified source blocker. This reviewer inspected the diff/tests/results and
did not execute them. The correction is gate orchestration only; the core
runtime hash is unchanged. The final freeze must bind this corrected runner.

## Source assessment

The prospective policy distinguishes completed policy hard zeros from
infrastructure exceptions and preserves the 0.5% fixed planned denominator.
`run_with_retry` permits two total attempts, checks resource-name/ID overlap,
requires cleanup before retry, and records attempts and full exception journals.
Observed policy evidence dominates simultaneous infrastructure symptoms;
cancellation is terminal. Unknown errors and second-attempt failures remain
terminal. Ordinary wrong answers and completed crash/timeout/tamper zeros do not
enter the retry path. Relevant prospective tests cover each boundary, including
transport statuses 125/126/127 and policy/infrastructure collisions.

The protected child-status file separates Docker-client failure from solver exit;
the solver's 20-second deadline is distinct from the 60-second host-client
deadline. Teardown serializes removal and leaves an unsuccessful removal
unfinished. Attempt cleanup revisits tracked runtimes. Journals retain cause,
implicit context and exception-group members in hashed, untruncated parts.
The narrow closed-scoring compatibility hook preserves the actual scoring error;
live borrowed-runtime guards remain guards and receive trusted-origin typed
evidence. The original round-two initiating error remains unknown: reproduced
guard masking and injected causal failures do not establish its historical cause.

`phase.py` changes E6 admission/routing only inside a scoped context: it changes
one upper seed-bound constant, rejects the unreserved gap, derives replay seeds
in 1006000..1006999 for new primaries, and restores all hooks. It does not translate
seeds or change case/reward algorithms. Its public-case invariance test covers
one existing seed/tier, not an exhaustive case-space equivalence proof. The
constant-only source transformation supports the narrower admission claim.

`logs/p2d3_financial_invariance.json` records unchanged E1/E5/E6 source, generator
and prereg files against `c18691665116f1ea0bee9486b7c0b3b9dd144bcf`.
`logs/p2d3_source_preflight_correction.json` correctly retracts direct historical
E1 source-hash coverage: all 6400 saved E1 rows lack that top-level hash. The
component hash/AST audit in `logs/p2d3_e1_source_construction_audit.json` supports
unchanged construction, but cannot supply missing historical per-row hashes.
Keep this limitation in the final report. E5 and E6 each have 7000 eligible saved
source hashes with zero reported preflight mismatches.

Historical E6 regression loads the hash-checked archived reward from its own
freeze commit and temporarily substitutes its score/error functions. This is
the appropriate comparison to historical round-one rewards; running exponent3
against archived exponent32 results would confound financial and runtime changes.
The contexts restore current functions on exit. No current reward edit is needed.

## Gate protocol comparison

The planned population matches round two: four tiers, 500 oracle episodes per
tier and 50 per other existing policy, 8400 total. The summary retains first-50
policy statistics and all-500 oracle checks, per-row find-k expectations,
near-miss/false-flag floors, never-flag semantics, conceptual gaps, source/truth
binding, full lifecycle, clean false-positive ceilings, numeric/reward fractions,
and k/n counts. It adds explicit missing outcomes without fabricating zero
rewards. Independent real comparisons use the fixed full population denominator;
unit comparisons require at least 2000 oracle records. Container uniqueness
includes failed/retried attempts. Freeze comparison covers financial/runtime/
runner/design/image inputs and checks source stability after the gate.

The 50-sample selection changes from the old tier/policy/index schedule to evenly
spaced planned indices. This is prospective and still yields 50 retained full
trajectories with host truth and attempts; it is not an author review by itself.
Final review must confirm actual samples and the completed author review. Freeze
prerequisite names/results also need manual verification: the preflight trusts
the listed prerequisite results rather than independently proving the list is
the complete required six stress plus three historical batches.

## Evidence available and pending

Completed summaries `results/p2d3-r2-stress-{E1,E5,E6}-c{12,24}.json`
each report 5000/5000 complete, zero retries,
zero terminal failures and the stated core runtime hash. Their independent
`results/p2d3_stress_*_review.json` audits report no issues. Policy exception
journal counts are respectively 653, 578, 456 and 653; these are retained policy
findings, not infrastructure retries. The E5/E6 concurrency24 audits likewise
report no issues and respectively 578/456 policy journals. All six required
batches therefore report 30000/30000 complete with zero retries. This review reads those audits and does
not claim to have independently re-audited every stress row.

`results/p2d3_stress_development_interrupted.json` preserves the predecessor:
1969 retained complete rows, zero retained retries, and 3031 unretained or
unstarted. It explicitly discloses missing older in-flight cancellation evidence.
That experiment is not one of the six completed required batches.

At the follow-up snapshot, full-suite validation, all 20400 historical
per-row comparisons, dated amendment and committed new freeze, fresh 8400-row
one-shot gate, independent checker outcomes and 50 author-reviewed trajectories
are pending. Final approval is withheld. The one-shot marker finding is resolved
in the reviewed working-tree diff; recheck its committed/frozen identity and all
prerequisites before the first fresh gate. Existing artifacts must remain intact.

This review incurred no API/GPU spend or rollout compute. Completed stress
summary durations are recorded in their respective results; no inference about
uncompleted batch cost or CI success is made here.
