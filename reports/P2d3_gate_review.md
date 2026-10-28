# P2d3 independent post-gate review

Verdict: PASS for the recorded one-shot gate and infrastructure evidence. No
source/reward changes, tuning, new case construction or rollout execution were
performed. This is an independent agent review, not human labels or the separate
50-trajectory author review. The pinned pre-freeze review was not changed.

The detailed reproducible file hashes, independently recomputed policy means/
distributions and check counts are in
`results/p2d3_gate_independent_review.json`: 8400 rows reviewed, 214671 recorded
checks, zero issues. Environment E6 uses generator
`eac6db9224a724d63a3e7c7df71e0af46e65d29bb66b7c6e0d18061d55313921`, runtime
`5ac8cf100aabc4d4b47f38fe8ecc4a34fe4db1c77f6042d719c165489769781a`, orchestration
`4a381f28d00632acea36703121351326586b1cb9`, and prospective freeze
`e994296f7db7a7d41fe74eba4cc8da6aeba23f04`.

Every saved row matches the frozen plan and exact tier/policy/seed populations:
500 oracle episodes and 50 of each other policy per tier. Primaries are within
1005000..1005499; recorded replay seeds are within 1006000..1006999. All 8400
rows completed the full setup/solver/finalize/score lifecycle, with one attempt,
zero retries and zero terminal failures. Every policy-evidence row has zero
reward. The fixed global reservation records completion. No alternate gate was
launched by this reviewer.

Independently recomputed first-50 policy means, reward distributions, flagged/
false-positive counts, numeric-error fractions, all-oracle fractions and find-k
corruption/retained-flag distributions agree with the saved summary. Oracle,
random, each wrong solution and cheater thresholds pass; all-oracle checks,
clean false-positive ceilings, partial-credit floors, never-flag semantics and
every per-row find-k expectation pass. Conceptual gaps remain at least 0.02.
All 8400 real checker flags agree, and all 2000 oracle unit-comparison flags
agree. All 50 saved full trajectories were additionally rescored using only the
standalone independent scalar checker and saved primary/replay host truth:
50/50 match the recorded rewards. Their full-answer hashes, row/stage/attempt
bindings and primary oracle provenance hashes were independently checked.

All 23600 recorded container IDs and resource names have one owning row, no
stage shares an ID, every created ID has exactly one recorded removal, and all
attempts report completed cleanup. Stage image and source hashes bind to the
frozen image/submitted source. All 600 exception journals match their embedded
JSON and the concatenated full traceback SHA256; they are policy journals.
There are no unexplained/orphan JSON exception journals. Policy crash/audit
exceptions remain retained findings, not infrastructure retries.

All 43 frozen source files, nine prerequisite results, nine prerequisite audits,
two aggregate summaries and retained failed-round-two artifact hashes still
match the committed freeze and files. The pinned clean-context review hash also
matches. No frozen-input mutation was found. The interrupted predecessor and
failed round-two results remain preserved. The old round-two initiating cause
is still unknown; passing stress/regression/gate evidence does not establish it.

Limits: full answer data exist for the 50 sampled trajectories, so complete
checker recomputation is limited to that sample; all-row agreement outside it
is verified from recorded comparison flags and frozen execution source. Oracle
hash syntax/source bindings were checked for every row, and actual oracle hash
payloads were recomputed for the saved full sample. No new oracle cases were
generated. Cleanup is assessed from recorded Docker-removal evidence, without
a new Docker inspection. The earlier E1 historical source-hash omission remains
disclosed in the pre-freeze review. The separate author review ledger must be
reported separately and must not be described as independent human labels.

The gate summary records 4815.880343438999 seconds, zero API/GPU spend, and all
8400 outcomes retained. This review incurred no API/GPU spend or rollout compute.
It approves the reviewed recorded evidence; it does not authorize a next phase,
publication, another gate or modification of financial rules.
